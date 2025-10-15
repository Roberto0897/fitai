import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../service/api_service.dart';

class EditWorkoutPage extends StatefulWidget {
  final int workoutId;
  final String workoutName;

  const EditWorkoutPage({
    super.key,
    required this.workoutId,
    required this.workoutName,
  });

  @override
  State<EditWorkoutPage> createState() => _EditWorkoutPageState();
}

class _EditWorkoutPageState extends State<EditWorkoutPage> {
  // Controllers
  late TextEditingController _nameController;
  late TextEditingController _descriptionController;
  late TextEditingController _durationController;
  late TextEditingController _caloriesController;

  // Estados
  String _selectedDifficulty = 'beginner';
  String _selectedType = 'strength';
  bool _isLoading = true;
  bool _isSaving = false;

  // Exercícios
  List<WorkoutExerciseModel> _exercises = [];
  List<int> _exercisesToRemove = [];

  final _formKey = GlobalKey<FormState>();

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController();
    _descriptionController = TextEditingController();
    _durationController = TextEditingController();
    _caloriesController = TextEditingController();
    _loadWorkoutData();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    _durationController.dispose();
    _caloriesController.dispose();
    super.dispose();
  }

  Future<void> _loadWorkoutData() async {
    setState(() => _isLoading = true);

    try {
      final response = await ApiService.getWorkoutForEditing(widget.workoutId);

      if (!mounted) return;

      final workout = response['workout'];
      final exercises = response['exercises'] as List;

      _nameController.text = workout['name'] ?? '';
      _descriptionController.text = workout['description'] ?? '';
      _durationController.text = (workout['estimated_duration'] ?? 30).toString();
      _caloriesController.text = (workout['calories_estimate'] ?? 0).toString();
      _selectedDifficulty = workout['difficulty_level'] ?? 'beginner';
      _selectedType = workout['workout_type'] ?? 'strength';

      _exercises = exercises.map((e) => WorkoutExerciseModel.fromJson(e)).toList();

      setState(() => _isLoading = false);

      print('✅ Treino carregado: ${_exercises.length} exercícios');
    } catch (e) {
      print('❌ Erro ao carregar treino: $e');

      if (!mounted) return;

      setState(() => _isLoading = false);

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('❌ Erro ao carregar treino: $e'),
          backgroundColor: AppColors.error,
        ),
      );

      Navigator.pop(context);
    }
  }

  Future<void> _saveChanges() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isSaving = true);

    try {
      // Montar payload
      final data = {
        'workout': {
          'name': _nameController.text.trim(),
          'description': _descriptionController.text.trim(),
          'difficulty_level': _selectedDifficulty,
          'workout_type': _selectedType,
          'estimated_duration': int.parse(_durationController.text),
          'calories_estimate': int.parse(_caloriesController.text),
        },
        'exercises_to_update': _exercises
            .where((e) => e.id != null)
            .map((e) => {
                  'id': e.id,
                  'sets': e.sets,
                  'reps': e.reps,
                  'weight': e.weight,
                  'rest_time': e.restTime,
                  'order_in_workout': e.order,
                  'notes': e.notes,
                })
            .toList(),
        'exercises_to_add': _exercises
            .where((e) => e.id == null)
            .map((e) => {
                  'exercise_id': e.exerciseId,
                  'sets': e.sets,
                  'reps': e.reps,
                  'weight': e.weight,
                  'rest_time': e.restTime,
                  'order_in_workout': e.order,
                  'notes': e.notes,
                })
            .toList(),
        'exercises_to_remove': _exercisesToRemove,
      };

      print('📝 Salvando alterações...');
      print('   Remover: ${_exercisesToRemove.length}');

      final response = await ApiService.editWorkoutComplete(widget.workoutId, data);

      if (!mounted) return;

      print('✅ Treino salvo: ${response['message']}');

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: const [
              Icon(Icons.check_circle, color: Colors.white, size: 20),
              SizedBox(width: 12),
              Text('✅ Treino atualizado com sucesso!'),
            ],
          ),
          backgroundColor: AppColors.primary,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          margin: const EdgeInsets.all(16),
        ),
      );

      Navigator.pop(context, true);
    } catch (e) {
      print('❌ Erro ao salvar: $e');

      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('❌ Erro ao salvar: $e'),
          backgroundColor: AppColors.error,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _isSaving = false);
      }
    }
  }

  void _removeExercise(int index) {
    final exercise = _exercises[index];

    setState(() {
      if (exercise.id != null) {
        _exercisesToRemove.add(exercise.id!);
      }
      _exercises.removeAt(index);
      _reorderExercises();
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('🗑️ ${exercise.name} removido'),
        duration: const Duration(seconds: 2),
        action: SnackBarAction(
          label: 'Desfazer',
          onPressed: () {
            setState(() {
              if (exercise.id != null) {
                _exercisesToRemove.remove(exercise.id);
              }
              _exercises.insert(index, exercise);
              _reorderExercises();
            });
          },
        ),
      ),
    );
  }

  void _reorderExercises() {
    for (int i = 0; i < _exercises.length; i++) {
      _exercises[i].order = i + 1;
    }
  }

  void _openAddExercisesDialog() async {
    final selectedExercises = await showModalBottomSheet<List<AvailableExerciseModel>>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => _AddExercisesBottomSheet(
        alreadyAddedIds: _exercises.map((e) => e.exerciseId).toSet(),
      ),
    );

    if (selectedExercises != null && selectedExercises.isNotEmpty) {
      setState(() {
        for (final exercise in selectedExercises) {
          _exercises.add(WorkoutExerciseModel(
            id: null,
            exerciseId: exercise.id,
            name: exercise.name,
            description: exercise.description,
            muscleGroup: exercise.muscleGroup,
            sets: 3,
            reps: '10',
            weight: null,
            restTime: 60,
            order: _exercises.length + 1,
            notes: '',
          ));
        }
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('✅ ${selectedExercises.length} exercícios adicionados'),
          backgroundColor: AppColors.primary,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        body: SafeArea(
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: const [
                CircularProgressIndicator(color: AppColors.primary),
                SizedBox(height: 16),
                Text(
                  'Carregando treino...',
                  style: TextStyle(color: AppColors.textSecondary),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),
            Expanded(
              child: Form(
                key: _formKey,
                child: ListView(
                  padding: const EdgeInsets.all(20),
                  children: [
                    _buildBasicInfoSection(),
                    const SizedBox(height: 24),
                    _buildExercisesSection(),
                  ],
                ),
              ),
            ),
            _buildBottomBar(),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppColors.primary,
            AppColors.primary.withOpacity(0.7),
          ],
        ),
      ),
      child: Row(
        children: [
          GestureDetector(
            onTap: () => Navigator.pop(context),
            child: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.arrow_back, color: Colors.white),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Editar Treino',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  widget.workoutName,
                  style: const TextStyle(
                    fontSize: 14,
                    color: Colors.white70,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBasicInfoSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '📋 Informações Básicas',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: AppColors.textPrimary,
          ),
        ),
        const SizedBox(height: 16),
        _buildTextField(
          controller: _nameController,
          label: 'Nome do Treino',
          icon: Icons.fitness_center,
          validator: (value) {
            if (value == null || value.trim().isEmpty) {
              return 'Digite um nome';
            }
            return null;
          },
        ),
        const SizedBox(height: 16),
        _buildTextField(
          controller: _descriptionController,
          label: 'Descrição',
          icon: Icons.description,
          maxLines: 3,
          validator: (value) {
            if (value == null || value.trim().isEmpty) {
              return 'Digite uma descrição';
            }
            return null;
          },
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: _buildTextField(
                controller: _durationController,
                label: 'Duração (min)',
                icon: Icons.schedule,
                keyboardType: TextInputType.number,
                validator: (value) {
                  if (value == null || value.isEmpty) return 'Obrigatório';
                  final duration = int.tryParse(value);
                  if (duration == null || duration <= 0) return 'Inválido';
                  return null;
                },
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: _buildTextField(
                controller: _caloriesController,
                label: 'Calorias',
                icon: Icons.local_fire_department,
                keyboardType: TextInputType.number,
                validator: (value) {
                  if (value == null || value.isEmpty) return 'Obrigatório';
                  final calories = int.tryParse(value);
                  if (calories == null || calories < 0) return 'Inválido';
                  return null;
                },
              ),
            ),
          ],
        ),
      ],
    );
  }

 Widget _buildExercisesSection() {
  return Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Row(
        children: [
          Expanded(
            child: Text(
              '💪 Exercícios (${_exercises.length})',
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Flexible(
            child: ElevatedButton.icon(
              onPressed: _openAddExercisesDialog,
              icon: const Icon(Icons.add, size: 18),
              label: const Text('Adicionar'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
          ),
        ],
      ),
      const SizedBox(height: 16),
      if (_exercises.isEmpty)
        Container(
          padding: const EdgeInsets.all(32),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: AppColors.card,
              style: BorderStyle.solid,
            ),
          ),
          child: Column(
            children: const [
              Icon(
                Icons.fitness_center,
                size: 48,
                color: AppColors.textHint,
              ),
              SizedBox(height: 16),
              Text(
                'Nenhum exercício adicionado',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
              ),
              SizedBox(height: 8),
              Text(
                'Toque em "Adicionar" para incluir exercícios',
                style: TextStyle(
                  fontSize: 14,
                  color: AppColors.textSecondary,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        )
      else
        ReorderableListView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: _exercises.length,
          onReorder: (oldIndex, newIndex) {
            setState(() {
              if (newIndex > oldIndex) newIndex--;
              final item = _exercises.removeAt(oldIndex);
              _exercises.insert(newIndex, item);
              _reorderExercises();
            });
          },
          itemBuilder: (context, index) {
            final exercise = _exercises[index];
            return _ExerciseEditCard(
              key: ValueKey(exercise.exerciseId),
              exercise: exercise,
              index: index,
              onRemove: () => _removeExercise(index),
              onUpdate: (updated) {
                setState(() {
                  _exercises[index] = updated;
                });
              },
            );
          },
        ),
    ],
  );
}

  Widget _buildBottomBar() {
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
    child: SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        onPressed: _isSaving ? null : _saveChanges,
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primary,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          disabledBackgroundColor: AppColors.primary.withOpacity(0.5),
        ),
        child: _isSaving
            ? const SizedBox(
                height: 20,
                width: 20,
                child: CircularProgressIndicator(
                  color: Colors.white,
                  strokeWidth: 2,
                ),
              )
            : const Text(
                'Salvar Alterações',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
      ),
    ),
  );
}
  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    int maxLines = 1,
    TextInputType? keyboardType,
    String? Function(String?)? validator,
  }) {
    return TextFormField(
      controller: controller,
      maxLines: maxLines,
      keyboardType: keyboardType,
      validator: validator,
      style: const TextStyle(color: AppColors.textPrimary),
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: AppColors.primary),
        filled: true,
        fillColor: AppColors.surface,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.card),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.primary, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.error),
        ),
      ),
    );
  }
}

