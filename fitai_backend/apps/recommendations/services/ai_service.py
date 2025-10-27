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
                        "created_at": datetime.now().isoformat(),
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
    

    def generate_daily_recommendation(self, user_profile: UserProfile, 
                        workout_history: List[Dict] = None) -> Optional[Dict]:
        """
        🔥 AJUSTADO: Verifica treino recomendado ANTES de gerar novo
        Evita recomendações conflitantes
        """
        
        # ✅ ADICIONAR ESTAS 4 LINHAS NO INÍCIO:
        cache_key = f"daily_rec_{user_profile.user.id}_{datetime.now().date()}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        # ✅ FIM DA ADIÇÃO
        
        # Verifica se há treino recomendado recente (últimas 24h)
        from django.utils import timezone
        from datetime import timedelta
        from apps.workouts.models import Workout
        
        recent_recommended = Workout.objects.filter(
            created_by_user=user_profile.user,
            is_recommended=True,
            is_personalized=True,
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-created_at').first()
        
        if recent_recommended:
            logger.info(f"✅ Usando treino recomendado existente: {recent_recommended.name}")
            
            # Extrair foco do treino
            focus = self._extract_focus_from_workout(recent_recommended)
            
            # Determinar intensidade
            intensity_map = {
                'beginner': 'moderate',
                'intermediate': 'moderate',
                'advanced': 'high'
            }
            intensity = intensity_map.get(recent_recommended.difficulty_level, 'moderate')
            
            # 🔥 CORRIGIDO: Calcular exercise_count dinamicamente
            exercise_count = recent_recommended.workout_exercises.count()
            
            # ✅ CRIAR VARIÁVEL result:
            result = {
                'recommendation_type': 'workout',
                'title': f'Seu Treino: {recent_recommended.name}',
                'message': f'{user_profile.user.first_name or "Você"}, treino personalizado pronto!',
                'focus_area': focus,
                'reasoning': 'Treino gerado pela IA especialmente para você hoje',
                'intensity': intensity,
                'suggested_duration': recent_recommended.estimated_duration or 30,
                'motivational_tip': self._generate_workout_tip(recent_recommended, user_profile),
                'emoji': '🎯',
                'workout_id': recent_recommended.id,
                'workout_name': recent_recommended.name,
                'respects_limitations': True,
                'aligns_with_schedule': True,
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'model': 'workout_recommendation',
                    'confidence': 1.0,
                    'personalization_factors': [
                        f'workout: {recent_recommended.name}',
                        f'created: {recent_recommended.created_at.strftime("%d/%m %H:%M")}',
                        f'exercises: {exercise_count}',
                        f'duration: {recent_recommended.estimated_duration or 30}min'
                    ]
                }
            }
            
            # ✅ ADICIONAR ESTAS 2 LINHAS:
            cache.set(cache_key, result, 3600)  # Cache por 1 hora
            return result
            # ✅ FIM DA ADIÇÃO (remova o return que estava antes)
        
        # 🤖 PASSO 2: Se não há treino recomendado, gerar nova recomendação
        
        if not self.is_available or cache.get("gemini_temp_disabled"):
            logger.info("IA indisponível, usando fallback baseado em regras")
            # ✅ MODIFICAR ESTA LINHA:
            fallback = self._generate_rule_based_recommendation(user_profile, workout_history)
            cache.set(cache_key, fallback, 3600)
            return fallback
        
        try:
            # Coletar contexto do usuário
            user_context = self._get_user_context(user_profile.user)
            
            # Analisar histórico recente
            history_analysis = self._analyze_recent_workout_history(user_profile.user, workout_history)
            
            # Análise de preferências
            preferences_analysis = self._analyze_user_preferences(user_profile)
            
            # Verificar restrições físicas
            physical_constraints = self._check_physical_constraints(user_profile, history_analysis)
            
            # Construir prompt
            prompt = self._build_daily_recommendation_prompt_simple(
                user_profile, 
                user_context, 
                history_analysis
            )
            
            response = self._make_gemini_request(prompt)
            
            if response:
                # Limpar markdown
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.endswith('```'):
                    response = response[:-3]
                response = response.strip()
                
                recommendation = json.loads(response)
                
                # Validar e enriquecer recomendação
                validated_recommendation = self._validate_daily_recommendation(recommendation)
                
                if validated_recommendation:
                    validated_recommendation['metadata'] = {
                        'created_at': datetime.now().isoformat(),
                        'model': settings.GEMINI_MODEL,
                        'confidence': self._calculate_recommendation_confidence(history_analysis),
                        'personalization_factors': self._build_personalization_factors(
                            user_profile,
                            history_analysis,
                            preferences_analysis,
                            physical_constraints
                        )
                    }
                    
                    # ✅ ADICIONAR ESTAS 2 LINHAS:
                    cache.set(cache_key, validated_recommendation, 3600)
                    return validated_recommendation
            
            # Fallback para regras se IA falhar
            logger.warning("Gemini retornou resposta inválida, usando fallback")
            # ✅ MODIFICAR ESTA LINHA:
            fallback = self._generate_rule_based_recommendation(user_profile, workout_history)
            cache.set(cache_key, fallback, 3600)
            return fallback
            
        except Exception as e:
            logger.error(f"Error generating daily recommendation: {e}")
            # ✅ MODIFICAR ESTA LINHA:
            fallback = self._generate_rule_based_recommendation(user_profile, workout_history)
            cache.set(cache_key, fallback, 3600)
            return fallback


    def _extract_focus_from_workout(self, workout):
        """🆕 Extrai foco principal do treino"""
        focus_keywords = {
            'chest': ['peito', 'peitoral', 'chest', 'supino'],
            'back': ['costas', 'dorsal', 'back', 'remada'],
            'legs': ['pernas', 'legs', 'quadríceps', 'glúteos', 'agachamento'],
            'shoulders': ['ombros', 'shoulders', 'deltoides', 'desenvolvimento'],
            'arms': ['braços', 'arms', 'bíceps', 'tríceps'],
            'cardio': ['cardio', 'hiit', 'aeróbico', 'corrida'],
            'abs': ['abdômen', 'abs', 'core', 'abdominal']
        }
        
        text = f"{workout.name} {workout.description}".lower()
        
        for focus, keywords in focus_keywords.items():
            if any(keyword in text for keyword in keywords):
                return focus
        
        return 'full_body'


    def _generate_workout_tip(self, workout, profile):
        """🆕 Gera dica motivacional para o treino"""
        difficulty_tips = {
            'beginner': 'Foque na forma correta, não na velocidade!',
            'intermediate': 'Aumente a intensidade progressivamente!',
            'advanced': 'Desafie seus limites com segurança!',
        }
        
        base_tip = difficulty_tips.get(workout.difficulty_level, 'Você consegue!')
        
        # Adicionar horário preferido se configurado
        if profile.preferred_workout_time and profile.preferred_workout_time != 'flexible':
            time_names = {
                'morning': 'manhã',
                'afternoon': 'tarde',
                'evening': 'noite'
            }
            time_name = time_names.get(profile.preferred_workout_time)
            if time_name:
                base_tip = f"Seu horário ideal é {time_name}. {base_tip}"
        
        return base_tip

    def _analyze_user_preferences(self, user_profile: UserProfile) -> Dict:
        """
        🆕 Analisa preferências configuradas do usuário
        """
        from datetime import datetime
        
        today = datetime.now()
        current_weekday = (today.weekday() + 1) % 7  # 0=Dom, 6=Sáb
        
        # Verificar se é dia preferido
        is_preferred_day = user_profile.is_preferred_training_day(current_weekday)
        is_rest_day = user_profile.is_preferred_rest_day(current_weekday)
        
        # Nome do dia
        weekday_names = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
        current_day_name = weekday_names[current_weekday]
        
        # Dias preferidos configurados
        preferred_days_names = [
            weekday_names[d] for d in user_profile.preferred_training_days
        ] if user_profile.preferred_training_days else []
        
        # Horário preferido
        time_preferences = {
            'morning': 'manhã',
            'afternoon': 'tarde',
            'evening': 'noite',
            'flexible': 'qualquer horário'
        }
        preferred_time = time_preferences.get(
            user_profile.preferred_workout_time, 
            'qualquer horário'
        )
        
        return {
            'training_frequency': user_profile.training_frequency,
            'min_rest_days': user_profile.min_rest_days_between_workouts,
            'current_day': current_day_name,
            'current_weekday': current_weekday,
            'is_preferred_day': is_preferred_day,
            'is_rest_day': is_rest_day,
            'preferred_days': preferred_days_names,
            'preferred_time': preferred_time,
            'has_time_preference': user_profile.preferred_workout_time != 'flexible',
        }


    def _check_physical_constraints(self, user_profile: UserProfile, 
                                    history_analysis: Dict) -> Dict:
        """
        🆕 Verifica restrições físicas e necessidade de descanso
        """
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        constraints = {
            'needs_rest': False,
            'reason': None,
            'has_limitations': False,
            'limitations_text': None,
            'suggested_modifications': []
        }
        
        # 1. Verificar limitações físicas cadastradas
        if user_profile.physical_limitations:
            constraints['has_limitations'] = True
            constraints['limitations_text'] = user_profile.physical_limitations
            
            # Sugerir modificações baseadas em palavras-chave
            limitations_lower = user_profile.physical_limitations.lower()
            
            if any(word in limitations_lower for word in ['joelho', 'joelhos', 'knee']):
                constraints['suggested_modifications'].append('Evitar agachamentos profundos')
                constraints['suggested_modifications'].append('Preferir exercícios de baixo impacto')
            
            if any(word in limitations_lower for word in ['costas', 'lombar', 'coluna', 'back']):
                constraints['suggested_modifications'].append('Evitar cargas muito pesadas')
                constraints['suggested_modifications'].append('Foco em exercícios de fortalecimento de core')
            
            if any(word in limitations_lower for word in ['ombro', 'shoulder']):
                constraints['suggested_modifications'].append('Cuidado com movimentos acima da cabeça')
                constraints['suggested_modifications'].append('Preferir exercícios com amplitude controlada')
        
        # 2. Verificar se precisa de descanso (min_rest_days)
        days_since_last = history_analysis.get('days_since_last_workout')
        min_rest = user_profile.min_rest_days_between_workouts
        
        if days_since_last is not None and days_since_last < min_rest:
            constraints['needs_rest'] = True
            constraints['reason'] = f'Treinou há {days_since_last} dia(s), mínimo é {min_rest} dia(s)'
        
        # 3. Verificar overtraining
        workouts_this_week = history_analysis.get('workouts_this_week', 0)
        target_frequency = user_profile.training_frequency
        
        if workouts_this_week >= target_frequency:
            constraints['needs_rest'] = True
            constraints['reason'] = f'Meta semanal atingida ({workouts_this_week}/{target_frequency})'
        
        # 4. Verificar se treinou demais grupos musculares
        overtrained_groups = []
        muscle_groups_worked = history_analysis.get('muscle_groups_worked', {})
        
        # Threshold baseado no nível
        level_thresholds = {
            'sedentary': 2,
            'light': 2,
            'moderate': 3,
            'active': 4,
            'very_active': 5
        }
        threshold = level_thresholds.get(user_profile.activity_level, 3)
        
        for group, count in muscle_groups_worked.items():
            if count >= threshold:
                overtrained_groups.append(group)
        
        if overtrained_groups:
            constraints['overtrained_groups'] = overtrained_groups
            constraints['suggested_modifications'].append(
                f'Grupos sobrecarregados: {", ".join(overtrained_groups)}'
            )
        
        return constraints


    def _build_daily_recommendation_prompt_simple(self, profile: UserProfile, 
                                             context: Dict, history: Dict) -> str:
        """
        ✅ PROMPT SIMPLES QUE FUNCIONA (baseado na sua versão antiga)
        """
        
        weekday_names = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        current_day = weekday_names[history.get('current_weekday', 0)]

        # 🔥 Tratamento do days_since_last_workout
        days_since = history.get('days_since_last_workout')
        if days_since is None:
            days_since_text = "Nenhum treino registrado"
        elif days_since == 0:
            days_since_text = "Treinou hoje"
        elif days_since == 1:
            days_since_text = "1 dia"
        else:
            days_since_text = f"{days_since} dias"
        
        # Grupos musculares
        muscle_groups_worked = history.get('muscle_groups_worked', {})
        overtrained_groups = [
            group for group, count in muscle_groups_worked.items() 
            if count >= 3
        ]
        underworked_groups = history.get('underworked_groups', [])
        
        return f"""Você é um personal trainer expert. Crie UMA recomendação específica para HOJE.

PERFIL DO USUÁRIO:
- Nome: {profile.user.first_name or 'Usuário'}
- Objetivo: {profile.goal or 'fitness geral'}
- Nível: {profile.activity_level or 'iniciante'}

CONTEXTO ATUAL:
- Dia: {current_day}
- Treinos esta semana: {history.get('workouts_this_week', 0)}
- Dias desde último treino: {days_since_text}
- Frequência semanal: {history.get('weekly_frequency', 'baixa')}

ANÁLISE MUSCULAR:
- Grupos SOBRECARREGADOS: {', '.join(overtrained_groups) or 'nenhum'}
- Grupos NEGLIGENCIADOS: {', '.join(underworked_groups) or 'nenhum'}

RESPONDA APENAS COM JSON VÁLIDO (sem markdown):
{{
    "recommendation_type": "workout|rest|active_recovery|motivation",
    "title": "Título curto (máx 40 caracteres)",
    "message": "Mensagem motivacional (máx 120 caracteres)",
    "focus_area": "chest|back|legs|cardio|recovery|full_body",
    "reasoning": "Explicação clara",
    "intensity": "low|moderate|high",
    "suggested_duration": 30,
    "motivational_tip": "Dica prática (máx 80 caracteres)",
    "emoji": "emoji apropriado"
}}

IMPORTANTE:
- Use o nome: {profile.user.first_name or 'Usuário'}
- Seja específico sobre grupos musculares
- Se treinou 5+ vezes esta semana → sugerir descanso
- Se grupo sobrecarregado → recuperação ativa DESSE grupo
- Se grupo negligenciado → treino do grupo negligenciado"""


    def _generate_rule_based_recommendation(self, profile: UserProfile,
                                    workout_history: List[Dict] = None) -> Dict:
        """
        🆕 Sistema de FALLBACK baseado em regras (quando IA não disponível)
        """
        analysis = self._analyze_recent_workout_history(profile.user, workout_history)
        preferences = self._analyze_user_preferences(profile)
        constraints = self._check_physical_constraints(profile, analysis)
        
        workouts_this_week = analysis.get('workouts_this_week', 0)
        target_frequency = preferences['training_frequency']
        
        # 🔥 CORREÇÃO: Separar valor interno (999) do valor para mensagens
        days_since_last_raw = analysis.get('days_since_last_workout')
        
        # Valor interno para comparações (999 se None)
        days_since_last = 999 if days_since_last_raw is None else days_since_last_raw
        
        # Indicador se nunca treinou (para mensagens)
        never_trained = days_since_last_raw is None
        
        # REGRA 1: Descanso obrigatório
        if constraints['needs_rest']:
            return {
                'recommendation_type': 'rest',
                'title': 'Dia de Descanso Necessário',
                'message': f'{profile.user.first_name or "Você"}, seu corpo precisa de recuperação hoje.',
                'focus_area': 'recovery',
                'intensity': 'low',
                'suggested_duration': 0,
                'emoji': '😴',
                'reasoning': constraints['reason'],
                'motivational_tip': 'O crescimento acontece no descanso!',
                'respects_limitations': True,
                'aligns_with_schedule': True
            }
        
        # REGRA 2: Dia de descanso preferido
        if preferences['is_rest_day'] and workouts_this_week >= target_frequency - 1:
            return {
                'recommendation_type': 'rest',
                'title': f'Aproveite seu {preferences["current_day"]}',
                'message': f'{profile.user.first_name or "Você"} configurou hoje como dia de descanso.',
                'focus_area': 'recovery',
                'intensity': 'low',
                'suggested_duration': 0,
                'emoji': '🧘',
                'reasoning': f'Hoje é {preferences["current_day"]}, seu dia de descanso preferido',
                'motivational_tip': 'Descanso também faz parte do treino!',
                'respects_limitations': True,
                'aligns_with_schedule': True
            }
        
        # REGRA 3: Meta semanal atingida
        if workouts_this_week >= target_frequency:
            return {
                'recommendation_type': 'rest',
                'title': 'Meta Semanal Completa! 🎉',
                'message': f'{profile.user.first_name or "Você"} atingiu {workouts_this_week}/{target_frequency} treinos!',
                'focus_area': 'recovery',
                'intensity': 'low',
                'suggested_duration': 0,
                'emoji': '🏆',
                'reasoning': f'Meta de {target_frequency} treinos/semana completa',
                'motivational_tip': 'Parabéns! Agora é hora de recuperar.',
                'respects_limitations': True,
                'aligns_with_schedule': True
            }
        
        # 🔥 REGRA 4: Muito tempo sem treinar (CORRIGIDO - sem "999 dias")
        if days_since_last >= 4:
            underworked = analysis.get('underworked_groups', [])
            focus = underworked[0] if underworked else 'full_body'
            
            # Considerar limitações
            if constraints['has_limitations'] and focus in ['legs', 'back']:
                focus = 'upper_body'
            
            # ✅ MENSAGEM DIFERENTE se nunca treinou
            if never_trained:
                title = 'Comece Hoje!'
                message = f'{profile.user.first_name or "Você"}, vamos começar sua jornada fitness! 🚀'
                reasoning = 'Primeiro treino - começar com intensidade moderada'
            else:
                title = 'Hora de Voltar!'
                message = f'{profile.user.first_name or "Você"} está há {days_since_last} dias sem treinar.'
                reasoning = f'Retome gradualmente com treino de {focus}'
            
            return {
                'recommendation_type': 'workout',
                'title': title,
                'message': message,
                'focus_area': focus,
                'intensity': 'moderate',
                'suggested_duration': 30,
                'emoji': '🔥',
                'reasoning': reasoning,
                'motivational_tip': 'Começar é metade da vitória!',
                'respects_limitations': True,
                'aligns_with_schedule': preferences['is_preferred_day']
            }
        
        # REGRA 5: Balanceamento muscular
        underworked = analysis.get('underworked_groups', [])
        if underworked:
            focus = underworked[0]
            
            # Adaptar se houver limitações
            if constraints['has_limitations']:
                limitations_lower = constraints['limitations_text'].lower()
                if ('joelho' in limitations_lower or 'knee' in limitations_lower) and focus == 'legs':
                    focus = 'upper_body'
                elif ('costas' in limitations_lower or 'back' in limitations_lower) and focus == 'back':
                    focus = 'cardio'
            
            intensity = 'moderate' if workouts_this_week < target_frequency - 1 else 'light'
            
            return {
                'recommendation_type': 'workout',
                'title': f'Treino de {focus.replace("_", " ").title()}',
                'message': f'{profile.user.first_name or "Você"}, vamos equilibrar o treino!',
                'focus_area': focus,
                'intensity': intensity,
                'suggested_duration': 35,
                'emoji': '💪',
                'reasoning': f'{focus} foi pouco trabalhado esta semana',
                'motivational_tip': f'Treino no {preferences["preferred_time"]} é perfeito!',
                'respects_limitations': bool(constraints['has_limitations']),
                'aligns_with_schedule': preferences['is_preferred_day']
            }
        
        # REGRA PADRÃO: Continue o ritmo
        return {
            'recommendation_type': 'workout',
            'title': 'Continue o Ritmo!',
            'message': f'{profile.user.first_name or "Você"}, mais um treino hoje?',
            'focus_area': 'full_body',
            'intensity': 'moderate',
            'suggested_duration': 30,
            'emoji': '💪',
            'reasoning': f'{workouts_this_week}/{target_frequency} treinos - mantenha a consistência',
            'motivational_tip': f'Seu horário preferido é {preferences["preferred_time"]}!',
            'respects_limitations': True,
            'aligns_with_schedule': preferences['is_preferred_day']
        }


    def _build_personalization_factors(self, profile: UserProfile, history: Dict,
                                    preferences: Dict, constraints: Dict) -> List[str]:
        """
        🆕 Constrói lista de fatores de personalização
        """
        factors = []
        
        # Objetivo
        factors.append(f"goal: {profile.goal or 'maintain'}")
        
        # Nível
        factors.append(f"level: {profile.activity_level or 'moderate'}")
        
        # Frequência
        factors.append(f"frequency: {preferences['training_frequency']}/semana")
        
        # Progresso semanal
        workouts = history.get('workouts_this_week', 0)
        factors.append(f"workouts_this_week: {workouts}/{preferences['training_frequency']}")
        
        # Último treino
        days_since = history.get('days_since_last_workout')
        if days_since is not None:
            factors.append(f"days_since_last: {days_since}")
        
        # Dia preferido
        if preferences['is_preferred_day']:
            factors.append(f"✅ Dia preferido: {preferences['current_day']}")
        elif preferences['is_rest_day']:
            factors.append(f"🛑 Dia de descanso: {preferences['current_day']}")
        
        # Horário preferido
        if preferences['has_time_preference']:
            factors.append(f"⏰ Horário: {preferences['preferred_time']}")
        
        # Limitações físicas
        if constraints['has_limitations']:
            factors.append(f"⚠️ Limitações: {constraints['limitations_text'][:50]}...")
        
        # Descanso necessário
        if constraints['needs_rest']:
            factors.append(f"💤 Precisa descansar: {constraints['reason']}")
        
        return factors


    def _analyze_recent_workout_history(self, user, workout_history: List[Dict] = None) -> Dict:
        """Analisa histórico recente de treinos para contexto"""
        try:
            from datetime import timedelta
            from django.utils import timezone
            from django.db.models import Count
            
            now = timezone.now()
            one_week_ago = now - timedelta(days=7)
            
            # Se o histórico foi passado, usar ele
            if workout_history:
                workouts_this_week = len([
                    w for w in workout_history 
                    if datetime.fromisoformat(w.get('date', '')) > one_week_ago
                ])
                
                if workout_history:
                    last_workout_date = datetime.fromisoformat(workout_history[0].get('date', ''))
                    days_since_last = (now - last_workout_date).days
                else:
                    days_since_last = None
                
                # Analisar grupos musculares trabalhados
                muscle_groups_worked = {}
                for workout in workout_history[:10]:
                    for group in workout.get('muscle_groups', []):
                        muscle_groups_worked[group] = muscle_groups_worked.get(group, 0) + 1
            else:
                # Buscar do banco
                recent_sessions = WorkoutSession.objects.filter(
                    user=user,
                    completed=True,
                    completed_at__gte=one_week_ago
                )
                
                workouts_this_week = recent_sessions.count()
                
                last_session = WorkoutSession.objects.filter(
                    user=user, completed=True
                ).order_by('-completed_at').first()
                
                days_since_last = (now - last_session.completed_at).days if last_session else None

                
                # Grupos musculares trabalhados
                muscle_groups_worked = {}
                exercise_logs = ExerciseLog.objects.filter(
                    session__user=user,
                    session__completed=True,
                    session__completed_at__gte=one_week_ago
                ).values('workout_exercise__exercise__muscle_group').annotate(
                    count=Count('id')
                )
                
                for log in exercise_logs:
                    group = log['workout_exercise__exercise__muscle_group']
                    if group:
                        muscle_groups_worked[group] = log['count']
            
            # Determinar grupos menos trabalhados
            all_groups = ['chest', 'back', 'shoulders', 'arms', 'legs', 'abs', 'cardio']
            underworked_groups = [g for g in all_groups if muscle_groups_worked.get(g, 0) < 2]
            
            # Identificar padrão de treino
            weekday = now.weekday()  # 0=Monday, 6=Sunday
            
            return {
                'workouts_this_week': workouts_this_week,
                'days_since_last_workout': days_since_last,
                'muscle_groups_worked': muscle_groups_worked,
                'underworked_groups': underworked_groups,
                'is_weekend': weekday in [5, 6],
                'current_weekday': weekday,
                'weekly_frequency': 'high' if workouts_this_week >= 4 else 'moderate' if workouts_this_week >= 2 else 'low'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing workout history: {e}")
            return {
                'workouts_this_week': 0,
                'days_since_last_workout': None,
                'muscle_groups_worked': {},
                'underworked_groups': [],
                'is_weekend': False,
                'weekly_frequency': 'unknown'
            }

    def _validate_daily_recommendation(self, recommendation: Dict) -> Optional[Dict]:
        """Valida recomendação diária"""
        try:
            required_fields = ['recommendation_type', 'title', 'message']
            if not all(field in recommendation for field in required_fields):
                logger.error("Missing required fields in daily recommendation")
                return None
            
            # Validar tipo
            valid_types = ['workout', 'rest', 'active_recovery', 'motivation']
            if recommendation['recommendation_type'] not in valid_types:
                recommendation['recommendation_type'] = 'workout'
            
            # Garantir campos opcionais
            recommendation.setdefault('focus_area', 'full_body')
            recommendation.setdefault('intensity', 'moderate')
            recommendation.setdefault('suggested_duration', 30)
            recommendation.setdefault('emoji', '💪')
            recommendation.setdefault('reasoning', 'Recomendação baseada no seu perfil')
            recommendation.setdefault('motivational_tip', 'Continue firme!')
            
            # Limitar tamanhos
            recommendation['title'] = recommendation['title'][:60]
            recommendation['message'] = recommendation['message'][:150]
            recommendation['motivational_tip'] = recommendation['motivational_tip'][:100]
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error validating daily recommendation: {e}")
            return None

    def _calculate_recommendation_confidence(self, history: Dict) -> float:
        """Calcula confiança da recomendação (0-1)"""
        try:
            confidence = 0.5  # Base
            
            # Mais treinos = mais confiança
            workouts = history.get('workouts_this_week', 0)
            if workouts >= 3:
                confidence += 0.3
            elif workouts >= 1:
                confidence += 0.15
            
            # Dados recentes = mais confiança
            days_since = history.get('days_since_last_workout', 999)
            if days_since <= 2:
                confidence += 0.2
            elif days_since <= 7:
                confidence += 0.1
            
            return min(1.0, confidence)
            
        except Exception:
            return 0.5
        
        