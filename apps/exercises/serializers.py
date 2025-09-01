# apps/exercises/serializers.py

from rest_framework import serializers
from .models import Exercise

class ExerciseSerializer(serializers.ModelSerializer):
    """Serializer completo para exercícios"""
    
    class Meta:
        model = Exercise
        fields = [
            'id', 'name', 'description', 'category', 'primary_muscle_group',
            'secondary_muscle_groups', 'difficulty_level', 'equipment_needed',
            'instructions', 'tips', 'common_mistakes', 'calories_per_minute',
            'safety_rating', 'image_url', 'video_url', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ExerciseListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas de exercícios"""
    
    class Meta:
        model = Exercise
        fields = [
            'id', 'name', 'description', 'category', 'primary_muscle_group',
            'difficulty_level', 'equipment_needed', 'calories_per_minute',
            'image_url'
        ]

class ExerciseMinimalSerializer(serializers.ModelSerializer):
    """Serializer mínimo para exercícios (usado em relacionamentos)"""
    
    class Meta:
        model = Exercise
        fields = ['id', 'name', 'primary_muscle_group', 'difficulty_level']