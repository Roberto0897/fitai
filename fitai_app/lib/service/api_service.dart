import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';

/// Serviço de API para comunicação com o backend Django
class ApiService {
  // ============================================================
  // CONFIGURAÇÃO DA URL BASE
  // ============================================================
  
  // DESENVOLVIMENTO - Ajuste conforme seu ambiente:
  // Android Emulator: 'http://10.0.2.2:8000'
  // iOS Simulator: 'http://localhost:8000' ou 'http://127.0.0.1:8000'
  // Dispositivo físico: 'http://SEU_IP_LOCAL:8000' (ex: 'http://192.168.1.100:8000')
  // Web: 'http://localhost:8000'
  
  static const String _baseUrl = 'http://localhost:8000'; 
  
  // PRODUÇÃO: Descomente e ajuste quando for fazer deploy
  // static const String _baseUrl = 'https://api.seudominio.com';
  
  static const String _apiVersion = '/api/v1';
  
  // Firebase Auth instance
  static final FirebaseAuth _auth = FirebaseAuth.instance;
  
  // ============================================================
  // OBTER TOKEN FIREBASE
  // ============================================================
  
  /// Obtém o ID Token do usuário autenticado no Firebase
  static Future<String?> _getFirebaseToken() async {
    try {
      final user = _auth.currentUser;
      if (user == null) {
        print('⚠️ Nenhum usuário logado no Firebase');
        return null;
      }
      
      print('👤 Usuário logado: ${user.email} (${user.uid})');
      
      // Obter ID Token (força refresh se necessário)
      final token = await user.getIdToken(true);
      
      if (token == null) {
        print('⚠️ Não foi possível obter token do Firebase');
        return null;
      }
      
      print('✅ Token Firebase obtido com sucesso (${token.length} caracteres)');
      print('🔑 Primeiros 50 caracteres: ${token.substring(0, 50)}...');
      
      return token;
      
    } catch (e) {
      print('❌ Erro ao obter token Firebase: $e');
      return null;
    }
  }
  
  // ============================================================
  // HEADERS PARA REQUISIÇÕES
  // ============================================================
  
  /// Headers padrão para requisições autenticadas
  static Future<Map<String, String>> _getHeaders() async {
    final token = await _getFirebaseToken();
    
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
  // MÉTODOS HTTP GENÉRICOS
  // ============================================================
  
  /// GET - Buscar dados
  static Future<dynamic> get(String endpoint, {bool requireAuth = true}) async {
    try {
      final url = Uri.parse('$_baseUrl$_apiVersion$endpoint');
      final headers = requireAuth ? await _getHeaders() : _getPublicHeaders();
      
      print('📡 GET: $url');
      print('🔐 Requer autenticação: $requireAuth');
      
      final response = await http.get(url, headers: headers);
      
      return _handleResponse(response);
      
    } catch (e) {
      print('❌ Erro no GET $endpoint: $e');
      rethrow;
    }
  }
  
  /// POST - Enviar dados
  static Future<dynamic> post(
    String endpoint, 
    Map<String, dynamic> data, 
    {bool requireAuth = true}
  ) async {
    try {
      final url = Uri.parse('$_baseUrl$_apiVersion$endpoint');
      final headers = requireAuth ? await _getHeaders() : _getPublicHeaders();
      
      print('📡 POST: $url');
      print('📦 Body: $data');
      
      final response = await http.post(
        url,
        headers: headers,
        body: jsonEncode(data),
      );
      
      return _handleResponse(response);
      
    } catch (e) {
      print('❌ Erro no POST $endpoint: $e');
      rethrow;
    }
  }
  
  /// PUT - Atualizar dados
  static Future<dynamic> put(
    String endpoint, 
    Map<String, dynamic> data,
    {bool requireAuth = true}
  ) async {
    try {
      final url = Uri.parse('$_baseUrl$_apiVersion$endpoint');
      final headers = requireAuth ? await _getHeaders() : _getPublicHeaders();
      
      print('📡 PUT: $url');
      
      final response = await http.put(
        url,
        headers: headers,
        body: jsonEncode(data),
      );
      
      return _handleResponse(response);
      
    } catch (e) {
      print('❌ Erro no PUT $endpoint: $e');
      rethrow;
    }
  }
  
  /// DELETE - Remover dados
  static Future<dynamic> delete(String endpoint, {bool requireAuth = true}) async {
    try {
      final url = Uri.parse('$_baseUrl$_apiVersion$endpoint');
      final headers = requireAuth ? await _getHeaders() : _getPublicHeaders();
      
      print('📡 DELETE: $url');
      
      final response = await http.delete(url, headers: headers);
      
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
    return await post('/workouts/$workoutId/start/', {});
  }
  
  /// Completar sessão de treino
  static Future<Map<String, dynamic>> completeWorkoutSession({
    int? userRating,
    int? caloriesBurned,
    String? notes,
  }) async {
    return await post('/sessions/complete/', {
      if (userRating != null) 'user_rating': userRating,
      if (caloriesBurned != null) 'calories_burned': caloriesBurned,
      if (notes != null) 'notes': notes,
    });
  }
  
  /// Histórico de treinos
  static Future<Map<String, dynamic>> getWorkoutHistory() async {
    return await get('/sessions/history/');
  }
  
  /// Status da sessão atual
  static Future<Map<String, dynamic>> getCurrentSessionStatus() async {
    return await get('/sessions/current/');
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
  
   /// Busca o perfil completo do usuário (substitui o dashboard) //NOVO 04/10 /17:07
  static Future<Map<String, dynamic>> getUserProfile() async {
    // Usamos o endpoint que mapeamos no Django para o UserProfileUpdateView
    // O Django usa o token para saber qual perfil retornar
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
    return await get('/analytics/');
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
  // ============================================================
  // TESTE DE CONEXÃO
  // ============================================================
  
  /// Testa conexão com a API
  static Future<bool> testConnection() async {
    try {
      print('🧪 Iniciando teste de conexão...');
      await get('/workouts/test/', requireAuth: true); // Mudou para true
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