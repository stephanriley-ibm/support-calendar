from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extended user model with role-based permissions"""
    
    ROLE_CHOICES = [
        ('engineer', 'Engineer'),
        ('coach', 'Coach'),
        ('admin', 'Admin'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='engineer',
        help_text="User's role in the organization"
    )
    team = models.ForeignKey(
        'Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        help_text="Team the user belongs to"
    )
    must_change_password = models.BooleanField(
        default=False,
        help_text="User must change password on next login"
    )
    temp_password = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Temporary password for display to admin/coach"
    )
    oncall_eligible = models.BooleanField(
        default=True,
        help_text="Whether engineer is eligible for on-call rotation assignments"
    )
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="User's preferred timezone (e.g., 'America/Denver', 'Europe/London')"
    )
    
    class Meta:
        db_table = 'users'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['team', 'role']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    @property
    def is_coach(self):
        """Check if user is a coach"""
        return self.role == 'coach'
    
    @property
    def is_admin(self):
        """Check if user is an admin"""
        return self.role == 'admin'
    
    @property
    def is_engineer(self):
        """Check if user is an engineer"""
        return self.role == 'engineer'


class Team(models.Model):
    """Team model for organizing engineers"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Team name"
    )
    coach = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coached_teams',
        help_text="Team coach/manager"
    )
    max_concurrent_off = models.IntegerField(
        default=2,
        help_text="Maximum number of team members that can be off on the same day"
    )
    description = models.TextField(
        blank=True,
        help_text="Team description"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'teams'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_member_count(self):
        """Get count of team members"""
        return self.members.filter(is_active=True).count()
    
    def get_coach_name(self):
        """Get coach's full name"""
        return self.coach.get_full_name() if self.coach else "No coach assigned"

# Made with Bob
