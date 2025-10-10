// Provider CORRIGIDO para gerenciar dados de relatórios
// Localização: lib/providers/reports_provider.dart

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

      // CARREGAR HISTÓRICO PRIMEIRO (sequencial)
      await _loadWorkoutHistory();
      
      // Depois carregar stats e peso em paralelo
      await Future.wait([
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
      
      print('📦 Resposta COMPLETA do histórico:');
      print('   Tipo: ${response.runtimeType}');
      print('   Conteúdo: $response');

      // Tentar diferentes formatos de resposta
      List<dynamic>? sessionsList;
      
      if (response is List) {
        print('✅ Resposta é uma lista direta');
        sessionsList = response;
      } else if (response is Map) {
        print('📋 Resposta é um Map, procurando chaves...');
        print('   Chaves disponíveis: ${response.keys.toList()}');
        
        // Tentar diferentes chaves possíveis
        sessionsList = response['results'] ?? 
                      response['sessions'] ?? 
                      response['data'] ??
                      response['history'];
        
        if (sessionsList != null) {
          print('✅ Lista encontrada em: ${response.keys.firstWhere((k) => response[k] == sessionsList)}');
        }
      }

      if (sessionsList == null || sessionsList.isEmpty) {
        print('⚠️ Nenhuma sessão encontrada no histórico');
        _historyError = 'Nenhum treino encontrado';
        _workoutHistory = [];
        return;
      }

      print('📊 Processando ${sessionsList.length} sessões...');

      _workoutHistory = sessionsList
          .map((json) {
            try {
              return WorkoutHistoryModel.fromJson(json);
            } catch (e, stackTrace) {
              print('❌ ERRO ao parsear workout: $e');
              return null;
            }
          })
          .whereType<WorkoutHistoryModel>()
          .toList();

      // Ordenar do mais recente para o mais antigo
      _workoutHistory.sort((a, b) => b.date.compareTo(a.date));
      
      print('✅ ${_workoutHistory.length} treinos carregados com sucesso');
      
    } on ApiException catch (e) {
      print('❌ Erro API ao buscar histórico: ${e.message}');
      _historyError = _getErrorMessage(e);
      _workoutHistory = [];
    } catch (e, stackTrace) {
      print('❌ Erro GERAL ao buscar histórico: $e');
      _historyError = 'Erro ao buscar histórico de treinos';
      _workoutHistory = [];
    } finally {
      _isLoadingHistory = false;
    }
  }

  // ============================================================
  // CARREGAR ESTATÍSTICAS - AGORA COM EXERCÍCIOS!
  // ============================================================

  Future<void> _loadStats() async {
    _isLoadingStats = true;
    _statsError = null;
    
    try {
      print('📊 Buscando estatísticas...');
      
      // SEMPRE calcular localmente com os dados completos
      _calculateStatsLocally();
      
    } catch (e) {
      print('❌ Erro ao calcular stats: $e');
      _statsError = 'Erro ao buscar estatísticas';
      _calculateStatsLocally();
    } finally {
      _isLoadingStats = false;
    }
  }

  void _calculateStatsLocally() {
    print('🧮 Calculando estatísticas localmente...');
    
    if (_workoutHistory.isEmpty) {
      print('⚠️ Nenhum treino no histórico para calcular stats');
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
    print('📊 Contabilizando grupos musculares...');
    
    for (var workout in _workoutHistory) {
      if (workout.muscleGroups.isEmpty) continue;
      
      for (var muscle in workout.muscleGroups) {
        muscleGroupFrequency[muscle] = (muscleGroupFrequency[muscle] ?? 0) + 1;
      }
    }

    // ⭐ NOVO: Calcular exercício favorito
    // Se o modelo tem exercícios, contar; senão usar nome do treino
    final exerciseFrequency = <String, int>{};
    
    for (var workout in _workoutHistory) {
      // Usar o nome do treino como exercício principal
      exerciseFrequency[workout.workoutName] = 
          (exerciseFrequency[workout.workoutName] ?? 0) + 1;
    }

    String favoriteExercise = 'Nenhum';
    int favoriteExerciseCount = 0;

    if (exerciseFrequency.isNotEmpty) {
      final favorite = exerciseFrequency.entries.reduce((a, b) => 
          a.value > b.value ? a : b);
      favoriteExercise = favorite.key;
      favoriteExerciseCount = favorite.value;
    }

    print('⭐ Exercício favorito: $favoriteExercise ($favoriteExerciseCount x)');

    _stats = WorkoutStats(
      totalWorkouts: totalWorkouts,
      totalDuration: totalDuration,
      totalCalories: totalCalories,
      activeDays: activeDays,
      currentStreak: _calculateStreak(),
      workoutsByCategory: workoutsByCategory,
      muscleGroupFrequency: muscleGroupFrequency,
      favoriteExercise: favoriteExercise,
      favoriteExerciseCount: favoriteExerciseCount,
      averageDuration: totalWorkouts > 0 ? totalDuration / totalWorkouts : 0,
    );

    print('✅ Stats calculadas com sucesso');
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
        if (streak == 0 && currentDate.day == DateTime.now().day) {
          break;
        }
        if (streak > 0) {
          break;
        }
        currentDate = currentDate.subtract(const Duration(days: 1));
        if (DateTime.now().difference(currentDate).inDays > 7) {
          break;
        }
      }
    }

    return streak;
  }

  // ============================================================
  // CARREGAR HISTÓRICO DE PESO - USANDO LOCAL STORAGE
  // ============================================================

  Future<void> _loadWeightHistory() async {
  _isLoadingWeight = true;
  _weightError = null;
  
  try {
    print('⚖️ Carregando histórico de peso da API...');
    
    // CORREÇÃO 1: Usando o endpoint correto do Django
    final response = await ApiService.get('/users/weight_history/'); 
    
    List<dynamic> weightList = [];
    
    // CORREÇÃO 2: Lógica para encontrar a lista de pesos
    if (response is List) {
      weightList = response;
      print('✅ Lista encontrada como resposta direta.');
    } else if (response is Map) {
      if (response['results'] is List) {
         weightList = response['results'] as List<dynamic>;
         print('✅ Lista encontrada na chave "results".');
      } 
      // ⭐ NOVO: Tratar a chave "weights" que a API está usando
      else if (response['weights'] is List) {
         weightList = response['weights'] as List<dynamic>;
         print('✅ Lista encontrada na chave "weights".');
      }
    }

    if (weightList.isNotEmpty) {
      // Mapeia os JSONs para a classe WeightEntry
      _weightHistory = weightList
          .map((json) {
            try {
              return WeightEntry.fromJson(json); 
            } catch (e) {
              print('❌ ERRO ao parsear WeightEntry: $e, JSON: $json');
              return null;
            }
          })
          .whereType<WeightEntry>() // Remove quaisquer entradas nulas
          .toList();

      // Ordena por data e confirma
      _weightHistory.sort((a, b) => a.date.compareTo(b.date)); 
      print('✅ ${_weightHistory.length} registros de peso carregados com sucesso.');
    } else {
      _weightHistory = [];
      print('⚠️ Nenhuma lista de peso válida encontrada na resposta da API.');
    }
    
    _weightError = null; // Sucesso no carregamento
    
  } on ApiException catch (e) {
    print('⚠️ Erro API ao carregar peso: ${e.message}');
    _weightError = 'Histórico de peso não disponível';
    _weightHistory = [];
  } catch (e) {
    print('❌ Erro GERAL ao buscar histórico de peso: $e');
    _weightError = 'Erro ao buscar histórico de peso';
    _weightHistory = [];
  } finally {
    _isLoadingWeight = false;
    // Não precisa chamar notifyListeners() aqui, pois loadReports() fará isso.
  }
}

  // ============================================================
  // ATUALIZAR PESO
  // ============================================================

  Future<bool> updateWeight(double weight) async {
    try {
      print('⚖️ Atualizando peso: $weight kg');
      
      // Tentar enviar ao backend
      try {
        await ApiService.post('/users/set_weight_info/', {
          'peso_atual': weight,
        });
        print('✅ Peso salvo no backend');
      } catch (e) {
        print('⚠️ Não foi possível salvar no backend, salvando localmente');
      }

      // Adicionar/atualizar no histórico local
      final now = DateTime.now();
      
      // Verificar se já existe entrada de hoje
      final todayIndex = _weightHistory.indexWhere((w) =>
        w.date.year == now.year &&
        w.date.month == now.month &&
        w.date.day == now.day
      );

      if (todayIndex >= 0) {
        _weightHistory[todayIndex] = WeightEntry(
          date: now,
          weight: weight,
        );
        print('✅ Peso atualizado para hoje');
      } else {
        _weightHistory.add(WeightEntry(
          date: now,
          weight: weight,
        ));
        print('✅ Novo registro de peso adicionado');
      }

      // Ordenar por data
      _weightHistory.sort((a, b) => a.date.compareTo(b.date));

      notifyListeners();
      return true;
      
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

// ============================================================
// MODELOS
// ============================================================

class WeightEntry {
  final DateTime date;
  final double weight;

  WeightEntry({
    required this.date,
    required this.weight,
  });

  factory WeightEntry.fromJson(Map<String, dynamic> json) {
    return WeightEntry(
      date: DateTime.parse(json['date']),
      weight: (json['weight'] as num).toDouble(),
    );
  }
}

class WorkoutStats {
  final int totalWorkouts;
  final int totalDuration;
  final int totalCalories;
  final int activeDays;
  final int currentStreak;
  final Map<String, int> workoutsByCategory;
  final Map<String, int> muscleGroupFrequency;
  final String favoriteExercise;
  final int favoriteExerciseCount;
  final double averageDuration;

  WorkoutStats({
    required this.totalWorkouts,
    required this.totalDuration,
    required this.totalCalories,
    required this.activeDays,
    required this.currentStreak,
    required this.workoutsByCategory,
    required this.muscleGroupFrequency,
    required this.favoriteExercise,
    required this.favoriteExerciseCount,
    required this.averageDuration,
  });

  String get formattedTotalDuration {
    final hours = (totalDuration / 60).floor();
    final minutes = totalDuration % 60;
    if (hours > 0) {
      return '${hours}h${minutes > 0 ? minutes : ''}';
    }
    return '${minutes}min';
  }

  String get mostTrainedMuscleGroup {
    if (muscleGroupFrequency.isEmpty) return 'Nenhum';
    return muscleGroupFrequency.entries
        .reduce((a, b) => a.value > b.value ? a : b)
        .key;
  }

  factory WorkoutStats.fromJson(Map<String, dynamic> json) {
    return WorkoutStats(
      totalWorkouts: json['totalWorkouts'] ?? 0,
      totalDuration: json['totalDuration'] ?? 0,
      totalCalories: json['totalCalories'] ?? 0,
      activeDays: json['activeDays'] ?? 0,
      currentStreak: json['currentStreak'] ?? 0,
      workoutsByCategory: Map<String, int>.from(json['workoutsByCategory'] ?? {}),
      muscleGroupFrequency: Map<String, int>.from(json['muscleGroupFrequency'] ?? {}),
      favoriteExercise: json['favoriteExercise'] ?? 'Nenhum',
      favoriteExerciseCount: json['favoriteExerciseCount'] ?? 0,
      averageDuration: (json['averageDuration'] ?? 0).toDouble(),
    );
  }
}