import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../../presentation/pages/login_page.dart';
import '../../core/theme/app_theme.dart';
import '../../presentation/pages/dashboard/dashboard_page.dart';
import '../../presentation/pages/workouts/workouts_page.dart';
import '../../presentation/pages/workouts/workout_detail_page.dart';
import '../../presentation/pages/exercises/exercise_execution_page.dart';
import '../../presentation/pages/register_page.dart';
import '../../presentation/pages/reports/reports_page.dart';
import '../../presentation/pages/chat/chat_bot_page.dart';
import '../../presentation/pages/profile/profile_page.dart';
import '../../service/user_service.dart';
import 'dart:async'; // Para Timer 
import 'package:flutter/foundation.dart'; // Para kDebugMode

/// Rotas da aplicação FITAI
class AppRoutes {
  static const String login = '/login';
  static const String register = '/register';
  static const String dashboard = '/dashboard';
  static const String workouts = '/workouts';
  static const String workoutDetail = '/workout-detail';
  static const String exerciseExecution = '/exercise-execution';
  static const String rest = '/rest';
  static const String reports = '/reports';
  static const String chatbot = '/chatbot';
  static const String profile = '/profile';
}

/// Sistema de roteamento da aplicação FITAI - CORRIGIDO
class AppRouter {
  static GoRouter get router => _router;
  static bool _isRedirecting = false; // Previne loops de redirecionamento

  static final GoRouter _router = GoRouter(
    debugLogDiagnostics: true, // Ative para debug
    initialLocation: AppRoutes.login,
    
    // 🔥 REDIRECT CORRIGIDO - Previne loops infinitos
    redirect: (context, state) async {
      // Prevenir múltiplos redirects simultâneos
      if (_isRedirecting) {
        debugPrint('🔄 ROUTER: Redirect já em andamento, ignorando...');
        return null;
      }

      _isRedirecting = true;

      try {
        // Usar UserService em vez de Firebase direto (fonte única de verdade)
        final isLoggedIn = await UserService.isUserLoggedIn();
        final currentPath = state.uri.path;
        
        debugPrint('🔍 ROUTER: Path atual: $currentPath');
        debugPrint('🔍 ROUTER: Usuário logado: $isLoggedIn');
        
        final isPublicRoute = currentPath == AppRoutes.login || currentPath == AppRoutes.register;
        
        // Usuário logado tentando acessar páginas públicas
        if (isLoggedIn && isPublicRoute) {
          debugPrint('🚀 ROUTER: Usuário logado, redirecionando para dashboard');
          return AppRoutes.dashboard;
        }
        
        // Usuário não logado tentando acessar páginas protegidas
        if (!isLoggedIn && !isPublicRoute) {
          debugPrint('🚀 ROUTER: Usuário não logado, redirecionando para login');
          return AppRoutes.login;
        }
        
        // Não redirecionar
        debugPrint('✅ ROUTER: Mantendo na rota atual: $currentPath');
        return null;
        
      } catch (e) {
        debugPrint('❌ ROUTER: Erro no redirect: $e');
        return AppRoutes.login; // Fallback seguro
      } finally {
        // Pequeno delay para evitar loops
        await Future.delayed(Duration(milliseconds: 100));
        _isRedirecting = false;
      }
    },
    
    // 🔥 AUTH NOTIFIER MELHORADO - Com debounce
    refreshListenable: AuthNotifierImproved(),

    routes: [
      GoRoute(
        path: AppRoutes.login,
        name: 'login',
        builder: (context, state) {
          debugPrint('📱 ROUTER: Construindo LoginPage');
          return const LoginPage();
        },
      ),
      
      GoRoute(
        path: AppRoutes.register,
        name: 'register',
        builder: (context, state) {
          debugPrint('📱 ROUTER: Construindo RegisterPage');
          return const RegisterPageOptimized();
        },
      ),
      
      GoRoute(
        path: AppRoutes.dashboard,
        name: 'dashboard',
        builder: (context, state) {
          debugPrint('📱 ROUTER: Construindo DashboardPage');
          return const DashboardPage();
        },
      ),
      
      GoRoute(
        path: AppRoutes.workouts,
        name: 'workouts',
        builder: (context, state) {
          debugPrint('📱 ROUTER: Construindo WorkoutsPage');
          return const WorkoutsPage();
        },
      ),
      
      GoRoute(
        path: AppRoutes.workoutDetail,
        name: 'workoutDetail',
        builder: (context, state) {
          debugPrint('📱 ROUTER: Construindo WorkoutDetailPage');
          final workout = state.extra as WorkoutModel;
          return WorkoutDetailPage(workout: workout);
        },
      ),

      GoRoute(
      path: AppRoutes.exerciseExecution,
      name: 'exerciseExecution',
      builder: (context, state) {
        debugPrint('📱 ROUTER: Construindo ExerciseExecutionPage');
        final params = state.extra as Map<String, dynamic>;
        return ExerciseExecutionPage(
          exercise: params['exercise'] as ExerciseModel,
          totalExercises: params['totalExercises'] as int,
          currentExerciseIndex: params['currentExerciseIndex'] as int,
          allExercises: params['allExercises'] as List<ExerciseModel>, // ADICIONE
        );
      },
    ),
      
      GoRoute(
        path: AppRoutes.reports,
        name: 'reports',
        builder: (context, state) {
          debugPrint('📱 ROUTER: Construindo ReportsPage');
          return const ReportsPage();
        },
      ),
    
       GoRoute(
        path: AppRoutes.chatbot,
        name: 'chatbot',
        builder: (context, state) {
          debugPrint('📱 ROUTER: Construindo ChatBotPage');
          return const ChatBotPage();
        },
      ),

        GoRoute(
        path: AppRoutes.profile,
        name: 'profile',
        builder: (context, state) {
          debugPrint('📱 ROUTER: Construindo ProfilePage');
          return const ProfilePage();
        },
      ),

    ], // adicione goRoute antes disso
    
    errorBuilder: (context, state) {
      debugPrint('❌ ROUTER: Erro de rota: ${state.error}');
      return const ErrorPage();
    },

    
  );

