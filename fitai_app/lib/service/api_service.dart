import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';

/// Serviço de API para comunicação com o backend Django
class ApiService {
  // ============================================================
  // CONFIGURAÇÃO DA URL BASE
  // ============================================================
  
  static const String _baseUrl = 'http://localhost:8000'; 
  static const String _apiVersion = '/api/v1';
  
  // Firebase Auth instance
  static final FirebaseAuth _auth = FirebaseAuth.instance;
  
  // ============================================================
  // 🔥 CACHE DE TOKEN (NOVO)
  // ============================================================
  
  static String? _cachedToken;
  static DateTime? _tokenExpiry;
  
  /// Limpa cache de token
  static void clearTokenCache() {
    _cachedToken = null;
    _tokenExpiry = null;
    print('🗑️ Cache de token limpo');
  }
  
  // ============================================================
  // 🔥 OBTER TOKEN COM CACHE E RENOVAÇÃO AUTOMÁTICA (MELHORADO)
  // ============================================================
  
  /// Obtém token válido (usa cache se disponível)
  static Future<String?> _getFirebaseToken({bool forceRefresh = false}) async {
    try {
      final user = _auth.currentUser;
      if (user == null) {
        print('⚠️ Nenhum usuário logado no Firebase');
        return null;
      }
      
      final now = DateTime.now();
      
      // 🔥 Se tem cache válido por mais de 5 minutos, usar
      if (!forceRefresh && 
          _cachedToken != null && 
          _tokenExpiry != null && 
          _tokenExpiry!.isAfter(now.add(Duration(minutes: 5)))) {
        print('✅ Usando token em cache (válido por ${_tokenExpiry!.difference(now).inMinutes} min)');
        return _cachedToken;
      }
      
      print('🔄 Renovando token Firebase...');
      
      // Obter novo token
      final token = await user.getIdToken(true); // true = force refresh
      
      if (token == null) {
        print('⚠️ Não foi possível obter token do Firebase');
        return null;
      }
      
      // Atualizar cache (tokens do Firebase duram 1 hora)
      _cachedToken = token;
      _tokenExpiry = now.add(Duration(minutes: 55)); // 5 min de margem
      
      print('✅ Token renovado (${token.length} chars)');
      print('🔑 Expira em: ${_tokenExpiry!.toIso8601String()}');
      
      return token;
      
    } catch (e) {
      print('❌ Erro ao obter token Firebase: $e');
      clearTokenCache();
      return null;
    }
  }
  
  // ============================================================
  // HEADERS PARA REQUISIÇÕES
  // ============================================================
  
  /// Headers padrão para requisições autenticadas
  static Future<Map<String, String>> _getHeaders({bool forceRefresh = false}) async {
    final token = await _getFirebaseToken(forceRefresh: forceRefresh);
    
    final headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    
    if (token != null) {
      headers['Authorization'] = 'Bearer $token';
      print('✅ Authorization header adicionado');
    } else {
      print('❌ Token null - Authorization header NÃO adicionado');
    }
    
    print('📦 Headers keys: ${headers.keys.toList()}');
    
    return headers;
  }
  
  /// Headers sem autenticação (para endpoints públicos)
  static Map<String, String> _getPublicHeaders() {
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
  }
  
  // ============================================================
  // 🔥 MÉTODOS HTTP COM RETRY AUTOMÁTICO (MELHORADO)
  // ============================================================
  
  /// GET - Buscar dados (com retry)
  static Future<dynamic> get(
    String endpoint, 
    {bool requireAuth = true, int retryCount = 0}
  ) async {
    try {
      final url = Uri.parse('$_baseUrl$_apiVersion$endpoint');
      final headers = requireAuth 
          ? await _getHeaders(forceRefresh: retryCount > 0) 
          : _getPublicHeaders();
      
      print('📡 GET: $url');
      print('🔐 Requer autenticação: $requireAuth');
      
      final response = await http.get(url, headers: headers);
      
      // 🔥 Se 403 e ainda tem retry, tentar novamente
      if (response.statusCode == 403 && retryCount < 2 && requireAuth) {
        print('⚠️ 403 Forbidden - Token inválido, renovando... (retry ${retryCount + 1}/2)');
        
        // Limpar cache e esperar um pouco
        clearTokenCache();
        await Future.delayed(Duration(milliseconds: 500));
        
        // Retry recursivo
        return await get(endpoint, requireAuth: requireAuth, retryCount: retryCount + 1);
      }
      
      return _handleResponse(response);
      
    } catch (e) {
      print('❌ Erro no GET $endpoint: $e');
      rethrow;
    }
  }
  
