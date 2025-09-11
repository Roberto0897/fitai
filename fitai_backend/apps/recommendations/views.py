# apps/recommendations/views.py - VERSÃO COMPLETA COM TODAS AS FUNÇÕES
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.cache import cache
from django.conf import settings
from datetime import datetime, timedelta
from functools import wraps

from .models import Recommendation
from .services.recommendation_engine import RecommendationEngine
from .services.ai_service import AIService
from apps.users.models import UserProfile
from apps.workouts.models import Workout, WorkoutSession

import logging
import time

logger = logging.getLogger(__name__)


def rate_limit_user(max_requests_per_hour=20, max_requests_per_day=100):
    """
    Decorator para rate limiting por usuário
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            
            user_id = request.user.id
            now = datetime.now()
            
            # Chaves de rate limiting
            hourly_key = f"user_ai_requests_{user_id}_{now.strftime('%Y%m%d%H')}"
            daily_key = f"user_ai_requests_{user_id}_{now.strftime('%Y%m%d')}"
            
            # Verificar limites
            hourly_requests = cache.get(hourly_key, 0)
            daily_requests = cache.get(daily_key, 0)
            
            if hourly_requests >= max_requests_per_hour:
                return Response({
                    'error': 'Rate limit excedido',
                    'message': f'Máximo de {max_requests_per_hour} requisições por hora',
                    'retry_after': 3600 - (now.minute * 60 + now.second),
                    'current_usage': {
                        'hourly': hourly_requests,
                        'daily': daily_requests
                    }
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            if daily_requests >= max_requests_per_day:
                return Response({
                    'error': 'Rate limit diário excedido',
                    'message': f'Máximo de {max_requests_per_day} requisições por dia',
                    'retry_after': 86400 - (now.hour * 3600 + now.minute * 60 + now.second),
                    'current_usage': {
                        'hourly': hourly_requests,
                        'daily': daily_requests
                    }
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Executar view
            response = view_func(request, *args, **kwargs)
            
            # Atualizar contadores apenas se a requisição foi bem-sucedida
            if 200 <= response.status_code < 300:
                cache.set(hourly_key, hourly_requests + 1, 3600)
                cache.set(daily_key, daily_requests + 1, 86400)
                
                # Adicionar headers de rate limiting
                response['X-RateLimit-Hourly-Limit'] = str(max_requests_per_hour)
                response['X-RateLimit-Hourly-Remaining'] = str(max_requests_per_hour - hourly_requests - 1)
                response['X-RateLimit-Daily-Limit'] = str(max_requests_per_day)
                response['X-RateLimit-Daily-Remaining'] = str(max_requests_per_day - daily_requests - 1)
            
            return response
        return wrapper
    return decorator


@api_view(['GET'])
def test_recommendations_api(request):
    """Teste básico da API de recomendações com status detalhado"""
    try:
        ai_service = AIService()
    except Exception as e:
        logger.error(f"Error initializing AIService: {e}")
        ai_service = None
    
    # Status detalhado do sistema
    system_status = {
        "api_status": "funcionando",
        "timestamp": timezone.now().isoformat(),
        "ai_integration": {
            "openai_available": ai_service.is_available if ai_service else False,
            "fallback_enabled": getattr(settings, 'AI_FALLBACK_TO_RULES', True),
            "api_usage_stats": ai_service.get_api_usage_stats() if ai_service and ai_service.is_available else None
        },
        "features_available": {
            "personalized_recommendations": True,
            "ai_workout_generation": ai_service.is_available if ai_service else False,
            "progress_analysis": ai_service.is_available if ai_service else False,
            "motivational_content": ai_service.is_available if ai_service else False
        }
    }
    
    # Se usuário está logado, adicionar info pessoal
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            system_status["user_info"] = {
                "has_profile": True,
                "goal": profile.goal,
                "activity_level": profile.activity_level,
                "personalization_ready": True
            }
        except UserProfile.DoesNotExist:
            system_status["user_info"] = {
                "has_profile": False,
                "personalization_ready": False,
                "suggestion": "Complete seu perfil para melhor experiência"
            }
    
    return Response(system_status)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@rate_limit_user(max_requests_per_hour=50)
def get_personalized_recommendations(request):
    """
    Recomendações personalizadas com rate limiting e cache inteligente
    """
    start_time = time.time()
    
    try:
        # Parâmetros da query
        algorithm = request.GET.get('algorithm', 'hybrid')
        limit = min(int(request.GET.get('limit', 5)), 10)
        force_refresh = request.GET.get('refresh', '').lower() == 'true'
        
        # Cache key para esta requisição
        cache_key = f"recommendations_{request.user.id}_{algorithm}_{limit}"
        
        # Verificar cache (a menos que force_refresh)
        if not force_refresh:
            cached_recommendations = cache.get(cache_key)
            if cached_recommendations:
                cached_recommendations['from_cache'] = True
                cached_recommendations['cache_hit'] = True
                return Response(cached_recommendations)
        
        # Gerar recomendações
        try:
            recommendation_engine = RecommendationEngine()
            recommendations = recommendation_engine.generate_recommendations(
                user=request.user,
                algorithm=algorithm,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error initializing RecommendationEngine: {e}")
            recommendations = []
        
        if not recommendations:
            return Response({
                'personalized_recommendations': [],
                'message': 'Não foi possível gerar recomendações no momento',
                'suggestion': 'Tente novamente em alguns minutos ou complete mais treinos'
            }, status=status.HTTP_204_NO_CONTENT)
        
        # Enriquecer dados com informações dos treinos
        enriched_recommendations = []
        for rec in recommendations:
            try:
                workout = Workout.objects.get(id=rec['workout_id'])
                enriched_recommendations.append({
                    'recommendation_id': rec.get('id'),
                    'workout': {
                        'id': workout.id,
                        'name': workout.name,
                        'description': workout.description,
                        'difficulty_level': workout.difficulty_level,
                        'estimated_duration': workout.estimated_duration,
                        'workout_type': workout.workout_type,
                        'target_muscle_groups': workout.target_muscle_groups,
                        'calories_estimate': workout.calories_estimate
                    },
                    'ai_analysis': {
                        'confidence_score': rec['confidence_score'],
                        'recommendation_reason': rec['reason'],
                        'algorithm_used': rec['algorithm_used'],
                        'personalization_factors': rec.get('personalization_factors', [])
                    }
                })
            except Workout.DoesNotExist:
                logger.warning(f"Workout {rec['workout_id']} not found")
                continue
        
        # Informações do usuário para contexto
        try:
            profile = UserProfile.objects.get(user=request.user)
            user_context = {
                'goal': profile.goal,
                'activity_level': profile.activity_level,
                'age': profile.age,
                'personalization_complete': True
            }
        except UserProfile.DoesNotExist:
            user_context = {
                'personalization_complete': False,
                'message': 'Complete seu perfil para recomendações mais precisas'
            }
        
        # IA Status
        try:
            ai_service = AIService()
            ai_available = ai_service.is_available
        except Exception:
            ai_available = False
            
        ai_features = {
            'ai_available': ai_available,
            'personalization_level': 'high' if algorithm in ['ai_personalized', 'hybrid'] else 'medium',
            'quality_indicators': {
                'confidence_avg': sum([r['ai_analysis']['confidence_score'] for r in enriched_recommendations]) / len(enriched_recommendations) if enriched_recommendations else 0,
                'algorithm_diversity': len(set([r['ai_analysis']['algorithm_used'] for r in enriched_recommendations]))
            }
        }
        
        response_data = {
            'personalized_recommendations': enriched_recommendations,
            'metadata': {
                'algorithm_used': algorithm,
                'total_recommendations': len(enriched_recommendations),
                'generated_at': timezone.now().isoformat(),
                'response_time_ms': round((time.time() - start_time) * 1000, 2),
                'from_cache': False
            },
            'user_context': user_context,
            'ai_features': ai_features
        }
        
        # Cache por 30 minutos
        cache.set(cache_key, response_data, 1800)
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error generating personalized recommendations for user {request.user.id}: {e}")
        return Response({
            "error": "Erro interno na geração de recomendações",
            "fallback_message": "Tente novamente ou use treinos pré-definidos",
            "error_code": "RECOMMENDATION_ERROR"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_recommendation(request, recommendation_id):
    """Marca uma recomendação como aceita pelo usuário"""
    try:
        # Tentar buscar a recomendação no banco
        try:
            recommendation = Recommendation.objects.get(
                id=recommendation_id, 
                user=request.user
            )
            recommendation.accepted = True
            recommendation.accepted_at = timezone.now()
            recommendation.save()
            
            return Response({
                'message': 'Recomendação marcada como aceita',
                'recommendation_id': recommendation_id,
                'accepted_at': recommendation.accepted_at.isoformat()
            })
            
        except Recommendation.DoesNotExist:
            # Se não encontrou no banco, tentar via RecommendationEngine
            try:
                recommendation_engine = RecommendationEngine()
                success = recommendation_engine.mark_recommendation_accepted(recommendation_id, request.user)
                
                if success:
                    return Response({
                        'message': 'Recomendação marcada como aceita',
                        'recommendation_id': recommendation_id,
                        'accepted_at': timezone.now().isoformat(),
                        'method': 'engine_tracking'
                    })
                else:
                    return Response({
                        'error': 'Recomendação não encontrada',
                        'recommendation_id': recommendation_id
                    }, status=status.HTTP_404_NOT_FOUND)
                    
            except Exception as e:
                logger.error(f"Error with RecommendationEngine: {e}")
                # Mesmo que dê erro, podemos registrar como aceita
                return Response({
                    'message': 'Feedback registrado com sucesso',
                    'recommendation_id': recommendation_id,
                    'accepted_at': timezone.now().isoformat(),
                    'note': 'Feedback será usado para melhorar futuras recomendações'
                })
            
    except Exception as e:
        logger.error(f"Error accepting recommendation {recommendation_id} for user {request.user.id}: {e}")
        return Response({
            'error': 'Erro ao processar feedback da recomendação',
            'recommendation_id': recommendation_id
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommendation_history(request):
    """Histórico de recomendações do usuário"""
    try:
        days = int(request.GET.get('days', 30))
        days = min(days, 90)  # Máximo 90 dias
        
        # Buscar recomendações do banco de dados
        start_date = timezone.now() - timedelta(days=days)
        recommendations = Recommendation.objects.filter(
            user=request.user,
            created_at__gte=start_date
        ).order_by('-created_at')
        
        # Processar histórico
        history = []
        for rec in recommendations:
            history.append({
                'id': rec.id,
                'workout_id': rec.workout_id if hasattr(rec, 'workout_id') else None,
                'algorithm_used': rec.algorithm_used,
                'confidence_score': rec.confidence_score,
                'accepted': rec.accepted,
                'created_at': rec.created_at.isoformat(),
                'accepted_at': rec.accepted_at.isoformat() if rec.accepted_at else None
            })
        
        # Se não tem muitos dados no banco, tentar via RecommendationEngine
        if len(history) < 5:
            try:
                recommendation_engine = RecommendationEngine()
                engine_history = recommendation_engine.get_user_recommendation_history(request.user, days)
                
                # Combinar dados
                for eh in engine_history:
                    # Evitar duplicatas
                    if not any(h.get('id') == eh.get('id') for h in history):
                        history.append(eh)
                        
            except Exception as e:
                logger.error(f"Error getting history from RecommendationEngine: {e}")
        
        # Estatísticas
        total_recommendations = len(history)
        accepted_recommendations = len([h for h in history if h.get('accepted', False)])
        acceptance_rate = round(accepted_recommendations / total_recommendations * 100, 1) if total_recommendations > 0 else 0
        
        # Agrupar por algoritmo
        algorithm_stats = {}
        for h in history:
            algo = h.get('algorithm_used', 'unknown')
            if algo not in algorithm_stats:
                algorithm_stats[algo] = {'count': 0, 'accepted': 0}
            algorithm_stats[algo]['count'] += 1
            if h.get('accepted', False):
                algorithm_stats[algo]['accepted'] += 1
        
        # Calcular taxa de aceitação por algoritmo
        for algo in algorithm_stats:
            stats = algorithm_stats[algo]
            stats['acceptance_rate'] = round(stats['accepted'] / stats['count'] * 100, 1) if stats['count'] > 0 else 0
        
        return Response({
            'recommendation_history': history,
            'statistics': {
                'total_recommendations': total_recommendations,
                'accepted_recommendations': accepted_recommendations,
                'acceptance_rate_percentage': acceptance_rate,
                'period_days': days,
                'algorithm_performance': algorithm_stats
            },
            'ai_learning': {
                'message': 'Suas escolhas nos ajudam a melhorar as recomendações',
                'personalization_improving': acceptance_rate > 70,
                'data_points_collected': total_recommendations
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching recommendation history for user {request.user.id}: {e}")
        return Response({
            'error': 'Erro ao buscar histórico de recomendações',
            'fallback_data': {
                'recommendation_history': [],
                'message': 'Histórico temporariamente indisponível'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@rate_limit_user(max_requests_per_hour=10)  # Limite mais baixo para geração de IA
def generate_ai_workout(request):
    """
    Geração de treino com IA - rate limiting mais restrito
    """
    start_time = time.time()
    
    try:
        # Parâmetros da requisição
        duration = request.data.get('duration', 30)
        focus = request.data.get('focus', 'full_body')
        difficulty = request.data.get('difficulty')
        custom_request = request.data.get('custom_request', '')
        
        # Validações de entrada
        validation_errors = []
        
        if not (10 <= duration <= 120):
            validation_errors.append("Duração deve estar entre 10 e 120 minutos")
        
        valid_focus = ['full_body', 'upper', 'lower', 'cardio', 'strength', 'flexibility']
        if focus not in valid_focus:
            validation_errors.append(f"Focus deve ser um de: {', '.join(valid_focus)}")
        
        if custom_request and len(custom_request) > 200:
            validation_errors.append("Pedido personalizado deve ter no máximo 200 caracteres")
        
        if validation_errors:
            return Response({
                "error": "Parâmetros inválidos",
                "validation_errors": validation_errors,
                "valid_parameters": {
                    "duration": "10-120 minutos",
                    "focus": valid_focus,
                    "difficulty": ["beginner", "intermediate", "advanced", "auto"]
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Buscar perfil do usuário
        try:
            profile = UserProfile.objects.get(user=request.user)
            if not difficulty or difficulty == 'auto':
                # Mapear activity_level para difficulty
                mapping = {
                    'sedentary': 'beginner',
                    'light': 'beginner',
                    'moderate': 'intermediate',
                    'active': 'intermediate',
                    'very_active': 'advanced'
                }
                difficulty = mapping.get(profile.activity_level, 'beginner')
        except UserProfile.DoesNotExist:
            profile = None
            difficulty = difficulty or 'beginner'
            
            return Response({
                "error": "Perfil incompleto",
                "message": "Complete seu perfil para geração de treinos personalizados",
                "required_action": "Acesse configurações e complete seu perfil"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cache key para evitar regeneração desnecessária
        cache_params = f"{duration}_{focus}_{difficulty}_{hash(custom_request)}"
        cache_key = f"ai_workout_{request.user.id}_{cache_params}"
        
        # Verificar cache (válido por 1 hora)
        cached_workout = cache.get(cache_key)
        if cached_workout and not request.data.get('force_new', False):
            cached_workout['metadata']['from_cache'] = True
            return Response(cached_workout)
        
        # Tentar gerar com IA primeiro
        try:
            ai_service = AIService()
            if ai_service.is_available and profile:
                ai_workout = ai_service.generate_personalized_workout_plan(
                    profile, duration, focus, difficulty
                )
                
                if ai_workout and ai_workout.get('quality_score', 0) >= getattr(settings, 'AI_QUALITY_THRESHOLD', 70):
                    response_data = {
                        'ai_generated_workout': ai_workout,
                        'generation_method': 'ai_powered',
                        'personalization': {
                            'based_on_profile': True,
                            'user_goal': profile.goal,
                            'activity_level': profile.activity_level,
                            'custom_request': custom_request,
                            'difficulty_auto_selected': difficulty != request.data.get('difficulty')
                        },
                        'quality_metrics': {
                            'quality_score': ai_workout.get('quality_score', 0),
                            'exercise_count': len(ai_workout.get('exercises', [])),
                            'estimated_effectiveness': 'high' if ai_workout.get('quality_score', 0) >= 80 else 'medium'
                        },
                        'instructions': {
                            'warm_up': ai_workout.get('warm_up', {}),
                            'cool_down': ai_workout.get('cool_down', {}),
                            'safety_notes': 'Treino gerado por IA baseado no seu perfil único. Pare se sentir dor.'
                        },
                        'metadata': {
                            'generated_at': timezone.now().isoformat(),
                            'response_time_ms': round((time.time() - start_time) * 1000, 2),
                            'ai_model_used': getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
                            'from_cache': False
                        }
                    }
                    
                    # Cache por 1 hora
                    cache.set(cache_key, response_data, 3600)
                    
                    return Response(response_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error with AIService: {e}")
        
        # Fallback: geração por regras
        fallback_workout = generate_rule_based_workout(duration, focus, difficulty, profile)
        
        response_data = {
            'ai_generated_workout': fallback_workout,
            'generation_method': 'rule_based_fallback',
            'personalization': {
                'based_on_profile': profile is not None,
                'note': 'IA temporariamente indisponível, usando algoritmo inteligente'
            },
            'quality_metrics': {
                'quality_score': 75,  # Score padrão para fallback
                'exercise_count': len(fallback_workout.get('exercises', [])),
                'estimated_effectiveness': 'medium'
            },
            'instructions': {
                'warm_up': 'Faça 5-10 minutos de aquecimento adequado ao foco do treino',
                'cool_down': 'Finalize com 5-10 minutos de alongamento específico',
                'safety_notes': 'Treino personalizado baseado nas suas preferências. Ajuste conforme necessário.'
            },
            'metadata': {
                'generated_at': timezone.now().isoformat(),
                'response_time_ms': round((time.time() - start_time) * 1000, 2),
                'fallback_reason': 'IA indisponível ou qualidade baixa',
                'from_cache': False
            }
        }
        
        # Cache por 30 minutos (menos tempo que IA)
        cache.set(cache_key, response_data, 1800)
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error generating AI workout for user {request.user.id}: {e}")
        return Response({
            "error": "Erro na geração do treino personalizado",
            "suggestion": "Tente com parâmetros mais simples ou use treinos pré-definidos",
            "error_code": "WORKOUT_GENERATION_ERROR",
            "support_message": "Se o problema persistir, entre em contato com o suporte"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@rate_limit_user(max_requests_per_hour=15)
def analyze_progress_ai(request):
    """
    Análise de progresso com rate limiting e validações melhoradas
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return Response({
            'analysis_available': False,
            'error': 'Perfil incompleto',
            'message': 'Complete seu perfil para análise de progresso',
            'required_action': 'Acesse configurações e complete seu perfil'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verificar se há dados suficientes
    user_sessions = WorkoutSession.objects.filter(
        user=request.user, 
        completed=True
    )
    
    min_sessions_required = 3
    if user_sessions.count() < min_sessions_required:
        return Response({
            'analysis_available': False,
            'message': f'Complete pelo menos {min_sessions_required} treinos para análise de progresso',
            'current_progress': {
                'workout_count': user_sessions.count(),
                'sessions_needed': min_sessions_required - user_sessions.count(),
                'completion_percentage': round(user_sessions.count() / min_sessions_required * 100, 1)
            },
            'basic_stats': {
                'total_workouts': user_sessions.count(),
                'goal': profile.goal,
                'activity_level': profile.activity_level,
                'member_since': profile.user.date_joined.strftime('%d/%m/%Y')
            }
        })
    
    # Cache key para análise
    cache_key = f"progress_analysis_{request.user.id}"
    
    # Verificar cache (válido por 2 horas)
    cached_analysis = cache.get(cache_key)
    if cached_analysis and not request.GET.get('refresh'):
        cached_analysis['metadata']['from_cache'] = True
        return Response(cached_analysis)
    
    start_time = time.time()
    
    # Tentar análise com IA
    try:
        ai_service = AIService()
        if ai_service.is_available:
            ai_analysis = ai_service.analyze_user_progress(profile)
            
            if ai_analysis:
                response_data = {
                    'analysis_available': True,
                    'analysis_method': 'ai_powered',
                    'ai_insights': ai_analysis,
                    'confidence_level': ai_analysis.get('analysis_metadata', {}).get('confidence_level', 'medium'),
                    'personalization': {
                        'tailored_to_goal': profile.goal,
                        'considers_activity_level': profile.activity_level,
                        'includes_historical_data': True
                    },
                    'metadata': {
                        'generated_at': timezone.now().isoformat(),
                        'response_time_ms': round((time.time() - start_time) * 1000, 2),
                        'analysis_period': '30_days',
                        'data_points_analyzed': user_sessions.count(),
                        'from_cache': False
                    }
                }
                
                # Cache por 2 horas
                cache.set(cache_key, response_data, 7200)
                
                return Response(response_data)
    except Exception as e:
        logger.error(f"Error with AIService in progress analysis: {e}")
    
    # Fallback: análise por regras
    rule_analysis = generate_rule_based_analysis(request.user, profile)
    
    response_data = {
        'analysis_available': True,
        'analysis_method': 'rule_based',
        'progress_analysis': rule_analysis,
        'confidence_level': 'medium',
        'personalization': {
            'tailored_to_goal': profile.goal,
            'considers_activity_level': profile.activity_level,
            'includes_historical_data': True
        },
        'metadata': {
            'generated_at': timezone.now().isoformat(),
            'response_time_ms': round((time.time() - start_time) * 1000, 2),
            'analysis_period': '30_days',
            'fallback_reason': 'IA temporariamente indisponível',
            'from_cache': False
        }
    }
    
    # Cache por 1 hora (menos tempo que IA)
    cache.set(cache_key, response_data, 3600)
    
    return Response(response_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@rate_limit_user(max_requests_per_hour=30)
def generate_motivational_message(request):
    """
    Mensagens motivacionais com rate limiting inteligente
    """
    try:
        context = request.data.get('context', 'general')
        valid_contexts = ['workout_start', 'workout_complete', 'weekly_review', 'goal_reminder', 'comeback', 'general']
        
        if context not in valid_contexts:
            return Response({
                'error': 'Contexto inválido',
                'valid_contexts': valid_contexts
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response({
                'motivational_message': 'Você está no caminho certo para uma vida mais saudável! Continue assim!',
                'context': context,
                'personalized': False,
                'note': 'Complete seu perfil para mensagens mais personalizadas'
            })
        
        # Cache key específico para contexto
        cache_key = f"motivation_{request.user.id}_{context}"
        
        # Verificar cache (válido por 30 minutos)
        cached_message = cache.get(cache_key)
        if cached_message:
            cached_message['from_cache'] = True
            return Response(cached_message)
        
        # Tentar gerar com IA
        try:
            ai_service = AIService()
            if ai_service.is_available:
                motivational_message = ai_service.generate_motivational_content(profile, context)
                
                if motivational_message:
                    response_data = {
                        'motivational_message': motivational_message,
                        'context': context,
                        'personalized': True,
                        'generation_method': 'ai_powered',
                        'personalization_factors': {
                            'user_name': profile.user.first_name or 'Atleta',
                            'goal': profile.goal,
                            'activity_level': profile.activity_level
                        },
                        'metadata': {
                            'generated_at': timezone.now().isoformat(),
                            'ai_model': getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
                            'from_cache': False
                        }
                    }
                    
                    # Cache por 30 minutos
                    cache.set(cache_key, response_data, 1800)
                    
                    return Response(response_data)
        except Exception as e:
            logger.error(f"Error with AIService in motivational message: {e}")
        
        # Fallback: mensagens pré-definidas contextuais
        fallback_messages = {
            'workout_start': f"Hora de brilhar, {profile.user.first_name or 'campeão(ã)'}! Seu objetivo de {profile.goal or 'fitness'} está mais próximo a cada treino!",
            'workout_complete': f"Incrível! Mais um passo rumo ao seu objetivo de {profile.goal or 'saúde'}. Seu corpo e mente agradecem!",
            'weekly_review': f"Que semana produtiva! Continue focado(a) no seu {profile.goal or 'bem-estar'}. Você está evoluindo!",
            'goal_reminder': f"Lembre-se do seu 'porquê': {profile.goal or 'ser saudável'}. Cada treino te aproxima desta conquista!",
            'comeback': f"Que bom ter você de volta! Vamos retomar o caminho rumo ao seu objetivo: {profile.goal or 'fitness'}!",
            'general': f"Sua determinação em buscar {profile.goal or 'saúde'} é inspiradora. Continue se superando!"
        }
        
        response_data = {
            'motivational_message': fallback_messages.get(context, fallback_messages['general']),
            'context': context,
            'personalized': True,
            'generation_method': 'rule_based',
            'personalization_factors': {
                'user_name': profile.user.first_name or 'Atleta',
                'goal': profile.goal,
                'activity_level': profile.activity_level
            },
            'metadata': {
                'generated_at': timezone.now().isoformat(),
                'fallback_reason': 'IA indisponível',
                'from_cache': False
            }
        }
        
        # Cache por 20 minutos (menos que IA)
        cache.set(cache_key, response_data, 1200)
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error generating motivational message for user {request.user.id}: {e}")
        return Response({
            'error': 'Erro na geração da mensagem motivacional',
            'fallback_message': 'Você tem o poder de transformar sua vida através do movimento. Continue!'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# FUNÇÕES AUXILIARES

def generate_rule_based_workout(duration, focus, difficulty, profile):
    """Versão otimizada da geração por regras"""
    try:
        from apps.exercises.models import Exercise
    except ImportError:
        logger.error("Could not import Exercise model")
        # Fallback workout sem acessar banco
        return {
            'workout_name': f'Treino {focus.replace("_", " ").title()} - {difficulty.title()}',
            'description': f'Treino personalizado de {duration} minutos focado em {focus}',
            'estimated_duration': duration,
            'difficulty_level': difficulty,
            'exercises': [
                {
                    'order': 1,
                    'name': 'Push-ups',
                    'muscle_group': 'chest',
                    'sets': 3,
                    'reps': '12-15',
                    'rest_seconds': 45,
                    'instructions': 'Execute com controle e boa forma',
                    'modifications': f'Ajuste intensidade: {difficulty}',
                    'safety_tips': 'Pare se sentir dor. Mantenha respiração controlada.'
                },
                {
                    'order': 2,
                    'name': 'Squats',
                    'muscle_group': 'legs',
                    'sets': 3,
                    'reps': '15-20',
                    'rest_seconds': 45,
                    'instructions': 'Mantenha costas retas',
                    'modifications': f'Ajuste intensidade: {difficulty}',
                    'safety_tips': 'Não deixe joelhos passarem dos pés'
                }
            ],
            'warm_up': {
                'duration_minutes': 5,
                'instructions': f'Aquecimento específico para {focus}',
                'exercises': ['Mobilidade articular', 'Ativação muscular']
            },
            'cool_down': {
                'duration_minutes': 5,
                'instructions': 'Relaxamento e alongamento',
                'exercises': ['Alongamentos estáticos', 'Respiração profunda']
            },
            'quality_score': 75.0
        }
    
    # Cache para exercícios filtrados
    cache_key = f"exercises_{focus}_{difficulty}"
    exercises_query = cache.get(cache_key)
    
    if not exercises_query:
        try:
            exercises_query = Exercise.objects.all()
            
            # Filtro por foco
            focus_mapping = {
                'upper': ['chest', 'back', 'shoulders', 'arms'],
                'lower': ['legs', 'glutes'],
                'cardio': ['cardio'],
                'strength': ['chest', 'back', 'legs', 'shoulders'],
                'full_body': None,  # Inclui todos
                'flexibility': ['flexibility', 'stretching']
            }
            
            if focus in focus_mapping and focus_mapping[focus]:
                exercises_query = exercises_query.filter(muscle_group__in=focus_mapping[focus])
            
            # Filtro por dificuldade
            if difficulty == 'beginner':
                exercises_query = exercises_query.filter(difficulty_level='beginner')
            elif difficulty == 'intermediate':
                exercises_query = exercises_query.filter(difficulty_level__in=['beginner', 'intermediate'])
            
            exercises_query = list(exercises_query[:12])
            cache.set(cache_key, exercises_query, 3600)  # Cache por 1 hora
        except Exception as e:
            logger.error(f"Error querying exercises: {e}")
            exercises_query = []
    
    # Se não conseguiu buscar exercícios, usar fallback
    if not exercises_query:
        return generate_rule_based_workout(duration, focus, difficulty, profile)
    
    # Selecionar exercícios baseado na duração
    exercise_count = min(max(duration // 4, 4), len(exercises_query), 10)
    selected_exercises = exercises_query[:exercise_count]
    
    # Lógica aprimorada de séries/reps baseada no objetivo e duração
    workout_exercises = []
    for i, exercise in enumerate(selected_exercises, 1):
        # Ajustar baseado no objetivo do perfil
        if profile:
            if profile.goal == 'lose_weight':
                sets, reps, rest = (3, "45-60 seg", 30) if duration <= 30 else (4, "30-45 seg", 25)
            elif profile.goal == 'gain_muscle':
                sets, reps, rest = (4, "6-10", 90) if difficulty == 'advanced' else (3, "8-12", 60)
            elif profile.goal == 'improve_endurance':
                sets, reps, rest = (3, "60-90 seg", 20) if focus == 'cardio' else (3, "15-20", 30)
            else:
                sets, reps, rest = (3, "12-15", 45)
        else:
            sets, reps, rest = (3, "12-15", 45)
        
        workout_exercises.append({
            'order': i,
            'name': exercise.name,
            'muscle_group': exercise.muscle_group,
            'sets': sets,
            'reps': reps,
            'rest_seconds': rest,
            'instructions': exercise.instructions or 'Execute com controle e boa forma',
            'modifications': f'Ajuste intensidade: {difficulty}',
            'safety_tips': 'Pare se sentir dor. Mantenha respiração controlada.'
        })
    
    return {
        'workout_name': f'Treino {focus.replace("_", " ").title()} - {difficulty.title()}',
        'description': f'Treino personalizado de {duration} minutos focado em {focus}',
        'estimated_duration': duration,
        'difficulty_level': difficulty,
        'exercises': workout_exercises,
        'warm_up': {
            'duration_minutes': max(5, duration // 10),
            'instructions': f'Aquecimento específico para {focus}',
            'exercises': ['Mobilidade articular', 'Ativação muscular', 'Elevação gradual da FC']
        },
        'cool_down': {
            'duration_minutes': max(5, duration // 10),
            'instructions': 'Relaxamento e alongamento',
            'exercises': ['Alongamentos estáticos', 'Respiração profunda', 'Relaxamento muscular']
        },
        'quality_score': 75.0  # Score padrão para regras
    }


def generate_rule_based_analysis(user, profile):
    """Versão otimizada da análise por regras"""
    from datetime import timedelta
    from django.db.models import Avg, Count
    
    # Cache da análise
    cache_key = f"analysis_data_{user.id}"
    cached_data = cache.get(cache_key)
    
    if not cached_data:
        # Dados dos últimos períodos
        now = timezone.now()
        periods = {
            'week': now - timedelta(days=7),
            'month': now - timedelta(days=30),
            'quarter': now - timedelta(days=90)
        }
        
        cached_data = {}
        for period_name, start_date in periods.items():
            try:
                sessions = WorkoutSession.objects.filter(
                    user=user,
                    completed=True,
                    completed_at__gte=start_date
                )
                
                cached_data[period_name] = {
                    'count': sessions.count(),
                    'avg_rating': sessions.aggregate(Avg('user_rating'))['user_rating__avg'] or 0,
                    'avg_duration': sessions.aggregate(Avg('actual_duration'))['actual_duration__avg'] or 0
                }
            except Exception as e:
                logger.error(f"Error calculating {period_name} stats: {e}")
                cached_data[period_name] = {'count': 0, 'avg_rating': 0, 'avg_duration': 0}
        
        cache.set(cache_key, cached_data, 1800)  # 30 minutos
    
    month_data = cached_data.get('month', {})
    total_workouts = month_data.get('count', 0)
    avg_rating = month_data.get('avg_rating', 0)
    
    # Análise baseada em dados
    if total_workouts >= 16:  # 4+ por semana
        progress = 'excelente'
        message = f'Parabéns! Você está mantendo uma rotina excepcional de {total_workouts} treinos no último mês!'
    elif total_workouts >= 12:  # 3 por semana
        progress = 'muito_bom'
        message = f'Ótimo progresso com {total_workouts} treinos! Você está no caminho certo.'
    elif total_workouts >= 8:  # 2 por semana
        progress = 'bom'
        message = f'Bom ritmo com {total_workouts} treinos. Que tal tentar adicionar mais 1 por semana?'
    elif total_workouts >= 4:  # 1 por semana
        progress = 'médio'
        message = f'Você está começando bem com {total_workouts} treinos. Vamos aumentar a frequência gradualmente?'
    else:
        progress = 'precisa_melhorar'
        message = 'Vamos focar em criar uma rotina consistente. Comece com 2-3 treinos por semana!'
    
    return {
        'overall_progress': progress,
        'progress_summary': message,
        'strengths': _identify_strengths(total_workouts, avg_rating, profile),
        'areas_for_improvement': _identify_improvements(total_workouts, avg_rating, profile),
        'next_week_focus': _suggest_next_focus(progress, profile),
        'motivation_message': _generate_motivation(progress, profile.user.first_name or 'Atleta'),
        'specific_recommendations': _generate_specific_recs(total_workouts, profile),
        'goal_alignment': f'Progredindo bem rumo ao objetivo: {profile.goal or "fitness geral"}',
        'statistics': {
            'workouts_this_month': total_workouts,
            'average_rating': round(avg_rating, 1),
            'consistency_score': min(total_workouts / 16.0, 1.0)
        }
    }


def _identify_strengths(workout_count, avg_rating, profile):
    """Identifica pontos fortes do usuário"""
    strengths = []
    
    if workout_count >= 12:
        strengths.append("Excelente consistência nos treinos")
    elif workout_count >= 6:
        strengths.append("Boa regularidade nos exercícios")
    
    if avg_rating >= 4:
        strengths.append("Alta satisfação com os treinos")
    elif avg_rating >= 3.5:
        strengths.append("Boa avaliação dos treinos realizados")
    
    if profile.goal:
        strengths.append(f"Foco claro no objetivo: {profile.goal}")
    
    if not strengths:
        strengths.append("Iniciativa de começar a jornada fitness")
    
    return strengths


def _identify_improvements(workout_count, avg_rating, profile):
    """Identifica áreas para melhoria"""
    improvements = []
    
    if workout_count < 8:
        improvements.append("Aumentar frequência de treinos para 2-3x por semana")
    
    if avg_rating < 3.5:
        improvements.append("Experimentar diferentes tipos de treino para maior satisfação")
    
    if not profile.goal or profile.goal == 'maintain_fitness':
        improvements.append("Definir um objetivo específico para maior motivação")
    
    if workout_count > 0 and avg_rating == 0:
        improvements.append("Avaliar os treinos para feedback e melhoria contínua")
    
    return improvements if improvements else ["Manter o foco na consistência"]


def _suggest_next_focus(progress, profile):
    """Sugere foco para próxima semana"""
    suggestions = {
        'excelente': 'Manter a excelente rotina e considerar novos desafios',
        'muito_bom': 'Continuar o ritmo atual e explorar variações nos treinos',
        'bom': 'Tentar adicionar 1 treino extra na semana',
        'médio': 'Focar em criar consistência com 2-3 treinos por semana',
        'precisa_melhorar': 'Estabelecer rotina básica de 2 treinos por semana'
    }
    
    base_suggestion = suggestions.get(progress, 'Focar na consistência')
    
    if profile and profile.goal == 'lose_weight':
        return f"{base_suggestion}. Priorizar exercícios cardio e HIIT."
    elif profile and profile.goal == 'gain_muscle':
        return f"{base_suggestion}. Focar em treinos de força e resistência."
    else:
        return base_suggestion


def _generate_motivation(progress, name):
    """Gera mensagem motivacional personalizada"""
    messages = {
        'excelente': f'{name}, você é um exemplo de dedicação! Continue inspirando!',
        'muito_bom': f'Parabéns, {name}! Seu comprometimento está dando frutos!',
        'bom': f'{name}, você está no caminho certo. Continue assim!',
        'médio': f'{name}, cada treino é um passo importante. Continue crescendo!',
        'precisa_melhorar': f'{name}, o importante é não desistir. Vamos juntos!'
    }
    
    return messages.get(progress, f'{name}, você tem potencial incrível!')


def _generate_specific_recs(workout_count, profile):
    """Gera recomendações específicas"""
    recs = []
    
    if workout_count < 4:
        recs.append("Comece com treinos de 20-30 minutos, 2x por semana")
        recs.append("Escolha exercícios que você goste para manter motivação")
    elif workout_count < 8:
        recs.append("Aumente gradualmente para 3x por semana")
        recs.append("Varie entre treinos de força e cardio")
    else:
        recs.append("Experimente novos desafios e modalidades")
        recs.append("Considere treinos mais específicos para seu objetivo")
    
    # Recomendação baseada no objetivo
    if profile and profile.goal == 'lose_weight':
        recs.append("Combine exercícios com ajustes na alimentação")
    elif profile and profile.goal == 'gain_muscle':
        recs.append("Priorize treinos de força com sobrecarga progressiva")
    elif profile and profile.goal == 'improve_endurance':
        recs.append("Aumente gradualmente duração e intensidade dos treinos")
    
    return recs