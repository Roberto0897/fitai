/// Provider completo e corrigido para Django REST Framework
/// Localização: lib/providers/user_profile_provider.dart

import 'package:flutter/material.dart';
import '../models/user_model.dart';
import '../service/api_service.dart';

class UserProfileProvider extends ChangeNotifier {
  UserRegistrationData? _userData;
  bool _isLoading = false;
  String? _errorMessage;
  bool _profileExists = false;
  bool _onboardingCompleted = false;

  // Getters
  UserRegistrationData? get userData => _userData;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  bool get hasUserData => _userData != null;
  bool get profileExists => _profileExists;
  bool get onboardingCompleted => _onboardingCompleted;

  // Getters de conveniência
  String get nome => _userData?.nome ?? '';
  String get email => _userData?.email ?? '';
  int get idade => _userData?.idade ?? 0;
  String get genero => _userData?.sexo ?? '';
  double get pesoAtual => _userData?.pesoAtual ?? 0.0;
  double get pesoDesejado => _userData?.pesoDesejado ?? 0.0;
  double get altura => _userData?.altura ?? 0.0;
  String get objetivo => _userData?.metas.isNotEmpty == true ? _userData!.metas.first : '';
  String get nivelAtividade => _userData?.nivelAtividade ?? '';
  String get preferenciaTreino => _userData?.tiposTreino.join(', ') ?? '';
  double get imc => _userData?.calcularIMC() ?? 0.0;
  String get imcCategoria => _userData?.getIMCStatus() ?? '';

  /// Carregar perfil do backend
  Future<bool> loadProfile() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      print('🔍 Carregando perfil do backend...');
      
      final response = await ApiService.getDashboard();
      
      print('✅ Dashboard recebido: ${response.keys}');
      
      // Verificar se tem campos críticos null
      final user = response['user'] ?? {};
      final hasNullFields = user['goal'] == null || 
                           user['activity_level'] == null ||
                           user['current_weight'] == null;
      
      // Converter resposta do DRF
      _userData = _convertDRFToUserData(response);
      _profileExists = true;
      _onboardingCompleted = !hasNullFields; // Completo se não tem campos null
      
      _isLoading = false;
      notifyListeners();
      
