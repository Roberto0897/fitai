import openai
import json
import logging
import time
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from typing import Dict, List, Optional, Tuple
from apps.users.models import UserProfile
from apps.exercises.models import Exercise
from apps.workouts.models import Workout, WorkoutSession, ExerciseLog

logger = logging.getLogger(__name__)


class AIService:
    """
    Serviço principal de integração com IA (OpenAI)
    Versão atualizada para OpenAI v1.12.0 com rate limiting e métricas
    """
    
    def __init__(self):
        self.client = None
        self.is_available = False
        self.rate_limit_cache_key = "openai_rate_limit"
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa cliente OpenAI com a nova API v1.12.0"""
        try:
            if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.strip() == '':
                logger.warning("OpenAI API key not configured or empty")
                return
                
            # Nova forma de inicializar cliente OpenAI v1.12.0
            self.client = openai.OpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=30.0  # 30 segundos de timeout
            )
            
            # Teste rápido de conectividade
            if self._test_api_connection():
                self.is_available = True
                logger.info("OpenAI client initialized and tested successfully")
            else:
                logger.error("OpenAI API test failed")
                
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.is_available = False
    
    def _test_api_connection(self) -> bool:
        """Testa conexão com a API OpenAI sem gastar tokens desnecessários"""
        try:
            if not self.client:
                return False
                
            # Fazer uma requisição simples para testar
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "user", "content": "Test"}
                ],
                max_tokens=1,
                temperature=0
            )
            return True
            
        except openai.AuthenticationError:
            logger.error("OpenAI API key is invalid")
            return False
        except openai.RateLimitError:
            logger.warning("OpenAI rate limit reached during test")
            return True  # API funciona, mas tem limite
        except Exception as e:
            logger.error(f"OpenAI API test failed: {e}")
            return False
    
    def _check_rate_limit(self) -> bool:
        """Verifica se ainda podemos fazer requisições (rate limiting)"""
        rate_limit_data = cache.get(self.rate_limit_cache_key, {"count": 0, "reset_time": time.time()})
        
        current_time = time.time()
        
        # Reset contador a cada hora
        if current_time - rate_limit_data["reset_time"] > 3600:
            rate_limit_data = {"count": 0, "reset_time": current_time}
        
        # Limite de 50 requisições por hora para ser conservador
        if rate_limit_data["count"] >= 50:
            logger.warning("OpenAI rate limit reached locally")
            return False
            
        return True
    
    def _update_rate_limit_counter(self):
        """Atualiza contador de rate limiting"""
        rate_limit_data = cache.get(self.rate_limit_cache_key, {"count": 0, "reset_time": time.time()})
        rate_limit_data["count"] += 1
        cache.set(self.rate_limit_cache_key, rate_limit_data, 3600)  # Cache por 1 hora
    
    def _make_openai_request(self, messages: List[Dict], max_tokens: int = None, 
                           temperature: float = None) -> Optional[str]:
        """Faz requisição segura para OpenAI com nova API v1.12.0"""
        if not self.is_available or not self.client:
            return None
        
        # Verificar rate limiting
        if not self._check_rate_limit():
            logger.warning("Skipping OpenAI request due to rate limiting")
            return None
            
        try:
            # Usar nova API do OpenAI v1.12.0
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                max_tokens=max_tokens or settings.OPENAI_MAX_TOKENS,
                temperature=temperature or settings.OPENAI_TEMPERATURE,
                timeout=30  # 30 segundos
            )
            
            # Atualizar contador de rate limit
            self._update_rate_limit_counter()
            
            # Extrair resposta
            content = response.choices[0].message.content
            
            # Log métricas
            self._log_api_metrics(response, len(messages))
            
            return content.strip() if content else None
            
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            # Marcar como indisponível temporariamente
            cache.set("openai_temp_disabled", True, 300)  # 5 minutos
            return None
            
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication failed: {e}")
            self.is_available = False
            return None
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI request: {e}")
            return None
    
    def _log_api_metrics(self, response, message_count: int):
        """Log métricas da API para monitoramento"""
        try:
            usage = response.usage
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "model": response.model,
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
                "message_count": message_count
            }
            
            # Armazenar métricas em cache para dashboard futuro
            daily_key = f"openai_metrics_{datetime.now().strftime('%Y-%m-%d')}"
            daily_metrics = cache.get(daily_key, [])
            daily_metrics.append(metrics)
            cache.set(daily_key, daily_metrics, 86400)  # 24 horas
            
            logger.info(f"OpenAI API used {usage.total_tokens if usage else 0} tokens")
            
        except Exception as e:
            logger.error(f"Error logging API metrics: {e}")
    
    def generate_personalized_workout_plan(self, user_profile: UserProfile, 
                                         duration: int, focus: str, difficulty: str) -> Optional[Dict]:
        """
        Gera plano de treino personalizado usando IA com prompts otimizados
        """
        if not self.is_available or cache.get("openai_temp_disabled"):
            return None
        
        # Buscar histórico do usuário para contexto
        user_history = self._get_user_context(user_profile.user)
        
        # Prompt otimizado e mais específico
        system_prompt = """Você é um personal trainer expert com 15 anos de experiência. 
