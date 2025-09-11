# apps/notifications/services/notification_service.py
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Q, Avg
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
import random

from ..models import (
    NotificationPreference, 
    NotificationLog, 
    NotificationTemplate,
    UserNotificationStats
)
from apps.users.models import UserProfile
from apps.workouts.models import WorkoutSession, Workout
from apps.recommendations.services.ai_service import AIService

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Serviço principal para gerenciar notificações inteligentes
    """
    
    def __init__(self):
        self.ai_service = self._get_ai_service()
    
    def _get_ai_service(self):
        """Inicializa AIService se disponível"""
        try:
            return AIService()
        except Exception as e:
            logger.warning(f"AIService não disponível: {e}")
            return None
    
    # =============================================
    # MÉTODOS PRINCIPAIS DE CRIAÇÃO
    # =============================================
    
    def create_notification(
        self, 
        user: User, 
        notification_type: str,
        title: str = None,
        message: str = None,
        template_name: str = None,
        context_data: Dict = None,
        delivery_channel: str = 'in_app',
        priority: str = 'normal',
        scheduled_for: datetime = None
    ) -> NotificationLog:
        """
        Cria uma nova notificação
        """
        # Verificar preferências do usuário
        if not self._should_send_notification(user, notification_type, delivery_channel):
            logger.info(f"Notificação bloqueada pelas preferências: {user.username} - {notification_type}")
            return None
        
        # Se não forneceu título/mensagem, usar template
        if not title or not message:
            title, message = self._get_content_from_template(
                notification_type, template_name, user, context_data or {}
            )
        
        # Personalizar com IA se disponível
        if self.ai_service and self.ai_service.is_available:
            try:
                title, message = self._enhance_with_ai(user, notification_type, title, message, context_data)
            except Exception as e:
                logger.warning(f"Erro na personalização IA: {e}")
        
        # Determinar quando enviar
        if not scheduled_for:
            scheduled_for = self._get_optimal_send_time(user, notification_type)
        
        # Criar a notificação
        notification = NotificationLog.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            delivery_channel=delivery_channel,
            priority=priority,
            scheduled_for=scheduled_for,
            context_data=context_data or {}
        )
        
        logger.info(f"Notificação criada: {notification.id} para {user.username}")
        return notification
    
    def send_workout_reminder(self, user: User, context_data: Dict = None) -> Optional[NotificationLog]:
        """
        Envia lembrete de treino personalizado
        """
        # Verificar se deve enviar (não treinou hoje, etc.)
        if not self._should_send_workout_reminder(user):
            return None
        
        # Enriquecer contexto
        enhanced_context = self._build_workout_reminder_context(user, context_data or {})
        
        return self.create_notification(
            user=user,
            notification_type='workout_reminder',
            template_name='smart_workout_reminder',
            context_data=enhanced_context,
            priority='normal'
        )
    
    def send_achievement_notification(self, user: User, achievement_type: str, context_data: Dict = None) -> Optional[NotificationLog]:
        """
        Envia notificação de conquista
        """
        enhanced_context = self._build_achievement_context(user, achievement_type, context_data or {})
        
        return self.create_notification(
            user=user,
            notification_type='achievement',
            template_name=f'achievement_{achievement_type}',
            context_data=enhanced_context,
            priority='high'
        )
    
    def send_motivation_message(self, user: User, context_type: str = 'general', context_data: Dict = None) -> Optional[NotificationLog]:
        """
        Envia mensagem motivacional contextual
        """
        enhanced_context = self._build_motivation_context(user, context_type, context_data or {})
        
        return self.create_notification(
            user=user,
            notification_type='motivation',
            template_name=f'motivation_{context_type}',
            context_data=enhanced_context,
            priority='normal'
        )
    
    def send_progress_summary(self, user: User, period: str = 'weekly') -> Optional[NotificationLog]:
        """
        Envia resumo de progresso
        """
        progress_data = self._analyze_user_progress(user, period)
        
        if not progress_data['has_data']:
            return None
        
        return self.create_notification(
            user=user,
            notification_type='progress',
            template_name=f'progress_summary_{period}',
            context_data=progress_data,
            priority='normal'
        )
    
    def send_comeback_message(self, user: User) -> Optional[NotificationLog]:
        """
        Mensagem de volta para usuários inativos
        """
        last_workout = self._get_last_workout_date(user)
        if not last_workout or (timezone.now().date() - last_workout).days < 3:
            return None
        
        context = {
            'days_inactive': (timezone.now().date() - last_workout).days,
            'last_workout_date': last_workout.strftime('%d/%m/%Y')
        }
        
        return self.create_notification(
            user=user,
            notification_type='comeback',
            template_name='comeback_message',
            context_data=context,
            priority='high'
        )
    
    # =============================================
    # MÉTODOS DE AGENDAMENTO INTELIGENTE
    # =============================================
    
    def schedule_smart_reminders(self, user: User, days_ahead: int = 7):
        """
        Agenda lembretes inteligentes para os próximos dias
        """
        user_pattern = self._analyze_user_workout_pattern(user)
        
        for day_offset in range(1, days_ahead + 1):
            target_date = timezone.now().date() + timedelta(days=day_offset)
            
            # Verificar se deve agendar para este dia
            if self._should_schedule_reminder_for_date(user, target_date, user_pattern):
                scheduled_time = self._get_optimal_time_for_date(user, target_date)
                
                # Criar notificação agendada
                self.create_notification(
                    user=user,
                    notification_type='workout_reminder',
                    template_name='daily_reminder',
                    context_data={'target_date': target_date.isoformat()},
                    scheduled_for=scheduled_time
                )
    
    def process_pending_notifications(self, batch_size: int = 50) -> Dict[str, int]:
        """
        Processa notificações pendentes
        """
        now = timezone.now()
        pending_notifications = NotificationLog.objects.filter(
            status='pending',
            scheduled_for__lte=now
        )[:batch_size]
        
        results = {'sent': 0, 'failed': 0, 'skipped': 0}
        
        for notification in pending_notifications:
            try:
                # Verificar se ainda deve enviar
                if not self._should_send_notification(
                    notification.user, 
                    notification.notification_type, 
                    notification.delivery_channel
                ):
                    notification.status = 'cancelled'
                    notification.save()
                    results['skipped'] += 1
                    continue
                
                # Enviar conforme o canal
                success = self._send_via_channel(notification)
                
                if success:
                    notification.mark_as_sent()
                    self._update_user_stats(notification)
                    results['sent'] += 1
                else:
                    notification.mark_as_failed("Erro no envio")
                    results['failed'] += 1
                    
            except Exception as e:
                logger.error(f"Erro processando notificação {notification.id}: {e}")
                notification.mark_as_failed(str(e))
                results['failed'] += 1
        
        return results
    
    # =============================================
    # MÉTODOS DE VERIFICAÇÃO E VALIDAÇÃO
    # =============================================
    
    def _should_send_notification(self, user: User, notification_type: str, delivery_channel: str) -> bool:
        """
        Verifica se deve enviar a notificação baseado nas preferências
        """
        try:
            preference = NotificationPreference.objects.get(
                user=user,
                notification_type=notification_type,
                delivery_channel=delivery_channel
            )
            
            if not preference.enabled:
                return False
            
            # Verificar frequência
            if not self._check_frequency_limit(user, notification_type, preference.frequency_days):
                return False
            
            # Verificar contexto (dias inativos, descanso, etc.)
            if preference.only_on_inactive_days and self._user_worked_out_today(user):
                return False
            
            return True
            
        except NotificationPreference.DoesNotExist:
            # Usar configurações padrão se não tem preferência
            return self._get_default_send_decision(user, notification_type)
    
    def _should_send_workout_reminder(self, user: User) -> bool:
        """
        Lógica específica para lembretes de treino
        """
        # Não enviar se já treinou hoje
        if self._user_worked_out_today(user):
            return False
        
        # Não enviar se já enviou lembrete hoje
        today_reminders = NotificationLog.objects.filter(
            user=user,
            notification_type='workout_reminder',
            created_at__date=timezone.now().date()
        ).count()
        
        if today_reminders >= 2:  # Máximo 2 lembretes por dia
            return False
        
        return True
    
    def _check_frequency_limit(self, user: User, notification_type: str, frequency_days: int) -> bool:
        """
        Verifica se respeita a frequência configurada
        """
        cutoff_date = timezone.now() - timedelta(days=frequency_days)
        
        recent_notifications = NotificationLog.objects.filter(
            user=user,
            notification_type=notification_type,
            created_at__gte=cutoff_date,
            status__in=['sent', 'delivered', 'opened', 'clicked']
        ).count()
        
        return recent_notifications == 0
    
    # =============================================
    # MÉTODOS DE CONTEÚDO E PERSONALIZAÇÃO
    # =============================================
    
    def _get_content_from_template(
        self, 
        notification_type: str, 
        template_name: str, 
        user: User, 
        context_data: Dict
    ) -> Tuple[str, str]:
        """
        Obtém conteúdo do template com personalização
        """
        try:
            # Buscar template específico ou genérico
            template = None
            if template_name:
                template = NotificationTemplate.objects.filter(
                    notification_type=notification_type,
                    name=template_name,
                    active=True
                ).first()
            
            if not template:
                template = NotificationTemplate.objects.filter(
                    notification_type=notification_type,
                    active=True
                ).first()
            
            if template:
                # Enriquecer contexto com dados do usuário
                full_context = self._build_user_context(user)
                full_context.update(context_data)
                
                title, message = template.render(full_context)
                template.increment_usage()
                
                return title, message
            
        except Exception as e:
            logger.error(f"Erro no template: {e}")
        
        # Fallback: conteúdo padrão
        return self._get_fallback_content(notification_type, user, context_data)
    
    def _enhance_with_ai(
        self, 
        user: User, 
        notification_type: str, 
        title: str, 
        message: str, 
        context_data: Dict
    ) -> Tuple[str, str]:
        """
        Melhora o conteúdo usando IA
        """
        try:
            profile = UserProfile.objects.get(user=user)
            
            # Usar IA para personalizar mensagem
            enhanced_message = self.ai_service.generate_motivational_content(
                profile, 
                context=notification_type,
                base_message=message
            )
            
            if enhanced_message and len(enhanced_message) > 10:
                return title, enhanced_message
                
        except Exception as e:
            logger.error(f"Erro na personalização IA: {e}")
        
        return title, message
    
    def _build_user_context(self, user: User) -> Dict:
        """
        Constrói contexto básico do usuário para templates
        """
        context = {
            'user_name': user.first_name or user.username,
            'username': user.username
        }
        
        try:
            profile = UserProfile.objects.get(user=user)
            context.update({
                'user_goal': profile.goal or 'fitness',
                'activity_level': profile.activity_level or 'moderado'
            })
        except UserProfile.DoesNotExist:
            pass
        
        # Adicionar estatísticas básicas
        total_workouts = WorkoutSession.objects.filter(user=user, completed=True).count()
        context['total_workouts'] = total_workouts
        
        return context
    
    def _build_workout_reminder_context(self, user: User, base_context: Dict) -> Dict:
        """
        Contexto específico para lembretes de treino
        """
        context = base_context.copy()
        
        # Último treino
        last_workout = WorkoutSession.objects.filter(
            user=user, completed=True
        ).order_by('-completed_at').first()
        
        if last_workout:
            days_since = (timezone.now().date() - last_workout.completed_at.date()).days
            context.update({
                'days_since_last_workout': days_since,
                'last_workout_name': last_workout.workout.name,
                'motivation_level': 'high' if days_since >= 3 else 'normal'
            })
        
        # Treino sugerido
        suggested_workout = self._get_suggested_workout(user)
        if suggested_workout:
            context['suggested_workout'] = suggested_workout.name
            context['workout_duration'] = suggested_workout.estimated_duration
        
        return context
    
    def _build_achievement_context(self, user: User, achievement_type: str, base_context: Dict) -> Dict:
        """
        Contexto para notificações de conquista
        """
        context = base_context.copy()
        context['achievement_type'] = achievement_type
        
        # Adicionar dados específicos da conquista
        if achievement_type == 'streak':
            streak_days = context.get('streak_days', 0)
            context['celebration_level'] = 'high' if streak_days >= 7 else 'normal'
        elif achievement_type == 'milestone':
            milestone = context.get('milestone_number', 0)
            context['milestone_description'] = f"{milestone}º treino concluído"
        
        return context
    
    # =============================================
    # MÉTODOS DE ANÁLISE E OTIMIZAÇÃO
    # =============================================
    
    def _get_optimal_send_time(self, user: User, notification_type: str) -> datetime:
        """
        Determina o melhor horário para enviar
        """
        now = timezone.now()
        
        # Verificar preferências explícitas
        try:
            preference = NotificationPreference.objects.get(
                user=user,
                notification_type=notification_type
            )
            
            if preference.custom_time:
                # Usar horário personalizado
                target_time = preference.custom_time
            else:
                # Usar faixas predefinidas
                time_ranges = {
                    'morning': (7, 11),
                    'afternoon': (12, 17),
                    'evening': (18, 21)
                }
                
                start_hour, end_hour = time_ranges.get(preference.preferred_time, (9, 17))
                target_hour = random.randint(start_hour, end_hour)
                target_time = timezone.datetime.min.time().replace(
                    hour=target_hour, 
                    minute=random.randint(0, 59)
                )
            
        except NotificationPreference.DoesNotExist:
            # Usar estatísticas ou padrão
            target_time = self._get_user_best_time(user) or timezone.datetime.min.time().replace(hour=9)
        
        # Calcular próxima ocorrência deste horário
        target_datetime = timezone.now().replace(
            hour=target_time.hour,
            minute=target_time.minute,
            second=0,
            microsecond=0
        )
        
        # Se já passou hoje, agendar para amanhã
        if target_datetime <= now:
            target_datetime += timedelta(days=1)
        
        return target_datetime
    
    def _analyze_user_workout_pattern(self, user: User) -> Dict:
        """
        Analisa padrões de treino do usuário
        """
        # Cache por 1 hora
        cache_key = f"workout_pattern_{user.id}"
        cached_pattern = cache.get(cache_key)
        if cached_pattern:
            return cached_pattern
        
        # Analisar últimos 30 dias
        cutoff_date = timezone.now() - timedelta(days=30)
        sessions = WorkoutSession.objects.filter(
            user=user,
            completed=True,
            completed_at__gte=cutoff_date
        ).order_by('completed_at')
        
        pattern = {
            'total_workouts': sessions.count(),
            'avg_per_week': sessions.count() / 4.3,
            'preferred_days': [],
            'preferred_times': [],
            'consistency_score': 0
        }
        
        if sessions.exists():
            # Analisar dias da semana preferidos
            day_counts = {}
            time_counts = {}
            
            for session in sessions:
                weekday = session.completed_at.weekday()
                hour = session.completed_at.hour
                
                day_counts[weekday] = day_counts.get(weekday, 0) + 1
                time_range = self._get_time_range(hour)
                time_counts[time_range] = time_counts.get(time_range, 0) + 1
            
            # Dias mais frequentes
            sorted_days = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)
            pattern['preferred_days'] = [day for day, count in sorted_days[:3]]
            
            # Horários mais frequentes
            sorted_times = sorted(time_counts.items(), key=lambda x: x[1], reverse=True)
            pattern['preferred_times'] = [time_range for time_range, count in sorted_times[:2]]
            
            # Score de consistência (0-100)
            weeks = max(1, (timezone.now() - sessions.first().completed_at).days / 7)
            pattern['consistency_score'] = min(100, (pattern['total_workouts'] / weeks) * 25)
        
        cache.set(cache_key, pattern, 3600)
        return pattern
    
    def _analyze_user_progress(self, user: User, period: str = 'weekly') -> Dict:
        """
        Analisa progresso do usuário
        """
        days = {'weekly': 7, 'monthly': 30}.get(period, 7)
        cutoff_date = timezone.now() - timedelta(days=days)
        
        sessions = WorkoutSession.objects.filter(
            user=user,
            completed=True,
            completed_at__gte=cutoff_date
        )
        
        if not sessions.exists():
            return {'has_data': False}
        
        progress_data = {
            'has_data': True,
            'period': period,
            'total_workouts': sessions.count(),
            'total_time': sum(s.duration_minutes or 0 for s in sessions),
            'avg_rating': sessions.aggregate(Avg('user_rating'))['user_rating__avg'] or 0,
            'total_calories': sum(s.calories_burned or 0 for s in sessions),
            'improvement_areas': self._identify_improvement_areas(user, sessions),
            'achievements': self._identify_recent_achievements(user, sessions)
        }
        
        return progress_data
    
    # =============================================
    # MÉTODOS AUXILIARES
    # =============================================
    
    def _send_via_channel(self, notification: NotificationLog) -> bool:
        """
        Envia notificação pelo canal especificado
        """
        if notification.delivery_channel == 'in_app':
            return True  # In-app sempre "envia" (fica no banco)
        elif notification.delivery_channel == 'push':
            return self._send_push_notification(notification)
        elif notification.delivery_channel == 'email':
            return self._send_email_notification(notification)
        
        return False
    
    def _send_push_notification(self, notification: NotificationLog) -> bool:
        """
        Placeholder para push notifications
        """
        # TODO: Integrar com FCM/APNS quando implementar mobile
        logger.info(f"Push notification seria enviada: {notification.title}")
        return True
    
    def _send_email_notification(self, notification: NotificationLog) -> bool:
        """
        Placeholder para email notifications
        """
        # TODO: Integrar com sistema de email
        logger.info(f"Email seria enviado: {notification.title}")
        return True
    
    def _user_worked_out_today(self, user: User) -> bool:
        """
        Verifica se o usuário treinou hoje
        """
        return WorkoutSession.objects.filter(
            user=user,
            completed=True,
            completed_at__date=timezone.now().date()
        ).exists()
    
    def _get_last_workout_date(self, user: User) -> Optional[datetime]:
        """
        Retorna a data do último treino
        """
        last_session = WorkoutSession.objects.filter(
            user=user,
            completed=True
        ).order_by('-completed_at').first()
        
        return last_session.completed_at.date() if last_session else None
    
    def _get_suggested_workout(self, user: User) -> Optional[Workout]:
        """
        Sugere um treino baseado no perfil
        """
        try:
            profile = UserProfile.objects.get(user=user)
            
            # Lógica simples de sugestão
            filters = Q(is_recommended=True)
            
            if profile.activity_level in ['sedentary', 'light']:
                filters &= Q(difficulty_level='beginner')
            elif profile.activity_level == 'moderate':
                filters &= Q(difficulty_level__in=['beginner', 'intermediate'])
            
            return Workout.objects.filter(filters).order_by('?').first()
            
        except (UserProfile.DoesNotExist, Workout.DoesNotExist):
            return None
    
    def _get_user_best_time(self, user: User) -> Optional[timezone.datetime.time]:
        """
        Determina melhor horário baseado em estatísticas
        """
        try:
            stats = UserNotificationStats.objects.get(user=user)
            return stats.best_time_to_notify
        except UserNotificationStats.DoesNotExist:
            return None
    
    def _get_time_range(self, hour: int) -> str:
        """
        Converte hora em faixa de tempo
        """
        if 6 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 18:
            return 'afternoon'
        else:
            return 'evening'
    
    def _update_user_stats(self, notification: NotificationLog):
        """
        Atualiza estatísticas do usuário
        """
        stats, created = UserNotificationStats.objects.get_or_create(
            user=notification.user
        )
        stats.update_stats(notification)
    
    def _get_fallback_content(self, notification_type: str, user: User, context_data: Dict) -> Tuple[str, str]:
        """
        Conteúdo padrão quando não há template
        """
        name = user.first_name or user.username
        
        fallbacks = {
            'workout_reminder': (
                f"Hora do treino, {name}!",
                "Que tal fazer alguns exercícios hoje? Seu corpo agradece!"
            ),
            'achievement': (
                f"Parabéns, {name}!",
                "Você alcançou uma nova conquista! Continue assim!"
            ),
            'motivation': (
                f"Vamos lá, {name}!",
                "Cada dia é uma nova oportunidade para ser melhor!"
            ),
            'progress': (
                f"Seu progresso, {name}",
                "Confira como você está evoluindo nos seus treinos!"
            )
        }
        
        return fallbacks.get(notification_type, (
            f"FitAI - {name}",
            "Temos uma novidade para você!"
        ))
    
    def get_user_notification_summary(self, user: User, days: int = 7) -> Dict:
        """
        Resumo das notificações do usuário
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        
        notifications = NotificationLog.objects.filter(
            user=user,
            created_at__gte=cutoff_date
        )
        
        summary = {
            'total_sent': notifications.count(),
            'opened_count': notifications.filter(opened_at__isnull=False).count(),
            'clicked_count': notifications.filter(clicked_at__isnull=False).count(),
            'by_type': {},
            'engagement_rate': 0
        }
        
        # Agrupar por tipo
        for notification in notifications:
            type_name = notification.notification_type
            if type_name not in summary['by_type']:
                summary['by_type'][type_name] = {'sent': 0, 'opened': 0}
            
            summary['by_type'][type_name]['sent'] += 1
            if notification.opened_at:
                summary['by_type'][type_name]['opened'] += 1
        
        # Calcular engajamento
        if summary['total_sent'] > 0:
            summary['engagement_rate'] = round(
                summary['opened_count'] / summary['total_sent'] * 100, 1
            )
        
        return summary