import 'package:flutter/material.dart';
import '../service/api_service.dart';
import '../models/workout_history_model.dart';
import 'dart:convert';

/// Provider para gerenciar dados do Dashboard
/// ✨ ATUALIZADO: Integração completa com IA Gemini
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
      
      // 3. Buscar treino recomendado (tenta IA primeiro, depois fallback)
      await _loadRecommendedWorkoutWithAI();
      
      // 4. Gerar recomendação IA motivacional (em paralelo, não bloqueia)
      _loadAIMotivationalRecommendation();
      
      _error = null;
      
      debugPrint('✅ Dashboard carregado com sucesso:');
      debugPrint('   Total de treinos: $_totalWorkouts');
      debugPrint('   Dias ativos: $_activeDays');
      debugPrint('   Meta semanal: $_weeklyGoalPercentage%');
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
  // 🤖 BUSCAR TREINO RECOMENDADO COM IA
  // ============================================================
  
  /// Tenta buscar recomendação da IA, com fallback para endpoint normal
  Future<void> _loadRecommendedWorkoutWithAI() async {
    try {
      debugPrint('🤖 Tentando buscar recomendação da IA...');
      
      // 🔥 PRIMEIRO: Tentar recomendações de exercícios da IA
      // A IA usa automaticamente as características do perfil do usuário (goal, activity_level, etc)
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
            _isAIRecommendation = true;
            _aiRecommendationReason = firstRecommendation['reason'] ?? 
                                      'Recomendado com base no seu perfil';
            
            debugPrint('✅ Treino recomendado pela IA: ${_recommendedWorkout!['name']}');
            debugPrint('   Motivo: $_aiRecommendationReason');
            debugPrint('   Confiança: ${firstRecommendation['confidence_score'] ?? "N/A"}');
            
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
            _isAIRecommendation = false;
            _aiRecommendationReason = null;
            debugPrint('✅ Treino diferente recomendado: ${_recommendedWorkout!['name']}');
            return;
          }
          
          // Se não encontrar diferente, pega qualquer um
          if (allWorkouts.isNotEmpty) {
            _recommendedWorkout = allWorkouts.first;
            _isAIRecommendation = false;
            _aiRecommendationReason = null;
            debugPrint('✅ Treino padrão recomendado: ${_recommendedWorkout!['name']}');
            return;
          }
        }
      }
      
      debugPrint('ℹ️ Nenhum treino recomendado disponível');
      _recommendedWorkout = null;
      _isAIRecommendation = false;
      _aiRecommendationReason = null;
      
    } catch (e) {
      debugPrint('⚠️ Erro ao buscar treino recomendado: $e');
      _recommendedWorkout = null;
      _isAIRecommendation = false;
      _aiRecommendationReason = null;
    }
  }
  
  // ============================================================
  // 🤖 GERAR RECOMENDAÇÃO MOTIVACIONAL COM IA
  // ============================================================
  
  /// Gera mensagem motivacional personalizada usando IA
  /// Roda em paralelo, não bloqueia o carregamento do dashboard
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
        _daysSinceLastWorkout = 999; // Nenhum treino ainda
      }
      
      // Tentar obter mensagem da IA
      // O backend automaticamente usa o perfil do usuário (goal, activity_level, etc)
      try {
        // Determinar contexto baseado nos dias
        String context = 'workout_start';
        if (_daysSinceLastWorkout == 0) {
          context = 'workout_completed';
        } else if (_daysSinceLastWorkout! > 7) {
          context = 'comeback_motivation';
        }
        
        final aiResponse = await ApiService.getAIExerciseRecommendations();
        
        // A IA pode retornar uma mensagem motivacional
        if (aiResponse['motivational_message'] != null) {
          _aiMotivationalMessage = aiResponse['motivational_message'];
          debugPrint('✅ Mensagem motivacional da IA recebida');
        } else {
          // Fallback: gerar localmente baseado no histórico
          _generateLocalMotivationalMessage();
        }
        
      } catch (aiError) {
        debugPrint('⚠️ IA não disponível para mensagem motivacional: $aiError');
        _generateLocalMotivationalMessage();
      }
      
    } catch (e) {
      debugPrint('❌ Erro ao gerar recomendação motivacional: $e');
      _generateLocalMotivationalMessage();
    } finally {
      _isLoadingAIRecommendation = false;
      notifyListeners();
    }
  }
  
  /// Gera mensagem motivacional localmente (fallback)
  void _generateLocalMotivationalMessage() {
    debugPrint('🤖 Gerando mensagem motivacional local (fallback)...');
    
    if (_workoutHistory.isEmpty) {
      _aiMotivationalMessage = '🚀 Comece sua jornada fitness hoje!';
      _daysSinceLastWorkout = 0;
      return;
    }

    // Gerar mensagem baseada nos dias
    if (_daysSinceLastWorkout == 0) {
      _aiMotivationalMessage = '🔥 Ótimo! Você já treinou hoje!';
    } else if (_daysSinceLastWorkout == 1) {
      _aiMotivationalMessage = '💪 Continue consistente! Seu próximo treino está pronto.';
    } else if (_daysSinceLastWorkout! <= 3) {
      _aiMotivationalMessage = '⏰ Hora de voltar aos treinos!';
    } else if (_daysSinceLastWorkout! <= 7) {
      _aiMotivationalMessage = '👋 Sentimos sua falta! Vamos treinar?';
    } else {
      _aiMotivationalMessage = '🌟 Vamos recomeçar sua jornada fitness?';
    }

    // Adicionar recomendação de grupo muscular baseado no último treino
    if (_workoutHistory.isNotEmpty && _workoutHistory.first.muscleGroups.isNotEmpty) {
      final lastMuscle = _workoutHistory.first.muscleGroups.first.toLowerCase();
      
      if (lastMuscle.contains('peito') || lastMuscle.contains('peitoral')) {
        _aiMotivationalMessage = '$_aiMotivationalMessage Foque em pernas ou costas hoje.';
      } else if (lastMuscle.contains('perna') || lastMuscle.contains('coxa')) {
        _aiMotivationalMessage = '$_aiMotivationalMessage Que tal treinar superiores hoje?';
      } else if (lastMuscle.contains('costa') || lastMuscle.contains('costas')) {
        _aiMotivationalMessage = '$_aiMotivationalMessage Recomendo treino de pernas ou peito.';
      } else if (lastMuscle.contains('braço') || lastMuscle.contains('biceps')) {
        _aiMotivationalMessage = '$_aiMotivationalMessage Foque em grupos musculares maiores hoje.';
      }
    }

    debugPrint('🤖 Mensagem local: $_aiMotivationalMessage');
    debugPrint('📅 Dias desde último treino: $_daysSinceLastWorkout');
  }
  
  // ============================================================
  // HELPERS
  // ============================================================
  
  /// Define valores padrão em caso de erro
  void _setDefaultValues() {
    _totalWorkouts = 0;
    _activeDays = 0;
    _weeklyGoalPercentage = 0.0;
    _recommendedWorkout = null;
    _isAIRecommendation = false;
    _aiRecommendationReason = null;
    _aiMotivationalMessage = 'Não foi possível carregar recomendações';
    _daysSinceLastWorkout = null;
    _workoutHistory = [];
  }
  
  /// Limpa todos os dados
  void clear() {
    _totalWorkouts = 0;
    _activeDays = 0;
    _weeklyGoalPercentage = 0.0;
    _recommendedWorkout = null;
    _isAIRecommendation = false;
    _aiRecommendationReason = null;
    _aiMotivationalMessage = null;
    _daysSinceLastWorkout = null;
    _workoutHistory = [];
    _error = null;
    notifyListeners();
  }
  
  /// Atualiza apenas as estatísticas (refresh rápido)
  Future<void> refreshStatistics() async {
    try {
      debugPrint('🔄 Atualizando estatísticas...');
      await _loadWorkoutHistory();
      _calculateStatistics();
      _generateLocalMotivationalMessage();
      notifyListeners();
    } catch (e) {
      debugPrint('❌ Erro ao atualizar estatísticas: $e');
    }
  }
  
  /// Atualiza apenas o treino recomendado (força nova busca da IA)
  Future<void> refreshRecommendedWorkout() async {
    try {
      debugPrint('🔄 Atualizando treino recomendado...');
      await _loadRecommendedWorkoutWithAI();
      notifyListeners();
    } catch (e) {
      debugPrint('❌ Erro ao atualizar treino recomendado: $e');
    }
  }
  
  /// Atualiza recomendação motivacional (força nova geração da IA)
  Future<void> refreshMotivationalMessage() async {
    try {
      debugPrint('🔄 Atualizando mensagem motivacional...');
      await _loadAIMotivationalRecommendation();
    } catch (e) {
      debugPrint('❌ Erro ao atualizar mensagem motivacional: $e');
    }
  }
  
  // ============================================================
  // MÉTODOS AUXILIARES PARA UI
  // ============================================================
  
  /// Retorna informações do treino recomendado de forma segura
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
    
    // Traduzir para português
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
  
  /// Badge de recomendação IA (para mostrar na UI)
  String getRecommendationBadge() {
    if (_isAIRecommendation) {
      return '🤖 Recomendado pela IA';
    }
    return '';
  }
}