Crie planos de treino seguros, eficazes e personalizados. 
Sempre responda em JSON válido estruturado. Priorize segurança e progressão adequada."""
        
        user_prompt = self._build_optimized_workout_prompt(
            user_profile, duration, focus, difficulty, user_history
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self._make_openai_request(messages, max_tokens=1000, temperature=0.7)
        
        if response:
            try:
                # Parsear e validar JSON
                workout_plan = json.loads(response)
                validated_plan = self._validate_and_enhance_workout_plan(workout_plan)
                
                if validated_plan:
                    # Adicionar metadados de geração
                    validated_plan["ai_metadata"] = {
                        "generated_at": datetime.now().isoformat(),
                        "model_used": settings.OPENAI_MODEL,
                        "personalization_factors": [
                            f"goal: {user_profile.goal}",
                            f"level: {user_profile.activity_level}",
                            f"focus: {focus}",
                            f"duration: {duration}min"
                        ]
                    }
                    
                return validated_plan
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI workout response as JSON: {e}")
                logger.error(f"Response was: {response[:200]}...")
        
        return None
    
    def _build_optimized_workout_prompt(self, profile: UserProfile, duration: int, 
                                      focus: str, difficulty: str, history: Dict) -> str:
        """Prompt otimizado para melhor qualidade das respostas"""
        return f"""
CRIAR PLANO DE TREINO PERSONALIZADO

PERFIL DO USUÁRIO:
- Nome: {profile.user.first_name or 'Usuário'}
- Objetivo Principal: {profile.goal or 'fitness geral'}
- Nível de Atividade: {profile.activity_level or 'iniciante'}
- Idade: {profile.age or 'não informado'}
- Histórico Recente: {history.get('recent_activity', 'iniciando jornada fitness')}

ESPECIFICAÇÕES DO TREINO:
- Duração Total: {duration} minutos
- Foco Principal: {focus}
- Nível de Dificuldade: {difficulty}

FORMATO DE RESPOSTA OBRIGATÓRIO (JSON):
{{
    "workout_name": "Nome motivador e específico",
    "description": "Descrição inspiradora do treino (máx 100 palavras)",
    "estimated_duration": {duration},
    "difficulty_level": "{difficulty}",
    "target_focus": "{focus}",
    "exercises": [
        {{
            "order": 1,
            "name": "Nome do exercício",
            "muscle_group": "grupo muscular principal",
            "sets": número_de_séries,
            "reps": "repetições ou tempo",
            "rest_seconds": segundos_de_descanso,
            "instructions": "instruções claras e seguras",
            "modifications": "adaptações para diferentes níveis",
            "safety_tips": "dicas importantes de segurança"
        }}
    ],
    "warm_up": {{
        "duration_minutes": 5,
        "exercises": ["exercício 1", "exercício 2", "exercício 3"],
        "instructions": "instruções detalhadas de aquecimento"
    }},
    "cool_down": {{
        "duration_minutes": 5,
        "exercises": ["alongamento 1", "alongamento 2", "alongamento 3"],
        "instructions": "instruções de relaxamento e alongamento"
    }},
    "ai_coaching_tips": [
        "dica técnica específica",
        "motivação personalizada", 
        "progressão sugerida"
    ]
}}

REQUISITOS OBRIGATÓRIOS:
1. Incluir 6-10 exercícios apropriados ao nível
2. Séries/repetições adequadas ao objetivo
3. Tempos de descanso otimizados
4. Instruções de segurança claras
5. Progressão lógica dos exercícios
6. Aquecimento e alongamento específicos

