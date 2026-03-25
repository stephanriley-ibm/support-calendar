from rest_framework import serializers
from .models import User, Team
import secrets
import string


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    username = serializers.CharField(read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'team',
            'team_name',
            'is_active',
            'oncall_eligible',
            'timezone',
            'date_joined',
            'must_change_password',
        ]
        read_only_fields = ['id', 'username', 'date_joined', 'must_change_password']
    
    def get_full_name(self, obj):
        """Get user's full name"""
        return obj.get_full_name() or obj.username


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users"""
    
    username = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=False, allow_blank=True, style={'input_type': 'password'})
    temp_password = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'role',
            'team',
            'oncall_eligible',
            'temp_password',
        ]
    
    def validate(self, attrs):
        """Validate password confirmation if provided"""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        return attrs
    
    def generate_temp_password(self):
        """Generate a random temporary password"""
        # Generate 12 character password with letters and digits
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for i in range(12))
    
    def create(self, validated_data):
        """Create user with hashed password or temporary password"""
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        
        # Generate username from email if not provided
        if 'username' not in validated_data or not validated_data['username']:
            email = validated_data.get('email', '')
            username = email.split('@')[0] if '@' in email else email
            validated_data['username'] = username
        
        user = User.objects.create(**validated_data)
        
        if password:
            # Use provided password
            user.set_password(password)
            user.must_change_password = False
            user.temp_password = None
        else:
            # Generate temporary password
            temp_password = self.generate_temp_password()
            user.set_password(temp_password)
            user.temp_password = temp_password
            user.must_change_password = True
        
        user.save()
        return user
    
    def to_representation(self, instance):
        """Include temp_password in response if it exists"""
        data = super().to_representation(instance)
        # Only include temp_password if it was just set (not from database)
        if hasattr(instance, 'temp_password') and instance.temp_password:
            data['temp_password'] = instance.temp_password
        return data


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users"""
    
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'team',
            'is_active',
            'oncall_eligible',
            'timezone',
        ]


class TeamSerializer(serializers.ModelSerializer):
    """Serializer for Team model"""
    
    coach_name = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    members = UserSerializer(many=True, read_only=True)
    
    class Meta:
        model = Team
        fields = [
            'id',
            'name',
            'coach',
            'coach_name',
            'max_concurrent_off',
            'description',
            'member_count',
            'members',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_coach_name(self, obj):
        """Get coach's full name"""
        return obj.get_coach_name()
    
    def get_member_count(self, obj):
        """Get count of team members"""
        return obj.get_member_count()


class TeamListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing teams"""
    
    coach_name = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = [
            'id',
            'name',
            'coach',
            'coach_name',
            'max_concurrent_off',
            'member_count',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_coach_name(self, obj):
        """Get coach's full name"""
        return obj.get_coach_name()
    
    def get_member_count(self, obj):
        """Get count of team members"""
        return obj.get_member_count()

# Made with Bob
