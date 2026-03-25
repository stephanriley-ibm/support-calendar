# Calendar Application - Implementation Guide

## Overview

This guide provides detailed implementation instructions, code examples, and best practices for building the Calendar application.

---

## Phase 1: Backend Foundation

### Step 1: Project Initialization

#### Create Django Project
```bash
# Create project directory
mkdir calendar-app
cd calendar-app

# Create backend directory
mkdir backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Django and dependencies
pip install django djangorestframework django-cors-headers psycopg2-binary python-decouple celery redis

# Create Django project
django-admin startproject config .

# Create apps
python manage.py startapp users
python manage.py startapp timeoff
python manage.py startapp oncall
python manage.py startapp calendar
python manage.py startapp notifications
```

#### Configure Settings Structure
```bash
mkdir config/settings
touch config/settings/__init__.py
touch config/settings/base.py
touch config/settings/development.py
touch config/settings/production.py
```

### Step 2: Database Models Implementation

#### User Model (`apps/users/models.py`)
```python
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
        default='engineer'
    )
    team = models.ForeignKey(
        'Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members'
    )
    phone_number = models.CharField(max_length=20, blank=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
    
    @property
    def is_coach(self):
        return self.role == 'coach'
    
    @property
    def is_admin(self):
        return self.role == 'admin'


class Team(models.Model):
    """Team model for organizing engineers"""
    
    name = models.CharField(max_length=100, unique=True)
    coach = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='coached_teams'
    )
    max_concurrent_off = models.IntegerField(
        default=2,
        help_text="Maximum number of team members that can be off on the same day"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'teams'
        ordering = ['name']
    
    def __str__(self):
        return self.name
```

#### TimeOff Models (`apps/timeoff/models.py`)
```python
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.users.models import User

class TimeOffRequest(models.Model):
    """Time-off request model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='timeoff_requests'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    reason = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_requests'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'timeoff_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()}: {self.start_date} to {self.end_date}"
    
    def clean(self):
        """Validate time-off request"""
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError("End date must be after start date")
            
            if self.start_date < timezone.now().date():
                raise ValidationError("Cannot request time off in the past")
    
    @property
    def duration_days(self):
        """Calculate duration in days"""
        return (self.end_date - self.start_date).days + 1
    
    def approve(self, approved_by):
        """Approve the request"""
        self.status = 'approved'
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.save()
    
    def reject(self, rejected_by, reason=""):
        """Reject the request"""
        self.status = 'rejected'
        self.approved_by = rejected_by
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.save()
```

#### OnCall Models (`apps/oncall/models.py`)
```python
from django.db import models
from django.core.exceptions import ValidationError
from apps.users.models import User

class OnCallShift(models.Model):
    """On-call shift model"""
    
    SHIFT_TYPE_CHOICES = [
        ('early_primary', 'Early Primary'),
        ('late_primary', 'Late Primary'),
        ('secondary', 'Secondary'),
    ]
    
    DAY_CHOICES = [
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    shift_date = models.DateField()
    shift_type = models.CharField(max_length=20, choices=SHIFT_TYPE_CHOICES)
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    engineer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='oncall_shifts'
    )
    is_holiday_shift = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'oncall_shifts'
        ordering = ['shift_date', 'shift_type']
        unique_together = ['shift_date', 'shift_type', 'day_of_week']
        indexes = [
            models.Index(fields=['shift_date', 'engineer']),
            models.Index(fields=['engineer', 'shift_date']),
        ]
    
    def __str__(self):
        return f"{self.engineer.get_full_name()} - {self.get_shift_type_display()} on {self.shift_date}"


class DayInLieu(models.Model):
    """Days-in-lieu compensation model"""
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('used', 'Used'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='days_in_lieu'
    )
    oncall_shift = models.ForeignKey(
        OnCallShift,
        on_delete=models.CASCADE,
        related_name='days_in_lieu'
    )
    scheduled_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'days_in_lieu'
        ordering = ['scheduled_date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['scheduled_date']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.scheduled_date} ({self.status})"
```

### Step 3: Serializers

#### User Serializers (`apps/users/serializers.py`)
```python
from rest_framework import serializers
from .models import User, Team

class UserSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'team', 'team_name', 'phone_number'
        ]
        read_only_fields = ['id']

class TeamSerializer(serializers.ModelSerializer):
    coach_name = serializers.CharField(source='coach.get_full_name', read_only=True)
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = [
            'id', 'name', 'coach', 'coach_name',
            'max_concurrent_off', 'member_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_member_count(self, obj):
        return obj.members.count()
```

### Step 4: Business Logic Services

