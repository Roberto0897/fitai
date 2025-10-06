/// Model para Conversa do Chatbot
class ChatConversation {
  final int id;
  final String title;
  final String type;
  final String status;
  final DateTime createdAt;
  final DateTime lastActivity;
  final int messageCount;
  final int aiResponsesCount;
  final double? userRating;
  final bool isExpired;

  ChatConversation({
    required this.id,
    required this.title,
    required this.type,
    required this.status,
    required this.createdAt,
    required this.lastActivity,
    required this.messageCount,
    required this.aiResponsesCount,
    this.userRating,
    required this.isExpired,
  });

  factory ChatConversation.fromJson(Map<String, dynamic> json) {
    return ChatConversation(
      id: json['id'],
      title: json['title'] ?? 'Conversa',
      type: json['type'] ?? 'general_fitness',
      status: json['status'] ?? 'active',
      createdAt: DateTime.parse(json['created_at']),
      lastActivity: DateTime.parse(json['last_activity']),
      messageCount: json['message_count'] ?? 0,
      aiResponsesCount: json['ai_responses_count'] ?? 0,
      userRating: json['user_rating']?.toDouble(),
      isExpired: json['is_expired'] ?? false,
    );
  }
}

/// Model para Mensagem do Chat
class ChatMessage {
  final int? id;
  final String text;
  final bool isUser;
  final DateTime timestamp;
  final String? intent;
  final double? confidence;
  final String? reaction;
  final Map<String, dynamic>? metadata;

  ChatMessage({
    this.id,
    required this.text,
    required this.isUser,
    required this.timestamp,
    this.intent,
    this.confidence,
    this.reaction,
    this.metadata,
  });

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      id: json['id'],
      text: json['content'] ?? json['text'],
      isUser: json['type'] == 'user' || json['isUser'] == true,
      timestamp: json['timestamp'] != null 
          ? DateTime.parse(json['timestamp'])
          : DateTime.now(),
      intent: json['intent_detected'],
      confidence: json['confidence_score']?.toDouble(),
      reaction: json['user_reaction'],
      metadata: json['ai_metadata'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      if (id != null) 'id': id,
      'text': text,
      'isUser': isUser,
      'timestamp': timestamp.toIso8601String(),
      if (intent != null) 'intent': intent,
      if (confidence != null) 'confidence': confidence,
      if (reaction != null) 'reaction': reaction,
      if (metadata != null) 'metadata': metadata,
    };
  }
}

/// Tipos de conversa disponíveis
enum ConversationType {
  workoutConsultation('workout_consultation', 'Consulta de Treino', '💪'),
  nutritionAdvice('nutrition_advice', 'Orientação Nutricional', '🥗'),
  progressAnalysis('progress_analysis', 'Análise de Progresso', '📈'),
  motivationChat('motivation_chat', 'Motivação', '🌟'),
  techniqueGuidance('technique_guidance', 'Orientação de Técnica', '🎯'),
  generalFitness('general_fitness', 'Fitness Geral', '🏃');

  final String value;
  final String label;
  final String emoji;

  const ConversationType(this.value, this.label, this.emoji);
}

/// Tipos de reação para feedback
enum MessageReaction {
  helpful('helpful', 'Útil', '👍'),
  notHelpful('not_helpful', 'Não útil', '👎'),
  excellent('excellent', 'Excelente', '⭐'),
  needsImprovement('needs_improvement', 'Precisa melhorar', '🔄');

  final String value;
  final String label;
  final String emoji;

  const MessageReaction(this.value, this.label, this.emoji);
}