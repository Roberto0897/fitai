import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:flutter_svg/flutter_svg.dart';
import '../../../core/router/app_router.dart';
import '../../../providers/reports_provider.dart' show ReportsProvider, WeightEntry;
import '../../../models/workout_history_model.dart' hide WeightEntry;
import 'widgets/body_heatmap_widget.dart';

class ReportsPage extends StatefulWidget {
  const ReportsPage({Key? key}) : super(key: key);

  @override
  State<ReportsPage> createState() => _ReportsPageState();
}

class _ReportsPageState extends State<ReportsPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ReportsProvider>().loadReports();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1A1A1A),
      body: Consumer<ReportsProvider>(
        builder: (context, provider, child) {
          return SafeArea(
            child: Column(
              children: [
                Expanded(
                  child: RefreshIndicator(
                    onRefresh: provider.refresh,
                    color: const Color(0xFF00BCD4),
                    child: SingleChildScrollView(
                      physics: const AlwaysScrollableScrollPhysics(),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _buildHeader(),
                          const SizedBox(height: 24),
                          _buildMotivationalMessage(provider),
                          const SizedBox(height: 32),
                          _buildMetricsCards(provider),
                          const SizedBox(height: 32),
                          _buildWeeklyFrequencyChart(provider),
                          const SizedBox(height: 32),
                          if (provider.stats != null)
                            Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 24),
                              child: MuscleGroupCardsWidget(
                                muscleGroupFrequency: provider.stats!.muscleGroupFrequency,
                              ),
                            ),
                          const SizedBox(height: 32),
                          _buildCalendarHeatmap(provider),
                          const SizedBox(height: 32),
                          // WIDGET NOVO COM EXPANSÃO
                          if (provider.workoutHistory.isNotEmpty)
                            _WorkoutHistorySection(provider: provider),
                          const SizedBox(height: 24),
                          _buildWeightCard(provider),
                          const SizedBox(height: 24),
                          if (provider.stats != null)
                            _buildStatsCards(provider),
                          const SizedBox(height: 100),
                        ],
                      ),
                    ),
                  ),
                ),
                _buildBottomNavigation(),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.only(top: 40.0),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              SvgPicture.asset(
                "assets/images/iconeFitai.svg",
                width: 40,
                height: 40,
              ),
              const SizedBox(width: 16),
              Text(
                'FitAI',
                style: GoogleFonts.jockeyOne(
                  fontSize: 40,
                  fontWeight: FontWeight.bold,
                  color: const Color(0xFF00BCD4),
                  letterSpacing: 1,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _buildMotivationalMessage(ReportsProvider provider) {
    String message = 'Mantenha a constância e\ntreinos regulares!';
    
    if (provider.stats != null) {
      if (provider.stats!.currentStreak >= 7) {
        message = '🔥 ${provider.stats!.currentStreak} dias sem falhar!\nVocê é imparável!';
      } else if (provider.stats!.currentStreak >= 3) {
        message = '💪 Sequência de ${provider.stats!.currentStreak} dias!\nContinue firme!';
      }
    }

    return Center(
      child: Text(
        message,
        style: GoogleFonts.jockeyOne(
          color: const Color(0xFF00BCD4),
          fontSize: 24,
          fontWeight: FontWeight.w500,
          height: 1.3,
        ),
        textAlign: TextAlign.center,
      ),
    );
  }

  Widget _buildMetricsCards(ReportsProvider provider) {
    final stats = provider.stats;

    final metrics = [
      {'value': stats?.totalWorkouts.toString() ?? '0', 'label': 'Treinos'},
      {'value': stats?.formattedTotalDuration ?? '0h', 'label': 'Horas de\ntreinos'},
      {'value': stats?.currentStreak.toString() ?? '0', 'label': 'Dias\nConsecutivos'},
    ];

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Métricas de treinos',
            style: GoogleFonts.jockeyOne(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: metrics.map((metric) {
              return Column(
                children: [
                  Container(
                    width: 90,
                    height: 90,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: const Color(0xFF00BCD4), width: 3),
                      color: const Color(0xFF2A2A2A),
                    ),
                    child: Center(
                      child: Text(
                        metric['value']!,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    metric['label']!,
                    style: const TextStyle(color: Color(0xFF9E9E9E), fontSize: 11),
                    textAlign: TextAlign.center,
                  ),
                ],
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildWeeklyFrequencyChart(ReportsProvider provider) {
    final totalThisWeek = provider.thisWeekWorkouts.length;
    
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Treinos desta semana',
            style: GoogleFonts.jockeyOne(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: const Color(0xFF2A2A2A),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFF00BCD4), width: 1.5),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                Container(
                  width: 120,
                  height: 120,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: const Color(0xFF00BCD4),
                      width: 8,
                    ),
                  ),
                  child: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          '$totalThisWeek',
                          style: GoogleFonts.jockeyOne(
                            color: Colors.white,
                            fontSize: 48,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          totalThisWeek == 1 ? 'treino' : 'treinos',
                          style: const TextStyle(
                            color: Color(0xFF9E9E9E),
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildWeekInfo(
                      'Meta semanal',
                      '3-5 treinos',
                      Icons.flag,
                    ),
                    const SizedBox(height: 16),
                    _buildWeekInfo(
                      'Progresso',
                      _getProgressText(totalThisWeek),
                      Icons.trending_up,
                      color: _getProgressColor(totalThisWeek),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWeekInfo(String label, String value, IconData icon, {Color? color}) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: (color ?? const Color(0xFF00BCD4)).withOpacity(0.2),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(
            icon,
            color: color ?? const Color(0xFF00BCD4),
            size: 20,
          ),
        ),
        const SizedBox(width: 12),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label,
              style: const TextStyle(
                color: Color(0xFF9E9E9E),
                fontSize: 12,
              ),
            ),
            Text(
              value,
              style: TextStyle(
                color: color ?? Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ],
    );
  }

  String _getProgressText(int total) {
    if (total == 0) return 'Comece hoje!';
    if (total < 3) return 'Continue!';
    if (total <= 5) return 'Excelente!';
    return 'Incrível!';
  }

  Color _getProgressColor(int total) {
    if (total == 0) return const Color(0xFF9E9E9E);
    if (total < 3) return Colors.orange;
    if (total <= 5) return const Color(0xFF00BCD4);
    return Colors.green;
  }

  Widget _buildCalendarHeatmap(ReportsProvider provider) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    
    final last28Days = List.generate(28, (index) {
      return today.subtract(Duration(days: 27 - index));
    });
    
    final weeks = <List<DateTime?>>[];
    var currentWeek = <DateTime?>[];
    
    final firstDayWeekday = last28Days.first.weekday;
    for (int i = 0; i < firstDayWeekday % 7; i++) {
      currentWeek.add(null);
    }
    
    for (var day in last28Days) {
      if (currentWeek.length == 7) {
        weeks.add(currentWeek);
        currentWeek = <DateTime?>[];
      }
      currentWeek.add(day);
    }
    
    while (currentWeek.length < 7) {
      currentWeek.add(null);
    }
    if (currentWeek.isNotEmpty) {
      weeks.add(currentWeek);
    }
    
    bool hasWorkout(DateTime? date) {
      if (date == null) return false;
      return provider.workoutHistory.any((workout) =>
        workout.date.year == date.year &&
        workout.date.month == date.month &&
        workout.date.day == date.day
      );
    }

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Calendário de treinos',
            style: GoogleFonts.jockeyOne(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF2A2A2A),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFF00BCD4), width: 1.5),
            ),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'].map((day) {
                    return SizedBox(
                      width: 35,
                      child: Text(
                        day,
                        style: const TextStyle(
                          color: Color(0xFF9E9E9E),
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 12),
                ...weeks.map((week) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: week.map((date) {
                        final isToday = date != null && 
                          date.year == today.year &&
                          date.month == today.month &&
                          date.day == today.day;
                        
                        final hadWorkout = hasWorkout(date);
                        
                        return Container(
                          width: 35,
                          height: 35,
                          decoration: BoxDecoration(
                            color: date == null
                                ? Colors.transparent
                                : hadWorkout
                                    ? const Color(0xFF00BCD4)
                                    : const Color(0xFF404040),
                            borderRadius: BorderRadius.circular(6),
                            border: isToday
                                ? Border.all(
                                    color: Colors.white,
                                    width: 2,
                                  )
                                : null,
                          ),
                          child: date != null
                              ? Center(
                                  child: Text(
                                    '${date.day}',
                                    style: TextStyle(
                                      color: hadWorkout
                                          ? Colors.white
                                          : const Color(0xFF666666),
                                      fontSize: 10,
                                      fontWeight: isToday 
                                          ? FontWeight.bold 
                                          : FontWeight.normal,
                                    ),
                                  ),
                                )
                              : null,
                        );
                      }).toList(),
                    ),
                  );
                }).toList(),
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      width: 14,
                      height: 14,
                      decoration: BoxDecoration(
                        color: const Color(0xFF00BCD4),
                        borderRadius: BorderRadius.circular(3),
                      ),
                    ),
                    const SizedBox(width: 8),
                    const Text(
                      'Treinou',
                      style: TextStyle(
                        color: Color(0xFF9E9E9E),
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(width: 24),
                    Container(
                      width: 14,
                      height: 14,
                      decoration: BoxDecoration(
                        color: const Color(0xFF404040),
                        borderRadius: BorderRadius.circular(3),
                      ),
                    ),
                    const SizedBox(width: 8),
                    const Text(
                      'Descanso',
                      style: TextStyle(
                        color: Color(0xFF9E9E9E),
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Color _getCategoryColor(String category) {
    switch (category.toLowerCase()) {
      case 'força':
        return Colors.red.shade400;
      case 'cardio':
        return Colors.orange.shade400;
      case 'hipertrofia':
        return Colors.purple.shade400;
      case 'resistência':
        return Colors.blue.shade400;
      case 'flexibilidade':
        return Colors.green.shade400;
      default:
        return const Color(0xFF00BCD4);
    }
  }

 Widget _buildWeightCard(ReportsProvider provider) {
  final weightHistory = provider.weightHistory;
  final hasWeight = weightHistory.isNotEmpty;
  final currentWeight = hasWeight ? weightHistory.last.weight : null;

  return Padding(
    padding: const EdgeInsets.symmetric(horizontal: 24),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Peso Atual',
          style: GoogleFonts.jockeyOne(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: const Color(0xFF2A2A2A),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFF00BCD4), width: 1.5),
          ),
          child: Column(
            children: [
              // PESO ATUAL
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Peso registrado',
                        style: TextStyle(
                          color: Color(0xFF9E9E9E),
                          fontSize: 12,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        currentWeight != null 
                            ? '${currentWeight.toStringAsFixed(1)} kg'
                            : 'Não registrado',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 24,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                  ElevatedButton(
                    onPressed: () => _showUpdateWeightDialog(provider),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF00BCD4),
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      minimumSize: const Size(0, 32),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(20),
                      ),
                    ),
                    child: const Text('Atualizar', style: TextStyle(fontSize: 12)),
                  ),
                ],
              ),
              
              // MENSAGEM SE NÃO TEM PESO
              if (!hasWeight) ...[
                const SizedBox(height: 20),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFF404040),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Row(
                    children: [
                      Icon(
                        Icons.info_outline,
                        color: Color(0xFF00BCD4),
                        size: 20,
                      ),
                      SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'Adicione seu peso para começar o acompanhamento',
                          style: TextStyle(
                            color: Color(0xFF9E9E9E),
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
              
              // GRÁFICO DE HISTÓRICO
              if (hasWeight && weightHistory.length > 1) ...[
                const SizedBox(height: 24),
                _buildWeightChart(weightHistory),
              ],
            ],
          ),
        ),
      ],
    ),
  );
}

