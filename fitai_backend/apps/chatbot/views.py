# apps/chatbot/views.py
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
from typing import Dict, List  # Adicionado esta linha

from .models import Conversation, Message, ChatContext, ChatMetrics
from .services.chat_service import ChatService
from apps.users.models import UserProfile
from apps.recommendations.services.ai_service import AIService

import logging
import time
import json

logger = logging.getLogger(__name__)


def rate_limit_chatbot(max_requests_per_hour=30, max_requests_per_day=200):
    """
    Rate limiting específico para chatbot (mais permissivo que IA geral)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            
            user_id = request.user.id
            now = datetime.now()
            
            # Chaves de rate limiting específicas para chatbot
            hourly_key = f"chatbot_requests_{user_id}_{now.strftime('%Y%m%d%H')}"
            daily_key = f"chatbot_requests_{user_id}_{now.strftime('%Y%m%d')}"
            
            # Verificar limites
            hourly_requests = cache.get(hourly_key, 0)
            daily_requests = cache.get(daily_key, 0)
            
            if hourly_requests >= max_requests_per_hour:
                return Response({
                    'error': 'Limite de mensagens por hora excedido',
                    'message': f'Máximo de {max_requests_per_hour} mensagens por hora',
                    'retry_after': 3600 - (now.minute * 60 + now.second),
                    'suggestion': 'Que tal fazer uma pausa? O chat estará disponível em breve!',
                    'current_usage': {
                        'hourly': hourly_requests,
                        'daily': daily_requests,
                        'limits': {
                            'hourly_limit': max_requests_per_hour,
                            'daily_limit': max_requests_per_day
                        }
                    }
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            if daily_requests >= max_requests_per_day:
                return Response({
                    'error': 'Limite diário de mensagens excedido',
                    'message': f'Máximo de {max_requests_per_day} mensagens por dia',
                    'retry_after': 86400 - (now.hour * 3600 + now.minute * 60 + now.second),
                    'suggestion': 'Retorne amanhã para continuar nossa conversa!',
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
                
                # Headers informativos
                response['X-Chatbot-Hourly-Limit'] = str(max_requests_per_hour)
                response['X-Chatbot-Hourly-Remaining'] = str(max_requests_per_hour - hourly_requests - 1)
                response['X-Chatbot-Daily-Limit'] = str(max_requests_per_day)
                response['X-Chatbot-Daily-Remaining'] = str(max_requests_per_day - daily_requests - 1)
            
            return response
        return wrapper
    return decorator


@api_view(['GET'])
def test_chatbot_api(request):
    """Teste da API do chatbot com status detalhado"""
    try:
        chat_service = ChatService()
        ai_service = AIService()
    except Exception as e:
        logger.error(f"Error initializing services: {e}")
        chat_service = None
        ai_service = None
    
    # Status detalhado do sistema de chat
    system_status = {
        "chatbot_status": "funcionando",
        "timestamp": timezone.now().isoformat(),
        "ai_integration": {
            "openai_available": ai_service.is_available if ai_service else False,
            "chat_service_ready": chat_service is not None,
            "fallback_responses_enabled": True,
            "response_methods": ["ai_powered", "rule_based_fallback"]
        },
        "features_available": {
            "start_conversation": True,
            "send_messages": True,
            "conversation_history": True,
            "context_awareness": True,
            "intent_detection": ai_service.is_available if ai_service else "rule_based_only",
            "personalized_responses": True,
            "fitness_expertise": True
        },
        "conversation_types_supported": [
            "workout_consultation",
            "nutrition_advice", 
            "progress_analysis",
            "motivation_chat",
            "technique_guidance",
            "general_fitness",

          #  'workout_generation',
          #  'workout_modification',
        ]
    }
    
    # Se usuário está logado, adicionar info específica
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            
            # Buscar conversas ativas
            active_conversations = Conversation.objects.filter(
                user=request.user,
                status='active',
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            system_status["user_info"] = {
                "has_profile": True,
                "profile_complete": bool(profile.goal and profile.activity_level),
                "active_conversations": active_conversations,
                "can_start_chat": True,
                "personalization_level": "high" if profile.goal else "medium"
            }
        except UserProfile.DoesNotExist:
            system_status["user_info"] = {
                "has_profile": False,
                "profile_complete": False,
                "suggestion": "Complete seu perfil para conversas mais personalizadas",
                "can_start_chat": True,
                "personalization_level": "basic"
            }
    
    return Response(system_status)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@rate_limit_chatbot(max_requests_per_hour=10)  # Limite menor para criação de conversas
def start_conversation(request):
    """
    Inicia nova conversa de chatbot ou retoma conversa existente
    """
    start_time = time.time()
    
    try:
        # Parâmetros da requisição
        conversation_type = request.data.get('type', 'general_fitness')
        initial_message = request.data.get('message', '').strip()
        force_new = request.data.get('force_new', False)
        
        # Validações
        valid_types = [
            'workout_consultation', 'nutrition_advice', 'progress_analysis',
            'motivation_chat', 'technique_guidance', 'general_fitness'
        ]
        
        if conversation_type not in valid_types:
            return Response({
                'error': 'Tipo de conversa inválido',
                'valid_types': valid_types,
                'suggestion': 'Escolha um tipo de conversa válido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if initial_message and len(initial_message) > 500:
            return Response({
                'error': 'Mensagem inicial muito longa',
                'max_length': 500,
                'current_length': len(initial_message)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar se usuário tem perfil
        try:
            profile = UserProfile.objects.get(user=request.user)
            profile_complete = bool(profile.goal and profile.activity_level)
        except UserProfile.DoesNotExist:
            profile_complete = False
        
        # Inicializar serviço de chat
        try:
            chat_service = ChatService()
        except Exception as e:
            logger.error(f"Error initializing ChatService: {e}")
            return Response({
                'error': 'Serviço de chat temporariamente indisponível',
                'suggestion': 'Tente novamente em alguns minutos',
                'error_code': 'CHAT_SERVICE_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Verificar conversa ativa recente (a menos que force_new)
        if not force_new and not initial_message:
            recent_conversation = Conversation.objects.filter(
                user=request.user,
                status='active',
                last_activity_at__gte=timezone.now() - timedelta(hours=2)
            ).first()
            
            if recent_conversation:
                return Response({
                    'conversation_resumed': True,
                    'conversation_id': recent_conversation.id,
                    'conversation_type': recent_conversation.conversation_type,
                    'message': 'Continuando conversa anterior',
                    'last_activity': recent_conversation.last_activity_at.isoformat(),
                    'message_count': recent_conversation.message_count,
                    'suggestion': 'Digite sua mensagem para continuar ou force uma nova conversa'
                })
        
        # Criar nova conversa
        conversation_result = chat_service.start_conversation(
            user=request.user,
            conversation_type=conversation_type,
            initial_message=initial_message if initial_message else None
        )
        
        if 'error' in conversation_result:
            return Response({
                'error': conversation_result['error'],
                'fallback': conversation_result.get('fallback'),
                'suggestion': 'Verifique sua conexão e tente novamente'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Resposta de sucesso
        response_data = {
            'conversation_started': True,
            'conversation_id': conversation_result['conversation_id'],
            'conversation_type': conversation_type,
            'ai_available': conversation_result.get('ai_available', False),
            'personalization': {
                'profile_complete': profile_complete,
                'personalization_level': 'high' if profile_complete else 'medium',
                'context_loaded': conversation_result.get('context_loaded', False)
            },
            'capabilities': {
                'workout_recommendations': True,
                'technique_guidance': True,
                'progress_analysis': profile_complete,
                'personalized_motivation': profile_complete,
                'context_awareness': True
            },
            'usage_guidelines': {
                'message_limit_hour': 30,
                'message_limit_day': 200,
                'max_message_length': 500,
                'conversation_timeout_hours': 24
            },
            'metadata': {
                'created_at': timezone.now().isoformat(),
                'response_time_ms': round((time.time() - start_time) * 1000, 2),
                'welcome_message_included': conversation_result.get('welcome_message', False)
            }
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error starting conversation for user {request.user.id}: {e}")
        return Response({
            'error': 'Erro interno ao iniciar conversa',
            'suggestion': 'Tente novamente ou entre em contato com o suporte',
            'error_code': 'CONVERSATION_START_ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@rate_limit_chatbot(max_requests_per_hour=30)
def send_message(request, conversation_id):
    """
    Envia mensagem para conversa específica e recebe resposta da IA
    """
    start_time = time.time()
    
    try:
        # Validação do ID da conversa
        try:
            conversation_id = int(conversation_id)
        except (ValueError, TypeError):
            return Response({
                'error': 'ID da conversa inválido',
                'provided_id': str(conversation_id),
                'expected_format': 'número inteiro'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parâmetros da mensagem
        message = request.data.get('message', '').strip()
        context_hint = request.data.get('context_hint', '')  # Dica de contexto opcional
        
        # Validações da mensagem
        if not message:
            return Response({
                'error': 'Mensagem não pode estar vazia',
                'suggestion': 'Digite sua pergunta ou comentário sobre fitness'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(message) > 500:
            return Response({
                'error': 'Mensagem muito longa',
                'max_length': 500,
                'current_length': len(message),
                'suggestion': 'Resuma sua mensagem ou divida em partes menores'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar se conversa pertence ao usuário
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return Response({
                'error': 'Conversa não encontrada',
                'conversation_id': conversation_id,
                'suggestion': 'Verifique o ID da conversa ou inicie uma nova'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar se conversa não está expirada
        if conversation.is_expired():
            return Response({
                'error': 'Conversa expirada',
                'expired_at': conversation.expires_at.isoformat() if conversation.expires_at else None,
                'suggestion': 'Inicie uma nova conversa para continuar',
                'conversation_id': conversation_id
            }, status=status.HTTP_410_GONE)
        
        # Cache para evitar mensagens duplicadas
        message_hash = hash(f"{request.user.id}_{conversation_id}_{message}")
        duplicate_check_key = f"message_hash_{message_hash}"
        
        if cache.get(duplicate_check_key):
            return Response({
                'error': 'Mensagem duplicada detectada',
                'suggestion': 'Aguarde um momento antes de enviar a mesma mensagem novamente',
                'wait_seconds': 10
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Marcar mensagem como processada para evitar duplicatas
        cache.set(duplicate_check_key, True, 10)  # 10 segundos
        
        # Inicializar serviço de chat
        try:
            chat_service = ChatService()
        except Exception as e:
            logger.error(f"Error initializing ChatService: {e}")
            return Response({
                'error': 'Serviço de chat temporariamente indisponível',
                'suggestion': 'Tente novamente em alguns minutos'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Processar mensagem
        response_data = chat_service.process_user_message(conversation_id, message)
        
        if 'error' in response_data:
            return Response({
                'message_processing_failed': True,
                'error': response_data['error'],
                'suggestion': response_data.get('suggestion'),
                'conversation_id': conversation_id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Atualizar métricas
        try:
            ChatMetrics.update_daily_metrics(request.user)
        except Exception as e:
            logger.warning(f"Failed to update chat metrics: {e}")
        
        # Enriquecer resposta com metadados
        enriched_response = {
            'message_sent': True,
            'conversation_id': conversation_id,
            'ai_response': {
                'content': response_data['response'],
                'message_id': response_data['message_id'],
                'confidence_score': response_data.get('confidence_score', 0.8),
                'response_method': response_data.get('method', 'unknown'),
                'intent_detected': response_data.get('intent_detected'),
                'response_time_ms': response_data.get('response_time_ms', 0)
            },
            'conversation_status': {
                'total_messages': conversation.message_count + 2,  # +2 para user + ai
                'conversation_active': True,
                'last_activity': timezone.now().isoformat()
            },
            'suggested_actions': response_data.get('suggested_actions', []),
            'workout_references': response_data.get('workout_references', []),
            'follow_up_suggestions': [
                "Precisa de mais detalhes sobre algum exercício?",
                "Gostaria de sugestões de treino?",
                "Tem outras dúvidas sobre fitness?"
            ],
            'metadata': {
                'processed_at': timezone.now().isoformat(),
                'total_processing_time_ms': round((time.time() - start_time) * 1000, 2),
                'ai_available': chat_service.ai_service.is_available,
                'fallback_used': response_data.get('method') == 'rule_based_fallback'
            }
        }
        
        return Response(enriched_response)
        
    except Exception as e:
        logger.error(f"Error processing message in conversation {conversation_id}: {e}")
        return Response({
            'error': 'Erro interno ao processar mensagem',
            'conversation_id': conversation_id,
            'suggestion': 'Tente novamente ou reformule sua pergunta',
            'error_code': 'MESSAGE_PROCESSING_ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@rate_limit_chatbot(max_requests_per_hour=50)
def get_conversation_history(request, conversation_id):
    """
    Recupera histórico completo de uma conversa
    """
    try:
        # Validar ID da conversa
        try:
            conversation_id = int(conversation_id)
        except (ValueError, TypeError):
            return Response({
                'error': 'ID da conversa inválido',
                'provided_id': str(conversation_id)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parâmetros de paginação
        limit = min(int(request.GET.get('limit', 50)), 100)  # Máximo 100 mensagens
        offset = int(request.GET.get('offset', 0))
        include_context = request.GET.get('include_context', 'false').lower() == 'true'
        
        # Verificar se conversa existe e pertence ao usuário
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return Response({
                'error': 'Conversa não encontrada',
                'conversation_id': conversation_id
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Cache key para histórico
        cache_key = f"conversation_history_{conversation_id}_{offset}_{limit}"
        cached_history = cache.get(cache_key)
        
        if cached_history and not include_context:
            cached_history['from_cache'] = True
            return Response(cached_history)
        
        # Buscar mensagens
        messages_queryset = conversation.messages.order_by('created_at')[offset:offset + limit]
        
        # Processar mensagens
        messages_data = []
        for message in messages_queryset:
            message_data = {
                'id': message.id,
                'type': message.message_type,
                'content': message.content,
                'timestamp': message.created_at.isoformat(),
                'status': message.status,
                'intent_detected': message.intent_detected,
                'confidence_score': message.confidence_score,
                'user_reaction': message.user_reaction,
                'user_feedback': message.user_feedback
            }
            
            # Metadados específicos da IA
            if message.message_type == 'ai':
                message_data['ai_metadata'] = {
                    'model_version': message.ai_model_version,
                    'response_time_ms': message.response_time_ms,
                    'tokens_used': message.tokens_used
                }
            
            # Referências externas
            if message.referenced_workout_id:
                message_data['workout_reference'] = message.referenced_workout_id
            if message.referenced_exercise_id:
                message_data['exercise_reference'] = message.referenced_exercise_id
            
            messages_data.append(message_data)
        
        # Informações da conversa
        conversation_info = {
            'id': conversation.id,
            'title': conversation.title,
            'type': conversation.conversation_type,
            'status': conversation.status,
            'created_at': conversation.created_at.isoformat(),
            'last_activity': conversation.last_activity_at.isoformat(),
            'total_messages': conversation.message_count,
            'ai_responses': conversation.ai_responses_count,
            'user_rating': conversation.user_satisfaction_rating,
            'expires_at': conversation.expires_at.isoformat() if conversation.expires_at else None
        }
        
        # Contexto adicional se solicitado
        context_data = {}
        if include_context:
            try:
                chat_service = ChatService()
                context_data = chat_service._build_conversation_context(conversation)
            except Exception as e:
                logger.warning(f"Failed to build conversation context: {e}")
        
        response_data = {
            'conversation': conversation_info,
            'messages': messages_data,
            'pagination': {
                'total_messages': conversation.message_count,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < conversation.message_count,
                'next_offset': offset + limit if (offset + limit) < conversation.message_count else None
            },
            'context': context_data if include_context else None,
            'metadata': {
                'retrieved_at': timezone.now().isoformat(),
                'message_count_returned': len(messages_data),
                'context_included': include_context,
                'from_cache': False
            }
        }
        
        # Cache por 5 minutos (conversas ativas mudam frequentemente)
        if not include_context:
            cache.set(cache_key, response_data, 300)
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error getting conversation history {conversation_id}: {e}")
        return Response({
            'error': 'Erro ao recuperar histórico da conversa',
            'conversation_id': conversation_id,
            'suggestion': 'Verifique o ID da conversa e tente novamente'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@rate_limit_chatbot(max_requests_per_hour=20)
def get_user_conversations(request):
    """
    Lista todas as conversas do usuário com filtros e paginação
    """
    try:
        # Parâmetros de filtro
        status_filter = request.GET.get('status', 'all')  # all, active, completed, archived
        conversation_type = request.GET.get('type', 'all')
        days = int(request.GET.get('days', 30))  # Últimos X dias
        limit = min(int(request.GET.get('limit', 20)), 50)
        offset = int(request.GET.get('offset', 0))
        
        # Construir query
        conversations_query = Conversation.objects.filter(user=request.user)
        
        # Filtrar por status
        if status_filter != 'all':
            valid_statuses = ['active', 'completed', 'archived', 'paused']
            if status_filter in valid_statuses:
                conversations_query = conversations_query.filter(status=status_filter)
        
        # Filtrar por tipo
        if conversation_type != 'all':
            conversations_query = conversations_query.filter(conversation_type=conversation_type)
        
        # Filtrar por período
        if days > 0:
            start_date = timezone.now() - timedelta(days=min(days, 365))  # Máximo 1 ano
            conversations_query = conversations_query.filter(created_at__gte=start_date)
        
        # Ordenar e paginar
        conversations_query = conversations_query.order_by('-last_activity_at')
        total_conversations = conversations_query.count()
        conversations = conversations_query[offset:offset + limit]
        
        # Processar conversas
        conversations_data = []
        for conv in conversations:
            # Última mensagem
            last_message = conv.messages.order_by('-created_at').first()
            
            conv_data = {
                'id': conv.id,
                'title': conv.title,
                'type': conv.conversation_type,
                'status': conv.status,
                'created_at': conv.created_at.isoformat(),
                'last_activity': conv.last_activity_at.isoformat(),
                'message_count': conv.message_count,
                'ai_responses_count': conv.ai_responses_count,
                'user_rating': conv.user_satisfaction_rating,
                'is_expired': conv.is_expired(),
                'last_message': {
                    'content': last_message.content[:100] + "..." if last_message and len(last_message.content) > 100 else last_message.content if last_message else None,
                    'type': last_message.message_type if last_message else None,
                    'timestamp': last_message.created_at.isoformat() if last_message else None
                } if last_message else None
            }
            
            conversations_data.append(conv_data)
        
        # Estatísticas do usuário
        user_stats = {
            'total_conversations': total_conversations,
            'active_conversations': Conversation.objects.filter(
                user=request.user, status='active'
            ).count(),
            'completed_conversations': Conversation.objects.filter(
                user=request.user, status='completed'
            ).count(),
            'average_messages_per_conversation': round(
                sum([c.message_count for c in conversations]) / len(conversations)
            ) if conversations else 0,
            'favorite_conversation_type': _get_favorite_conversation_type(request.user)
        }
        
        response_data = {
            'conversations': conversations_data,
            'user_statistics': user_stats,
            'pagination': {
                'total': total_conversations,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total_conversations,
                'next_offset': offset + limit if (offset + limit) < total_conversations else None
            },
            'filters_applied': {
                'status': status_filter,
                'type': conversation_type,
                'days': days
            },
            'available_filters': {
                'statuses': ['all', 'active', 'completed', 'archived'],
                'types': ['all', 'workout_consultation', 'nutrition_advice', 'progress_analysis', 
                         'motivation_chat', 'technique_guidance', 'general_fitness']
            }
        }
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error getting user conversations for user {request.user.id}: {e}")
        return Response({
            'error': 'Erro ao recuperar conversas do usuário',
            'suggestion': 'Tente novamente ou ajuste os filtros'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@rate_limit_chatbot(max_requests_per_hour=20)
def end_conversation(request, conversation_id):
    """
    Finaliza uma conversa com avaliação opcional do usuário
    """
    try:
        # Validar ID
        try:
            conversation_id = int(conversation_id)
        except (ValueError, TypeError):
            return Response({
                'error': 'ID da conversa inválido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parâmetros de finalização
        user_rating = request.data.get('rating')
        feedback = request.data.get('feedback', '').strip()
        
        # Validar rating se fornecido
        if user_rating is not None:
            try:
                user_rating = float(user_rating)
                if not (1.0 <= user_rating <= 5.0):
                    return Response({
                        'error': 'Avaliação deve estar entre 1.0 e 5.0',
                        'provided_rating': user_rating
                    }, status=status.HTTP_400_BAD_REQUEST)
            except (ValueError, TypeError):
                return Response({
                    'error': 'Formato de avaliação inválido',
                    'expected_format': 'número decimal entre 1.0 e 5.0'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar se conversa existe e pertence ao usuário
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return Response({
                'error': 'Conversa não encontrada',
                'conversation_id': conversation_id
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar se conversa pode ser finalizada
        if conversation.status == 'completed':
            return Response({
                'message': 'Conversa já estava finalizada',
                'conversation_id': conversation_id,
                'completed_at': conversation.updated_at.isoformat()
            })
        
        # Finalizar conversa usando ChatService
        try:
            chat_service = ChatService()
            result = chat_service.end_conversation(conversation_id, user_rating)
            
            if 'error' in result:
                return Response({
                    'error': result['error'],
                    'conversation_id': conversation_id
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Error using ChatService to end conversation: {e}")
            # Fallback manual
            conversation.status = 'completed'
            if user_rating:
                conversation.user_satisfaction_rating = user_rating
            conversation.save()
            
            result = {
                'conversation_ended': True,
                'total_messages': conversation.message_count,
                'rating_saved': user_rating is not None
            }
        
        # Salvar feedback adicional se fornecido
        if feedback and len(feedback) <= 500:
            # Encontrar última mensagem da IA para adicionar feedback
            last_ai_message = conversation.messages.filter(message_type='ai').order_by('-created_at').first()
            if last_ai_message:
                last_ai_message.user_feedback = feedback
                last_ai_message.save()
        
        # Atualizar métricas
        try:
            ChatMetrics.update_daily_metrics(request.user)
        except Exception as e:
            logger.warning(f"Failed to update metrics after ending conversation: {e}")
        
        response_data = {
            'conversation_ended': True,
            'conversation_id': conversation_id,
            'final_statistics': {
                'total_messages': result.get('total_messages', conversation.message_count),
                'duration_minutes': result.get('duration_minutes', 0),
                'user_rating': user_rating,
                'feedback_saved': bool(feedback)
            },
            'conversation_summary': {
                'type': conversation.conversation_type,
                'ai_responses_count': conversation.ai_responses_count,
                'completed_at': timezone.now().isoformat()
            },
            'thank_you_message': "Obrigado por usar o chatbot fitness! Sua conversa foi finalizada e seu feedback nos ajuda a melhorar.",
            'next_steps': [
                "Inicie uma nova conversa quando precisar",
                "Explore outras funcionalidades do app",
                "Continue sua jornada fitness!"
            ]
        }
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error ending conversation {conversation_id}: {e}")
        return Response({
            'error': 'Erro ao finalizar conversa',
            'conversation_id': conversation_id,
            'suggestion': 'Tente novamente'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@rate_limit_chatbot(max_requests_per_hour=40)
def message_feedback(request, message_id):
    """
    Permite usuário dar feedback específico em mensagens da IA
    """
    try:
        # Validar ID da mensagem
        try:
            message_id = int(message_id)
        except (ValueError, TypeError):
            return Response({
                'error': 'ID da mensagem inválido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parâmetros do feedback
        reaction = request.data.get('reaction', '').strip()
        feedback_text = request.data.get('feedback', '').strip()
        
        # Validar reação
        valid_reactions = ['helpful', 'not_helpful', 'excellent', 'needs_improvement']
        if reaction not in valid_reactions:
            return Response({
                'error': 'Reação inválida',
                'valid_reactions': valid_reactions,
                'provided': reaction
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar feedback text
        if feedback_text and len(feedback_text) > 300:
            return Response({
                'error': 'Feedback muito longo',
                'max_length': 300,
                'current_length': len(feedback_text)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Buscar mensagem e verificar se pertence ao usuário
        try:
            message = Message.objects.get(
                id=message_id,
                conversation__user=request.user,
                message_type='ai'  # Só permitir feedback em mensagens da IA
            )
        except Message.DoesNotExist:
            return Response({
                'error': 'Mensagem não encontrada ou não é uma mensagem da IA',
                'message_id': message_id
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar se feedback já foi dado (evitar spam)
        if message.user_reaction and message.user_reaction == reaction:
            return Response({
                'message': 'Feedback já registrado anteriormente',
                'current_reaction': message.user_reaction,
                'message_id': message_id
            })
        
        # Salvar feedback
        message.add_user_feedback(reaction, feedback_text if feedback_text else None)
        
        # Atualizar métricas de qualidade
        try:
            _update_feedback_metrics(message, reaction)
        except Exception as e:
            logger.warning(f"Failed to update feedback metrics: {e}")
        
        response_data = {
            'feedback_saved': True,
            'message_id': message_id,
            'reaction': reaction,
            'feedback_text_saved': bool(feedback_text),
            'message': 'Obrigado pelo feedback! Isso nos ajuda a melhorar as respostas.',
            'impact': {
                'improves_ai_quality': True,
                'helps_personalization': True,
                'contributes_to_learning': True
            },
            'metadata': {
                'feedback_given_at': timezone.now().isoformat(),
                'conversation_id': message.conversation.id
            }
        }
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error saving message feedback {message_id}: {e}")
        return Response({
            'error': 'Erro ao salvar feedback',
            'message_id': message_id,
            'suggestion': 'Tente novamente'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@rate_limit_chatbot(max_requests_per_hour=10)
def get_chat_analytics(request):
    """
    Retorna analytics pessoais do usuário sobre uso do chatbot
    """
    try:
        # Parâmetros de período
        days = min(int(request.GET.get('days', 30)), 90)  # Máximo 90 dias
        
        # Cache das analytics
        cache_key = f"chat_analytics_{request.user.id}_{days}"
        cached_analytics = cache.get(cache_key)
        
        if cached_analytics:
            cached_analytics['from_cache'] = True
            return Response(cached_analytics)
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Buscar conversas do período
        conversations = Conversation.objects.filter(
            user=request.user,
            created_at__gte=start_date
        )
        
        # Métricas básicas
        total_conversations = conversations.count()
        total_messages = sum([c.message_count for c in conversations])
        completed_conversations = conversations.filter(status='completed').count()
        
        # Análise por tipo de conversa
        conversation_types = {}
        for conv in conversations:
            conv_type = conv.conversation_type
            if conv_type not in conversation_types:
                conversation_types[conv_type] = {
                    'count': 0,
                    'total_messages': 0,
                    'average_rating': 0,
                    'ratings_count': 0
                }
            
            conversation_types[conv_type]['count'] += 1
            conversation_types[conv_type]['total_messages'] += conv.message_count
            
            if conv.user_satisfaction_rating:
                conversation_types[conv_type]['average_rating'] += conv.user_satisfaction_rating
                conversation_types[conv_type]['ratings_count'] += 1
        
        # Calcular médias
        for conv_type in conversation_types:
            ratings_count = conversation_types[conv_type]['ratings_count']
            if ratings_count > 0:
                conversation_types[conv_type]['average_rating'] = round(
                    conversation_types[conv_type]['average_rating'] / ratings_count, 1
                )
        
        # Métricas de engajamento
        active_days = conversations.values('created_at__date').distinct().count()
        average_messages_per_conversation = round(total_messages / total_conversations, 1) if total_conversations > 0 else 0
        
        # Análise temporal (últimos 7 dias)
        daily_usage = []
        for i in range(7):
            day = timezone.now().date() - timedelta(days=i)
            day_conversations = conversations.filter(created_at__date=day).count()
            daily_usage.append({
                'date': day.isoformat(),
                'conversations': day_conversations
            })
        
        # Feedback e qualidade
        all_messages = Message.objects.filter(
            conversation__user=request.user,
            conversation__created_at__gte=start_date,
            message_type='ai'
        )
        
        positive_feedback = all_messages.filter(
            user_reaction__in=['helpful', 'excellent']
        ).count()
        
        negative_feedback = all_messages.filter(
            user_reaction__in=['not_helpful', 'needs_improvement']
        ).count()
        
        total_feedback = positive_feedback + negative_feedback
        satisfaction_percentage = round(
            positive_feedback / total_feedback * 100, 1
        ) if total_feedback > 0 else None
        
        # Insights personalizados
        insights = _generate_usage_insights(
            total_conversations, average_messages_per_conversation, 
            conversation_types, satisfaction_percentage
        )
        
        analytics_data = {
            'period_analyzed': {
                'days': days,
                'start_date': start_date.date().isoformat(),
                'end_date': timezone.now().date().isoformat()
            },
            'usage_summary': {
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'completed_conversations': completed_conversations,
                'active_days': active_days,
                'average_messages_per_conversation': average_messages_per_conversation
            },
            'conversation_breakdown': conversation_types,
            'engagement_metrics': {
                'daily_usage_last_7_days': list(reversed(daily_usage)),
                'most_used_conversation_type': max(conversation_types, key=lambda x: conversation_types[x]['count']) if conversation_types else None,
                'consistency_score': round(active_days / days * 100, 1) if days > 0 else 0
            },
            'quality_metrics': {
                'total_feedback_given': total_feedback,
                'positive_feedback': positive_feedback,
                'negative_feedback': negative_feedback,
                'satisfaction_percentage': satisfaction_percentage
            },
            'personalized_insights': insights,
            'recommendations': [
                "Continue usando o chat para dúvidas fitness",
                "Experimente diferentes tipos de conversa",
                "Dê feedback para melhorar as respostas"
            ],
            'metadata': {
                'generated_at': timezone.now().isoformat(),
                'from_cache': False
            }
        }
        
        # Cache por 1 hora
        cache.set(cache_key, analytics_data, 3600)
        
        return Response(analytics_data)
        
    except Exception as e:
        logger.error(f"Error generating chat analytics for user {request.user.id}: {e}")
        return Response({
            'error': 'Erro ao gerar analytics do chat',
            'suggestion': 'Tente novamente mais tarde'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# FUNÇÕES AUXILIARES

def _get_favorite_conversation_type(user) -> str:
    """Identifica tipo de conversa mais usado pelo usuário"""
    try:
        from django.db.models import Count
        result = Conversation.objects.filter(user=user).values(
            'conversation_type'
        ).annotate(
            count=Count('id')
        ).order_by('-count').first()
        
        return result['conversation_type'] if result else 'general_fitness'
    except:
        return 'general_fitness'


def _update_feedback_metrics(message: Message, reaction: str):
    """Atualiza métricas baseadas no feedback do usuário"""
    try:
        # Implementar lógica de atualização de métricas
        # Por exemplo, salvar em cache para dashboard de qualidade
        metrics_key = f"ai_quality_metrics_{timezone.now().strftime('%Y-%m-%d')}"
        daily_metrics = cache.get(metrics_key, {'positive': 0, 'negative': 0, 'total': 0})
        
        if reaction in ['helpful', 'excellent']:
            daily_metrics['positive'] += 1
        elif reaction in ['not_helpful', 'needs_improvement']:
            daily_metrics['negative'] += 1
        
        daily_metrics['total'] += 1
        cache.set(metrics_key, daily_metrics, 86400)  # 24 horas
        
    except Exception as e:
        logger.error(f"Error updating feedback metrics: {e}")


def _generate_usage_insights(total_conversations: int, avg_messages: float, 
                           conversation_types: dict, satisfaction: float) -> List[str]:
    """Gera insights personalizados baseados no uso"""
    insights = []
    
    if total_conversations == 0:
        insights.append("Você ainda não iniciou conversas com o chatbot. Experimente começar com dúvidas sobre exercícios!")
        return insights
    
    if total_conversations >= 10:
        insights.append("Parabéns! Você é um usuário ativo do chatbot fitness.")
    elif total_conversations >= 5:
        insights.append("Você está explorando bem o chatbot. Continue fazendo perguntas!")
    else:
        insights.append("Que tal fazer mais perguntas sobre fitness? O chatbot tem muito a oferecer.")
    
    if avg_messages > 10:
        insights.append("Suas conversas são bem detalhadas, o que permite respostas mais personalizadas.")
    elif avg_messages < 5:
        insights.append("Experimente fazer mais perguntas por conversa para obter orientações mais completas.")
    
    if satisfaction and satisfaction > 80:
        insights.append("Você está muito satisfeito com as respostas! Continue dando feedback.")
    elif satisfaction and satisfaction < 60:
        insights.append("Notamos que algumas respostas não foram úteis. Seu feedback ajuda a melhorar!")
    
    # Análise de tipos de conversa
    if conversation_types:
        most_used = max(conversation_types, key=lambda x: conversation_types[x]['count'])
        if most_used == 'workout_consultation':
            insights.append("Você foca bastante em consultoria de treinos. Ótima estratégia!")
        elif most_used == 'motivation_chat':
            insights.append("Buscar motivação é essencial. Continue cuidando da sua mente também!")
    
    if len(conversation_types) >= 4:
        insights.append("Você explora diversos temas fitness. Isso demonstra uma abordagem completa!")
    
    return insights