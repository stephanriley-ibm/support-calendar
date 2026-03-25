from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from users.models import User


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
        related_name='timeoff_requests',
        help_text="User requesting time off"
    )
    start_date = models.DateField(
        help_text="First day of time off"
    )
    end_date = models.DateField(
        help_text="Last day of time off"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the request"
    )
    reason = models.TextField(
        blank=True,
        help_text="Reason for time off (optional)"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_requests',
        help_text="Coach who approved/rejected the request"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the request was approved/rejected"
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection (if applicable)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'timeoff_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()}: {self.start_date} to {self.end_date} ({self.get_status_display()})"
    
    def clean(self):
        """Validate time-off request"""
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError("End date must be after or equal to start date")
    
    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def duration_days(self):
        """Calculate duration in days (inclusive)"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
    
    @property
    def is_pending(self):
        """Check if request is pending"""
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        """Check if request is approved"""
        return self.status == 'approved'
    
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
    
    def cancel(self):
        """Cancel the request"""
        self.status = 'cancelled'
        self.save()

# Made with Bob
