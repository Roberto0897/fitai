# apps/recommendations/views_monitoring.py
"""
Views para monitoramento e métricas do sistema de IA
Fornecem dados para dashboard e análises administrativas
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.core.cache import cache
from datetime import datetime, timedelta
import json

from .models import Recommendation
from .services.ai_service import AIService
from .services.recommendation_engine import RecommendationEngine
from apps.users.models import UserProfile
from apps.workouts.models import WorkoutSession, ExerciseLog


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_status_check(request):
    """
    Status rápido do sistema de IA para usuários
    Endpoint público para verificar disponibilidade
    """
    ai_service = AIService()
    
    # Status básico
    status_info = {
        'ai_available': ai_service.is_available,
        'timestamp': timezone.now().isoformat(),
        'features': {
            'workout_generation': ai_service.is_available,
            'progress_analysis': ai_service.is_available,
            'motivational_content': ai_service.is_available,
            'smart_recommendations': True  # Sempre disponível via fallbacks
        }
    }
    
    # Rate limits do usuário (sem expor detalhes internos)
    rate_limit_key = f"user_ai_requests_{request.user.id}_{datetime.now().strftime('%Y%m%d%H')}"
    user_requests_this_hour = cache.get(rate_limit_key, 0)
    
    status_info['user_limits'] = {
        'requests_this_hour': user_requests_this_hour,
        'hourly_limit': 20,  # Limite por usuário
        'can_make_request': user_requests_this_hour < 20
    }
    
    # Informações do usuário
    try:
        profile = UserProfile.objects.get(user=request.user)
        status_info['user_profile'] = {
            'has_complete_profile': True,
            'goal': profile.goal,
            'activity_level': profile.activity_level,
            'personalization_available': True
        }
    except UserProfile.DoesNotExist:
        status_info['user_profile'] = {
            'has_complete_profile': False,
            'personalization_available': False,
            'suggestion': 'Complete seu perfil para recomendações mais precisas'
        }
    
    return Response(status_info)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def ai_admin_dashboard(request):
    """
    Dashboard completo para administradores
    Métricas detalhadas do sistema de IA
    """
    # Período de análise (últimos 30 dias)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    ai_service = AIService()
    
    # 1. Status geral do sistema
    system_status = {
        'ai_service_available': ai_service.is_available,
        'api_usage_stats': ai_service.get_api_usage_stats(),
        'last_updated': timezone.now().isoformat()
    }
    
    # 2. Estatísticas de usuários
    user_stats = _get_user_statistics(thirty_days_ago, seven_days_ago)
    
    # 3. Estatísticas de recomendações
    recommendation_stats = _get_recommendation_statistics(thirty_days_ago)
    
    # 4. Métricas de performance
    performance_metrics = _get_performance_metrics()
    
    # 5. Análise de qualidade
    quality_metrics = _get_quality_metrics(thirty_days_ago)
    
    # 6. Alertas e problemas
    alerts = _get_system_alerts(ai_service)
    
    dashboard_data = {
        'system_status': system_status,
        'user_statistics': user_stats,
        'recommendation_statistics': recommendation_stats,
        'performance_metrics': performance_metrics,
        'quality_metrics': quality_metrics,
        'alerts': alerts,
        'generated_at': timezone.now().isoformat()
    }
    
    return Response(dashboard_data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def ai_usage_analytics(request):
    """
    Analytics detalhados de uso da IA
    """
    days = int(request.GET.get('days', 7))
    start_date = timezone.now() - timedelta(days=days)
    
    # Coletar métricas diárias
    daily_metrics = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        
        # Métricas do cache (se disponíveis)
        cache_key = f"openai_metrics_{date_str}"
        day_metrics = cache.get(cache_key, [])
        
        daily_summary = {
            'date': date_str,
            'total_requests': len(day_metrics),
            'total_tokens': sum([m.get('total_tokens', 0) for m in day_metrics]),
            'avg_response_time': _calculate_avg_response_time(day_metrics),
            'error_count': _count_errors_in_metrics(day_metrics)
        }
        
        daily_metrics.append(daily_summary)
    
    # Estatísticas por algoritmo
    algorithm_stats = Recommendation.objects.filter(
        created_at__gte=start_date
    ).values('algorithm_used').annotate(
        count=Count('id'),
        avg_confidence=Avg('confidence_score')
    ).order_by('-count')
    
    # Top usuários mais ativos
    top_users = User.objects.filter(
        workoutsession__created_at__gte=start_date
    ).annotate(
        session_count=Count('workoutsession')
    ).order_by('-session_count')[:10]
    
    top_users_data = []
    for user in top_users:
        try:
            profile = UserProfile.objects.get(user=user)
            goal = profile.goal
            level = profile.activity_level
        except UserProfile.DoesNotExist:
            goal = 'não definido'
            level = 'não definido'
        
        top_users_data.append({
            'username': user.username,
            'session_count': user.session_count,
            'goal': goal,
            'activity_level': level,
            'joined_date': user.date_joined.strftime('%Y-%m-%d')
        })
    
    analytics_data = {
        'period_days': days,
        'daily_metrics': daily_metrics,
        'algorithm_performance': list(algorithm_stats),
        'top_active_users': top_users_data,
        'summary': {
            'total_requests': sum([d['total_requests'] for d in daily_metrics]),
            'total_tokens': sum([d['total_tokens'] for d in daily_metrics]),
            'avg_daily_requests': sum([d['total_requests'] for d in daily_metrics]) / days,
            'error_rate': _calculate_overall_error_rate(daily_metrics)
        }
    }
    
    return Response(analytics_data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def trigger_ai_maintenance(request):
    """
    Endpoint para triggers de manutenção do sistema de IA
    """
    action = request.data.get('action')
    
    if action == 'clear_cache':
        # Limpar cache de IA
        cleared_items = _clear_ai_cache()
        return Response({
            'action': 'clear_cache',
            'status': 'success',
            'items_cleared': cleared_items,
            'timestamp': timezone.now()
        })
    
    elif action == 'refresh_stats':
        # Recalcular estatísticas
        ai_service = AIService()
        stats = ai_service.get_api_usage_stats()
        return Response({
            'action': 'refresh_stats',
            'status': 'success',
            'current_stats': stats,
            'timestamp': timezone.now()
        })
    
    elif action == 'test_api':
        # Testar conectividade da API
        ai_service = AIService()
        connection_test = ai_service._test_api_connection()
        return Response({
            'action': 'test_api',
            'status': 'success' if connection_test else 'failed',
            'api_available': ai_service.is_available,
            'connection_test': connection_test,
            'timestamp': timezone.now()
        })
    
    else:
        return Response({
            'error': 'Ação inválida',
            'available_actions': ['clear_cache', 'refresh_stats', 'test_api']
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_ai_insights(request):
    """
    Insights personalizados de IA para o usuário
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return Response({
            'insights_available': False,
            'message': 'Complete seu perfil para insights personalizados'
        })
    
    # Coletar dados do usuário
    thirty_days_ago = timezone.now() - timedelta(days=30)
    user_sessions = WorkoutSession.objects.filter(
        user=request.user,
        created_at__gte=thirty_days_ago
    )
    
    completed_sessions = user_sessions.filter(completed=True)
    
    if completed_sessions.count() < 3:
        return Response({
            'insights_available': False,
            'message': 'Complete mais treinos para insights detalhados',
            'sessions_needed': 3 - completed_sessions.count()
        })
    
    # Calcular insights
    insights = {
        'insights_available': True,
        'period': '30_days',
        'workout_patterns': {
            'total_workouts': completed_sessions.count(),
            'completion_rate': completed_sessions.count() / user_sessions.count() * 100 if user_sessions.count() > 0 else 0,
            'avg_duration': completed_sessions.aggregate(Avg('actual_duration'))['actual_duration__avg'] or 0,
            'consistency_score': _calculate_user_consistency(request.user, thirty_days_ago)
        },
        'progress_indicators': {
            'goal_alignment': _assess_goal_alignment(profile, completed_sessions),
            'improvement_trend': _calculate_improvement_trend(request.user, thirty_days_ago),
            'areas_of_focus': _identify_focus_areas(completed_sessions)
        },
        'ai_recommendations': {
            'next_focus': _get_next_focus_suggestion(profile, completed_sessions),
            'motivation_level': _assess_motivation_level(completed_sessions),
            'suggested_frequency': _suggest_workout_frequency(completed_sessions)
        }
    }
    
    return Response(insights)