  /// POST - Enviar dados (com retry)
  static Future<dynamic> post(
    String endpoint, 
    Map<String, dynamic> data, 
    {bool requireAuth = true, int retryCount = 0}
  ) async {
    try {
      final url = Uri.parse('$_baseUrl$_apiVersion$endpoint');
      final headers = requireAuth 
          ? await _getHeaders(forceRefresh: retryCount > 0)
          : _getPublicHeaders();
      
      print('📡 POST: $url');
      print('📦 Body: $data');
      
      final response = await http.post(
        url,
        headers: headers,
        body: jsonEncode(data),
      );
      
      // 🔥 Retry em 403
      if (response.statusCode == 403 && retryCount < 2 && requireAuth) {
        print('⚠️ 403 Forbidden - Renovando token... (retry ${retryCount + 1}/2)');
        
        clearTokenCache();
        await Future.delayed(Duration(milliseconds: 500));
        
        return await post(endpoint, data, requireAuth: requireAuth, retryCount: retryCount + 1);
      }
      
      return _handleResponse(response);
      
    } catch (e) {
      print('❌ Erro no POST $endpoint: $e');
      rethrow;
    }
  }
  
  /// PUT - Atualizar dados (com retry)
  static Future<dynamic> put(
    String endpoint, 
    Map<String, dynamic> data,
    {bool requireAuth = true, int retryCount = 0}
  ) async {
    try {
      final url = Uri.parse('$_baseUrl$_apiVersion$endpoint');
      final headers = requireAuth 
          ? await _getHeaders(forceRefresh: retryCount > 0)
          : _getPublicHeaders();
      
      print('📡 PUT: $url');
      
      final response = await http.put(
        url,
        headers: headers,
        body: jsonEncode(data),
      );
      
      // 🔥 Retry em 403
      if (response.statusCode == 403 && retryCount < 2 && requireAuth) {
        print('⚠️ 403 Forbidden - Renovando token... (retry ${retryCount + 1}/2)');
        
        clearTokenCache();
        await Future.delayed(Duration(milliseconds: 500));
        
        return await put(endpoint, data, requireAuth: requireAuth, retryCount: retryCount + 1);
      }
      
      return _handleResponse(response);
      
    } catch (e) {
      print('❌ Erro no PUT $endpoint: $e');
      rethrow;
    }
  }
  
  /// DELETE - Remover dados (com retry)
  static Future<dynamic> delete(
    String endpoint, 
    {bool requireAuth = true, int retryCount = 0}
  ) async {
    try {
      final url = Uri.parse('$_baseUrl$_apiVersion$endpoint');
      final headers = requireAuth 
          ? await _getHeaders(forceRefresh: retryCount > 0)
          : _getPublicHeaders();
      
      print('📡 DELETE: $url');
      
      final response = await http.delete(url, headers: headers);
      
      // 🔥 Retry em 403
      if (response.statusCode == 403 && retryCount < 2 && requireAuth) {
        print('⚠️ 403 Forbidden - Renovando token... (retry ${retryCount + 1}/2)');
        
        clearTokenCache();
        await Future.delayed(Duration(milliseconds: 500));
        
        return await delete(endpoint, requireAuth: requireAuth, retryCount: retryCount + 1);
      }
      
      return _handleResponse(response);
      
    } catch (e) {
      print('❌ Erro no DELETE $endpoint: $e');
      rethrow;
    }
  }
  
  // ============================================================
  // TRATAMENTO DE RESPOSTAS
  // ============================================================
  
  /// Processa a resposta HTTP e retorna os dados ou lança erro
  static dynamic _handleResponse(http.Response response) {
    print('📨 Status: ${response.statusCode}');
    print('📨 Body: ${response.body}');
    
    if (response.statusCode >= 200 && response.statusCode < 300) {
      // Sucesso
      if (response.body.isEmpty) {
        return {'success': true};
      }
      return jsonDecode(response.body);
    } else {
      // Erro
      String errorMessage = 'Erro desconhecido';
      
      try {
        final errorData = jsonDecode(response.body);
        errorMessage = errorData['error'] ?? errorData['detail'] ?? errorMessage;
      } catch (e) {
        errorMessage = response.body;
      }
      
      throw ApiException(
        statusCode: response.statusCode,
        message: errorMessage,
      );
    }
  }
  
