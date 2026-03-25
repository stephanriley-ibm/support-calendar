from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .models import User, Team
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    TeamSerializer,
    TeamListSerializer,
)
from .permissions import IsCoachOrAdmin, IsAdmin


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model
    
    list: Get all users (admin/coach only)
    retrieve: Get user details
    create: Create new user (admin only)
    update: Update user (admin only)
    partial_update: Partial update user (admin only)
    destroy: Delete user (admin only)
    me: Get current user info
    """
    
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action == 'login':
            return [AllowAny()]
        elif self.action in ['create', 'reset_password', 'destroy']:
            # Coaches can create users, reset passwords, and delete users from their team
            return [IsCoachOrAdmin()]
        elif self.action in ['update', 'partial_update']:
            # Users can update themselves, coaches can update their team, admins can update anyone
            return [IsAuthenticated()]
        elif self.action == 'list':
            return [IsCoachOrAdmin()]
        return [IsAuthenticated()]
    
    def perform_update(self, serializer):
        """Validate update permissions based on user role"""
        user = self.request.user
        instance = self.get_object()
        
        # Check if user has permission to update this profile
        can_update = False
        
        if user.is_admin:
            # Admins can update anyone
            can_update = True
        elif user.is_coach:
            # Coaches can update their team members or themselves
            if instance.id == user.id or (instance.team and instance.team.coach == user):
                can_update = True
        elif instance.id == user.id:
            # Users can update their own profile
            can_update = True
            
            # But users can only update certain fields on their own profile
            allowed_fields = {'email', 'first_name', 'last_name', 'timezone'}
            request_fields = set(self.request.data.keys())
            
            # Check if user is trying to update restricted fields
            restricted_fields = request_fields - allowed_fields
            if restricted_fields:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(f'You cannot update these fields: {", ".join(restricted_fields)}')
        
        if not can_update:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You do not have permission to update this profile')
        
        # Use partial=True to ensure only provided fields are updated
        serializer.save()
    
    def update(self, request, *args, **kwargs):
        """Override update to ensure partial updates"""
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        """Override partial_update to ensure partial updates"""
        kwargs['partial'] = True
        return super().partial_update(request, *args, **kwargs)
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        
        if user.is_admin:
            # Admin can see all users
            return User.objects.all()
        elif user.is_coach:
            # Coach can see their team members
            return User.objects.filter(team__coach=user)
        else:
            # Engineers can only see themselves
            return User.objects.filter(id=user.id)
    
    def perform_create(self, serializer):
        """Validate team assignment for coaches"""
        user = self.request.user
        
        if user.is_coach and not user.is_admin:
            # Coach can only create users for their own team
            team_id = self.request.data.get('team')
            if team_id:
                from .models import Team
                try:
                    team = Team.objects.get(id=team_id)
                    if team.coach != user:
                        from rest_framework.exceptions import PermissionDenied
                        raise PermissionDenied('You can only add members to your own team')
                except Team.DoesNotExist:
                    from rest_framework.exceptions import ValidationError
                    raise ValidationError({'team': 'Invalid team'})
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Validate team assignment for coaches before deletion"""
        user = self.request.user
        
        if user.is_coach and not user.is_admin:
            # Coach can only delete users from their own team
            if not instance.team or instance.team.coach != user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('You can only delete members from your own team')
        
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user information"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        Login endpoint
        
        Request body:
        {
            "username": "string",
            "password": "string"
        }
        """
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=username, password=password)
        
        if user:
            token, created = Token.objects.get_or_create(user=user)
            serializer = UserSerializer(user)
            
            response_data = {
                'token': token.key,
                'user': serializer.data
            }
            
            # Check if user must change password
            if user.must_change_password:
                response_data['must_change_password'] = True
            
            return Response(response_data)
        
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Logout endpoint - deletes auth token"""
        if request.user.is_authenticated:
            Token.objects.filter(user=request.user).delete()
        return Response({'message': 'Successfully logged out'})
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """
        Change password endpoint
        
        Request body:
        {
            "old_password": "string",
            "new_password": "string",
            "new_password_confirm": "string"
        }
        """
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        new_password_confirm = request.data.get('new_password_confirm')
        
        if not all([old_password, new_password, new_password_confirm]):
            return Response(
                {'error': 'All password fields are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_password != new_password_confirm:
            return Response(
                {'error': 'New passwords do not match'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.check_password(old_password):
            return Response(
                {'error': 'Old password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password and clear temporary password flag
        user.set_password(new_password)
        user.must_change_password = False
        user.temp_password = None
        user.save()
        
        return Response({'message': 'Password changed successfully'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsCoachOrAdmin])
    def reset_password(self, request, pk=None):
        """
        Reset user password - generates new temporary password
        Admin can reset any user, Coach can reset their team members
        
        Returns the new temporary password
        """
        import secrets
        import string
        
        target_user = self.get_object()
        requesting_user = request.user
        
        # Check permissions
        if not requesting_user.is_admin:
            # Coach can only reset passwords for their team members
            if not requesting_user.is_coach or target_user.team != requesting_user.team:
                return Response(
                    {'error': 'You can only reset passwords for your team members'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Generate new temporary password
        alphabet = string.ascii_letters + string.digits
        temp_password = ''.join(secrets.choice(alphabet) for i in range(12))
        
        # Set temporary password
        target_user.set_password(temp_password)
        target_user.temp_password = temp_password
        target_user.must_change_password = True
        target_user.save()
        
        return Response({
            'message': 'Password reset successfully',
            'username': target_user.username,
            'temp_password': temp_password
        })


class TeamViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Team model
    
    list: Get all teams
    retrieve: Get team details with members
    create: Create new team (admin only)
    update: Update team (admin only)
    partial_update: Partial update team (admin only)
    destroy: Delete team (admin only)
    members: Get team members
    """
    
    queryset = Team.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TeamListSerializer
        return TeamSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Annotate with member count"""
        return Team.objects.annotate(
            member_count=models.Count('members', filter=models.Q(members__is_active=True))
        )
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get team members"""
        team = self.get_object()
        members = team.members.filter(is_active=True)
        serializer = UserSerializer(members, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """
        Get team availability for date range
        
        Query params:
        - start_date: YYYY-MM-DD
        - end_date: YYYY-MM-DD
        """
        from datetime import datetime
        from timeoff.services import TimeOffService
        
        team = self.get_object()
        
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
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
        
        availability = TimeOffService.get_team_availability(team, start_date, end_date)
        return Response(availability)


# Import models for annotation
from django.db import models

# Made with Bob
