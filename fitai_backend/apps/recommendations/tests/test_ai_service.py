# apps/recommendations/tests/test_ai_service.py
import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.cache import cache

from apps.users.models import UserProfile
from apps.workouts.models import WorkoutSession, ExerciseLog
from apps.recommendations.services.ai_service import AIService


class AIServiceTestCase(TestCase):
    """Testes abrangentes para o AIService"""
    
    def setUp(self):
        """Setup para testes"""
        cache.clear()  # Limpar cache entre testes
        
        # Criar usuário de teste
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='test123',
            first_name='João'
        )
        
        # Criar perfil
        self.profile = UserProfile.objects.create(
            user=self.user,
            age=25,
            goal='lose_weight',
            activity_level='moderate',
            height=175,
            weight=80
        )
        
        # Criar algumas sessões para contexto
        for i in range(3):
            WorkoutSession.objects.create(
                user=self.user,
                workout_id=1,
                completed=True,
                actual_duration=30,
                user_rating=4
            )
    
    def tearDown(self):
        """Limpar cache após cada teste"""
        cache.clear()
    
    def test_initialization_without_api_key(self):
        """Testa inicialização sem API key"""
        with override_settings(OPENAI_API_KEY=''):
            ai_service = AIService()
            self.assertFalse(ai_service.is_available)
            self.assertIsNone(ai_service.client)
    
    @patch('apps.recommendations.services.ai_service.openai.OpenAI')
    def test_initialization_with_api_key(self, mock_openai):
        """Testa inicialização com API key válida"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock do teste de conectividade
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test"
        mock_client.chat.completions.create.return_value = mock_response
        
        with override_settings(OPENAI_API_KEY='test-key'):
            ai_service = AIService()
            ai_service._test_api_connection = Mock(return_value=True)
            ai_service._initialize_client()
            
            self.assertTrue(ai_service.is_available)
            self.assertIsNotNone(ai_service.client)
    
    def test_rate_limiting(self):
        """Testa sistema de rate limiting"""
        ai_service = AIService()
        
        # Simular 50 requisições (limite)
        rate_limit_data = {"count": 50, "reset_time": 0}
        cache.set(ai_service.rate_limit_cache_key, rate_limit_data, 3600)
        
        # Deve retornar False (limite atingido)
        self.assertFalse(ai_service._check_rate_limit())
        
        # Resetar contador
        rate_limit_data = {"count": 0, "reset_time": 0}
        cache.set(ai_service.rate_limit_cache_key, rate_limit_data, 3600)
        
        # Deve retornar True
        self.assertTrue(ai_service._check_rate_limit())
    
    def test_user_context_collection(self):
        """Testa coleta de contexto do usuário"""
        ai_service = AIService()
        context = ai_service._get_user_context(self.user)
        
        self.assertIn('total_workouts', context)
        self.assertIn('recent_activity', context)
        self.assertIn('has_recent_data', context)
        self.assertEqual(context['total_workouts'], 3)
        self.assertTrue(context['has_recent_data'])
    
    def test_workout_plan_validation(self):
        """Testa validação de planos de treino"""
        ai_service = AIService()
        
        # Plano válido
        valid_plan = {
            'workout_name': 'Teste',
            'estimated_duration': 30,
            'exercises': [
                {
                    'name': 'Push-up',
                    'sets': '3',
                    'reps': '12',
                    'rest_seconds': '45'
                },
                {
                    'name': 'Squat',
                    'sets': 4,
                    'reps': '15',
                    'rest_seconds': 60
                }
            ]
        }
        
        result = ai_service._validate_and_enhance_workout_plan(valid_plan)
        self.assertIsNotNone(result)
        self.assertIn('quality_score', result)
        self.assertEqual(len(result['exercises']), 2)
        
        # Verificar sanitização de dados
        self.assertEqual(result['exercises'][0]['sets'], 3)
        self.assertEqual(result['exercises'][1]['rest_seconds'], 60)
        
        # Plano inválido (poucos exercícios)
        invalid_plan = {
            'workout_name': 'Teste',
            'exercises': [
                {'name': 'Push-up'}
            ]
        }
        
        result = ai_service._validate_and_enhance_workout_plan(invalid_plan)
        self.assertIsNone(result)
    
    def test_sets_sanitization(self):
        """Testa sanitização de número de séries"""
        ai_service = AIService()
        
        # Testes de diferentes inputs
        self.assertEqual(ai_service._sanitize_sets('3 sets'), 3)
        self.assertEqual(ai_service._sanitize_sets('10'), 6)  # Máximo 6
        self.assertEqual(ai_service._sanitize_sets(0), 1)     # Mínimo 1
        self.assertEqual(ai_service._sanitize_sets('invalid'), 3)  # Default
        self.assertEqual(ai_service._sanitize_sets(4.5), 4)   # Float para int
    
    def test_rest_sanitization(self):
        """Testa sanitização de tempo de descanso"""
        ai_service = AIService()
        
        # Testes de diferentes inputs
        self.assertEqual(ai_service._sanitize_rest('45 seconds'), 45)
        self.assertEqual(ai_service._sanitize_rest('300'), 180)  # Máximo 180
        self.assertEqual(ai_service._sanitize_rest(10), 15)     # Mínimo 15
        self.assertEqual(ai_service._sanitize_rest('invalid'), 45)  # Default
    
    def test_quality_score_calculation(self):
        """Testa cálculo de score de qualidade"""
        ai_service = AIService()
        
        # Plano de alta qualidade
        high_quality_plan = {
            'exercises': [
                {
                    'muscle_group': 'chest',
                    'instructions': 'Instruções detalhadas muito completas para execução',
                    'safety_tips': 'Dicas de segurança importantes'
                },
                {
                    'muscle_group': 'back',
                    'instructions': 'Mais instruções detalhadas completas',
                    'safety_tips': 'Mais dicas de segurança'
                },
                {
                    'muscle_group': 'legs',
                    'instructions': 'Instruções bem detalhadas',
                    'safety_tips': 'Segurança em primeiro lugar'
                },
                {
                    'muscle_group': 'arms',
                    'instructions': 'Instruções muito claras',
                    'safety_tips': 'Cuidados especiais'
                },
                {
                    'muscle_group': 'shoulders',
                    'instructions': 'Instruções bem explicadas',
                    'safety_tips': 'Atenção à forma'
                },
                {
                    'muscle_group': 'core',
                    'instructions': 'Detalhes da execução',
                    'safety_tips': 'Proteção da coluna'
                }
            ],
            'warm_up': {'instructions': 'Aquecimento'},
            'cool_down': {'instructions': 'Alongamento'}
        }
        
        score = ai_service._calculate_workout_quality_score(high_quality_plan)
        self.assertGreater(score, 80)  # Deve ter score alto
        
        # Plano de baixa qualidade
        low_quality_plan = {
            'exercises': [
                {'muscle_group': 'chest', 'instructions': 'curto'},
                {'muscle_group': 'chest', 'instructions': 'curto'}
            ]
        }
        
        score = ai_service._calculate_workout_quality_score(low_quality_plan)
        self.assertLess(score, 50)  # Deve ter score baixo
    
    @patch('apps.recommendations.services.ai_service.openai.OpenAI')
    def test_openai_request_success(self, mock_openai):
        """Testa requisição OpenAI bem-sucedida"""
        # Mock do cliente OpenAI
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock da resposta
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Resposta da IA"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        mock_response.model = "gpt-3.5-turbo"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Configurar AI Service
        with override_settings(OPENAI_API_KEY='test-key'):
            ai_service = AIService()
            ai_service.client = mock_client
            ai_service.is_available = True
            
            # Fazer requisição
            messages = [{"role": "user", "content": "Test"}]
            result = ai_service._make_openai_request(messages)
            
            self.assertEqual(result, "Resposta da IA")
            mock_client.chat.completions.create.assert_called_once()
    
    @patch('apps.recommendations.services.ai_service.openai.OpenAI')
    def test_openai_request_rate_limit_error(self, mock_openai):
        """Testa tratamento de erro de rate limit"""
        import openai
        
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = openai.RateLimitError("Rate limit exceeded", None, None)
        
        with override_settings(OPENAI_API_KEY='test-key'):
            ai_service = AIService()
            ai_service.client = mock_client
            ai_service.is_available = True
            
            messages = [{"role": "user", "content": "Test"}]
            result = ai_service._make_openai_request(messages)
            
            self.assertIsNone(result)
            # Verificar se foi marcado como temporariamente indisponível
            self.assertTrue(cache.get("openai_temp_disabled"))
    
    def test_detailed_progress_collection(self):
        """Testa coleta detalhada de dados de progresso"""
        ai_service = AIService()
        
        # Criar mais sessões para dados suficientes
        for i in range(5):
            WorkoutSession.objects.create(
                user=self.user,
                workout_id=1,
                completed=True,
                actual_duration=35,
                user_rating=4
            )
        
        data = ai_service._collect_detailed_user_progress(self.user)
        
        self.assertTrue(data['has_sufficient_data'])
        self.assertIn('month_stats', data)
        self.assertIn('week_stats', data)
        self.assertIn('trends', data)
        
        month_stats = data['month_stats']
        self.assertGreater(month_stats['completed_sessions'], 0)
        self.assertGreater(month_stats['completion_rate'], 0)
    
    def test_overall_progress_score(self):
        """Testa cálculo de score geral de progresso"""
        ai_service = AIService()
        
        # Dados simulados de alto desempenho
        high_performance_data = {
            'month_stats': {
                'completed_sessions': 16,
                'completion_rate': 90,
                'avg_rating': 4.5
            },
            'trends': {
                'consistency_score': 0.8
            }
        }
        
        score = ai_service._calculate_overall_progress_score(high_performance_data)
        self.assertGreater(score, 80)
        
        # Dados simulados de baixo desempenho
        low_performance_data = {
            'month_stats': {
                'completed_sessions': 2,
                'completion_rate': 50,
                'avg_rating': 2.0
            },
            'trends': {
                'consistency_score': 0.3
            }
        }
        
        score = ai_service._calculate_overall_progress_score(low_performance_data)
        self.assertLess(score, 40)
    
    def test_api_usage_stats(self):
        """Testa coleta de estatísticas de uso da API"""
        ai_service = AIService()
        
        # Simular métricas do dia
        from datetime import datetime
        today_key = f"openai_metrics_{datetime.now().strftime('%Y-%m-%d')}"
        mock_metrics = [
            {
                'timestamp': '2025-08-27T10:00:00',
                'total_tokens': 100,
                'prompt_tokens': 60,
                'completion_tokens': 40
            },
            {
                'timestamp': '2025-08-27T11:00:00',
                'total_tokens': 150,
                'prompt_tokens': 90,
                'completion_tokens': 60
            }
        ]
        cache.set(today_key, mock_metrics, 86400)
        
        stats = ai_service.get_api_usage_stats()
        
        self.assertIn('usage_today', stats)
        self.assertEqual(stats['usage_today']['requests_made'], 2)
        self.assertEqual(stats['usage_today']['tokens_used'], 250)
        
    def test_fallback_when_ai_unavailable(self):
        """Testa comportamento quando IA está indisponível"""
        # AI service sem chave
        with override_settings(OPENAI_API_KEY=''):
            ai_service = AIService()
            
            # Todas as funções devem retornar None
            result = ai_service.generate_personalized_workout_plan(
                self.profile, 30, 'full_body', 'beginner'
            )
            self.assertIsNone(result)
            
            result = ai_service.analyze_user_progress(self.profile)
            self.assertIsNone(result)
            
            result = ai_service.generate_motivational_content(self.profile, 'workout_start')
            self.assertIsNone(result)


class AIServiceIntegrationTestCase(TestCase):
    """Testes de integração que requerem API key real (executar manualmente)"""
    
    def setUp(self):
        """Setup para testes de integração"""
        self.user = User.objects.create_user(
            username='integration_test',
            email='integration@test.com',
            first_name='Maria'
        )
        
        self.profile = UserProfile.objects.create(
            user=self.user,
            age=28,
            goal='gain_muscle',
            activity_level='active'
        )
    
    def test_real_workout_generation(self):
        """Teste com API real - executar manualmente com API key válida"""
        # Pular se não há API key configurada
        from django.conf import settings
        if not settings.OPENAI_API_KEY:
            self.skipTest("OpenAI API key not configured")
        
        ai_service = AIService()
        if not ai_service.is_available:
            self.skipTest("OpenAI service not available")
        
        result = ai_service.generate_personalized_workout_plan(
            self.profile, 30, 'upper', 'intermediate'
        )
        
        if result:  # Só testa se a API respondeu
            self.assertIsInstance(result, dict)
            self.assertIn('workout_name', result)
            self.assertIn('exercises', result)
            self.assertGreater(len(result['exercises']), 3)
            self.assertIn('quality_score', result)
    
    def test_real_progress_analysis(self):
        """Teste de análise de progresso com API real"""
        from django.conf import settings
        if not settings.OPENAI_API_KEY:
            self.skipTest("OpenAI API key not configured")
        
        # Criar algumas sessões para análise
        for i in range(5):
            WorkoutSession.objects.create(
                user=self.user,
                workout_id=1,
                completed=True,
                actual_duration=30,
                user_rating=4
            )
        
        ai_service = AIService()
        if not ai_service.is_available:
            self.skipTest("OpenAI service not available")
        
        result = ai_service.analyze_user_progress(self.profile)
        
        if result:  # Só testa se a API respondeu
            self.assertIsInstance(result, dict)
            self.assertIn('overall_progress', result)
            self.assertIn('analysis_metadata', result)


# Comando para executar testes:
# python manage.py test apps.recommendations.tests.test_ai_service -v 2

# Para executar apenas testes que não precisam de API key:
# python manage.py test apps.recommendations.tests.test_ai_service.AIServiceTestCase -v 2

# Para executar testes de integração (com API key):
# OPENAI_API_KEY=sua_chave python manage.py test apps.recommendations.tests.test_ai_service.AIServiceIntegrationTestCase -v 2