// ============================================================
// 📦 MODEL: WorkoutExerciseModel
// ============================================================
class WorkoutExerciseModel {
  int? id;
  final int exerciseId;
  final String name;
  final String description;
  final String muscleGroup;
  int sets;
  String reps;
  double? weight;
  int restTime;
  int order;
  String notes;

  WorkoutExerciseModel({
    this.id,
    required this.exerciseId,
    required this.name,
    required this.description,
    required this.muscleGroup,
    required this.sets,
    required this.reps,
    this.weight,
    required this.restTime,
    required this.order,
    required this.notes,
  });

  factory WorkoutExerciseModel.fromJson(Map<String, dynamic> json) {
    return WorkoutExerciseModel(
      id: json['id'],
      exerciseId: json['exercise_id'],
      name: json['exercise_name'],
      description: json['exercise_description'] ?? '',
      muscleGroup: json['muscle_group'] ?? 'Geral',
      sets: json['sets'] ?? 3,
      reps: json['reps'] ?? '10',
      weight: json['weight'] != null ? (json['weight'] as num).toDouble() : null,
      restTime: json['rest_time'] ?? 60,
      order: json['order_in_workout'] ?? 1,
      notes: json['notes'] ?? '',
    );
  }
}

// ============================================================
// 📦 MODEL: AvailableExerciseModel
// ============================================================
class AvailableExerciseModel {
  final int id;
  final String name;
  final String description;
  final String muscleGroup;
  final String difficulty;

