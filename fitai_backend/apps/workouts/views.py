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
from datetime import datetime, timedelta

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
        is_personalized=False,  # Exclui TODOS os treinos personalizados
        is_recommended=False,   #  Exclui treinos de IA
        is_active=True  
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
            'is_personalized': False,  # Sempre False nesta lista
            'is_recommended': False, # Sempre False nesta lista
        })
    
    return Response({
        'workouts': data,
        'total': len(data)
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommended_workouts(request):
    """
    🤖 RECOMENDADOS - APENAS TREINOS DE IA DO USUÁRIO ATUAL
    
    ✅ Retorna SOMENTE:
    - Treinos gerados pela IA (is_recommended=True)
    - DO usuário logado (created_by_user=request.user)
    - Personalizados (is_personalized=True)
    - Ativos (is_active=True)
    
    ❌ NÃO retorna:
    - Treinos de IA de outros usuários
    - Treinos do catálogo
    - Treinos criados manualmente pelo usuário
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
        
        # ============================================================
        # ✅ FILTRO CORRETO: APENAS TREINOS DE IA DO USUÁRIO ATUAL
        # ============================================================
        
        workouts = Workout.objects.filter(
            is_recommended=True,           # ✅ Gerado pela IA
            is_personalized=True,          # ✅ Personalizado
            created_by_user=request.user,  # ✅ CRÍTICO: Apenas do usuário atual
            is_active=True                 # ✅ Apenas ativos
        ).order_by('-created_at')[:10]     # ✅ Mais recentes primeiro, limite 10
        
        print(f'🤖 [RECOMENDADOS] Usuário: {request.user.username}')
        print(f'   Treinos encontrados: {workouts.count()}')
        
        data = []
        for workout in workouts:
            exercise_count = WorkoutExercise.objects.filter(workout=workout).count()
            
            # ✅ Verificação extra de segurança
            if workout.created_by_user != request.user:
                print(f'⚠️ ALERTA: Treino {workout.id} não pertence ao usuário!')
                continue  # Pula este treino
            
            data.append({
                'id': workout.id,
                'name': workout.name,
                'description': workout.description,
                'difficulty_level': workout.difficulty_level,
                'estimated_duration': workout.estimated_duration,
                'workout_type': workout.workout_type,
                'calories_estimate': workout.calories_estimate,
                'exercise_count': exercise_count,
                'is_recommended': True,            # ✅ Sempre True nesta lista (treinos de IA)
                'is_personalized': True,           # ✅ Sempre True nesta lista
                'created_at': workout.created_at,  # ✅ Data de criação
                'source': 'ai_recommendation',     # ✅ Identificador da fonte
                'recommendation_reason': f"Treino personalizado pela IA baseado no seu perfil"
            })
        
        print(f'   Retornando: {len(data)} treinos')
        
        return Response({
            'recommended_workouts': data,
            'total': len(data),
            'source': 'ai_recommendation',
            'user_goal': profile.goal,
            'activity_level': profile.activity_level,
            'message': 'Treinos gerados pela IA para você'
        })
        
    except UserProfile.DoesNotExist:
        # ✅ Fallback: Retornar VAZIO se não tem perfil
        print(f'⚠️ [RECOMENDADOS] Usuário {request.user.username} sem perfil')
        
        return Response({
            'recommended_workouts': [],
            'total': 0,
            'message': 'Complete seu perfil para receber treinos personalizados pela IA',
            'action_required': 'complete_profile'
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
    
    sessions = WorkoutSession.objects.filter(
        user=request.user,
        completed=True
    ).select_related('workout').order_by('-completed_at')[:50]
    
    if not sessions.exists():
        return Response({
            'results': [],
            'count': 0,
            'message': 'Nenhum treino concluído ainda'
        })
    
    history = []
    for session in sessions:
        exercise_logs = ExerciseLog.objects.filter(session=session)
        total_exercises = exercise_logs.count()
        
        # ✅ CORREÇÃO: Se a sessão foi concluída, contar todos os logs como completos
        # (exceto os pulados)
        if session.completed:
            completed_exercises = exercise_logs.exclude(skipped=True).count()
        else:
            completed_exercises = exercise_logs.filter(completed=True, skipped=False).count()
        
        date = session.completed_at if session.completed_at else session.created_at
        
        muscle_groups = []
        if session.workout.target_muscle_groups:
            muscle_groups = [g.strip() for g in session.workout.target_muscle_groups.split(',')]
        
        history.append({
            'id': session.id,
            'workout_name': session.workout.name,
            'name': session.workout.name,
            'date': date.isoformat(),
            'completed_at': date.isoformat(),
            'duration': session.duration_minutes or session.workout.estimated_duration or 0,
            'calories': session.calories_burned or session.workout.calories_estimate or 0,
            'category': session.workout.workout_type or 'Geral',
            'muscle_groups': muscle_groups,
            'focus_areas': muscle_groups,
            'exercises_completed': completed_exercises,  # ✅ Agora correto
            'total_exercises': total_exercises,
            'completed': True,
            'user_rating': session.user_rating,
            'notes': session.notes or ''
        })
    
    return Response({
        'results': history,
        'sessions': history,
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
        
        # ✅ CORREÇÃO 1: CALCULAR DURAÇÃO REAL
        if session.started_at:
            duration = timezone.now() - session.started_at
            duration_minutes = int(duration.total_seconds() / 60)
            session.duration_minutes = duration_minutes
            print(f'⏱️ Duração REAL calculada: {duration_minutes} min')
        else:
            # Fallback para duração estimada
            session.duration_minutes = session.workout.estimated_duration or 30
            print(f'⚠️ Usando duração estimada: {session.duration_minutes} min')
        
        # ✅ CORREÇÃO 2: SALVAR GRUPOS MUSCULARES REAIS
        # Buscar os exercícios realizados na sessão
        exercise_logs = ExerciseLog.objects.filter(
            session=session,
            completed=True,
            skipped=False
        ).select_related('workout_exercise__exercise')
        
        # Coletar grupos musculares únicos dos exercícios REALIZADOS
        muscle_groups_set = set()
        for log in exercise_logs:
            muscle_group = log.workout_exercise.exercise.muscle_group
            if muscle_group:
                muscle_groups_set.add(muscle_group)
        
        # Se não realizou nenhum exercício, usar os grupos do workout
        if not muscle_groups_set and session.workout.target_muscle_groups:
            muscle_groups_list = [
                g.strip() 
                for g in session.workout.target_muscle_groups.split(',')
                if g.strip()
            ]
        else:
            muscle_groups_list = list(muscle_groups_set)
        
        # Salvar como string separada por vírgula
        session.workout.target_muscle_groups = ', '.join(muscle_groups_list)
        session.workout.save()
        
        print(f'💪 Grupos musculares salvos: {muscle_groups_list}')
        
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
        print(f'   Duração: {session.duration_minutes}min')
        print(f'   Grupos musculares: {muscle_groups_list}')
        
        # Estatísticas da sessão
        total_exercises = ExerciseLog.objects.filter(session=session).count()
        completed_exercises = ExerciseLog.objects.filter(
            session=session, 
            completed=True, 
            skipped=False
        ).count()
        skipped_exercises = ExerciseLog.objects.filter(
            session=session, 
            skipped=True
        ).count()
        
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
                "duration_minutes": session.duration_minutes,  # ✅ Duração REAL
                "user_rating": session.user_rating,
                "calories_burned": session.calories_burned,
                "muscle_groups_worked": muscle_groups_list  # ✅ Grupos REAIS
            },
            "exercise_summary": {
                "total_exercises": total_exercises,
                "completed_exercises": completed_exercises,
                "skipped_exercises": skipped_exercises,
                "completion_rate": round(
                    completed_exercises / total_exercises * 100, 1
                ) if total_exercises > 0 else 0
            },
            "congratulations": {
                "message": "Excelente trabalho!",
                "motivation": "Você está no caminho certo para alcançar seus objetivos!"
            }
        }, status=status.HTTP_200_OK)
        
    except WorkoutSession.DoesNotExist:
        return Response(
            {"error": "Nenhuma sessão encontrada"}, 
            status=status.HTTP_404_NOT_FOUND
        )

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
        is_recommended=False,
        created_by_user=request.user,
        is_active=True
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
# ============================================================
# 🔧 EDITAR TREINO PERSONALIZADO - ADICIONAR AO views.py
# ============================================================

from django.db.models import Max

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_workout_for_editing(request, workout_id):
    """
    🔍 Busca treino completo para edição
    Retorna todos os dados incluindo exercícios
    """
    try:
        workout = Workout.objects.get(id=workout_id)
        
        # ============================================================
        # VALIDAÇÃO: VERIFICAR PERMISSÕES
        # ============================================================
        
        if workout.is_personalized and workout.created_by_user != request.user:
            return Response({
                'error': 'Você não tem permissão para visualizar este treino',
                'owner': workout.created_by_user.username if workout.created_by_user else 'Sistema'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # ============================================================
        # BUSCAR EXERCÍCIOS DO TREINO
        # ============================================================
        
        workout_exercises = WorkoutExercise.objects.filter(
            workout=workout
        ).select_related('exercise').order_by('order_in_workout')
        
        exercises_data = []
        for we in workout_exercises:
            exercises_data.append({
                'id': we.id,
                'exercise_id': we.exercise.id,
                'exercise_name': we.exercise.name,
                'exercise_description': we.exercise.description,
                'muscle_group': we.exercise.muscle_group,
                'difficulty_level': we.exercise.difficulty_level,
                'equipment_needed': we.exercise.equipment_needed,
                'duration_minutes': we.exercise.duration_minutes,
                'video_url': we.exercise.video_url,
               # 'image_url': we.exercise.image_url,
                # Configurações no treino
                'sets': we.sets,
                'reps': we.reps,
                'weight': we.weight,
                'rest_time': we.rest_time,
                'order_in_workout': we.order_in_workout,
                'notes': we.notes or '',
            })
        
        print(f'✅ Treino {workout_id} carregado para edição')
        print(f'   Exercícios: {len(exercises_data)}')
        
        return Response({
            'success': True,
            'workout': {
                'id': workout.id,
                'name': workout.name,
                'description': workout.description,
                'difficulty_level': workout.difficulty_level,
                'estimated_duration': workout.estimated_duration,
                'target_muscle_groups': workout.target_muscle_groups,
                'equipment_needed': workout.equipment_needed,
                'calories_estimate': workout.calories_estimate,
                'workout_type': workout.workout_type,
                'is_personalized': workout.is_personalized,
                'is_active': workout.is_active,
                'created_at': workout.created_at,
                'created_by': workout.created_by_user.username if workout.created_by_user else None
            },
            'exercises': exercises_data,
            'total_exercises': len(exercises_data)
        })
        
    except Workout.DoesNotExist:
        return Response({
            'error': 'Treino não encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        print(f'❌ Erro ao buscar treino: {str(e)}')
        import traceback
        traceback.print_exc()
        
        return Response({
            'error': 'Erro ao buscar treino',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def edit_workout_complete(request, workout_id):
    """
    ✏️ EDIÇÃO COMPLETA: Atualiza treino e seus exercícios
    
    Body esperado:
    {
      "workout": { name, description, difficulty_level, ... },
      "exercises_to_add": [ { exercise_id, sets, reps, ... } ],
      "exercises_to_update": [ { id, sets, reps, ... } ],
      "exercises_to_remove": [ workout_exercise_id_1, workout_exercise_id_2 ]
    }
    """
    try:
        workout = Workout.objects.get(id=workout_id)
        
        # ============================================================
        # VALIDAÇÃO 1: VERIFICAR PERMISSÕES
        # ============================================================
        
        if not workout.is_personalized or workout.created_by_user != request.user:
            return Response({
                'error': 'Você não tem permissão para editar este treino',
                'owner': workout.created_by_user.username if workout.created_by_user else 'Sistema'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # ============================================================
        # VALIDAÇÃO 2: VERIFICAR SE ESTÁ EM SESSÃO ATIVA
        # ============================================================
        
        active_session = WorkoutSession.objects.filter(
            workout=workout,
            completed=False
        ).first()
        
        if active_session:
            return Response({
                'error': 'Não é possível editar este treino',
                'reason': 'Existe uma sessão ativa em andamento',
                'active_session_id': active_session.id,
                'started_at': active_session.started_at,
                'suggestion': 'Cancele ou complete a sessão antes de editar'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ============================================================
        # ATUALIZAR DADOS DO TREINO
        # ============================================================
        
        workout_data = request.data.get('workout', {})
        
        if workout_data:
            workout.name = workout_data.get('name', workout.name)
            workout.description = workout_data.get('description', workout.description)
            workout.difficulty_level = workout_data.get('difficulty_level', workout.difficulty_level)
            workout.estimated_duration = workout_data.get('estimated_duration', workout.estimated_duration)
            workout.target_muscle_groups = workout_data.get('target_muscle_groups', workout.target_muscle_groups)
            workout.equipment_needed = workout_data.get('equipment_needed', workout.equipment_needed)
            workout.calories_estimate = workout_data.get('calories_estimate', workout.calories_estimate)
            workout.workout_type = workout_data.get('workout_type', workout.workout_type)
            
            workout.save()
            print(f'✅ Treino atualizado: {workout.name}')
        
        # ============================================================
        # REMOVER EXERCÍCIOS
        # ============================================================
        
        exercises_to_remove = request.data.get('exercises_to_remove', [])
        removed_count = 0
        
        for exercise_id in exercises_to_remove:
            try:
                we = WorkoutExercise.objects.get(
                    id=exercise_id,
                    workout=workout
                )
                exercise_name = we.exercise.name
                we.delete()
                removed_count += 1
                print(f'  🗑️ Removido: {exercise_name}')
            except WorkoutExercise.DoesNotExist:
                print(f'  ⚠️ Exercício {exercise_id} não encontrado')
                continue
        
        # ============================================================
        # ATUALIZAR EXERCÍCIOS EXISTENTES
        # ============================================================
        
        exercises_to_update = request.data.get('exercises_to_update', [])
        updated_count = 0
        
        for ex_data in exercises_to_update:
            exercise_id = ex_data.get('id')
            
            try:
                we = WorkoutExercise.objects.get(
                    id=exercise_id,
                    workout=workout
                )
                
                # Atualizar campos fornecidos
                if 'sets' in ex_data:
                    we.sets = ex_data['sets']
                if 'reps' in ex_data:
                    we.reps = ex_data['reps']
                if 'weight' in ex_data:
                    we.weight = ex_data['weight']
                if 'rest_time' in ex_data:
                    we.rest_time = ex_data['rest_time']
                if 'order_in_workout' in ex_data:
                    we.order_in_workout = ex_data['order_in_workout']
                if 'notes' in ex_data:
                    we.notes = ex_data['notes']
                
                we.save()
                updated_count += 1
                print(f'  ✏️ Atualizado: {we.exercise.name}')
                
            except WorkoutExercise.DoesNotExist:
                print(f'  ⚠️ Exercício {exercise_id} não encontrado')
                continue
        
        # ============================================================
        # ADICIONAR NOVOS EXERCÍCIOS
        # ============================================================
        
        exercises_to_add = request.data.get('exercises_to_add', [])
        added_count = 0
        
        for ex_data in exercises_to_add:
            exercise_id = ex_data.get('exercise_id')
            
            if not exercise_id:
                print(f'  ⚠️ exercise_id ausente')
                continue
            
            try:
                exercise = Exercise.objects.get(id=exercise_id)
                
                # Calcular ordem se não fornecida
                order = ex_data.get('order_in_workout')
                if not order:
                    max_order = WorkoutExercise.objects.filter(
                        workout=workout
                    ).aggregate(Max('order_in_workout'))['order_in_workout__max'] or 0
                    order = max_order + 1
                
                we = WorkoutExercise.objects.create(
                    workout=workout,
                    exercise=exercise,
                    sets=ex_data.get('sets', 3),
                    reps=ex_data.get('reps', '10'),
                    weight=ex_data.get('weight'),
                    rest_time=ex_data.get('rest_time', 60),
                    order_in_workout=order,
                    notes=ex_data.get('notes', '')
                )
                
                added_count += 1
                print(f'  ➕ Adicionado: {exercise.name}')
                
            except Exercise.DoesNotExist:
                print(f'  ⚠️ Exercício {exercise_id} não encontrado no banco')
                continue
        
        # ============================================================
        # RESPOSTA COM RESUMO
        # ============================================================
        
        # Recarregar exercícios do treino
        updated_exercises = WorkoutExercise.objects.filter(
            workout=workout
        ).select_related('exercise').order_by('order_in_workout')
        
        exercises_data = []
        for we in updated_exercises:
            exercises_data.append({
                'id': we.id,
                'exercise_id': we.exercise.id,
                'exercise_name': we.exercise.name,
                'muscle_group': we.exercise.muscle_group,
                'sets': we.sets,
                'reps': we.reps,
                'weight': we.weight,
                'rest_time': we.rest_time,
                'order': we.order_in_workout
            })
        
        print(f'✅ Edição completa do treino {workout_id}:')
        print(f'   ➕ Adicionados: {added_count}')
        print(f'   ✏️ Atualizados: {updated_count}')
        print(f'   🗑️ Removidos: {removed_count}')
        print(f'   📊 Total final: {len(exercises_data)} exercícios')
        
        return Response({
            'success': True,
            'message': 'Treino editado com sucesso! 📝',
            'workout': {
                'id': workout.id,
                'name': workout.name,
                'description': workout.description,
                'difficulty_level': workout.difficulty_level,
                'estimated_duration': workout.estimated_duration,
                'target_muscle_groups': workout.target_muscle_groups,
                'workout_type': workout.workout_type
            },
            'changes': {
                'exercises_added': added_count,
                'exercises_updated': updated_count,
                'exercises_removed': removed_count,
                'total_exercises': len(exercises_data)
            },
            'exercises': exercises_data
        })
        
    except Workout.DoesNotExist:
        return Response({
            'error': 'Treino não encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        print(f'❌ Erro ao editar treino: {str(e)}')
        import traceback
        traceback.print_exc()
        
        return Response({
            'error': 'Erro ao editar treino',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_exercises_for_editing(request):
    """
    🔍 Lista TODOS os exercícios disponíveis para adicionar ao treino
    Pode filtrar por:
    - muscle_group (query param)
    - difficulty_level (query param)
    - search (query param)
    """
    try:
        # Iniciar query
        exercises = Exercise.objects.all()
        
        # Filtros opcionais
        muscle_group = request.GET.get('muscle_group')
        difficulty = request.GET.get('difficulty_level')
        search = request.GET.get('search')
        
        if muscle_group and muscle_group != 'all':
            exercises = exercises.filter(muscle_group=muscle_group)
        
        if difficulty and difficulty != 'all':
            exercises = exercises.filter(difficulty_level=difficulty)
        
        if search:
            from django.db.models import Q
            exercises = exercises.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        # Limitar a 100 resultados
        exercises = exercises[:100]
        
        exercises_data = []
        for exercise in exercises:
            exercises_data.append({
                'id': exercise.id,
                'name': exercise.name,
                'description': exercise.description,
                'muscle_group': exercise.muscle_group,
                'difficulty_level': exercise.difficulty_level,
                'equipment_needed': exercise.equipment_needed,
                'duration_minutes': exercise.duration_minutes,
                'video_url': exercise.video_url,
                #'image_url': exercise.image_url,
            })
        
        print(f'✅ {len(exercises_data)} exercícios disponíveis')
        
        return Response({
            'success': True,
            'exercises': exercises_data,
            'total': len(exercises_data),
            'filters_applied': {
                'muscle_group': muscle_group,
                'difficulty_level': difficulty,
                'search': search
            }
        })
        
    except Exception as e:
        print(f'❌ Erro ao buscar exercícios: {str(e)}')
        return Response({
            'error': 'Erro ao buscar exercícios',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_workout(request, workout_id):
    """
    🗑️ Deleta um treino usando SOFT DELETE
    
    Regras:
    - ✅ Treinos personalizados: só o criador pode deletar
    - ❌ Treinos do catálogo: apenas admins
    - ⚠️ Não deleta fisicamente, apenas marca como inativo
    - ✅ Pode ser restaurado depois
    """
    try:
        workout = Workout.objects.get(id=workout_id)
        
        # ============================================================
        # VALIDAÇÃO 1: VERIFICAR SE JÁ ESTÁ DELETADO
        # ============================================================
        
        if not workout.is_active:
            return Response({
                'error': 'Este treino já foi deletado',
                'workout_name': workout.name,
                'deleted_at': workout.deleted_at,
                'deleted_by': workout.deleted_by.username if workout.deleted_by else None,
                'suggestion': 'Use a rota de restauração para recuperá-lo'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ============================================================
        # VALIDAÇÃO 2: VERIFICAR PERMISSÕES
        # ============================================================
        
        # Treinos do catálogo (públicos)
        if not workout.is_personalized:
            if not request.user.is_staff:
                return Response({
                    'error': 'Apenas administradores podem deletar treinos do catálogo',
                    'workout_name': workout.name,
                    'is_catalog': True
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Treinos personalizados
        else:
            if workout.created_by_user != request.user:
                return Response({
                    'error': 'Você não tem permissão para deletar este treino',
                    'workout_name': workout.name,
                    'owner': workout.created_by_user.username if workout.created_by_user else 'Sistema'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # ============================================================
        # VALIDAÇÃO 3: VERIFICAR SESSÕES ATIVAS
        # ============================================================
        
        active_sessions = WorkoutSession.objects.filter(
            workout=workout,
            completed=False
        )
        
        if active_sessions.exists():
            return Response({
                'error': 'Não é possível deletar este treino',
                'reason': 'Existem sessões ativas usando este treino',
                'active_sessions_count': active_sessions.count(),
                'suggestion': 'Cancele ou complete as sessões ativas primeiro'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ============================================================
        # SOFT DELETE: MARCAR COMO INATIVO
        # ============================================================
        
        workout_name = workout.name
        workout_type = 'personalizado' if workout.is_personalized else 'catálogo'
        
        # Contar sessões completas (para informação)
        completed_sessions_count = WorkoutSession.objects.filter(
            workout=workout,
            completed=True
        ).count()
        
        # Marcar como deletado
        workout.is_active = False
        workout.deleted_at = timezone.now()
        workout.deleted_by = request.user
        workout.save()
        
        print(f'✅ Treino soft-deleted: {workout_name} (ID: {workout_id})')
        print(f'   Por: {request.user.username}')
        print(f'   Em: {workout.deleted_at}')
        
        return Response({
            'success': True,
            'message': f'Treino "{workout_name}" removido com sucesso',
            'action': 'soft_delete',
            'workout': {
                'id': workout.id,
                'name': workout_name,
                'type': workout_type,
                'deleted_at': workout.deleted_at,
                'deleted_by': request.user.username
            },
            'info': {
                'completed_sessions_preserved': completed_sessions_count,
                'can_be_restored': True,
                'restore_instructions': 'Use POST /api/workouts/{id}/restore/ para restaurar'
            }
        })
        
    except Workout.DoesNotExist:
        return Response({
            'error': 'Treino não encontrado',
            'workout_id': workout_id
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        print(f'❌ Erro ao deletar treino {workout_id}: {str(e)}')
        import traceback
        traceback.print_exc()
        
        return Response({
            'error': 'Erro ao deletar treino',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def restore_workout(request, workout_id):
    """
    ♻️ Restaura um treino deletado (soft delete)
    """
    try:
        # Buscar treino deletado
        workout = Workout.objects.get(id=workout_id, is_active=False)
        
        # ============================================================
        # VALIDAÇÃO: VERIFICAR PERMISSÕES
        # ============================================================
        
        # Treinos do catálogo: só admin
        if not workout.is_personalized and not request.user.is_staff:
            return Response({
                'error': 'Apenas administradores podem restaurar treinos do catálogo'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Treinos personalizados: só o criador ou admin
        if workout.is_personalized:
            if workout.created_by_user != request.user and not request.user.is_staff:
                return Response({
                    'error': 'Você não tem permissão para restaurar este treino',
                    'owner': workout.created_by_user.username if workout.created_by_user else 'Sistema'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # ============================================================
        # RESTAURAR
        # ============================================================
        
        workout_name = workout.name
        deleted_info = {
            'was_deleted_at': workout.deleted_at,
            'was_deleted_by': workout.deleted_by.username if workout.deleted_by else None
        }
        
        # Limpar campos de deleção
        workout.is_active = True
        workout.deleted_at = None
        workout.deleted_by = None
        workout.save()
        
        print(f'♻️ Treino restaurado: {workout_name} (ID: {workout_id})')
        print(f'   Por: {request.user.username}')
        
        return Response({
            'success': True,
            'message': f'Treino "{workout_name}" restaurado com sucesso! 🎉',
            'workout': {
                'id': workout.id,
                'name': workout_name,
                'is_active': workout.is_active,
                'restored_by': request.user.username,
                'restored_at': timezone.now()
            },
            'previous_deletion': deleted_info
        })
        
    except Workout.DoesNotExist:
        return Response({
            'error': 'Treino deletado não encontrado',
            'workout_id': workout_id,
            'suggestion': 'Verifique se o ID está correto e se o treino foi realmente deletado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        print(f'❌ Erro ao restaurar treino {workout_id}: {str(e)}')
        import traceback
        traceback.print_exc()
        
        return Response({
            'error': 'Erro ao restaurar treino',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
    

# ============================================================
# ✅ FUNÇÃO AUXILIAR: Extrair dados do UserProfile REAL
# ============================================================

def _extract_user_data_from_profile(profile):
    """
    Extrai dados do UserProfile real do Django
    
    Args:
        profile: UserProfile object
    
    Returns:
        dict com dados formatados para o prompt
    """
    user = profile.user
    
    # ✅ Nome (priorizar first_name, fallback username)
    nome = user.first_name or user.username
    
    # ✅ Idade
    idade = profile.age or 25
    
    # ✅ Sexo
    gender_map = {
        'M': 'Masculino',
        'F': 'Feminino',
        'O': 'Outro',
        None: 'Não informado'
    }
    sexo = gender_map.get(profile.gender, 'Não informado')
    
    # ✅ Peso e altura
    peso_atual = profile.current_weight or 70
    peso_desejado = profile.target_weight or peso_atual
    altura = profile.height or 170
    
    # ✅ Metas (converter choice para texto legível)
    goal_map = {
        'lose_weight': 'Perder peso',
        'gain_muscle': 'Ganhar massa muscular',
        'maintain': 'Manter forma física',
        'endurance': 'Melhorar resistência',
        None: 'Condicionamento geral'
    }
    meta_principal = goal_map.get(profile.goal, 'Condicionamento geral')
    metas = [meta_principal]  # Lista para compatibilidade
    
    # ✅ Áreas de foco (string CSV → lista)
    if profile.focus_areas:
        areas_desejadas = [area.strip() for area in profile.focus_areas.split(',')]
    else:
        areas_desejadas = ['Corpo completo']
    
    # ✅ Nível de atividade
    activity_map = {
        'sedentary': 'Sedentário',
        'light': 'Levemente ativo',
        'moderate': 'Moderadamente ativo',
        'active': 'Ativo',
        'very_active': 'Muito ativo',
        None: 'Iniciante'
    }
    nivel_atividade = activity_map.get(profile.activity_level, 'Iniciante')
    
    # ✅ Frequência semanal
    frequencia_semanal = profile.training_frequency or 3
    
    # ✅ Dias preferidos (JSONField → lista nomes)
    dias_semana = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
    preferred_days = profile.preferred_training_days or []
    dias_preferidos_nomes = [dias_semana[d] for d in preferred_days if 0 <= d <= 6]
    
    # ✅ Horário preferido
    time_map = {
        'morning': 'Manhã',
        'afternoon': 'Tarde',
        'evening': 'Noite',
        'flexible': 'Flexível'
    }
    horario_preferido = time_map.get(profile.preferred_workout_time, 'Flexível')
    
    # ✅ Limitações físicas
    limitacoes = profile.physical_limitations or ''
    
    # ✅ Equipamentos (inferir do goal + activity_level)
    # Se não tem campo explícito, fazer suposição razoável
    if profile.activity_level in ['sedentary', 'light']:
        equipamentos = 'Peso corporal e elásticos'
    elif profile.activity_level == 'moderate':
        equipamentos = 'Halteres e peso corporal'
    else:
        equipamentos = 'Academia completa'
    
    # ✅ Tempo disponível (inferir da frequência)
    if frequencia_semanal <= 2:
        tempo_disponivel = '45-60 minutos'
    elif frequencia_semanal <= 4:
        tempo_disponivel = '30-45 minutos'
    else:
        tempo_disponivel = '20-30 minutos'
    
    # ✅ Tipos de treino preferidos (inferir do goal)
    if profile.goal == 'lose_weight':
        tipos_treino = ['Cardio', 'HIIT', 'Circuito']
    elif profile.goal == 'gain_muscle':
        tipos_treino = ['Musculação', 'Força', 'Hipertrofia']
    elif profile.goal == 'endurance':
        tipos_treino = ['Cardio', 'Resistência', 'Funcional']
    else:
        tipos_treino = ['Variados', 'Funcional']
    
    return {
        'nome': nome,
        'idade': idade,
        'sexo': sexo,
        'peso_atual': peso_atual,
        'peso_desejado': peso_desejado,
        'altura': altura,
        'metas': metas,
        'areas_desejadas': areas_desejadas,
        'nivel_atividade': nivel_atividade,
        'frequencia_semanal': frequencia_semanal,
        'preferred_training_days': preferred_days,  # Lista de ints
        'dias_preferidos_nomes': dias_preferidos_nomes,  # Lista de strings
        'horario_preferido': horario_preferido,
        'limitacoes_fisicas': limitacoes,
        'equipamentos': equipamentos,
        'tempo_disponivel': tempo_disponivel,
        'tipos_treino': tipos_treino,
        # Extras úteis
        'descanso_minimo': profile.min_rest_days_between_workouts or 1,
        'bmi': profile.calculate_bmi(),
        'bmi_status': profile.get_bmi_status(),
    }


# ============================================================
# ✅ PROMPT PLANO SEMANAL - Usando dados reais
# ============================================================

def _build_weekly_plan_prompt(user_data):
    """
    Prompt para PLANO SEMANAL usando dados do UserProfile real
    
    Args:
        user_data: dict retornado por _extract_user_data_from_profile()
    """
    
    # Extrair dados
    nome = user_data['nome']
    idade = user_data['idade']
    sexo = user_data['sexo']
    peso_atual = user_data['peso_atual']
    peso_desejado = user_data['peso_desejado']
    altura = user_data['altura']
    bmi = user_data['bmi'] or 23.0
    bmi_status = user_data['bmi_status'] or 'Normal'
    
    metas = ', '.join(user_data['metas'])
    areas_desejadas = ', '.join(user_data['areas_desejadas'])
    tipos_treino = ', '.join(user_data['tipos_treino'])
    equipamentos = user_data['equipamentos']
    limitacoes = user_data['limitacoes_fisicas']
    
    nivel_atividade = user_data['nivel_atividade']
    frequencia = user_data['frequencia_semanal']
    tempo = user_data['tempo_disponivel']
    horario = user_data['horario_preferido']
    dias_preferidos = user_data['dias_preferidos_nomes']
    
    # Mapear nível → dificuldade
    nivel_lower = nivel_atividade.lower()
    if 'sedentário' in nivel_lower or 'sedentario' in nivel_lower:
        difficulty = 'beginner'
        nivel_texto = 'iniciante (sedentário)'
    elif 'levemente' in nivel_lower or 'leve' in nivel_lower:
        difficulty = 'beginner'
        nivel_texto = 'iniciante'
    elif 'moderado' in nivel_lower:
        difficulty = 'intermediate'
        nivel_texto = 'intermediário'
    elif 'ativo' in nivel_lower and 'muito' not in nivel_lower:
        difficulty = 'intermediate'
        nivel_texto = 'intermediário avançado'
    else:
        difficulty = 'advanced'
        nivel_texto = 'avançado'
    
    # Calcular exercícios por tempo
    if '15-30' in tempo or '20-30' in tempo:
        ex_count = 4
        duration = 25
    elif '30-45' in tempo:
        ex_count = 5
        duration = 40
    elif '45-60' in tempo:
        ex_count = 6
        duration = 50
    else:
        ex_count = 7
        duration = 60
    
    # Focos por frequência
    if frequencia <= 2:
        focos = ['corpo_completo', 'funcional']
        focos_texto = 'Corpo completo e funcional'
    elif frequencia == 3:
        focos = ['superior', 'inferior', 'corpo_completo']
        focos_texto = 'Superior, inferior e corpo completo'
    elif frequencia == 4:
        focos = ['superior_a', 'inferior', 'superior_b', 'cardio']
        focos_texto = 'Superior A, inferior, superior B, cardio'
    elif frequencia == 5:
        focos = ['peito_triceps', 'pernas', 'costas_biceps', 'ombros', 'cardio']
        focos_texto = 'Peito/tríceps, pernas, costas/bíceps, ombros, cardio'
    else:
        focos = ['peito', 'pernas', 'costas', 'ombros_bracos', 'funcional', 'cardio']
        focos_texto = 'Divisão completa por grupo muscular'
    
    # Dias da semana
    if dias_preferidos:
        dias_treino_texto = ', '.join(dias_preferidos[:frequencia])
    else:
        dias_semana = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
        if frequencia == 3:
            dias_treino_texto = 'Segunda, Quarta, Sexta'
        elif frequencia == 4:
            dias_treino_texto = 'Segunda, Terça, Quinta, Sexta'
        else:
            dias_treino_texto = ', '.join(dias_semana[:frequencia])
    
    # PROMPT EM PORTUGUÊS
    return f'''
Você é um personal trainer expert criando um PLANO SEMANAL.

👤 PERFIL: {nome}, {idade} anos, {sexo}
📊 Dados: {peso_atual}kg → {peso_desejado}kg | Altura: {altura}cm | IMC: {bmi:.1f}
💪 Nível: {nivel_texto} | Meta: {metas}
📅 Frequência: {frequencia}x/semana | Tempo: {tempo}min/treino

⚠️ REGRA CRÍTICA: Crie EXATAMENTE {frequencia} treinos.

✅ JSON (SEM markdown, SEM comentários):
{{
  "weekly_plan": [
    {{
      "day_name": "Segunda",
      "workout_name": "Nome Motivacional",
      "description": "Descrição curta (máx 80 chars)",
      "difficulty_level": "{difficulty}",
      "estimated_duration": {duration},
      "target_muscle_groups": "grupos",
      "equipment_needed": "{equipamentos}",
      "workout_type": "strength",
      "calories_estimate": 250,
      "exercises": [
        {{
          "name": "Nome do Exercício",
          "description": "Como fazer (máx 100 chars)",
          "muscle_group": "grupo",
          "difficulty_level": "{difficulty}",
          "equipment_needed": "equip",
          "duration_minutes": 5,
          "sets": 3,
          "reps": "12",
          "rest_time": 60,
          "order_in_workout": 1,
          "instructions": ["Passo 1", "Passo 2"],
          "tips": ["Dica 1"]
        }}
      ]
    }}
  ]
}}

🎯 IMPORTANTE:
- EXATAMENTE {frequencia} treinos
- {ex_count} exercícios por treino
- Descrições CURTAS (evitar texto longo)
- JSON válido (fechar todas chaves)

Distribuição: {focos_texto}
'''


# ============================================================
# ✅ PROMPT TREINO ÚNICO - Usando dados reais
# ============================================================

def _build_onboarding_prompt(user_data):
    """
    Prompt para TREINO ÚNICO usando dados do UserProfile real
    
    Args:
        user_data: dict retornado por _extract_user_data_from_profile()
    """
    
    # Extrair dados
    nome = user_data['nome']
    idade = user_data['idade']
    sexo = user_data['sexo']
    peso_atual = user_data['peso_atual']
    peso_desejado = user_data['peso_desejado']
    altura = user_data['altura']
    bmi = user_data['bmi'] or 23.0
    bmi_status = user_data['bmi_status'] or 'Normal'
    
    metas = ', '.join(user_data['metas'])
    areas = ', '.join(user_data['areas_desejadas'])
    tipos = ', '.join(user_data['tipos_treino'])
    equip = user_data['equipamentos']
    limitacoes = user_data['limitacoes_fisicas']
    tempo = user_data['tempo_disponivel']
    
    nivel_atividade = user_data['nivel_atividade']
    
    # Mapear nível → dificuldade
    nivel_lower = nivel_atividade.lower()
    if 'sedentário' in nivel_lower or 'sedentario' in nivel_lower:
        difficulty = 'beginner'
        nivel_texto = 'iniciante'
    elif 'levemente' in nivel_lower or 'leve' in nivel_lower:
        difficulty = 'beginner'
        nivel_texto = 'iniciante'
    elif 'moderado' in nivel_lower:
        difficulty = 'intermediate'
        nivel_texto = 'intermediário'
    else:
        difficulty = 'intermediate'
        nivel_texto = 'avançado'
    
    # Calcular exercícios
    if '15-30' in tempo or '20-30' in tempo:
        ex_count = 5
        duration = 25
    elif '30-45' in tempo:
        ex_count = 7
        duration = 35
    elif '45-60' in tempo:
        ex_count = 9
        duration = 50
    else:
        ex_count = 10
        duration = 60
    
    return f'''
Você é um personal trainer expert criando um TREINO PERSONALIZADO.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 PERFIL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 {nome}, {idade} anos, {sexo}
⚖️ {peso_atual}kg → Meta: {peso_desejado}kg
📏 {altura}cm | IMC: {bmi:.1f} ({bmi_status})
💪 Nível: {nivel_texto}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 OBJETIVOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Metas: {metas}
🎪 Focos: {areas}
🏋️ Preferências: {tipos}
🛠️ Equipamentos: {equip}
⏰ Tempo: {tempo}
{f'⚠️ LIMITAÇÕES: {limitacoes}' if limitacoes else ''}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 CRIAR TREINO:
• {ex_count} exercícios ESPECÍFICOS
• Duração: {duration} minutos
• Nível: {difficulty}
• PORTUGUÊS BRASILEIRO

⚠️ JSON (sem markdown):
{{
  "workout_name": "Nome Motivacional",
  "description": "Foco e objetivo (máx 120 chars)",
  "difficulty_level": "{difficulty}",
  "estimated_duration": {duration},
  "target_muscle_groups": "{areas}",
  "equipment_needed": "{equip}",
  "workout_type": "full_body",
  "calories_estimate": 250,
  "exercises": [
    {{
      "name": "Nome Específico em Português",
      "description": "Execução clara (máx 150 chars)",
      "muscle_group": "grupo",
      "difficulty_level": "{difficulty}",
      "equipment_needed": "equipamento",
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

✅ REGRAS:
1. Português brasileiro
2. Exercícios específicos (ex: "Rosca Martelo")
3. Respeitar: {equip}
4. Focar: {areas}
5. Nível: {nivel_texto}
{f'6. EVITAR: {limitacoes}' if limitacoes else ''}

Crie o treino perfeito para {nome}! 💪
'''


# ============================================================
# ✅ ATUALIZAR A VIEW generate_onboarding_workout
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_onboarding_workout(request):
    """Gera PLANO SEMANAL ou TREINO ÚNICO usando UserProfile real"""
    try:
        from django.conf import settings
        import google.generativeai as genai
        
        user = request.user
        
        # ✅ BUSCAR PERFIL REAL
        try:
            profile = user.userprofile
        except UserProfile.DoesNotExist:
            return Response({
                'error': 'Perfil não encontrado',
                'message': 'Complete seu perfil antes de gerar treinos'
            }, status=400)
        
        # ✅ EXTRAIR DADOS DO PERFIL REAL
        user_data = _extract_user_data_from_profile(profile)
        
        print(f"🤖 Gerando treino para: {user_data['nome']}")
        print(f"   Nível: {user_data['nivel_atividade']}")
        print(f"   Frequência: {user_data['frequencia_semanal']}x/semana")
        
        # ✅ VERIFICAR SE É PLANO SEMANAL
        frequencia = user_data['frequencia_semanal']
        generate_plan = frequencia > 1  # Plano se treina mais de 1x
        
        # ✅ CONSTRUIR PROMPT
        if generate_plan:
            print(f"📅 Gerando PLANO SEMANAL: {frequencia} dias")
            ai_prompt = _build_weekly_plan_prompt(user_data)
        else:
            print(f"📝 Gerando treino único")
            ai_prompt = _build_onboarding_prompt(user_data)
        
        # ✅ CHAMAR IA
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not api_key:
            raise ValueError("GEMINI_API_KEY não configurada")
        
        genai.configure(api_key=api_key)
        model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash-exp')
        model = genai.GenerativeModel(model_name)
        
        generation_config = {
            'max_output_tokens': 16384,
            'temperature': 0.7,  # ✅ Aumentar criatividade
            'response_mime_type': 'application/json',
        }
        
        response = model.generate_content(ai_prompt, generation_config=generation_config)
        plan_data = _extract_json_from_ai_response(response.text)
        
        if not plan_data:
            raise ValueError("JSON inválido retornado pela IA")
        
        # ✅ CRIAR TREINOS
        if generate_plan and 'weekly_plan' in plan_data:
            created_workouts = []
            
            for idx, workout_data in enumerate(plan_data['weekly_plan']):
                workout = _create_ai_workout(
                    user, workout_data, user_data,
                    is_part_of_plan=True,
                    plan_day=idx + 1
                )
                created_workouts.append({
                    'id': workout.id,
                    'name': workout.name,
                    'duration': workout.estimated_duration,
                    'exercises_count': workout.workout_exercises.count(),
                })
            
            return Response({
                'success': True,
                'is_weekly_plan': True,
                'message': f'{len(created_workouts)} treinos criados!',
                'plan_summary': {
                    'total_workouts': len(created_workouts),
                    'frequency': frequencia,
                    'total_weekly_duration': sum(w['duration'] for w in created_workouts),
                },
                'workouts': created_workouts,
            }, status=201)
        else:
            workout = _create_ai_workout(user, plan_data, user_data)
            
            return Response({
                'success': True,
                'is_weekly_plan': False,
                'workout_id': workout.id,
                'workout_name': workout.name,
                'exercises_count': workout.workout_exercises.count(),
            }, status=201)
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': 'Erro ao gerar treino',
            'details': str(e)
        }, status=500)

# ============================================================
# FUNÇÃO _create_ai_workout (atualizar)
# ============================================================

def _create_ai_workout(user, workout_data, user_profile, is_part_of_plan=False, plan_day=None):
    """Cria Workout no banco"""
    
    # Metadata
    if is_part_of_plan:
        ai_metadata = f"\n\n🤖 Treino {plan_day} do Plano Semanal"
    else:
        ai_metadata = f"\n\n🤖 Treino gerado por IA"
    
    description = workout_data.get('description', '')
    full_description = description + ai_metadata
    
    # ✅ CRÍTICO: is_recommended=True
    workout = Workout.objects.create(
        name=workout_data.get('workout_name', 'Treino Personalizado'),
        description=full_description,
        difficulty_level=workout_data.get('difficulty_level', 'beginner'),
        estimated_duration=workout_data.get('estimated_duration', 30),
        target_muscle_groups=workout_data.get('target_muscle_groups', ''),
        equipment_needed=workout_data.get('equipment_needed', 'Variado'),
        calories_estimate=workout_data.get('calories_estimate', 200),
        workout_type=workout_data.get('workout_type', 'full_body'),
        is_recommended=True,
        is_personalized=True,      # ✅ Vai para "Recomendados FitAI"
        created_by_user=user,
    )
    
    # Adicionar exercícios
    exercises_data = workout_data.get('exercises', [])
    
    for idx, ex_data in enumerate(exercises_data, start=1):
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
    
    return workout

def _extract_json_from_ai_response(text):
    """Extrai e limpa JSON - VERSÃO ROBUSTA"""
    import re
    import json
    
    print(f'📝 Processando {len(text)} caracteres...')
    
    # ============================================================
    # 1. EXTRAIR JSON
    # ============================================================
    json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        json_text = json_match.group(1)
        print('✅ JSON extraído de markdown')
    else:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
            print('✅ JSON extraído diretamente')
        else:
            print('❌ JSON não encontrado')
            return None
    
    # ============================================================
    # 2. LIMPEZA AGRESSIVA
    # ============================================================
    
    # Remove caracteres de controle
    json_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_text)
    
    # Remove comentários
    json_text = re.sub(r'//.*?\n', '\n', json_text)
    json_text = re.sub(r'/\*.*?\*/', '', json_text, flags=re.DOTALL)
    
    # Remove quebras de linha DENTRO de strings (CRÍTICO!)
    def remove_newlines_in_strings(match):
        string_content = match.group(1)
        # Remove \n e \r
        cleaned = string_content.replace('\n', ' ').replace('\r', ' ')
        # Remove espaços múltiplos
        cleaned = re.sub(r'\s+', ' ', cleaned)
        # Remove aspas internas (causa erro)
        cleaned = cleaned.replace('"', '')
        return f'"{cleaned.strip()}"'
    
    # Aplicar limpeza em todas as strings
    json_text = re.sub(r'"((?:[^"\\]|\\.)*)?"', remove_newlines_in_strings, json_text)
    
    # Truncar strings muito longas
    def truncate_long_strings(match):
        content = match.group(1)
        if len(content) > 300:
            return f'"{content[:297]}..."'
        return match.group(0)
    
    json_text = re.sub(r'"([^"]{300,})"', truncate_long_strings, json_text)
    
    # Remove trailing commas
    json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
    
    # ============================================================
    # 3. PARSEAR JSON
    # ============================================================
    try:
        data = json.loads(json_text)
        print('✅ JSON parseado com sucesso!')
        
        # Validar estrutura
        if 'weekly_plan' in data:
            if isinstance(data['weekly_plan'], list) and len(data['weekly_plan']) > 0:
                print(f'✅ Plano com {len(data["weekly_plan"])} treinos')
                return data
            else:
                print('❌ weekly_plan inválido')
                return None
        elif 'exercises' in data:
            if isinstance(data['exercises'], list) and len(data['exercises']) > 0:
                print(f'✅ Treino com {len(data["exercises"])} exercícios')
                return data
            else:
                print('❌ exercises inválido')
                return None
        else:
            print('⚠️ Estrutura desconhecida, mas JSON válido')
            return data
            
    except json.JSONDecodeError as e:
        print(f'❌ ERRO JSON: linha {e.lineno}, coluna {e.colno}')
        print(f'   Mensagem: {e.msg}')
        
        # Mostrar contexto do erro
        lines = json_text.split('\n')
        if e.lineno <= len(lines):
            start = max(0, e.lineno - 2)
            end = min(len(lines), e.lineno + 1)
            print('📍 Contexto:')
            for i in range(start, end):
                prefix = '>>> ' if i == e.lineno - 1 else '    '
                print(f'{prefix}L{i+1}: {lines[i][:100]}')
        
        # Salvar para análise
        try:
            import tempfile, os
            error_file = os.path.join(
                tempfile.gettempdir(), 
                f'gemini_error_{int(timezone.now().timestamp())}.txt'
            )
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write('=== RESPOSTA ORIGINAL ===\n\n')
                f.write(text)
                f.write('\n\n=== JSON LIMPO ===\n\n')
                f.write(json_text)
            print(f'💾 Erro salvo em: {error_file}')
        except Exception as save_err:
            print(f'⚠️ Não salvou arquivo: {save_err}')
        
        return None



# RECOMENDAR CARD

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def smart_recommendation_view(request):
    """
    🧠 Recomendação Inteligente CORRIGIDA
    
    Considera:
    ✅ training_frequency (meta semanal REAL)
    ✅ preferred_training_days (dias preferidos)
    ✅ min_rest_days_between_workouts (descanso mínimo)
    ✅ activity_level (nível correto → dificuldade)
    ✅ goal (objetivo do usuário)
    ✅ physical_limitations (lesões/restrições)
    ✅ preferred_workout_time (horário preferido)
    
    Busca treinos:
    1. Treinos gerados pela IA (is_recommended=True + created_by_user)
    2. Treinos criados pelo usuário via chat/manual
    3. Treinos do catálogo compatíveis
    """
    try:
        user = request.user
        profile = user.userprofile
        
        print(f'🧠 Gerando recomendação inteligente para: {user.username}')
        print(f'   Nível: {profile.activity_level}')
        print(f'   Meta semanal: {profile.training_frequency} dias')
        print(f'   Descanso mínimo: {profile.min_rest_days_between_workouts} dias')
        
        # ============================================================
        # 1. BUSCAR RECOMENDAÇÃO DIÁRIA DA IA (Gemini)
        # ============================================================
        
        ai_recommendation = None
        try:
            ai_service = AIService()
            ai_recommendation = ai_service.generate_daily_recommendation(profile)
            
            if ai_recommendation:
                print(f'✅ IA sugeriu: {ai_recommendation.get("recommendation_type", "workout")}')
                print(f'   Foco: {ai_recommendation.get("focus_area", "N/A")}')
                print(f'   Intensidade: {ai_recommendation.get("intensity", "N/A")}')
        except Exception as e:
            print(f'⚠️ IA falhou: {e}')
        
        # ============================================================
        # 2. ANÁLISE DO HISTÓRICO DO USUÁRIO
        # ============================================================
        
        from datetime import datetime, timedelta
        
        # Último treino
        last_session = WorkoutSession.objects.filter(
            user=user,
            completed=True
        ).order_by('-completed_at').first()
        
        # ✅ CORRIGIDO: None se nunca treinou
        days_since_last = None
        last_workout_date = None
        
        if last_session:
            session_date = last_session.completed_at or last_session.started_at
            if session_date:
                last_workout_date = session_date.date()
                days_since_last = (timezone.now().date() - last_workout_date).days
        
        # Treinos esta semana (últimos 7 dias)
        week_ago = timezone.now() - timedelta(days=7)
        workouts_this_week = WorkoutSession.objects.filter(
            user=user,
            completed=True,
            started_at__gte=week_ago
        ).count()
        
        # ✅ USAR META REAL DO PERFIL
        weekly_goal = profile.training_frequency
        
        # Dia da semana atual (0=Dom, 6=Sáb)
        today_weekday = (timezone.now().weekday() + 1) % 7
        
        # ✅ VERIFICAR SE É DIA PREFERIDO
        is_preferred_day = profile.is_preferred_training_day(today_weekday)
        is_rest_day = profile.is_preferred_rest_day(today_weekday)
        
        print(f'📊 Análise:')
        print(f'   Último treino: {days_since_last} dias atrás' if days_since_last is not None else '   Último treino: Nunca')
        print(f'   Esta semana: {workouts_this_week}/{weekly_goal}')
        print(f'   Hoje é preferido: {is_preferred_day}')
        print(f'   Hoje é descanso: {is_rest_day}')
        
        # ============================================================
        # 3. VERIFICAR SE DEVE DESCANSAR (REGRAS INTELIGENTES)
        # ============================================================
        
        should_rest = False
        rest_reason = None
        rest_priority = 0  # 1=sugestão, 2=recomendado, 3=obrigatório
        
        # REGRA 1: Dia de descanso configurado (prioridade média)
        if is_rest_day:
            should_rest = True
            rest_reason = f"Hoje não é um dos seus dias preferidos de treino 📅"
            rest_priority = 2
        
        # REGRA 2: Já treinou hoje (prioridade alta)
        if days_since_last == 0:
            should_rest = True
            rest_reason = "Você já treinou hoje! Músculos precisam de recuperação 🧘"
            rest_priority = 3
        
        # REGRA 3: Meta semanal atingida (prioridade alta)
        elif workouts_this_week >= weekly_goal:
            should_rest = True
            rest_reason = f"Meta semanal completa ({workouts_this_week}/{weekly_goal})! Parabéns! 🎉"
            rest_priority = 3
        
        # REGRA 4: Descanso mínimo não cumprido (prioridade alta)
        elif last_workout_date and profile.should_rest_today(last_workout_date):
            should_rest = True
            rest_reason = f"Seu corpo precisa de descanso ({days_since_last}/{profile.min_rest_days_between_workouts} dias)"
            rest_priority = 3
        
        # ============================================================
        # SE DEVE DESCANSAR, RETORNAR RECOMENDAÇÃO DE DESCANSO
        # ============================================================
        
        if should_rest and rest_priority >= 2:  # Apenas se recomendado ou obrigatório
            print(f'😴 Recomendação: DESCANSO (prioridade {rest_priority})')
            
            # Fatores de personalização
            factors = []
            factors.append(f'🎯 Meta: {workouts_this_week}/{weekly_goal} treinos esta semana')
            
            if days_since_last is not None:
                factors.append(f'⏱️ Último treino: há {days_since_last} dia(s)')
            
            if profile.physical_limitations:
                factors.append(f'⚠️ Limitações: {profile.physical_limitations[:50]}...')
            
            factors.append('😴 Descanso é parte do treino!')
            
            return Response({
                'success': True,
                'has_recommendation': False,
                'should_rest': True,
                'rest_priority': 'obrigatório' if rest_priority == 3 else 'recomendado',
                'analysis': {
                    'recommendation_type': 'rest',
                    'recommendation_reason': rest_reason,
                    'days_since_last_workout': days_since_last,
                    'workouts_this_week': workouts_this_week,
                    'weekly_goal': weekly_goal,
                    'is_preferred_day': is_preferred_day,
                    'confidence_score': 0.95,
                    'personalization_factors': factors
                }
            })
        
        # ============================================================
        # 4. BUSCAR TREINO RECOMENDADO (PRIORIDADES CORRETAS)
        # ============================================================
        
        recommended_workout = None
        recommendation_source = None
        
        # ✅ MAPEAR activity_level → difficulty_level
        difficulty_map = {
            'sedentary': 'beginner',
            'light': 'beginner',
            'moderate': 'intermediate',
            'active': 'intermediate',
            'very_active': 'advanced'
        }
        user_difficulty = difficulty_map.get(profile.activity_level, 'beginner')
        
        print(f'🎯 Buscando treinos com dificuldade: {user_difficulty}')
        
        # Determinar foco (da IA ou padrão)
        if ai_recommendation:
            focus_area = ai_recommendation.get('focus_area', 'full_body')
            intensity = ai_recommendation.get('intensity', 'moderate')
        else:
            focus_area = 'full_body'
            intensity = 'moderate'
        
        # Mapear focus_area → workout_type
        focus_to_types = {
            'full_body': ['full_body', 'mixed', 'strength'],
            'upper_body': ['upper_body', 'chest', 'back', 'shoulders'],
            'lower_body': ['lower_body', 'legs'],
            'chest': ['chest', 'upper_body'],
            'back': ['back', 'upper_body'],
            'legs': ['legs', 'lower_body'],
            'arms': ['arms', 'upper_body'],
            'shoulders': ['shoulders', 'upper_body'],
            'cardio': ['cardio', 'hiit'],
            'abs': ['abs', 'core'],
            'recovery': ['flexibility', 'recovery']
        }
        
        target_types = focus_to_types.get(focus_area, ['strength', 'full_body'])
        
        print(f'🔍 Foco: {focus_area} → Tipos: {target_types}')
        
        # ============================================================
        # PRIORIDADE 1: TREINOS GERADOS PELA IA PARA O USUÁRIO
        # ============================================================
        
        for workout_type in target_types:
            recommended_workout = Workout.objects.filter(
                created_by_user=user,
                is_recommended=True,  # ✅ Treinos da IA
                is_personalized=True,
                is_active=True,
                difficulty_level=user_difficulty,
                workout_type__icontains=workout_type
            ).order_by('-created_at').first()  # Mais recente
            
            if recommended_workout:
                recommendation_source = 'ai_generated'
                print(f'✅ [IA] {recommended_workout.name}')
                break
        
        # ============================================================
        # PRIORIDADE 2: TREINOS CRIADOS PELO USUÁRIO (Chat/Manual)
        # ============================================================
        
        if not recommended_workout:
            for workout_type in target_types:
                recommended_workout = Workout.objects.filter(
                    created_by_user=user,
                    is_personalized=True,
                    is_active=True,
                    difficulty_level=user_difficulty,
                    workout_type__icontains=workout_type
                ).order_by('-created_at').first()
                
                if recommended_workout:
                    recommendation_source = 'user_created'
                    print(f'✅ [User] {recommended_workout.name}')
                    break
        
        # ============================================================
        # PRIORIDADE 3: CATÁLOGO PÚBLICO (mesma dificuldade)
        # ============================================================
        
        if not recommended_workout:
            for workout_type in target_types:
                recommended_workout = Workout.objects.filter(
                    is_personalized=False,
                    is_active=True,
                    difficulty_level=user_difficulty,
                    workout_type__icontains=workout_type
                ).order_by('estimated_duration').first()
                
                if recommended_workout:
                    recommendation_source = 'catalog_exact'
                    print(f'✅ [Catalog] {recommended_workout.name}')
                    break
        
        # ============================================================
        # PRIORIDADE 4: CATÁLOGO (dificuldade compatível)
        # ============================================================
        
        if not recommended_workout:
            # Se intermediário, aceitar beginner também
            compatible_difficulties = [user_difficulty]
            if user_difficulty == 'intermediate':
                compatible_difficulties.append('beginner')
            elif user_difficulty == 'advanced':
                compatible_difficulties.extend(['intermediate', 'beginner'])
            
            for workout_type in target_types:
                recommended_workout = Workout.objects.filter(
                    is_personalized=False,
                    is_active=True,
                    difficulty_level__in=compatible_difficulties,
                    workout_type__icontains=workout_type
                ).order_by('estimated_duration').first()
                
                if recommended_workout:
                    recommendation_source = 'catalog_compatible'
                    print(f'✅ [Catalog Compatible] {recommended_workout.name}')
                    break
        
        # ============================================================
        # FALLBACK FINAL: Qualquer treino ativo do nível do usuário
        # ============================================================
        
        if not recommended_workout:
            recommended_workout = Workout.objects.filter(
                is_active=True,
                difficulty_level=user_difficulty
            ).first()
            
            if recommended_workout:
                recommendation_source = 'fallback_level'
                print(f'⚠️ [Fallback] {recommended_workout.name}')
        
        # Último fallback: qualquer treino
        if not recommended_workout:
            recommended_workout = Workout.objects.filter(is_active=True).first()
            recommendation_source = 'fallback_any'
        
        if not recommended_workout:
            return Response({
                'success': False,
                'error': 'Nenhum treino disponível',
                'suggestion': 'Crie um treino personalizado ou entre em contato com o suporte'
            }, status=404)
        
        # ============================================================
        # 5. CONSTRUIR RESPOSTA COM ANÁLISE DETALHADA
        # ============================================================
        
        # Razão da recomendação (personalizada)
        if ai_recommendation:
            base_reason = ai_recommendation.get('message', '')
        else:
            base_reason = _build_recommendation_reason(
                days_since_last, 
                workouts_this_week, 
                weekly_goal,
                is_preferred_day,
                profile
            )
        
        # Fatores de personalização
        factors = []
        
        # Status da meta
        if days_since_last is None:
            factors.append('🆕 Primeiro treino! Comece sua jornada!')
        else:
            factors.append(f'⏱️ Último treino: há {days_since_last} dia(s)')
        
        factors.append(f'🎯 Meta: {workouts_this_week}/{weekly_goal} treinos esta semana')
        
        # Dia preferido
        if is_preferred_day:
            factors.append(f'✅ Hoje é um dos seus dias preferidos de treino!')
        elif not is_rest_day:
            factors.append(f'📅 Treino extra fora dos dias habituais')
        
        # Horário preferido
        if profile.preferred_workout_time != 'flexible':
            time_map = {
                'morning': 'manhã',
                'afternoon': 'tarde',
                'evening': 'noite'
            }
            preferred_time = time_map.get(profile.preferred_workout_time, 'qualquer horário')
            factors.append(f'⏰ Melhor horário: {preferred_time}')
        
        # Limitações físicas
        if profile.physical_limitations:
            factors.append(f'⚠️ Limitações consideradas: {profile.physical_limitations[:50]}...')
        
        # Insights da IA
        if ai_recommendation:
            if ai_recommendation.get('reasoning'):
                factors.append(f'💡 {ai_recommendation["reasoning"]}')
            
            if ai_recommendation.get('motivational_tip'):
                factors.append(f'✨ {ai_recommendation["motivational_tip"]}')
        
        # Confiança
        if ai_recommendation:
            confidence = ai_recommendation.get('metadata', {}).get('confidence', 0.8)
        else:
            # Calcular confiança baseado na qualidade da recomendação
            confidence = 0.6
            if recommendation_source == 'ai_generated':
                confidence = 0.95
            elif recommendation_source == 'user_created':
                confidence = 0.85
            elif recommendation_source == 'catalog_exact':
                confidence = 0.75
        
        print(f'✅ Recomendação: {recommended_workout.name}')
        print(f'   Fonte: {recommendation_source}')
        print(f'   Confiança: {confidence}')
        
        return Response({
            'success': True,
            'has_recommendation': True,
            'workout': {
                'id': recommended_workout.id,
                'name': recommended_workout.name,
                'description': recommended_workout.description,
                'difficulty_level': recommended_workout.difficulty_level,
                'estimated_duration': recommended_workout.estimated_duration,
                'calories_estimate': recommended_workout.calories_estimate,
                'target_muscle_groups': recommended_workout.target_muscle_groups,
                'workout_type': recommended_workout.workout_type,
                'is_personalized': recommended_workout.is_personalized,
                'is_ai_generated': recommended_workout.is_recommended and recommended_workout.is_personalized,
            },
            'analysis': {
                'recommendation_type': ai_recommendation.get('recommendation_type', 'workout') if ai_recommendation else 'workout',
                'recommendation_reason': base_reason,
                'recommendation_source': recommendation_source,
                'days_since_last_workout': days_since_last,
                'workouts_this_week': workouts_this_week,
                'weekly_goal': weekly_goal,
                'is_preferred_day': is_preferred_day,
                'confidence_score': confidence,
                'personalization_factors': factors,
                'pattern_info': {
                    'training_frequency': profile.training_frequency,
                    'min_rest_days': profile.min_rest_days_between_workouts,
                    'preferred_days': profile.preferred_training_days,
                    'preferred_time': profile.preferred_workout_time,
                }
            }
        })
        
    except Exception as e:
        import traceback
        print(f"❌ Erro em smart_recommendation_view: {e}")
        print(traceback.format_exc())
        return Response({
            'success': False,
            'error': 'Erro ao gerar recomendação',
            'details': str(e)
        }, status=500)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def _build_recommendation_reason(days_since_last, workouts_this_week, 
                                weekly_goal, is_preferred_day, profile):
    """Constrói razão personalizada da recomendação"""
    
    user_name = profile.user.first_name or profile.user.username
    
    # Nunca treinou
    if days_since_last is None:
        return f"{user_name}, bem-vindo! Vamos começar sua jornada fitness 🚀"
    
    # Treinou ontem
    if days_since_last == 1:
        if is_preferred_day:
            return f"{user_name}, continue sua sequência! Hoje é um ótimo dia 🔥"
        else:
            return f"{user_name}, mantendo o ritmo! Excelente consistência 💪"
    
    # Treinou há 2-3 dias
    if days_since_last <= 3:
        progress = f"{workouts_this_week}/{weekly_goal}"
        return f"{user_name}, você está em {progress} da meta. Vamos continuar! 💪"
    
    # Treinou há 4-7 dias
    if days_since_last <= 7:
        if workouts_this_week < weekly_goal:
            return f"{user_name}, vamos retomar! Ainda dá para atingir a meta semanal ✨"
        else:
            return f"{user_name}, hora de recomeçar a semana com energia! 🌟"
    
    # Mais de 7 dias
    return f"{user_name}, que tal recomeçar hoje? Treino adaptado ao seu ritmo 🎯"


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def _get_difficulty_for_level(activity_level):
    """Mapeia nível de atividade para dificuldade do treino"""
    level_map = {
        'sedentary': 'beginner',
        'light': 'beginner',
        'moderate': 'intermediate',
        'active': 'intermediate',
        'very_active': 'advanced',
    }
    return level_map.get(activity_level, 'beginner')


def _get_simple_reason(days_since_last, workouts_this_week, weekly_goal):
    """Gera razão simples baseada em dias"""
    
    if days_since_last is None:
        return "Bem-vindo! Vamos começar sua jornada fitness 🚀"
    
    if days_since_last == 0:
        return "Você já treinou hoje, mas pode fazer mais se quiser 💪"
    
    if days_since_last == 1:
        return "Continue sua sequência! Mantendo o ritmo 🔥"
    
    if days_since_last <= 3:
        return "Hora de voltar! Treino balanceado para você 💪"
    
    if days_since_last <= 7:
        return "Vamos retomar! Treino adaptado ao seu nível ✨"
    
    return "Recomeçando! Vamos com calma e progressão 🎯"

# ============================================================
# ✅ FUNÇÃO AUXILIAR: Validar propriedade do treino
# ============================================================

def validate_workout_ownership(workout, user):
    """
    Valida se o usuário é dono do treino
    
    Retorna:
    - True: Se é treino do catálogo OU se é do usuário
    - False: Se é treino de outro usuário
    """
    # Treinos do catálogo são públicos
    if not workout.is_personalized:
        return True
    
    # Treinos personalizados: só o criador
    return workout.created_by_user == user
