from datetime import timedelta
from django.db.models import Q, Count
from .models import TimeOffRequest
from oncall.models import DayInLieu


class TimeOffService:
    """Business logic for time-off management"""
    
    @staticmethod
    def check_conflicts(user, start_date, end_date, exclude_request_id=None):
        """
        Check for conflicts with team availability limits
        
        Args:
            user: User requesting time off
            start_date: Start date of time off
            end_date: End date of time off
            exclude_request_id: ID of request to exclude (for updates)
        
        Returns:
            tuple: (has_conflict, conflict_dates, message)
        """
        team = user.team
        if not team:
            return False, [], "User has no team assigned"
        
        max_off = team.max_concurrent_off
        conflict_dates = []
        
        # Get all dates in range
        current_date = start_date
        while current_date <= end_date:
            # Count approved time-off for this date
            approved_count = TimeOffRequest.objects.filter(
                user__team=team,
                status='approved',
                start_date__lte=current_date,
                end_date__gte=current_date
            )
            
            if exclude_request_id:
                approved_count = approved_count.exclude(id=exclude_request_id)
            
            approved_count = approved_count.count()
            
            # Count scheduled days-in-lieu for this date
            dil_count = DayInLieu.objects.filter(
                user__team=team,
                scheduled_date=current_date,
                status='scheduled'
            ).count()
            
            total_off = approved_count + dil_count
            
            if total_off >= max_off:
                conflict_dates.append(current_date)
            
            current_date += timedelta(days=1)
        
        has_conflict = len(conflict_dates) > 0
        message = ""
        
        if has_conflict:
            message = (
                f"Conflict detected: {len(conflict_dates)} day(s) exceed team limit "
                f"of {max_off} members off. Dates: {', '.join(str(d) for d in conflict_dates[:5])}"
            )
            if len(conflict_dates) > 5:
                message += f" and {len(conflict_dates) - 5} more..."
        
        return has_conflict, conflict_dates, message
    
    @staticmethod
    def get_team_availability(team, start_date, end_date):
        """
        Get team availability for date range
        
        Args:
            team: Team to check
            start_date: Start date
            end_date: End date
        
        Returns:
            dict: Availability data by date
        """
        availability = {}
        current_date = start_date
        
        while current_date <= end_date:
            # Count who's off
            off_count = TimeOffRequest.objects.filter(
                user__team=team,
                status='approved',
                start_date__lte=current_date,
                end_date__gte=current_date
            ).count()
            
            # Add days-in-lieu
            dil_count = DayInLieu.objects.filter(
                user__team=team,
                scheduled_date=current_date,
                status='scheduled'
            ).count()
            
            total_off = off_count + dil_count
            total_members = team.members.filter(is_active=True).count()
            available = total_members - total_off
            
            availability[current_date.isoformat()] = {
                'date': current_date.isoformat(),
                'total_members': total_members,
                'off_count': total_off,
                'timeoff_count': off_count,
                'dil_count': dil_count,
                'available': available,
                'at_limit': total_off >= team.max_concurrent_off,
                'over_limit': total_off > team.max_concurrent_off,
            }
            
            current_date += timedelta(days=1)
        
        return availability
    
    @staticmethod
    def get_conflicting_requests(user, start_date, end_date, exclude_request_id=None):
        """
        Get list of conflicting time-off requests and days-in-lieu
        
        Args:
            user: User requesting time off
            start_date: Start date
            end_date: End date
            exclude_request_id: ID to exclude
        
        Returns:
            dict: Conflicting requests and days-in-lieu by date
        """
        team = user.team
        if not team:
            return {}
        
        conflicts = {}
        current_date = start_date
        
        while current_date <= end_date:
            # Get approved requests for this date
            requests = TimeOffRequest.objects.filter(
                user__team=team,
                status='approved',
                start_date__lte=current_date,
                end_date__gte=current_date
            ).select_related('user')
            
            if exclude_request_id:
                requests = requests.exclude(id=exclude_request_id)
            
            # Get days-in-lieu for this date
            days_in_lieu = DayInLieu.objects.filter(
                user__team=team,
                scheduled_date=current_date,
                status='scheduled'
            ).select_related('user')
            
            if requests.exists() or days_in_lieu.exists():
                conflicts[current_date.isoformat()] = {
                    'date': current_date.isoformat(),
                    'requests': [
                        {
                            'id': req.id,
                            'user': req.user.get_full_name(),
                            'user_id': req.user.id,
                        }
                        for req in requests
                    ],
                    'days_in_lieu': [
                        {
                            'id': dil.id,
                            'user': dil.user.get_full_name(),
                            'user_id': dil.user.id,
                        }
                        for dil in days_in_lieu
                    ],
                }
            
            current_date += timedelta(days=1)
        
        return conflicts
    
    @staticmethod
    def get_user_upcoming_timeoff(user, days_ahead=90):
        """
        Get user's upcoming time-off requests
        
        Args:
            user: User to check
            days_ahead: Number of days to look ahead
        
        Returns:
            QuerySet: Upcoming time-off requests
        """
        from django.utils import timezone
        today = timezone.now().date()
        future_date = today + timedelta(days=days_ahead)
        
        return TimeOffRequest.objects.filter(
            user=user,
            status__in=['pending', 'approved'],
            end_date__gte=today,
            start_date__lte=future_date
        ).order_by('start_date')
    
    @staticmethod
    def get_team_upcoming_timeoff(team, days_ahead=90):
        """
        Get team's upcoming time-off requests
        
        Args:
            team: Team to check
            days_ahead: Number of days to look ahead
        
        Returns:
            QuerySet: Upcoming time-off requests
        """
        from django.utils import timezone
        today = timezone.now().date()
        future_date = today + timedelta(days=days_ahead)
        
        return TimeOffRequest.objects.filter(
            user__team=team,
            status__in=['pending', 'approved'],
            end_date__gte=today,
            start_date__lte=future_date
        ).select_related('user').order_by('start_date')

# Made with Bob
