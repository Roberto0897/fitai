# apps/recommendations/management/commands/ai_operations.py
import json
import time
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone

from apps.users.models import UserProfile
from apps.recommendations.services.ai_service import AIService
from apps.recommendations.services.recommendation_engine import RecommendationEngine
from apps.workouts.models import WorkoutSession


class Command(BaseCommand):
    help = 'Gerencia operações de IA do FitAI - testes, diagnósticos e manutenção'

    def add_arguments(self, parser):
        """Define argumentos do comando"""
        parser.add_argument(
            'action',
            type=str,
            choices=['test', 'diagnose', 'generate_batch', 'stats', 'clear_cache', 'validate_setup'],
            help='Ação a ser executada'
        )
        
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID do usuário para operações específicas'
        )
        
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Número de itens para operações em lote (default: 5)'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força operação mesmo com limitações'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Saída detalhada'
        )

    def handle(self, *args, **options):
        """Handler principal do comando"""
        action = options['action']
        
        # Banner de início
        self.stdout.write(
            self.style.SUCCESS('🤖 FITAI - AI OPERATIONS MANAGER')
        )
        self.stdout.write(f"Executando ação: {action}")
        self.stdout.write(f"Timestamp: {datetime.now().isoformat()}")
        self.stdout.write("-" * 50)
        
        try:
            # Dispatch para ação específica
            if action == 'test':
                self.handle_test(options)
            elif action == 'diagnose':
                self.handle_diagnose(options)
            elif action == 'generate_batch':
                self.handle_generate_batch(options)
            elif action == 'stats':
                self.handle_stats(options)
            elif action == 'clear_cache':
                self.handle_clear_cache(options)
            elif action == 'validate_setup':
                self.handle_validate_setup(options)
                
        except Exception as e:
            raise CommandError(f'Erro na execução: {e}')
        
        self.stdout.write(
            self.style.SUCCESS('✅ Operação concluída com sucesso!')
        )

    def handle_test(self, options):
        """Testa integração com OpenAI"""
        self.stdout.write("🧪 TESTANDO INTEGRAÇÃO OPENAI")
        
        ai_service = AIService()
        
        # 1. Teste de disponibilidade
        self.stdout.write(f"API Disponível: {ai_service.is_available}")
        
        if not ai_service.is_available:
            self.stdout.write(
                self.style.WARNING("⚠️ OpenAI não disponível. Verificar configurações.")
            )
            self._show_setup_help()
            return
        
        # 2. Teste de conectividade
        self.stdout.write("Testando conectividade...")
        connection_test = ai_service._test_api_connection()
        self.stdout.write(f"Conexão OpenAI: {'✅' if connection_test else '❌'}")
        
        # 3. Teste com usuário real
        user = self._get_test_user(options.get('user_id'))
        if not user:
            return
            
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("❌ Usuário não tem perfil. Use um usuário com perfil completo.")
            )
            return
        
        self.stdout.write(f"Testando com usuário: {user.username}")
        
        # 4. Teste de geração de treino
        if options.get('force') or input("Testar geração de treino? (s/N): ").lower() == 's':
            self.stdout.write("Gerando treino de teste...")
            start_time = time.time()
            
            workout = ai_service.generate_personalized_workout_plan(
                profile, 30, 'full_body', 'intermediate'
            )
            
            elapsed = time.time() - start_time
            
            if workout:
                self.stdout.write(f"✅ Treino gerado em {elapsed:.2f}s")
                self.stdout.write(f"Nome: {workout.get('workout_name', 'N/A')}")
                self.stdout.write(f"Exercícios: {len(workout.get('exercises', []))}")
                self.stdout.write(f"Score de qualidade: {workout.get('quality_score', 'N/A')}")
                
                if options.get('verbose'):
                    self._show_workout_details(workout)
            else:
                self.stdout.write("❌ Falha na geração do treino")
        
        # 5. Teste de análise de progresso
        if options.get('force') or input("Testar análise de progresso? (s/N): ").lower() == 's':
            self.stdout.write("Analisando progresso...")
            start_time = time.time()
            
            analysis = ai_service.analyze_user_progress(profile)
            elapsed = time.time() - start_time
            
            if analysis:
                self.stdout.write(f"✅ Análise gerada em {elapsed:.2f}s")
                self.stdout.write(f"Progresso geral: {analysis.get('overall_progress', 'N/A')}")
                
                if options.get('verbose'):
                    self._show_analysis_details(analysis)
            else:
                self.stdout.write("❌ Falha na análise de progresso")
        
        # 6. Teste de mensagem motivacional
        if options.get('force') or input("Testar mensagem motivacional? (s/N): ").lower() == 's':
            message = ai_service.generate_motivational_content(profile, 'workout_start')
            
            if message:
                self.stdout.write("✅ Mensagem motivacional:")
                self.stdout.write(f"'{message}'")
            else:
                self.stdout.write("❌ Falha na geração de mensagem")

    def handle_diagnose(self, options):
        """Diagnóstica sistema de IA"""
        self.stdout.write("🔍 DIAGNÓSTICO DO SISTEMA DE IA")
        
        # 1. Configurações
        self.stdout.write("\n📋 CONFIGURAÇÕES:")
        config_items = [
            ('OPENAI_API_KEY', '***' if settings.OPENAI_API_KEY else 'NÃO CONFIGURADA'),
            ('OPENAI_MODEL', getattr(settings, 'OPENAI_MODEL', 'N/A')),
            ('OPENAI_MAX_TOKENS', getattr(settings, 'OPENAI_MAX_TOKENS', 'N/A')),
            ('OPENAI_TEMPERATURE', getattr(settings, 'OPENAI_TEMPERATURE', 'N/A')),
            ('AI_FEATURES_ENABLED', getattr(settings, 'AI_FEATURES_ENABLED', 'N/A')),
        ]
        
        for key, value in config_items:
            self.stdout.write(f"  {key}: {value}")
        
        # 2. Estado do cache
        ai_service = AIService()
        self.stdout.write("\n💾 CACHE:")
        
        rate_limit_data = cache.get(ai_service.rate_limit_cache_key, {})
        self.stdout.write(f"  Rate limit count: {rate_limit_data.get('count', 0)}")
        
        temp_disabled = cache.get("openai_temp_disabled", False)
        self.stdout.write(f"  Temporariamente desabilitado: {temp_disabled}")
        
        # 3. Estatísticas de uso
        stats = ai_service.get_api_usage_stats()
        if 'usage_today' in stats:
            self.stdout.write("\n📊 USO HOJE:")
            usage = stats['usage_today']
            self.stdout.write(f"  Requisições: {usage.get('requests_made', 0)}")
            self.stdout.write(f"  Tokens usados: {usage.get('tokens_used', 0)}")
            self.stdout.write(f"  Rate limit restante: {usage.get('rate_limit_remaining', 0)}")
        
        # 4. Status dos usuários
        self.stdout.write("\n👥 USUÁRIOS:")
        total_users = User.objects.count()
        users_with_profile = UserProfile.objects.count()
        users_with_sessions = WorkoutSession.objects.values('user').distinct().count()
        
        self.stdout.write(f"  Total de usuários: {total_users}")
        self.stdout.write(f"  Com perfil completo: {users_with_profile}")
        self.stdout.write(f"  Com sessões de treino: {users_with_sessions}")
        
        # 5. Recomendações
        self.stdout.write("\n🎯 RECOMENDAÇÕES:")
        
        issues = []
        recommendations = []
        
        if not settings.OPENAI_API_KEY:
            issues.append("API Key não configurada")
            recommendations.append("Configure OPENAI_API_KEY no arquivo .env")
        
        if rate_limit_data.get('count', 0) > 40:
            issues.append("Rate limit próximo do limite")
            recommendations.append("Monitore uso da API ou aumente limite")
        
        if temp_disabled:
            issues.append("API temporariamente desabilitada")
            recommendations.append("Aguarde alguns minutos e teste novamente")
        
        if users_with_profile < total_users:
            issues.append("Usuários sem perfil completo")
            recommendations.append("Incentive usuários a completarem o perfil")
        
        if issues:
            for issue in issues:
                self.stdout.write(self.style.WARNING(f"  ⚠️ {issue}"))
        
        if recommendations:
            self.stdout.write("\n💡 AÇÕES SUGERIDAS:")
            for rec in recommendations:
                self.stdout.write(f"  • {rec}")
        
        if not issues:
            self.stdout.write("  ✅ Sistema funcionando normalmente")

    def handle_generate_batch(self, options):
        """Gera recomendações em lote para usuários"""
        count = options['count']
        self.stdout.write(f"🔄 GERANDO {count} RECOMENDAÇÕES EM LOTE")
        
        # Buscar usuários ativos com perfil
        users = User.objects.filter(
            userprofile__isnull=False,
            workoutsession__created_at__gte=timezone.now() - timedelta(days=30)
        ).distinct()[:count]
        
        if not users.exists():
            self.stdout.write(
                self.style.WARNING("❌ Nenhum usuário ativo encontrado")
            )
            return
        
        ai_service = AIService()
        recommendation_engine = RecommendationEngine()
        
        success_count = 0
        error_count = 0
        
        for user in users:
            try:
                self.stdout.write(f"Processando {user.username}...")
                
                # Gerar recomendações híbridas
                recommendations = recommendation_engine.generate_recommendations(
                    user=user,
                    algorithm='hybrid',
                    limit=3
                )
                
                if recommendations:
                    success_count += 1
                    self.stdout.write(f"  ✅ {len(recommendations)} recomendações geradas")
                else:
                    error_count += 1
                    self.stdout.write("  ❌ Falha na geração")
                
                # Pequena pausa para não sobrecarregar
                time.sleep(0.5)
                
            except Exception as e:
                error_count += 1
                self.stdout.write(f"  ❌ Erro: {e}")
        
        self.stdout.write(f"\n📊 RESULTADOS:")
        self.stdout.write(f"  Sucessos: {success_count}")
        self.stdout.write(f"  Erros: {error_count}")
        self.stdout.write(f"  Taxa de sucesso: {success_count/(success_count+error_count)*100:.1f}%")

    def handle_stats(self, options):
        """Mostra estatísticas detalhadas"""
        self.stdout.write("📊 ESTATÍSTICAS DE IA")
        
        ai_service = AIService()
        
        # Stats da API
        api_stats = ai_service.get_api_usage_stats()
        self.stdout.write("\n🔌 API OpenAI:")
        self.stdout.write(f"  Status: {'✅ Ativa' if api_stats.get('api_available') else '❌ Inativa'}")
        
        if 'usage_today' in api_stats:
            usage = api_stats['usage_today']
            self.stdout.write(f"  Requisições hoje: {usage.get('requests_made', 0)}")
            self.stdout.write(f"  Tokens consumidos: {usage.get('tokens_used', 0)}")
            
            # Estimativa de custo (aproximado para GPT-3.5-turbo)
            tokens = usage.get('tokens_used', 0)
            estimated_cost = tokens * 0.002 / 1000  # $0.002 per 1K tokens
            self.stdout.write(f"  Custo estimado: ${estimated_cost:.4f}")
        
        # Stats dos usuários
        self.stdout.write("\n👤 USUÁRIOS:")
        
        total_profiles = UserProfile.objects.count()
        active_users = User.objects.filter(
            workoutsession__created_at__gte=timezone.now() - timedelta(days=7)
        ).distinct().count()
        
        self.stdout.write(f"  Perfis completos: {total_profiles}")
        self.stdout.write(f"  Usuários ativos (7 dias): {active_users}")
        
        # Goals distribution
        goals = UserProfile.objects.values_list('goal', flat=True)
        goal_distribution = {}
        for goal in goals:
            goal_distribution[goal] = goal_distribution.get(goal, 0) + 1
        
        self.stdout.write("\n🎯 DISTRIBUIÇÃO DE OBJETIVOS:")
        for goal, count in goal_distribution.items():
            percentage = count / total_profiles * 100 if total_profiles > 0 else 0
            self.stdout.write(f"  {goal or 'não definido'}: {count} ({percentage:.1f}%)")
        
        # Workout sessions stats
        recent_sessions = WorkoutSession.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        total_sessions = recent_sessions.count()
        completed_sessions = recent_sessions.filter(completed=True).count()
        completion_rate = completed_sessions / total_sessions * 100 if total_sessions > 0 else 0
        
        self.stdout.write(f"\n🏋️ TREINOS (30 DIAS):")
        self.stdout.write(f"  Total de sessões: {total_sessions}")
        self.stdout.write(f"  Sessões completadas: {completed_sessions}")
        self.stdout.write(f"  Taxa de conclusão: {completion_rate:.1f}%")

    def handle_clear_cache(self, options):
        """Limpa cache de IA"""
        self.stdout.write("🧹 LIMPANDO CACHE DE IA")
        
        ai_service = AIService()
        
        # Listar itens que serão limpos
        items_to_clear = [
            ai_service.rate_limit_cache_key,
            "openai_temp_disabled",
        ]
        
        # Limpar métricas diárias (últimos 7 dias)
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            items_to_clear.append(f"openai_metrics_{date}")
        
        # Limpar contextos de usuários
        user_ids = User.objects.values_list('id', flat=True)
        for user_id in user_ids[:50]:  # Limitar para evitar sobrecarga
            items_to_clear.append(f"user_context_{user_id}")
        
        cleared_count = 0
        for key in items_to_clear:
            if cache.get(key) is not None:
                cache.delete(key)
                cleared_count += 1
        
        self.stdout.write(f"✅ {cleared_count} itens removidos do cache")

    def handle_validate_setup(self, options):
        """Valida setup completo do sistema de IA"""
        self.stdout.write("✅ VALIDAÇÃO COMPLETA DO SETUP")
        
        validation_steps = [
            ("Configuração OpenAI", self._validate_openai_config),
            ("Modelos de dados", self._validate_data_models),
            ("Serviços de IA", self._validate_ai_services),
            ("Cache configurado", self._validate_cache_setup),
            ("Dados de teste", self._validate_test_data),
        ]
        
        passed = 0
        total = len(validation_steps)
        
        for step_name, validator in validation_steps:
            self.stdout.write(f"\n🔍 {step_name}:")
            try:
                success, message = validator()
                if success:
                    self.stdout.write(f"  ✅ {message}")
                    passed += 1
                else:
                    self.stdout.write(self.style.ERROR(f"  ❌ {message}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Erro: {e}"))
        
        # Resultado final
        self.stdout.write(f"\n🎯 RESULTADO: {passed}/{total} validações passaram")
        
        if passed == total:
            self.stdout.write(self.style.SUCCESS("🎉 Sistema totalmente configurado!"))
        else:
            self.stdout.write(self.style.WARNING("⚠️ Alguns problemas encontrados. Verifique acima."))

    # Métodos auxiliares

    def _get_test_user(self, user_id=None):
        """Obtém usuário para teste"""
        if user_id:
            try:
                return User.objects.get(id=user_id)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"❌ Usuário {user_id} não encontrado")
                )
                return None
        
        # Buscar usuário com perfil e sessões
        user = User.objects.filter(
            userprofile__isnull=False,
            workoutsession__isnull=False
        ).first()
        
        if not user:
            self.stdout.write(
                self.style.ERROR("❌ Nenhum usuário com perfil e sessões encontrado")
            )
            return None
        
        return user

    def _show_setup_help(self):
        """Mostra ajuda de configuração"""
        self.stdout.write("\n💡 COMO CONFIGURAR:")
        self.stdout.write("1. Obtenha uma API key em: https://platform.openai.com/api-keys")
        self.stdout.write("2. Adicione no arquivo .env:")
        self.stdout.write("   OPENAI_API_KEY=sua_chave_aqui")
        self.stdout.write("3. Reinicie o servidor Django")

    def _show_workout_details(self, workout):
        """Mostra detalhes do treino gerado"""
        exercises = workout.get('exercises', [])
        self.stdout.write(f"  Exercícios ({len(exercises)}):")
        for ex in exercises[:3]:  # Mostrar apenas os 3 primeiros
            self.stdout.write(f"    • {ex.get('name', 'N/A')} ({ex.get('sets', 0)} séries)")

    def _show_analysis_details(self, analysis):
        """Mostra detalhes da análise"""
        strengths = analysis.get('strengths', [])
        if strengths:
            self.stdout.write(f"  Pontos fortes: {', '.join(strengths[:2])}")

    def _validate_openai_config(self):
        """Valida configuração OpenAI"""
        if not settings.OPENAI_API_KEY:
            return False, "API Key não configurada"
        
        ai_service = AIService()
        if not ai_service.is_available:
            return False, "Serviço não disponível"
        
        return True, "Configuração OK"

    def _validate_data_models(self):
        """Valida modelos de dados"""
        from apps.recommendations.models import Recommendation
        
        # Verificar se as tabelas existem
        try:
            User.objects.first()
            UserProfile.objects.first()
            WorkoutSession.objects.first()
            Recommendation.objects.first()
        except Exception as e:
            return False, f"Erro nos modelos: {e}"
        
        return True, "Modelos de dados OK"

    def _validate_ai_services(self):
        """Valida serviços de IA"""
        try:
            ai_service = AIService()
            recommendation_engine = RecommendationEngine()
            
            if not hasattr(ai_service, 'generate_personalized_workout_plan'):
                return False, "Método de geração de treino não encontrado"
            
            return True, "Serviços de IA OK"
            
        except Exception as e:
            return False, f"Erro nos serviços: {e}"

    def _validate_cache_setup(self):
        """Valida configuração de cache"""
        try:
            cache.set('test_key', 'test_value', 10)
            value = cache.get('test_key')
            cache.delete('test_key')
            
            if value != 'test_value':
                return False, "Cache não funcionando corretamente"
            
            return True, "Cache funcionando"
            
        except Exception as e:
            return False, f"Erro no cache: {e}"

    def _validate_test_data(self):
        """Valida dados de teste"""
        users_count = User.objects.count()
        profiles_count = UserProfile.objects.count()
        
        if users_count < 1:
            return False, "Nenhum usuário de teste encontrado"
        
        if profiles_count < 1:
            return False, "Nenhum perfil de usuário encontrado"
        
        return True, f"{users_count} usuários, {profiles_count} perfis"