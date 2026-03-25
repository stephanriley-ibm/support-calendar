from rest_framework import serializers
from .models import Holiday, OnCallShift, DayInLieu


class HolidaySerializer(serializers.ModelSerializer):
    """Serializer for Holiday model"""
    
    is_past = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Holiday
        fields = [
            'id',
            'name',
            'date',
            'description',
            'requires_coverage',
            'is_past',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OnCallShiftSerializer(serializers.ModelSerializer):
    """Serializer for OnCallShift model"""
    
    engineer_name = serializers.CharField(source='engineer.get_full_name', read_only=True)
    holiday_name = serializers.CharField(source='holiday.name', read_only=True)
    shift_type_display = serializers.CharField(source='get_shift_type_display', read_only=True)
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    is_weekend_shift = serializers.BooleanField(read_only=True)
    is_holiday_shift = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = OnCallShift
        fields = [
            'id',
            'shift_date',
            'shift_type',
            'shift_type_display',
            'day_of_week',
            'day_of_week_display',
            'engineer',
            'engineer_name',
            'holiday',
            'holiday_name',
            'start_time',
            'end_time',
            'notes',
            'is_weekend_shift',
            'is_holiday_shift',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OnCallShiftCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating on-call shifts"""
    
    class Meta:
        model = OnCallShift
        fields = [
            'shift_date',
            'shift_type',
            'engineer',
            'holiday',
            'start_time',
            'end_time',
            'notes',
        ]
    
    def validate(self, attrs):
        """Validate shift creation"""
        # Validate holiday shifts
        if attrs['shift_type'] == 'holiday' and not attrs.get('holiday'):
            raise serializers.ValidationError({
                'holiday': 'Holiday shifts must be associated with a Holiday.'
            })
        
        # Validate weekend shifts
        if attrs['shift_type'] in ['early_primary', 'late_primary', 'secondary']:
            day_of_week = attrs['shift_date'].weekday()
            if day_of_week not in [5, 6]:  # Saturday=5, Sunday=6
                raise serializers.ValidationError({
                    'shift_date': f'{attrs["shift_type"]} shifts are only for weekends.'
                })
        
        return attrs


class OnCallShiftListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing on-call shifts"""
    
    engineer_name = serializers.CharField(source='engineer.get_full_name', read_only=True)
    shift_type_display = serializers.CharField(source='get_shift_type_display', read_only=True)
    
    class Meta:
        model = OnCallShift
        fields = [
            'id',
            'shift_date',
            'shift_type',
            'shift_type_display',
            'day_of_week',
            'engineer',
            'engineer_name',
            'holiday',
        ]


class DayInLieuSerializer(serializers.ModelSerializer):
    """Serializer for DayInLieu model"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    adjusted_by_name = serializers.CharField(source='adjusted_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    was_adjusted = serializers.BooleanField(read_only=True)
    shift_info = serializers.SerializerMethodField()
    
    class Meta:
        model = DayInLieu
        fields = [
            'id',
            'user',
            'user_name',
            'oncall_shift',
            'shift_info',
            'scheduled_date',
            'original_scheduled_date',
            'status',
            'status_display',
            'is_manually_created',
            'adjusted_by',
            'adjusted_by_name',
            'adjusted_at',
            'adjustment_reason',
            'notes',
            'was_adjusted',
            'created_at',
            'used_at',
        ]
        read_only_fields = [
            'id',
            'adjusted_by',
            'adjusted_at',
            'created_at',
            'used_at',
        ]
    
    def get_shift_info(self, obj):
        """Get basic shift information"""
        if obj.oncall_shift:
            return {
                'date': obj.oncall_shift.shift_date,
                'type': obj.oncall_shift.get_shift_type_display(),
            }
        return None


class DayInLieuCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating days in lieu (manual creation by coach)"""
    
    class Meta:
        model = DayInLieu
        fields = [
            'user',
            'scheduled_date',
            'notes',
        ]
    
    def create(self, validated_data):
        """Create manually created day in lieu"""
        validated_data['is_manually_created'] = True
        return super().create(validated_data)


class DayInLieuRescheduleSerializer(serializers.Serializer):
    """Serializer for rescheduling days in lieu"""
    
    new_date = serializers.DateField(required=True)
    reason = serializers.CharField(required=True, allow_blank=False)
    
    def validate_new_date(self, value):
        """Validate new date is in the future"""
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError('New date must be in the future.')
        return value


class DayInLieuListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing days in lieu"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    team_name = serializers.CharField(source='user.team.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DayInLieu
        fields = [
            'id',
            'user',
            'user_name',
            'team_name',
            'scheduled_date',
            'status',
            'status_display',
            'is_manually_created',
            'created_at',
        ]

# Made with Bob
