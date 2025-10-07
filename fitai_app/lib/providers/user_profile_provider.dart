import 'package:flutter/foundation.dart';
import '../service/user_service.dart';
import '../models/user_model.dart';

class UserProfileProvider extends ChangeNotifier {
  UserRegistrationData? _userData;
  bool _isLoading = false;

  // Getters
  bool get isLoading => _isLoading;
  bool get hasUserData => _userData != null;

  String get nome => _userData?.nome ?? 'Usuário';
  String get email => _userData?.email ?? 'email@exemplo.com';
  int get idade => _userData?.idade ?? 0;
  String get genero => _userData?.sexo ?? 'Não informado';
  
  double get pesoAtual => _userData?.pesoAtual ?? 0.0;
  double get pesoDesejado => _userData?.pesoDesejado ?? 0.0;
  double get altura => _userData?.altura ?? 0.0;
  
  double get imc => _userData?.calcularIMC() ?? 0.0;
  String get imcCategoria => _userData?.getIMCStatus() ?? 'Não calculado';
  
  String get objetivo => _userData?.metas.isNotEmpty == true 
      ? _userData!.metas.first 
      : 'Não definido';
  
  String get nivelAtividade => _userData?.nivelAtividade ?? 'Não informado';
  
  String get preferenciaTreino => _userData?.tiposTreino.isNotEmpty == true
      ? _userData!.tiposTreino.join(', ')
      : 'Não definido';

  /// Carregar perfil do usuário (PRIORIZA DJANGO)
  Future<void> loadProfile() async {
    _isLoading = true;
    notifyListeners();

    try {
      debugPrint('📥 Carregando perfil do usuário...');
      
      // PASSO 1: Tentar carregar do Django primeiro
      UserRegistrationData? djangoProfile = await UserService.getProfileFromDjango();
      
      if (djangoProfile != null) {
        _userData = djangoProfile;
        debugPrint('✅ Perfil carregado do Django');
      } else {
        // PASSO 2: Fallback para Firebase/Local
        debugPrint('⚠️ Django falhou, carregando do Firebase...');
        _userData = await UserService.getCurrentUser();
        
        if (_userData != null) {
          debugPrint('✅ Perfil carregado do Firebase');
          
          // Tentar sincronizar com Django em background
          _syncWithDjangoInBackground();
        } else {
          debugPrint('❌ Nenhum perfil encontrado');
        }
      }

    } catch (e) {
      debugPrint('❌ Erro ao carregar perfil: $e');
      
      // Último recurso: tentar Firebase
      try {
        _userData = await UserService.getCurrentUser();
      } catch (e2) {
        debugPrint('❌ Erro ao carregar do Firebase também: $e2');
      }
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Sincronizar com Django em background (não bloqueia UI)
  Future<void> _syncWithDjangoInBackground() async {
    if (_userData == null) return;
    
    try {
      debugPrint('🔄 Sincronizando perfil com Django em background...');
      await UserService.syncProfileWithDjango(_userData!);
      debugPrint('✅ Sincronização em background concluída');
    } catch (e) {
      debugPrint('⚠️ Erro na sincronização em background: $e');
      // Não falhar - é apenas sincronização
    }
  }

  /// Atualizar métricas corporais
  Future<bool> updateMetrics({
    double? pesoAtual,
    double? pesoDesejado,
    double? altura,
  }) async {
    if (_userData == null) return false;

    try {
      _isLoading = true;
      notifyListeners();

      // Atualizar dados locais
      if (pesoAtual != null) _userData!.pesoAtual = pesoAtual;
      if (pesoDesejado != null) _userData!.pesoDesejado = pesoDesejado;
      if (altura != null) _userData!.altura = altura;

      // Salvar no Firebase
      await UserService.updateUser(_userData!);
      
      // Sincronizar com Django
      await UserService.updateProfileInDjango(_userData!);

      debugPrint('✅ Métricas atualizadas');
      return true;

    } catch (e) {
      debugPrint('❌ Erro ao atualizar métricas: $e');
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Atualizar informações pessoais
  Future<bool> updatePersonalInfo({
    String? nome,
    String? email,
    int? idade,
    String? sexo,
  }) async {
    if (_userData == null) return false;

    try {
      _isLoading = true;
      notifyListeners();

      if (nome != null) _userData!.nome = nome;
      if (email != null) _userData!.email = email;
      if (idade != null) _userData!.idade = idade;
      if (sexo != null) _userData!.sexo = sexo;

      await UserService.updateUser(_userData!);
      await UserService.updateProfileInDjango(_userData!);

      debugPrint('✅ Informações pessoais atualizadas');
      return true;

    } catch (e) {
      debugPrint('❌ Erro ao atualizar informações: $e');
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Atualizar objetivos
  Future<bool> updateGoals({
    String? objetivo,
    String? nivelAtividade,
    String? preferenciaTreino,
  }) async {
    if (_userData == null) return false;

    try {
      _isLoading = true;
      notifyListeners();

      if (objetivo != null) {
        _userData!.metas = [objetivo];
      }
      
      if (nivelAtividade != null) {
        _userData!.nivelAtividade = nivelAtividade;
      }
      
      if (preferenciaTreino != null) {
        _userData!.tiposTreino = preferenciaTreino.split(',').map((e) => e.trim()).toList();
      }

      await UserService.updateUser(_userData!);
      await UserService.updateProfileInDjango(_userData!);

      debugPrint('✅ Objetivos atualizados');
      return true;

    } catch (e) {
      debugPrint('❌ Erro ao atualizar objetivos: $e');
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Atualizar perfil (refresh)
  Future<void> refreshProfile() async {
    await loadProfile();
  }

  /// Limpar dados (logout)
  void clearProfile() {
    _userData = null;
    notifyListeners();
  }
}