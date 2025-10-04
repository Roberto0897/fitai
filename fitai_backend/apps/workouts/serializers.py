"""
Serializers para treinos
"""
from rest_framework import serializers
from .models import Workout, WorkoutExercise, WorkoutSession
from apps.exercises.serializers import ExerciseSerializer  # ← MUDOU AQUI


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    """Serializer para exercícios dentro do treino"""
    exercise = ExerciseSerializer(read_only=True)  # ← MUDOU AQUI
    
    class Meta:
        model = WorkoutExercise
        fields = ['exercise', 'series', 'repeticoes', 'peso_sugerido', 'tempo_descanso', 'ordem']


class WorkoutSerializer(serializers.ModelSerializer):
    """Serializer para treinos"""
    exercises = WorkoutExerciseSerializer(source='workoutexercise_set', many=True, read_only=True)
    
    class Meta:
        model = Workout
        fields = '__all__'


class WorkoutListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para lista de treinos"""
    
    class Meta:
        model = Workout
        fields = [
            'id', 'nome', 'categoria', 'tipo_treino', 'nivel_dificuldade', 
            'duracao_estimada', 'calorias_estimadas', 'popularidade'
        ]


class WorkoutSessionSerializer(serializers.ModelSerializer):
    """Serializer para sessões de treino"""
    workout = WorkoutListSerializer(read_only=True)
    
    class Meta:
        model = WorkoutSession
        fields = '__all__'