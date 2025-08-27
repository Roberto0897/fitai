from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from apps.recommendations.services.recommendation_engine import RecommendationEngine
from apps.recommendations.models import Recommendation
from apps.users.models import UserProfile


class Command(BaseCommand):
    help = 'Gera recomendações personalizadas para todos os usuários ativos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--algorithm',
            type=str,
            default='hybrid',
            choices=['ai_personalized', 'content_based', 'collaborative', 'hybrid'],
            help='Algoritmo a ser usado para gerar recomendações'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=5,
            help='Número de recomendações por usuário'
        )
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Gerar apenas para usuários ativos nos últimos 30 dias'
        )
        parser.add_argument(
            '--force-refresh',
            action='store_true',
            help='Forçar geração mesmo se já existem recomendações recentes'
        )

    def handle(self, *args, **options):
        algorithm = options['algorithm']
        limit = options['limit']
        active_only = options['active_only']
        force_refresh = options['force_refresh']
        
        self.stdout.write(
            self.style.HTTP_INFO(
                f'🤖 Iniciando geração de recomendações...\n'
                f'Algoritmo: {algorithm}\n'
                f'Limite por usuário: {limit}\n'
                f'Apenas usuários ativos: {active_only}\n'
            )
        )
        
        # Buscar usuários
        users_query = User.objects.filter(is_active=True)
        
        if active_only:
            # Filtrar usuários com atividade nos últimos 30 dias
            thirty_days_ago = timezone.now() - timedelta(days=30)
            from apps.workouts.models import WorkoutSession
            active_user_ids = WorkoutSession.objects.filter(
                created_at__gte=thirty_days_ago
            ).values_list('user_id', flat=True).distinct()
            users_query = users_query.filter(id__in=active_user_ids)
        
        users = list(users_query)
        total_users = len(users)
        
        if total_users == 0:
            self.stdout.write(
                self.style.WARNING('Nenhum usuário encontrado com os critérios especificados.')
            )
            return
        
        self.stdout.write(f'📊 Processando {total_users} usuários...\n')
        
        # Inicializar motor de recomendações
        recommendation_engine = RecommendationEngine()
        
        # Contadores
        successful_generations = 0
        skipped_users = 0
        error_count = 0
        total_recommendations_created = 0
        
        # Processar cada usuário
        for i, user in enumerate(users, 1):
            try:
                self.stdout.write(f'👤 [{i}/{total_users}] Processando {user.username}...', ending=' ')
                
                # Verificar se já tem recomendações recentes
                if not force_refresh:
                    recent_recommendations = Recommendation.objects.filter(
                        usuario=user,
                        data_geracao__gte=timezone.now() - timedelta(days=1)
                    ).count()
                    
                    if recent_recommendations >= limit:
                        self.stdout.write(self.style.WARNING('PULADO (já tem recomendações recentes)'))
                        skipped_users += 1
                        continue
                
                # Gerar recomendações
                recommendations = recommendation_engine.generate_recommendations(
                    user=user,
                    algorithm=algorithm,
                    limit=limit
                )
                
                if recommendations:
                    successful_generations += 1
                    total_recommendations_created += len(recommendations)
                    self.stdout.write(
                        self.style.SUCCESS(f'SUCESSO ({len(recommendations)} recomendações)')
                    )
                else:
                    self.stdout.write(self.style.WARNING('NENHUMA RECOMENDAÇÃO'))
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'ERRO: {str(e)}'))
        
        # Relatório final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('🎉 GERAÇÃO DE RECOMENDAÇÕES CONCLUÍDA!'))
        self.stdout.write('='*50)
        self.stdout.write(f'📈 ESTATÍSTICAS FINAIS:')
        self.stdout.write(f'  • Total de usuários processados: {total_users}')
        self.stdout.write(f'  • Gerações bem-sucedidas: {successful_generations}')
        self.stdout.write(f'  • Usuários pulados: {skipped_users}')
        self.stdout.write(f'  • Erros: {error_count}')
        self.stdout.write(f'  • Total de recomendações criadas: {total_recommendations_created}')
        
        if successful_generations > 0:
            avg_recs_per_user = total_recommendations_created / successful_generations
            self.stdout.write(f'  • Média de recomendações por usuário: {avg_recs_per_user:.1f}')
        
        self.stdout.write(f'\n🚀 Algoritmo utilizado: {algorithm}')
        
        # Relatório de qualidade das recomendações
        if total_recommendations_created > 0:
            self._show_quality_report(algorithm)
        
        self.stdout.write('\n✅ Comando executado com sucesso!')

    def _show_quality_report(self, algorithm):
        """Mostra relatório de qualidade das recomendações geradas"""
        try:
            from django.db.models import Avg, Count
            
            # Recomendações criadas hoje
            today_recommendations = Recommendation.objects.filter(
                data_geracao__date=timezone.now().date(),
                algoritmo_utilizado=algorithm
            )
            
            # Estatísticas de qualidade
            avg_confidence = today_recommendations.aggregate(
                avg_conf=Avg('score_confianca')
            )['avg_conf'] or 0
            
            # Distribuição por algoritmo
            algorithm_distribution = today_recommendations.values('algoritmo_utilizado').annotate(
                count=Count('id')
            )
            
            self.stdout.write(f'\n📊 RELATÓRIO DE QUALIDADE:')
            self.stdout.write(f'  • Score médio de confiança: {avg_confidence:.2f}')
            
            for item in algorithm_distribution:
                self.stdout.write(f'  • {item["algoritmo_utilizado"]}: {item["count"]} recomendações')
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Erro no relatório de qualidade: {e}'))

    def _check_ai_availability(self):
        """Verifica se a IA está disponível"""
        from apps.recommendations.services.ai_service import AIService
        ai_service = AIService()
        
        if ai_service.is_available:
            self.stdout.write(self.style.SUCCESS('🤖 IA (OpenAI) disponível'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  IA não disponível - usando algoritmos de fallback'))