#### Conflict Detection Service (`apps/timeoff/services.py`)
```python
from datetime import timedelta
from django.db.models import Q, Count
from .models import TimeOffRequest
from apps.oncall.models import DayInLieu

class TimeOffService:
    """Business logic for time-off management"""
    
    @staticmethod
    def check_conflicts(user, start_date, end_date, exclude_request_id=None):
        """
        Check for conflicts with team availability limits
        Returns: (has_conflict, conflict_dates, message)
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
            message = f"Conflict detected: {len(conflict_dates)} day(s) exceed team limit of {max_off} members off"
        
        return has_conflict, conflict_dates, message
    
    @staticmethod
    def get_team_availability(team, start_date, end_date):
        """Get team availability for date range"""
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
            available = team.members.count() - total_off
            
            availability[current_date.isoformat()] = {
                'total_members': team.members.count(),
                'off_count': total_off,
                'available': available,
                'at_limit': total_off >= team.max_concurrent_off
            }
            
            current_date += timedelta(days=1)
        
        return availability
```

#### On-Call Rotation Service (`apps/oncall/services.py`)
```python
from datetime import datetime, timedelta
from django.db.models import Count, Q
from .models import OnCallShift
from apps.users.models import User
from apps.timeoff.models import TimeOffRequest

class OnCallRotationService:
    """Business logic for on-call rotation generation"""
    
    @staticmethod
    def get_saturdays_in_range(start_date, end_date):
        """Get all Saturdays in date range"""
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
        """Check if engineer is available on given date"""
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
        from apps.oncall.models import DayInLieu
        has_dil = DayInLieu.objects.filter(
            user=engineer,
            scheduled_date=date,
            status='scheduled'
        ).exists()
        
        return not has_dil
    
    @staticmethod
    def get_engineer_shift_count(engineer, since_date=None):
        """Get total shifts for engineer"""
        query = OnCallShift.objects.filter(engineer=engineer)
        if since_date:
            query = query.filter(shift_date__gte=since_date)
        return query.count()
    
    @staticmethod
    def select_engineer_for_shift(available_engineers, shift_type, saturday, recent_assignments):
        """
        Select best engineer for shift based on:
        1. Availability
        2. Fairness (least recent shifts)
        3. Not assigned to recent weekends
        """
        candidates = []
        
        for engineer in available_engineers:
            # Check availability for both Saturday and Sunday
            sunday = saturday + timedelta(days=1)
            
            if not OnCallRotationService.is_engineer_available(engineer, saturday):
                continue
            if not OnCallRotationService.is_engineer_available(engineer, sunday):
                continue
            
            # Check if assigned to recent weekend
            if engineer.id in recent_assignments:
                continue
            
            # Get shift count for fairness
            shift_count = OnCallRotationService.get_engineer_shift_count(engineer)
            
            candidates.append({
                'engineer': engineer,
                'shift_count': shift_count
            })
        
        if not candidates:
            return None
        
        # Sort by shift count (fairness)
        candidates.sort(key=lambda x: x['shift_count'])
        
        return candidates[0]['engineer']
    
    @staticmethod
    def generate_rotation(start_date, end_date, team=None):
        """
        Generate on-call rotation for date range
        Returns: (success, shifts_created, errors)
        """
        saturdays = OnCallRotationService.get_saturdays_in_range(start_date, end_date)
        
        if not saturdays:
            return False, [], ["No Saturdays found in date range"]
        
        # Get available engineers
        engineers_query = User.objects.filter(role='engineer', is_active=True)
        if team:
            engineers_query = engineers_query.filter(team=team)
        
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
                shifts_created.append(OnCallShift.objects.create(
                    shift_date=saturday,
                    shift_type='early_primary',
                    day_of_week='saturday',
                    engineer=early_engineer
                ))
                
                shifts_created.append(OnCallShift.objects.create(
                    shift_date=saturday,
                    shift_type='late_primary',
                    day_of_week='saturday',
                    engineer=late_engineer
                ))
                
                shifts_created.append(OnCallShift.objects.create(
                    shift_date=saturday,
                    shift_type='secondary',
                    day_of_week='saturday',
                    engineer=secondary_engineer
                ))
                
                # Sunday shifts
                shifts_created.append(OnCallShift.objects.create(
                    shift_date=sunday,
                    shift_type='early_primary',
                    day_of_week='sunday',
                    engineer=early_engineer
                ))
                
                shifts_created.append(OnCallShift.objects.create(
                    shift_date=sunday,
                    shift_type='late_primary',
                    day_of_week='sunday',
                    engineer=late_engineer
                ))
                
                # Track recent assignments (avoid consecutive weekends)
                recent_assignments.add(early_engineer.id)
                recent_assignments.add(late_engineer.id)
                recent_assignments.add(secondary_engineer.id)
                
                # Clear old assignments (keep last 2 weekends)
                if len(recent_assignments) > 6:
                    recent_assignments.clear()
                
            except Exception as e:
                errors.append(f"Error creating shifts for {saturday}: {str(e)}")
        
        success = len(shifts_created) > 0
        return success, shifts_created, errors
```

