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

      // NOVO: Carregar recomendação inteligente
      context.read<DashboardProvider>().loadSmartRecommendation();
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

      // NOVO: Recarregar recomendação ao fazer pull-to-refresh
      context.read<DashboardProvider>().loadSmartRecommendation(),
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
  // ✅ CORREÇÃO: Verificar se tem qualquer tipo de recomendação (workout OU descanso)
  final hasRecommendation = provider.hasSmartRecommendation;
  final analysis = provider.analysisData;
  final workout = provider.smartRecommendation;
  
  // ✅ NOVO: Detectar se é recomendação de descanso
  final shouldRest = analysis['recommendation_type'] == 'rest';
  final isOffSchedule = analysis['recommendation_type'] == 'reschedule';
  
  // ✅ Definir título e ícone baseado no tipo
  String title;
  IconData iconData;
  Color iconColor;
  
  if (shouldRest) {
    title = 'Dia de Descanso';
    iconData = Icons.bedtime;
    iconColor = const Color(0xFF9C27B0); // Roxo
  } else if (isOffSchedule) {
    title = 'Fora do Cronograma';
    iconData = Icons.schedule;
    iconColor = const Color(0xFFFFC107); // Amarelo
  } else if (hasRecommendation) {
    title = 'Recomendação Inteligente';
    iconData = Icons.auto_awesome;
    iconColor = const Color(0xFF00BCD4); // Azul
  } else {
    title = 'Aguardando análise';
    iconData = Icons.fitness_center;
    iconColor = const Color(0xFF9E9E9E); // Cinza
  }
  
  final workoutName = hasRecommendation && !shouldRest && !isOffSchedule
      ? (workout['name'] ?? 'Treino Recomendado')
      : shouldRest
          ? 'Você merece descansar!'
          : isOffSchedule
              ? 'Não é seu dia de treino'
              : 'Nenhuma recomendação ainda';
  
  final workoutId = hasRecommendation && !shouldRest && !isOffSchedule
      ? workout['id']
      : null;

  return Padding(
    padding: const EdgeInsets.symmetric(horizontal: 20),
    child: Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: const Color(0xFF2A2A2A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: shouldRest
              ? const Color(0xFF9C27B0)
              : isOffSchedule
                  ? const Color(0xFFFFC107)
                  : hasRecommendation
                      ? const Color(0xFF00BCD4)
                      : const Color(0xFF424242),
          width: 1.5,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: iconColor.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  iconData,
                  color: iconColor,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        color: Color(0xFF9E9E9E),
                        fontSize: 14,
                      ),
                    ),
                    const SizedBox(height: 4),
                    if (provider.isLoading)
                      Row(
                        children: const [
                          SizedBox(
                            height: 16,
                            width: 16,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              valueColor: AlwaysStoppedAnimation<Color>(
                                Color(0xFF00BCD4),
                              ),
                            ),
                          ),
                          SizedBox(width: 8),
                          Text(
                            'Carregando...',
                            style: TextStyle(
                              color: Colors.white70,
                              fontSize: 16,
                            ),
                          ),
                        ],
                      )
                    else
                      Text(
                        workoutName,
                        style: TextStyle(
                          fontFamily: 'JockeyOne',
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                          color: hasRecommendation || shouldRest || isOffSchedule
                              ? Colors.white
                              : const Color(0xFF9E9E9E),
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
          
          // ✅ NOVO: Mostrar análise para TODOS os tipos de recomendação
          if ((hasRecommendation || shouldRest || isOffSchedule) && !provider.isLoading) ...[
            const SizedBox(height: 16),
            
            // Razão da recomendação
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: shouldRest
                    ? const Color(0xFF9C27B0).withOpacity(0.1)
                    : isOffSchedule
                        ? const Color(0xFFFFC107).withOpacity(0.1)
                        : const Color(0xFF00BCD4).withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: shouldRest
                      ? const Color(0xFF9C27B0).withOpacity(0.3)
                      : isOffSchedule
                          ? const Color(0xFFFFC107).withOpacity(0.3)
                          : const Color(0xFF00BCD4).withOpacity(0.3),
                  width: 1,
                ),
              ),
              child: Row(
                children: [
                  Text(
                    provider.getRecommendationEmoji(),
                    style: const TextStyle(fontSize: 18),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      provider.getFormattedReason(),
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 13,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 12),
            
            // ✅ NOVO: Fatores de personalização (para todos os tipos)
            if (provider.personalizationFactors.isNotEmpty) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.05),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: Colors.white.withOpacity(0.1),
                    width: 1,
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: const [
                        Icon(
                          Icons.info_outline,
                          color: Color(0xFF00BCD4),
                          size: 14,
                        ),
                        SizedBox(width: 6),
                        Text(
                          'Fatores considerados:',
                          style: TextStyle(
                            color: Color(0xFF9E9E9E),
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    ...provider.personalizationFactors.map((factor) {
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              '• ',
                              style: TextStyle(
                                color: Color(0xFF00BCD4),
                                fontSize: 12,
                              ),
                            ),
                            Expanded(
                              child: Text(
                                factor,
                                style: const TextStyle(
                                  color: Colors.white70,
                                  fontSize: 11,
                                ),
                              ),
                            ),
                          ],
                        ),
                      );
                    }).toList(),
                  ],
                ),
              ),
              const SizedBox(height: 12),
            ],
            
            // Informações do treino (apenas se não for descanso)
            if (!shouldRest && !isOffSchedule) ...[
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  if (workout['difficulty_level'] != null)
                    _buildInfoChip(
                      icon: '📊',
                      label: workout['difficulty_level'],
                    ),
                  if (workout['estimated_duration'] != null)
                    _buildInfoChip(
                      icon: '⏱️',
                      label: '${workout['estimated_duration']} min',
                    ),
                  if (workout['calories_estimate'] != null)
                    _buildInfoChip(
                      icon: '🔥',
                      label: '~${workout['calories_estimate']} kcal',
                    ),
                ],
              ),
            ],
          ],
          
          // Mensagem quando não há recomendação
          if (!hasRecommendation && !shouldRest && !isOffSchedule && !provider.isLoading) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFF1A1A1A),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: const Color(0xFF424242),
                  width: 1,
                ),
              ),
              child: Row(
                children: const [
                  Icon(
                    Icons.info_outline,
                    color: Color(0xFF9E9E9E),
                    size: 18,
                  ),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Complete alguns treinos para receber recomendações personalizadas',
                      style: TextStyle(
                        color: Color(0xFF9E9E9E),
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
          
          const SizedBox(height: 16),
          
          // ✅ NOVO: Botão adaptado ao tipo de recomendação
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: shouldRest || isOffSchedule
                  ? () {
                      // Se é descanso ou fora do cronograma, ir para treinos disponíveis
                      AppRouter.goToWorkouts();
                    }
                  : hasRecommendation && workoutId != null
                      ? () async {
                          // Lógica original para carregar treino
                          try {
                            debugPrint('🔍 Carregando treino recomendado ID: $workoutId');
                            
                            final response = await ApiService.getWorkoutDetail(workoutId);
                            final workoutDetails = response['workout'] ?? response;
                            
                            if (workoutDetails['id'] == null) {
                              throw Exception('ID do treino não encontrado');
                            }
                            
                            int exerciseCount = 0;
                            if (response['exercises'] != null && response['exercises'] is List) {
                              exerciseCount = (response['exercises'] as List).length;
                            } else if (workoutDetails['exercises'] != null) {
                              if (workoutDetails['exercises'] is List) {
                                exerciseCount = (workoutDetails['exercises'] as List).length;
                              } else if (workoutDetails['exercises'] is int) {
                                exerciseCount = workoutDetails['exercises'];
                              }
                            } else if (response['total_exercises'] != null) {
                              exerciseCount = response['total_exercises'];
                            }
                            
                            final id = workoutDetails['id'] is int 
                                ? workoutDetails['id'] 
                                : int.tryParse(workoutDetails['id'].toString()) ?? 0;
                            
                            final duration = workoutDetails['estimated_duration'] is int
                                ? workoutDetails['estimated_duration']
                                : int.tryParse(workoutDetails['estimated_duration']?.toString() ?? '0') ?? 0;
                            
                            final calories = workoutDetails['calories_estimate'] is int
                                ? workoutDetails['calories_estimate']
                                : int.tryParse(workoutDetails['calories_estimate']?.toString() ?? '0') ?? 0;
                            
                            final workoutModel = WorkoutModel(
                              id: id,
                              name: workoutDetails['name'] ?? 'Treino sem nome',
                              description: workoutDetails['description'] ?? '',
                              duration: duration,
                              exercises: exerciseCount,
                              difficulty: workoutDetails['difficulty_level'] ?? 'Iniciante',
                              category: workoutDetails['workout_type'] ?? 'Geral',
                              calories: calories,
                            );
                            
                            if (mounted) {
                              AppRouter.goToWorkoutDetail(workout: workoutModel);
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
                                ),
                              );
                            }
                          }
                        }
                      : () {
                          AppRouter.goToWorkouts();
                        },
              style: ElevatedButton.styleFrom(
                backgroundColor: shouldRest
                    ? const Color(0xFF9C27B0)
                    : isOffSchedule
                        ? const Color(0xFFFFC107)
                        : hasRecommendation
                            ? const Color(0xFF00BCD4)
                            : const Color(0xFF424242),
                foregroundColor: shouldRest || isOffSchedule || hasRecommendation
                    ? Colors.white
                    : const Color(0xFF9E9E9E),
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    shouldRest
                        ? Icons.self_improvement
                        : isOffSchedule
                            ? Icons.calendar_today
                            : hasRecommendation
                                ? Icons.play_arrow
                                : Icons.search,
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    shouldRest
                        ? 'Aproveitar o descanso'
                        : isOffSchedule
                            ? 'Ver dias preferidos'
                            : hasRecommendation
                                ? 'Começar Treino'
                                : 'Ver Treinos Disponíveis',
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
// Widget auxiliar para chips de informação
Widget _buildInfoChip({required String icon, required String label}) {
  return Container(
    padding: const EdgeInsets.symmetric(
      horizontal: 8,
      vertical: 4,
    ),
    decoration: BoxDecoration(
      color: Colors.white.withOpacity(0.05),
      borderRadius: BorderRadius.circular(6),
      border: Border.all(
        color: Colors.white.withOpacity(0.1),
        width: 1,
      ),
    ),
    child: Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          icon,
          style: const TextStyle(fontSize: 12),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: const TextStyle(
            color: Colors.white70,
            fontSize: 11,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
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
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ✅ CABEÇALHO
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
          const SizedBox(height: 12),
          
          // ✅ CONTEÚDO PRINCIPAL (SEM SCROLL - APENAS FLEXIBLE)
          Flexible(
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
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
                  : Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        // ✅ ÍCONE + TÍTULO COMPLETO
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Icon(
                              Icons.fitness_center,
                              color: Color(0xFF00BCD4),
                              size: 18,
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                provider.aiRecommendationType == 'rest'
                                    ? 'Dia de Descanso'
                                    : provider.aiRecommendationType == 'motivation'
                                        ? 'Motivação do Dia'
                                        : provider.aiRecommendationType == 'active_recovery'
                                            ? 'Recuperação Ativa'
                                            : 'Seu Treino de Hoje',
                                style: GoogleFonts.jockeyOne(
                                  color: Colors.white,
                                  fontSize: 14,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        
                        // ✅ MENSAGEM (COM maxLines PARA EVITAR CRESCIMENTO EXCESSIVO)
                        Flexible(
                          child: Text(
                            provider.aiRecommendation.isNotEmpty
                                ? provider.aiRecommendation
                                : 'Mantenha a consistência nos treinos!',
                            style: GoogleFonts.jockeyOne(
                              color: Colors.white70,
                              fontSize: 13,
                              fontWeight: FontWeight.w400,
                              height: 1.5,
                            ),
                            maxLines: 3,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        
                        // ✅ EMOJI + CONTEXTO
                        if (provider.hasDailyAIRecommendation) ...[
                          const SizedBox(height: 10),
                          Row(
                            children: [
                              Text(
                                provider.aiRecommendationEmoji,
                                style: const TextStyle(fontSize: 20),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  provider.aiRecommendationType == 'rest'
                                      ? 'Aproveite para recuperação'
                                      : provider.aiRecommendationType == 'active_recovery'
                                          ? 'Recuperação leve e eficaz'
                                          : provider.aiRecommendationType == 'workout'
                                              ? 'Hora de treinar'
                                              : 'Continue motivado',
                                  style: GoogleFonts.jockeyOne(
                                    color: Colors.white54,
                                    fontSize: 12,
                                    fontStyle: FontStyle.italic,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ],
                    ),
            ),
          ),
          
          const SizedBox(height: 10),
          
          // ✅ RODAPÉ DINÂMICO
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
            decoration: BoxDecoration(
              color: provider.workoutStatusBadge['color'].withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: provider.workoutStatusBadge['color'].withOpacity(0.3),
                width: 1.5,
              ),
            ),
            child: Row(
              children: [
                Text(
                  provider.workoutStatusBadge['icon'],
                  style: const TextStyle(fontSize: 16),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    provider.workoutStatusBadge['text'],
                    style: GoogleFonts.jockeyOne(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
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