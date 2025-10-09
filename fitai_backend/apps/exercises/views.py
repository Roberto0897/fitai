from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import Exercise

@api_view(['GET'])
def test_exercises_api(request):
    return Response({"message": "Exercises API funcionando!"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_exercises(request):
    """Lista todos os exercícios disponíveis"""
    exercises = Exercise.objects.all()
    data = []
    
    for exercise in exercises:
        data.append({
            'id': exercise.id,
            'name': exercise.name,
            'description': exercise.description,
            'muscle_group': exercise.muscle_group,
            'difficulty_level': exercise.difficulty_level,
            'equipment_needed': exercise.equipment_needed,
            'duration_minutes': exercise.duration_minutes,
            'calories_per_minute': exercise.calories_per_minute,
            'video_url': exercise.video_url,
            'instructions': exercise.instructions,
        })
    
    return Response({
        'exercises': data,
        'total': len(data)
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def exercises_by_muscle_group(request):
    """Lista exercícios por grupo muscular"""
    muscle_group = request.GET.get('muscle_group')
    
    if not muscle_group:
        return Response({"error": "Parâmetro muscle_group é obrigatório"}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    exercises = Exercise.objects.filter(muscle_group=muscle_group)
    data = []
    
    for exercise in exercises:
        data.append({
            'id': exercise.id,
            'name': exercise.name,
            'description': exercise.description,
            'difficulty_level': exercise.difficulty_level,
            'equipment_needed': exercise.equipment_needed,
            'duration_minutes': exercise.duration_minutes,
            'video_url': exercise.video_url,
            'instructions': exercise.instructions,
        })
    
    return Response({
        'muscle_group': muscle_group,
        'exercises': data,
        'total': len(data)
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_exercises(request):
    """Busca exercícios por nome ou descrição"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return Response({"error": "Query deve ter pelo menos 2 caracteres"}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    exercises = Exercise.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    )
    
    data = []
    for exercise in exercises:
        data.append({
            'id': exercise.id,
            'name': exercise.name,
            'description': exercise.description,
            'muscle_group': exercise.muscle_group,
            'difficulty_level': exercise.difficulty_level,
            'video_url': exercise.video_url,
        })
    
    return Response({
        'query': query,
        'exercises': data,
        'total': len(data)
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def exercise_detail(request, exercise_id):
    """Detalhes completos de um exercício"""
    try:
        exercise = Exercise.objects.get(id=exercise_id)
        
        return Response({
            'id': exercise.id,
            'name': exercise.name,
            'description': exercise.description,
            'muscle_group': exercise.muscle_group,
            'difficulty_level': exercise.difficulty_level,
            'equipment_needed': exercise.equipment_needed,
            'duration_minutes': exercise.duration_minutes,
            'calories_per_minute': exercise.calories_per_minute,
            'instructions': exercise.instructions,
            'video_url': exercise.video_url,
        })
    except Exercise.DoesNotExist:
        return Response({"error": "Exercício não encontrado"}, 
                       status=status.HTTP_404_NOT_FOUND)