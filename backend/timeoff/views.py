from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from datetime import datetime
from .models import TimeOffRequest
from .serializers import (
    TimeOffRequestSerializer,
    TimeOffRequestCreateSerializer,
    TimeOffRequestUpdateSerializer,
    TimeOffRequestApprovalSerializer,
    TimeOffRequestListSerializer,
)
from .services import TimeOffService
from users.permissions import IsOwnerOrCoach, CanApproveTimeOff


class TimeOffRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TimeOffRequest model
    
    list: Get time-off requests (filtered by permissions)
    retrieve: Get time-off request details
    create: Create new time-off request
    update: Update time-off request (pending only)
    partial_update: Partial update time-off request (pending only)
    destroy: Cancel time-off request
    approve: Approve time-off request (coach only)
    reject: Reject time-off request (coach only)
    check_conflicts: Check for conflicts before submitting
    my_requests: Get current user's requests
    pending: Get pending requests (coach view)
    """
    
    queryset = TimeOffRequest.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TimeOffRequestCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TimeOffRequestUpdateSerializer
        elif self.action == 'list':
            return TimeOffRequestListSerializer
        elif self.action in ['approve', 'reject']:
            return TimeOffRequestApprovalSerializer
        return TimeOffRequestSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['approve', 'reject']:
            return [IsAuthenticated(), CanApproveTimeOff()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrCoach()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Filter queryset based on user role and query params"""
        user = self.request.user
        queryset = TimeOffRequest.objects.select_related('user', 'user__team', 'approved_by')
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(end_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(start_date__lte=end_date)
        
        # Role-based filtering
        if user.is_admin:
            # Admin can see all requests
            return queryset
        elif user.is_coach:
            # Coach can see their team's requests
            team_filter = self.request.query_params.get('team')
            if team_filter:
                return queryset.filter(user__team_id=team_filter)
            return queryset.filter(user__team__coach=user)
        else:
            # Engineers can only see their own requests
            return queryset.filter(user=user)
    
    def perform_create(self, serializer):
        """Create request and check for conflicts"""
        serializer.save()
    
    def perform_destroy(self, instance):
        """Cancel pending requests or delete approved/rejected requests"""
        if instance.status == 'pending':
            # Cancel pending requests (soft delete)
            instance.cancel()
        else:
            # Allow hard delete for approved/rejected requests
            instance.delete()
    
    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """Get current user's time-off requests"""
        requests = self.get_queryset().filter(user=request.user).order_by('-created_at')
        serializer = TimeOffRequestListSerializer(requests, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending requests for coach approval"""
        if not (request.user.is_coach or request.user.is_admin):
            return Response(
                {'error': 'Only coaches and admins can view pending requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset().filter(status='pending').order_by('created_at')
        serializer = TimeOffRequestListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a time-off request"""
        instance = self.get_object()
        
        if instance.status != 'pending':
            return Response(
                {'error': 'Only pending requests can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for conflicts
        has_conflict, conflict_dates, message = TimeOffService.check_conflicts(
            instance.user,
            instance.start_date,
            instance.end_date,
            exclude_request_id=instance.id
        )
        
        if has_conflict:
            return Response(
                {
                    'error': 'Cannot approve due to conflicts',
                    'message': message,
                    'conflict_dates': [str(d) for d in conflict_dates]
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.approve(request.user)
        serializer = TimeOffRequestSerializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a time-off request"""
        instance = self.get_object()
        
        if instance.status != 'pending':
            return Response(
                {'error': 'Only pending requests can be rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TimeOffRequestApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reason = serializer.validated_data.get('rejection_reason', '')
        instance.reject(request.user, reason)
        
        response_serializer = TimeOffRequestSerializer(instance)
        return Response(response_serializer.data)
    
    @action(detail=False, methods=['post'])
    def check_conflicts(self, request):
        """
        Check for conflicts before submitting a request
        
        Request body:
        {
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD",
            "exclude_request_id": 123 (optional)
        }
        """
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')
        exclude_id = request.data.get('exclude_request_id')
        
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
        
        has_conflict, conflict_dates, message = TimeOffService.check_conflicts(
            request.user,
            start_date,
            end_date,
            exclude_request_id=exclude_id
        )
        
        conflicts = TimeOffService.get_conflicting_requests(
            request.user,
            start_date,
            end_date,
            exclude_request_id=exclude_id
        )
        
        return Response({
            'has_conflict': has_conflict,
            'message': message,
            'conflict_dates': [str(d) for d in conflict_dates],
            'conflicts': conflicts,
        })
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming time-off for user or team"""
        days_ahead = int(request.query_params.get('days', 90))
        
        if request.user.is_coach or request.user.is_admin:
            team_id = request.query_params.get('team')
            if team_id:
                from users.models import Team
                try:
                    team = Team.objects.get(id=team_id)
                    requests = TimeOffService.get_team_upcoming_timeoff(team, days_ahead)
                except Team.DoesNotExist:
                    return Response(
                        {'error': 'Team not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                requests = TimeOffService.get_user_upcoming_timeoff(request.user, days_ahead)
        else:
            requests = TimeOffService.get_user_upcoming_timeoff(request.user, days_ahead)
        
        serializer = TimeOffRequestListSerializer(requests, many=True)
        return Response(serializer.data)

# Made with Bob
