# apps/recommendations/tests/test_ai_service.py
# VERSÃO ATUALIZADA PARA GOOGLE GEMINI
import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.cache import cache

from apps.users.models import UserProfile
from apps.workouts.models import WorkoutSession, ExerciseLog
from apps.recommendations.services.ai_service import AIService


class AIServiceTestCase(TestCase):
    """Testes abrangentes para o AIService com Gemini"""
    
    def setUp(self):
        """Setup para testes"""
        cache.clear()
        
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
        
        # Criar sessões para contexto
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
        """Testa inicialização sem API key do Gemini"""
        with override_settings(GEMINI_API_KEY=''):
            ai_service = AIService()
            self.assertFalse(ai_service.is_available)
            self.assertIsNone(ai_service.model)
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_initialization_with_api_key(self, mock_model, mock_configure):
        """Testa inicialização com API key válida do Gemini"""
        # Mock do modelo Gemini
        mock_gemini_model = Mock()
        mock_model.return_value = mock_gemini_model
        
        # Mock do teste de conectividade
        mock_response = Mock()
        mock_response.text = "Test"
        mock_gemini_model.generate_content.return_value = mock_response
        
        with override_settings(GEMINI_API_KEY='test-key'):
            ai_service = AIService()
            ai_service._test_api_connection = Mock(return_value=True)
            ai_service._initialize_client()
            
            self.assertTrue(ai_service.is_available)
            self.assertIsNotNone(ai_service.model)
            mock_configure.assert_called_once_with(api_key='test-key')
    
    def test_rate_limiting_gemini(self):
        """Testa rate limiting do Gemini (15 req/min)"""
        ai_service = AIService()
        
        # Simular 15 requisições (limite do Gemini)
        rate_limit_data = {"count": 15, "reset_time": 0}
        cache.set(ai_service.rate_limit_cache_key, rate_limit_data, 60)
        
        # Deve retornar False (limite atingido)
        self.assertFalse(ai_service._check_rate_limit())
        
        # Resetar contador
        rate_limit_data = {"count": 0, "reset_time": 0}
        cache.set(ai_service.rate_limit_cache_key, rate_limit_data, 60)
        
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
                },
                {
                    'name': 'Plank',
                    'sets': 3,
                    'reps': '30s',
                    'rest_seconds': 30
                }
            ]
        }
        
        result = ai_service._validate_and_enhance_workout_plan(valid_plan)
        self.assertIsNotNone(result)
        self.assertIn('quality_score', result)
        self.assertEqual(len(result['exercises']), 3)
        
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
        
        self.assertEqual(ai_service._sanitize_sets('3 sets'), 3)
        self.assertEqual(ai_service._sanitize_sets('10'), 6)  # Máximo 6
        self.assertEqual(ai_service._sanitize_sets(0), 1)     # Mínimo 1
        self.assertEqual(ai_service._sanitize_sets('invalid'), 3)
        self.assertEqual(ai_service._sanitize_sets(4.5), 4)
    
    def test_rest_sanitization(self):
        """Testa sanitização de tempo de descanso"""
        ai_service = AIService()
        
        self.assertEqual(ai_service._sanitize_rest('45 seconds'), 45)
        self.assertEqual(ai_service._sanitize_rest('300'), 180)  # Máximo 180
        self.assertEqual(ai_service._sanitize_rest(10), 15)      # Mínimo 15
        self.assertEqual(ai_service._sanitize_rest('invalid'), 45)
    
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
        self.assertGreater(score, 80)
        
        # Plano de baixa qualidade
        low_quality_plan = {
            'exercises': [
                {'muscle_group': 'chest', 'instructions': 'curto'},
                {'muscle_group': 'chest', 'instructions': 'curto'}
            ]
        }
        
        score = ai_service._calculate_workout_quality_score(low_quality_plan)
        self.assertLess(score, 50)
    
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_request_success(self, mock_model):
        """Testa requisição Gemini bem-sucedida"""
        # Mock do modelo
        mock_gemini_model = Mock()
        mock_model.return_value = mock_gemini_model
        
        # Mock da resposta
        mock_response = Mock()
        mock_response.text = "Resposta do Gemini"
        mock_gemini_model.generate_content.return_value = mock_response
        
        with override_settings(GEMINI_API_KEY='test-key'):
            ai_service = AIService()
            ai_service.model = mock_gemini_model
            ai_service.is_available = True
            
            result = ai_service._make_gemini_request("Test prompt")
            
            self.assertEqual(result, "Resposta do Gemini")
            mock_gemini_model.generate_content.assert_called_once_with("Test prompt")
    
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_request_with_markdown_cleanup(self, mock_model):
        """Testa limpeza de markdown nas respostas do Gemini"""
        mock_gemini_model = Mock()
        mock_model.return_value = mock_gemini_model
        
        # Resposta com markdown
        mock_response = Mock()
        mock_response.text = '```json\n{"test": "value"}\n```'
        mock_gemini_model.generate_content.return_value = mock_response
        
        with override_settings(GEMINI_API_KEY='test-key'):
            ai_service = AIService()
            ai_service.model = mock_gemini_model
            ai_service.is_available = True
            
            result = ai_service._make_gemini_request("Test")
            
            # Deve limpar o markdown
            self.assertNotIn('```', result)
    
    def test_detailed_progress_collection(self):
        """Testa coleta detalhada de dados de progresso"""
        ai_service = AIService()
        
        # Criar mais sessões
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
        
        # Alto desempenho
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
        
        # Baixo desempenho
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
        """Testa estatísticas de uso da API Gemini"""
        ai_service = AIService()
        
        from datetime import datetime
        today_key = f"gemini_metrics_{datetime.now().strftime('%Y-%m-%d')}"
        mock_metrics = [
            {
                'timestamp': '2025-10-06T10:00:00',
                'prompt_chars': 100,
                'response_chars': 200
            },
            {
                'timestamp': '2025-10-06T11:00:00',
                'prompt_chars': 150,
                'response_chars': 300
            }
        ]
        cache.set(today_key, mock_metrics, 86400)
        
        stats = ai_service.get_api_usage_stats()
        
        self.assertIn('usage_today', stats)
        self.assertEqual(stats['usage_today']['requests_made'], 2)
        
    def test_fallback_when_ai_unavailable(self):
        """Testa fallback quando Gemini está indisponível"""
        with override_settings(GEMINI_API_KEY=''):
            ai_service = AIService()
            
            # Todas as funções devem retornar None
            result = ai_service.generate_personalized_workout_plan(
                self.profile, 30, 'full_body', 'beginner'
            )
            self.assertIsNone(result)
            
            result = ai_service.analyze_user_progress(self.profile)
            self.assertIsNone(result)
            
            result = ai_service.generate_motivational_content(
                self.profile, 'workout_start'
            )
            self.assertIsNone(result)