  // ============================================================
  // 🔥 MÉTODO PARA FORÇAR RENOVAÇÃO MANUAL (NOVO)
  // ============================================================
  
  /// Força renovação do token (útil após login/logout)
  static Future<void> refreshToken() async {
    print('🔄 Forçando renovação de token...');
    clearTokenCache();
    await _getFirebaseToken(forceRefresh: true);
  }
  
  // ============================================================
  // ENDPOINTS ESPECÍFICOS - WORKOUTS
  // ============================================================
  
  /// Listar todos os treinos
  static Future<Map<String, dynamic>> getWorkouts() async {
    return await get('/workouts/');
  }
  
  /// Obter treinos recomendados
  static Future<Map<String, dynamic>> getRecommendedWorkouts() async {
    return await get('/workouts/recommended/');
  }
  
  /// Obter detalhes de um treino
  static Future<Map<String, dynamic>> getWorkoutDetail(int workoutId) async {
    return await get('/workouts/$workoutId/');
  }
  
  /// Iniciar sessão de treino
  static Future<Map<String, dynamic>> startWorkoutSession(int workoutId) async {
    try {
      print('🏁 Tentando iniciar sessão para workout $workoutId...');
      
      // Verificar se já existe sessão ativa
      final activeSession = await getActiveSession();
      
      if (activeSession != null) {
        final sessionId = activeSession['active_session_id'];
        final workoutName = activeSession['active_workout'];
        
        print('⚠️ JÁ EXISTE SESSÃO ATIVA:');
        print('   Session ID: $sessionId');
        print('   Workout: $workoutName');
        
        throw ActiveSessionException(
          sessionId: sessionId,
          workoutName: workoutName,
          startedAt: activeSession['started_at'],
          workoutId: activeSession['workout_id'],
        );
      }
      
      print('✅ Nenhuma sessão ativa, iniciando nova sessão...');
      final response = await post('/workouts/$workoutId/start/', {});
      
      print('✅ Sessão iniciada com sucesso!');
      print('   Session ID: ${response['session_id']}');
      
      return response;
      
    } catch (e) {
      print('❌ Erro ao iniciar sessão: $e');
      rethrow;
    }
  }
  
  /// Completar sessão de treino
  static Future<Map<String, dynamic>> completeWorkoutSession({
    int? sessionId,
    int? userRating,
    int? caloriesBurned,
    String? notes,
  }) async {
    try {
      int? finalSessionId = sessionId;
      
      if (finalSessionId == null) {
        print('🔍 SessionId não fornecido, buscando sessão ativa...');
        final activeSession = await getActiveSession();
        
        if (activeSession == null || activeSession['active_session_id'] == null) {
          throw Exception('Nenhuma sessão ativa encontrada para finalizar');
        }
        
        finalSessionId = activeSession['active_session_id'];
      }
      
      print('🏁 Finalizando sessão $finalSessionId no backend...');
      print('   Rating: $userRating');
      print('   Calorias: $caloriesBurned');
      print('   Notas: $notes');
      
      final response = await post(
        '/workouts/sessions/$finalSessionId/complete/',
        {
          if (userRating != null) 'user_rating': userRating,
          if (caloriesBurned != null) 'calories_burned': caloriesBurned,
          if (notes != null && notes.isNotEmpty) 'notes': notes,
        },
      );
      
      print('✅ Sessão $finalSessionId finalizada com sucesso!');
      print('📊 Resposta do backend: $response');
      
      return response;
      
    } catch (e) {
      print('❌ Erro ao finalizar sessão: $e');
      rethrow;
    }
  }
  
  /// Buscar sessão ativa
  static Future<Map<String, dynamic>?> getActiveSession() async {
    try {
      print('🔍 Buscando sessão ativa...');
      final response = await get('/workouts/sessions/active/');
      print('✅ Sessão ativa encontrada: $response');
      return response;
    } catch (e) {
      if (e is ApiException && e.statusCode == 404) {
        print('ℹ️ Nenhuma sessão ativa encontrada');
        return null;
      }
      print('❌ Erro ao buscar sessão ativa: $e');
      rethrow;
    }
  }
  
