/// Provider para gerenciar dados de relatórios
/// Localização: lib/providers/reports_provider.dart

import 'package:flutter/material.dart';
import '../models/workout_history_model.dart';
import '../service/api_service.dart';

class ReportsProvider extends ChangeNotifier {
  List<WorkoutHistoryModel> _workoutHistory = [];
  WorkoutStats? _stats;
  List<WeightEntry> _weightHistory = [];
  bool _isLoading = false;
  bool _isLoadingHistory = false;
  bool _isLoadingStats = false;
  bool _isLoadingWeight = false;
  String? _errorMessage;
  String? _historyError;
  String? _statsError;
  String? _weightError;
  int _selectedPeriod = 30;

  // Getters
  List<WorkoutHistoryModel> get workoutHistory => _workoutHistory;
  WorkoutStats? get stats => _stats;
  List<WeightEntry> get weightHistory => _weightHistory;
  bool get isLoading => _isLoading;
  bool get isLoadingHistory => _isLoadingHistory;
  bool get isLoadingStats => _isLoadingStats;
  bool get isLoadingWeight => _isLoadingWeight;
  String? get errorMessage => _errorMessage;
  String? get historyError => _historyError;
  String? get statsError => _statsError;
  String? get weightError => _weightError;
  int get selectedPeriod => _selectedPeriod;

  WorkoutHistoryModel? get lastWorkout {
    if (_workoutHistory.isEmpty) return null;
    return _workoutHistory.first;
  }

  List<WorkoutHistoryModel> get thisWeekWorkouts {
    final now = DateTime.now();
    final startOfWeek = now.subtract(Duration(days: now.weekday - 1));
    
    return _workoutHistory.where((workout) {
      return workout.date.isAfter(startOfWeek) && workout.date.isBefore(now);
    }).toList();
  }

  Map<int, int> get weeklyFrequency {
    final frequency = <int, int>{};
    for (int i = 0; i < 7; i++) {
      frequency[i] = 0;
    }

    for (var workout in thisWeekWorkouts) {
      final weekday = workout.date.weekday - 1;
      frequency[weekday] = (frequency[weekday] ?? 0) + 1;
    }

    return frequency;
  }

  List<bool> get activityCalendar {
    final calendar = List.generate(28, (index) => false);
    final now = DateTime.now();

    for (int i = 0; i < 28; i++) {
      final date = now.subtract(Duration(days: 27 - i));
      final hasWorkout = _workoutHistory.any((workout) =>
        workout.date.year == date.year &&
        workout.date.month == date.month &&
        workout.date.day == date.day
      );
      calendar[i] = hasWorkout;
    }

    return calendar;
  }

  // ============================================================
  // CARREGAR TODOS OS RELATÓRIOS
  // ============================================================

  Future<void> loadReports() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      print('📊 Carregando relatórios...');

      // Carregar em paralelo para melhor performance
      await Future.wait([
        _loadWorkoutHistory(),
        _loadStats(),
        _loadWeightHistory(),
      ]);

      _isLoading = false;
      
      // Se todos falharam, mostra erro geral
      if (_historyError != null && _statsError != null && _weightError != null) {
        _errorMessage = 'Não foi possível carregar os dados. Verifique sua conexão.';
      }
      
      notifyListeners();

