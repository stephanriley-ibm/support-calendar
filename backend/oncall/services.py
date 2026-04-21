from datetime import datetime, timedelta, date
from django.db.models import Count, Q
from django.utils import timezone
from django.db import transaction
from .models import OnCallShift, DayInLieu, Holiday, OnCallProvider, ExternalUserMapping, ProviderSyncLog
from users.models import User
from timeoff.models import TimeOffRequest
from typing import List, Dict, Optional


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

class ProviderSyncService:
    """
    Service for syncing on-call shifts from external providers.
    
    Orchestrates the process of:
    1. Fetching shifts from provider (e.g., PagerDuty)
    2. Mapping external users to local users
    3. Creating/updating OnCallShift records
    4. Generating days-in-lieu automatically
    """
    
    def __init__(self, provider: OnCallProvider):
        """
        Initialize sync service for a provider.
        
        Args:
            provider: OnCallProvider model instance
        """
        self.provider = provider
        self.provider_instance = None
        self.stats = {
            'fetched': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': [],
        }
    
    def _get_provider_instance(self):
        """Lazy load provider instance."""
        if not self.provider_instance:
            from .providers import get_provider_instance
            self.provider_instance = get_provider_instance(self.provider)
        return self.provider_instance
    
    def sync_shifts(
        self,
        schedule_ids: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sync_type: str = 'manual'
    ) -> ProviderSyncLog:
        """
        Sync shifts from external provider.
        
        Args:
            schedule_ids: List of external schedule IDs (None = use config)
            start_date: Start date for sync (None = use lookback setting)
            end_date: End date for sync (None = use lookahead setting)
            sync_type: Type of sync ('manual', 'scheduled', 'initial')
        
        Returns:
            ProviderSyncLog instance with sync results
        """
        # Create sync log
        sync_log = ProviderSyncLog.objects.create(
            provider=self.provider,
            sync_type=sync_type,
            status='started',
        )
        
        try:
            # Determine date range
            if not start_date:
                start_date = date.today() - timedelta(days=self.provider.sync_lookback_days)
            if not end_date:
                end_date = date.today() + timedelta(days=self.provider.sync_lookahead_days)
            
            # Get schedule IDs from config if not provided
            if not schedule_ids:
                schedule_ids = self.provider.config.get('schedule_ids', [])
            
            if not schedule_ids:
                raise ValueError("No schedule IDs configured or provided")
            
            # Get provider instance
            provider_inst = self._get_provider_instance()
            
            # Fetch shifts from provider
            external_shifts = provider_inst.fetch_shifts(
                schedule_ids=schedule_ids,
                start_date=start_date,
                end_date=end_date
            )
            
            self.stats['fetched'] = len(external_shifts)
            
            # Process each shift
            for external_shift in external_shifts:
                try:
                    self._process_shift(external_shift)
                except Exception as e:
                    self.stats['errors'].append({
                        'shift_id': external_shift.get('external_shift_id'),
                        'error': str(e)
                    })
            
            # Update sync log
            sync_log.status = 'success' if not self.stats['errors'] else 'partial'
            sync_log.shifts_fetched = self.stats['fetched']
            sync_log.shifts_created = self.stats['created']
            sync_log.shifts_updated = self.stats['updated']
            sync_log.shifts_skipped = self.stats['skipped']
            sync_log.details = self.stats
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            self.stats['errors'].append({'general': str(e)})
        
        finally:
            sync_log.end_time = timezone.now()
            sync_log.save()
            
            # Update provider last sync
            self.provider.last_sync_at = timezone.now()
            self.provider.last_sync_status = sync_log.status
            if sync_log.status == 'failed':
                self.provider.last_sync_error = sync_log.error_message
            else:
                self.provider.last_sync_error = ''
            self.provider.save()
        
        return sync_log
    
    @transaction.atomic
    def _process_shift(self, external_shift: Dict):
        """
        Process a single external shift.
        
        Creates or updates OnCallShift and generates days-in-lieu.
        """
        # Map external user to local user
        user_mapping = self._get_or_create_user_mapping(
            external_shift['external_user_id'],
            external_shift.get('metadata', {})
        )
        
        if not user_mapping:
            self.stats['skipped'] += 1
            return
        
        # Get all dates covered by this shift
        provider_inst = self._get_provider_instance()
        shift_dates = provider_inst.calculate_shift_dates(
            external_shift['start_datetime'],
            external_shift['end_datetime']
        )
        
        # Only process weekend shifts (Saturday or Sunday)
        weekend_dates = [d for d in shift_dates if provider_inst.is_weekend_shift(d)]
        
        if not weekend_dates:
            self.stats['skipped'] += 1
            return
        
        # Create shift for each weekend date
        for shift_date in weekend_dates:
            self._create_or_update_shift(
                shift_date=shift_date,
                shift_type=external_shift['shift_type'],
                engineer=user_mapping.local_user,
                external_shift=external_shift
            )
    
    def _create_or_update_shift(
        self,
        shift_date: date,
        shift_type: str,
        engineer: User,
        external_shift: Dict
    ):
        """Create or update a single shift record."""
        # Check if shift already exists
        existing_shift = OnCallShift.objects.filter(
            provider=self.provider,
            external_shift_id=external_shift['external_shift_id'],
            shift_date=shift_date
        ).first()
        
        shift_data = {
            'shift_date': shift_date,
            'shift_type': shift_type,
            'engineer': engineer,
            'provider': self.provider,
            'external_shift_id': external_shift['external_shift_id'],
            'external_schedule_id': external_shift['external_schedule_id'],
            'synced_at': timezone.now(),
            'is_synced': True,
            'sync_metadata': external_shift.get('metadata', {}),
        }
        
        if existing_shift:
            # Update existing shift
            for key, value in shift_data.items():
                setattr(existing_shift, key, value)
            existing_shift.save()
            self.stats['updated'] += 1
        else:
            # Create new shift
            shift = OnCallShift.objects.create(**shift_data)
            self.stats['created'] += 1
            
            # Generate days in lieu for weekend shifts only
            if shift.is_weekend_shift:
                self._generate_days_in_lieu(shift)
    
    def _generate_days_in_lieu(self, shift: OnCallShift):
        """
        Generate days-in-lieu for a shift using existing logic.
        
        Maps shift types to appropriate days off:
        - early_primary: Thursday & Friday
        - late_primary: Monday & Tuesday
        - secondary/early_secondary/late_secondary: Wednesday
        """
        # Calculate following week dates
        saturday = shift.shift_date
        if shift.shift_date.weekday() == 6:  # If Sunday, get previous Saturday
            saturday = shift.shift_date - timedelta(days=1)
        
        following_monday = saturday + timedelta(days=2)
        
        days_to_create = []
        
        if shift.shift_type == 'early_primary':
            # Thursday & Friday
            thursday = following_monday + timedelta(days=3)
            friday = following_monday + timedelta(days=4)
            days_to_create = [thursday, friday]
            
        elif shift.shift_type == 'late_primary':
            # Monday & Tuesday
            tuesday = following_monday + timedelta(days=1)
            days_to_create = [following_monday, tuesday]
            
        elif shift.shift_type in ['secondary', 'early_secondary', 'late_secondary']:
            # Wednesday
            wednesday = following_monday + timedelta(days=2)
            days_to_create = [wednesday]
        
        # Create the days-in-lieu records
        for scheduled_date in days_to_create:
            # Check if already exists
            existing = DayInLieu.objects.filter(
                user=shift.engineer,
                oncall_shift=shift,
                scheduled_date=scheduled_date
            ).exists()
            
            if not existing:
                DayInLieu.objects.create(
                    user=shift.engineer,
                    oncall_shift=shift,
                    scheduled_date=scheduled_date,
                    status='scheduled'
                )
    
    def _get_or_create_user_mapping(
        self,
        external_user_id: str,
        metadata: Dict
    ) -> Optional[ExternalUserMapping]:
        """
        Get or create user mapping for external user.
        
        Tries to auto-map by email if no mapping exists.
        """
        # Try to find existing mapping
        mapping = ExternalUserMapping.objects.filter(
            provider=self.provider,
            external_user_id=external_user_id,
            is_active=True
        ).first()
        
        if mapping:
            return mapping
        
        # Try to auto-map by email
        email = metadata.get('user_email', '')
        if email:
            local_user = User.objects.filter(email=email).first()
            
            if local_user:
                mapping = ExternalUserMapping.objects.create(
                    provider=self.provider,
                    external_user_id=external_user_id,
                    external_email=email,
                    external_name=metadata.get('user_name', ''),
                    local_user=local_user,
                    is_active=True
                )
                return mapping
        
        # No mapping found and couldn't auto-create
        return None
    
    def test_connection(self) -> tuple[bool, str]:
        """Test connection to provider."""
        try:
            provider_inst = self._get_provider_instance()
            return provider_inst.test_connection()
        except Exception as e:
            return False, f"Error initializing provider: {str(e)}"
    
    def fetch_and_map_users(self) -> Dict:
        """
        Fetch users from provider and attempt to map them.
        
        Returns dict with mapping statistics.
        """
        stats = {
            'total_fetched': 0,
            'auto_mapped': 0,
            'already_mapped': 0,
            'unmapped': 0,
            'unmapped_users': []
        }
        
        try:
            provider_inst = self._get_provider_instance()
            external_users = provider_inst.fetch_users()
            stats['total_fetched'] = len(external_users)
            
            for ext_user in external_users:
                # Check if already mapped
                existing = ExternalUserMapping.objects.filter(
                    provider=self.provider,
                    external_user_id=ext_user['external_user_id']
                ).first()
                
                if existing:
                    stats['already_mapped'] += 1
                    continue
                
                # Try to auto-map by email
                if ext_user['email']:
                    local_user = User.objects.filter(email=ext_user['email']).first()
                    
                    if local_user:
                        ExternalUserMapping.objects.create(
                            provider=self.provider,
                            external_user_id=ext_user['external_user_id'],
                            external_email=ext_user['email'],
                            external_name=ext_user['name'],
                            local_user=local_user,
                            is_active=True
                        )
                        stats['auto_mapped'] += 1
                        continue
                
                # Couldn't map
                stats['unmapped'] += 1
                stats['unmapped_users'].append({
                    'id': ext_user['external_user_id'],
                    'name': ext_user['name'],
                    'email': ext_user['email']
                })
        
        except Exception as e:
            stats['error'] = str(e)
        
        return stats


# Made with Bob
