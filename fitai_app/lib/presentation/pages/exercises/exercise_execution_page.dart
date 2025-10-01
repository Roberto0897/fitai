import 'package:flutter/material.dart';
import 'package:flutter/services.dart'; 
import '../../../core/theme/app_theme.dart';
import '../../../core/router/app_router.dart';
// Certifique-se de que essas classes existam ou use mock-ups
import '../workouts/workout_detail_page.dart'; 
import 'package:flutter_svg/flutter_svg.dart';
import 'rest_page.dart'; 

// -----------------------------------------------------------------------------------
// MODELOS MOCK
// -----------------------------------------------------------------------------------


class SeriesData {
  int number;
  double weight;
  int reps;
  bool isCompleted;
  final TextEditingController weightController;
  final TextEditingController repsController;

  SeriesData({
    required this.number,
    required this.weight,
    required this.reps,
    required this.isCompleted,
    required this.weightController,
    required this.repsController,
  });
}

// -----------------------------------------------------------------------------------
// CLASSE PRINCIPAL
// -----------------------------------------------------------------------------------

class ExerciseExecutionPage extends StatefulWidget {
  final ExerciseModel exercise;
  final int totalExercises;
  final int currentExerciseIndex;

  const ExerciseExecutionPage({
    super.key,
    required this.exercise,
    required this.totalExercises,
    required this.currentExerciseIndex,
  });

  @override
  State<ExerciseExecutionPage> createState() => _ExerciseExecutionPageState();
}

class _ExerciseExecutionPageState extends State<ExerciseExecutionPage> {
  final List<SeriesData> _series = [];
  int _completedSeries = 0;

  @override
  void initState() {
    super.initState();
    _initializeSeries();
  }

  @override
  void dispose() {
    for (var s in _series) {
      s.weightController.dispose();
      s.repsController.dispose();
    }
    super.dispose();
  }
  
  // --- LÓGICA DE SÉRIES ---

  void _initializeSeries() {
    for (int i = 0; i < 4; i++) {
      _addSeries(i + 1);
    }
  }

  void _addSeries(int seriesNumber) {
    setState(() {
      final initialWeight = 0.0;
      final initialReps = 0;
      
      final newSeries = SeriesData(
        number: seriesNumber,
        weight: initialWeight,
        reps: initialReps,
        isCompleted: false,
        weightController: TextEditingController(text: initialWeight.toStringAsFixed(1)),
        repsController: TextEditingController(text: initialReps.toString()),
      );
      _series.add(newSeries);
    });
  }

  void _removeSeries(int index) {
    if (_series.length <= 1) return;
    
    setState(() {
      final removedSeries = _series.removeAt(index);
      removedSeries.weightController.dispose();
      removedSeries.repsController.dispose();

      for (int i = index; i < _series.length; i++) {
        _series[i].number = i + 1;
      }
      
      if (removedSeries.isCompleted) {
        _completedSeries--;
      }
    });
  }