---

## Phase 2: Frontend Foundation

### React Project Setup

```bash
cd ..  # Back to calendar-app root
npx create-react-app frontend
cd frontend

# Install dependencies
npm install react-router-dom @reduxjs/toolkit react-redux axios
npm install @mui/material @mui/icons-material @emotion/react @emotion/styled
npm install @fullcalendar/react @fullcalendar/daygrid @fullcalendar/interaction
npm install react-hook-form date-fns
```

### API Service Setup (`src/services/api.js`)

```javascript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

## Best Practices

### Backend Best Practices

1. **Use Django's ORM efficiently**
   - Use `select_related()` for foreign keys
   - Use `prefetch_related()` for many-to-many
   - Add database indexes for frequently queried fields

2. **Implement proper validation**
   - Use model `clean()` methods
   - Use serializer validation
   - Return clear error messages

3. **Write comprehensive tests**
   - Test models, views, and services
   - Use fixtures for test data
   - Test edge cases and error conditions

4. **Security considerations**
   - Use Django's built-in security features
   - Implement proper permission checks
   - Validate all user input
   - Use HTTPS in production

### Frontend Best Practices

1. **Component organization**
   - Keep components small and focused
   - Use composition over inheritance
   - Separate presentational and container components

2. **State management**
   - Use Redux for global state
   - Use local state for component-specific data
   - Normalize state shape

3. **Performance optimization**
   - Use React.memo for expensive components
   - Implement code splitting
   - Lazy load routes and components
   - Optimize re-renders

4. **Error handling**
   - Implement error boundaries
   - Show user-friendly error messages
   - Log errors for debugging

---

## Testing Strategy

### Backend Testing Example

```python
# apps/timeoff/tests/test_services.py
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User, Team
from apps.timeoff.models import TimeOffRequest
from apps.timeoff.services import TimeOffService

class TimeOffServiceTest(TestCase):
    def setUp(self):
        # Create test team
        self.team = Team.objects.create(
            name="Test Team",
            max_concurrent_off=2
        )
        
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            team=self.team
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            team=self.team
        )
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@test.com',
            team=self.team
        )
    
    def test_conflict_detection_no_conflict(self):
        """Test that no conflict is detected when under limit"""
        start_date = timezone.now().date() + timedelta(days=1)
        end_date = start_date + timedelta(days=2)
        
        # Create one approved request
        TimeOffRequest.objects.create(
            user=self.user1,
            start_date=start_date,
            end_date=end_date,
            status='approved'
        )
        
        # Check for conflict with second request
        has_conflict, dates, message = TimeOffService.check_conflicts(
            self.user2, start_date, end_date
        )
        
        self.assertFalse(has_conflict)
        self.assertEqual(len(dates), 0)
    
    def test_conflict_detection_with_conflict(self):
        """Test that conflict is detected when at limit"""
        start_date = timezone.now().date() + timedelta(days=1)
        end_date = start_date + timedelta(days=2)
        
        # Create two approved requests (at limit)
        TimeOffRequest.objects.create(
            user=self.user1,
            start_date=start_date,
            end_date=end_date,
            status='approved'
        )
        TimeOffRequest.objects.create(
            user=self.user2,
            start_date=start_date,
            end_date=end_date,
            status='approved'
        )
        
        # Check for conflict with third request
        has_conflict, dates, message = TimeOffService.check_conflicts(
            self.user3, start_date, end_date
        )
        
        self.assertTrue(has_conflict)
        self.assertEqual(len(dates), 3)  # 3 days in range
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] Security audit completed

### Deployment Steps
- [ ] Backup production database
- [ ] Deploy backend code
- [ ] Run database migrations
- [ ] Deploy frontend build
- [ ] Update environment variables
- [ ] Restart services
- [ ] Verify deployment
- [ ] Monitor logs

### Post-Deployment
- [ ] Smoke tests passed
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Verify user access
- [ ] Update documentation

---

## Conclusion

This implementation guide provides the foundation for building the Calendar application. Follow the phased approach, implement comprehensive tests, and adhere to best practices for a robust, maintainable system.

For questions or clarifications, refer to the technical specification document or consult with the development team.