Gere um treino seguro, eficaz e motivador!
"""
    
    def _validate_and_enhance_workout_plan(self, plan: Dict) -> Optional[Dict]:
        """Validação robusta e melhorias no plano de treino"""
        try:
            # Validações obrigatórias
            required_fields = ['workout_name', 'exercises', 'estimated_duration']
            if not all(field in plan for field in required_fields):
                logger.error("Missing required fields in workout plan")
                return None
            
            # Validar exercícios
            if not isinstance(plan['exercises'], list) or len(plan['exercises']) < 3:
                logger.error("Invalid exercises list in workout plan")
                return None
            
            # Melhorar e sanitizar exercícios
            enhanced_exercises = []
            for i, exercise in enumerate(plan['exercises'], 1):
                enhanced_exercise = {
                    'order': i,
                    'name': exercise.get('name', f'Exercício {i}'),
                    'muscle_group': exercise.get('muscle_group', 'full_body'),
                    'sets': self._sanitize_sets(exercise.get('sets', 3)),
                    'reps': exercise.get('reps', '12-15'),
                    'rest_seconds': self._sanitize_rest(exercise.get('rest_seconds', 45)),
                    'instructions': exercise.get('instructions', 'Execute com boa forma'),
                    'modifications': exercise.get('modifications', 'Adapte conforme necessário'),
                    'safety_tips': exercise.get('safety_tips', 'Mantenha controle do movimento')
                }
                enhanced_exercises.append(enhanced_exercise)
            
            plan['exercises'] = enhanced_exercises
            
            # Adicionar defaults se necessário
            if 'warm_up' not in plan:
                plan['warm_up'] = {
                    'duration_minutes': 5,
                    'instructions': 'Movimentos leves para preparar o corpo'
                }
            
            if 'cool_down' not in plan:
                plan['cool_down'] = {
                    'duration_minutes': 5,
                    'instructions': 'Alongamentos para relaxar a musculatura'
                }
            
            # Adicionar score de qualidade
            plan['quality_score'] = self._calculate_workout_quality_score(plan)
            
            return plan
            
        except Exception as e:
            logger.error(f"Error validating workout plan: {e}")
            return None
    
    def _sanitize_sets(self, sets) -> int:
        """Sanitiza número de séries"""
        try:
            if isinstance(sets, str):
                # Extrair número da string
                import re
                numbers = re.findall(r'\d+', sets)
                if numbers:
                    sets = int(numbers[0])
                else:
                    sets = 3
            elif isinstance(sets, (int, float)):
                sets = int(sets)
            else:
                sets = 3
            
            # Limitar entre 1 e 6 séries
            return max(1, min(6, sets))
        except:
            return 3
    
    def _sanitize_rest(self, rest) -> int:
        """Sanitiza tempo de descanso"""
        try:
            if isinstance(rest, str):
                import re
                numbers = re.findall(r'\d+', rest)
                if numbers:
                    rest = int(numbers[0])
                else:
                    rest = 45
            elif isinstance(rest, (int, float)):
                rest = int(rest)
            else:
                rest = 45
            
            # Limitar entre 15 e 180 segundos
            return max(15, min(180, rest))
        except:
            return 45
    
    def _calculate_workout_quality_score(self, plan: Dict) -> float:
        """Calcula score de qualidade do treino gerado (0-100)"""
        score = 0
        
        # Número adequado de exercícios (20 pontos)
        exercise_count = len(plan.get('exercises', []))
        if 6 <= exercise_count <= 10:
            score += 20
        elif 4 <= exercise_count <= 12:
            score += 15
        else:
            score += 5
        
        # Presença de aquecimento e alongamento (20 pontos)
        if plan.get('warm_up'):
            score += 10
        if plan.get('cool_down'):
            score += 10
        
        # Qualidade das instruções (20 pontos)
        instruction_quality = sum([
            1 for ex in plan.get('exercises', [])
            if len(ex.get('instructions', '')) > 20
        ])
        score += min(20, instruction_quality * 2)
        
        # Variedade de grupos musculares (20 pontos)
        muscle_groups = set([
            ex.get('muscle_group', '') 
            for ex in plan.get('exercises', [])
        ])
        score += min(20, len(muscle_groups) * 4)
        
        # Presença de dicas de segurança (20 pontos)
        safety_tips = sum([
            1 for ex in plan.get('exercises', [])
            if ex.get('safety_tips') and len(ex.get('safety_tips', '')) > 10
        ])
        score += min(20, safety_tips * 2)
        
        return round(score, 1)
    
    def analyze_user_progress(self, user_profile: UserProfile) -> Optional[Dict]:
        """
        Análise de progresso com prompts otimizados e validação robusta
        """
        if not self.is_available or cache.get("openai_temp_disabled"):
            return None
        
        # Coletar dados detalhados
        user_data = self._collect_detailed_user_progress(user_profile.user)
        
        if not user_data['has_sufficient_data']:
            return None
        
        # Prompt otimizado para análise
        system_prompt = """Você é um especialista em análise de performance e fisiologia do exercício. 