      print('✅ Relatórios carregados');
    } catch (e) {
      print('❌ Erro geral ao carregar relatórios: $e');
      _errorMessage = 'Erro ao carregar dados: $e';
      _isLoading = false;
      notifyListeners();
    }
  }

  // ============================================================
  // CARREGAR HISTÓRICO DE TREINOS
  // ============================================================

  Future<void> _loadWorkoutHistory() async {
    _isLoadingHistory = true;
    _historyError = null;
    
    try {
      print('📥 Buscando histórico de treinos...');
      
      final response = await ApiService.get('/sessions/history/');
      
      print('📦 Resposta do histórico: $response');

      // Tentar diferentes formatos de resposta
      List<dynamic>? sessionsList;
      
      if (response is List) {
        sessionsList = response;
      } else if (response is Map) {
        // Tentar diferentes chaves possíveis
        sessionsList = response['results'] ?? 
                      response['sessions'] ?? 
                      response['data'] ??
                      response['history'];
      }

      if (sessionsList == null) {
        print('⚠️ Formato de resposta inesperado para histórico');
        _historyError = 'Formato de dados inválido';
        _workoutHistory = [];
        return;
      }

      _workoutHistory = sessionsList
          .map((json) {
            try {
              return WorkoutHistoryModel.fromJson(json);
            } catch (e) {
              print('⚠️ Erro ao parsear workout: $e');
              print('JSON problemático: $json');
              return null;
            }
          })
          .whereType<WorkoutHistoryModel>()
          .toList();

      // Ordenar do mais recente para o mais antigo
      _workoutHistory.sort((a, b) => b.date.compareTo(a.date));
      
      print('✅ ${_workoutHistory.length} treinos carregados');
      
    } on ApiException catch (e) {
      print('❌ Erro API ao buscar histórico: ${e.message}');
      _historyError = _getErrorMessage(e);
      _workoutHistory = [];
    } catch (e) {
      print('❌ Erro ao buscar histórico: $e');
      _historyError = 'Erro ao buscar histórico de treinos';
      _workoutHistory = [];
    } finally {
      _isLoadingHistory = false;
    }
  }

  // ============================================================
  // CARREGAR ESTATÍSTICAS
  // ============================================================

  Future<void> _loadStats() async {
    _isLoadingStats = true;
    _statsError = null;
    
    try {
      print('📊 Buscando estatísticas...');
      
      final response = await ApiService.get('/analytics/');
      
      print('📦 Resposta das stats: $response');

      // Tentar parsear as stats do backend
      try {
        _stats = WorkoutStats.fromJson(response);
        print('✅ Stats carregadas do backend');
      } catch (e) {
        print('⚠️ Erro ao parsear stats do backend: $e');
        print('📝 Calculando stats localmente...');
        _calculateStatsLocally();
      }
      
    } on ApiException catch (e) {
      if (e.statusCode == 404) {
        print('⚠️ Endpoint de analytics não existe, calculando localmente');
        _calculateStatsLocally();
      } else {
        print('❌ Erro API ao buscar stats: ${e.message}');
        _statsError = _getErrorMessage(e);
        _calculateStatsLocally();
      }
    } catch (e) {
      print('❌ Erro ao buscar stats: $e');
      _statsError = 'Erro ao buscar estatísticas';
      _calculateStatsLocally();
    } finally {
      _isLoadingStats = false;
    }
  }

  void _calculateStatsLocally() {
    print('🧮 Calculando estatísticas localmente...');
    
    if (_workoutHistory.isEmpty) {
      _stats = WorkoutStats(
        totalWorkouts: 0,
        totalDuration: 0,
        totalCalories: 0,
        activeDays: 0,
        currentStreak: 0,
        workoutsByCategory: {},
        muscleGroupFrequency: {},
        favoriteExercise: 'Nenhum',
        favoriteExerciseCount: 0,
        averageDuration: 0,
      );
      return;
    }

    final totalWorkouts = _workoutHistory.length;
    final totalDuration = _workoutHistory.fold<int>(0, (sum, w) => sum + w.duration);
    final totalCalories = _workoutHistory.fold<int>(0, (sum, w) => sum + w.calories);
    
    // Contar dias únicos
    final uniqueDays = <String>{};
    for (var workout in _workoutHistory) {
      uniqueDays.add('${workout.date.year}-${workout.date.month}-${workout.date.day}');
    }
    final activeDays = uniqueDays.length;

    // Treinos por categoria
    final workoutsByCategory = <String, int>{};
    for (var workout in _workoutHistory) {
      workoutsByCategory[workout.category] = (workoutsByCategory[workout.category] ?? 0) + 1;
    }

    // Frequência de grupos musculares
    final muscleGroupFrequency = <String, int>{};
    for (var workout in _workoutHistory) {
      for (var muscle in workout.muscleGroups) {
        muscleGroupFrequency[muscle] = (muscleGroupFrequency[muscle] ?? 0) + 1;
      }
    }

    _stats = WorkoutStats(
      totalWorkouts: totalWorkouts,
      totalDuration: totalDuration,
      totalCalories: totalCalories,
      activeDays: activeDays,
      currentStreak: _calculateStreak(),
      workoutsByCategory: workoutsByCategory,
      muscleGroupFrequency: muscleGroupFrequency,
      favoriteExercise: _stats?.favoriteExercise ?? 'Nenhum',
      favoriteExerciseCount: _stats?.favoriteExerciseCount ?? 0,
      averageDuration: totalWorkouts > 0 ? totalDuration / totalWorkouts : 0,
    );

    print('✅ Stats calculadas: ${_stats?.totalWorkouts} treinos');
  }

  int _calculateStreak() {
    if (_workoutHistory.isEmpty) return 0;

    int streak = 0;
    var currentDate = DateTime.now();
    currentDate = DateTime(currentDate.year, currentDate.month, currentDate.day);

    while (true) {
      final hasWorkout = _workoutHistory.any((w) =>
        w.date.year == currentDate.year &&
        w.date.month == currentDate.month &&
        w.date.day == currentDate.day
      );

      if (hasWorkout) {
        streak++;
        currentDate = currentDate.subtract(const Duration(days: 1));
      } else {
        // Se é o primeiro dia e não tem treino, streak é 0
        if (streak == 0 && currentDate.day == DateTime.now().day) {
          break;
        }
        // Se já começou a contar e não tem treino, quebrou o streak
        if (streak > 0) {
          break;
        }
        // Pula um dia de descanso
        currentDate = currentDate.subtract(const Duration(days: 1));
        if (DateTime.now().difference(currentDate).inDays > 7) {
          break; // Não procurar mais de 7 dias atrás
        }
      }
    }

    return streak;
  }

  // ============================================================
  // CARREGAR HISTÓRICO DE PESO
  // ============================================================

  Future<void> _loadWeightHistory() async {
    _isLoadingWeight = true;
    _weightError = null;
    
    try {
      print('⚖️ Buscando histórico de peso...');
      
      // CORREÇÃO: Endpoint não existe ainda no backend
      // Por enquanto, apenas limpa o histórico
      print('⚠️ Endpoint de peso não implementado no backend ainda');
      _weightHistory = [];
      _weightError = 'Histórico de peso não disponível';
      
      // TODO: Quando o endpoint for criado no backend, descomentar:
      /*
      final response = await ApiService.get('/users/weight_history/');
      
      if (response['weights'] != null) {
        _weightHistory = (response['weights'] as List)
            .map((json) => WeightEntry.fromJson(json))
            .toList();
            
        _weightHistory.sort((a, b) => a.date.compareTo(b.date));
        print('✅ ${_weightHistory.length} registros de peso carregados');
      }
      */
      
    } on ApiException catch (e) {
      if (e.statusCode == 404) {
        print('⚠️ Endpoint de peso não existe (404)');
        _weightError = 'Histórico de peso não disponível';
      } else {
        print('❌ Erro API ao buscar peso: ${e.message}');
        _weightError = _getErrorMessage(e);
      }
      _weightHistory = [];
    } catch (e) {
      print('❌ Erro ao buscar histórico de peso: $e');
      _weightError = 'Erro ao buscar histórico de peso';
      _weightHistory = [];
    } finally {
      _isLoadingWeight = false;
    }
  }

  // ============================================================
  // ATUALIZAR PESO
  // ============================================================

  Future<bool> updateWeight(double weight) async {
    try {
      print('⚖️ Atualizando peso: $weight kg');
      
      // Usar o endpoint que existe: /users/set_weight_info/
      await ApiService.post('/users/set_weight_info/', {
        'peso_atual': weight,
      });

      // Adicionar ao histórico local
      _weightHistory.add(WeightEntry(
        date: DateTime.now(),
        weight: weight,
      ));

      // Ordenar por data
      _weightHistory.sort((a, b) => a.date.compareTo(b.date));

      notifyListeners();
      
      print('✅ Peso atualizado com sucesso');
      return true;
      
    } on ApiException catch (e) {
      print('❌ Erro API ao atualizar peso: ${e.message}');
      return false;
    } catch (e) {
      print('❌ Erro ao atualizar peso: $e');
      return false;
    }
  }

  // ============================================================
  // HELPERS
  // ============================================================

  String _getErrorMessage(ApiException e) {
    switch (e.statusCode) {
      case 401:
        return 'Sessão expirada. Faça login novamente.';
      case 403:
        return 'Sem permissão para acessar estes dados.';
      case 404:
        return 'Dados não encontrados.';
      case 500:
        return 'Erro no servidor. Tente novamente mais tarde.';
      default:
        return e.message;
    }
  }

  void setPeriod(int days) {
    _selectedPeriod = days;
    notifyListeners();
    // TODO: Implementar filtro no backend quando disponível
    // loadReports(); // Recarregar com novo período
  }

  Future<void> refresh() async {
    await loadReports();
  }

  void clearData() {
    _workoutHistory = [];
    _stats = null;
    _weightHistory = [];
    _errorMessage = null;
    _historyError = null;
    _statsError = null;
    _weightError = null;
    notifyListeners();
  }

  // ============================================================
  // DADOS MOCK (APENAS PARA DESENVOLVIMENTO/TESTE)
  // ============================================================

  void loadMockData() {
    print('📦 Carregando dados mock para desenvolvimento...');

    final now = DateTime.now();
    
    _workoutHistory = List.generate(17, (index) {
      return WorkoutHistoryModel(
        id: index + 1,
        workoutName: [
          'Peito e Tríceps',
          'Costas e Bíceps',
          'Pernas',
          'Ombros e Abdômen',
          'Cardio'
        ][index % 5],
        date: now.subtract(Duration(days: index * 2)),
        duration: 45 + (index % 4) * 10,
        calories: 250 + (index % 3) * 50,
        category: ['Força', 'Cardio', 'Hipertrofia'][index % 3],
        muscleGroups: [
          ['Peito', 'Tríceps'],
          ['Costas', 'Bíceps'],
          ['Pernas'],
          ['Ombros', 'Abdômen'],
          ['Cardio']
        ][index % 5],
        exercisesCompleted: 8,
        totalExercises: 10,
        completed: true,
      );
    });

    _calculateStatsLocally();

    _weightHistory = List.generate(7, (index) {
      return WeightEntry(
        date: now.subtract(Duration(days: index * 7)),
        weight: 70.0 + index * 1.5,
      );
    }).reversed.toList();

    notifyListeners();
    print('✅ Dados mock carregados');
  }
}