  /// Cancelar sessão ativa
  static Future<Map<String, dynamic>> cancelActiveSession(int sessionId) async {
    try {
      print('🗑️ Cancelando sessão $sessionId...');
      
      final response = await post(
        '/workouts/sessions/$sessionId/cancel/',
        {},
      );
      
      print('✅ Sessão cancelada com sucesso');
      return response;
      
    } catch (e) {
      print('❌ Erro ao cancelar sessão: $e');
      rethrow;
    }
  }
  
  /// Método auxiliar para lidar com sessão travada
  static Future<void> handleStuckSession() async {
    try {
      print('🔧 Tentando resolver sessão travada...');
      
      final activeSession = await getActiveSession();
      
      if (activeSession == null) {
        print('ℹ️ Nenhuma sessão travada encontrada');
        return;
      }
      
      final sessionId = activeSession['active_session_id'];
      print('⚠️ Sessão travada encontrada: $sessionId');
      
      try {
        await completeWorkoutSession(
          sessionId: sessionId,
          userRating: null,
          notes: 'Sessão finalizada automaticamente (travada)',
        );
        print('✅ Sessão travada finalizada com sucesso');
      } catch (e) {
        print('⚠️ Não foi possível finalizar, tentando cancelar...');
        await cancelActiveSession(sessionId);
        print('✅ Sessão travada cancelada com sucesso');
      }
      
    } catch (e) {
      print('❌ Erro ao resolver sessão travada: $e');
      rethrow;
    }
  }
  
  /// Histórico de treinos
  static Future<Map<String, dynamic>> getWorkoutHistory() async {
    return await get('/workouts/sessions/history/');
  }
  
  /// Status da sessão atual
  static Future<Map<String, dynamic>> getCurrentSessionStatus() async {
    return await get('/workouts/sessions/current/');
  }
  
  // ============================================================
  // ENDPOINTS ESPECÍFICOS - EXERCISES
  // ============================================================
  
  /// Listar exercícios
  static Future<Map<String, dynamic>> getExercises() async {
    return await get('/exercises/');
  }
  
  /// Buscar exercícios
  static Future<Map<String, dynamic>> searchExercises(String query) async {
    return await get('/exercises/search/?q=$query');
  }
  
  /// Exercícios por grupo muscular
  static Future<Map<String, dynamic>> getExercisesByMuscleGroup(String muscleGroup) async {
    return await get('/exercises/by_muscle_group/?muscle_group=$muscleGroup');
  }
  
  // ============================================================
  // ENDPOINTS ESPECÍFICOS - USER
  // ============================================================
  
  /// Dashboard do usuário
  static Future<Map<String, dynamic>> getDashboard() async {
    return await get('/users/dashboard/');
  }
  
  /// Busca o perfil completo do usuário
  static Future<Map<String, dynamic>> getUserProfile() async {
    return await get('/users/profile/'); 
  }

  /// Progresso do usuário
  static Future<Map<String, dynamic>> getUserProgress() async {
    return await get('/users/progress/');
  }
  
  /// Atualizar peso
  static Future<Map<String, dynamic>> updateWeight(double weight) async {
    return await post('/users/update_weight/', {'weight': weight});
  }
  
  /// Analytics do usuário
  static Future<Map<String, dynamic>> getUserAnalytics() async {
    return await get('/users/analytics/');
  }
  
  // ============================================================
  // ENDPOINTS ESPECÍFICOS - AI RECOMMENDATIONS
  // ============================================================
  
  /// Recomendações de exercícios por IA
  static Future<Map<String, dynamic>> getAIExerciseRecommendations() async {
    return await get('/ai/exercise-recommendations/');
  }
  
  
  /// Gerar plano de treino com IA
  static Future<Map<String, dynamic>> generateAIWorkoutPlan({
    int? duration,
    String? focus,
    String? difficulty,
  }) async {
    return await post('/ai/generate-workout/', {
      if (duration != null) 'duration': duration,
      if (focus != null) 'focus': focus,
      if (difficulty != null) 'difficulty': difficulty,
    });
  }
  
  /// Listar apenas MEUS treinos personalizados
  static Future<Map<String, dynamic>> getMyWorkouts() async {
    return await get('/workouts/my-workouts/');
  }