  void _completeSeries(int index) {
    final series = _series[index];
    
    series.weight = double.tryParse(series.weightController.text.replaceAll(',', '.')) ?? 0.0;
    series.reps = int.tryParse(series.repsController.text) ?? 0;

    if (series.weight <= 0.0 || series.reps <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Preencha peso e repetições (maior que zero) antes de concluir'),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }

    setState(() {
      _series[index].isCompleted = true;
      _completedSeries++;
    });

    if (index < _series.length - 1) {
      _goToRest();
    }
  }

  // --- MÉTODOS DE NAVEGAÇÃO (CORRIGIDOS) ---

  // Método _goToRest (Corrigido o undefined_method)
  void _goToRest() {
    Navigator.of(context).push(
      PageRouteBuilder(
        opaque: false,
        barrierDismissible: false,
        barrierColor: Colors.black.withOpacity(0.5),
        pageBuilder: (context, animation, secondaryAnimation) {
          return RestPage(
            onRestComplete: () {
              Navigator.of(context).pop();
            },
          );
        },
        transitionsBuilder: (context, animation, secondaryAnimation, child) {
          return FadeTransition(
            opacity: animation,
            child: child,
          );
        },
      ),
    );
  }

  // Método _goToNextExercise (Corrigido o undefined_identifier)
  void _goToNextExercise() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Indo para o próximo exercício...'),
        backgroundColor: AppColors.primary,
      ),
    );
    // Assumindo que AppRouter.goBack() é o método para fechar esta tela.
    AppRouter.goBack(); 
  }


  // --- WIDGET BUILD OBRIGATÓRIO ---
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),
            Expanded(
              child: SingleChildScrollView(
                child: Column(
                  children: [
                    _buildExerciseInfo(),
                    _buildSeriesList(),
                    // Botão para adicionar série
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                      child: OutlinedButton.icon(
                        icon: const Icon(Icons.add_circle_outline, color: AppColors.primary),
                        label: const Text('Adicionar Série', style: TextStyle(color: AppColors.primary)),
                        style: OutlinedButton.styleFrom(
                          minimumSize: const Size(double.infinity, 50),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          side: const BorderSide(color: AppColors.primary, width: 1.5),
                        ),
                        onPressed: () => _addSeries(_series.length + 1),
                      ),
                    ),
                    const SizedBox(height: 100), // Espaço para o botão fixo
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: _buildBottomBar(),
    );
  }
  // --------------------------------

  // --- WIDGETS DE CONSTRUÇÃO ---

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppColors.primary,
            // Corrigido para usar withOpacity (solução para o erro String? -> String)
            AppColors.primary.withOpacity(0.7), 
          ],
        ),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              GestureDetector(
                onTap: () => _showExitDialog(),
                child: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    // Corrigido para usar withOpacity
                    color: Colors.white.withOpacity(0.2), 
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(Icons.close, color: Colors.white),
                ),
              ),
              GestureDetector(
                onTap: () => _showOptionsMenu(),
                child: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    // Corrigido para usar withOpacity
                    color: Colors.white.withOpacity(0.2), 
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(Icons.more_horiz, color: Colors.white),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          const Text('Treino em andamento', style: TextStyle(fontSize: 14, color: Colors.white70)),
          const SizedBox(height: 8),
          const Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.fitness_center, color: Colors.white, size: 20),
              SizedBox(width: 8),
              Text('Push day - Peito e Tríceps', style: TextStyle(fontSize: 16, color: Colors.white, fontWeight: FontWeight.w600)),
            ],
          ),
        ],
      ),
    );
  }