# Funções auxiliares

def _get_user_statistics(thirty_days_ago, seven_days_ago):
    """Coleta estatísticas de usuários"""
    total_users = User.objects.count()
    users_with_profile = UserProfile.objects.count()
    
    active_users_30d = User.objects.filter(
        workoutsession__created_at__gte=thirty_days_ago
    ).distinct().count()
    
    active_users_7d = User.objects.filter(
        workoutsession__created_at__gte=seven_days_ago
    ).distinct().count()
    
    # Distribuição de objetivos
    goal_distribution = UserProfile.objects.values('goal').annotate(
        count=Count('id')
    ).order_by('-count')
    
    return {
        'total_users': total_users,
        'users_with_profile': users_with_profile,
        'profile_completion_rate': users_with_profile / total_users * 100 if total_users > 0 else 0,
        'active_users_30d': active_users_30d,
        'active_users_7d': active_users_7d,
        'user_retention_rate': active_users_7d / active_users_30d * 100 if active_users_30d > 0 else 0,
        'goal_distribution': list(goal_distribution)
    }


def _get_recommendation_statistics(thirty_days_ago):
    """Coleta estatísticas de recomendações"""
    total_recommendations = Recommendation.objects.filter(
        created_at__gte=thirty_days_ago
    ).count()
    
    accepted_recommendations = Recommendation.objects.filter(
        created_at__gte=thirty_days_ago,
        accepted=True
    ).count()
    
    by_algorithm = Recommendation.objects.filter(
        created_at__gte=thirty_days_ago
    ).values('algorithm_used').annotate(
        count=Count('id'),
        acceptance_rate=Count('id', filter=Q(accepted=True)) * 100.0 / Count('id')
    ).order_by('-count')
    
    return {
        'total_generated': total_recommendations,
        'total_accepted': accepted_recommendations,
        'overall_acceptance_rate': accepted_recommendations / total_recommendations * 100 if total_recommendations > 0 else 0,
        'by_algorithm': list(by_algorithm),
        'avg_confidence_score': Recommendation.objects.filter(
            created_at__gte=thirty_days_ago
        ).aggregate(Avg('confidence_score'))['confidence_score__avg'] or 0
    }