  // 🔥 MÉTODOS DE NAVEGAÇÃO CORRIGIDOS
  
  static void goToLogin() {
    try {
      _router.go(AppRoutes.login);
      debugPrint('✅ Navegação para Login realizada');
    } catch (e) {
      debugPrint('❌ Erro ao navegar para Login: $e');
    }
  }

  static void goToRegister() {
    try {
      _router.go(AppRoutes.register);
      debugPrint('✅ Navegação para Registro realizada');
    } catch (e) {
      debugPrint('❌ Erro ao navegar para Registro: $e');
    }
  }

  static void goToDashboard() {
    try {
      _router.go(AppRoutes.dashboard);
      debugPrint('✅ Navegação para Dashboard realizada');
    } catch (e) {
      debugPrint('❌ Erro ao navegar para Dashboard: $e');
    }
  }

  static void goToWorkouts() {  
    try {
      _router.go(AppRoutes.workouts);
      debugPrint('✅ Navegação para Workouts realizada');
    } catch (e) {
      debugPrint('❌ Erro ao navegar para Workouts: $e');
    }
  }

  static void goBack() {
    try {
      if (_router.canPop()) {
        _router.pop();
        debugPrint('✅ Navegação de volta realizada');
      } else {
        goToLogin();
        debugPrint('✅ Não pode voltar, indo para login');
      }
    } catch (e) {
      debugPrint('❌ Erro ao navegar de volta: $e');
    }
  }

  // 🔥 LOGOUT CORRIGIDO - Agora faz logout real
  static Future<void> logout() async {
    try {
      debugPrint('🚀 ROUTER: Iniciando processo de logout...');
      
      // 1. Fazer logout real usando UserService
      await UserService.logout();
      
      // 2. Navegar para login (será automático pelo AuthNotifier, mas garantimos)
      _router.go(AppRoutes.login);
      
      debugPrint('✅ Logout completo realizado');
    } catch (e) {
      debugPrint('❌ Erro durante logout: $e');
      // Fallback: ao menos navegar para login
      _router.go(AppRoutes.login);
    }
  }
  
