import 'package:flutter/material.dart';
import '../../../core/router/app_router.dart';
import '../../../service/user_service.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_svg/flutter_svg.dart';
import '../workouts/workout_detail_page.dart';
import '../workouts/workouts_page.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({Key? key}) : super(key: key);

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  String userName = 'Ana';
  bool _isLoggingOut = false;

  @override
  void initState() {
    super.initState();
    _loadUserData();
  }

  Future<void> _loadUserData() async {
    try {
      final user = await UserService.getCurrentUser();
      if (user != null && mounted) {
        setState(() {
          userName = user.nome.split(' ')[0];
        });
      }
    } catch (e) {
      debugPrint('Erro ao carregar dados do usuário: $e');
    }
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1A1A1A),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildHeader(),
                    const SizedBox(height: 32),
                    _buildStatsCards(),
                    const SizedBox(height: 32),
                    _buildTodayWorkoutCard(),
                    const SizedBox(height: 24),
                    _buildActionCardsGrid(),
                    const SizedBox(height: 100),
                  ],
                ),
              ),
            ),
            _buildBottomNavigation(),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
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
                  color: Color(0xFF00BCD4),
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

  Widget _buildStatsCards() {
    final stats = [
      {'value': '17', 'label': 'Treinos'},
      {'value': '18', 'label': 'Dias ativos'},
      {'value': '80%', 'label': 'Meta diária'},
    ];

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: stats.map((stat) {
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
                  child: Text(
                    stat['value']!,
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
                stat['label']!,
                style: const TextStyle(
                  color: Color(0xFF9E9E9E),
                  fontSize: 11,
                ),
              ),
            ],
          );
        }).toList(),
      ),
    );
  }

  Widget _buildTodayWorkoutCard() {
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
            const Row(
              children: [
                Icon(
                  Icons.fitness_center,
                  color: Color(0xFF00BCD4),
                  size: 20,
                ),
                SizedBox(width: 12),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Seu treino de hoje',
                      style: TextStyle(
                        color: Color(0xFF9E9E9E),
                        fontSize: 18,
                      ),
                    ),
                    SizedBox(height: 4),
                    Text(
                      'Peito e Triceps',
                      style: TextStyle(
                        fontFamily: 'JockeyOne',
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                        letterSpacing: 1,
                      ),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
               onPressed: () {
               // Criar um workout de exemplo Temporario 
                final workout = WorkoutModel(
                  id: 1,
                  name: 'Push day - Peito e Tríceps',
                  description: 'Treino focado em peito e tríceps para desenvolvimento muscular',
                  duration: 50,
                  exercises: 10,
                  difficulty: 'Avançado',
                  category: 'Força',
                  calories: 320,
                );
                
                AppRouter.goToWorkoutDetail(workout);
              },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF00BCD4),
                  foregroundColor: const Color(0xFF1A1A1A),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.play_arrow, size: 20),
                    SizedBox(width: 8),
                    Text(
                      'Começar',
                      style: TextStyle(
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

Widget _buildActionCardsGrid() {
  return Padding(
    padding: const EdgeInsets.symmetric(horizontal: 20),
    child: IntrinsicHeight( // Adicione isso
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch, // Mude para stretch
        children: [
          // Coluna esquerda: Progresso e Histórico
          Expanded(
            child: Column(
              children: [
                _buildProgressCard(),
                const SizedBox(height: 12),
                _buildHistoryCard(),
              ],
            ),
          ),
          const SizedBox(width: 12),
          // Coluna direita: Meus Treinos (altura total)
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
      height: 160,
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
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
           Text(
            'Progresso',
            style:GoogleFonts.jockeyOne(
              color: Colors.white,
              fontSize: 17,
              fontWeight: FontWeight.w500,
              
            ),
          ),
          // Círculo de progresso
          Center(
            child: SizedBox(
              width: 70,
              height: 70,
              child: Stack(
                children: [
                  Center(
                    child: SizedBox(
                      width: 70,
                      height: 70,
                      child: CircularProgressIndicator(
                        value: 0.0,
                        strokeWidth: 4,
                        backgroundColor: const Color(0xFF404040),
                        valueColor: const AlwaysStoppedAnimation<Color>(
                          Color(0xFF00BCD4),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          // Texto
        ],
      ),
    );
  }

Widget _buildMyWorkoutsCard() {
   return GestureDetector(
    onTap: () {
      AppRouter.goToWorkouts();
      // Ou use context.push('/meus-treinos')
      
    },
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
          // Imagem de fundo (PRIMEIRO - embaixo)
          SvgPicture.asset(
            "assets/images/secaoMeusTreinos.svg",
            fit: BoxFit.cover,
            alignment: Alignment.center,
          ),
          
         
          
          // Texto (TERCEIRO - por cima de tudo)
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
  );
}
Widget _buildHistoryCard() {
  return Container(
    height: 160,
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
      mainAxisAlignment: MainAxisAlignment.spaceBetween,  // Centraliza tudo
      crossAxisAlignment: CrossAxisAlignment.stretch,  // ← ADICIONE isso
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          
          child: SvgPicture.asset(
            "assets/images/iconeHistotico.svg",
            width: 50,
            height: 50,
          ),
        ),
        const SizedBox(height: 10),
        Text(
          'Histórico de treinos',
          style: GoogleFonts.jockeyOne(
            color: Colors.white,
            fontSize: 17,
            fontWeight: FontWeight.w500,
          ),
          textAlign: TextAlign.center,
          overflow: TextOverflow.ellipsis,
        ),
      ],
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
        if (label == 'Treinos') {
          AppRouter.goToWorkouts();
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