// ============================================================
// GRÁFICO DE PESO
// ============================================================

Widget _buildWeightChart(List<WeightEntry> weightHistory) {
  if (weightHistory.isEmpty) return const SizedBox.shrink();

  final sorted = List<WeightEntry>.from(weightHistory)
    ..sort((a, b) => a.date.compareTo(b.date));

  final recentWeights = sorted.length > 10 
      ? sorted.sublist(sorted.length - 10)
      : sorted;

  final weights = recentWeights.map((w) => w.weight).toList();
  final minWeight = weights.reduce((a, b) => a < b ? a : b);
  final maxWeight = weights.reduce((a, b) => a > b ? a : b);
  final range = maxWeight - minWeight;
  
  final adjustedRange = range == 0 ? 5.0 : range;

  return Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        'Histórico de Peso (últimas ${recentWeights.length} entradas)',
        style: const TextStyle(
          color: Color(0xFF9E9E9E),
          fontSize: 12,
          fontWeight: FontWeight.w500,
        ),
      ),
      const SizedBox(height: 16),

      Container(
        height: 200,
        padding: const EdgeInsets.only(bottom: 16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: recentWeights.asMap().entries.map((entry) {
            final index = entry.key;
            final weightEntry = entry.value;  // ⭐ RENOMEADO para evitar conflito
            final weight = weightEntry.weight;
            final date = weightEntry.date;
            
            final normalizedWeight = (weight - minWeight) / adjustedRange;
            final barHeight = (normalizedWeight * 150).clamp(10.0, 150.0);

            final isLatest = index == recentWeights.length - 1;
            final isLowest = weight == minWeight;
            final barColor = isLatest  // ⭐ RENOMEADO de 'color' para 'barColor'
                ? const Color(0xFF00BCD4)
                : isLowest
                    ? Colors.orange.shade400
                    : Colors.green.shade400;

            return Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    Text(
                      weight.toStringAsFixed(1),
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 10,
                        fontWeight: isLatest ? FontWeight.bold : FontWeight.normal,
                      ),
                    ),
                    const SizedBox(height: 4),
                    
                    Container(
                      width: double.infinity,
                      height: barHeight,
                      decoration: BoxDecoration(
                        color: barColor.withOpacity(0.7),  // ⭐ Usando barColor
                        borderRadius: const BorderRadius.vertical(
                          top: Radius.circular(6),
                        ),
                        border: Border.all(
                          color: barColor,  // ⭐ Usando barColor
                          width: isLatest ? 2 : 1,
                        ),
                      ),
                      child: isLatest
                          ? const Center(
                              child: Icon(
                                Icons.check_circle,
                                size: 16,
                                color: Color(0xFF00BCD4),
                              ),
                            )
                          : null,
                    ),
                    const SizedBox(height: 4),
                    
                    if (index % 2 == 0 || index == recentWeights.length - 1)
                      Text(
                        '${date.day}/${date.month}',
                        style: const TextStyle(
                          color: Color(0xFF9E9E9E),
                          fontSize: 9,
                        ),
                      ),
                  ],
                ),
              ),
            );
          }).toList(),
        ),
      ),

      const SizedBox(height: 12),
      Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: const Color(0xFF404040),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _buildWeightStat(
              label: 'Inicial',
              value: '${recentWeights.first.weight.toStringAsFixed(1)} kg',
              icon: Icons.arrow_upward,
            ),
            _buildWeightStat(
              label: 'Atual',
              value: '${recentWeights.last.weight.toStringAsFixed(1)} kg',
              icon: Icons.fitness_center,
            ),
            _buildWeightStat(
              label: 'Variação',
              value: '${(recentWeights.last.weight - recentWeights.first.weight).toStringAsFixed(1)} kg',
              icon: (recentWeights.last.weight - recentWeights.first.weight) < 0
                  ? Icons.trending_down
                  : Icons.trending_up,
            ),
          ],
        ),
      ),
    ],
  );
}