  AvailableExerciseModel({
    required this.id,
    required this.name,
    required this.description,
    required this.muscleGroup,
    required this.difficulty,
  });

  factory AvailableExerciseModel.fromJson(Map<String, dynamic> json) {
    return AvailableExerciseModel(
      id: json['id'],
      name: json['name'],
      description: json['description'] ?? '',
      muscleGroup: json['muscle_group'] ?? 'Geral',
      difficulty: json['difficulty_level'] ?? 'beginner',
    );
  }
}

// ============================================================
// 🎴 CARD: Exercício Editável
// ============================================================
class _ExerciseEditCard extends StatefulWidget {
  final WorkoutExerciseModel exercise;
  final int index;
  final VoidCallback onRemove;
  final Function(WorkoutExerciseModel) onUpdate;

  const _ExerciseEditCard({
    required super.key,
    required this.exercise,
    required this.index,
    required this.onRemove,
    required this.onUpdate,
  });

  @override
  State<_ExerciseEditCard> createState() => _ExerciseEditCardState();
}

class _ExerciseEditCardState extends State<_ExerciseEditCard> {
  late TextEditingController _setsController;
  late TextEditingController _repsController;
  late TextEditingController _weightController;
  late TextEditingController _restController;

  @override
  void initState() {
    super.initState();
    _setsController = TextEditingController(text: widget.exercise.sets.toString());
    _repsController = TextEditingController(text: widget.exercise.reps);
    _weightController = TextEditingController(
      text: widget.exercise.weight?.toString() ?? '',
    );
    _restController = TextEditingController(
      text: widget.exercise.restTime.toString(),
    );
  }

