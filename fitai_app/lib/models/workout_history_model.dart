class WorkoutHistoryModel {
  final int id;
  final String workoutName;
  final DateTime date;
  final int duration; // em minutos
  final int calories;
  final String category; // Força, Cardio, etc
  final List<String> muscleGroups; // Grupos musculares trabalhados
  final int exercisesCompleted;
  final int totalExercises;
  final bool completed;

  WorkoutHistoryModel({
    required this.id,
    required this.workoutName,
    required this.date,
    required this.duration,
    required this.calories,
    required this.category,
    required this.muscleGroups,
    required this.exercisesCompleted,
    required this.totalExercises,
    required this.completed,
  });

  /// Converter do JSON do backend
  factory WorkoutHistoryModel.fromJson(Map<String, dynamic> json) {
    return WorkoutHistoryModel(
      id: json['id'] ?? 0,
      workoutName: json['workout_name'] ?? json['name'] ?? 'Treino',
      date: DateTime.parse(json['date'] ?? json['completed_at'] ?? DateTime.now().toIso8601String()),
      duration: json['duration'] ?? 0,
      calories: json['calories'] ?? 0,
      category: json['category'] ?? 'Geral',
      muscleGroups: _parseMuscleGroups(json['muscle_groups'] ?? json['focus_areas']),
      exercisesCompleted: json['exercises_completed'] ?? 0,
      totalExercises: json['total_exercises'] ?? 0,
      completed: json['completed'] ?? false,
    );
  }

  /// Parse muscle groups (pode vir como string ou lista)
  static List<String> _parseMuscleGroups(dynamic value) {
    if (value == null) return [];
    if (value is List) return value.map((e) => e.toString()).toList();
    if (value is String) {
      return value.split(',').map((e) => e.trim()).where((e) => e.isNotEmpty).toList();
    }
    return [];
  }

  /// Converter para JSON (caso precise enviar ao backend)
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'workout_name': workoutName,
      'date': date.toIso8601String(),
      'duration': duration,
      'calories': calories,
      'category': category,
      'muscle_groups': muscleGroups.join(','),
      'exercises_completed': exercisesCompleted,
      'total_exercises': totalExercises,
      'completed': completed,
    };
  }

  /// Calcular percentual de conclusão
  double get completionPercentage {
    if (totalExercises == 0) return 0.0;
    return (exercisesCompleted / totalExercises) * 100;
  }

  /// Formatar duração (ex: "1h 30min")
  String get formattedDuration {
    if (duration < 60) return '${duration}min';
    final hours = duration ~/ 60;
    final mins = duration % 60;
    if (mins == 0) return '${hours}h';
    return '${hours}h ${mins}min';
  }

  /// Tempo relativo (ex: "Há 2h", "Ontem", "3 dias atrás")
  String get relativeTime {
    final now = DateTime.now();
    final difference = now.difference(date);

    if (difference.inMinutes < 60) {
      return 'Há ${difference.inMinutes}min';
    } else if (difference.inHours < 24) {
      return 'Há ${difference.inHours}h';
    } else if (difference.inDays == 1) {
      return 'Ontem';
    } else if (difference.inDays < 7) {
      return '${difference.inDays} dias atrás';
    } else if (difference.inDays < 30) {
      final weeks = difference.inDays ~/ 7;
      return weeks == 1 ? '1 semana atrás' : '$weeks semanas atrás';
    } else {
      final months = difference.inDays ~/ 30;
      return months == 1 ? '1 mês atrás' : '$months meses atrás';
    }
  }

  @override
  String toString() {
    return 'WorkoutHistory(id: $id, name: $workoutName, date: $date, completed: $completed)';
  }
}

/// Modelo para estatísticas de treino
class WorkoutStats {
  final int totalWorkouts;
  final int totalDuration; // em minutos
  final int totalCalories;
  final int activeDays;
  final int currentStreak; // dias consecutivos
  final Map<String, int> workoutsByCategory;
  final Map<String, int> muscleGroupFrequency;
  final String favoriteExercise;
  final int favoriteExerciseCount;
  final double averageDuration; // em minutos

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

  factory WorkoutStats.fromJson(Map<String, dynamic> json) {
    return WorkoutStats(
      totalWorkouts: json['total_workouts'] ?? 0,
      totalDuration: json['total_duration'] ?? 0,
      totalCalories: json['total_calories'] ?? 0,
      activeDays: json['active_days'] ?? 0,
      currentStreak: json['current_streak'] ?? 0,
      workoutsByCategory: Map<String, int>.from(json['workouts_by_category'] ?? {}),
      muscleGroupFrequency: Map<String, int>.from(json['muscle_group_frequency'] ?? {}),
      favoriteExercise: json['favorite_exercise'] ?? 'Nenhum',
      favoriteExerciseCount: json['favorite_exercise_count'] ?? 0,
      averageDuration: (json['average_duration'] ?? 0).toDouble(),
    );
  }

  /// Formatar duração total (ex: "15h 30min")
  String get formattedTotalDuration {
    if (totalDuration < 60) return '${totalDuration}min';
    final hours = totalDuration ~/ 60;
    final mins = totalDuration % 60;
    if (mins == 0) return '${hours}h';
    return '${hours}h ${mins}min';
  }

  /// Dias sem treinar
  int get daysWithoutWorkout {
    // Calculado no provider com base na última data de treino
    return 0;
  }

  /// Grupo muscular mais trabalhado
  String get mostTrainedMuscleGroup {
    if (muscleGroupFrequency.isEmpty) return 'Nenhum';
    
    var maxEntry = muscleGroupFrequency.entries.first;
    for (var entry in muscleGroupFrequency.entries) {
      if (entry.value > maxEntry.value) {
        maxEntry = entry;
      }
    }
    return maxEntry.key;
  }

  @override
  String toString() {
    return 'WorkoutStats(workouts: $totalWorkouts, duration: $totalDuration, calories: $totalCalories)';
  }
}

/// Modelo para peso do usuário ao longo do tempo
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
      weight: (json['weight'] ?? 0).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'date': date.toIso8601String(),
      'weight': weight,
    };
  }
}