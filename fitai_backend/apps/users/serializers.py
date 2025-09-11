# apps/users/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, UserProgress, DailyTip

class UserSerializer(serializers.ModelSerializer):
    """Serializer básico do usuário"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['date_joined']

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer para registro de novos usuários"""
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 6},
            'email': {'required': True}
        }
    
    def validate(self, data):
        """Valida se as senhas coincidem"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("As senhas não coincidem")
        return data
    
    def validate_email(self, value):
        """Valida se o email já não está em uso"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email já está em uso")
        return value
    
    def validate_username(self, value):
        """Valida se o username já não está em uso"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este username já está em uso")
        return value
    
    def create(self, validated_data):
        """Cria o usuário"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para perfil do usuário"""
    bmi = serializers.ReadOnlyField()
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'username', 'date_of_birth', 'gender', 'height', 'weight', 'bmi',
            'goal', 'activity_level', 'focus_areas', 'onboarding_completed',
            'bio', 'location', 'phone', 'experience_level', 'preferred_workout_duration',
            'available_equipment', 'workout_frequency', 'notifications_enabled', 
            'reminder_time', 'created_at', 'updated_at'
        ]
        read_only_fields = ['bmi', 'created_at', 'updated_at']

class UserProgressSerializer(serializers.ModelSerializer):
    """Serializer para progresso do usuário"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserProgress
        fields = [
            'id', 'user', 'username', 'current_weight', 'target_weight',
            'total_workouts', 'total_exercise_time', 'calories_burned',
            'current_streak', 'longest_streak', 'last_workout',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class DailyTipSerializer(serializers.ModelSerializer):
    """Serializer para dicas diárias"""
    
    class Meta:
        model = DailyTip
        fields = [
            'id', 'title', 'content', 'category', 'target_level',
            'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']

# Serializers simplificados para listas
class UserProfileListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas de perfis"""
    username = serializers.CharField(source='user.username', read_only=True)
    bmi = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'username', 'goal', 'activity_level', 'experience_level',
            'onboarding_completed', 'bmi'
        ]

class UserProgressListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas de progresso"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserProgress
        fields = [
            'id', 'username', 'total_workouts', 'current_streak',
            'calories_burned', 'last_workout'
        ]