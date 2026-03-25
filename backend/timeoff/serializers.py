from rest_framework import serializers
from .models import TimeOffRequest
from users.serializers import UserSerializer


class TimeOffRequestSerializer(serializers.ModelSerializer):
    """Serializer for TimeOffRequest model"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    duration_days = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = TimeOffRequest
        fields = [
            'id',
            'user',
            'user_name',
            'start_date',
            'end_date',
            'duration_days',
            'status',
            'status_display',
            'reason',
            'approved_by',
            'approved_by_name',
            'approved_at',
            'rejection_reason',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'approved_by',
            'approved_at',
            'created_at',
            'updated_at',
        ]


class TimeOffRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating time-off requests"""
    
    class Meta:
        model = TimeOffRequest
        fields = [
            'start_date',
            'end_date',
            'reason',
        ]
    
    def validate(self, attrs):
        """Validate date range and check for overlapping requests"""
        if attrs['start_date'] > attrs['end_date']:
            raise serializers.ValidationError({
                'end_date': 'End date must be after or equal to start date.'
            })
        
        # Check for overlapping time-off requests for the same user
        user = self.context['request'].user
        overlapping = TimeOffRequest.objects.filter(
            user=user,
            start_date__lte=attrs['end_date'],
            end_date__gte=attrs['start_date']
        ).exclude(status='rejected')
        
        if overlapping.exists():
            raise serializers.ValidationError({
                'non_field_errors': 'You already have a time-off request for these dates. Please check your existing requests.'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create request with current user"""
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class TimeOffRequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating time-off requests"""
    
    class Meta:
        model = TimeOffRequest
        fields = [
            'start_date',
            'end_date',
            'reason',
        ]
    
    def validate(self, attrs):
        """Validate date range and status"""
        instance = self.instance
        
        # Only allow updates to pending requests
        if instance.status != 'pending':
            raise serializers.ValidationError(
                'Only pending requests can be updated.'
            )
        
        start_date = attrs.get('start_date', instance.start_date)
        end_date = attrs.get('end_date', instance.end_date)
        
        if start_date > end_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after or equal to start date.'
            })
        
        return attrs


class TimeOffRequestApprovalSerializer(serializers.Serializer):
    """Serializer for approving/rejecting time-off requests"""
    
    action = serializers.ChoiceField(choices=['approve', 'reject'], required=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validate rejection reason"""
        if attrs['action'] == 'reject' and not attrs.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason is required when rejecting a request.'
            })
        return attrs


class TimeOffRequestListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing time-off requests"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    team_name = serializers.CharField(source='user.team.name', read_only=True)
    duration_days = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = TimeOffRequest
        fields = [
            'id',
            'user',
            'user_name',
            'team_name',
            'start_date',
            'end_date',
            'duration_days',
            'reason',
            'status',
            'status_display',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

# Made with Bob
