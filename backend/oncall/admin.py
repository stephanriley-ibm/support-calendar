from django.contrib import admin
from .models import Holiday, OnCallShift, DayInLieu


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    """Admin interface for Holiday model"""
    
    list_display = ['name', 'date', 'requires_coverage', 'is_past', 'created_at']
    list_filter = ['requires_coverage', 'date']
    search_fields = ['name', 'description']
    ordering = ['-date']
    date_hierarchy = 'date'
    
    fieldsets = (
        (None, {
            'fields': ('name', 'date', 'requires_coverage', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(OnCallShift)
class OnCallShiftAdmin(admin.ModelAdmin):
    """Admin interface for OnCallShift model"""
    
    list_display = [
        'shift_date',
        'day_of_week',
        'shift_type',
        'engineer',
        'holiday',
        'is_holiday_shift',
        'created_at'
    ]
    list_filter = ['shift_type', 'day_of_week', 'holiday', 'shift_date']
    search_fields = [
        'engineer__username',
        'engineer__first_name',
        'engineer__last_name',
        'notes'
    ]
    ordering = ['-shift_date', 'shift_type']
    date_hierarchy = 'shift_date'
    
    fieldsets = (
        ('Shift Information', {
            'fields': ('shift_date', 'day_of_week', 'shift_type', 'engineer')
        }),
        ('Holiday Coverage', {
            'fields': ('holiday',),
            'classes': ('collapse',)
        }),
        ('Time Details', {
            'fields': ('start_time', 'end_time'),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def is_holiday_shift(self, obj):
        """Display if this is a holiday shift"""
        return obj.is_holiday_shift
    is_holiday_shift.boolean = True
    is_holiday_shift.short_description = 'Holiday Shift'


@admin.register(DayInLieu)
class DayInLieuAdmin(admin.ModelAdmin):
    """Admin interface for DayInLieu model"""
    
    list_display = [
        'user',
        'scheduled_date',
        'original_scheduled_date',
        'status',
        'oncall_shift',
        'is_manually_created',
        'was_adjusted',
        'created_at'
    ]
    list_filter = ['status', 'is_manually_created', 'scheduled_date']
    search_fields = [
        'user__username',
        'user__first_name',
        'user__last_name',
        'notes',
        'adjustment_reason'
    ]
    ordering = ['-scheduled_date']
    date_hierarchy = 'scheduled_date'
    
    fieldsets = (
        ('Day In Lieu Information', {
            'fields': ('user', 'oncall_shift', 'scheduled_date', 'status')
        }),
        ('Manual Creation', {
            'fields': ('is_manually_created',),
            'classes': ('collapse',)
        }),
        ('Adjustment Information', {
            'fields': (
                'original_scheduled_date',
                'adjusted_by',
                'adjusted_at',
                'adjustment_reason'
            ),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'used_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'used_at', 'adjusted_at']
    
    actions = ['mark_as_used', 'mark_as_expired', 'cancel_days']
    
    def mark_as_used(self, request, queryset):
        """Bulk mark days as used"""
        count = 0
        for day in queryset.filter(status='scheduled'):
            day.mark_as_used()
            count += 1
        self.message_user(request, f'{count} day(s) in lieu marked as used.')
    mark_as_used.short_description = 'Mark selected days as used'
    
    def mark_as_expired(self, request, queryset):
        """Bulk mark days as expired"""
        count = 0
        for day in queryset.filter(status='scheduled'):
            day.mark_as_expired()
            count += 1
        self.message_user(request, f'{count} day(s) in lieu marked as expired.')
    mark_as_expired.short_description = 'Mark selected days as expired'
    
    def cancel_days(self, request, queryset):
        """Bulk cancel days"""
        count = 0
        for day in queryset.filter(status='scheduled'):
            day.cancel()
            count += 1
        self.message_user(request, f'{count} day(s) in lieu cancelled.')
    cancel_days.short_description = 'Cancel selected days'
    
    def was_adjusted(self, obj):
        """Display if day was adjusted"""
        return obj.was_adjusted
    was_adjusted.boolean = True
    was_adjusted.short_description = 'Adjusted'

# Made with Bob