  static void goToWorkoutDetail({required WorkoutModel workout}) {
    try {
      _router.push(AppRoutes.workoutDetail, extra: workout);
      debugPrint('✅ Navegação para Workout Detail realizada - ID: ${workout.id}');
    } catch (e) {
      debugPrint('❌ Erro ao navegar para Workout Detail: $e');
    }
  }
  // Método para debug - verificar estado atual
  static Future<Map<String, dynamic>> getRouterDebugInfo() async {
    final currentLocation = _router.routerDelegate.currentConfiguration.uri.path;
    final isLoggedIn = await UserService.isUserLoggedIn();
    
    return {
      'currentLocation': currentLocation,
      'isLoggedIn': isLoggedIn,
      'canPop': _router.canPop(),
      'isRedirecting': _isRedirecting,
    };
  }
   static void goToExerciseExecution({
    required ExerciseModel exercise,
    required int totalExercises,
    required int currentExerciseIndex,
    required List<ExerciseModel> allExercises,
    int initialWorkoutSeconds = 0,
    bool isFullWorkout = false, // NOVO PARÂMETRO
    int? sessionId,        //  NOVO
    int? workoutId, 
  }) {
    try {
      _router.push(
        AppRoutes.exerciseExecution,
        extra: {
          'exercise': exercise,
          'totalExercises': totalExercises,
          'currentExerciseIndex': currentExerciseIndex,
          'allExercises': allExercises,
          'initialWorkoutSeconds': initialWorkoutSeconds,
          'isFullWorkout': isFullWorkout, // NOVO
          'sessionId': sessionId,        //  NOVO
          'workoutId': workoutId,
        },
      );
      debugPrint('✅ Navegação para Exercise Execution realizada (isFullWorkout: $isFullWorkout)');
    } catch (e) {
      debugPrint('❌ Erro ao navegar para Exercise Execution: $e');
    }
  }
static void goToReports() {
    try {
      _router.go(AppRoutes.reports);
      debugPrint('✅ Navegação para Reports realizada');
    } catch (e) {
      debugPrint('❌ Erro ao navegar para Reports: $e');
    }
  }

    static void goToChatBot() {
    try {
      _router.push(AppRoutes.chatbot);
      debugPrint('✅ Navegação para Chat Bot realizada');
    } catch (e) {
      debugPrint('❌ Erro ao navegar para Chat Bot: $e');
    }
  }

  static void goToProfile() {
    try {
      _router.go(AppRoutes.profile);
      debugPrint('✅ Navegação para Profile realizada');
    } catch (e) {
      debugPrint('❌ Erro ao navegar para Profile: $e');
    }
  }
}

// 🔥 AUTH NOTIFIER MELHORADO - Com debounce para evitar loops
class AuthNotifierImproved extends ChangeNotifier {
  Timer? _debounceTimer;
  User? _lastUser;

  AuthNotifierImproved() {
    FirebaseAuth.instance.authStateChanges().listen((User? user) {
      // Só notificar se realmente mudou
      if (_lastUser?.uid != user?.uid) {
        debugPrint('🔥 AUTH CHANGED: ${user?.uid ?? "logged out"}');
        
        _lastUser = user;
        
        // Debounce para evitar múltiplas notificações rápidas
        _debounceTimer?.cancel();
        _debounceTimer = Timer(Duration(milliseconds: 500), () {
          notifyListeners();
        });
      }
    });
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    super.dispose();
  }
}

// 🔥 PÁGINA DE ERRO MELHORADA
class ErrorPage extends StatelessWidget {
  const ErrorPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Erro - FITAI'),
        backgroundColor: AppColors.background,
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.error_outline,
                size: 80,
                color: AppColors.error,
              ),
              const SizedBox(height: 24),
              const Text(
                'Oops! Algo deu errado',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                'Tente voltar e tentar novamente',
                style: TextStyle(
                  color: AppColors.textSecondary,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),
              ElevatedButton.icon(
                onPressed: () => AppRouter.goToLogin(),
                icon: const Icon(Icons.home),
                label: const Text('Voltar ao Login'),
              ),
              const SizedBox(height: 16),
              // Botão de debug (remover em produção)
              if (kDebugMode)
                TextButton(
                  onPressed: () async {
                    final info = await AppRouter.getRouterDebugInfo();
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Debug: $info')),
                    );
                  },
                  child: const Text('Debug Info'),
                ),
            ],
          ),
        ),
      ),
    );
  }
}