Analise os dados fornecidos e gere insights precisos e acionáveis em formato JSON estruturado."""
        
        user_prompt = self._build_progress_analysis_prompt(user_profile, user_data)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self._make_openai_request(messages, max_tokens=800, temperature=0.6)
        
        if response:
            try:
                analysis = json.loads(response)
                # Validar e enriquecer análise
                return self._enhance_progress_analysis(analysis, user_data)
            except json.JSONDecodeError:
                logger.error("Failed to parse OpenAI progress analysis as JSON")
        
        return None
    
    def _collect_detailed_user_progress(self, user) -> Dict:
        """Coleta dados mais detalhados para análise"""
        try:
            from datetime import timedelta
            from django.utils import timezone
            from django.db.models import Avg, Count, Sum
            
            # Diferentes períodos de análise
            now = timezone.now()
            periods = {
                'week': now - timedelta(days=7),
                'month': now - timedelta(days=30),
                'quarter': now - timedelta(days=90)
            }
            
            data = {'has_sufficient_data': False}
            
            for period_name, start_date in periods.items():
                sessions = WorkoutSession.objects.filter(
                    user=user, 
                    created_at__gte=start_date
                )
                
                completed_sessions = sessions.filter(completed=True)
                total_sessions = sessions.count()
                
                if total_sessions >= (3 if period_name == 'week' else 5):
                    data['has_sufficient_data'] = True
                
                # Estatísticas detalhadas
                data[f'{period_name}_stats'] = {
                    'total_sessions': total_sessions,
                    'completed_sessions': completed_sessions.count(),
                    'completion_rate': round(
                        completed_sessions.count() / total_sessions * 100, 1
                    ) if total_sessions > 0 else 0,
                    'avg_duration': completed_sessions.aggregate(
                        Avg('actual_duration')
                    )['actual_duration__avg'] or 0,
                    'avg_rating': completed_sessions.aggregate(
                        Avg('user_rating')
                    )['user_rating__avg'] or 0
                }
                
                # Análise de exercícios
                exercise_logs = ExerciseLog.objects.filter(
                    session__in=completed_sessions,
                    completed=True
                )
                
                muscle_group_distribution = {}
                for log in exercise_logs:
                    group = log.workout_exercise.exercise.muscle_group
                    muscle_group_distribution[group] = muscle_group_distribution.get(group, 0) + 1
                
                data[f'{period_name}_muscle_groups'] = muscle_group_distribution
            
            # Tendências e padrões
            data['trends'] = self._calculate_user_trends(user)
            
            return data
            
        except Exception as e:
            logger.error(f"Error collecting detailed progress data: {e}")
            return {'has_sufficient_data': False}
    
    def _calculate_user_trends(self, user) -> Dict:
        """Calcula tendências do usuário"""
        try:
            from datetime import timedelta
            from django.utils import timezone
            
            # Últimas 4 semanas para análise de tendência
            weeks_data = []
            for week in range(4):
                start_date = timezone.now() - timedelta(days=(week + 1) * 7)
                end_date = timezone.now() - timedelta(days=week * 7)
                
                week_sessions = WorkoutSession.objects.filter(
                    user=user,
                    completed=True,
                    completed_at__range=(start_date, end_date)
                ).count()
                
                weeks_data.append(week_sessions)
            
            # Calcular tendência
            if len(weeks_data) >= 3:
                recent_avg = sum(weeks_data[:2]) / 2
                older_avg = sum(weeks_data[2:]) / 2
                
                if recent_avg > older_avg * 1.2:
                    trend = 'crescente'
                elif recent_avg < older_avg * 0.8:
                    trend = 'decrescente'
                else:
                    trend = 'estável'
            else:
                trend = 'insuficiente'
            
            return {
                'weekly_frequency': weeks_data,
                'trend': trend,
                'consistency_score': min(weeks_data) / max(weeks_data) if max(weeks_data) > 0 else 0
            }
            
        except Exception:
            return {'trend': 'indeterminado'}
    
    def _enhance_progress_analysis(self, analysis: Dict, user_data: Dict) -> Dict:
        """Enriquece análise com dados calculados"""
        try:
            # Adicionar metadados
            analysis['analysis_metadata'] = {
                'generated_at': datetime.now().isoformat(),
                'data_period': 'last_30_days',
                'ai_model': settings.OPENAI_MODEL,
                'confidence_level': 'high' if user_data['has_sufficient_data'] else 'medium'
            }
            
            # Adicionar métricas calculadas
            analysis['calculated_metrics'] = {
                'consistency_score': user_data.get('trends', {}).get('consistency_score', 0),
                'improvement_trend': user_data.get('trends', {}).get('trend', 'indeterminado'),
                'total_workouts_month': user_data.get('month_stats', {}).get('completed_sessions', 0)
            }
            
            # Score geral de progresso
            analysis['overall_progress_score'] = self._calculate_overall_progress_score(user_data)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error enhancing progress analysis: {e}")
            return analysis
    
    def _calculate_overall_progress_score(self, user_data: Dict) -> float:
        """Calcula score geral de progresso (0-100)"""
        try:
            score = 0
            month_stats = user_data.get('month_stats', {})
            
            # Frequência (40 pontos)
            completed_sessions = month_stats.get('completed_sessions', 0)
            if completed_sessions >= 16:  # 4+ por semana
                score += 40
            elif completed_sessions >= 12:  # 3 por semana
                score += 30
            elif completed_sessions >= 8:  # 2 por semana
                score += 20
            elif completed_sessions >= 4:  # 1 por semana
                score += 10
            
            # Taxa de conclusão (30 pontos)
            completion_rate = month_stats.get('completion_rate', 0)
            score += min(30, completion_rate * 0.3)
            
            # Satisfação (20 pontos)
            avg_rating = month_stats.get('avg_rating', 0)
            score += min(20, avg_rating * 4)
            
            # Consistência (10 pontos)
            consistency = user_data.get('trends', {}).get('consistency_score', 0)
            score += consistency * 10
            
            return round(score, 1)
            
        except Exception:
            return 50.0
    
    def generate_motivational_content(self, user_profile: UserProfile, context: str) -> Optional[str]:
        """
        Gera conteúdo motivacional com prompts otimizados
        """
        if not self.is_available or cache.get("openai_temp_disabled"):
            return None
        
        user_context = self._get_user_context(user_profile.user)
        
        # Prompt otimizado para motivação
        system_prompt = """Você é um coach motivacional especialista em fitness e bem-estar. 
