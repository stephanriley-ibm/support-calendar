from datetime import datetime, timedelta
from django.db.models import Count, Q
from django.utils import timezone
from .models import OnCallShift, DayInLieu, Holiday
from users.models import User
from timeoff.models import TimeOffRequest


class OnCallRotationService:
    """Business logic for on-call rotation generation"""
    
    @staticmethod
    def get_saturdays_in_range(start_date, end_date):
        """
        Get all Saturdays in date range
        
        Args:
            start_date: Start date
            end_date: End date
        
        Returns:
            list: List of Saturday dates
        """
        saturdays = []
        current = start_date
        
        # Find first Saturday
        while current.weekday() != 5:  # 5 = Saturday
            current += timedelta(days=1)
            if current > end_date:
                return saturdays
        
        # Collect all Saturdays
        while current <= end_date:
            saturdays.append(current)
            current += timedelta(days=7)
        
        return saturdays
    
    @staticmethod
    def is_engineer_available(engineer, date):
        """
        Check if engineer is available on given date
        
        Args:
            engineer: User object
            date: Date to check
        
        Returns:
            bool: True if available
        """
        # Check time-off
        has_timeoff = TimeOffRequest.objects.filter(
            user=engineer,
            status='approved',
            start_date__lte=date,
            end_date__gte=date
        ).exists()
        
        if has_timeoff:
            return False
        
        # Check days-in-lieu
        has_dil = DayInLieu.objects.filter(
            user=engineer,
            scheduled_date=date,
            status='scheduled'
        ).exists()
        
        return not has_dil
    
    @staticmethod
    def get_engineer_shift_count(engineer, since_date=None):
        """
        Get total shifts for engineer
        
        Args:
            engineer: User object
            since_date: Optional date to count from
        
        Returns:
            int: Number of shifts
        """
        query = OnCallShift.objects.filter(engineer=engineer)
        if since_date:
            query = query.filter(shift_date__gte=since_date)
        return query.count()
    
    @staticmethod
    def get_engineer_last_shift_date(engineer):
        """
        Get date of engineer's last shift
        
        Args:
            engineer: User object
        
        Returns:
            date or None: Last shift date
        """
        last_shift = OnCallShift.objects.filter(
            engineer=engineer
        ).order_by('-shift_date').first()
        
        return last_shift.shift_date if last_shift else None
    
    @staticmethod
    def select_engineer_for_shift(available_engineers, shift_type, saturday, recent_assignments):
        """
        Select best engineer for shift based on:
        1. Availability
        2. Fairness (least recent shifts)
        3. Not assigned to recent weekends
        
        Args:
            available_engineers: List of User objects
            shift_type: Type of shift
            saturday: Saturday date
            recent_assignments: Set of recently assigned engineer IDs
        
        Returns:
            User or None: Selected engineer
        """
        candidates = []
        sunday = saturday + timedelta(days=1)
        
        for engineer in available_engineers:
            # Check availability for both Saturday and Sunday
            if not OnCallRotationService.is_engineer_available(engineer, saturday):
                continue
            if not OnCallRotationService.is_engineer_available(engineer, sunday):
                continue
            
            # Check if assigned to recent weekend
            if engineer.id in recent_assignments:
                continue
            
            # Get shift count for fairness
            shift_count = OnCallRotationService.get_engineer_shift_count(engineer)
            last_shift_date = OnCallRotationService.get_engineer_last_shift_date(engineer)
            
            # Calculate days since last shift (for tie-breaking)
            days_since_last = 999
            if last_shift_date:
                days_since_last = (saturday - last_shift_date).days
            
            candidates.append({
                'engineer': engineer,
                'shift_count': shift_count,
                'days_since_last': days_since_last,
            })
        
        if not candidates:
            return None
        
        # Sort by shift count (fairness), then by days since last shift
        candidates.sort(key=lambda x: (x['shift_count'], -x['days_since_last']))
        
        return candidates[0]['engineer']
    
    @staticmethod
    def generate_rotation(start_date, end_date, teams=None):
        """
        Generate on-call rotation for date range
        
        Args:
            start_date: Start date
            end_date: End date
            teams: Optional list of teams or single team to filter engineers
        
        Returns:
            tuple: (success, shifts_created, errors)
        """
        saturdays = OnCallRotationService.get_saturdays_in_range(start_date, end_date)
        
        if not saturdays:
            return False, [], ["No Saturdays found in date range"]
        
        # Get available engineers (active, eligible for on-call)
        engineers_query = User.objects.filter(
            role='engineer',
            is_active=True,
            oncall_eligible=True
        )
        
        # Handle both single team (backward compatibility) and multiple teams
        if teams:
            if isinstance(teams, list):
                # Multiple teams - pool engineers from all teams
                engineers_query = engineers_query.filter(team__in=teams)
            else:
                # Single team (backward compatibility)
                engineers_query = engineers_query.filter(team=teams)
        
        available_engineers = list(engineers_query)
        
        if len(available_engineers) < 3:
            return False, [], ["Not enough engineers available (minimum 3 required)"]
        
        shifts_created = []
        errors = []
        recent_assignments = set()
        
        for saturday in saturdays:
            sunday = saturday + timedelta(days=1)
            
            # Select engineers for this weekend
            early_engineer = OnCallRotationService.select_engineer_for_shift(
                available_engineers, 'early_primary', saturday, recent_assignments
            )
            
            if not early_engineer:
                errors.append(f"Could not assign Early Primary for {saturday}")
                continue
            
            # Remove from pool temporarily
            temp_pool = [e for e in available_engineers if e.id != early_engineer.id]
            
            late_engineer = OnCallRotationService.select_engineer_for_shift(
                temp_pool, 'late_primary', saturday, recent_assignments
            )
            
            if not late_engineer:
                errors.append(f"Could not assign Late Primary for {saturday}")
                continue
            
            # Remove from pool temporarily
            temp_pool = [e for e in temp_pool if e.id != late_engineer.id]
            
            secondary_engineer = OnCallRotationService.select_engineer_for_shift(
                temp_pool, 'secondary', saturday, recent_assignments
            )
            
            if not secondary_engineer:
                errors.append(f"Could not assign Secondary for {saturday}")
                continue
            
            # Create shifts
            try:
                # Saturday shifts
                sat_early = OnCallShift.objects.create(
                    shift_date=saturday,
                    shift_type='early_primary',
                    day_of_week='saturday',
                    engineer=early_engineer
                )
                shifts_created.append(sat_early)
                
                sat_late = OnCallShift.objects.create(
                    shift_date=saturday,
                    shift_type='late_primary',
                    day_of_week='saturday',
                    engineer=late_engineer
                )
                shifts_created.append(sat_late)
                
                sat_secondary = OnCallShift.objects.create(
                    shift_date=saturday,
                    shift_type='secondary',
                    day_of_week='saturday',
                    engineer=secondary_engineer
                )
                shifts_created.append(sat_secondary)
                
                # Sunday shifts
                sun_early = OnCallShift.objects.create(
                    shift_date=sunday,
                    shift_type='early_primary',
                    day_of_week='sunday',
                    engineer=early_engineer
                )
                shifts_created.append(sun_early)
                
                sun_late = OnCallShift.objects.create(
                    shift_date=sunday,
                    shift_type='late_primary',
                    day_of_week='sunday',
                    engineer=late_engineer
                )
                shifts_created.append(sun_late)
                
                # Sunday secondary shifts (cross-assignment)
                # Early Secondary = Late Primary engineer
                sun_early_secondary = OnCallShift.objects.create(
                    shift_date=sunday,
                    shift_type='early_secondary',
                    day_of_week='sunday',
                    engineer=late_engineer
                )
                shifts_created.append(sun_early_secondary)
                
                # Late Secondary = Early Primary engineer
                sun_late_secondary = OnCallShift.objects.create(
                    shift_date=sunday,
                    shift_type='late_secondary',
                    day_of_week='sunday',
                    engineer=early_engineer
                )
                shifts_created.append(sun_late_secondary)
                
                # Generate days-in-lieu for each engineer
                DaysInLieuGenerator.generate_for_weekend(
                    saturday, early_engineer, late_engineer, secondary_engineer
                )
                
                # Track recent assignments (avoid consecutive weekends)
                recent_assignments.add(early_engineer.id)
                recent_assignments.add(late_engineer.id)
                recent_assignments.add(secondary_engineer.id)
                
                # Clear old assignments (keep last 2 weekends worth)
                if len(recent_assignments) > 6:
                    recent_assignments.clear()
                
            except Exception as e:
                errors.append(f"Error creating shifts for {saturday}: {str(e)}")
        
        success = len(shifts_created) > 0
        return success, shifts_created, errors