  @override
  void dispose() {
    _setsController.dispose();
    _repsController.dispose();
    _weightController.dispose();
    _restController.dispose();
    super.dispose();
  }

  void _updateExercise() {
    widget.onUpdate(WorkoutExerciseModel(
      id: widget.exercise.id,
      exerciseId: widget.exercise.exerciseId,
      name: widget.exercise.name,
      description: widget.exercise.description,
      muscleGroup: widget.exercise.muscleGroup,
      sets: int.tryParse(_setsController.text) ?? 3,
      reps: _repsController.text,
      weight: double.tryParse(_weightController.text),
      restTime: int.tryParse(_restController.text) ?? 60,
      order: widget.exercise.order,
      notes: widget.exercise.notes,
    ));
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.card),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppColors.primary.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  '#${widget.index + 1}',
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: AppColors.primary,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.exercise.name,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      widget.exercise.muscleGroup,
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
              IconButton(
                onPressed: widget.onRemove,
                icon: const Icon(Icons.delete_outline, color: AppColors.error),
              ),
              const Icon(Icons.drag_handle, color: AppColors.textHint),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _buildMiniField(
                  controller: _setsController,
                  label: 'Séries',
                  onChanged: (_) => _updateExercise(),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildMiniField(
                  controller: _repsController,
                  label: 'Reps',
                  onChanged: (_) => _updateExercise(),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildMiniField(
                  controller: _weightController,
                  label: 'Peso (kg)',
                  onChanged: (_) => _updateExercise(),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildMiniField(
                  controller: _restController,
                  label: 'Descanso (s)',
                  onChanged: (_) => _updateExercise(),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMiniField({
    required TextEditingController controller,
    required String label,
    required Function(String) onChanged,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 10,
            color: AppColors.textSecondary,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 4),
        TextFormField(
          controller: controller,
          keyboardType: TextInputType.number,
          onChanged: onChanged,
          style: const TextStyle(fontSize: 14, color: AppColors.textPrimary),
          decoration: InputDecoration(
            filled: true,
            fillColor: AppColors.card,
            contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide.none,
            ),
          ),
        ),
      ],
    );
  }
}

// ============================================================
// 🎴 BOTTOM SHEET: Adicionar Exercícios
// ============================================================
class _AddExercisesBottomSheet extends StatefulWidget {
  final Set<int> alreadyAddedIds;

  const _AddExercisesBottomSheet({
    required this.alreadyAddedIds,
  });

  @override
  State<_AddExercisesBottomSheet> createState() => _AddExercisesBottomSheetState();
}

class _AddExercisesBottomSheetState extends State<_AddExercisesBottomSheet> {
  List<AvailableExerciseModel> _allExercises = [];
  Set<int> _selectedIds = {};
  bool _isLoading = true;
  String _searchQuery = '';
  String _selectedMuscleGroup = 'all';
  String _selectedDifficulty = 'all';

  final List<String> _muscleGroups = [
    'all',
    'chest',
    'back',
    'legs',
    'shoulders',
    'arms',
    'core',
    'cardio',
  ];

  final Map<String, String> _muscleGroupLabels = {
    'all': 'Todos',
    'chest': 'Peito',
    'back': 'Costas',
    'legs': 'Pernas',
    'shoulders': 'Ombros',
    'arms': 'Braços',
    'core': 'Core',
    'cardio': 'Cardio',
  };

  @override
  void initState() {
    super.initState();
    _loadExercises();
  }

