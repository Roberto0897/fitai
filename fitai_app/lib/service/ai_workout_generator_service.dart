// lib/service/ai_workout_generator_service.dart

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';

class AIWorkoutGeneratorService {
  // USAR SEU BACKEND EXISTENTE
  static const String baseUrl = 'http://localhost:8000/api/v1';
  
  /// Gera treino personalizado durante onboarding usando RecommendationEngine
  static Future<Map<String, dynamic>?> generatePersonalizedWorkout({
    required Map<String, dynamic> userData,
  }) async {
    try {
      // 1. Pegar token Firebase
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) {
        print('❌ Usuário não autenticado');
        return null;
      }
      
      final token = await user.getIdToken(true);
      if (token == null) {
        print('❌ Token Firebase null');
        return null;
      }
      
      print('📦 Preparando dados para backend...');
      print('👤 User data: $userData');
      
      // 2. Preparar body
      final body = {
        'user_data': userData,
      };
      
      print('📤 Enviando para: $baseUrl/workouts/onboarding/generate/');
      
      // 3. Fazer requisição para ENDPOINT EXISTENTE
      final response = await http.post(
        Uri.parse('$baseUrl/workouts/onboarding/generate/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: json.encode(body),
      ).timeout(
        const Duration(seconds: 30),
        onTimeout: () {
          print('⏰ Timeout após 30s');
          throw Exception('Timeout na geração do treino');
        },
      );
      
      print('📡 Status: ${response.statusCode}');
      print('📦 Response: ${response.body}');
      
      if (response.statusCode == 201 || response.statusCode == 200) {
        final data = json.decode(response.body);
        
        if (data['success'] == true) {
          print('✅ Treino gerado com sucesso!');
          print('🏋️ Workout ID: ${data['workout_id']}');
          print('📝 Nome: ${data['workout_name']}');
          print('💪 Exercícios: ${data['exercises_count']}');
          
          return {
            'success': true,
            'workout_id': data['workout_id'],
            'workout_name': data['workout_name'],
            'exercises_count': data['exercises_count'],
            'is_ai_generated': data['is_ai_generated'] ?? false,
            'message': data['message'],
          };
        }
      } else if (response.statusCode == 503) {
        print('⚠️ Serviço temporariamente indisponível');
        final data = json.decode(response.body);
        return {
          'success': false,
          'message': data['message'] ?? 'Serviço indisponível',
        };
      } else {
        print('❌ Erro ${response.statusCode}: ${response.body}');
      }
      
      return null;
      
    } catch (e, stackTrace) {
      print('❌ Erro ao gerar treino de onboarding: $e');
      print('Stack trace: $stackTrace');
      return null;
    }
  }
  
  /// Busca recomendações usando sistema existente
  static Future<List<Map<String, dynamic>>> getRecommendations({
    String algorithm = 'hybrid',
    int limit = 5,
  }) async {
    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) return [];
      
      final token = await user.getIdToken(true);
      if (token == null) return [];
      
      final response = await http.get(
        Uri.parse('$baseUrl/recommendations/personalized/?algorithm=$algorithm&limit=$limit'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final recommendations = data['personalized_recommendations'] as List?;
        
        if (recommendations != null) {
          return recommendations.map((r) => r as Map<String, dynamic>).toList();
        }
      }
      
      return [];
      
    } catch (e) {
      print('❌ Erro ao buscar recomendações: $e');
      return [];
    }
  }
  
  /// Marca recomendação como aceita
  static Future<bool> acceptRecommendation(int recommendationId) async {
    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) return false;
      
      final token = await user.getIdToken(true);
      if (token == null) return false;
      
      final response = await http.post(
        Uri.parse('$baseUrl/recommendations/$recommendationId/accept/'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );
      
      return response.statusCode == 200;
      
    } catch (e) {
      print('❌ Erro ao aceitar recomendação: $e');
      return false;
    }
  }
}