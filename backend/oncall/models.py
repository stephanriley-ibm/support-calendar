from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.fields import JSONField
from users.models import User
import json


class Holiday(models.Model):
    """Holiday model for tracking company holidays"""
    
    name = models.CharField(
        max_length=100,
        help_text="Name of the holiday (e.g., 'Christmas Day', 'Independence Day')"
    )
    date = models.DateField(
        help_text="Date of the holiday"
    )
    description = models.TextField(
        blank=True,
        help_text="Additional information about the holiday"
    )
    requires_coverage = models.BooleanField(
        default=True,
        help_text="Whether this holiday requires on-call coverage"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'holidays'
        ordering = ['date']
        unique_together = ['name', 'date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['requires_coverage', 'date']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.date}"
    
    @property
    def is_past(self):
        """Check if holiday is in the past"""
        return self.date < timezone.now().date()
    
    def save(self, *args, **kwargs):
        """Override save to track if date changed"""
        if self.pk:  # Existing holiday
            old_holiday = Holiday.objects.get(pk=self.pk)
            self._date_changed = old_holiday.date != self.date
        else:
            self._date_changed = False
        super().save(*args, **kwargs)


class OnCallProvider(models.Model):
    """Configuration for external on-call scheduling providers"""
    
    PROVIDER_TYPE_CHOICES = [
        ('pagerduty', 'PagerDuty'),
        ('opsgenie', 'Opsgenie'),
        ('custom', 'Custom Provider'),
    ]
    
    name = models.CharField(
        max_length=100,
        help_text="Provider name (e.g., 'Production PagerDuty')"
    )
    provider_type = models.CharField(
        max_length=50,
        choices=PROVIDER_TYPE_CHOICES,
        help_text="Type of provider"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this provider is active"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary provider for sync"
    )
    
    # Configuration stored as JSON
    config = models.JSONField(
        default=dict,
        help_text="Provider configuration (API keys, schedule IDs, etc.)"
    )
    
    # Sync settings
    auto_sync_enabled = models.BooleanField(
        default=True,
        help_text="Enable automatic sync"
    )
    sync_frequency_hours = models.IntegerField(
        default=24,
        help_text="Sync frequency in hours"
    )
    sync_lookback_days = models.IntegerField(
        default=7,
        help_text="Days to look back when syncing"
    )
    sync_lookahead_days = models.IntegerField(
        default=90,
        help_text="Days to look ahead when syncing"
    )
    
    # Sync status
    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful sync time"
    )
    last_sync_status = models.CharField(
        max_length=20,
        default='never',
        help_text="Status of last sync"
    )
    last_sync_error = models.TextField(
        blank=True,
        help_text="Error message from last sync"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'oncall_providers'
        ordering = ['-is_primary', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"
    
    def get_config_value(self, key, default=None):
        """Safely get configuration value"""
        return self.config.get(key, default)
    
    def set_config_value(self, key, value):
        """Set configuration value"""
        self.config[key] = value
        self.save()


class ExternalUserMapping(models.Model):
    """Maps external provider users to local application users"""
    
    provider = models.ForeignKey(
        OnCallProvider,
        on_delete=models.CASCADE,
        related_name='user_mappings',
        help_text="Provider this mapping belongs to"
    )
    external_user_id = models.CharField(
        max_length=100,
        help_text="User ID in external provider"
    )
    external_email = models.EmailField(
        help_text="User email in external provider"
    )
    external_name = models.CharField(
        max_length=200,
        help_text="User name in external provider"
    )
    
    local_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='external_mappings',
        help_text="Local user this maps to"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this mapping is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'external_user_mappings'
        unique_together = ['provider', 'external_user_id']
        indexes = [
            models.Index(fields=['provider', 'external_user_id']),
            models.Index(fields=['local_user']),
        ]
    
    def __str__(self):
        return f"{self.external_name} ({self.provider.name}) → {self.local_user.get_full_name()}"


class ProviderSyncLog(models.Model):
    """Log of provider sync operations"""
    
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('success', 'Success'),
        ('partial', 'Partial Success'),
        ('failed', 'Failed'),
    ]
    
    provider = models.ForeignKey(
        OnCallProvider,
        on_delete=models.CASCADE,
        related_name='sync_logs',
        help_text="Provider that was synced"
    )
    sync_type = models.CharField(
        max_length=50,
        help_text="Type of sync (scheduled, manual, initial)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        help_text="Sync status"
    )
    
    start_time = models.DateTimeField(
        auto_now_add=True,
        help_text="Sync start time"
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Sync end time"
    )
    
    # Statistics
    shifts_fetched = models.IntegerField(
        default=0,
        help_text="Number of shifts fetched from provider"
    )
    shifts_created = models.IntegerField(
        default=0,
        help_text="Number of new shifts created"
    )
    shifts_updated = models.IntegerField(
        default=0,
        help_text="Number of existing shifts updated"
    )
    shifts_skipped = models.IntegerField(
        default=0,
        help_text="Number of shifts skipped"
    )
    
    error_message = models.TextField(
        blank=True,
        help_text="Error message if sync failed"
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional sync details"
    )
    
    class Meta:
        db_table = 'provider_sync_logs'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['provider', '-start_time']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.provider.name} - {self.sync_type} - {self.status} ({self.start_time})"
    
    @property
    def duration_seconds(self):
        """Calculate sync duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class OnCallShift(models.Model):
    """On-call shift model for both weekend and holiday coverage"""
    
    SHIFT_TYPE_CHOICES = [
        ('early_primary', 'Early Primary'),
        ('late_primary', 'Late Primary'),
        ('secondary', 'Secondary'),
        ('early_secondary', 'Early Secondary'),
        ('late_secondary', 'Late Secondary'),
        ('holiday', 'Holiday Coverage'),
    ]
    
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    shift_date = models.DateField(
        help_text="Date of the shift"
    )
    shift_type = models.CharField(
        max_length=20,
        choices=SHIFT_TYPE_CHOICES,
        help_text="Type of on-call shift"
    )
    day_of_week = models.CharField(
        max_length=10,
        choices=DAY_CHOICES,
        blank=True,
        help_text="Day of the week (auto-calculated from shift_date if not provided)"
    )
    engineer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='oncall_shifts',
        help_text="Engineer assigned to this shift"
    )
    holiday = models.ForeignKey(
        Holiday,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='shifts',
        help_text="Associated holiday (if this is holiday coverage)"
    )
    start_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Start time of shift (optional, for custom schedules)"
    )
    end_time = models.TimeField(
        null=True,
        blank=True,
        help_text="End time of shift (optional, for custom schedules)"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the shift"
    )
    
    # Provider tracking fields
    provider = models.ForeignKey(
        OnCallProvider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='synced_shifts',
        help_text="External provider this shift was synced from"
    )
    external_shift_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="ID in external provider system"
    )
    external_schedule_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Schedule ID in external provider system"
    )
    synced_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this shift was last synced from provider"
    )
    is_synced = models.BooleanField(
        default=False,
        help_text="Whether this shift came from an external provider"
    )
    sync_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata from provider"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'oncall_shifts'
        ordering = ['shift_date', 'shift_type']
        indexes = [
            models.Index(fields=['shift_date', 'engineer']),
            models.Index(fields=['engineer', 'shift_date']),
            models.Index(fields=['holiday']),
            models.Index(fields=['shift_type', 'shift_date']),
            models.Index(fields=['provider', 'external_shift_id']),
            models.Index(fields=['is_synced', 'shift_date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['provider', 'external_shift_id'],
                condition=models.Q(provider__isnull=False, external_shift_id__isnull=False),
                name='unique_provider_shift'
            ),
        ]
    
    def __str__(self):
        if self.holiday:
            return f"{self.engineer.get_full_name()} - Holiday Coverage ({self.holiday.name}) on {self.shift_date}"
        return f"{self.engineer.get_full_name()} - {self.get_shift_type_display()} on {self.shift_date}"
    
    def clean(self):
        """Validate on-call shift"""
        if self.shift_date:
            # Auto-set day_of_week based on shift_date
            day_map = {
                0: 'monday',
                1: 'tuesday',
                2: 'wednesday',
                3: 'thursday',
                4: 'friday',
                5: 'saturday',
                6: 'sunday',
            }
            expected_day = day_map[self.shift_date.weekday()]
            if not self.day_of_week:
                self.day_of_week = expected_day
            elif self.day_of_week != expected_day:
                raise ValidationError(f"Day of week '{self.day_of_week}' doesn't match shift date {self.shift_date}")
        
        # Validate holiday shifts
        if self.shift_type == 'holiday' and not self.holiday:
            raise ValidationError("Holiday shifts must be associated with a Holiday")
        
        # Validate weekend shifts
        if self.shift_type in ['early_primary', 'late_primary', 'secondary', 'early_secondary', 'late_secondary']:
            if self.day_of_week not in ['saturday', 'sunday']:
                raise ValidationError(f"{self.get_shift_type_display()} shifts are only for weekends")
    
    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_weekend_shift(self):
        """Check if this is a weekend shift"""
        return self.day_of_week in ['saturday', 'sunday'] and self.shift_type != 'holiday'
    
    @property
    def is_holiday_shift(self):
        """Check if this is a holiday shift"""
        return self.shift_type == 'holiday' or self.holiday is not None


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
        related_name='days_in_lieu',
        help_text="User receiving the day in lieu"
    )
    oncall_shift = models.ForeignKey(
        OnCallShift,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='days_in_lieu',
        help_text="The on-call shift this compensates for (optional for manually created days)"
    )
    scheduled_date = models.DateField(
        help_text="Date the day in lieu is scheduled for"
    )
    original_scheduled_date = models.DateField(
        null=True,
        blank=True,
        help_text="Original scheduled date (if adjusted by coach)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        help_text="Current status of the day in lieu"
    )
    is_manually_created = models.BooleanField(
        default=False,
        help_text="Whether this was manually created by a coach (not auto-generated)"
    )
    adjusted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='adjusted_days_in_lieu',
        help_text="Coach who adjusted this day in lieu"
    )
    adjusted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the day was adjusted"
    )
    adjustment_reason = models.TextField(
        blank=True,
        help_text="Reason for adjustment (if applicable)"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the day was used"
    )
    
    class Meta:
        db_table = 'days_in_lieu'
        ordering = ['scheduled_date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['status', 'scheduled_date']),
            models.Index(fields=['is_manually_created']),
        ]
        verbose_name_plural = 'Days in lieu'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.scheduled_date} ({self.get_status_display()})"
    
    def reschedule(self, new_date, adjusted_by, reason=""):
        """Reschedule the day in lieu to a new date"""
        if not self.original_scheduled_date:
            self.original_scheduled_date = self.scheduled_date
        self.scheduled_date = new_date
        self.adjusted_by = adjusted_by
        self.adjusted_at = timezone.now()
        self.adjustment_reason = reason
        self.save()
    
    def mark_as_used(self):
        """Mark the day in lieu as used"""
        self.status = 'used'
        self.used_at = timezone.now()
        self.save()
    
    def cancel(self):
        """Cancel the day in lieu"""
        self.status = 'cancelled'
        self.save()
    
    def mark_as_expired(self):
        """Mark the day in lieu as expired"""
        self.status = 'expired'
        self.save()
    
    @property
    def is_scheduled(self):
        """Check if day is scheduled"""
        return self.status == 'scheduled'
    
    @property
    def is_used(self):
        """Check if day has been used"""
        return self.status == 'used'
    
    @property
    def is_expired(self):
        """Check if day has expired"""
        return self.status == 'expired'
    
    @property
    def was_adjusted(self):
        """Check if this day was adjusted from its original date"""
        return self.original_scheduled_date is not None

# Made with Bob

# Signal handler to update holiday shifts when holiday date changes
@receiver(post_save, sender=Holiday)
def update_holiday_shifts_on_date_change(sender, instance, **kwargs):
    """
    When a holiday's date is changed, update all associated shifts to the new date.
    This ensures holiday shifts stay synchronized with their holiday dates.
    """
    if hasattr(instance, '_date_changed') and instance._date_changed:
        # Update all shifts associated with this holiday
        shifts = OnCallShift.objects.filter(holiday=instance, shift_type='holiday')
        for shift in shifts:
            shift.shift_date = instance.date
            # Recalculate day_of_week based on new date
            day_map = {0: 'monday', 1: 'tuesday', 2: 'wednesday', 3: 'thursday', 
                      4: 'friday', 5: 'saturday', 6: 'sunday'}
            shift.day_of_week = day_map[instance.date.weekday()]
            shift.save()