  /// Criar novo treino personalizado
  static Future<Map<String, dynamic>> createWorkout({
    required String name,
    required String description,
    String? difficultyLevel,
    int? estimatedDuration,
    String? targetMuscleGroups,
    String? equipmentNeeded,
    int? caloriesEstimate,
    String? workoutType,
  }) async {
    return await post('/workouts/create/', {
      'name': name,
      'description': description,
      if (difficultyLevel != null) 'difficulty_level': difficultyLevel,
      if (estimatedDuration != null) 'estimated_duration': estimatedDuration,
      if (targetMuscleGroups != null) 'target_muscle_groups': targetMuscleGroups,
      if (equipmentNeeded != null) 'equipment_needed': equipmentNeeded,
      if (caloriesEstimate != null) 'calories_estimate': caloriesEstimate,
      if (workoutType != null) 'workout_type': workoutType,
    });
  }

  /// Atualizar treino personalizado
  static Future<Map<String, dynamic>> updateWorkout(
    int workoutId,
    Map<String, dynamic> data,
  ) async {
    return await put('/workouts/$workoutId/update/', data);
  }

  /// Deletar treino personalizado
  static Future<Map<String, dynamic>> deleteWorkout(int workoutId) async {
    return await delete('/workouts/$workoutId/delete/');
  }

  /// Adicionar exercício ao treino
  static Future<Map<String, dynamic>> addExerciseToWorkout({
    required int workoutId,
    required int exerciseId,
    int sets = 3,
    String reps = '10',
    double? weight,
    int restTime = 60,
    int orderInWorkout = 1,
    String? notes,
  }) async {
    return await post('/workouts/$workoutId/exercises/add/', {
      'exercise_id': exerciseId,
      'sets': sets,
      'reps': reps,
      if (weight != null) 'weight': weight,
      'rest_time': restTime,
      'order_in_workout': orderInWorkout,
      if (notes != null) 'notes': notes,
    });
  }

  /// Remover exercício do treino
  static Future<Map<String, dynamic>> removeExerciseFromWorkout({
    required int workoutId,
    required int workoutExerciseId,
  }) async {
    return await delete('/workouts/$workoutId/exercises/$workoutExerciseId/delete/');
  }

  /// Duplicar treino (criar cópia personalizada)
  static Future<Map<String, dynamic>> duplicateWorkout(int workoutId) async {
    return await post('/workouts/$workoutId/duplicate/', {});
  }
  //widget dash
  static Future<Map<String, dynamic>> getSmartRecommendation() async {
    try {
      print('🧠 Buscando recomendação inteligente...');
      final response = await get('/workouts/smart-recommendation/');
      print('✅ Recomendação inteligente obtida com sucesso');
      return response;
    } catch (e) {
      if (e is ApiException && e.statusCode == 404) {
        print('ℹ️ Nenhuma recomendação disponível');
        return {'success': false, 'has_recommendation': false};
      }
      print('❌ Erro ao obter recomendação: $e');
      return {'success': false, 'error': e.toString()};
    }
  }

 /// 🤖 Buscar recomendação diária da IA
/// GET /api/v1/recommendations/ai/daily-recommendation/
static Future<Map<String, dynamic>> getDailyAIRecommendation() async {
  try {
    print('🤖 Buscando recomendação diária da IA...');
    print('📡 Endpoint: /recommendations/ai/daily-recommendation/');
    
    final response = await get('/recommendations/ai/daily-recommendation/');
    
    print('✅ Resposta recebida:');
    print('   Success: ${response['success']}');
    print('   Has recommendation: ${response['recommendation'] != null}');
    
    if (response['recommendation'] != null) {
      print('   Tipo: ${response['recommendation']['recommendation_type']}');
      print('   Título: ${response['recommendation']['title']}');
    }
    
    return response;
    
  } catch (e) {
    print('❌ Erro ao buscar recomendação diária: $e');
    
    // Retornar fallback local em caso de erro
    return {
      'success': true,
      'recommendation': {
        'recommendation_type': 'motivation',
        'title': 'Continue firme!',
        'message': 'Cada treino é um passo rumo ao seu objetivo!',
        'emoji': '💪',
        'focus_area': 'full_body',
        'intensity': 'moderate',
        'reasoning': 'Mensagem motivacional padrão',
        'motivational_tip': 'Você consegue!',
        'suggested_duration': 30
      },
      'cached': false,
      'is_fallback': true
    };
  }
}

/// 🔄 Forçar atualização da recomendação diária
/// POST /api/v1/recommendations/ai/daily-recommendation/refresh/
static Future<Map<String, dynamic>> refreshDailyAIRecommendation() async {
  try {
    print('🔄 Forçando refresh da recomendação...');
    
    final response = await post('/recommendations/ai/daily-recommendation/refresh/', {});
    
    return response;
    
  } catch (e) {
    print('❌ Erro ao fazer refresh: $e');
    return {
      'success': false,
      'error': e.toString()
    };
  }
}
  // ============================================================
  // ENDPOINTS ESPECÍFICOS - CHATBOT
  // ============================================================