// ============================================================
// ESTATÍSTICA INDIVIDUAL
// ============================================================

Widget _buildWeightStat({
  required String label,
  required String value,
  required IconData icon,
}) {
  return Column(
    children: [
      Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: 14,
            color: const Color(0xFF00BCD4),
          ),
          const SizedBox(width: 4),
          Text(
            label,
            style: const TextStyle(
              color: Color(0xFF9E9E9E),
              fontSize: 11,
            ),
          ),
        ],
      ),
      const SizedBox(height: 4),
      Text(
        value,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 13,
          fontWeight: FontWeight.w600,
        ),
      ),
    ],
  );
}

void _showUpdateWeightDialog(ReportsProvider provider) {
  final controller = TextEditingController();

  showDialog(
    context: context,
    builder: (dialogContext) => AlertDialog(
      backgroundColor: const Color(0xFF2A2A2A),
      title: Text('Atualizar Peso', style: GoogleFonts.jockeyOne(color: Colors.white)),
      content: TextField(
        controller: controller,
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        style: const TextStyle(color: Colors.white),
        decoration: const InputDecoration(
          labelText: 'Peso (kg)',
          labelStyle: TextStyle(color: Color(0xFF9E9E9E)),
          suffixText: 'kg',
          suffixStyle: TextStyle(color: Color(0xFF9E9E9E)),
          enabledBorder: OutlineInputBorder(
            borderSide: BorderSide(color: Color(0xFF00BCD4)),
          ),
          focusedBorder: OutlineInputBorder(
            borderSide: BorderSide(color: Color(0xFF00BCD4), width: 2),
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(dialogContext),
          child: const Text('Cancelar', style: TextStyle(color: Color(0xFF9E9E9E))),
        ),
        ElevatedButton(
          onPressed: () async {
            final weight = double.tryParse(controller.text);
            if (weight != null && weight > 0) {
              Navigator.pop(dialogContext);
              final success = await provider.updateWeight(weight);
              
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(
                      success ? 'Peso atualizado com sucesso!' : 'Erro ao atualizar peso'
                    ),
                    backgroundColor: success ? Colors.green : Colors.red,
                  ),
                );
              }
            }
          },
          style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF00BCD4)),
          child: const Text('Salvar'),
        ),
      ],
    ),
  );
}

 

  Widget _buildStatsCards(ReportsProvider provider) {
    final stats = provider.stats!;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        children: [
          _buildStatCard(
            icon: Icons.favorite,
            title: 'Exercício Preferido',
            value: stats.favoriteExercise,
            subtitle: '${stats.favoriteExerciseCount} vezes realizado',
          ),
          const SizedBox(height: 12),
          _buildStatCard(
            icon: Icons.timer,
            title: 'Duração Média',
            value: '${stats.averageDuration.toInt()} min',
            subtitle: 'Por treino',
          ),
          const SizedBox(height: 12),
          _buildStatCard(
            icon: Icons.local_fire_department,
            title: 'Calorias Totais',
            value: '${stats.totalCalories} kcal',
            subtitle: 'Queimadas no período',
          ),
          const SizedBox(height: 12),
          _buildStatCard(
            icon: Icons.fitness_center,
            title: 'Grupo Mais Trabalhado',
            value: stats.mostTrainedMuscleGroup,
            subtitle: 'Foco principal',
          ),
        ],
      ),
    );
  }

  Widget _buildStatCard({
    required IconData icon,
    required String title,
    required String value,
    required String subtitle,
  }) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF2A2A2A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF00BCD4), width: 1.5),
      ),
      child: Row(
        children: [
          Container(
            width: 50,
            height: 50,
            decoration: BoxDecoration(
              color: const Color(0xFF00BCD4).withOpacity(0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: const Color(0xFF00BCD4), size: 24),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(color: Color(0xFF9E9E9E), fontSize: 12),
                ),
                const SizedBox(height: 4),
                Text(
                  value,
                  style: GoogleFonts.jockeyOne(
                    color: Colors.white,
                    fontSize: 20,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  subtitle,
                  style: const TextStyle(color: Color(0xFF9E9E9E), fontSize: 11),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBottomNavigation() {
    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFF2A2A2A),
        border: Border(top: BorderSide(color: Color(0xFF424242), width: 1)),
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 12),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildNavItem('Inicio', Icons.home, false),
              _buildNavItem('Treinos', Icons.fitness_center, false),
              _buildNavItem('Relatórios', Icons.bar_chart, true),
              _buildNavItem('Chatbot', Icons.chat_bubble_outline, false),
              _buildNavItem('Perfil', Icons.person, false),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(String label, IconData icon, bool isActive) {
    return GestureDetector(
      onTap: () {
        if (label == 'Inicio') {
          AppRouter.goToDashboard();
        } else if (label == 'Treinos') {
          AppRouter.goToWorkouts();
        } else if (label == 'Chatbot') {
          AppRouter.goToChatBot();
        } else if (label == 'Perfil') {
          AppRouter.goToProfile();
        }
      },
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            color: isActive ? const Color(0xFF00BCD4) : const Color(0xFF9E9E9E),
            size: 24,
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(
              color: isActive ? const Color(0xFF00BCD4) : const Color(0xFF9E9E9E),
              fontSize: 10,
            ),
          ),
        ],
      ),
    );
  }
}

