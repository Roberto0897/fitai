import google.generativeai as genai
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
    Serviço principal de integração com IA (Google Gemini)
    Migrado de OpenAI para Gemini - mantém compatibilidade com código existente
    """
    
    def __init__(self):
        self.model = None
        self.is_available = False
        self.rate_limit_cache_key = "gemini_rate_limit"
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa cliente Gemini"""
        try:
            if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == '':
                logger.warning("Gemini API key not configured or empty")
                return
            
            # Configurar Gemini
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Inicializar modelo
            self.model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                generation_config={
                    'temperature': settings.GEMINI_TEMPERATURE,
                    'max_output_tokens': settings.GEMINI_MAX_TOKENS,
                }
            )
            
            # Teste rápido de conectividade
            if self._test_api_connection():
                self.is_available = True
                logger.info(f"Gemini client initialized successfully with model {settings.GEMINI_MODEL}")
            else:
                logger.error("Gemini API test failed")
                
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.is_available = False
    
    def _test_api_connection(self) -> bool:
        """Testa conexão com a API Gemini"""
        try:
            if not self.model:
                return False
            
            # Fazer uma requisição simples para testar
            response = self.model.generate_content("Test")
            return bool(response.text)
            
        except Exception as e:
            logger.error(f"Gemini API test failed: {e}")
            return False
    
    def _check_rate_limit(self) -> bool:
        """Verifica rate limiting (Gemini tem limites mais generosos)"""
        rate_limit_data = cache.get(self.rate_limit_cache_key, {"count": 0, "reset_time": time.time()})
        
        current_time = time.time()
        
        # Reset contador a cada minuto para Gemini
        if current_time - rate_limit_data["reset_time"] > 60:
            rate_limit_data = {"count": 0, "reset_time": current_time}
        
        # Limite do Gemini: 15 requisições por minuto no free tier
        if rate_limit_data["count"] >= settings.GEMINI_RATE_LIMIT_PER_MINUTE:
            logger.warning("Gemini rate limit reached locally")
            return False
            
        return True
    
    def _update_rate_limit_counter(self):
        """Atualiza contador de rate limiting"""
        rate_limit_data = cache.get(self.rate_limit_cache_key, {"count": 0, "reset_time": time.time()})
        rate_limit_data["count"] += 1
        cache.set(self.rate_limit_cache_key, rate_limit_data, 60)  # Cache por 1 minuto
    
    def _make_gemini_request(self, prompt: str) -> Optional[str]:
        """Faz requisição segura para Gemini"""
        if not self.is_available or not self.model:
            return None
        
        # Verificar rate limiting
        if not self._check_rate_limit():
            logger.warning("Skipping Gemini request due to rate limiting")
            return None
            
        try:
            # Fazer requisição
            response = self.model.generate_content(prompt)
            
            # Atualizar contador de rate limit
            self._update_rate_limit_counter()
            
            # Extrair resposta
            content = response.text
            
            # Log métricas
            self._log_api_metrics(response, len(prompt))
            
            return content.strip() if content else None
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            if "quota" in str(e).lower() or "rate" in str(e).lower():
                # Marcar como indisponível temporariamente
                cache.set("gemini_temp_disabled", True, 60)  # 1 minuto
            return None
    
    def _log_api_metrics(self, response, prompt_length: int):
        """Log métricas da API para monitoramento"""
        try:
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "model": settings.GEMINI_MODEL,
                "prompt_chars": prompt_length,
                "response_chars": len(response.text) if response.text else 0,
            }
            
            # Armazenar métricas em cache
            daily_key = f"gemini_metrics_{datetime.now().strftime('%Y-%m-%d')}"
            daily_metrics = cache.get(daily_key, [])
            daily_metrics.append(metrics)
            cache.set(daily_key, daily_metrics, 86400)  # 24 horas
            
            logger.info(f"Gemini API used {metrics['response_chars']} chars in response")
            
        except Exception as e:
            logger.error(f"Error logging API metrics: {e}")
    
    def generate_personalized_workout_plan(self, user_profile: UserProfile, 
                                         duration: int, focus: str, difficulty: str) -> Optional[Dict]:
        """
        Gera plano de treino personalizado usando Gemini
        """
        if not self.is_available or cache.get("gemini_temp_disabled"):
            return None
        
        # Buscar histórico do usuário para contexto
        user_history = self._get_user_context(user_profile.user)
        
        # Prompt otimizado para Gemini
        prompt = self._build_optimized_workout_prompt(
            user_profile, duration, focus, difficulty, user_history
        )
        
        response = self._make_gemini_request(prompt)
        
        if response:
            try:
                # Gemini às vezes retorna com markdown, limpar
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.endswith('```'):
                    response = response[:-3]
                response = response.strip()
                
                # Parsear e validar JSON
                workout_plan = json.loads(response)
                validated_plan = self._validate_and_enhance_workout_plan(workout_plan)
                
                if validated_plan:
                    # Adicionar metadados de geração
                    validated_plan["ai_metadata"] = {
                        "generated_at": datetime.now().isoformat(),
                        "model_used": settings.GEMINI_MODEL,
                        "personalization_factors": [
                            f"goal: {user_profile.goal}",
                            f"level: {user_profile.activity_level}",
                            f"focus: {focus}",
                            f"duration: {duration}min"
                        ]
                    }
                    
                return validated_plan
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini workout response as JSON: {e}")
                logger.error(f"Response was: {response[:200]}...")
        
        return None
    
    def _build_optimized_workout_prompt(self, profile: UserProfile, duration: int, 
                                      focus: str, difficulty: str, history: Dict) -> str:
        """Prompt otimizado para Gemini"""
        return f"""Você é um personal trainer expert. Crie um plano de treino personalizado.

PERFIL DO USUÁRIO:
- Nome: {profile.user.first_name or 'Usuário'}
- Objetivo: {profile.goal or 'fitness geral'}
- Nível: {profile.activity_level or 'iniciante'}
- Idade: {profile.age or 'não informado'}
- Histórico: {history.get('recent_activity', 'iniciando')}

ESPECIFICAÇÕES:
- Duração: {duration} minutos
- Foco: {focus}
- Dificuldade: {difficulty}

RESPONDA APENAS COM JSON VÁLIDO (sem markdown):
{{
    "workout_name": "Nome motivador",
    "description": "Descrição inspiradora (máx 100 palavras)",
    "estimated_duration": {duration},
    "difficulty_level": "{difficulty}",
    "target_focus": "{focus}",
    "exercises": [
        {{
            "order": 1,
            "name": "Nome do exercício",
            "muscle_group": "grupo muscular",
            "sets": 3,
            "reps": "12-15",
            "rest_seconds": 45,
            "instructions": "instruções claras",
            "modifications": "adaptações",
            "safety_tips": "dicas de segurança"
        }}
    ],
    "warm_up": {{
        "duration_minutes": 5,
        "exercises": ["exercício 1", "exercício 2"],
        "instructions": "instruções de aquecimento"
    }},
    "cool_down": {{
        "duration_minutes": 5,
        "exercises": ["alongamento 1", "alongamento 2"],
        "instructions": "instruções de relaxamento"
    }},
    "ai_coaching_tips": [
        "dica técnica",
        "motivação personalizada"
    ]
}}

IMPORTANTE: 
- Incluir 6-10 exercícios apropriados
- Instruções de segurança claras
- Progressão lógica dos exercícios
- Responda APENAS com o JSON, sem texto adicional"""
    
    def _validate_and_enhance_workout_plan(self, plan: Dict) -> Optional[Dict]:
        """Validação robusta do plano de treino"""
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
            
            # Melhorar exercícios
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
            
            return max(15, min(180, rest))
        except:
            return 45
    
    def _calculate_workout_quality_score(self, plan: Dict) -> float:
        """Calcula score de qualidade do treino (0-100)"""
        score = 0
        
        exercise_count = len(plan.get('exercises', []))
        if 6 <= exercise_count <= 10:
            score += 20
        elif 4 <= exercise_count <= 12:
            score += 15
        else:
            score += 5
        
        if plan.get('warm_up'):
            score += 10
        if plan.get('cool_down'):
            score += 10
        
        instruction_quality = sum([
            1 for ex in plan.get('exercises', [])
            if len(ex.get('instructions', '')) > 20
        ])
        score += min(20, instruction_quality * 2)
        
        muscle_groups = set([
            ex.get('muscle_group', '') 
            for ex in plan.get('exercises', [])
        ])
        score += min(20, len(muscle_groups) * 4)
        
        safety_tips = sum([
            1 for ex in plan.get('exercises', [])
            if ex.get('safety_tips') and len(ex.get('safety_tips', '')) > 10
        ])
        score += min(20, safety_tips * 2)
        
        return round(score, 1)
    
    def analyze_user_progress(self, user_profile: UserProfile) -> Optional[Dict]:
        """Análise de progresso com Gemini"""
        if not self.is_available or cache.get("gemini_temp_disabled"):
            return None
        
        # Coletar dados detalhados
        user_data = self._collect_detailed_user_progress(user_profile.user)
        
        if not user_data['has_sufficient_data']:
            return None
        
        # Prompt para análise
        prompt = self._build_progress_analysis_prompt(user_profile, user_data)
        
        response = self._make_gemini_request(prompt)
        
        if response:
            try:
                # Limpar markdown
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.endswith('```'):
                    response = response[:-3]
                response = response.strip()
                
                analysis = json.loads(response)
                return self._enhance_progress_analysis(analysis, user_data)
            except json.JSONDecodeError:
                logger.error("Failed to parse Gemini progress analysis as JSON")
        
        return None
    
    def _collect_detailed_user_progress(self, user) -> Dict:
        """Coleta dados detalhados para análise"""
        try:
            from datetime import timedelta
            from django.utils import timezone
            from django.db.models import Avg, Count, Sum
            
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
            analysis['analysis_metadata'] = {
                'generated_at': datetime.now().isoformat(),
                'data_period': 'last_30_days',
                'ai_model': settings.GEMINI_MODEL,
                'confidence_level': 'high' if user_data['has_sufficient_data'] else 'medium'
            }
            
            analysis['calculated_metrics'] = {
                'consistency_score': user_data.get('trends', {}).get('consistency_score', 0),
                'improvement_trend': user_data.get('trends', {}).get('trend', 'indeterminado'),
                'total_workouts_month': user_data.get('month_stats', {}).get('completed_sessions', 0)
            }
            
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
            
            completed_sessions = month_stats.get('completed_sessions', 0)
            if completed_sessions >= 16:
                score += 40
            elif completed_sessions >= 12:
                score += 30
            elif completed_sessions >= 8:
                score += 20
            elif completed_sessions >= 4:
                score += 10
            
            completion_rate = month_stats.get('completion_rate', 0)
            score += min(30, completion_rate * 0.3)
            
            avg_rating = month_stats.get('avg_rating', 0)
            score += min(20, avg_rating * 4)
            
            consistency = user_data.get('trends', {}).get('consistency_score', 0)
            score += consistency * 10
            
            return round(score, 1)
            
        except Exception:
            return 50.0
    
    def generate_motivational_content(self, user_profile: UserProfile, context: str) -> Optional[str]:
        """Gera conteúdo motivacional com Gemini"""
        if not self.is_available or cache.get("gemini_temp_disabled"):
            return None
        
        user_context = self._get_user_context(user_profile.user)
        
        # Prompt otimizado para motivação
        prompt = f"""Você é um coach motivacional especialista em fitness. Crie uma mensagem inspiradora e personalizada.

CONTEXTO: {context}
OBJETIVO: {user_profile.goal or 'manter a forma'}
NÍVEL: {user_profile.activity_level or 'iniciante'}
PROGRESSO: {user_context.get('recent_activity', 'começando')}
NOME: {user_profile.user.first_name or 'Atleta'}

REQUISITOS:
- Máximo 80 palavras
- Tom encorajador mas não excessivo
- Mencione o objetivo específico
- Seja inspirador e realista
- Use o nome da pessoa
- Evite frases clichês

Responda APENAS com a mensagem motivacional, sem aspas ou formatação adicional."""
        
        response = self._make_gemini_request(prompt)
        
        if response:
            cleaned_message = response.strip().replace('"', '').replace('\n', ' ')
            if len(cleaned_message) > 200:
                cleaned_message = cleaned_message[:200] + "..."
            
            return cleaned_message
        
        return None
    
    def get_api_usage_stats(self) -> Dict:
        """Retorna estatísticas de uso da API"""
        try:
            today_key = f"gemini_metrics_{datetime.now().strftime('%Y-%m-%d')}"
            today_metrics = cache.get(today_key, [])
            
            if not today_metrics:
                return {"usage_today": 0, "requests_made": 0}
            
            total_requests = len(today_metrics)
            
            rate_limit_data = cache.get(self.rate_limit_cache_key, {"count": 0})
            
            return {
                "api_available": self.is_available,
                "usage_today": {
                    "requests_made": total_requests,
                    "rate_limit_remaining": max(0, settings.GEMINI_RATE_LIMIT_PER_MINUTE - rate_limit_data.get("count", 0))
                },
                "last_test": self._test_api_connection()
            }
            
        except Exception as e:
            logger.error(f"Error getting API usage stats: {e}")
            return {"error": "Unable to fetch stats"}
    
    def _get_user_context(self, user) -> Dict:
        """Coleta contexto do usuário com cache"""
        try:
            cache_key = f"user_context_{user.id}"
            cached_context = cache.get(cache_key)
            if cached_context:
                return cached_context
            
            recent_sessions = WorkoutSession.objects.filter(
                user=user, completed=True
            ).order_by('-completed_at')[:10]
            
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
        
        return f"""Você é um especialista em análise de performance fitness. Analise os dados e forneça insights precisos.

PERFIL:
- Objetivo: {profile.goal or 'fitness geral'}
- Nível: {profile.activity_level or 'iniciante'}
- Idade: {profile.age or 'não informada'}

DADOS ÚLTIMO MÊS:
- Total de treinos: {month_stats.get('completed_sessions', 0)}
- Taxa de conclusão: {month_stats.get('completion_rate', 0)}%
- Duração média: {month_stats.get('avg_duration', 0):.1f} min
- Avaliação média: {month_stats.get('avg_rating', 0):.1f}/5

ÚLTIMA SEMANA:
- Treinos: {week_stats.get('completed_sessions', 0)}
- Taxa de conclusão: {week_stats.get('completion_rate', 0)}%

TENDÊNCIAS:
- Padrão: {trends.get('trend', 'estável')}
- Consistência: {trends.get('consistency_score', 0):.1f}

RESPONDA APENAS COM JSON VÁLIDO (sem markdown):
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

Seja específico, honesto e construtivo baseado nos dados fornecidos."""