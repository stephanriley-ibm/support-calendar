from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Team


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model"""
    
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'team', 'is_active']
    list_filter = ['role', 'team', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['last_name', 'first_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'team')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'team', 'email', 'first_name', 'last_name')
        }),
    )


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Admin interface for Team model"""
    
    list_display = ['name', 'coach', 'member_count', 'max_concurrent_off', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'coach__username', 'coach__first_name', 'coach__last_name']
    ordering = ['name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'coach', 'max_concurrent_off', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def member_count(self, obj):
        """Display member count in admin list"""
        return obj.get_member_count()
    member_count.short_description = 'Members'

# Made with Bob