class DaysInLieuGenerator:
    """Generate days-in-lieu for on-call shifts"""
    
    @staticmethod
    def generate_for_weekend(saturday, early_engineer, late_engineer, secondary_engineer):
        """
        Generate days-in-lieu for a weekend rotation
        
        Schedule:
        - Early Primary (Sat + Sun): Thursday & Friday of following week
        - Late Primary (Sat + Sun): Monday & Tuesday of following week
        - Saturday Secondary: Wednesday of following week
        
        Args:
            saturday: Saturday date
            early_engineer: Engineer for early shifts
            late_engineer: Engineer for late shifts
            secondary_engineer: Engineer for secondary shift
        
        Returns:
            list: Created DayInLieu objects
        """
        days_created = []
        
        # Calculate following week dates
        following_monday = saturday + timedelta(days=2)  # Saturday + 2 = Monday
        
        # Get the shifts for linking
        saturday_early = OnCallShift.objects.filter(
            shift_date=saturday,
            shift_type='early_primary',
            engineer=early_engineer
        ).first()
        
        saturday_late = OnCallShift.objects.filter(
            shift_date=saturday,
            shift_type='late_primary',
            engineer=late_engineer
        ).first()
        
        saturday_secondary = OnCallShift.objects.filter(
            shift_date=saturday,
            shift_type='secondary',
            engineer=secondary_engineer
        ).first()
        
        # Early Primary: Thursday & Friday
        if saturday_early:
            thursday = following_monday + timedelta(days=3)
            friday = following_monday + timedelta(days=4)
            
            days_created.append(DayInLieu.objects.create(
                user=early_engineer,
                oncall_shift=saturday_early,
                scheduled_date=thursday,
                status='scheduled'
            ))
            
            days_created.append(DayInLieu.objects.create(
                user=early_engineer,
                oncall_shift=saturday_early,
                scheduled_date=friday,
                status='scheduled'
            ))
        
        # Late Primary: Monday & Tuesday
        if saturday_late:
            tuesday = following_monday + timedelta(days=1)
            
            days_created.append(DayInLieu.objects.create(
                user=late_engineer,
                oncall_shift=saturday_late,
                scheduled_date=following_monday,
                status='scheduled'
            ))
            
            days_created.append(DayInLieu.objects.create(
                user=late_engineer,
                oncall_shift=saturday_late,
                scheduled_date=tuesday,
                status='scheduled'
            ))
        
        # Saturday Secondary: Wednesday
        if saturday_secondary:
            wednesday = following_monday + timedelta(days=2)
            
            days_created.append(DayInLieu.objects.create(
                user=secondary_engineer,
                oncall_shift=saturday_secondary,
                scheduled_date=wednesday,
                status='scheduled'
            ))
        
        return days_created
    
    @staticmethod
    def generate_for_holiday_shift(shift, num_days=1):
        """
        Generate days-in-lieu for a holiday shift
        
        Args:
            shift: OnCallShift object
            num_days: Number of days in lieu to grant
        
        Returns:
            list: Created DayInLieu objects
        """
        days_created = []
        
        # Schedule days in lieu for the following week
        base_date = shift.shift_date + timedelta(days=7)
        
        for i in range(num_days):
            scheduled_date = base_date + timedelta(days=i)
            
            # Skip weekends
            while scheduled_date.weekday() in [5, 6]:
                scheduled_date += timedelta(days=1)
            
            days_created.append(DayInLieu.objects.create(
                user=shift.engineer,
                oncall_shift=shift,
                scheduled_date=scheduled_date,
                status='scheduled'
            ))
        
        return days_created

# Made with Bob
