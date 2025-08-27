from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Avg, Count
from django.utils import timezone
from .models import Workout, WorkoutExercise, WorkoutSession, ExerciseLog
from apps.users.models import UserProfile
from apps.exercises.models import Exercise

@api_view(['GET'])
def test_workouts_api(request):
    return Response({"message": "Workouts API funcionando!"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_workouts(request):
    """Lista todos os treinos disponíveis"""
    workouts = Workout.objects.all()
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
        filters = Q(is_recommended=True)
        
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
                    'instructions': we.exercise.instructions
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
    """Histórico de treinos do usuário"""
    sessions = WorkoutSession.objects.filter(user=request.user).order_by('-created_at')[:20]
    
    data = []
    for session in sessions:
        data.append({
            'id': session.id,
            'workout_name': session.workout.name,
            'completed': session.completed,
            'started_at': session.started_at,
            'completed_at': session.completed_at,
            'duration_minutes': session.duration_minutes,
            'calories_burned': session.calories_burned,
            'user_rating': session.user_rating,
            'created_at': session.created_at
        })
    
    # Estatísticas
    total_sessions = WorkoutSession.objects.filter(user=request.user).count()
    completed_sessions = WorkoutSession.objects.filter(user=request.user, completed=True).count()
    
    return Response({
        'history': data,
        'statistics': {
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'completion_rate': round(completed_sessions / total_sessions * 100, 1) if total_sessions > 0 else 0
        }
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
def complete_workout_session(request):
    """Finaliza completamente uma sessão de treino"""
    try:
        session = WorkoutSession.objects.get(user=request.user, completed=False)
        
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
        
        # Atualizar progresso do usuário
        from apps.users.models import UserProgress
        try:
            progress = UserProgress.objects.get(user=request.user)
            progress.total_workouts += 1
            progress.save()
        except UserProgress.DoesNotExist:
            UserProgress.objects.create(user=request.user, total_workouts=1)
        
        # Estatísticas da sessão
        total_exercises = ExerciseLog.objects.filter(session=session).count()
        completed_exercises = ExerciseLog.objects.filter(session=session, completed=True, skipped=False).count()
        skipped_exercises = ExerciseLog.objects.filter(session=session, skipped=True).count()
        
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
        return Response({"error": "Nenhuma sessão ativa encontrada"}, 
                       status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cancel_session(request):
    """Cancela a sessão atual"""
    try:
        session = WorkoutSession.objects.get(user=request.user, completed=False)
        
        session_info = {
            "workout_name": session.workout.name,
            "started_at": session.started_at
        }
        
        # Deletar logs da sessão e a sessão
        ExerciseLog.objects.filter(session=session).delete()
        session.delete()
        
        return Response({
            "message": "Sessão cancelada",
            "cancelled_session": session_info
        })
        
    except WorkoutSession.DoesNotExist:
        return Response({"error": "Nenhuma sessão ativa encontrada"}, 
                       status=status.HTTP_404_NOT_FOUND)

# ADICIONAR AO FINAL DO ARQUIVO apps/workouts/views.py

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_analytics(request):
    """Analytics completas do usuário - última semana/mês"""
    from django.db.models import Sum, Avg, Count
    from datetime import datetime, timedelta
    
    # Períodos de análise
    now = timezone.now()
    last_week = now - timedelta(days=7)
    last_month = now - timedelta(days=30)
    
    # Sessões do usuário
    all_sessions = WorkoutSession.objects.filter(user=request.user, completed=True)
    week_sessions = all_sessions.filter(completed_at__gte=last_week)
    month_sessions = all_sessions.filter(completed_at__gte=last_month)
    
    # Estatísticas gerais
    total_workouts = all_sessions.count()
    total_time = all_sessions.aggregate(Sum('duration_minutes'))['duration_minutes__sum'] or 0
    avg_rating = all_sessions.aggregate(Avg('user_rating'))['user_rating__avg'] or 0
    total_calories = all_sessions.aggregate(Sum('calories_burned'))['calories_burned__sum'] or 0
    
    # Estatísticas semanais
    week_workouts = week_sessions.count()
    week_time = week_sessions.aggregate(Sum('duration_minutes'))['duration_minutes__sum'] or 0
    week_calories = week_sessions.aggregate(Sum('calories_burned'))['calories_burned__sum'] or 0
    
    # Estatísticas mensais
    month_workouts = month_sessions.count()
    month_time = month_sessions.aggregate(Sum('duration_minutes'))['duration_minutes__sum'] or 0
    month_calories = month_sessions.aggregate(Sum('calories_burned'))['calories_burned__sum'] or 0
    
    # Treinos mais realizados
    popular_workouts = (all_sessions.values('workout__name')
                       .annotate(count=Count('id'))
                       .order_by('-count')[:5])
    
    # Análise de consistência (dias consecutivos)
    recent_sessions = all_sessions.filter(completed_at__gte=last_month).order_by('-completed_at')
    streak_days = 0
    if recent_sessions.exists():
        last_workout_date = recent_sessions.first().completed_at.date()
        current_date = last_workout_date
        
        for session in recent_sessions:
            session_date = session.completed_at.date()
            if session_date == current_date:
                streak_days += 1
                current_date = current_date - timedelta(days=1)
            else:
                break
    
    return Response({
        "analytics_period": {
            "generated_at": now,
            "week_start": last_week.date(),
            "month_start": last_month.date()
        },
        "overall_stats": {
            "total_workouts": total_workouts,
            "total_time_minutes": total_time,
            "total_time_hours": round(total_time / 60, 1) if total_time else 0,
            "average_rating": round(avg_rating, 1),
            "total_calories_burned": total_calories,
            "current_streak_days": streak_days
        },
        "weekly_stats": {
            "workouts": week_workouts,
            "time_minutes": week_time,
            "calories_burned": week_calories,
            "avg_per_day": round(week_workouts / 7, 1)
        },
        "monthly_stats": {
            "workouts": month_workouts,
            "time_minutes": month_time,
            "calories_burned": month_calories,
            "avg_per_week": round(month_workouts / 4, 1)
        },
        "popular_workouts": list(popular_workouts),
        "insights": {
            "most_active_day": "Análise disponível com mais dados",
            "improvement_trend": "Positiva" if week_workouts > 0 else "Inicie hoje!",
            "consistency_level": "Excelente" if streak_days >= 7 else "Boa" if streak_days >= 3 else "Pode melhorar"
        }
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