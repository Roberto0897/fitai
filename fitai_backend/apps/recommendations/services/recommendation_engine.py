import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.contrib.auth.models import User

from apps.users.models import UserProfile
from apps.workouts.models import Workout, WorkoutSession, ExerciseLog
from apps.exercises.models import Exercise
from ..models import Recommendation
from .ai_service import AIService

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Motor de recomendações híbrido que combina:
    - IA (OpenAI) para recomendações avançadas
    - Algoritmos baseados em regras (fallback)
    - Machine Learning simples baseado em histórico
    - Filtros colaborativos básicos
    """
    
    def __init__(self):
        self.ai_service = AIService()
        self.algorithms = {
            'ai_personalized': self._ai_personalized_recommendations,
            'content_based': self._content_based_recommendations, 
            'collaborative': self._collaborative_filtering,
            'hybrid': self._hybrid_recommendations
        }
    
    def generate_recommendations(self, user: User, algorithm: str = 'hybrid', 
                               limit: int = 5) -> List[Dict]:
        """
        Gera recomendações usando o algoritmo especificado
        
        Args:
            user: Usuário para gerar recomendações
            algorithm: Tipo de algoritmo ('ai_personalized', 'content_based', 'collaborative', 'hybrid')
            limit: Número máximo de recomendações
        
        Returns:
            Lista de dicionários com recomendações
        """
        try:
            if algorithm not in self.algorithms:
                algorithm = 'hybrid'
            
            recommendations = self.algorithms[algorithm](user, limit)
            
            # Salvar recomendações no banco
            self._save_recommendations(user, recommendations, algorithm)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations for user {user.id}: {e}")
            # Fallback para recomendações básicas
            return self._content_based_recommendations(user, limit)
    
    def _ai_personalized_recommendations(self, user: User, limit: int) -> List[Dict]:
        """Recomendações usando IA da OpenAI"""
        try:
            profile = UserProfile.objects.get(user=user)
            
            # Verificar se IA está disponível
            if not self.ai_service.is_available:
                logger.info("AI not available, falling back to content-based")
                return self._content_based_recommendations(user, limit)
            
            # Analisar progresso primeiro para contexto
            progress_analysis = self.ai_service.analyze_user_progress(profile)
            
            # Buscar treinos disponíveis
            available_workouts = Workout.objects.all()
            
            # Criar contexto para IA
            user_context = self._build_user_context(user)
            
            # Gerar recomendações via IA
            ai_recommendations = self._request_ai_recommendations(
                profile, user_context, available_workouts.values(), limit
            )
            
            if ai_recommendations:
                return self._process_ai_recommendations(ai_recommendations, available_workouts)
            
            # Fallback se IA falhou
            return self._content_based_recommendations(user, limit)
            
        except UserProfile.DoesNotExist:
            return self._content_based_recommendations(user, limit)
        except Exception as e:
            logger.error(f"AI recommendations failed: {e}")
            return self._content_based_recommendations(user, limit)
    
    def _content_based_recommendations(self, user: User, limit: int) -> List[Dict]:
        """Recomendações baseadas no perfil e histórico do usuário"""
        try:
            profile = UserProfile.objects.get(user=user)
            recommendations = []
            
            # Filtro base por nível de atividade
            workout_filter = Q()
            
            if profile.activity_level in ['sedentary', 'light']:
                workout_filter &= Q(difficulty_level='beginner')
            elif profile.activity_level == 'moderate':
                workout_filter &= Q(difficulty_level__in=['beginner', 'intermediate'])
            else:
                workout_filter &= Q(difficulty_level__in=['intermediate', 'advanced'])
            
            # Filtro por objetivo
            if profile.goal == 'lose_weight':
                workout_filter &= Q(workout_type__in=['cardio', 'hiit', 'mixed'])
            elif profile.goal == 'gain_muscle':
                workout_filter &= Q(workout_type__in=['strength', 'bodybuilding', 'mixed'])
            elif profile.goal == 'improve_endurance':
                workout_filter &= Q(workout_type__in=['cardio', 'endurance', 'mixed'])
            
            # Buscar treinos que o usuário NÃO fez recentemente
            recent_workouts = WorkoutSession.objects.filter(
                user=user,
                created_at__gte=timezone.now() - timedelta(days=14)
            ).values_list('workout_id', flat=True)
            
            if recent_workouts:
                workout_filter &= ~Q(id__in=recent_workouts)
            
            # Buscar treinos
            workouts = Workout.objects.filter(workout_filter)[:limit * 2]  # Buscar mais para scoring
            
            # Calcular score para cada treino
            scored_workouts = []
            for workout in workouts:
                score = self._calculate_workout_score(user, workout, profile)
                if score > 0:
                    scored_workouts.append({
                        'workout': workout,
                        'score': score,
                        'reason': self._generate_recommendation_reason(workout, profile)
                    })
            
            # Ordenar por score e retornar top N
            scored_workouts.sort(key=lambda x: x['score'], reverse=True)
            
            for item in scored_workouts[:limit]:
                recommendations.append({
                    'workout_id': item['workout'].id,
                    'workout_name': item['workout'].name,
                    'confidence_score': min(item['score'] / 10.0, 1.0),  # Normalizar para 0-1
                    'reason': item['reason'],
                    'algorithm_used': 'content_based'
                })
            
            return recommendations
            
        except UserProfile.DoesNotExist:
            # Usuário sem perfil - recomendações genéricas para iniciantes
            beginner_workouts = Workout.objects.filter(difficulty_level='beginner')[:limit]
            return [{
                'workout_id': w.id,
                'workout_name': w.name,
                'confidence_score': 0.7,
                'reason': 'Recomendado para iniciantes',
                'algorithm_used': 'content_based'
            } for w in beginner_workouts]
    
    def _collaborative_filtering(self, user: User, limit: int) -> List[Dict]:
        """Filtro colaborativo: usuários similares fizeram estes treinos"""
        try:
            profile = UserProfile.objects.get(user=user)
            
            # Encontrar usuários similares
            similar_users = self._find_similar_users(user, profile)
            
            if not similar_users:
                # Fallback para content-based
                return self._content_based_recommendations(user, limit)
            
            # Treinos populares entre usuários similares
            popular_workouts = WorkoutSession.objects.filter(
                user__in=similar_users,
                completed=True,
                user_rating__gte=4  # Apenas treinos bem avaliados
            ).values('workout').annotate(
                popularity=Count('workout'),
                avg_rating=Avg('user_rating')
            ).order_by('-popularity', '-avg_rating')
            
            # Excluir treinos já feitos pelo usuário
            user_workouts = WorkoutSession.objects.filter(user=user).values_list('workout_id', flat=True)
            popular_workouts = popular_workouts.exclude(workout__in=user_workouts)
            
            recommendations = []
            for item in popular_workouts[:limit]:
                try:
                    workout = Workout.objects.get(id=item['workout'])
                    recommendations.append({
                        'workout_id': workout.id,
                        'workout_name': workout.name,
                        'confidence_score': min(item['popularity'] / 5.0, 1.0),  # Normalizar
                        'reason': f'Popular entre usuários com perfil similar (avaliação média: {item["avg_rating"]:.1f})',
                        'algorithm_used': 'collaborative'
                    })
                except Workout.DoesNotExist:
                    continue
            
            # Se não achou suficientes, completar com content-based
            if len(recommendations) < limit:
                content_recs = self._content_based_recommendations(user, limit - len(recommendations))
                recommendations.extend(content_recs)
            
            return recommendations[:limit]
            
        except UserProfile.DoesNotExist:
            return self._content_based_recommendations(user, limit)
    
    def _hybrid_recommendations(self, user: User, limit: int) -> List[Dict]:
        """Combina múltiplos algoritmos para melhores recomendações"""
        recommendations = []
        
        # 50% IA (se disponível) ou content-based
        ai_limit = max(1, limit // 2)
        if self.ai_service.is_available:
            ai_recs = self._ai_personalized_recommendations(user, ai_limit)
        else:
            ai_recs = self._content_based_recommendations(user, ai_limit)
        
        # 30% collaborative filtering
        collab_limit = max(1, int(limit * 0.3))
        collab_recs = self._collaborative_filtering(user, collab_limit)
        
        # 20% content-based (para diversidade)
        content_limit = limit - len(ai_recs) - len(collab_recs)
        if content_limit > 0:
            content_recs = self._content_based_recommendations(user, content_limit)
        else:
            content_recs = []
        
        # Combinar e remover duplicatas
        all_recs = ai_recs + collab_recs + content_recs
        seen_workouts = set()
        
        for rec in all_recs:
            if rec['workout_id'] not in seen_workouts:
                rec['algorithm_used'] = 'hybrid'
                recommendations.append(rec)
                seen_workouts.add(rec['workout_id'])
                
                if len(recommendations) >= limit:
                    break
        
        return recommendations
    
    def _calculate_workout_score(self, user: User, workout: Workout, profile: UserProfile) -> float:
        """Calcula score de relevância de um treino para o usuário"""
        score = 5.0  # Score base
        
        # Bonus por compatibilidade com objetivo
        if profile.goal == 'lose_weight' and workout.workout_type in ['cardio', 'hiit']:
            score += 3.0
        elif profile.goal == 'gain_muscle' and workout.workout_type in ['strength', 'bodybuilding']:
            score += 3.0
        elif profile.goal == 'improve_endurance' and workout.workout_type in ['cardio', 'endurance']:
            score += 3.0
        
        # Bonus por nível de dificuldade adequado
        if profile.activity_level in ['sedentary', 'light'] and workout.difficulty_level == 'beginner':
            score += 2.0
        elif profile.activity_level == 'moderate' and workout.difficulty_level == 'intermediate':
            score += 2.0
        elif profile.activity_level in ['active', 'very_active'] and workout.difficulty_level == 'advanced':
            score += 2.0
        
        # Penalidade se muito difícil para o nível
        if profile.activity_level in ['sedentary', 'light'] and workout.difficulty_level == 'advanced':
            score -= 3.0
        
        # Bonus por duração adequada (baseado no nível)
        if profile.activity_level in ['sedentary', 'light'] and workout.estimated_duration <= 30:
            score += 1.0
        elif profile.activity_level in ['active', 'very_active'] and workout.estimated_duration >= 45:
            score += 1.0
        
        # Bonus se é treino recomendado
        if workout.is_recommended:
            score += 1.5
        
        return max(0, score)
    
    def _find_similar_users(self, user: User, profile: UserProfile) -> List[int]:
        """Encontra usuários com perfil similar"""
        similar_users = UserProfile.objects.filter(
            goal=profile.goal,
            activity_level=profile.activity_level
        ).exclude(user=user)
        
        # Filtrar apenas usuários com atividade recente
        active_users = []
        for similar_profile in similar_users[:20]:  # Limite para performance
            recent_sessions = WorkoutSession.objects.filter(
                user=similar_profile.user,
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count()
            
            if recent_sessions >= 3:  # Usuários ativos
                active_users.append(similar_profile.user.id)
        
        return active_users[:10]  # Top 10 usuários similares
    
    def _generate_recommendation_reason(self, workout: Workout, profile: UserProfile) -> str:
        """Gera explicação para a recomendação"""
        reasons = []
        
        # Razão baseada no objetivo
        if profile.goal == 'lose_weight' and workout.workout_type in ['cardio', 'hiit']:
            reasons.append("ideal para queima de calorias")
        elif profile.goal == 'gain_muscle' and workout.workout_type in ['strength', 'bodybuilding']:
            reasons.append("perfeito para ganho de massa muscular")
        elif profile.goal == 'improve_endurance':
            reasons.append("excelente para melhorar resistência")
        
        # Razão baseada no nível
        if profile.activity_level in ['sedentary', 'light'] and workout.difficulty_level == 'beginner':
            reasons.append("adequado para seu nível atual")
        elif profile.activity_level in ['active', 'very_active'] and workout.difficulty_level == 'advanced':
            reasons.append("desafiador para seu nível")
        
        # Duração
        if workout.estimated_duration <= 30:
            reasons.append("treino rápido e eficiente")
        elif workout.estimated_duration >= 45:
            reasons.append("treino completo e intenso")
        
        return f"Recomendado: {', '.join(reasons) if reasons else 'treino balanceado para você'}"
    
    def _build_user_context(self, user: User) -> Dict:
        """Constrói contexto completo do usuário para IA"""
        try:
            # Sessões recentes
            recent_sessions = WorkoutSession.objects.filter(
                user=user,
                completed=True,
                completed_at__gte=timezone.now() - timedelta(days=30)
            )
            
            # Grupos musculares trabalhados
            exercise_logs = ExerciseLog.objects.filter(
                session__user=user,
                session__completed=True,
                completed=True
            )
            
            muscle_groups = {}
            for log in exercise_logs:
                group = log.workout_exercise.exercise.muscle_group
                muscle_groups[group] = muscle_groups.get(group, 0) + 1
            
            # Tipos de treino preferidos
            workout_types = {}
            for session in recent_sessions:
                wtype = session.workout.workout_type
                workout_types[wtype] = workout_types.get(wtype, 0) + 1
            
            return {
                'total_workouts': recent_sessions.count(),
                'avg_rating': recent_sessions.aggregate(Avg('user_rating'))['user_rating__avg'] or 0,
                'favorite_muscle_groups': sorted(muscle_groups.items(), key=lambda x: x[1], reverse=True)[:3],
                'favorite_workout_types': sorted(workout_types.items(), key=lambda x: x[1], reverse=True)[:2],
                'consistency_score': self._calculate_consistency_score(user),
                'improvement_trend': self._calculate_improvement_trend(user)
            }
        except Exception as e:
            logger.error(f"Error building user context: {e}")
            return {'total_workouts': 0}
    
    def _calculate_consistency_score(self, user: User) -> float:
        """Calcula score de consistência do usuário (0-1)"""
        try:
            # Últimas 4 semanas
            weeks_data = []
            for week in range(4):
                start_date = timezone.now() - timedelta(days=(week + 1) * 7)
                end_date = timezone.now() - timedelta(days=week * 7)
                
                week_sessions = WorkoutSession.objects.filter(
                    user=user,
                    completed=True,
                    completed_at__gte=start_date,
                    completed_at__lt=end_date
                ).count()
                
                weeks_data.append(week_sessions)
            
            # Score baseado na regularidade
            if not weeks_data or max(weeks_data) == 0:
                return 0.0
            
            # Penalizar semanas sem atividade
            weeks_with_activity = len([w for w in weeks_data if w > 0])
            consistency = weeks_with_activity / 4.0
            
            return min(consistency, 1.0)
            
        except Exception:
            return 0.5  # Score neutro em caso de erro
    
    def _calculate_improvement_trend(self, user: User) -> str:
        """Calcula tendência de melhoria do usuário"""
        try:
            # Comparar últimas 2 semanas com 2 semanas anteriores
            now = timezone.now()
            
            # Últimas 2 semanas
            recent_sessions = WorkoutSession.objects.filter(
                user=user,
                completed=True,
                completed_at__gte=now - timedelta(days=14)
            ).count()
            
            # 2 semanas anteriores
            previous_sessions = WorkoutSession.objects.filter(
                user=user,
                completed=True,
                completed_at__gte=now - timedelta(days=28),
                completed_at__lt=now - timedelta(days=14)
            ).count()
            
            if previous_sessions == 0:
                return 'iniciante'
            
            if recent_sessions > previous_sessions:
                return 'melhorando'
            elif recent_sessions == previous_sessions:
                return 'estável'
            else:
                return 'em declínio'
                
        except Exception:
            return 'estável'
    
    def _request_ai_recommendations(self, profile: UserProfile, context: Dict, 
                                  available_workouts: List[Dict], limit: int) -> Optional[List]:
        """Solicita recomendações personalizadas à IA"""
        # Este método seria implementado quando integrarmos com OpenAI
        # Por enquanto, retorna None para usar fallback
        return None
    
    def _process_ai_recommendations(self, ai_recs: List, workouts) -> List[Dict]:
        """Processa recomendações vindas da IA"""
        # Método para processar resposta da IA
        # Implementação futura quando integrarmos completamente com OpenAI
        return []
    
    def _save_recommendations(self, user: User, recommendations: List[Dict], algorithm: str):
        """Salva recomendações no banco de dados"""
        try:
            for rec in recommendations:
                workout_id = rec['workout_id']
                
                # Verificar se já existe recomendação recente para este treino
                existing = Recommendation.objects.filter(
                    usuario=user,
                    workout_recomendado_id=workout_id,
                    data_geracao__gte=timezone.now() - timedelta(days=1)
                ).exists()
                
                if not existing:
                    Recommendation.objects.create(
                        usuario=user,
                        workout_recomendado_id=workout_id,
                        algoritmo_utilizado=algorithm,
                        score_confianca=rec['confidence_score'],
                        motivo_recomendacao=rec['reason']
                    )
        except Exception as e:
            logger.error(f"Error saving recommendations: {e}")

    def get_user_recommendation_history(self, user: User, days: int = 30) -> List[Dict]:
        """Retorna histórico de recomendações do usuário"""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        recommendations = Recommendation.objects.filter(
            usuario=user,
            data_geracao__gte=cutoff_date
        ).select_related('workout_recomendado').order_by('-data_geracao')
        
        return [{
            'id': rec.id,
            'workout_name': rec.workout_recomendado.name,
            'algorithm': rec.algoritmo_utilizado,
            'confidence': rec.score_confianca,
            'reason': rec.motivo_recomendacao,
            'generated_at': rec.data_geracao,
            'accepted': rec.aceita_pelo_usuario,
            'accepted_at': rec.data_aceite
        } for rec in recommendations]
    
    def mark_recommendation_accepted(self, recommendation_id: int, user: User) -> bool:
        """Marca uma recomendação como aceita pelo usuário"""
        try:
            recommendation = Recommendation.objects.get(id=recommendation_id, usuario=user)
            recommendation.aceita_pelo_usuario = True
            recommendation.data_aceite = timezone.now()
            recommendation.save()
            return True
        except Recommendation.DoesNotExist:
            return False