Widget _buildExerciseInfo() {
  return Container(
    margin: const EdgeInsets.all(20),
    padding: const EdgeInsets.all(20),
    decoration: BoxDecoration(
      color: AppColors.surface,
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: AppColors.primary.withOpacity(0.2)),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(widget.exercise.name, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white)),
        const SizedBox(height: 8),
        Text('${widget.exercise.muscleGroup} - Exercício ${widget.currentExerciseIndex} de ${widget.totalExercises}', style: const TextStyle(fontSize: 14, color: AppColors.textSecondary)),
        const SizedBox(height: 16),
        Container(
          height: 180,
          width: double.infinity,
          decoration: BoxDecoration(color: AppColors.background, borderRadius: BorderRadius.circular(12)),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(12),
            // --- AQUI ESTÁ A MUDANÇA PARA USAR SVG ---
            child: Stack( // Usamos Stack para poder aplicar o BlendMode se necessário
              fit: StackFit.expand,
              children: [
                Image.asset(
                  "images/supinoBarra.png", 
                  alignment: Alignment.center,
                  fit: BoxFit.contain, // ou BoxFit.cover dependendo do que você precisa
                  ), // Opcional: placeholder enquanto o SVG carrega
                // Se você ainda quiser a sobreposição escura do BlendMode, pode adicionar um Container por cima
                // Container(color: Colors.black.withOpacity(0.3)), 
              ],
            ),
            // --- FIM DA MUDANÇA ---
          ),
        ),
      ],
    ),
  );
}
  Widget _buildSeriesList() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Séries', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
          const SizedBox(height: 16),
          ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: _series.length,
            itemBuilder: (context, index) {
              return _buildSeriesItem(_series[index], index);
            },
          ),
        ],
      ),
    );
  }
  
 Widget _buildSeriesItem(SeriesData series, int index) {
  return Container(
    margin: const EdgeInsets.only(bottom: 12),
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: series.isCompleted ? AppColors.primary.withOpacity(0.1) : AppColors.surface,
      borderRadius: BorderRadius.circular(16),
      border: Border.all(
        color: series.isCompleted ? AppColors.primary : AppColors.primary.withOpacity(0.2),
        width: series.isCompleted ? 2 : 1,
      ),
    ),
    child: Row(
      children: [
        // Número da série
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: series.isCompleted ? AppColors.primary : AppColors.background,
            shape: BoxShape.circle,
          ),
          child: Center(
            child: Text(
              '${series.number}',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: series.isCompleted ? Colors.white : AppColors.primary,
              ),
            ),
          ),
        ),
        
        const SizedBox(width: 16),
        
        // Peso (KG)
        Expanded(
          child: _buildQuantityInputField(
            label: 'KG',
            controller: series.weightController,
            enabled: !series.isCompleted,
            isWeight: true,
            onChanged: (value) {},
            onDecrement: () {
              setState(() {
                double newValue = (series.weight - 1).clamp(0.0, double.infinity);
                _series[index].weight = newValue;
                series.weightController.text = newValue.toStringAsFixed(1);
              });
            },
            onIncrement: () {
              setState(() {
                double newValue = series.weight + 1;
                _series[index].weight = newValue;
                series.weightController.text = newValue.toStringAsFixed(1);
              });
            },
          ),
        ),
        
        const SizedBox(width: 12),
        
        // Repetições (REP)
        Expanded(
          child: _buildQuantityInputField(
            label: 'REP',
            controller: series.repsController,
            enabled: !series.isCompleted,
            isWeight: false,
            onChanged: (value) {},
            onDecrement: () {
              setState(() {
                int newValue = (series.reps - 1).clamp(0, 999);
                _series[index].reps = newValue;
                series.repsController.text = newValue.toString();
              });
            },
            onIncrement: () {
              setState(() {
                int newValue = series.reps + 1;
                _series[index].reps = newValue;
                series.repsController.text = newValue.toString();
              });
            },
          ),
        ),
        
        const SizedBox(width: 12),
        
        // Botão de Concluir a Série
        GestureDetector(
          onTap: series.isCompleted ? null : () => _completeSeries(index),
          child: Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: series.isCompleted ? AppColors.primary : Colors.transparent,
              shape: BoxShape.circle,
              border: Border.all(
                color: series.isCompleted ? AppColors.primary : AppColors.textSecondary.withOpacity(0.5),
                width: 2,
              ),
            ),
            child: Center(
              child: series.isCompleted
                  ? const Icon(Icons.check, color: Colors.white, size: 20)
                  : Icon(Icons.check, color: AppColors.textSecondary.withOpacity(0.5), size: 20),
            ),
          ),
        ),
        
        const SizedBox(width: 8),
        
        // Botão de remover série (agora separado e mais visível)
        if (!series.isCompleted && _series.length > 1)
          GestureDetector(
            onTap: () => _removeSeries(index),
            child: Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: AppColors.error.withOpacity(0.1),
                shape: BoxShape.circle,
                border: Border.all(
                  color: AppColors.error.withOpacity(0.3),
                  width: 1,
                ),
              ),
              child: const Icon(
                Icons.close,
                size: 18,
                color: AppColors.error,
              ),
            ),
          )
        else
          const SizedBox(width: 32), // Espaço vazio para manter alinhamento quando não há botão
      ],
    ),
  );
}

  Widget _buildQuantityInputField({
    required String label,
    required TextEditingController controller,
    required Function(String) onChanged,
    required Function() onDecrement,
    required Function() onIncrement,
    required bool enabled,
    required bool isWeight,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(fontSize: 10, color: enabled ? AppColors.textSecondary : AppColors.textHint, fontWeight: FontWeight.w500)),
        const SizedBox(height: 4),
        Container(
          height: 40,
          decoration: BoxDecoration(
            color: AppColors.background,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: enabled ? AppColors.primary.withOpacity(0.4) : AppColors.textHint.withOpacity(0.2),
              width: 1,
            ),
          ),
          child: Row(
            children: [
              // Botão de Decrementar (-)
              GestureDetector(
                onTap: enabled ? onDecrement : null,
                child: Container(
                  width: 30,
                  alignment: Alignment.center,
                  child: Icon(Icons.remove, size: 16, color: enabled ? AppColors.primary : AppColors.textHint),
                ),
              ),
              // Campo de Texto Editável
              Expanded(
                child: TextFormField(
                  controller: controller,
                  enabled: enabled,
                  textAlign: TextAlign.center,
                  keyboardType: isWeight ? const TextInputType.numberWithOptions(decimal: true) : TextInputType.number,
                  inputFormatters: <TextInputFormatter>[
                    isWeight ? FilteringTextInputFormatter.allow(RegExp(r'^\d*[\.,]?\d*')) : FilteringTextInputFormatter.digitsOnly,
                  ],
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: enabled ? Colors.white : AppColors.textHint),
                  decoration: const InputDecoration(isDense: true, contentPadding: EdgeInsets.zero, border: InputBorder.none),
                  onChanged: onChanged,
                ),
              ),
              // Botão de Incrementar (+)
              GestureDetector(
                onTap: enabled ? onIncrement : null,
                child: Container(
                  width: 30,
                  alignment: Alignment.center,
                  child: Icon(Icons.add, size: 16, color: enabled ? AppColors.primary : AppColors.textHint),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildBottomBar() {
    final allSeriesCompleted = _completedSeries == _series.length;
    
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, -5),
          ),
        ],
      ),
      child: SafeArea(
        child: SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            // Chamada para o método _goToNextExercise (agora definido)
            onPressed: allSeriesCompleted ? _goToNextExercise : null,
            style: ElevatedButton.styleFrom(
              backgroundColor: allSeriesCompleted ? AppColors.primary : AppColors.textHint,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            child: Text(
              allSeriesCompleted ? 'Próximo exercício' : 'Complete todas as séries',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
          ),
        ),
      ),
    );
  }

  // --- MÉTODOS DE DIÁLOGO (Para complementar o Header) ---

  void _showExitDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text('Sair do treino?', style: TextStyle(color: Colors.white)),
        content: const Text('Você perderá o progresso do treino atual.', style: TextStyle(color: AppColors.textSecondary)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              AppRouter.goBack();
            },
            child: const Text('Sair', style: TextStyle(color: AppColors.error)),
          ),
        ],
      ),
    );
  }

  void _showOptionsMenu() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => Container(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(leading: const Icon(Icons.info_outline, color: AppColors.primary), title: const Text('Ver instruções'), onTap: () => Navigator.pop(context)),
            ListTile(leading: const Icon(Icons.swap_horiz, color: AppColors.primary), title: const Text('Substituir exercício'), onTap: () => Navigator.pop(context)),
            ListTile(leading: const Icon(Icons.skip_next, color: AppColors.primary), title: const Text('Pular exercício'), onTap: () => Navigator.pop(context)),
          ],
        ),
      ),
    );
  }
}