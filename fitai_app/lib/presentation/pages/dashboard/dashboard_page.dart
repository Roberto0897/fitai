import 'package:flutter/material.dart';
import '../../../core/router/app_router.dart';
import 'package:google_fonts/google_fonts.dart';
import '../workouts/workouts_page.dart';
import 'package:provider/provider.dart';
import '../../../providers/user_profile_provider.dart';
import '../../../providers/dashboard_provider.dart';
import '../../../service/api_service.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({Key? key}) : super(key: key);

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  bool _isLoggingOut = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      // Carrega o perfil do usuário e dados do dashboard
      context.read<UserProfileProvider>().loadProfile();
      context.read<DashboardProvider>().loadDashboard();
    });
  }

  Future<void> _performLogout() async {
    if (_isLoggingOut) return;
    
    setState(() {
      _isLoggingOut = true;
    });

    try {
      debugPrint('🚀 DASHBOARD: Iniciando logout...');
      await AppRouter.logout();
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Logout realizado com sucesso'),
            backgroundColor: Colors.green,
            duration: Duration(seconds: 2),
          ),
        );
      }
      
    } catch (e) {
      debugPrint('❌ DASHBOARD: Erro no logout: $e');
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erro ao fazer logout: $e'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoggingOut = false;
        });
      }
    }
  }

  Future<void> _refreshData() async {
    await Future.wait([
      context.read<UserProfileProvider>().loadProfile(),
      context.read<DashboardProvider>().loadDashboard(),
    ]);
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;

    return Scaffold(
      backgroundColor: const Color(0xFF1A1A1A),
      body: Consumer2<UserProfileProvider, DashboardProvider>(
        builder: (context, userProvider, dashboardProvider, child) {
          // Mostra loading apenas se ambos estão carregando e não tem dados
          if (userProvider.isLoading && dashboardProvider.isLoading &&
              !userProvider.hasUserData && !dashboardProvider.hasData) {
            return const Center(
              child: CircularProgressIndicator(color: Color(0xFF00BCD4)),
            );
          }

          return RefreshIndicator(
            onRefresh: _refreshData,
            color: const Color(0xFF00BCD4),
            backgroundColor: const Color(0xFF2A2A2A),
            child: SafeArea(
              child: SizedBox(
                width: size.width,
                height: size.height,
                child: Column(
                  children: [
                    Expanded(
                      child: SingleChildScrollView(
                        physics: const AlwaysScrollableScrollPhysics(),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _buildHeader(userProvider),
                            const SizedBox(height: 32),
                            _buildStatsCards(dashboardProvider),
                            const SizedBox(height: 32),
                            _buildTodayWorkoutCard(dashboardProvider),
                            const SizedBox(height: 24),
                            _buildActionCardsGrid(dashboardProvider),
                            const SizedBox(height: 16),
                          ],
                        ),
                      ),
                    ),
                    _buildBottomNavigation(),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildHeader(UserProfileProvider provider) {
    final userName = provider.nome.split(' ')[0];
    
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              RichText(
                text: TextSpan(
                  style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w300),
                  children: [
                    const TextSpan(
                      text: 'Olá, ',
                      style: TextStyle(color: Colors.white),
                    ),
                    TextSpan(
                      text: '$userName!',
                      style: const TextStyle(
                        color: Color(0xFF00BCD4),
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 4),
              const Text(
                'Pronto para treinar hoje?',
                style: TextStyle(
                  color: Color(0xFF9E9E9E),
                  fontSize: 17,
                ),
              ),
            ],
          ),
          Row(
            children: [
              Text(
                'FitAI',
                style: GoogleFonts.jockeyOne(
                  color: const Color(0xFF00BCD4),
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(width: 16),
              GestureDetector(
                onTap: _performLogout,
                child: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF2A2A2A),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: _isLoggingOut
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(
                              Color(0xFF00BCD4),
                            ),
                          ),
                        )
                      : const Icon(
                          Icons.logout,
                          color: Color(0xFF9E9E9E),
                          size: 20,
                        ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatsCards(DashboardProvider provider) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildStatCircle(
            value: provider.totalWorkouts.toString(),
            label: 'Treinos',
            isLoading: provider.isLoading,
          ),
          _buildStatCircle(
            value: provider.activeDays.toString(),
            label: 'Dias ativos',
            isLoading: provider.isLoading,
          ),
          _buildStatCircle(
            value: provider.weeklyGoalDisplay,
            label: 'Meta semanal',
            isLoading: provider.isLoading,
          ),
        ],
      ),
    );
  }

  Widget _buildStatCircle({
    required String value,
    required String label,
    required bool isLoading,
  }) {
    return Column(
      children: [
        Container(
          width: 100,
          height: 100,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(
              color: const Color(0xFF424242),
              width: 3,
            ),
            color: const Color(0xFF2A2A2A),
          ),
          child: Center(
            child: isLoading
                ? const SizedBox(
                    width: 24,
                    height: 24,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(
                        Color(0xFF00BCD4),
                      ),
                    ),
                  )
                : Text(
                    value,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          label,
          style: const TextStyle(
            color: Color(0xFF9E9E9E),
            fontSize: 11,
          ),
        ),
      ],
    );
  }

  Widget _buildTodayWorkoutCard(DashboardProvider provider) {
    final hasWorkout = provider.hasRecommendedWorkout;
    final workoutName = provider.getRecommendedWorkoutName();
    final workoutId = provider.getRecommendedWorkoutId();

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: const Color(0xFF2A2A2A),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: const Color(0xFF00BCD4),
            width: 1,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(
                  Icons.fitness_center,
                  color: Color(0xFF00BCD4),
                  size: 20,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Sugestão Inteligente da FitAI',
                        style: TextStyle(
                          color: Color(0xFF9E9E9E),
                          fontSize: 18,
                        ),
                      ),
                      const SizedBox(height: 4),
                      if (provider.isLoading)
                        const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(
                              Color(0xFF00BCD4),
                            ),
                          ),
                        )
                      else
                        Text(
                          workoutName,
                          style: const TextStyle(
                            fontFamily: 'JockeyOne',
                            fontSize: 28,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                            letterSpacing: 1,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: hasWorkout && workoutId != null
                    ? () async {
                        try {
                          debugPrint('🔍 Carregando treino recomendado ID: $workoutId');
                          
                          // Buscar detalhes completos do treino
                          final response = await ApiService.getWorkoutDetail(workoutId);
                          
                          debugPrint('📦 Resposta completa: $response');
                          
                          // 🔥 CORRIGIDO: Backend retorna dentro de "workout"
                          final workoutDetails = response['workout'] ?? response;
                          
                          debugPrint('✅ Detalhes do treino: ${workoutDetails['name']}');
                          
                          // Validar dados essenciais
                          if (workoutDetails['id'] == null) {
                            throw Exception('ID do treino não encontrado na resposta');
                          }
                          
                          // Contar exercícios corretamente
                          int exerciseCount = 0;
                          
                          // Verificar se tem campo 'exercises' na raiz da resposta
                          if (response['exercises'] != null && response['exercises'] is List) {
                            exerciseCount = (response['exercises'] as List).length;
                          } 
                          // Ou se tem no workoutDetails
                          else if (workoutDetails['exercises'] != null) {
                            if (workoutDetails['exercises'] is List) {
                              exerciseCount = (workoutDetails['exercises'] as List).length;
                            } else if (workoutDetails['exercises'] is int) {
                              exerciseCount = workoutDetails['exercises'];
                            }
                          }
                          // Ou se tem 'total_exercises'
                          else if (response['total_exercises'] != null) {
                            exerciseCount = response['total_exercises'];
                          }
                          
                          debugPrint('📊 Total de exercícios: $exerciseCount');
                          
                          // Garantir que valores numéricos sejam int
                          final id = workoutDetails['id'] is int 
                              ? workoutDetails['id'] 
                              : int.tryParse(workoutDetails['id'].toString()) ?? 0;
                          
                          final duration = workoutDetails['estimated_duration'] is int
                              ? workoutDetails['estimated_duration']
                              : int.tryParse(workoutDetails['estimated_duration']?.toString() ?? '0') ?? 0;
                          
                          final calories = workoutDetails['calories_estimate'] is int
                              ? workoutDetails['calories_estimate']
                              : int.tryParse(workoutDetails['calories_estimate']?.toString() ?? '0') ?? 0;
                          
                          // Criar modelo de treino
                          final workout = WorkoutModel(
                            id: id,
                            name: workoutDetails['name'] ?? 'Treino sem nome',
                            description: workoutDetails['description'] ?? '',
                            duration: duration,
                            exercises: exerciseCount,
                            difficulty: workoutDetails['difficulty_level'] ?? 'Iniciante',
                            category: workoutDetails['workout_type'] ?? 'Geral',
                            calories: calories,
                          );
                          
                          debugPrint('✅ Modelo criado: ${workout.name} (ID: ${workout.id}, ${workout.exercises} exercícios)');
                          
                          if (mounted) {
                            AppRouter.goToWorkoutDetail(workout: workout);
                          }
                        } catch (e, stackTrace) {
                          debugPrint('❌ Erro ao carregar treino: $e');
                          debugPrint('Stack trace: $stackTrace');
                          
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text('Erro ao carregar treino: ${e.toString()}'),
                                backgroundColor: Colors.red,
                                duration: const Duration(seconds: 4),
                                action: SnackBarAction(
                                  label: 'Ver Treinos',
                                  textColor: Colors.white,
                                  onPressed: () {
                                    AppRouter.goToWorkouts();
                                  },
                                ),
                              ),
                            );
                          }
                        }
                      }
                    : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF00BCD4),
                  foregroundColor: const Color(0xFF1A1A1A),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  disabledBackgroundColor: const Color(0xFF424242),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.play_arrow, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      hasWorkout ? 'Começar' : 'Sem treino disponível',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionCardsGrid(DashboardProvider provider) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: IntrinsicHeight(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Expanded(
              child: Column(
                children: [
                  _buildProgressCard(),
                  const SizedBox(height: 12),
                  _buildHistoryCard(provider),
                ],
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildMyWorkoutsCard(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProgressCard() {
  return Container(
    padding: const EdgeInsets.all(20),
    decoration: BoxDecoration(
      color: const Color(0xFF2A2A2A),
      borderRadius: BorderRadius.circular(16),
      border: Border.all(
        color: const Color(0xFF00BCD4),
        width: 1.5,
      ),
    ),
    child: Column(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: const Color(0xFF00BCD4),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                Icons.auto_awesome,
                color: Colors.white,
                size: 20,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Assistente IA',
                    style: GoogleFonts.jockeyOne(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  Text(
                    'Personalize seu treino',
                    style: GoogleFonts.jockeyOne(
                      color: Colors.grey[400],
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        
        // 🔥 BOTÃO 1: GERAR NOVO TREINO
        SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            onPressed: () {
              // 🔥 PASSAR CONTEXTO PARA O CHATBOT
              AppRouter.goToChatBot(
                initialContext: 'workout_generation',
                initialMessage: 'Olá! Gostaria de criar um treino personalizado baseado no meu perfil.',
              );
            },
            icon: const Icon(Icons.add_circle_outline, size: 20),
            label: Text(
              'Gerar novo treino',
              style: GoogleFonts.jockeyOne(
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF00BCD4),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 12),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
        ),
        const SizedBox(height: 10),
      ],
    ),
  );
}

  Widget _buildMyWorkoutsCard() {
    return GestureDetector(
      onTap: () {
        AppRouter.goToWorkouts();
      },
      child: ConstrainedBox(
        constraints: const BoxConstraints(
          maxWidth: 350,
          maxHeight: 220,
        ),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: const Color(0xFF00BCD4),
              width: 1.5,
            ),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: Stack(
              fit: StackFit.expand,
              children: [
                Image.asset(
                  "images/mulherCapa.png",
                  fit: BoxFit.cover,
                  alignment: Alignment.center,
                ),
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: Text(
                    'Meus Treinos',
                    style: GoogleFonts.jockeyOne(
                      color: Colors.white,
                      fontSize: 17,
                      fontWeight: FontWeight.w500,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHistoryCard(DashboardProvider provider) {
    return Flexible(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF2A2A2A),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: const Color(0xFF00BCD4),
            width: 1.5,
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: const Color(0xFF00BCD4).withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.lightbulb_outline,
                    color: Color(0xFF00BCD4),
                    size: 18,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Recomendações IA',
                    style: GoogleFonts.jockeyOne(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Expanded(
              child: Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFF1A1A1A),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: const Color(0xFF00BCD4).withOpacity(0.3),
                    width: 1,
                  ),
                ),
                child: provider.isLoading
                    ? const Center(
                        child: SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(
                              Color(0xFF00BCD4),
                            ),
                          ),
                        ),
                      )
                    : Row(
                        children: [
                          const Icon(
                            Icons.fitness_center,
                            color: Color(0xFF00BCD4),
                            size: 16,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              provider.aiRecommendation,
                              style: GoogleFonts.jockeyOne(
                                color: Colors.white,
                                fontSize: 13,
                                fontWeight: FontWeight.w400,
                              ),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
              ),
            ),
            const SizedBox(height: 6),
            Text(
              provider.daysSinceLastWorkoutText,
              style: GoogleFonts.jockeyOne(
                color: Colors.grey[500],
                fontSize: 11,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBottomNavigation() {
    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFF2A2A2A),
        border: Border(
          top: BorderSide(
            color: Color(0xFF424242),
            width: 1,
          ),
        ),
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 12),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildNavItem('Inicio', Icons.home, true),
              _buildNavItem('Treinos', Icons.fitness_center, false),
              _buildNavItem('Relatórios', Icons.bar_chart, false),
              _buildNavItem('Chatbot', Icons.chat_bubble_outline, false),
              _buildNavItem('Perfil', Icons.person, false),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(String label, IconData icon, bool isActive) {
    return GestureDetector(
      onTap: () {
        if (label == 'Inicio') {
          // Já está no dashboard
        } else if (label == 'Treinos') {
          AppRouter.goToWorkouts();
        } else if (label == 'Relatórios') {
          AppRouter.goToReports();
        } else if (label == 'Chatbot') {
          AppRouter.goToChatBot();
        } else if (label == 'Perfil') {
          AppRouter.goToProfile();
        }
      },
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            color: isActive ? const Color(0xFF00BCD4) : const Color(0xFF9E9E9E),
            size: 24,
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(
              color: isActive ? const Color(0xFF00BCD4) : const Color(0xFF9E9E9E),
              fontSize: 10,
            ),
          ),
        ],
      ),
    );
  }
}