  Future<void> _loadExercises() async {
    setState(() => _isLoading = true);

    try {
      final response = await ApiService.getAvailableExercisesForEditing(
        muscleGroup: _selectedMuscleGroup,
        difficultyLevel: _selectedDifficulty,
        search: _searchQuery.isNotEmpty ? _searchQuery : null,
      );

      final exercises = response['exercises'] as List;

      setState(() {
        _allExercises = exercises
            .map((e) => AvailableExerciseModel.fromJson(e))
            .where((e) => !widget.alreadyAddedIds.contains(e.id))
            .toList();
        _isLoading = false;
      });

      print('✅ ${_allExercises.length} exercícios disponíveis');
    } catch (e) {
      print('❌ Erro ao carregar exercícios: $e');
      setState(() => _isLoading = false);
    }
  }

  void _applyFilters() {
    _loadExercises();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      decoration: const BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        children: [
          _buildHeader(),
          _buildSearchBar(),
          _buildFilters(),
          Expanded(child: _buildExercisesList()),
          _buildBottomBar(),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        children: [
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.card,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Adicionar Exercícios',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
              if (_selectedIds.isNotEmpty)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: AppColors.primary,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    '${_selectedIds.length} selecionados',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
                    ),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSearchBar() {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: TextField(
        onChanged: (value) {
          setState(() => _searchQuery = value);
          _applyFilters();
        },
        style: const TextStyle(color: AppColors.textPrimary),
        decoration: InputDecoration(
          hintText: 'Buscar exercícios...',
          prefixIcon: const Icon(Icons.search, color: AppColors.textHint),
          filled: true,
          fillColor: AppColors.surface,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide.none,
          ),
        ),
      ),
    );
  }

  Widget _buildFilters() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        children: [
          Expanded(
            child: _buildFilterDropdown(
              value: _selectedMuscleGroup,
              items: _muscleGroups,
              labels: _muscleGroupLabels,
              onChanged: (value) {
                setState(() => _selectedMuscleGroup = value!);
                _applyFilters();
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterDropdown({
    required String value,
    required List<String> items,
    required Map<String, String> labels,
    required ValueChanged<String?> onChanged,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.card),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: value,
          isExpanded: true,
          icon: const Icon(Icons.keyboard_arrow_down, color: AppColors.primary),
          dropdownColor: AppColors.surface,
          items: items.map((item) {
            return DropdownMenuItem<String>(
              value: item,
              child: Text(
                labels[item] ?? item,
                style: const TextStyle(fontSize: 14, color: AppColors.textPrimary),
              ),
            );
          }).toList(),
          onChanged: onChanged,
        ),
      ),
    );
  }

  Widget _buildExercisesList() {
    if (_isLoading) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.primary),
      );
    }

    if (_allExercises.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: const [
            Icon(Icons.search_off, size: 64, color: AppColors.textHint),
            SizedBox(height: 16),
            Text(
              'Nenhum exercício encontrado',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: AppColors.textPrimary,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Tente ajustar os filtros',
              style: TextStyle(
                fontSize: 14,
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      itemCount: _allExercises.length,
      itemBuilder: (context, index) {
        final exercise = _allExercises[index];
        final isSelected = _selectedIds.contains(exercise.id);

        return GestureDetector(
          onTap: () {
            setState(() {
              if (isSelected) {
                _selectedIds.remove(exercise.id);
              } else {
                _selectedIds.add(exercise.id);
              }
            });
          },
          child: Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: isSelected ? AppColors.primary : AppColors.card,
                width: isSelected ? 2 : 1,
              ),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: isSelected
                        ? AppColors.primary
                        : AppColors.primary.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    isSelected ? Icons.check : Icons.fitness_center,
                    color: isSelected ? Colors.white : AppColors.primary,
                    size: 20,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        exercise.name,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        exercise.description,
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.textSecondary,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppColors.primary.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          _muscleGroupLabels[exercise.muscleGroup] ?? exercise.muscleGroup,
                          style: const TextStyle(
                            fontSize: 10,
                            color: AppColors.primary,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildBottomBar() {
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
      child: Row(
        children: [
          Expanded(
            child: OutlinedButton(
              onPressed: () => Navigator.pop(context),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                side: const BorderSide(color: AppColors.card),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Text('Cancelar'),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            flex: 2,
            child: ElevatedButton(
              onPressed: _selectedIds.isEmpty
                  ? null
                  : () {
                      final selected = _allExercises
                          .where((e) => _selectedIds.contains(e.id))
                          .toList();
                      Navigator.pop(context, selected);
                    },
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                disabledBackgroundColor: AppColors.primary.withOpacity(0.3),
              ),
              child: Text(
                _selectedIds.isEmpty
                    ? 'Selecione exercícios'
                    : 'Adicionar (${_selectedIds.length})',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}