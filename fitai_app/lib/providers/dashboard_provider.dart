import 'package:flutter/material.dart';
import '../service/api_service.dart';
import '../models/workout_history_model.dart';
import 'dart:convert';

/// Provider para gerenciar dados do Dashboard
/// ✨ ATUALIZADO: Prioriza treinos gerados pela IA
class DashboardProvider extends ChangeNotifier {
  // ============================================================
  // ESTADO
  // ============================================================
  
  bool _isLoading = false;
  String? _error;
  
  // Estatísticas do usuário
  int _totalWorkouts = 0;
  int _activeDays = 0;
  double _weeklyGoalPercentage = 0.0;
  
  // Treino recomendado do dia (pode vir da IA ou do backend)
  Map<String, dynamic>? _recommendedWorkout;
  bool _isAIRecommendation = false; // Indica se veio da IA
  String? _aiRecommendationReason; // Motivo da recomendação
  
  // 🔥 NOVO: Flag para indicar se é treino GERADO pela IA (não apenas recomendado)
  bool _isAIGeneratedWorkout = false;
  
  // Recomendação IA (mensagem motivacional)
  String? _aiMotivationalMessage;
  int? _daysSinceLastWorkout;
  bool _isLoadingAIRecommendation = false;
  
  // Histórico para cálculos
  List<WorkoutHistoryModel> _workoutHistory = [];
  
  // ============================================================
  // GETTERS
  // ============================================================
  
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get hasData => _totalWorkouts > 0 || _recommendedWorkout != null;
  
  // Estatísticas
  int get totalWorkouts => _totalWorkouts;
  int get activeDays => _activeDays;
  double get weeklyGoalPercentage => _weeklyGoalPercentage;
  String get weeklyGoalDisplay => '${_weeklyGoalPercentage.toStringAsFixed(0)}%';
  
  // Treino recomendado
  Map<String, dynamic>? get recommendedWorkout => _recommendedWorkout;
  bool get hasRecommendedWorkout => _recommendedWorkout != null;
  bool get isAIRecommendation => _isAIRecommendation;
  bool get isAIGeneratedWorkout => _isAIGeneratedWorkout;
  String? get aiRecommendationReason => _aiRecommendationReason;
  
  // Recomendação IA
  String get aiRecommendation => _aiMotivationalMessage ?? 'Mantenha a consistência nos treinos!';
  int get daysSinceLastWorkout => _daysSinceLastWorkout ?? 0;
  bool get isLoadingAIRecommendation => _isLoadingAIRecommendation;
  
  String get daysSinceLastWorkoutText {
    if (_daysSinceLastWorkout == null) return 'Sem dados';
    if (_daysSinceLastWorkout == 0) return 'Treinou hoje!';
    if (_daysSinceLastWorkout == 1) return '1 dia desde último treino';
    return '$_daysSinceLastWorkout dias desde último treino';
  }
  
  // ============================================================
  // MÉTODOS PRINCIPAIS
  // ============================================================
  
