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
    print('🔍 [WorkoutHistoryModel] Parseando JSON:');
    print('   Chaves disponíveis: ${json.keys.toList()}');
    
    // ID
    final id = json['id'] ?? json['session_id'] ?? 0;
    print('   ✓ ID: $id');
    
    // Nome do treino
    final workoutName = json['workout_name'] ?? 
                       json['name'] ?? 
                       json['workout']?.toString() ?? 
                       'Treino';
    print('   ✓ Nome: $workoutName');
    
    // Data
    final dateStr = json['date'] ?? 
                   json['completed_at'] ?? 
                   json['finished_at'] ?? 
                   DateTime.now().toIso8601String();
    final date = DateTime.parse(dateStr);
    print('   ✓ Data: $date');
    
    // Duração
    final duration = json['duration'] ?? 
                    json['duration_minutes'] ?? 
                    json['total_duration'] ?? 
                    0;
    print('   ✓ Duração: $duration min');
    
    // Calorias
    var calories = json['calories'] ?? 
            json['calories_burned'] ?? 
            json['total_calories'] ?? 
            0;

    // Se calorias é 0, calcular estimativa baseado na duração
    if (calories == 0 && duration > 0) {
      // Estimativa: ~6-8 kcal por minuto (varia por intensidade)
      // Você pode ajustar esse valor conforme necessário
      calories = (duration * 6).toInt();
      print('   ⚠️ Calorias calculadas (estimativa): $calories kcal');
    } else {
      print('   ✓ Calorias: $calories');
    }

    
    
    // Categoria - buscar em vários lugares
    String category = json['category'] ?? 
                     json['workout_category'] ?? 
                     json['type'] ?? 
                     'Geral';
    
    // Se não encontrou categoria, tentar inferir do nome ou grupos musculares
    if (category == 'Geral') {
      final nameUpper = workoutName.toUpperCase();
      if (nameUpper.contains('CARDIO') || nameUpper.contains('CORRIDA')) {
        category = 'Cardio';
      } else if (nameUpper.contains('FORÇA') || nameUpper.contains('MUSCULAÇÃO')) {
        category = 'Força';
      } else if (nameUpper.contains('HIPERTROFIA')) {
        category = 'Hipertrofia';
      }
    }
    print('   ✓ Categoria: $category');
    
    // Grupos musculares - buscar em vários formatos
    final muscleGroupsRaw = json['muscle_groups'] ?? 
                           json['focus_areas'] ?? 
                           json['muscles'] ?? 
                           json['target_muscles'];
    
    print('   ℹ️ muscle_groups raw: $muscleGroupsRaw (tipo: ${muscleGroupsRaw?.runtimeType})');
    
    final muscleGroups = _parseMuscleGroups(muscleGroupsRaw);
    
    // Se não encontrou grupos musculares, tentar inferir do nome do treino
    if (muscleGroups.isEmpty) {
      final inferredMuscles = _inferMuscleGroupsFromName(workoutName);
      muscleGroups.addAll(inferredMuscles);
      print('   ⚠️ Grupos musculares inferidos do nome: $inferredMuscles');
    }
    
    print('   ✓ Grupos musculares: $muscleGroups');
    
    // Exercícios
    final exercisesCompleted = json['exercises_completed'] ?? 
                              json['completed_exercises'] ?? 
                              0;
    final totalExercises = json['total_exercises'] ?? 
                          json['exercises_count'] ?? 
                          1;
    print('   ✓ Exercícios: $exercisesCompleted/$totalExercises');
    
    // Status de conclusão
    final completed = json['completed'] ?? 
                     json['is_completed'] ?? 
                     json['finished'] ?? 
                     false;
    print('   ✓ Completo: $completed');
    
    return WorkoutHistoryModel(
      id: id,
      workoutName: workoutName,
      date: date,
      duration: duration,
      calories: calories,
      category: category,
      muscleGroups: muscleGroups,
      exercisesCompleted: exercisesCompleted,
      totalExercises: totalExercises,
      completed: completed,
    );
  }

  /// Parse muscle groups (pode vir como string ou lista)
  static List<String> _parseMuscleGroups(dynamic value) {
    if (value == null) return [];
    
    if (value is List) {
      return value
          .map((e) => e.toString().trim())
          .where((e) => e.isNotEmpty)
          .toList();
    }
    
    if (value is String) {
      // Pode vir separado por vírgula, ponto e vírgula, ou pipe
      final separators = [',', ';', '|'];
      for (var sep in separators) {
        if (value.contains(sep)) {
          return value
              .split(sep)
              .map((e) => e.trim())
              .where((e) => e.isNotEmpty)
              .toList();
        }
      }
      // Se não tem separadores, retorna a string única
      return [value.trim()];
    }
    
    return [];
  }

  /// Inferir grupos musculares do nome do treino
  static List<String> _inferMuscleGroupsFromName(String name) {
    final nameUpper = name.toUpperCase();
    final muscles = <String>[];
    
    // Mapeamento de palavras-chave para grupos musculares
    final muscleMap = {
      'PEITO': 'Peito',
      'PEITORAL': 'Peito',
      'COSTAS': 'Costas',
      'DORSAL': 'Costas',
      'OMBRO': 'Ombros',
      'OMBROS': 'Ombros',
      'DELTOIDE': 'Ombros',
      'BRAÇO': 'Braços',
      'BRAÇOS': 'Braços',
      'BICEPS': 'Bíceps',
      'BÍCEPS': 'Bíceps',
      'TRICEPS': 'Tríceps',
      'TRÍCEPS': 'Tríceps',
      'PERNA': 'Pernas',
      'PERNAS': 'Pernas',
      'QUADRICEPS': 'Pernas',
      'QUADRÍCEPS': 'Pernas',
      'POSTERIOR': 'Pernas',
      'GLÚTEO': 'Glúteos',
      'GLÚTEOS': 'Glúteos',
      'ABDOMEN': 'Abdômen',
      'ABDÔMEN': 'Abdômen',
      'ABS': 'Abdômen',
      'CORE': 'Abdômen',
      'CARDIO': 'Cardio',
      'CORRIDA': 'Cardio',
      'AERÓBICO': 'Cardio',
    };
    
    for (var entry in muscleMap.entries) {
      if (nameUpper.contains(entry.key)) {
        if (!muscles.contains(entry.value)) {
          muscles.add(entry.value);
        }
      }
    }
    
    return muscles;
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
    return 'WorkoutHistory(id: $id, name: $workoutName, date: $date, muscles: $muscleGroups, completed: $completed)';
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