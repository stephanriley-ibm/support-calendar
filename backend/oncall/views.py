from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta
from .models import Holiday, OnCallShift, DayInLieu
from .serializers import (
    HolidaySerializer,
    OnCallShiftSerializer,
    OnCallShiftCreateSerializer,
    OnCallShiftListSerializer,
    DayInLieuSerializer,
    DayInLieuCreateSerializer,
    DayInLieuRescheduleSerializer,
    DayInLieuListSerializer,
)
from .services import OnCallRotationService, DaysInLieuGenerator
from users.permissions import (
    IsCoachOrAdmin,
    CanManageOnCallRotation,
    CanRescheduleDaysInLieu,
)


class HolidayViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Holiday model
    
    list: Get all holidays
    retrieve: Get holiday details
    create: Create new holiday (coach/admin only)
    update: Update holiday (coach/admin only)
    partial_update: Partial update holiday (coach/admin only)
    destroy: Delete holiday (coach/admin only)
    upcoming: Get upcoming holidays
    """
    
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsCoachOrAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Filter queryset by query params"""
        queryset = Holiday.objects.all()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Filter by coverage requirement
        requires_coverage = self.request.query_params.get('requires_coverage')
        if requires_coverage is not None:
            queryset = queryset.filter(requires_coverage=requires_coverage.lower() == 'true')
        
        return queryset.order_by('date')
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming holidays"""
        from django.utils import timezone
        today = timezone.now().date()
        
        days_ahead = int(request.query_params.get('days', 90))
        future_date = today + timezone.timedelta(days=days_ahead)
        
        holidays = Holiday.objects.filter(
            date__gte=today,
            date__lte=future_date
        ).order_by('date')
        
        serializer = self.get_serializer(holidays, many=True)
        return Response(serializer.data)


class OnCallShiftViewSet(viewsets.ModelViewSet):
    """
    ViewSet for OnCallShift model
    
    list: Get on-call shifts
    retrieve: Get shift details
    create: Create new shift (coach/admin only)
    update: Update shift (coach/admin only)
    partial_update: Partial update shift (coach/admin only)
    destroy: Delete shift (coach/admin only)
    generate_rotation: Generate weekend rotation (coach/admin only)
    my_shifts: Get current user's shifts
    schedule: Get schedule view
    """
    
    queryset = OnCallShift.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OnCallShiftCreateSerializer
        elif self.action == 'list':
            return OnCallShiftListSerializer
        return OnCallShiftSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'generate_rotation']:
            return [CanManageOnCallRotation()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Filter queryset by query params"""
        queryset = OnCallShift.objects.select_related('engineer', 'holiday')
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(shift_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(shift_date__lte=end_date)
        
        # Filter by engineer
        engineer_id = self.request.query_params.get('engineer')
        if engineer_id:
            queryset = queryset.filter(engineer_id=engineer_id)
        
        # Filter by shift type
        shift_type = self.request.query_params.get('shift_type')
        if shift_type:
            queryset = queryset.filter(shift_type=shift_type)
        
        # Filter by holiday shifts
        is_holiday = self.request.query_params.get('is_holiday')
        if is_holiday is not None:
            if is_holiday.lower() == 'true':
                queryset = queryset.filter(shift_type='holiday')
            else:
                queryset = queryset.exclude(shift_type='holiday')
        
        return queryset.order_by('shift_date', 'shift_type')
    
    @action(detail=False, methods=['post'])
    def generate_rotation(self, request):
        """
        Generate on-call rotation for date range
        
        Request body:
        {
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD",
            "team_ids": [123, 456] (optional - can be single team_id for backward compatibility)
        }
        """
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')
        team_ids = request.data.get('team_ids', [])
        team_id = request.data.get('team_id')  # Backward compatibility
        
        if not start_date_str or not end_date_str:
            return Response(
                {'error': 'start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Handle backward compatibility - convert single team_id to list
        if team_id and not team_ids:
            team_ids = [team_id]
        
        # Get teams if specified
        teams = None
        if team_ids:
            from users.models import Team
            try:
                teams = list(Team.objects.filter(id__in=team_ids))
                if len(teams) != len(team_ids):
                    return Response(
                        {'error': 'One or more teams not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            except Exception as e:
                return Response(
                    {'error': f'Error fetching teams: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Generate rotation
        success, shifts_created, errors = OnCallRotationService.generate_rotation(
            start_date, end_date, teams
        )
        
        if not success:
            return Response(
                {
                    'success': False,
                    'errors': errors,
                    'shifts_created': 0
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = OnCallShiftListSerializer(shifts_created, many=True)
        return Response({
            'success': True,
            'shifts_created': len(shifts_created),
            'errors': errors,
            'shifts': serializer.data
        })
    @action(detail=False, methods=['post'])
    def preview_rotation(self, request):
        """
        Preview on-call rotation for date range without creating shifts
        
        Request body:
        {
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD",
            "team_ids": [123, 456] (optional - can be single team_id for backward compatibility)
        }
        """
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')
        team_ids = request.data.get('team_ids', [])
        team_id = request.data.get('team_id')  # Backward compatibility
        
        if not start_date_str or not end_date_str:
            return Response(
                {'error': 'start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Handle backward compatibility - convert single team_id to list
        if team_id and not team_ids:
            team_ids = [team_id]
        
        # Get teams if specified
        teams = None
        if team_ids:
            from users.models import Team
            try:
                teams = list(Team.objects.filter(id__in=team_ids))
                if len(teams) != len(team_ids):
                    return Response(
                        {'error': 'One or more teams not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            except Exception as e:
                return Response(
                    {'error': f'Error fetching teams: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get Saturdays in range
        saturdays = OnCallRotationService.get_saturdays_in_range(start_date, end_date)
        
        if not saturdays:
            return Response({
                'weekend_count': 0,
                'total_shifts': 0,
                'shifts': [],
                'errors': ['No Saturdays found in date range']
            })
        
        # Get available engineers (active, eligible for on-call)
        from users.models import User
        engineers_query = User.objects.filter(
            role='engineer',
            is_active=True,
            oncall_eligible=True
        )
        
        # Handle both single team and multiple teams
        if teams:
            if isinstance(teams, list):
                engineers_query = engineers_query.filter(team__in=teams)
            else:
                engineers_query = engineers_query.filter(team=teams)
        
        available_engineers = list(engineers_query)
        
        if len(available_engineers) < 3:
            return Response({
                'weekend_count': len(saturdays),
                'total_shifts': 0,
                'shifts': [],
                'errors': ['Not enough engineers available (minimum 3 required)']
            })
        
        # Generate preview data
        preview_shifts = []
        for saturday in saturdays:
            sunday = saturday + timedelta(days=1)
            
            # Create preview entries for each shift type
            shift_types = ['early_primary', 'late_primary', 'secondary']
            for shift_type in shift_types:
                # Saturday
                preview_shifts.append({
                    'date': saturday.isoformat(),
                    'day': 'Saturday',
                    'shift_type': shift_type,
                    'engineer': 'TBD'
                })
                # Sunday
                preview_shifts.append({
                    'date': sunday.isoformat(),
                    'day': 'Sunday',
                    'shift_type': shift_type,
                    'engineer': 'TBD'
                })
        
        return Response({
            'weekend_count': len(saturdays),
            'total_shifts': len(preview_shifts),
            'shifts': preview_shifts,
            'errors': []
        })
    
    
    @action(detail=False, methods=['post'], permission_classes=[CanManageOnCallRotation])
    def delete_rotation(self, request):
        """
        Delete on-call shifts for a date range
        
        Request body:
        {
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD",
            "team_ids": [123, 456] (optional - delete only shifts for these teams)
        }
        """
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')
        team_ids = request.data.get('team_ids', [])
        
        if not start_date_str or not end_date_str:
            return Response(
                {'error': 'start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build query
        query = OnCallShift.objects.filter(
            shift_date__gte=start_date,
            shift_date__lte=end_date
        )
        
        # Filter by teams if specified
        if team_ids:
            query = query.filter(engineer__team__id__in=team_ids)
        
        # Count before deletion
        count = query.count()
        
        if count == 0:
            return Response({
                'success': True,
                'shifts_deleted': 0,
                'message': 'No shifts found in the specified date range'
            })
        
        # Delete shifts and associated days in lieu
        deleted_shifts = count
        query.delete()
        
        return Response({
            'success': True,
            'shifts_deleted': deleted_shifts,
            'message': f'Successfully deleted {deleted_shifts} shift(s)'
        })
    
    @action(detail=False, methods=['get'])
    def my_shifts(self, request):
        """Get current user's on-call shifts"""
        shifts = self.get_queryset().filter(engineer=request.user)
        serializer = OnCallShiftListSerializer(shifts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def schedule(self, request):
        """
        Get on-call schedule view
        Returns shifts grouped by date
        """
        queryset = self.get_queryset()
        
        # Group shifts by date
        schedule = {}
        for shift in queryset:
            date_str = shift.shift_date.isoformat()
            if date_str not in schedule:
                schedule[date_str] = {
                    'date': date_str,
                    'day_of_week': shift.get_day_of_week_display(),
                    'shifts': []
                }
            
            schedule[date_str]['shifts'].append({
                'id': shift.id,
                'shift_type': shift.shift_type,
                'shift_type_display': shift.get_shift_type_display(),
                'engineer': {
                    'id': shift.engineer.id,
                    'name': shift.engineer.get_full_name(),
                },
                'holiday': shift.holiday.name if shift.holiday else None,
                'start_time': shift.start_time,
                'end_time': shift.end_time,
            })
        
        # Convert to list and sort by date
        schedule_list = sorted(schedule.values(), key=lambda x: x['date'])
        
        return Response(schedule_list)


class DayInLieuViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DayInLieu model
    
    list: Get days in lieu
    retrieve: Get day in lieu details
    create: Create manual day in lieu (coach/admin only)
    update: Update day in lieu (coach/admin only)
    partial_update: Partial update day in lieu (coach/admin only)
    destroy: Delete day in lieu (coach/admin only)
    reschedule: Reschedule day in lieu (coach only)
    mark_used: Mark day as used
    my_days: Get current user's days in lieu
    balance: Get user's balance
    """
    
    queryset = DayInLieu.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DayInLieuCreateSerializer
        elif self.action == 'list':
            return DayInLieuListSerializer
        elif self.action == 'reschedule':
            return DayInLieuRescheduleSerializer
        return DayInLieuSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsCoachOrAdmin()]
        elif self.action == 'reschedule':
            return [CanRescheduleDaysInLieu()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Filter queryset by query params"""
        queryset = DayInLieu.objects.select_related('user', 'user__team', 'oncall_shift', 'adjusted_by')
        
        # Filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        elif not (self.request.user.is_coach or self.request.user.is_admin):
            # Non-coaches can only see their own
            queryset = queryset.filter(user=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(scheduled_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_date__lte=end_date)
        
        return queryset.order_by('scheduled_date')
    
    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """
        Reschedule a day in lieu
        
        Request body:
        {
            "new_date": "YYYY-MM-DD",
            "reason": "string"
        }
        """
        instance = self.get_object()
        
        if instance.status != 'scheduled':
            return Response(
                {'error': 'Only scheduled days can be rescheduled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = DayInLieuRescheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_date = serializer.validated_data['new_date']
        reason = serializer.validated_data['reason']
        
        instance.reschedule(new_date, request.user, reason)
        
        response_serializer = self.get_serializer(instance)
        return Response(response_serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_used(self, request, pk=None):
        """Mark a day in lieu as used"""
        instance = self.get_object()
        
        if instance.status != 'scheduled':
            return Response(
                {'error': 'Only scheduled days can be marked as used'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.mark_as_used()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_days(self, request):
        """Get current user's days in lieu"""
        days = self.get_queryset().filter(user=request.user)
        serializer = DayInLieuListSerializer(days, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get user's days in lieu balance"""
        user_id = request.query_params.get('user')
        
        if user_id and (request.user.is_coach or request.user.is_admin):
            from users.models import User
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            user = request.user
        
        scheduled = DayInLieu.objects.filter(user=user, status='scheduled').count()
        used = DayInLieu.objects.filter(user=user, status='used').count()
        expired = DayInLieu.objects.filter(user=user, status='expired').count()
        
        return Response({
            'user': {
                'id': user.id,
                'name': user.get_full_name(),
            },
            'scheduled': scheduled,
            'used': used,
            'expired': expired,
            'total': scheduled + used + expired,
        })

# Made with Bob