class AIServiceIntegrationTestCase(TestCase):
    """Testes de integração com API real do Gemini"""
    
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
        """Teste com API real do Gemini - executar manualmente"""
        from django.conf import settings
        if not settings.GEMINI_API_KEY:
            self.skipTest("Gemini API key not configured")
        
        ai_service = AIService()
        if not ai_service.is_available:
            self.skipTest("Gemini service not available")
        
        result = ai_service.generate_personalized_workout_plan(
            self.profile, 30, 'upper', 'intermediate'
        )
        
        if result:
            self.assertIsInstance(result, dict)
            self.assertIn('workout_name', result)
            self.assertIn('exercises', result)
            self.assertGreater(len(result['exercises']), 3)
            self.assertIn('quality_score', result)
            print(f"\n✅ Treino gerado: {result['workout_name']}")
            print(f"   Exercícios: {len(result['exercises'])}")
            print(f"   Qualidade: {result['quality_score']}")
    
    def test_real_progress_analysis(self):
        """Teste de análise com API real do Gemini"""
        from django.conf import settings
        if not settings.GEMINI_API_KEY:
            self.skipTest("Gemini API key not configured")
        
        # Criar sessões para análise
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
            self.skipTest("Gemini service not available")
        
        result = ai_service.analyze_user_progress(self.profile)
        
        if result:
            self.assertIsInstance(result, dict)
            self.assertIn('overall_progress', result)
            self.assertIn('analysis_metadata', result)
            print(f"\n✅ Análise gerada: {result.get('overall_progress')}")
    
    def test_real_motivational_message(self):
        """Teste de mensagem motivacional com API real"""
        from django.conf import settings
        if not settings.GEMINI_API_KEY:
            self.skipTest("Gemini API key not configured")
        
        ai_service = AIService()
        if not ai_service.is_available:
            self.skipTest("Gemini service not available")
        
        result = ai_service.generate_motivational_content(
            self.profile, 'workout_start'
        )
        
        if result:
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 20)
            self.assertLess(len(result), 250)
            print(f"\n✅ Mensagem gerada: {result}")


# ============================================================================
# COMANDOS PARA EXECUTAR OS TESTES
# ============================================================================

# Testes unitários (não precisam de API key):
# python manage.py test apps.recommendations.tests.test_ai_service.AIServiceTestCase -v 2

# Testes de integração (COM API key do Gemini):
# python manage.py test apps.recommendations.tests.test_ai_service.AIServiceIntegrationTestCase -v 2

# Todos os testes:
# python manage.py test apps.recommendations.tests.test_ai_service -v 2

# Teste específico:
# python manage.py test apps.recommendations.tests.test_ai_service.AIServiceTestCase.test_gemini_request_success -v 2