import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/router/app_router.dart';
import 'widgets/dashboard_widgets.dart';

class DashboardPage extends StatelessWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header Section
              _buildHeader(context),
              const SizedBox(height: 24),
              
              // Personal Info Cards
              _buildPersonalInfoSection(context),
              const SizedBox(height: 24),
              
              // Quick Actions
              _buildQuickActionsSection(context),
              const SizedBox(height: 24),
              
              // Recommended Workouts
              _buildRecommendedWorkoutsSection(context),
              const SizedBox(height: 80), // Espaço para bottom navigation
            ],
          ),
        ),
      ),
      bottomNavigationBar: _buildBottomNavigation(context),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Olá, José!',
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Hoje é um ótimo dia para treinar',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
        Container(
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(12),
          ),
          child: IconButton(
            icon: const Icon(Icons.notifications_outlined),
            color: AppColors.primary,
            onPressed: () => _showComingSoon(context, 'Notificações'),
          ),
        ),
        const SizedBox(width: 8),
        Container(
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(12),
          ),
          child: IconButton(
            icon: const Icon(Icons.logout),
            color: AppColors.primary,
            onPressed: () => _showLogoutDialog(context),
          ),
        ),
      ],
    );
  }

  Widget _buildPersonalInfoSection(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Suas Métricas',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: MetricCard(
                icon: Icons.monitor_weight,
                label: 'Peso',
                value: '82.5',
                unit: 'kg',
                change: '-2.3kg',
                isPositive: true,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: MetricCard(
                icon: Icons.height,
                label: 'Altura',
                value: '1.75',
                unit: 'm',
                change: null,
                isPositive: null,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        MetricCard(
          icon: Icons.analytics,
          label: 'IMC',
          value: '26.9',
          unit: '',
          change: 'Normal',
          isPositive: true,
          isWide: true,
        ),
      ],
    );
  }

  Widget _buildQuickActionsSection(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Ações Rápidas',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: ActionCard(
                icon: Icons.play_arrow,
                title: 'Iniciar Treino',
                subtitle: 'Comece agora',
                gradient: AppColors.primaryGradient,
                onTap: () => _showComingSoon(context, 'Iniciar Treino'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: ActionCard(
                icon: Icons.chat,
                title: 'Chat IA',
                subtitle: 'Converse comigo',
                gradient: const LinearGradient(
                  colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
                ),
                onTap: () => _showComingSoon(context, 'Chat IA'),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildRecommendedWorkoutsSection(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Treinos Recomendados',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            TextButton(
              onPressed: () => _showComingSoon(context, 'Ver Todos'),
              child: const Text('Ver todos'),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Column(
          children: [
            WorkoutCard(
              title: 'Full Body - Iniciante',
              duration: '45 min',
              exercises: '8 exercícios',
              difficulty: 'Iniciante',
              onTap: () => _showComingSoon(context, 'Full Body'),
            ),
            const SizedBox(height: 12),
            WorkoutCard(
              title: 'Cardio HIIT',
              duration: '30 min',
              exercises: '6 exercícios',
              difficulty: 'Intermediário',
              onTap: () => _showComingSoon(context, 'Cardio HIIT'),
            ),
            const SizedBox(height: 12),
            WorkoutCard(
              title: 'Força - Peito e Tríceps',
              duration: '50 min',
              exercises: '10 exercícios',
              difficulty: 'Avançado',
              onTap: () => _showComingSoon(context, 'Força'),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildBottomNavigation(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.surface,
        border: Border(
          top: BorderSide(color: AppColors.card, width: 0.5),
        ),
      ),
      child: BottomNavigationBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        type: BottomNavigationBarType.fixed,
        selectedItemColor: AppColors.primary,
        unselectedItemColor: AppColors.textHint,
        currentIndex: 0,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home),
            label: 'Início',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.fitness_center),
            label: 'Treinos',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.chat),
            label: 'Chat',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.analytics),
            label: 'Progresso',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person),
            label: 'Perfil',
          ),
        ],
        onTap: (index) {
          switch (index) {
            case 0:
              break; // Já estamos na home
            case 1:
             AppRouter.goToWorkouts();
              break;
            case 2:
              _showComingSoon(context, 'Chat');
              break;
            case 3:
              _showComingSoon(context, 'Progresso');
              break;
            case 4:
              _showComingSoon(context, 'Perfil');
              break;
          }
        },
      ),
    );
  }

  void _showComingSoon(BuildContext context, String feature) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('$feature será implementado em breve!'),
        behavior: SnackBarBehavior.floating,
        backgroundColor: AppColors.primary,
      ),
    );
  }

  void _showLogoutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text('Confirmar Logout'),
        content: const Text('Deseja realmente sair da sua conta?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              AppRouter.logout();
            },
            child: const Text('Sair'),
          ),
        ],
      ),
    );
  }
}