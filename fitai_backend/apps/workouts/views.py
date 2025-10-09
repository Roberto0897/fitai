from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Avg, Count
from django.utils import timezone
from .models import Workout, WorkoutExercise, WorkoutSession, ExerciseLog
from apps.users.models import UserProfile
from apps.exercises.models import Exercise
import google.generativeai as genai
from apps.recommendations.services.recommendation_engine import RecommendationEngine
from apps.recommendations.services.ai_service import AIService
import logging
from django.conf import settings
import re
import json

@api_view(['GET'])
def test_workouts_api(request):
    return Response({"message": "Workouts API funcionando!"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_workouts(request):
    """Lista todos os treinos disponíveis"""
   # workouts = Workout.objects.all()
   # SÓ TREINOS PÚBLICOS (catálogo)
    workouts = Workout.objects.filter(
        is_personalized=False  # Exclui TODOS os treinos personalizados
    )
    data = []
    
    for workout in workouts:
        # Contar exercícios no treino
        exercise_count = WorkoutExercise.objects.filter(workout=workout).count()
        
        data.append({
            'id': workout.id,
            'name': workout.name,
            'description': workout.description,
            'difficulty_level': workout.difficulty_level,
            'estimated_duration': workout.estimated_duration,
            'target_muscle_groups': workout.target_muscle_groups,
            'workout_type': workout.workout_type,
            'calories_estimate': workout.calories_estimate,
            'exercise_count': exercise_count,
            'is_recommended': workout.is_recommended
        })
    
    return Response({
        'workouts': data,
        'total': len(data)
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommended_workouts(request):
    """Treinos recomendados baseados no perfil do usuário"""
    try:
        profile = UserProfile.objects.get(user=request.user)
        
        # Filtros baseados no perfil
        #filters = Q(is_recommended=True)
        #  SÓ meus treinos IA
        filters = Q(is_recommended=True) & Q(created_by_user=request.user)#alteracao 08/10
        
        # Filtrar por nível de atividade
        if profile.activity_level:
            if profile.activity_level in ['sedentary', 'light']:
                filters &= Q(difficulty_level='beginner')
            elif profile.activity_level == 'moderate':
                filters &= Q(difficulty_level__in=['beginner', 'intermediate'])
            else:  # active, very_active
                filters &= Q(difficulty_level__in=['intermediate', 'advanced'])
        
        workouts = Workout.objects.filter(filters)[:10]  # Limitar a 10
        
        data = []
        for workout in workouts:
            exercise_count = WorkoutExercise.objects.filter(workout=workout).count()
            data.append({
                'id': workout.id,
                'name': workout.name,
                'description': workout.description,
                'difficulty_level': workout.difficulty_level,
                'estimated_duration': workout.estimated_duration,
                'workout_type': workout.workout_type,
                'calories_estimate': workout.calories_estimate,
                'exercise_count': exercise_count,
                'is_ai_generated': True, #alteracao 08/10
                'recommendation_reason': f"Recomendado para {profile.activity_level or 'seu nível'}"
            })
        
        return Response({
            'recommended_workouts': data,
            'total': len(data),
            'user_goal': profile.goal,
            'activity_level': profile.activity_level
        })
        
    except UserProfile.DoesNotExist:
        # Fallback: treinos para iniciantes
        workouts = Workout.objects.filter(difficulty_level='beginner')[:5]
        data = []
        for workout in workouts:
            exercise_count = WorkoutExercise.objects.filter(workout=workout).count()
            data.append({
                'id': workout.id,
                'name': workout.name,
                'description': workout.description,
                'difficulty_level': workout.difficulty_level,
                'estimated_duration': workout.estimated_duration,
                'exercise_count': exercise_count
            })
        
        return Response({
            'recommended_workouts': data,
            'total': len(data),
            'message': 'Complete seu perfil para recomendações personalizadas'
        })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def workout_detail(request, workout_id):
    """Detalhes completos de um treino, incluindo exercícios"""
    try:
        workout = Workout.objects.get(id=workout_id)
        workout_exercises = WorkoutExercise.objects.filter(workout=workout).order_by('order_in_workout')
        
        exercises_data = []
        for we in workout_exercises:
            exercises_data.append({
                'id': we.id,
                'exercise': {
                    'id': we.exercise.id,
                    'name': we.exercise.name,
                    'description': we.exercise.description,
                    'muscle_group': we.exercise.muscle_group,
                    'difficulty_level': we.exercise.difficulty_level, 
                    'equipment_needed': we.exercise.equipment_needed, 
                    'duration_minutes': we.exercise.duration_minutes,  
                    'calories_per_minute': we.exercise.calories_per_minute, 
                    'instructions': we.exercise.instructions,
                    'video_url': we.exercise.video_url, 
                },
                'sets': we.sets,
                'reps': we.reps,
                'weight': we.weight,
                'rest_time': we.rest_time,
                'order_in_workout': we.order_in_workout,
                'notes': we.notes
            })
        
        return Response({
            'workout': {
                'id': workout.id,
                'name': workout.name,
                'description': workout.description,
                'difficulty_level': workout.difficulty_level,
                'estimated_duration': workout.estimated_duration,
                'target_muscle_groups': workout.target_muscle_groups,
                'equipment_needed': workout.equipment_needed,
                'calories_estimate': workout.calories_estimate,
                'workout_type': workout.workout_type
            },
            'exercises': exercises_data,
            'total_exercises': len(exercises_data)
        })
        
    except Workout.DoesNotExist:
        return Response({"error": "Treino não encontrado"}, 
                       status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_workout_session(request, workout_id):
    """Inicia uma nova sessão de treino"""
    try:
        workout = Workout.objects.get(id=workout_id)
        
        # Verificar se já tem sessão em andamento
        active_session = WorkoutSession.objects.filter(
            user=request.user, 
            completed=False
        ).first()
        
        if active_session:
            return Response({
                "error": "Você já tem uma sessão em andamento",
                "active_session_id": active_session.id,
                "active_workout": active_session.workout.name
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Criar nova sessão
        session = WorkoutSession.objects.create(
            user=request.user,
            workout=workout,
            started_at=timezone.now()
        )
        
        # Criar logs para cada exercício do treino
        workout_exercises = WorkoutExercise.objects.filter(workout=workout)
        for we in workout_exercises:
            ExerciseLog.objects.create(
                session=session,
                workout_exercise=we
            )
        
        return Response({
            "message": "Sessão iniciada com sucesso",
            "session_id": session.id,
            "workout_name": workout.name,
            "started_at": session.started_at,
            "total_exercises": workout_exercises.count()
        }, status=status.HTTP_201_CREATED)
        
    except Workout.DoesNotExist:
        return Response({"error": "Treino não encontrado"}, 
                       status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def workout_history(request):
    """
    Histórico de treinos do usuário - formato compatível com Flutter
    """
    from django.db.models import Sum, Count
    from datetime import timedelta
    from collections import defaultdict
    
    # Buscar sessões concluídas do usuário
    sessions = WorkoutSession.objects.filter(
        user=request.user,
        completed=True
    ).select_related('workout').order_by('-completed_at')[:50]  # Últimos 50 treinos
    
    if not sessions.exists():
        return Response({
            'results': [],
            'count': 0,
            'message': 'Nenhum treino concluído ainda'
        })
    
    # Formatar dados para o Flutter
    history = []
    for session in sessions:
        # Calcular exercícios completados
        exercise_logs = ExerciseLog.objects.filter(session=session)
        total_exercises = exercise_logs.count()
        completed_exercises = exercise_logs.filter(completed=True, skipped=False).count()
        
        # Data do treino
        date = session.completed_at if session.completed_at else session.created_at
        
        # Grupos musculares trabalhados
        muscle_groups = []
        if session.workout.target_muscle_groups:
            muscle_groups = [g.strip() for g in session.workout.target_muscle_groups.split(',')]
        
        history.append({
            'id': session.id,
            'workout_name': session.workout.name,
            'name': session.workout.name,  # Alias
            'date': date.isoformat(),
            'completed_at': date.isoformat(),
            'duration': session.duration_minutes or session.workout.estimated_duration or 0,
            'calories': session.calories_burned or session.workout.calories_estimate or 0,
            'category': session.workout.workout_type or 'Geral',
            'muscle_groups': muscle_groups,
            'focus_areas': muscle_groups,  # Alias
            'exercises_completed': completed_exercises,
            'total_exercises': total_exercises,
            'completed': True,
            'user_rating': session.user_rating,
            'notes': session.notes or ''
        })
    
    return Response({
        'results': history,
        'sessions': history,  # Alias para compatibilidade
        'count': len(history),
        'total': len(history)
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_session_status(request):
    """Status da sessão atual do usuário"""
    try:
        session = WorkoutSession.objects.get(user=request.user, completed=False)
        
        # Pegar logs dos exercícios
        exercise_logs = ExerciseLog.objects.filter(session=session).order_by('workout_exercise__order_in_workout')
        
        exercises_data = []
        for log in exercise_logs:
            exercises_data.append({
                'id': log.id,
                'exercise_name': log.workout_exercise.exercise.name,
                'planned_sets': log.workout_exercise.sets,
                'planned_reps': log.workout_exercise.reps,
                'sets_completed': log.sets_completed,
                'reps_completed': log.reps_completed,
                'completed': log.completed,
                'skipped': log.skipped,
                'order': log.workout_exercise.order_in_workout
            })
        
        total_exercises = len(exercises_data)
        completed_exercises = len([e for e in exercises_data if e['completed']])
        
        return Response({
            'session': {
                'id': session.id,
                'workout_name': session.workout.name,
                'started_at': session.started_at,
                'duration_so_far': int((timezone.now() - session.started_at).total_seconds() / 60) if session.started_at else 0
            },
            'progress': {
                'total_exercises': total_exercises,
                'completed_exercises': completed_exercises,
                'progress_percentage': round(completed_exercises / total_exercises * 100, 1) if total_exercises > 0 else 0
            },
            'exercises': exercises_data
        })
        
    except WorkoutSession.DoesNotExist:
        return Response({"message": "Nenhuma sessão ativa encontrada"}, 
                       status=status.HTTP_404_NOT_FOUND)
        
# ADICIONAR AO FINAL DO ARQUIVO apps/workouts/views.py

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_exercise_progress(request, exercise_log_id):
    """Atualiza progresso de um exercício específico"""
    try:
        exercise_log = ExerciseLog.objects.get(
            id=exercise_log_id,
            session__user=request.user,
            session__completed=False
        )
        
        # Dados que podem ser atualizados
        sets_completed = request.data.get('sets_completed')
        reps_completed = request.data.get('reps_completed')
        weight_used = request.data.get('weight_used')
        rest_time_actual = request.data.get('rest_time_actual')
        notes = request.data.get('notes')
        
        # Atualizar campos fornecidos
        if sets_completed is not None:
            exercise_log.sets_completed = sets_completed
        if reps_completed is not None:
            exercise_log.reps_completed = reps_completed
        if weight_used is not None:
            exercise_log.weight_used = weight_used
        if rest_time_actual is not None:
            exercise_log.rest_time_actual = rest_time_actual
        if notes is not None:
            exercise_log.notes = notes
            
        exercise_log.save()
        
        return Response({
            "message": "Progresso atualizado com sucesso",
            "exercise_log": {
                "id": exercise_log.id,
                "exercise_name": exercise_log.workout_exercise.exercise.name,
                "sets_completed": exercise_log.sets_completed,
                "reps_completed": exercise_log.reps_completed,
                "weight_used": exercise_log.weight_used,
                "completed": exercise_log.completed
            }
        })
        
    except ExerciseLog.DoesNotExist:
        return Response({"error": "Log de exercício não encontrado ou sessão inválida"}, 
                       status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_exercise(request, exercise_log_id):
    """Marca um exercício como completo"""
    try:
        exercise_log = ExerciseLog.objects.get(
            id=exercise_log_id,
            session__user=request.user,
            session__completed=False
        )
        
        # Marcar como completo
        exercise_log.completed = True
        exercise_log.completed_at = timezone.now()
        
        # Se não tem dados de progresso, usar os planejados
        if not exercise_log.sets_completed:
            exercise_log.sets_completed = exercise_log.workout_exercise.sets
        if not exercise_log.reps_completed:
            exercise_log.reps_completed = exercise_log.workout_exercise.reps or "Completo"
            
        exercise_log.save()
        
        # Verificar se todos os exercícios da sessão foram completados
        session = exercise_log.session
        total_exercises = ExerciseLog.objects.filter(session=session).count()
        completed_exercises = ExerciseLog.objects.filter(session=session, completed=True).count()
        
        return Response({
            "message": "Exercício concluído com sucesso",
            "exercise_log": {
                "id": exercise_log.id,
                "exercise_name": exercise_log.workout_exercise.exercise.name,
                "completed": exercise_log.completed,
                "completed_at": exercise_log.completed_at
            },
            "session_progress": {
                "completed_exercises": completed_exercises,
                "total_exercises": total_exercises,
                "progress_percentage": round(completed_exercises / total_exercises * 100, 1),
                "all_exercises_completed": completed_exercises == total_exercises
            }
        })
        
    except ExerciseLog.DoesNotExist:
        return Response({"error": "Log de exercício não encontrado"}, 
                       status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def skip_exercise(request, exercise_log_id):
    """Pula um exercício"""
    try:
        exercise_log = ExerciseLog.objects.get(
            id=exercise_log_id,
            session__user=request.user,
            session__completed=False
        )
        
        reason = request.data.get('reason', 'Sem motivo especificado')
        
        exercise_log.skipped = True
        exercise_log.completed = True  # Marca como "processado"
        exercise_log.completed_at = timezone.now()
        exercise_log.notes = f"Pulado: {reason}"
        exercise_log.save()
        
        return Response({
            "message": "Exercício pulado",
            "exercise_log": {
                "id": exercise_log.id,
                "exercise_name": exercise_log.workout_exercise.exercise.name,
                "skipped": exercise_log.skipped,
                "reason": reason
            }
        })
        
    except ExerciseLog.DoesNotExist:
        return Response({"error": "Log de exercício não encontrado"}, 
                       status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pause_session(request):
    """Pausa a sessão atual"""
    try:
        session = WorkoutSession.objects.get(user=request.user, completed=False)
        
        # Adicionar nota de pausa
        pause_note = f"Sessão pausada em {timezone.now().strftime('%H:%M')}"
        if session.notes:
            session.notes += f"\n{pause_note}"
        else:
            session.notes = pause_note
        session.save()
        
        return Response({
            "message": "Sessão pausada",
            "session_id": session.id,
            "paused_at": timezone.now(),
            "workout_name": session.workout.name
        })
        
    except WorkoutSession.DoesNotExist:
        return Response({"error": "Nenhuma sessão ativa encontrada"}, 
                       status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_workout_session(request, session_id=None):
    """Finaliza completamente uma sessão de treino"""
    try:
        # Se session_id foi passado na URL, usar esse
        # Senão, buscar a sessão ativa do usuário
        if session_id:
            session = WorkoutSession.objects.get(
                id=session_id,
                user=request.user,
                completed=False
            )
            print(f'✅ Usando session_id da URL: {session_id}')
        else:
            session = WorkoutSession.objects.get(
                user=request.user,
                completed=False
            )
            print(f'✅ Usando session ativa do usuário')
        
        # Dados opcionais fornecidos pelo usuário
        user_rating = request.data.get('user_rating')
        calories_burned = request.data.get('calories_burned')
        user_notes = request.data.get('notes', '')
        
        # Calcular duração se ainda não foi calculada
        if session.started_at and not session.duration_minutes:
            duration = timezone.now() - session.started_at
            session.duration_minutes = int(duration.total_seconds() / 60)
        
        # Finalizar sessão
        session.completed = True
        session.completed_at = timezone.now()
        
        if user_rating and 1 <= int(user_rating) <= 5:
            session.user_rating = user_rating
        if calories_burned:
            session.calories_burned = calories_burned
        if user_notes:
            session.notes = f"{session.notes or ''}\nNotas finais: {user_notes}".strip()
            
        session.save()
        
        print(f'✅ Sessão {session.id} finalizada com sucesso!')
        print(f'   Duration: {session.duration_minutes}min')
        
        # Estatísticas da sessão
        total_exercises = ExerciseLog.objects.filter(session=session).count()
        completed_exercises = ExerciseLog.objects.filter(session=session, completed=True, skipped=False).count()
        skipped_exercises = ExerciseLog.objects.filter(session=session, skipped=True).count()
        
        # Atualizar progresso do usuário
        from apps.users.models import UserProgress
        try:
            progress = UserProgress.objects.get(user=request.user)
            progress.total_workouts += 1
            progress.save()
        except UserProgress.DoesNotExist:
            UserProgress.objects.create(user=request.user, total_workouts=1)
        
        return Response({
            "message": "Treino finalizado com sucesso! Parabéns! 🎉",
            "session_summary": {
                "id": session.id,
                "workout_name": session.workout.name,
                "completed_at": session.completed_at,
                "duration_minutes": session.duration_minutes,
                "user_rating": session.user_rating,
                "calories_burned": session.calories_burned
            },
            "exercise_summary": {
                "total_exercises": total_exercises,
                "completed_exercises": completed_exercises,
                "skipped_exercises": skipped_exercises,
                "completion_rate": round(completed_exercises / total_exercises * 100, 1) if total_exercises > 0 else 0
            },
            "congratulations": {
                "message": "Excelente trabalho!",
                "motivation": "Você está no caminho certo para alcançar seus objetivos!"
            }
        }, status=status.HTTP_200_OK)
        
    except WorkoutSession.DoesNotExist:
        return Response({"error": "Nenhuma sessão encontrada"}, 
                       status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])  # ✅ Aceita DELETE e POST
@permission_classes([IsAuthenticated])
def cancel_active_session(request, session_id):
    """Cancela uma sessão ativa específica"""
    try:
        session = WorkoutSession.objects.get(
            id=session_id,
            user=request.user,
            completed=False
        )
        
        # Marcar como cancelada (não deletar para manter histórico)
        session.completed = True
        session.completed_at = timezone.now()
        
        # Adicionar nota de cancelamento
        cancel_note = f"Sessão cancelada pelo usuário em {timezone.now().strftime('%d/%m/%Y às %H:%M')}"
        if session.notes:
            session.notes += f"\n{cancel_note}"
        else:
            session.notes = cancel_note
        
        session.save()
        
        print(f'✅ Sessão {session_id} cancelada com sucesso')
        
        return Response({
            'message': 'Sessão cancelada com sucesso',
            'session_id': session_id,
            'workout_name': session.workout.name
        })
        
    except WorkoutSession.DoesNotExist:
        print(f'❌ Sessão {session_id} não encontrada')
        return Response(
            {'error': 'Sessão não encontrada ou não pertence a você'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_analytics(request):
    """
    Analytics completas do usuário - formato compatível com Flutter
    """
    from django.db.models import Sum, Avg, Count
    from datetime import timedelta
    from collections import defaultdict
    
    # Períodos de análise
    now = timezone.now()
    ninety_days_ago = now - timedelta(days=90)
    
    # Sessões do usuário
    all_sessions = WorkoutSession.objects.filter(
        user=request.user, 
        completed=True,
        completed_at__gte=ninety_days_ago
    )
    
    if not all_sessions.exists():
        return Response({
            'total_workouts': 0,
            'total_duration': 0,
            'total_calories': 0,
            'active_days': 0,
            'current_streak': 0,
            'workouts_by_category': {},
            'muscle_group_frequency': {},
            'favorite_exercise': 'Nenhum',
            'favorite_exercise_count': 0,
            'average_duration': 0.0,
        })
    
    # Estatísticas básicas
    total_workouts = all_sessions.count()
    total_duration = all_sessions.aggregate(total=Sum('duration_minutes'))['total'] or 0
    total_calories = all_sessions.aggregate(total=Sum('calories_burned'))['total'] or 0
    
    # Dias ativos (dias únicos com treino)
    active_dates = all_sessions.values_list('completed_at__date', flat=True).distinct()
    active_days = len(set(active_dates))
    
    # Calcular streak de dias consecutivos
    current_streak = 0
    workout_dates = set(all_sessions.values_list('completed_at__date', flat=True))
    if workout_dates:
        current_date = now.date()
        # Permitir streak mesmo se não treinou hoje (considera ontem)
        if current_date not in workout_dates:
            current_date = current_date - timedelta(days=1)
        
        while current_date in workout_dates:
            current_streak += 1
            current_date = current_date - timedelta(days=1)
            if current_streak > 365:  # Limite de segurança
                break
    
    # Treinos por categoria
    workouts_by_category = defaultdict(int)
    for session in all_sessions:
        category = session.workout.workout_type or 'Geral'
        workouts_by_category[category] += 1
    
    # Frequência de grupos musculares
    muscle_group_frequency = defaultdict(int)
    for session in all_sessions:
        if session.workout.target_muscle_groups:
            groups = [g.strip() for g in session.workout.target_muscle_groups.split(',')]
            for group in groups:
                if group:
                    muscle_group_frequency[group] += 1
    
    # Exercício favorito
    favorite_exercise = 'Nenhum'
    favorite_count = 0
    try:
        exercise_counts = ExerciseLog.objects.filter(
            session__user=request.user,
            completed=True,
            skipped=False
        ).values('workout_exercise__exercise__name').annotate(
            count=Count('id')
        ).order_by('-count').first()
        
        if exercise_counts:
            favorite_exercise = exercise_counts['workout_exercise__exercise__name']
            favorite_count = exercise_counts['count']
    except Exception as e:
        print(f"Erro ao buscar exercício favorito: {e}")
    
    # Duração média
    average_duration = float(total_duration / total_workouts) if total_workouts > 0 else 0.0
    
    return Response({
        'total_workouts': total_workouts,
        'total_duration': total_duration,
        'total_calories': total_calories,
        'active_days': active_days,
        'current_streak': current_streak,
        'workouts_by_category': dict(workouts_by_category),
        'muscle_group_frequency': dict(muscle_group_frequency),
        'favorite_exercise': favorite_exercise,
        'favorite_exercise_count': favorite_count,
        'average_duration': round(average_duration, 1),
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_exercise_recommendations(request):
    """Recomendações de exercícios personalizadas baseadas em IA"""
    try:
        profile = UserProfile.objects.get(user=request.user)
        
        # Analisar histórico do usuário
        user_sessions = WorkoutSession.objects.filter(user=request.user, completed=True)
        
        # Exercícios já realizados
        completed_exercise_logs = ExerciseLog.objects.filter(
            session__user=request.user,
            session__completed=True,
            completed=True,
            skipped=False
        )
        
        # Grupos musculares mais trabalhados
        muscle_groups_worked = {}
        for log in completed_exercise_logs:
            muscle_group = log.workout_exercise.exercise.muscle_group
            if muscle_group:
                muscle_groups_worked[muscle_group] = muscle_groups_worked.get(muscle_group, 0) + 1
        
        # Identificar grupos musculares menos trabalhados
        all_muscle_groups = ['chest', 'back', 'shoulders', 'arms', 'legs', 'abs', 'cardio']
        underworked_groups = []
        for group in all_muscle_groups:
            if muscle_groups_worked.get(group, 0) < 3:  # Menos de 3 vezes
                underworked_groups.append(group)
        
        # Buscar exercícios recomendados
        recommended_exercises = []
        
        # Priorizar grupos musculares menos trabalhados
        if underworked_groups:
            for group in underworked_groups[:2]:  # Top 2 grupos
                exercises = Exercise.objects.filter(muscle_group=group)
                
                # Filtrar por nível de dificuldade baseado no perfil
                if profile.activity_level in ['sedentary', 'light']:
                    exercises = exercises.filter(difficulty_level='beginner')
                elif profile.activity_level == 'moderate':
                    exercises = exercises.filter(difficulty_level__in=['beginner', 'intermediate'])
                
                for exercise in exercises[:3]:  # 3 exercícios por grupo
                    recommended_exercises.append({
                        'id': exercise.id,
                        'name': exercise.name,
                        'description': exercise.description,
                        'muscle_group': exercise.muscle_group,
                        'difficulty_level': exercise.difficulty_level,
                        'recommendation_reason': f'Foco em {exercise.muscle_group} - área menos trabalhada',
                        'equipment_needed': exercise.equipment_needed,
                        'duration_minutes': exercise.duration_minutes
                    })
        
        # Se não há grupos subtraballhados, recomendar baseado no objetivo
        if not recommended_exercises and profile.goal:
            if profile.goal == 'lose_weight':
                cardio_exercises = Exercise.objects.filter(muscle_group='cardio')[:5]
                for exercise in cardio_exercises:
                    recommended_exercises.append({
                        'id': exercise.id,
                        'name': exercise.name,
                        'description': exercise.description,
                        'muscle_group': exercise.muscle_group,
                        'difficulty_level': exercise.difficulty_level,
                        'recommendation_reason': 'Ideal para queima de calorias',
                        'equipment_needed': exercise.equipment_needed
                    })
            elif profile.goal == 'gain_muscle':
                strength_exercises = Exercise.objects.filter(muscle_group__in=['chest', 'back', 'arms', 'legs'])[:6]
                for exercise in strength_exercises:
                    recommended_exercises.append({
                        'id': exercise.id,
                        'name': exercise.name,
                        'description': exercise.description,
                        'muscle_group': exercise.muscle_group,
                        'difficulty_level': exercise.difficulty_level,
                        'recommendation_reason': 'Ideal para ganho de massa muscular',
                        'equipment_needed': exercise.equipment_needed
                    })
        
        # Fallback: exercícios gerais para iniciantes
        if not recommended_exercises:
            general_exercises = Exercise.objects.filter(difficulty_level='beginner')[:5]
            for exercise in general_exercises:
                recommended_exercises.append({
                    'id': exercise.id,
                    'name': exercise.name,
                    'description': exercise.description,
                    'muscle_group': exercise.muscle_group,
                    'difficulty_level': exercise.difficulty_level,
                    'recommendation_reason': 'Recomendado para iniciantes',
                    'equipment_needed': exercise.equipment_needed
                })
        
        return Response({
            "ai_recommendations": {
                "personalization_based_on": {
                    "user_goal": profile.goal,
                    "activity_level": profile.activity_level,
                    "total_workouts_completed": user_sessions.count(),
                    "underworked_muscle_groups": underworked_groups
                },
                "recommended_exercises": recommended_exercises,
                "recommendation_strategy": "Balanceamento de grupos musculares + objetivos pessoais",
                "total_recommendations": len(recommended_exercises)
            },
            "next_steps": {
                "suggestion": "Incorpore estes exercícios em seus próximos treinos",
                "focus": f"Priorize {underworked_groups[0] if underworked_groups else 'exercícios variados'}" if underworked_groups else "Continue diversificando seus treinos"
            }
        })
        
    except UserProfile.DoesNotExist:
        return Response({
            "message": "Complete seu perfil para recomendações personalizadas",
            "generic_recommendations": [
                {"name": "Flexões", "reason": "Exercício básico para iniciantes"},
                {"name": "Agachamentos", "reason": "Fortalece pernas e core"},
                {"name": "Caminhada", "reason": "Cardio de baixo impacto"}
            ]
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_ai_workout_plan(request):
    """Gera um plano de treino personalizado com IA"""
    try:
        profile = UserProfile.objects.get(user=request.user)
        
        # Parâmetros da requisição
        duration = request.data.get('duration', 30)  # minutos
        focus = request.data.get('focus', 'full_body')  # full_body, upper, lower, cardio
        difficulty = request.data.get('difficulty', profile.activity_level or 'beginner')
        
        # Mapear nível de atividade para dificuldade
        difficulty_mapping = {
            'sedentary': 'beginner',
            'light': 'beginner', 
            'moderate': 'intermediate',
            'active': 'intermediate',
            'very_active': 'advanced'
        }
        
        if difficulty in difficulty_mapping:
            difficulty = difficulty_mapping[difficulty]
        
        # Selecionar exercícios baseados no foco
        exercises_query = Exercise.objects.all()
        
        if focus == 'upper':
            exercises_query = exercises_query.filter(muscle_group__in=['chest', 'back', 'shoulders', 'arms'])
        elif focus == 'lower':
            exercises_query = exercises_query.filter(muscle_group__in=['legs', 'abs'])
        elif focus == 'cardio':
            exercises_query = exercises_query.filter(muscle_group='cardio')
        # full_body usa todos os exercícios
        
        # Filtrar por dificuldade
        if difficulty == 'beginner':
            exercises_query = exercises_query.filter(difficulty_level='beginner')
        elif difficulty == 'intermediate':
            exercises_query = exercises_query.filter(difficulty_level__in=['beginner', 'intermediate'])
        # advanced usa todos os níveis
        
        # Selecionar exercícios para o plano
        available_exercises = list(exercises_query)
        
        if not available_exercises:
            return Response({"error": "Não há exercícios disponíveis para os critérios especificados"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Algoritmo de seleção baseado na duração
        import random
        random.shuffle(available_exercises)
        
        selected_exercises = []
        total_estimated_time = 0
        target_time = int(duration)
        
        for exercise in available_exercises:
            exercise_time = exercise.duration_minutes or 5  # Default 5 min
            if total_estimated_time + exercise_time <= target_time:
                selected_exercises.append(exercise)
                total_estimated_time += exercise_time
                
            if len(selected_exercises) >= 8 or total_estimated_time >= target_time:
                break
        
        # Gerar plano estruturado
        workout_plan = []
        for i, exercise in enumerate(selected_exercises, 1):
            # Lógica de séries/reps baseada no objetivo e dificuldade
            if profile.goal == 'lose_weight' or exercise.muscle_group == 'cardio':
                sets = 3
                reps = "30-45 segundos" if exercise.muscle_group == 'cardio' else "15-20"
                rest_time = 30
            elif profile.goal == 'gain_muscle':
                sets = 4
                reps = "8-12"
                rest_time = 60
            else:  # maintain, endurance
                sets = 3
                reps = "12-15"
                rest_time = 45
            
            workout_plan.append({
                'order': i,
                'exercise': {
                    'id': exercise.id,
                    'name': exercise.name,
                    'description': exercise.description,
                    'muscle_group': exercise.muscle_group,
                    'instructions': exercise.instructions
                },
                'sets': sets,
                'reps': reps,
                'rest_time_seconds': rest_time,
                'estimated_duration': exercise.duration_minutes or 5
            })
        
        return Response({
            "ai_generated_workout": {
                "plan_info": {
                    "total_exercises": len(workout_plan),
                    "estimated_duration": total_estimated_time,
                    "focus": focus,
                    "difficulty": difficulty,
                    "personalized_for": profile.user.username
                },
                "workout_plan": workout_plan,
                "ai_recommendations": {
                    "warm_up": "Faça 5 minutos de aquecimento antes de começar",
                    "cool_down": "Finalize com alongamentos por 5 minutos",
                    "hydration": "Mantenha-se hidratado durante todo o treino",
                    "progression": "Aumente a intensidade gradualmente a cada semana"
                },
                "customization_note": f"Este treino foi personalizado baseado no seu objetivo: {profile.goal or 'geral'} e nível: {profile.activity_level or 'iniciante'}"
            }
        }, status=status.HTTP_201_CREATED)
        
    except UserProfile.DoesNotExist:
        return Response({"error": "Perfil de usuário não encontrado"}, 
                       status=status.HTTP_404_NOT_FOUND)
    
# criar treinos

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_personalized_workouts(request):
    """Lista apenas treinos personalizados criados pelo usuário"""
    workouts = Workout.objects.filter(
        is_personalized=True,
        created_by_user=request.user
    ).order_by('-created_at')
    
    data = []
    for workout in workouts:
        exercise_count = WorkoutExercise.objects.filter(workout=workout).count()
        data.append({
            'id': workout.id,
            'name': workout.name,
            'description': workout.description,
            'difficulty_level': workout.difficulty_level,
            'estimated_duration': workout.estimated_duration,
            'target_muscle_groups': workout.target_muscle_groups,
            'equipment_needed': workout.equipment_needed,
            'calories_estimate': workout.calories_estimate,
            'workout_type': workout.workout_type,
            'exercise_count': exercise_count,
            'is_personalized': workout.is_personalized,
            'created_at': workout.created_at
        })
    
    return Response({
        'my_workouts': data,
        'total': len(data)
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_personalized_workout(request):
    """Cria um novo treino personalizado"""
    name = request.data.get('name')
    description = request.data.get('description')
    difficulty_level = request.data.get('difficulty_level', 'beginner')
    estimated_duration = request.data.get('estimated_duration', 30)
    target_muscle_groups = request.data.get('target_muscle_groups', '')
    equipment_needed = request.data.get('equipment_needed', '')
    calories_estimate = request.data.get('calories_estimate', 0)
    workout_type = request.data.get('workout_type', 'strength')
    
    # Validações
    if not name or not description:
        return Response(
            {"error": "Nome e descrição são obrigatórios"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Criar treino
    workout = Workout.objects.create(
        name=name,
        description=description,
        difficulty_level=difficulty_level,
        estimated_duration=estimated_duration,
        target_muscle_groups=target_muscle_groups,
        equipment_needed=equipment_needed,
        calories_estimate=calories_estimate,
        workout_type=workout_type,
        is_personalized=True,
        created_by_user=request.user,
        is_recommended=False
    )
    
    return Response({
        'message': 'Treino criado com sucesso',
        'workout': {
            'id': workout.id,
            'name': workout.name,
            'description': workout.description,
            'difficulty_level': workout.difficulty_level,
            'estimated_duration': workout.estimated_duration,
            'workout_type': workout.workout_type,
            'is_personalized': workout.is_personalized
        }
    }, status=status.HTTP_201_CREATED)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_personalized_workout(request, workout_id):
    """Atualiza treino personalizado (apenas do próprio usuário)"""
    try:
        workout = Workout.objects.get(id=workout_id)
        
        # Verificar permissão
        if not workout.is_personalized or workout.created_by_user != request.user:
            return Response(
                {"error": "Você não tem permissão para editar este treino"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Atualizar campos fornecidos
        workout.name = request.data.get('name', workout.name)
        workout.description = request.data.get('description', workout.description)
        workout.difficulty_level = request.data.get('difficulty_level', workout.difficulty_level)
        workout.estimated_duration = request.data.get('estimated_duration', workout.estimated_duration)
        workout.target_muscle_groups = request.data.get('target_muscle_groups', workout.target_muscle_groups)
        workout.equipment_needed = request.data.get('equipment_needed', workout.equipment_needed)
        workout.calories_estimate = request.data.get('calories_estimate', workout.calories_estimate)
        workout.workout_type = request.data.get('workout_type', workout.workout_type)
        workout.save()
        
        return Response({
            'message': 'Treino atualizado com sucesso',
            'workout': {
                'id': workout.id,
                'name': workout.name,
                'description': workout.description
            }
        })
        
    except Workout.DoesNotExist:
        return Response(
            {"error": "Treino não encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_personalized_workout(request, workout_id):
    """Deleta treino personalizado (apenas do próprio usuário)"""
    try:
        workout = Workout.objects.get(id=workout_id)
        
        # Verificar permissão
        if not workout.is_personalized or workout.created_by_user != request.user:
            return Response(
                {"error": "Você não tem permissão para deletar este treino"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        workout_name = workout.name
        workout.delete()
        
        return Response({
            'message': f'Treino "{workout_name}" deletado com sucesso'
        })
        
    except Workout.DoesNotExist:
        return Response(
            {"error": "Treino não encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_exercise_to_workout(request, workout_id):
    """Adiciona exercício ao treino personalizado"""
    try:
        workout = Workout.objects.get(id=workout_id)
        
        # Verificar permissão
        if not workout.is_personalized or workout.created_by_user != request.user:
            return Response(
                {"error": "Você só pode adicionar exercícios aos seus treinos"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        exercise_id = request.data.get('exercise_id')
        sets = request.data.get('sets', 3)
        reps = request.data.get('reps', '10')
        weight = request.data.get('weight')
        rest_time = request.data.get('rest_time', 60)
        order_in_workout = request.data.get('order_in_workout', 1)
        notes = request.data.get('notes', '')
        
        if not exercise_id:
            return Response(
                {"error": "exercise_id é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        exercise = Exercise.objects.get(id=exercise_id)
        
        # Criar WorkoutExercise
        workout_exercise = WorkoutExercise.objects.create(
            workout=workout,
            exercise=exercise,
            sets=sets,
            reps=reps,
            weight=weight,
            rest_time=rest_time,
            order_in_workout=order_in_workout,
            notes=notes
        )
        
        return Response({
            'message': 'Exercício adicionado com sucesso',
            'workout_exercise': {
                'id': workout_exercise.id,
                'exercise_name': exercise.name,
                'sets': workout_exercise.sets,
                'reps': workout_exercise.reps,
                'order': workout_exercise.order_in_workout
            }
        }, status=status.HTTP_201_CREATED)
        
    except Workout.DoesNotExist:
        return Response({"error": "Treino não encontrado"}, status=status.HTTP_404_NOT_FOUND)
    except Exercise.DoesNotExist:
        return Response({"error": "Exercício não encontrado"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_exercise_in_workout(request, workout_id, workout_exercise_id):
    """Atualiza configurações de um exercício no treino"""
    try:
        workout = Workout.objects.get(id=workout_id)
        
        # Verificar permissão
        if not workout.is_personalized or workout.created_by_user != request.user:
            return Response(
                {"error": "Você não tem permissão para editar este treino"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        workout_exercise = WorkoutExercise.objects.get(
            id=workout_exercise_id,
            workout=workout
        )
        
        # Atualizar campos fornecidos
        if 'sets' in request.data:
            workout_exercise.sets = request.data['sets']
        if 'reps' in request.data:
            workout_exercise.reps = request.data['reps']
        if 'weight' in request.data:
            workout_exercise.weight = request.data['weight']
        if 'rest_time' in request.data:
            workout_exercise.rest_time = request.data['rest_time']
        if 'order_in_workout' in request.data:
            workout_exercise.order_in_workout = request.data['order_in_workout']
        if 'notes' in request.data:
            workout_exercise.notes = request.data['notes']
        
        workout_exercise.save()
        
        return Response({
            'message': 'Exercício atualizado com sucesso',
            'workout_exercise': {
                'id': workout_exercise.id,
                'sets': workout_exercise.sets,
                'reps': workout_exercise.reps,
                'weight': workout_exercise.weight
            }
        })
        
    except Workout.DoesNotExist:
        return Response({"error": "Treino não encontrado"}, status=status.HTTP_404_NOT_FOUND)
    except WorkoutExercise.DoesNotExist:
        return Response({"error": "Exercício no treino não encontrado"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_exercise_from_workout(request, workout_id, workout_exercise_id):
    """Remove exercício do treino"""
    try:
        workout = Workout.objects.get(id=workout_id)
        
        # Verificar permissão
        if not workout.is_personalized or workout.created_by_user != request.user:
            return Response(
                {"error": "Você não tem permissão para editar este treino"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        workout_exercise = WorkoutExercise.objects.get(
            id=workout_exercise_id,
            workout=workout
        )
        
        exercise_name = workout_exercise.exercise.name
        workout_exercise.delete()
        
        return Response({
            'message': f'Exercício "{exercise_name}" removido do treino'
        })
        
    except Workout.DoesNotExist:
        return Response({"error": "Treino não encontrado"}, status=status.HTTP_404_NOT_FOUND)
    except WorkoutExercise.DoesNotExist:
        return Response({"error": "Exercício no treino não encontrado"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def duplicate_workout(request, workout_id):
    """Duplica um treino (catálogo ou próprio) para criar versão personalizada"""
    try:
        original_workout = Workout.objects.get(id=workout_id)
        
        # Criar cópia
        new_workout = Workout.objects.create(
            name=f"{original_workout.name} (Cópia)",
            description=original_workout.description,
            difficulty_level=original_workout.difficulty_level,
            estimated_duration=original_workout.estimated_duration,
            target_muscle_groups=original_workout.target_muscle_groups,
            equipment_needed=original_workout.equipment_needed,
            calories_estimate=original_workout.calories_estimate,
            workout_type=original_workout.workout_type,
            is_personalized=True,
            created_by_user=request.user,
            is_recommended=False
        )
        
        # Copiar todos os exercícios
        for workout_exercise in WorkoutExercise.objects.filter(workout=original_workout):
            WorkoutExercise.objects.create(
                workout=new_workout,
                exercise=workout_exercise.exercise,
                sets=workout_exercise.sets,
                reps=workout_exercise.reps,
                weight=workout_exercise.weight,
                rest_time=workout_exercise.rest_time,
                order_in_workout=workout_exercise.order_in_workout,
                notes=workout_exercise.notes
            )
        
        exercise_count = WorkoutExercise.objects.filter(workout=new_workout).count()
        
        return Response({
            'message': 'Treino duplicado com sucesso',
            'workout': {
                'id': new_workout.id,
                'name': new_workout.name,
                'description': new_workout.description,
                'exercise_count': exercise_count,
                'is_personalized': new_workout.is_personalized
            }
        }, status=status.HTTP_201_CREATED)
        
    except Workout.DoesNotExist:
        return Response({"error": "Treino não encontrado"}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_session(request):
    """Retorna a sessão ativa do usuário"""
    active_session = WorkoutSession.objects.filter(
        user=request.user,
        completed=False
    ).first()
    
    if not active_session:
        return Response(
            {'message': 'Nenhuma sessão ativa'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    return Response({
        'active_session_id': active_session.id,
        'active_workout': active_session.workout.name,
        'started_at': active_session.started_at,
        'workout_id': active_session.workout.id,
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_active_session(request, session_id):
    """Cancela uma sessão ativa específica"""
    try:
        session = WorkoutSession.objects.get(
            id=session_id,
            user=request.user,
            completed=False
        )
        
        # Marcar como cancelada (não deletar para manter histórico)
        session.completed = True
        session.completed_at = timezone.now()
        
        # Adicionar nota de cancelamento
        cancel_note = f"Sessão cancelada pelo usuário em {timezone.now().strftime('%d/%m/%Y às %H:%M')}"
        if session.notes:
            session.notes += f"\n{cancel_note}"
        else:
            session.notes = cancel_note
        
        session.save()
        
        return Response({
            'message': 'Sessão cancelada com sucesso',
            'session_id': session_id,
            'workout_name': session.workout.name
        })
        
    except WorkoutSession.DoesNotExist:
        return Response(
            {'error': 'Sessão não encontrada ou não pertence a você'},
            status=status.HTTP_404_NOT_FOUND
        )
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_onboarding_workout(request):
    """
    🤖 Gera treino personalizado com IA durante o cadastro/onboarding
    """
    try:
        from django.conf import settings
        import google.generativeai as genai
        
        user = request.user
        user_data = request.data.get('user_data', {})
        ai_prompt = request.data.get('ai_prompt')
        create_workout = request.data.get('create_workout', True)
        
        print(f"🤖 Gerando treino IA para: {user.email}")
        
        # Construir prompt
        if not ai_prompt:
            ai_prompt = _build_onboarding_prompt(user_data)
        
        # ✅ CONFIGURAR GEMINI
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not api_key:
            raise ValueError("GEMINI_API_KEY não está configurada")
        
        genai.configure(api_key=api_key)
        
        # ✅ USAR EXATAMENTE O MESMO PADRÃO DO CHAT SERVICE
        model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash-exp')
        print(f"🤖 Modelo: {model_name}")
        
        model = genai.GenerativeModel(model_name)
        print("📡 Chamando Gemini...")
        response = model.generate_content(ai_prompt)
        
        ai_text = response.text
        print(f"✅ Resposta: {len(ai_text)} chars")
        
        # Parsear JSON
        workout_data = _extract_json_from_ai_response(ai_text)
        
        if not workout_data:
            raise ValueError("JSON inválido da IA")
        
        # Criar treino
        if create_workout:
            workout = _create_ai_workout(user, workout_data, user_data)
            
            return Response({
                'success': True,
                'message': 'Treino criado com sucesso!',
                'workout_id': workout.id,
                'workout_name': workout.name,
                'exercises_count': workout.workout_exercises.count(),
                'estimated_duration': workout.estimated_duration,
                'difficulty_level': workout.difficulty_level,
                'is_ai_generated': True,
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': True,
                'workout_data': workout_data,
            })
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return Response({
            'error': 'Erro ao gerar treino',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ====== gerar treinos final do cadrasto======

def _build_onboarding_prompt(user_data):
    """Constrói prompt detalhado"""
    
    # Calcular IMC
    peso = user_data.get('peso_atual', 0)
    altura = user_data.get('altura', 0)
    imc = 0
    imc_cat = 'N/A'
    
    if peso > 0 and altura > 0:
        altura_m = altura / 100
        imc = peso / (altura_m * altura_m)
        if imc < 18.5:
            imc_cat = 'Abaixo do peso'
        elif imc < 25:
            imc_cat = 'Normal'
        elif imc < 30:
            imc_cat = 'Sobrepeso'
        else:
            imc_cat = 'Obesidade'
    
    # Mapear nível -> dificuldade
    nivel = user_data.get('nivel_atividade', '').lower()
    if 'sedentário' in nivel or 'sedentario' in nivel:
        difficulty = 'beginner'
        days = 3
    elif 'moderado' in nivel:
        difficulty = 'beginner'
        days = 4
    elif 'ativo' in nivel and 'muito' not in nivel:
        difficulty = 'intermediate'
        days = 5
    else:
        difficulty = 'intermediate'
        days = 6
    
    # Exercícios por tempo
    tempo = user_data.get('tempo_disponivel', '30-45')
    if '15-30' in tempo:
        ex_count = 5
    elif '30-45' in tempo:
        ex_count = 7
    elif '45-60' in tempo:
        ex_count = 9
    else:
        ex_count = 10
    
    metas = ', '.join(user_data.get('metas', ['Condicionamento geral']))
    areas = ', '.join(user_data.get('areas_desejadas', ['Corpo completo']))
    tipos = ', '.join(user_data.get('tipos_treino', ['Variados']))
    equip = user_data.get('equipamentos', 'Sem equipamentos')
    
    return f'''
Crie um treino personalizado COMPLETO para:

📊 PERFIL:
- Nome: {user_data.get('nome', 'Usuário')}
- {user_data.get('idade', 25)} anos, {user_data.get('sexo', 'N/A')}
- IMC: {imc:.1f} ({imc_cat})
- Peso: {peso}kg → Meta: {user_data.get('peso_desejado', peso)}kg
- Altura: {altura}cm

🎯 OBJETIVOS:
- Metas: {metas}
- Nível: {user_data.get('nivel_atividade', 'Iniciante')}
- Foco: {areas}
- Preferências: {tipos}
- Equipamentos: {equip}
- Tempo: {tempo}

💪 CRIAR TREINO:
- Dificuldade: {difficulty}
- {days} dias/semana
- {ex_count} exercícios
- Duração: {tempo}

⚠️ FORMATO JSON OBRIGATÓRIO (SEM MARKDOWN):
{{
  "workout_name": "Nome Motivacional do Treino",
  "description": "Descrição clara dos objetivos (2-3 linhas)",
  "difficulty_level": "{difficulty}",
  "estimated_duration": {30 if '30-45' in tempo else 45},
  "target_muscle_groups": "{areas}",
  "equipment_needed": "{equip}",
  "workout_type": "full_body",
  "calories_estimate": 250,
  "exercises": [
    {{
      "name": "Nome Específico do Exercício",
      "description": "Como executar (máx 4 linhas)",
      "muscle_group": "grupo_primário",
      "difficulty_level": "{difficulty}",
      "equipment_needed": "equipamento_ou_bodyweight",
      "duration_minutes": 5,
      "sets": 3,
      "reps": "12-15",
      "rest_time": 60,
      "order_in_workout": 1,
      "instructions": ["Passo 1", "Passo 2", "Passo 3"],
      "tips": ["Dica 1", "Dica 2"]
    }}
  ]
}}

🚨 REGRAS:
1. Retornar APENAS JSON (sem ```json ou explicações)
2. Exatamente {ex_count} exercícios
3. Nomes específicos (ex: "Agachamento Livre", não "Agachamento")
4. Considerar equipamento: {equip}
5. Focar nas áreas: {areas}
6. Adaptar para nível: {difficulty}
'''


def _extract_json_from_ai_response(text):
    """Extrai JSON da resposta (remove markdown)"""
    
    # Remover blocos markdown
    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        json_text = json_match.group(1)
    else:
        # Buscar objeto JSON
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
        else:
            json_text = text
    
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"⚠️ Erro JSON: {e}")
        print(f"Texto: {json_text[:300]}...")
        return None


def _create_ai_workout(user, workout_data, user_profile):
    """
    Cria Workout usando APENAS campos existentes
    
    🔥 CAMPOS USADOS (já existem no seu modelo):
    - is_recommended = True (marca como treino IA)
    - is_personalized = True
    - created_by_user = user
    - description (pode incluir info da IA aqui)
    """
    
    # Adicionar metadata da IA na descrição
    ai_metadata = f"\n\n🤖 Treino gerado por IA em {timezone.now().strftime('%d/%m/%Y')}"
    ai_metadata += f"\n📊 Baseado em: {', '.join(user_profile.get('metas', []))}"
    
    description = workout_data.get('description', '')
    full_description = description + ai_metadata
    
    # Criar workout
    workout = Workout.objects.create(
        name=workout_data.get('workout_name', 'Treino Personalizado'),
        description=full_description,
        difficulty_level=workout_data.get('difficulty_level', 'beginner'),
        estimated_duration=workout_data.get('estimated_duration', 30),
        target_muscle_groups=workout_data.get('target_muscle_groups', ''),
        equipment_needed=workout_data.get('equipment_needed', 'Variado'),
        calories_estimate=workout_data.get('calories_estimate', 200),
        workout_type=workout_data.get('workout_type', 'full_body'),
        # 🔥 USAR CAMPOS EXISTENTES
        is_recommended=True,  # Marca como treino gerado por IA
        is_personalized=True,  # Personalizado para o usuário
        created_by_user=user,  # Dono do treino
    )
    
    print(f"✅ Workout criado: {workout.name} (ID: {workout.id})")
    
    # Adicionar exercícios
    exercises_data = workout_data.get('exercises', [])
    
    for idx, ex_data in enumerate(exercises_data, start=1):
        # Buscar ou criar exercício
        exercise, created = Exercise.objects.get_or_create(
            name=ex_data.get('name', f'Exercício {idx}'),
            defaults={
                'description': ex_data.get('description', ''),
                'muscle_group': ex_data.get('muscle_group', 'full_body'),
                'difficulty_level': ex_data.get('difficulty_level', 'beginner'),
                'equipment_needed': ex_data.get('equipment_needed', 'bodyweight'),
                'duration_minutes': ex_data.get('duration_minutes', 5),
                'calories_per_minute': 5.0,
                'instructions': ex_data.get('instructions', []),
                'video_url': '',
            }
        )
        
        if created:
            print(f"  ✅ Exercício criado: {exercise.name}")
        else:
            print(f"  ♻️ Exercício existente: {exercise.name}")
        
        # Criar WorkoutExercise
        WorkoutExercise.objects.create(
            workout=workout,
            exercise=exercise,
            sets=ex_data.get('sets', 3),
            reps=ex_data.get('reps', '12'),
            weight=ex_data.get('weight'),
            rest_time=ex_data.get('rest_time', 60),
            order_in_workout=ex_data.get('order_in_workout', idx),
            notes='\n'.join(ex_data.get('tips', [])),
        )
    
    print(f"✅ Total: {len(exercises_data)} exercícios adicionados")
    
    return workout