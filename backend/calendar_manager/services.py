from datetime import datetime, timedelta
from django.db.models import Q
from timeoff.models import TimeOffRequest
from oncall.models import OnCallShift, DayInLieu, Holiday


class CalendarService:
    """Service for aggregating calendar events from multiple sources"""
    
    @staticmethod
    def get_calendar_events(start_date, end_date, user=None, team=None, event_types=None):
        """
        Get all calendar events for a date range
        
        Args:
            start_date: Start date
            end_date: End date
            user: Optional user filter
            team: Optional team filter
            event_types: Optional list of event types to include
                ['timeoff', 'oncall', 'days_in_lieu', 'holidays']
        
        Returns:
            list: List of calendar events
        """
        if event_types is None:
            event_types = ['timeoff', 'oncall', 'days_in_lieu', 'holidays']
        
        events = []
        
        # Get time-off events
        if 'timeoff' in event_types:
            events.extend(CalendarService._get_timeoff_events(
                start_date, end_date, user, team
            ))
        
        # Get on-call shift events
        if 'oncall' in event_types:
            events.extend(CalendarService._get_oncall_events(
                start_date, end_date, user, team
            ))
        
        # Get days-in-lieu events
        if 'days_in_lieu' in event_types:
            events.extend(CalendarService._get_days_in_lieu_events(
                start_date, end_date, user, team
            ))
        
        # Get holiday events
        if 'holidays' in event_types:
            events.extend(CalendarService._get_holiday_events(
                start_date, end_date
            ))
        
        # Sort by date
        events.sort(key=lambda x: x['start'])
        
        return events
    
    @staticmethod
    def _get_timeoff_events(start_date, end_date, user=None, team=None):
        """Get time-off request events"""
        queryset = TimeOffRequest.objects.filter(
            status='approved',
            start_date__lte=end_date,
            end_date__gte=start_date
        ).select_related('user', 'user__team')
        
        if user:
            queryset = queryset.filter(user=user)
        if team:
            queryset = queryset.filter(user__team=team)
        
        events = []
        for request in queryset:
            events.append({
                'id': f'timeoff-{request.id}',
                'type': 'timeoff',
                'title': f'{request.user.get_full_name()} - Time Off',
                'start': request.start_date.isoformat(),
                'end': (request.end_date + timedelta(days=1)).isoformat(),  # End is exclusive
                'allDay': True,
                'user': {
                    'id': request.user.id,
                    'name': request.user.get_full_name(),
                    'team': request.user.team.name if request.user.team else None,
                },
                'details': {
                    'reason': request.reason,
                    'duration_days': request.duration_days,
                    'approved_by': request.approved_by.get_full_name() if request.approved_by else None,
                },
                'color': '#3788d8',  # Blue
            })
        
        return events
    
    @staticmethod
    def _get_oncall_events(start_date, end_date, user=None, team=None):
        """Get on-call shift events"""
        queryset = OnCallShift.objects.filter(
            shift_date__gte=start_date,
            shift_date__lte=end_date
        ).select_related('engineer', 'engineer__team', 'holiday')
        
        if user:
            queryset = queryset.filter(engineer=user)
        if team:
            queryset = queryset.filter(engineer__team=team)
        
        events = []
        for shift in queryset:
            # Determine color based on shift type
            color_map = {
                'early_primary': '#28a745',      # Green
                'late_primary': '#ffc107',       # Yellow
                'secondary': '#17a2b8',          # Cyan
                'early_secondary': '#3498db',    # Blue
                'late_secondary': '#9b59b6',     # Purple
                'holiday': '#dc3545',            # Red
            }
            
            title = f'{shift.engineer.get_full_name()} - {shift.get_shift_type_display()}'
            if shift.holiday:
                title += f' ({shift.holiday.name})'
            
            # Use specific type for holiday shifts
            event_type = f'oncall_holiday' if shift.holiday else f'oncall_{shift.shift_type}'
            
            events.append({
                'id': f'oncall-{shift.id}',
                'type': event_type,
                'title': title,
                'start': shift.shift_date.isoformat(),
                'end': (shift.shift_date + timedelta(days=1)).isoformat(),
                'allDay': True if not shift.start_time else False,
                'user': {
                    'id': shift.engineer.id,
                    'name': shift.engineer.get_full_name(),
                    'team': shift.engineer.team.name if shift.engineer.team else None,
                },
                'details': {
                    'shift_type': shift.shift_type,
                    'shift_type_display': shift.get_shift_type_display(),
                    'day_of_week': shift.get_day_of_week_display(),
                    'start_time': shift.start_time.isoformat() if shift.start_time else None,
                    'end_time': shift.end_time.isoformat() if shift.end_time else None,
                    'holiday': shift.holiday.name if shift.holiday else None,
                    'notes': shift.notes,
                },
                'color': color_map.get(shift.shift_type, '#6c757d'),
            })
        
        return events
    
    @staticmethod
    def _get_days_in_lieu_events(start_date, end_date, user=None, team=None):
        """Get days-in-lieu events"""
        queryset = DayInLieu.objects.filter(
            status='scheduled',
            scheduled_date__gte=start_date,
            scheduled_date__lte=end_date
        ).select_related('user', 'user__team', 'oncall_shift')
        
        if user:
            queryset = queryset.filter(user=user)
        if team:
            queryset = queryset.filter(user__team=team)
        
        events = []
        for dil in queryset:
            events.append({
                'id': f'dil-{dil.id}',
                'type': 'day_in_lieu',
                'title': f'{dil.user.get_full_name()} - Day in Lieu',
                'start': dil.scheduled_date.isoformat(),
                'end': (dil.scheduled_date + timedelta(days=1)).isoformat(),
                'allDay': True,
                'user': {
                    'id': dil.user.id,
                    'name': dil.user.get_full_name(),
                    'team': dil.user.team.name if dil.user.team else None,
                },
                'details': {
                    'is_manually_created': dil.is_manually_created,
                    'was_adjusted': dil.was_adjusted,
                    'original_date': dil.original_scheduled_date.isoformat() if dil.original_scheduled_date else None,
                    'shift_date': dil.oncall_shift.shift_date.isoformat() if dil.oncall_shift else None,
                    'notes': dil.notes,
                },
                'color': '#6f42c1',  # Purple
            })
        
        return events
    
    @staticmethod
    def _get_holiday_events(start_date, end_date):
        """Get holiday events"""
        queryset = Holiday.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        )
        
        events = []
        for holiday in queryset:
            events.append({
                'id': f'holiday-{holiday.id}',
                'type': 'holiday',
                'title': holiday.name,
                'start': holiday.date.isoformat(),
                'end': (holiday.date + timedelta(days=1)).isoformat(),
                'allDay': True,
                'details': {
                    'description': holiday.description,
                    'requires_coverage': holiday.requires_coverage,
                },
                'color': '#fd7e14',  # Orange
            })
        
        return events
    
    @staticmethod
    def get_user_calendar(user, start_date, end_date):
        """Get calendar events for a specific user"""
        return CalendarService.get_calendar_events(
            start_date, end_date, user=user
        )
    
    @staticmethod
    def get_team_calendar(team, start_date, end_date):
        """Get calendar events for a specific team"""
        return CalendarService.get_calendar_events(
            start_date, end_date, team=team
        )
    
    @staticmethod
    def get_organization_calendar(start_date, end_date):
        """Get calendar events for entire organization"""
        return CalendarService.get_calendar_events(
            start_date, end_date
        )

# Made with Bob