  /// Carrega todos os dados do dashboard
  Future<void> loadDashboard() async {
    if (_isLoading) return;
    
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      debugPrint('📊 Carregando dados do dashboard...');
      
      // 1. Carregar histórico de treinos
      await _loadWorkoutHistory();
      
      // 2. Calcular estatísticas localmente
      _calculateStatistics();
      
      // 3. 🔥 NOVO: Buscar último treino gerado pela IA PRIMEIRO
      await _loadLastAIGeneratedWorkout();
      
      // 4. Se não houver treino da IA, buscar recomendado normal
      if (_recommendedWorkout == null) {
        await _loadRecommendedWorkoutWithAI();
      }
      
      // 5. Gerar recomendação IA motivacional (em paralelo, não bloqueia)
      _loadAIMotivationalRecommendation();
      
      _error = null;
      
      debugPrint('✅ Dashboard carregado com sucesso:');
      debugPrint('   Total de treinos: $_totalWorkouts');
      debugPrint('   Dias ativos: $_activeDays');
      debugPrint('   Meta semanal: $_weeklyGoalPercentage%');
      debugPrint('   Treino gerado pela IA: ${_isAIGeneratedWorkout ? "SIM" : "NÃO"}');
      debugPrint('   Recomendação IA: ${_isAIRecommendation ? "SIM" : "NÃO"}');
      
    } catch (e) {
      debugPrint('❌ Erro ao carregar dashboard: $e');
      _error = 'Erro ao carregar dados: $e';
      _setDefaultValues();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  // ============================================================
  // 🔥 NOVO: BUSCAR ÚLTIMO TREINO GERADO PELA IA
  // ============================================================
  
  /// Busca o último treino criado pela IA para o usuário
  Future<void> _loadLastAIGeneratedWorkout() async {
    try {
      debugPrint('🤖 Buscando último treino gerado pela IA...');
      
      // Buscar todos os treinos do usuário
      final response = await ApiService.getWorkouts();
      
      if (response['workouts'] == null || (response['workouts'] as List).isEmpty) {
        debugPrint('ℹ️ Nenhum treino encontrado');
        return;
      }
      
      final allWorkouts = response['workouts'] as List;
      
      // 🔥 FILTRAR: Apenas treinos criados pela IA
      final aiWorkouts = allWorkouts.where((workout) {
        // ✅ Opção 1 (PRINCIPAL): Campo is_recommended do seu backend
        if (workout['is_recommended'] == true) {
          debugPrint('   ✓ Treino ${workout['name']} marcado com is_recommended');
          return true;
        }
        
        // ✅ Opção 2: Campo is_personalized (treinos personalizados do usuário)
        if (workout['is_personalized'] == true) {
          debugPrint('   ✓ Treino ${workout['name']} marcado com is_personalized');
          return true;
        }
        
        // ✅ Opção 3: Tem created_by_user (foi criado por um usuário específico)
        if (workout['created_by_user'] != null) {
          debugPrint('   ✓ Treino ${workout['name']} criado por usuário');
          return true;
        }
        
        // ✅ Opção 4: Descrição contém indicadores de IA
        final description = (workout['description'] ?? '').toString().toLowerCase();
        if (description.contains('gerado pela ia') ||
            description.contains('gerado pela inteligência artificial') ||
            description.contains('criado pela ia') ||
            description.contains('personalizado pela ia') ||
            description.contains('fitai')) {
          debugPrint('   ✓ Treino ${workout['name']} com descrição de IA');
          return true;
        }
        
        return false;
      }).toList();
      
      if (aiWorkouts.isEmpty) {
        debugPrint('ℹ️ Nenhum treino gerado pela IA encontrado');
        return;
      }
      
      // Ordenar por data de criação (mais recente primeiro)
      aiWorkouts.sort((a, b) {
        try {
          final dateA = DateTime.parse(a['created_at'] ?? '');
          final dateB = DateTime.parse(b['created_at'] ?? '');
          return dateB.compareTo(dateA);
        } catch (e) {
          return 0;
        }
      });
      
      // Pegar o mais recente
      final lastAIWorkout = aiWorkouts.first;
      
      // Buscar detalhes completos do treino
      final workoutId = lastAIWorkout['id'];
      final workoutDetails = await ApiService.getWorkoutDetail(workoutId);
      
      _recommendedWorkout = workoutDetails;
      _isAIGeneratedWorkout = true;
      _isAIRecommendation = true;
      _aiRecommendationReason = 'Último treino gerado pela IA para você';
      
      debugPrint('✅ Último treino da IA encontrado: ${_recommendedWorkout!['name']}');
      debugPrint('   ID: $workoutId');
      debugPrint('   Criado em: ${lastAIWorkout['created_at']}');
      
    } catch (e) {
      debugPrint('⚠️ Erro ao buscar treino da IA: $e');
      // Não definir _recommendedWorkout = null aqui, deixa tentar o fallback
    }
  }
  
  // ============================================================
  // CARREGAR HISTÓRICO DE TREINOS
  // ============================================================
  
  Future<void> _loadWorkoutHistory() async {
    try {
      debugPrint('📥 Buscando histórico de treinos...');
      
      final response = await ApiService.get('/sessions/history/');
      
      debugPrint('📦 Resposta do histórico: $response');

      List<dynamic>? sessionsList;
      
      if (response is List) {
        sessionsList = response;
      } else if (response is Map) {
        sessionsList = response['results'] ?? 
                      response['sessions'] ?? 
                      response['data'] ??
                      response['history'];
      }

      if (sessionsList == null) {
        debugPrint('⚠️ Formato de resposta inesperado');
        _workoutHistory = [];
        return;
      }

      _workoutHistory = sessionsList
          .map((json) {
            try {
              return WorkoutHistoryModel.fromJson(json);
            } catch (e) {
              debugPrint('⚠️ Erro ao parsear workout: $e');
              return null;
            }
          })
          .whereType<WorkoutHistoryModel>()
          .toList();

      // Ordenar do mais recente para o mais antigo
      _workoutHistory.sort((a, b) => b.date.compareTo(a.date));
      
      debugPrint('✅ ${_workoutHistory.length} treinos carregados para dashboard');
      
    } catch (e) {
      debugPrint('❌ Erro ao buscar histórico: $e');
      _workoutHistory = [];
    }
  }
  
  // ============================================================
  // CALCULAR ESTATÍSTICAS LOCALMENTE
  // ============================================================
  
  void _calculateStatistics() {
    debugPrint('🧮 Calculando estatísticas...');
    
    if (_workoutHistory.isEmpty) {
      _totalWorkouts = 0;
      _activeDays = 0;
      _weeklyGoalPercentage = 0.0;
      return;
    }

    // Total de treinos
    _totalWorkouts = _workoutHistory.length;
    
    // Contar dias únicos com treinos
    final uniqueDays = <String>{};
    for (var workout in _workoutHistory) {
      uniqueDays.add('${workout.date.year}-${workout.date.month}-${workout.date.day}');
    }
    _activeDays = uniqueDays.length;

    // Meta semanal (últimos 7 dias)
    final now = DateTime.now();
    final sevenDaysAgo = now.subtract(const Duration(days: 7));
    
    final workoutsThisWeek = _workoutHistory.where((workout) {
      return workout.date.isAfter(sevenDaysAgo) && workout.date.isBefore(now);
    }).length;
    
    // Meta de 5 treinos por semana
    const weeklyGoal = 5;
    _weeklyGoalPercentage = ((workoutsThisWeek / weeklyGoal) * 100).clamp(0, 100);
    
    debugPrint('📈 Estatísticas calculadas:');
    debugPrint('   Total: $_totalWorkouts');
    debugPrint('   Dias ativos: $_activeDays');
    debugPrint('   Esta semana: $workoutsThisWeek');
    debugPrint('   Meta: $_weeklyGoalPercentage%');
  }
  
  // ============================================================
  // 🤖 BUSCAR TREINO RECOMENDADO COM IA (FALLBACK)
  // ============================================================
  
  /// Tenta buscar recomendação da IA, com fallback para endpoint normal
  Future<void> _loadRecommendedWorkoutWithAI() async {
    try {
      debugPrint('🤖 Tentando buscar recomendação da IA (fallback)...');
      
      // 🔥 PRIMEIRO: Tentar recomendações de exercícios da IA
      try {
        final aiResponse = await ApiService.getAIExerciseRecommendations();
        
        if (aiResponse['recommendations'] != null && 
            (aiResponse['recommendations'] as List).isNotEmpty) {
          
          final firstRecommendation = (aiResponse['recommendations'] as List).first;
          
          // Verificar se tem workout_id
          if (firstRecommendation['workout_id'] != null) {
            // Buscar detalhes completos do treino
            final workoutId = firstRecommendation['workout_id'];
            final workoutDetails = await ApiService.getWorkoutDetail(workoutId);
            
            _recommendedWorkout = workoutDetails;
            _isAIGeneratedWorkout = false; // É recomendado, não gerado
            _isAIRecommendation = true;
            _aiRecommendationReason = firstRecommendation['reason'] ?? 
                                      'Recomendado com base no seu perfil';
            
            debugPrint('✅ Treino recomendado pela IA: ${_recommendedWorkout!['name']}');
            debugPrint('   Motivo: $_aiRecommendationReason');
            
            return;
          }
        }
      } catch (aiError) {
        debugPrint('⚠️ IA não disponível ou sem recomendações: $aiError');
      }
      
      // 🔥 SEGUNDO: Fallback para endpoint de treinos recomendados normal
      debugPrint('💪 Buscando treino recomendado do backend...');
      
      final response = await ApiService.getRecommendedWorkouts();
      
      if (response['workouts'] != null && (response['workouts'] as List).isNotEmpty) {
        _recommendedWorkout = (response['workouts'] as List).first;
        _isAIGeneratedWorkout = false;
        _isAIRecommendation = false;
        _aiRecommendationReason = null;
        debugPrint('✅ Treino recomendado (backend): ${_recommendedWorkout!['name']}');
        return;
      }
      
      // 🔥 TERCEIRO: Buscar treino diferente do último
      if (_workoutHistory.isNotEmpty) {
        final lastWorkout = _workoutHistory.first;
        
        final workoutsResponse = await ApiService.getWorkouts();
        
        if (workoutsResponse['workouts'] != null) {
          final allWorkouts = workoutsResponse['workouts'] as List;
          
          // Filtrar treinos diferentes do último
          final differentWorkouts = allWorkouts.where((w) {
            final muscleGroups = w['target_muscle_groups'] ?? '';
            return !lastWorkout.muscleGroups.any((m) => 
              muscleGroups.toString().toLowerCase().contains(m.toLowerCase())
            );
          }).toList();
          
          if (differentWorkouts.isNotEmpty) {
            _recommendedWorkout = differentWorkouts.first;
            _isAIGeneratedWorkout = false;
            _isAIRecommendation = false;
            _aiRecommendationReason = null;
            debugPrint('✅ Treino diferente recomendado: ${_recommendedWorkout!['name']}');
            return;
          }
          
          // Se não encontrar diferente, pega qualquer um
          if (allWorkouts.isNotEmpty) {
            _recommendedWorkout = allWorkouts.first;
            _isAIGeneratedWorkout = false;
            _isAIRecommendation = false;
            _aiRecommendationReason = null;
            debugPrint('✅ Treino padrão recomendado: ${_recommendedWorkout!['name']}');
            return;
          }
        }
      }
      
      debugPrint('ℹ️ Nenhum treino recomendado disponível');
      _recommendedWorkout = null;
      _isAIGeneratedWorkout = false;
      _isAIRecommendation = false;
      _aiRecommendationReason = null;
      
    } catch (e) {
      debugPrint('⚠️ Erro ao buscar treino recomendado: $e');
      _recommendedWorkout = null;
      _isAIGeneratedWorkout = false;
      _isAIRecommendation = false;
      _aiRecommendationReason = null;
    }
  }
  
  // ============================================================
  // 🤖 GERAR RECOMENDAÇÃO MOTIVACIONAL COM IA
  // ============================================================
  
  Future<void> _loadAIMotivationalRecommendation() async {
    _isLoadingAIRecommendation = true;
    notifyListeners();
    
    try {
      debugPrint('🤖 Gerando recomendação motivacional com IA...');
      
      // Calcular dias desde último treino
      if (_workoutHistory.isNotEmpty) {
        final lastWorkout = _workoutHistory.first;
        final now = DateTime.now();
        _daysSinceLastWorkout = now.difference(lastWorkout.date).inDays;
      } else {
        _daysSinceLastWorkout = 999;
      }
      
      try {
        final aiResponse = await ApiService.getAIExerciseRecommendations();
        
        String? motivationalText;
        
        if (aiResponse['motivational_message'] != null) {
          motivationalText = aiResponse['motivational_message'];
        } else if (aiResponse['next_steps'] != null && 
                 aiResponse['next_steps']['suggestion'] != null) {
          final suggestion = aiResponse['next_steps']['suggestion'];
          final focus = aiResponse['next_steps']['focus'];
          
          if (focus != null) {
            motivationalText = '$suggestion - $focus';
          } else {
            motivationalText = suggestion;
          }
        } else if (aiResponse['ai_recommendations'] != null &&
                 aiResponse['ai_recommendations']['recommendation_strategy'] != null) {
          motivationalText = aiResponse['ai_recommendations']['recommendation_strategy'];
        }
        
        if (motivationalText != null && motivationalText.isNotEmpty) {
          _aiMotivationalMessage = motivationalText;
          debugPrint('✅ Mensagem motivacional da IA: $_aiMotivationalMessage');
        } else {
          _generateLocalMotivationalMessage();
        }
        
      } catch (aiError) {
        debugPrint('⚠️ IA não disponível: $aiError');
        _generateLocalMotivationalMessage();
      }
      
    } catch (e) {
      debugPrint('❌ Erro ao gerar recomendação: $e');
      _generateLocalMotivationalMessage();
    } finally {
      _isLoadingAIRecommendation = false;
      notifyListeners();
    }
  }
  
  void _generateLocalMotivationalMessage() {
    if (_workoutHistory.isEmpty) {
      _aiMotivationalMessage = '🚀 Comece sua jornada fitness hoje!';
      _daysSinceLastWorkout = 0;
      return;
    }

    if (_daysSinceLastWorkout == 0) {
      _aiMotivationalMessage = '🔥 Ótimo! Você já treinou hoje!';
    } else if (_daysSinceLastWorkout == 1) {
      _aiMotivationalMessage = '💪 Continue consistente!';
    } else if (_daysSinceLastWorkout! <= 3) {
      _aiMotivationalMessage = '⏰ Hora de voltar aos treinos!';
    } else if (_daysSinceLastWorkout! <= 7) {
      _aiMotivationalMessage = '👋 Sentimos sua falta!';
    } else {
      _aiMotivationalMessage = '🌟 Vamos recomeçar?';
    }
  }
  
  // ============================================================
  // HELPERS
  // ============================================================
  
  void _setDefaultValues() {
    _totalWorkouts = 0;
    _activeDays = 0;
    _weeklyGoalPercentage = 0.0;
    _recommendedWorkout = null;
    _isAIGeneratedWorkout = false;
    _isAIRecommendation = false;
    _aiRecommendationReason = null;
    _aiMotivationalMessage = 'Não foi possível carregar recomendações';
    _daysSinceLastWorkout = null;
    _workoutHistory = [];
  }
  
  void clear() {
    _setDefaultValues();
    _error = null;
    notifyListeners();
  }
  
  Future<void> refreshStatistics() async {
    try {
      await _loadWorkoutHistory();
      _calculateStatistics();
      _generateLocalMotivationalMessage();
      notifyListeners();
    } catch (e) {
      debugPrint('❌ Erro ao atualizar: $e');
    }
  }
  
  Future<void> refreshRecommendedWorkout() async {
    try {
      await _loadLastAIGeneratedWorkout();
      if (_recommendedWorkout == null) {
        await _loadRecommendedWorkoutWithAI();
      }
      notifyListeners();
    } catch (e) {
      debugPrint('❌ Erro: $e');
    }
  }
  
  // ============================================================
  // MÉTODOS AUXILIARES PARA UI
  // ============================================================
  
  String getRecommendedWorkoutName() {
    return _recommendedWorkout?['name'] ?? 'Nenhum treino disponível';
  }
  
  int? getRecommendedWorkoutId() {
    return _recommendedWorkout?['id'];
  }
  
  String getRecommendedWorkoutDescription() {
    return _recommendedWorkout?['description'] ?? 'Sem descrição';
  }
  
  int getRecommendedWorkoutDuration() {
    return _recommendedWorkout?['estimated_duration'] ?? 0;
  }
  
  String getRecommendedWorkoutDifficulty() {
    final difficulty = _recommendedWorkout?['difficulty_level'] ?? 'beginner';
    
    switch (difficulty.toString().toLowerCase()) {
      case 'beginner':
        return 'Iniciante';
      case 'intermediate':
        return 'Intermediário';
      case 'advanced':
        return 'Avançado';
      default:
        return 'Iniciante';
    }
  }
  
  String getRecommendationBadge() {
    if (_isAIGeneratedWorkout) {
      return '🤖 Gerado pela IA';
    } else if (_isAIRecommendation) {
      return '🤖 Recomendado pela IA';
    }
    return '';
  }
}