  /// Testar API do chatbot
  static Future<Map<String, dynamic>> testChatbotAPI() async {
    return await get('/chat/test/');
  }

  /// Iniciar nova conversa
  static Future<Map<String, dynamic>> startConversation({
    String conversationType = 'general_fitness',
    String? initialMessage,
    bool forceNew = false,
  }) async {
    return await post('/chat/conversations/start/', {
      'type': conversationType,
      if (initialMessage != null) 'message': initialMessage,
      'force_new': forceNew,
    });
  }

  /// Enviar mensagem em conversa
  static Future<Map<String, dynamic>> sendChatMessage({
    required int conversationId,
    required String message,
    String? contextHint,
  }) async {
    return await post('/chat/conversations/$conversationId/message/', {
      'message': message,
      if (contextHint != null) 'context_hint': contextHint,
    });
  }

  /// Buscar histórico da conversa
  static Future<Map<String, dynamic>> getConversationHistory({
    required int conversationId,
    int limit = 50,
    int offset = 0,
    bool includeContext = false,
  }) async {
    return await get(
      '/chat/conversations/$conversationId/history/?limit=$limit&offset=$offset&include_context=$includeContext'
    );
  }

  /// Listar todas conversas do usuário
  static Future<Map<String, dynamic>> getUserConversations({
    String status = 'all',
    String type = 'all',
    int days = 30,
    int limit = 20,
    int offset = 0,
  }) async {
    return await get(
      '/chat/conversations/?status=$status&type=$type&days=$days&limit=$limit&offset=$offset'
    );
  }

  /// Finalizar conversa
  static Future<Map<String, dynamic>> endConversation({
    required int conversationId,
    double? rating,
    String? feedback,
  }) async {
    return await post('/chat/conversations/$conversationId/end/', {
      if (rating != null) 'rating': rating,
      if (feedback != null) 'feedback': feedback,
    });
  }

  /// Dar feedback em mensagem específica
  static Future<Map<String, dynamic>> sendMessageFeedback({
    required int messageId,
    required String reaction,
    String? feedback,
  }) async {
    return await post('/chat/messages/$messageId/feedback/', {
      'reaction': reaction,
      if (feedback != null) 'feedback': feedback,
    });
  }

  /// Buscar analytics do chat
  static Future<Map<String, dynamic>> getChatAnalytics({
    int days = 30,
  }) async {
    return await get('/chat/analytics/?days=$days');
  }

  /// Gerar treino a partir do chat
  static Future<Map<String, dynamic>> generateWorkoutFromChat({
    int? conversationId,
    int? daysPerWeek,
    String? focus,
  }) async {
    return await post('/recommendations/generate-workout-from-chat/', {
      if (conversationId != null) 'conversation_id': conversationId,
      'user_preferences': {
        if (daysPerWeek != null) 'days_per_week': daysPerWeek,
        if (focus != null) 'focus': focus,
      },
    });
  }
  
  // ============================================================
  // TESTE DE CONEXÃO
  // ============================================================
  
  /// Testa conexão com a API
  static Future<bool> testConnection() async {
    try {
      print('🧪 Iniciando teste de conexão...');
      await get('/workouts/test/', requireAuth: true);
      print('✅ Conexão com API bem-sucedida');
      return true;
    } catch (e) {
      print('❌ Erro ao conectar com API: $e');
      return false;
    }
  }
}

// ============================================================
// EXCEPTION CUSTOMIZADA
// ============================================================

class ApiException implements Exception {
  final int statusCode;
  final String message;
  
  ApiException({
    required this.statusCode,
    required this.message,
  });
  
  @override
  String toString() => 'ApiException($statusCode): $message';
}

/// Exception específica para sessão ativa
class ActiveSessionException implements Exception {
  final int sessionId;
  final String workoutName;
  final String? startedAt;
  final int? workoutId;
  
  ActiveSessionException({
    required this.sessionId,
    required this.workoutName,
    this.startedAt,
    this.workoutId,
  });
  
  @override
  String toString() => 'ActiveSessionException: Sessão $sessionId já está ativa ($workoutName)';
}