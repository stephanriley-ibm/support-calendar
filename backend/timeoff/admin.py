from django.contrib import admin
from .models import TimeOffRequest


@admin.register(TimeOffRequest)
class TimeOffRequestAdmin(admin.ModelAdmin):
    """Admin interface for TimeOffRequest model"""
    
    list_display = [
        'user',
        'start_date',
        'end_date',
        'duration_days',
        'status',
        'approved_by',
        'created_at'
    ]
    list_filter = ['status', 'start_date', 'created_at']
    search_fields = [
        'user__username',
        'user__first_name',
        'user__last_name',
        'reason'
    ]
    ordering = ['-created_at']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'start_date', 'end_date', 'reason')
        }),
        ('Status', {
            'fields': ('status', 'approved_by', 'approved_at', 'rejection_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'approved_at']
    
    def duration_days(self, obj):
        """Display duration in days"""
        return obj.duration_days
    duration_days.short_description = 'Duration (days)'
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        """Bulk approve selected requests"""
        count = 0
        for req in queryset.filter(status='pending'):
            req.approve(request.user)
            count += 1
        self.message_user(request, f'{count} request(s) approved.')
    approve_requests.short_description = 'Approve selected requests'
    
    def reject_requests(self, request, queryset):
        """Bulk reject selected requests"""
        count = 0
        for req in queryset.filter(status='pending'):
            req.reject(request.user, reason='Bulk rejection')
            count += 1
        self.message_user(request, f'{count} request(s) rejected.')
    reject_requests.short_description = 'Reject selected requests'

# Made with Bob