Crie mensagens inspiradoras, personalizadas e genuínas. Evite clichês e seja autêntico."""
        
        user_prompt = f"""
Crie uma mensagem motivacional personalizada para {user_profile.user.first_name or 'o usuário'}.

CONTEXTO: {context}
OBJETIVO PRINCIPAL: {user_profile.goal or 'manter a forma'}
NÍVEL ATUAL: {user_profile.activity_level or 'iniciante'}
PROGRESSO RECENTE: {user_context.get('recent_activity', 'começando a jornada')}
IDADE: {user_profile.age or 'não informada'}

REQUISITOS:
- Máximo 80 palavras
- Tom encorajador mas não excessivo
- Mencione o objetivo específico
- Seja inspirador e realista
- Use o nome da pessoa se disponível
- Evite frases clichês como "você consegue!"

CONTEXTOS ESPECÍFICOS:
- workout_start: Motivação para começar o treino
- workout_complete: Parabenizar conclusão
- weekly_review: Reflexão semanal
- goal_reminder: Lembrar do objetivo
- comeback: Retorno após pausa
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self._make_openai_request(messages, max_tokens=120, temperature=0.8)
        
        if response:
            # Limpar e validar resposta
            cleaned_message = response.strip().replace('"', '').replace('\n', ' ')
            if len(cleaned_message) > 200:
                cleaned_message = cleaned_message[:200] + "..."
            
            return cleaned_message
        
        return None
    
    def get_api_usage_stats(self) -> Dict:
        """Retorna estatísticas de uso da API para monitoramento"""
        try:
            today_key = f"openai_metrics_{datetime.now().strftime('%Y-%m-%d')}"
            today_metrics = cache.get(today_key, [])
            
            if not today_metrics:
                return {"usage_today": 0, "tokens_used": 0, "requests_made": 0}
            
            total_tokens = sum([m.get('total_tokens', 0) for m in today_metrics])
            total_requests = len(today_metrics)
            
            # Verificar rate limit
            rate_limit_data = cache.get(self.rate_limit_cache_key, {"count": 0})
            
            return {
                "api_available": self.is_available,
                "usage_today": {
                    "requests_made": total_requests,
                    "tokens_used": total_tokens,
                    "rate_limit_remaining": max(0, 50 - rate_limit_data.get("count", 0))
                },
                "last_test": self._test_api_connection()
            }
            
        except Exception as e:
            logger.error(f"Error getting API usage stats: {e}")
            return {"error": "Unable to fetch stats"}
    
    def _get_user_context(self, user) -> Dict:
        """Versão otimizada de coleta de contexto do usuário"""
        try:
            # Cache por 1 hora para evitar queries desnecessárias
            cache_key = f"user_context_{user.id}"
            cached_context = cache.get(cache_key)
            if cached_context:
                return cached_context
            
            # Últimas 10 sessões
            recent_sessions = WorkoutSession.objects.filter(
                user=user, completed=True
            ).order_by('-completed_at')[:10]
            
            # Exercícios mais realizados
            from django.db.models import Count
            exercise_logs = ExerciseLog.objects.filter(
                session__user=user,
                session__completed=True,
                completed=True
            ).values('workout_exercise__exercise__muscle_group').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            context = {
                'total_workouts': recent_sessions.count(),
                'recent_activity': f"Completou {recent_sessions.count()} treinos recentes",
                'favorite_muscle_groups': [eg['workout_exercise__exercise__muscle_group'] for eg in exercise_logs],
                'last_workout': recent_sessions.first().completed_at.strftime('%d/%m') if recent_sessions.exists() else 'nunca',
                'has_recent_data': recent_sessions.exists(),
                'activity_level': 'ativo' if recent_sessions.count() >= 5 else 'moderado' if recent_sessions.count() >= 2 else 'iniciante'
            }
            
            # Cache por 1 hora
            cache.set(cache_key, context, 3600)
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return {'has_recent_data': False, 'recent_activity': 'dados indisponíveis'}

    def _build_progress_analysis_prompt(self, profile: UserProfile, data: Dict) -> str:
        """Prompt otimizado para análise de progresso"""
        month_stats = data.get('month_stats', {})
        week_stats = data.get('week_stats', {})
        trends = data.get('trends', {})
        
        return f"""
ANALISAR PROGRESSO FITNESS DO USUÁRIO

PERFIL:
- Objetivo: {profile.goal or 'fitness geral'}
- Nível: {profile.activity_level or 'iniciante'}
- Idade: {profile.age or 'não informada'}

DADOS ÚLTIMO MÊS:
- Total de treinos: {month_stats.get('completed_sessions', 0)}
- Taxa de conclusão: {month_stats.get('completion_rate', 0)}%
- Duração média: {month_stats.get('avg_duration', 0):.1f} min
- Avaliação média: {month_stats.get('avg_rating', 0):.1f}/5

DADOS ÚLTIMA SEMANA:
- Treinos esta semana: {week_stats.get('completed_sessions', 0)}
- Taxa de conclusão: {week_stats.get('completion_rate', 0)}%

TENDÊNCIAS:
- Padrão: {trends.get('trend', 'estável')}
- Consistência: {trends.get('consistency_score', 0):.1f}

GRUPOS MUSCULARES TRABALHADOS:
{', '.join(data.get('month_muscle_groups', {}).keys()) or 'dados insuficientes'}

FORMATO DE RESPOSTA (JSON):
{{
    "overall_progress": "excelente|muito_bom|bom|médio|precisa_melhorar",
    "progress_summary": "análise objetiva em 1-2 frases",
    "strengths": [
        "ponto forte específico 1",
        "ponto forte específico 2"
    ],
    "areas_for_improvement": [
        "área específica 1 com sugestão",
        "área específica 2 com sugestão"
    ],
    "next_week_focus": "recomendação específica e acionável",
    "motivation_message": "mensagem encorajadora personalizada (máx 60 palavras)",
    "specific_recommendations": [
        "ação específica 1",
        "ação específica 2",
        "ação específica 3"
    ],
    "goal_alignment": "como está progredindo em relação ao objetivo"
}}

Seja específico, honesto e construtivo. Baseie-se apenas nos dados fornecidos.
"""