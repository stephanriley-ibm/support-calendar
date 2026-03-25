from rest_framework import permissions


class IsEngineer(permissions.BasePermission):
    """Permission check for engineer role"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_engineer


class IsCoach(permissions.BasePermission):
    """Permission check for coach role"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_coach


class IsAdmin(permissions.BasePermission):
    """Permission check for admin role"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsCoachOrAdmin(permissions.BasePermission):
    """Permission check for coach or admin role"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_coach or request.user.is_admin)
        )


class IsOwnerOrCoach(permissions.BasePermission):
    """
    Permission check: object owner, their coach, or admin
    Requires the object to have a 'user' attribute
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if request.user.is_admin:
            return True
        
        # Owner can access their own objects
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # Coach can access their team members' objects
        if request.user.is_coach and hasattr(obj, 'user'):
            if obj.user.team and obj.user.team.coach == request.user:
                return True
        
        return False


class IsTeamCoachOrAdmin(permissions.BasePermission):
    """
    Permission check: team's coach or admin
    Requires the object to have a 'team' attribute
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if request.user.is_admin:
            return True
        
        # Coach can access their own team
        if request.user.is_coach and hasattr(obj, 'team'):
            if obj.team and obj.team.coach == request.user:
                return True
        
        return False


class CanApproveTimeOff(permissions.BasePermission):
    """
    Permission to approve time-off requests
    Only coaches can approve requests for their team members
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can approve anything
        if request.user.is_admin:
            return True
        
        # Coach can approve for their team members
        if request.user.is_coach:
            if obj.user.team and obj.user.team.coach == request.user:
                return True
        
        return False


class CanManageOnCallRotation(permissions.BasePermission):
    """
    Permission to manage on-call rotation
    Only coaches and admins can manage rotations
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_coach or request.user.is_admin)
        )


class CanRescheduleDaysInLieu(permissions.BasePermission):
    """
    Permission to reschedule days in lieu
    Only coaches can reschedule for their team members
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can reschedule anything
        if request.user.is_admin:
            return True
        
        # Coach can reschedule for their team members
        if request.user.is_coach:
            if obj.user.team and obj.user.team.coach == request.user:
                return True
        
        return False

# Made with Bob