def _get_performance_metrics():
    """Coleta métricas de performance"""
    # Rate limits atuais
    ai_service = AIService()
    rate_limit_data = cache.get(ai_service.rate_limit_cache_key, {"count": 0})
    
    return {
        'api_rate_limit': {
            'requests_this_hour': rate_limit_data.get('count', 0),
            'limit_per_hour': 50,
            'utilization_percentage': rate_limit_data.get('count', 0) / 50 * 100
        },
        'cache_status': {
            'cache_backend': 'redis' if 'redis' in str(cache._cache) else 'memory',
            'temp_disabled': cache.get('openai_temp_disabled', False)
        },
        'system_health': {
            'database_responsive': True,  # Poderia ser um teste real
            'ai_service_responsive': ai_service.is_available
        }
    }


def _get_quality_metrics(thirty_days_ago):
    """Análise de qualidade das respostas de IA"""
    # Analisar sessões que foram avaliadas pelos usuários
    rated_sessions = WorkoutSession.objects.filter(
        created_at__gte=thirty_days_ago,
        user_rating__isnull=False
    )
    
    if rated_sessions.exists():
        avg_rating = rated_sessions.aggregate(Avg('user_rating'))['user_rating__avg']
        high_rated = rated_sessions.filter(user_rating__gte=4).count()
        
        quality_score = high_rated / rated_sessions.count() * 100
    else:
        avg_rating = 0
        quality_score = 0
    
    return {
        'user_satisfaction': {
            'avg_workout_rating': avg_rating,
            'high_satisfaction_rate': quality_score,
            'total_rated_sessions': rated_sessions.count()
        },
        'ai_quality_indicators': {
            'recommendation_acceptance_rate': _get_current_acceptance_rate(),
            'user_engagement_score': _calculate_engagement_score(thirty_days_ago)
        }
    }


