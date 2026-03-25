from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import User


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