      print('📊 Onboarding completo: $_onboardingCompleted');
      return true;
      
    } catch (e) {
      print('⚠️ Erro ao carregar perfil: $e');
      
      if (e.toString().contains('404')) {
        print('📝 Criando perfil local temporário');
        await _createDefaultProfile();
        _profileExists = false;
        _onboardingCompleted = false;
        _errorMessage = 'Complete seu perfil para começar';
      } else {
        _errorMessage = 'Erro ao carregar: $e';
      }
      
      _isLoading = false;
      notifyListeners();
      
      return _userData != null;
    }
  }

  /// Criar perfil local padrão
  Future<void> _createDefaultProfile() async {
    _userData = UserRegistrationData(
      nome: 'Usuário',
      email: 'usuario@email.com',
      idade: 25,
      sexo: 'Não informado',
      pesoAtual: 70.0,
      pesoDesejado: 65.0,
      altura: 170.0,
      metas: ['Manter forma'],
      nivelAtividade: 'Moderado',
      tiposTreino: ['Geral'],
      areasDesejadas: [],
      equipamentos: 'Não especificado',
      tempoDisponivel: '30-45 min',
      malaFlexibilidade: false,
    );
  }

  /// Converter resposta do DRF para UserRegistrationData
  UserRegistrationData _convertDRFToUserData(Map<String, dynamic> json) {
    final user = json['user'] ?? {};
    
    // Mapear goal
    String mapGoal(String? goal) {
      if (goal == null || goal.isEmpty) return 'Manter forma';
      switch (goal) {
        case 'lose_weight': return 'Perder peso';
        case 'gain_muscle': return 'Ganhar massa';
        case 'maintain': return 'Manter forma';
        case 'endurance': return 'Melhorar Resistência';
        default: return 'Manter forma';
      }
    }
    
    // Mapear activity_level
    String mapActivityLevel(String? level) {
      if (level == null || level.isEmpty) return 'Moderado';
      switch (level) {
        case 'sedentary': return 'Sedentário';
        case 'light': return 'Leve';
        case 'moderate': return 'Moderado';
        case 'active': return 'Ativo';
        case 'very_active': return 'Muito Ativo';
        default: return 'Moderado';
      }
    }
    
    // Extrair nome: primeiro tenta first_name, depois username
    String getNome() {
      final firstName = user['first_name'];
      final username = user['username'];
      
      // Se first_name existe e não é vazio
      if (firstName != null && firstName.toString().isNotEmpty) {
        return firstName.toString();
      }
      
      // Se username parece ser UID (muito longo), usar "Usuário"
      if (username != null && username.toString().length > 25) {
        return 'Usuário';
      }
      
      return username?.toString() ?? 'Usuário';
    }
    
    // Parse números com segurança
    double parseDouble(dynamic value, double defaultValue) {
      if (value == null) return defaultValue;
      if (value is num) return value.toDouble();
      if (value is String) {
        final parsed = double.tryParse(value);
        return parsed ?? defaultValue;
      }
      return defaultValue;
    }
    
    return UserRegistrationData(
      nome: getNome(),
      email: user['email']?.toString() ?? '',
      idade: 25, // Modelo não tem date_of_birth
      sexo: 'Não informado', // Modelo não tem gender
      pesoAtual: parseDouble(user['current_weight'], 70.0),
      pesoDesejado: parseDouble(user['target_weight'], 65.0),
      altura: 170.0, // Modelo não tem height
      metas: [mapGoal(user['goal'])],
      nivelAtividade: mapActivityLevel(user['activity_level']),
      tiposTreino: ['Geral'],
      areasDesejadas: _parseAreas(user['focus_areas']),
      equipamentos: 'Não especificado',
      tempoDisponivel: '30-45 min',
      malaFlexibilidade: false,
    );
  }

  /// Parse áreas de foco
  List<String> _parseAreas(dynamic value) {
    if (value == null || value == '') return [];
    if (value is String) {
      return value.split(',').map((e) => e.trim()).where((e) => e.isNotEmpty).toList();
    }
    return [];
  }

  /// Criar perfil completo no backend
  Future<bool> createProfileInBackend(UserRegistrationData data) async {
    _isLoading = true;
    notifyListeners();

    try {
      print('📤 Criando perfil no backend...');
      
      final profileData = {
        'nome': data.nome,
        'email': data.email,
        'peso_atual': data.pesoAtual,
        'peso_desejado': data.pesoDesejado,
        'objetivo': data.metas.isNotEmpty ? data.metas.first : 'Manter forma',
        'nivel_atividade': data.nivelAtividade,
        'from_onboarding': true,
      };

      final response = await ApiService.post('/users/register/', profileData);
      
      if (response['success'] == true) {
        _userData = data;
        _profileExists = true;
        _onboardingCompleted = true;
        _errorMessage = null;
        
        print('✅ Perfil criado com sucesso');
        
        _isLoading = false;
        notifyListeners();
        
        return true;
      }
      
      throw Exception('Resposta inválida do servidor');
      
    } catch (e) {
      print('❌ Erro ao criar perfil: $e');
      _errorMessage = 'Erro ao criar perfil: $e';
      _isLoading = false;
      notifyListeners();
      
      return false;
    }
  }

  /// Atualizar métricas
  Future<bool> updateMetrics({
    double? pesoAtual,
    double? pesoDesejado,
    double? altura,
  }) async {
    if (_userData == null) return false;

    _isLoading = true;
    notifyListeners();

    try {
      print('📊 Atualizando métricas...');
      
      if (pesoAtual != null || pesoDesejado != null) {
        final weightData = <String, dynamic>{};
        if (pesoAtual != null) weightData['peso_atual'] = pesoAtual;
        if (pesoDesejado != null) weightData['peso_desejado'] = pesoDesejado;
        
        await ApiService.post('/users/set_weight_info/', weightData);
      }
      
      _userData = _userData!.copyWith(
        pesoAtual: pesoAtual ?? _userData!.pesoAtual,
        pesoDesejado: pesoDesejado ?? _userData!.pesoDesejado,
        altura: altura ?? _userData!.altura,
      );
      
      _isLoading = false;
      notifyListeners();
      
      print('✅ Métricas atualizadas');
      return true;
      
    } catch (e) {
      print('❌ Erro: $e');
      _errorMessage = 'Erro ao atualizar: $e';
      _isLoading = false;
      notifyListeners();
      
      return false;
    }
  }

  /// Atualizar informações pessoais (CORRIGIDO - agora salva no backend)
  Future<bool> updatePersonalInfo({
    String? nome,
    String? email,
    int? idade,
    String? sexo,
  }) async {
    if (_userData == null) return false;

    _isLoading = true;
    notifyListeners();

    try {
      print('📝 Atualizando informações pessoais...');
      
      // Enviar para o backend
      final updateData = <String, dynamic>{};
      if (nome != null) updateData['nome'] = nome;
      if (email != null) updateData['email'] = email;
      if (idade != null) updateData['idade'] = idade;
      if (sexo != null) updateData['genero'] = sexo;
      
      await ApiService.post('/users/register/', updateData);
      
      // Atualizar localmente após sucesso
      _userData = _userData!.copyWith(
        nome: nome ?? _userData!.nome,
        email: email ?? _userData!.email,
        idade: idade ?? _userData!.idade,
        sexo: sexo ?? _userData!.sexo,
      );
      
      _isLoading = false;
      notifyListeners();
      
      print('✅ Informações atualizadas no backend');
      return true;
      
    } catch (e) {
      print('❌ Erro ao atualizar: $e');
      _errorMessage = 'Erro ao atualizar: $e';
      _isLoading = false;
      notifyListeners();
      
      return false;
    }
  }

  /// Atualizar objetivos
  Future<bool> updateGoals({
    String? objetivo,
    String? nivelAtividade,
    String? preferenciaTreino,
  }) async {
    if (_userData == null) return false;

    _isLoading = true;
    notifyListeners();

    try {
      print('🎯 Atualizando objetivos...');
      
      if (objetivo != null) {
        await ApiService.post('/users/set_goal/', {'objetivo': objetivo});
      }
      
      if (nivelAtividade != null) {
        await ApiService.post('/users/set_activity_level/', {'nivel_atividade': nivelAtividade});
      }
      
      _userData = _userData!.copyWith(
        metas: objetivo != null ? [objetivo] : _userData!.metas,
        nivelAtividade: nivelAtividade ?? _userData!.nivelAtividade,
        tiposTreino: preferenciaTreino != null ? [preferenciaTreino] : _userData!.tiposTreino,
      );
      
      _isLoading = false;
      notifyListeners();
      
      print('✅ Objetivos atualizados');
      return true;
      
    } catch (e) {
      print('❌ Erro: $e');
      _errorMessage = 'Erro ao atualizar: $e';
      _isLoading = false;
      notifyListeners();
      
      return false;
    }
  }

  /// Limpar dados
  void clearProfile() {
    _userData = null;
    _errorMessage = null;
    _isLoading = false;
    _profileExists = false;
    _onboardingCompleted = false;
    notifyListeners();
  }

  /// Refresh
  Future<void> refreshProfile() async {
    await loadProfile();
  }
}