def _get_system_alerts(ai_service):
    """Identifica alertas e problemas do sistema"""
    alerts = []
    
    # Verificar API OpenAI
    if not ai_service.is_available:
        alerts.append({
            'level': 'error',
            'message': 'OpenAI API não está disponível',
            'action': 'Verificar configuração da API key'
        })
    
    # Verificar rate limits
    rate_limit_data = cache.get(ai_service.rate_limit_cache_key, {"count": 0})
    if rate_limit_data.get('count', 0) > 40:
        alerts.append({
            'level': 'warning',
            'message': 'Rate limit próximo do limite',
            'action': 'Monitorar uso da API'
        })
    
    # Verificar se API foi temporariamente desabilitada
    if cache.get('openai_temp_disabled'):
        alerts.append({
            'level': 'warning',
            'message': 'API temporariamente desabilitada devido a rate limit',
            'action': 'Aguardar reset automático'
        })
    
    # Verificar usuários sem perfil
    users_without_profile = User.objects.filter(userprofile__isnull=True).count()
    if users_without_profile > 0:
        alerts.append({
            'level': 'info',
            'message': f'{users_without_profile} usuários sem perfil completo',
            'action': 'Incentivar conclusão de perfis'
        })
    
    return alerts


def _clear_ai_cache():
    """Limpa cache relacionado à IA"""
    cleared_count = 0
    
    # Lista de chaves para limpar
    keys_to_clear = [
        'openai_rate_limit',
        'openai_temp_disabled'
    ]
    
    # Limpar métricas dos últimos 7 dias
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        keys_to_clear.append(f"openai_metrics_{date}")
    
    # Limpar contextos de usuários (sample)
    for user_id in range(1, 101):  # Primeiros 100 usuários
        keys_to_clear.append(f"user_context_{user_id}")
    
    for key in keys_to_clear:
        if cache.get(key) is not None:
            cache.delete(key)
            cleared_count += 1
    
    return cleared_count


def _calculate_avg_response_time(metrics):
    """Calcula tempo médio de resposta (placeholder)"""
    # Implementação real dependeria de métricas de timing
    return 1.5  # Simulado


def _count_errors_in_metrics(metrics):
    """Conta erros nas métricas (placeholder)"""
    # Implementação real analisaria logs de erro
    return 0  # Simulado


def _calculate_overall_error_rate(daily_metrics):
    """Calcula taxa geral de erro"""
    total_requests = sum([d['total_requests'] for d in daily_metrics])
    total_errors = sum([d['error_count'] for d in daily_metrics])
    
    return total_errors / total_requests * 100 if total_requests > 0 else 0


def _get_current_acceptance_rate():
    """Taxa atual de aceitação de recomendações"""
    recent_recs = Recommendation.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    )
    
    if recent_recs.exists():
        accepted = recent_recs.filter(accepted=True).count()
        return accepted / recent_recs.count() * 100
    
    return 0


def _calculate_engagement_score(thirty_days_ago):
    """Score de engajamento dos usuários"""
    active_users = User.objects.filter(
        workoutsession__created_at__gte=thirty_days_ago
    ).distinct().count()
    
    total_users = User.objects.count()
    
    return active_users / total_users * 100 if total_users > 0 else 0