// ============================================================
// WIDGET DE HISTÓRICO COM EXPANSÃO
// ============================================================

class _WorkoutHistorySection extends StatefulWidget {
  final ReportsProvider provider;

  const _WorkoutHistorySection({required this.provider});

  @override
  State<_WorkoutHistorySection> createState() => _WorkoutHistorySectionState();
}

class _WorkoutHistorySectionState extends State<_WorkoutHistorySection> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    final workouts = widget.provider.workoutHistory;

    if (workouts.isEmpty) {
      return Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Último treino',
              style: GoogleFonts.jockeyOne(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: const Color(0xFF2A2A2A),
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Center(
                child: Text(
                  'Nenhum treino registrado ainda',
                  style: TextStyle(
                    color: Color(0xFF9E9E9E),
                    fontSize: 14,
                  ),
                ),
              ),
            ),
          ],
        ),
      );
    }

    final lastWorkout = workouts.first;
    final hasMoreWorkouts = workouts.length > 1;
    final remainingWorkouts = workouts.skip(1).take(9).toList();

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Último treino',
            style: GoogleFonts.jockeyOne(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 12),
          
          // CARD DO ÚLTIMO TREINO (DESTACADO)
          _buildLastWorkoutCard(lastWorkout),
          
          // BOTÃO VER MAIS
          if (hasMoreWorkouts) ...[
            const SizedBox(height: 12),
            Center(
              child: TextButton.icon(
                onPressed: () {
                  setState(() {
                    _isExpanded = !_isExpanded;
                  });
                },
                style: TextButton.styleFrom(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 20,
                    vertical: 10,
                  ),
                ),
                icon: Icon(
                  _isExpanded ? Icons.expand_less : Icons.expand_more,
                  size: 20,
                  color: const Color(0xFF00BCD4),
                ),
                label: Text(
                  _isExpanded 
                      ? 'Ver menos' 
                      : 'Ver mais (${workouts.length - 1})',
                  style: const TextStyle(
                    color: Color(0xFF00BCD4),
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
          ],
          
          // LISTA EXPANDIDA
          AnimatedSize(
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeInOut,
            child: _isExpanded
                ? Column(
                    children: [
                      const SizedBox(height: 4),
                      ListView.separated(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: remainingWorkouts.length,
                        separatorBuilder: (context, index) => 
                            const SizedBox(height: 12),
                        itemBuilder: (context, index) {
                          return TweenAnimationBuilder(
                            tween: Tween<double>(begin: 0, end: 1),
                            duration: Duration(milliseconds: 200 + (index * 50)),
                            curve: Curves.easeOut,
                            builder: (context, value, child) {
                              return Transform.translate(
                                offset: Offset(0, 10 * (1 - value)),
                                child: Opacity(
                                  opacity: value,
                                  child: child,
                                ),
                              );
                            },
                            child: _buildCompactWorkoutCard(remainingWorkouts[index]),
                          );
                        },
                      ),
                    ],
                  )
                : const SizedBox.shrink(),
          ),
        ],
      ),
    );
  }

  // CARD PRINCIPAL DO ÚLTIMO TREINO
  Widget _buildLastWorkoutCard(WorkoutHistoryModel workout) {
    // CORREÇÃO: Se completed=true, força 100%, senão calcula normalmente
    final progress = workout.completed 
        ? 1.0 
        : (workout.totalExercises > 0 
            ? workout.exercisesCompleted / workout.totalExercises 
            : 0.0);

    return TweenAnimationBuilder(
      tween: Tween<double>(begin: 0, end: 1),
      duration: const Duration(milliseconds: 400),
      curve: Curves.easeOut,
      builder: (context, value, child) {
        return Transform.scale(
          scale: 0.95 + (0.05 * value),
          child: Opacity(
            opacity: value,
            child: child,
          ),
        );
      },
      child: InkWell(
        onTap: () {
          print('Ver detalhes do treino #${workout.id}');
        },
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFF2A2A2A),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: const Color(0xFF00BCD4),
              width: 1.5,
            ),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF00BCD4).withOpacity(0.15),
                blurRadius: 12,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Column(
            children: [
              Row(
                children: [
                  // Ícone com badge "NOVO"
                  Stack(
                    clipBehavior: Clip.none,
                    children: [
                      Container(
                        width: 50,
                        height: 50,
                        decoration: BoxDecoration(
                          color: const Color(0xFF00BCD4).withOpacity(0.2),
                          borderRadius: BorderRadius.circular(25),
                        ),
                        child: const Icon(
                          Icons.fitness_center,
                          color: Color(0xFF00BCD4),
                          size: 24,
                        ),
                      ),
                      Positioned(
                        top: -4,
                        right: -4,
                        child: Container(
                          padding: const EdgeInsets.all(4),
                          decoration: BoxDecoration(
                            color: const Color(0xFF00BCD4),
                            shape: BoxShape.circle,
                            boxShadow: [
                              BoxShadow(
                                color: const Color(0xFF00BCD4).withOpacity(0.5),
                                blurRadius: 8,
                                spreadRadius: 2,
                              ),
                            ],
                          ),
                          child: const Icon(
                            Icons.fiber_manual_record,
                            size: 8,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(width: 16),
                  
                  // Informações
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Categoria e tempo
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 3,
                              ),
                              decoration: BoxDecoration(
                                color: _getCategoryColor(workout.category).withOpacity(0.2),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: Text(
                                workout.category,
                                style: TextStyle(
                                  color: _getCategoryColor(workout.category),
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                            const Spacer(),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 4,
                              ),
                              decoration: BoxDecoration(
                                color: const Color(0xFF00BCD4).withOpacity(0.2),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(
                                    Icons.schedule,
                                    size: 12,
                                    color: Color(0xFF00BCD4),
                                  ),
                                  const SizedBox(width: 4),
                                  Text(
                                    workout.formattedDuration,
                                    style: const TextStyle(
                                      color: Color(0xFF00BCD4),
                                      fontSize: 10,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        
                        // Nome do treino
                        Text(
                          workout.workoutName,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 8),
                        
                        // Grupos musculares
                        if (workout.muscleGroups.isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 8),
                            child: Wrap(
                              spacing: 6,
                              runSpacing: 4,
                              children: workout.muscleGroups.take(3).map((muscle) {
                                return Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 8,
                                    vertical: 3,
                                  ),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFF00BCD4).withOpacity(0.15),
                                    borderRadius: BorderRadius.circular(6),
                                    border: Border.all(
                                      color: const Color(0xFF00BCD4).withOpacity(0.3),
                                      width: 0.5,
                                    ),
                                  ),
                                  child: Text(
                                    muscle,
                                    style: const TextStyle(
                                      color: Color(0xFF00BCD4),
                                      fontSize: 10,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                );
                              }).toList(),
                            ),
                          ),
                        
                        // Métricas
                        Row(
                          children: [
                            Expanded(
                              child: Row(
                                children: [
                                  const Icon(
                                    Icons.check_circle_outline,
                                    size: 14,
                                    color: Color(0xFF9E9E9E),
                                  ),
                                  const SizedBox(width: 4),
                                  Flexible(
                                    child: Text(
                                      '${workout.exercisesCompleted}/${workout.totalExercises}',
                                      style: const TextStyle(
                                        color: Color(0xFF9E9E9E),
                                        fontSize: 12,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            Expanded(
                              child: Row(
                                children: [
                                  const Icon(
                                    Icons.timer_outlined,
                                    size: 14,
                                    color: Color(0xFF9E9E9E),
                                  ),
                                  const SizedBox(width: 4),
                                  Flexible(
                                    child: Text(
                                      workout.formattedDuration,
                                      style: const TextStyle(
                                        color: Color(0xFF9E9E9E),
                                        fontSize: 12,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              
              // Barra de progresso ou badge de conclusão
              if (progress < 1.0) ...[
                const SizedBox(height: 12),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'Progresso',
                          style: TextStyle(
                            color: Colors.grey.shade400,
                            fontSize: 11,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        Text(
                          '${(progress * 100).toInt()}%',
                          style: const TextStyle(
                            color: Color(0xFF00BCD4),
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: progress,
                        backgroundColor: Colors.grey.shade800,
                        color: const Color(0xFF00BCD4),
                        minHeight: 6,
                      ),
                    ),
                  ],
                ),
              ] else if (workout.completed) ...[
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.green.shade900.withOpacity(0.3),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: Colors.green.shade700,
                      width: 1,
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.check_circle,
                        size: 16,
                        color: Colors.green.shade400,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        'Treino Concluído',
                        style: TextStyle(
                          color: Colors.green.shade400,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  // CARDS COMPACTOS DOS OUTROS TREINOS
  Widget _buildCompactWorkoutCard(WorkoutHistoryModel workout) {
    // CORREÇÃO: Se completed=true, força 100%, senão calcula normalmente
    final progress = workout.completed 
        ? 1.0 
        : (workout.totalExercises > 0 
            ? workout.exercisesCompleted / workout.totalExercises 
            : 0.0);

    return InkWell(
      onTap: () {
        print('Ver detalhes do treino #${workout.id}');
      },
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: const Color(0xFF2A2A2A),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          children: [
            Row(
              children: [
                // Ícone menor
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: const Color(0xFF00BCD4).withOpacity(0.15),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Icon(
                    Icons.fitness_center,
                    color: Color(0xFF00BCD4),
                    size: 20,
                  ),
                ),
                const SizedBox(width: 12),
                
                // Informações
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Categoria e tempo
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 6,
                              vertical: 2,
                            ),
                            decoration: BoxDecoration(
                              color: _getCategoryColor(workout.category).withOpacity(0.2),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              workout.category,
                              style: TextStyle(
                                color: _getCategoryColor(workout.category),
                                fontSize: 10,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                          const SizedBox(width: 6),
                          Text(
                            workout.formattedDuration,
                            style: const TextStyle(
                              color: Color(0xFF9E9E9E),
                              fontSize: 11,
                            ),
                          ),
                          const Spacer(),
                          if (workout.completed)
                            Icon(
                              Icons.check_circle,
                              size: 16,
                              color: Colors.green.shade400,
                            ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      
                      // Nome do treino
                      Text(
                        workout.workoutName,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 6),
                      
                      // Grupos musculares inline
                      if (workout.muscleGroups.isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 4),
                          child: Text(
                            workout.muscleGroups.take(3).join(' • '),
                            style: const TextStyle(
                              color: Color(0xFF00BCD4),
                              fontSize: 10,
                              fontWeight: FontWeight.w500,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      
                      // Métricas em linha
                      Row(
                        children: [
                          Icon(
                            Icons.check_circle_outline,
                            size: 12,
                            color: Colors.grey.shade500,
                          ),
                          const SizedBox(width: 3),
                          Text(
                            '${workout.exercisesCompleted}/${workout.totalExercises}',
                            style: TextStyle(
                              color: Colors.grey.shade400,
                              fontSize: 11,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Icon(
                            Icons.timer_outlined,
                            size: 12,
                            color: Colors.grey.shade500,
                          ),
                          const SizedBox(width: 3),
                          Text(
                            workout.formattedDuration,
                            style: TextStyle(
                              color: Colors.grey.shade400,
                              fontSize: 11,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Icon(
                            Icons.local_fire_department,
                            size: 12,
                            color: Colors.orange.shade400,
                          ),
                          const SizedBox(width: 3),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
            
            // Barra de progresso (apenas se incompleto)
            if (progress < 1.0) ...[
              const SizedBox(height: 8),
              ClipRRect(
                borderRadius: BorderRadius.circular(3),
                child: LinearProgressIndicator(
                  value: progress,
                  backgroundColor: Colors.grey.shade800,
                  color: const Color(0xFF00BCD4),
                  minHeight: 4,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Color _getCategoryColor(String category) {
    switch (category.toLowerCase()) {
      case 'força':
        return Colors.red.shade400;
      case 'cardio':
        return Colors.orange.shade400;
      case 'hipertrofia':
        return Colors.purple.shade400;
      case 'resistência':
        return Colors.blue.shade400;
      case 'flexibilidade':
        return Colors.green.shade400;
      default:
        return const Color(0xFF00BCD4);
    }
  }
}