def _calculate_user_consistency(user, start_date):
    """Calcula score de consistência do usuário"""
    sessions = WorkoutSession.objects.filter(
        user=user,
        created_at__gte=start_date,
        completed=True
    ).order_by('completed_at')
    
    if sessions.count() < 2:
        return 0
    
    # Análise simples de consistência baseada na regularidade
    dates = [s.completed_at.date() for s in sessions]
    unique_dates = set(dates)
    
    days_with_workouts = len(unique_dates)
    total_days = (timezone.now().date() - start_date.date()).days
    
    return days_with_workouts / total_days * 100


def _assess_goal_alignment(profile, sessions):
    """Avalia alinhamento com objetivo"""
    # Implementação simplificada
    goal_mapping = {
        'lose_weight': 'cardio',
        'gain_muscle': 'strength',
        'maintain_fitness': 'mixed',
        'improve_endurance': 'cardio'
    }
    
    preferred_type = goal_mapping.get(profile.goal, 'mixed')
    return f"Alinhado com {preferred_type}"


def _calculate_improvement_trend(user, start_date):
    """Calcula tendência de melhoria"""
    sessions = WorkoutSession.objects.filter(
        user=user,
        created_at__gte=start_date,
        completed=True,
        user_rating__isnull=False
    ).order_by('completed_at')
    
    if sessions.count() < 3:
        return "Dados insuficientes"
    
    # Comparar primeira e última metade das avaliações
    half_point = sessions.count() // 2
    first_half_avg = sessions[:half_point].aggregate(Avg('user_rating'))['user_rating__avg']
    second_half_avg = sessions[half_point:].aggregate(Avg('user_rating'))['user_rating__avg']
    
    if second_half_avg > first_half_avg * 1.1:
        return "Melhorando"
    elif second_half_avg < first_half_avg * 0.9:
        return "Precisa atenção"
    else:
        return "Estável"


def _identify_focus_areas(sessions):
    """Identifica áreas de foco do usuário"""
    # Análise baseada nos exercícios mais realizados
    exercise_logs = ExerciseLog.objects.filter(
        session__in=sessions,
        completed=True
    )
    
    muscle_groups = exercise_logs.values(
        'workout_exercise__exercise__muscle_group'
    ).annotate(count=Count('id')).order_by('-count')[:3]
    
    return [mg['workout_exercise__exercise__muscle_group'] for mg in muscle_groups]


def _get_next_focus_suggestion(profile, sessions):
    """Sugere próximo foco baseado no perfil e histórico"""
    current_focus = _identify_focus_areas(sessions)
    
    suggestions = {
        'lose_weight': 'Intensificar cardio e HIIT',
        'gain_muscle': 'Focar em treinos de força',
        'maintain_fitness': 'Manter variedade nos treinos',
        'improve_endurance': 'Aumentar duração gradualmente'
    }
    
    return suggestions.get(profile.goal, 'Manter consistência nos treinos')


def _assess_motivation_level(sessions):
    """Avalia nível de motivação baseado nas avaliações"""
    recent_ratings = sessions.filter(
        user_rating__isnull=False
    ).order_by('-completed_at')[:5]
    
    if not recent_ratings.exists():
        return "Indeterminado"
    
    avg_rating = recent_ratings.aggregate(Avg('user_rating'))['user_rating__avg']
    
    if avg_rating >= 4:
        return "Alto"
    elif avg_rating >= 3:
        return "Médio"
    else:
        return "Baixo"


def _suggest_workout_frequency(sessions):
    """Sugere frequência de treinos"""
    weekly_average = sessions.count() / 4.3  # Aproximadamente 30 dias = 4.3 semanas
    
    if weekly_average >= 4:
        return "Manter frequência atual"
    elif weekly_average >= 2:
        return "Tentar adicionar 1 treino por semana"
    else:
        return "Começar com 2-3 treinos por semana"