import 'dart:convert';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:crypto/crypto.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:flutter/foundation.dart';
import '../models/user_model.dart';
import 'package:http/http.dart' as http;


class UserService {
  // Instâncias do Firebase
  static final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  static final FirebaseAuth _auth = FirebaseAuth.instance;
  
  // Collections do Firestore
  static const String _usersCollection = 'users';
  
  // Keys para armazenamento local
  static const String _usersKey = 'registered_users';
  static const String _currentUserKey = 'current_user';

   // 🔥 CONFIGURAÇÃO DA API DJANGO
  static const String _djangoBaseUrl = 'http://localhost:8000/api/v1';

  // ==================== GOOGLE SIGN-IN CONFIGURATION ====================
  
  // Configuração condicional do GoogleSignIn por plataforma
  static GoogleSignIn get _googleSignIn {
    if (kIsWeb) {
      // Para Web: usar Client ID específico
      return GoogleSignIn(
        clientId: '729376686349-9sielofvucvphtnnt7pipgjc1mr68eih.apps.googleusercontent.com',
        scopes: ['email', 'profile'],
      );
    } else {
      // Para Mobile: usar configuração automática do google-services.json
      return GoogleSignIn(
        scopes: ['email', 'profile'],
      );
    }
  }

  // ==================== GOOGLE SIGN-IN METHODS ====================
  
  /// Login com Google - Método principal
  static Future<UserRegistrationData?> signInWithGoogle() async {
    try {
      if (kIsWeb) {
        return await _signInGoogleWeb();
      } else {
        return await _signInGoogleMobile();
      }
    } catch (e) {
      print('Erro no Google Sign-In: $e');
      rethrow;
    }
  }

  /// Implementação específica para Web
  static Future<UserRegistrationData?> _signInGoogleWeb() async {
    try {
      // Tentar login silencioso primeiro (recomendado para web)
      GoogleSignInAccount? googleUser = await _googleSignIn.signInSilently();
      
      // Se não conseguir silenciosamente, usar método manual
      if (googleUser == null) {
        // Limpar cache antes de tentar novamente
        await _googleSignIn.signOut();
        googleUser = await _googleSignIn.signIn();
      }
      
      if (googleUser == null) {
        print('Login cancelado pelo usuário');
        return null;
      }

      final GoogleSignInAuthentication googleAuth = 
          await googleUser.authentication;

      if (googleAuth.accessToken == null) {
        throw Exception('Falha ao obter access token do Google');
      }

      final credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      final userCredential = await _auth.signInWithCredential(credential);
      
      // Criar/atualizar dados do usuário
      final userData = await _handleGoogleUserData(userCredential.user!, googleUser);
      
      return userData;
    } catch (e) {
      print('Erro Web Google Sign-In: $e');
      rethrow;
    }
  }

  /// Implementação específica para Mobile
  static Future<UserRegistrationData?> _signInGoogleMobile() async {
    try {
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      
      if (googleUser == null) {
        print('Login cancelado pelo usuário');
        return null;
      }

      final GoogleSignInAuthentication googleAuth = 
          await googleUser.authentication;

      final credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      final userCredential = await _auth.signInWithCredential(credential);
      
      // Criar/atualizar dados do usuário
      final userData = await _handleGoogleUserData(userCredential.user!, googleUser);
      
      return userData;
    } catch (e) {
      print('Erro Mobile Google Sign-In: $e');
      rethrow;
    }
  }

  /// Processar dados do usuário Google
  static Future<UserRegistrationData> _handleGoogleUserData(
    User firebaseUser, 
    GoogleSignInAccount googleUser
  ) async {
    try {
      // Verificar se usuário já existe no sistema
      UserRegistrationData? existingUser = await _getUserByEmail(firebaseUser.email!);
      
      if (existingUser != null) {
        // Usuário existe - atualizar dados se necessário
        existingUser = existingUser.copyWith(
          nome: firebaseUser.displayName ?? existingUser.nome,
        );
        
        await _saveCurrentUserLocally(existingUser);
        print('Usuario Google existente atualizado: ${firebaseUser.email}');
        return existingUser;
      } else {
        // Novo usuário Google - criar perfil básico
        final newUser = UserRegistrationData(
          nome: firebaseUser.displayName ?? 'Usuario Google',
          email: firebaseUser.email!,
          senha: '', // Não usar senha para usuários Google
          createdAt: DateTime.now(),
        );

        // Salvar no Firebase e localmente
        await _saveGoogleUserToFirebase(firebaseUser.uid, newUser);
        await _saveCurrentUserLocally(newUser);
        
        print('Novo usuario Google criado: ${firebaseUser.email}');
        return newUser;
      }
    } catch (e) {
      print('Erro ao processar dados do usuario Google: $e');
      rethrow;
    }
  }

  /// Salvar usuário Google no Firebase
  static Future<void> _saveGoogleUserToFirebase(String uid, UserRegistrationData userData) async {
    try {
      await _firestore.collection(_usersCollection).doc(uid).set({
        'uid': uid,
        'nome': userData.nome,
        'email': userData.email,
        'provider': 'google',
        'idade': userData.idade,
        'sexo': userData.sexo,
        'metas': userData.metas,
        'nivelAtividade': userData.nivelAtividade,
        'areasDesejadas': userData.areasDesejadas,
        'pesoAtual': userData.pesoAtual,
        'pesoDesejado': userData.pesoDesejado,
        'altura': userData.altura,
        'imc': userData.calcularIMC(),
        'imcStatus': userData.getIMCStatus(),
        'tiposTreino': userData.tiposTreino,
        'equipamentos': userData.equipamentos,
        'tempoDisponivel': userData.tempoDisponivel,
        'malaFlexibilidade': userData.malaFlexibilidade,
        'createdAt': FieldValue.serverTimestamp(),
        'updatedAt': FieldValue.serverTimestamp(),
        'syncStatus': 'synced',
      }, SetOptions(merge: true));
    } catch (e) {
      print('Erro ao salvar usuario Google no Firebase: $e');
      // Não relançar erro - permitir funcionamento offline
    }
  }

  /// Buscar usuário por email
  static Future<UserRegistrationData?> _getUserByEmail(String email) async {
    // Primeiro tentar localmente
    try {
      final prefs = await SharedPreferences.getInstance();
      final usersJson = prefs.getString(_usersKey) ?? '[]';
      final List<dynamic> usersList = jsonDecode(usersJson);

      for (var userJson in usersList) {
        if (userJson['email'] == email.toLowerCase()) {
          return UserRegistrationData.fromJson(userJson);
        }
      }
    } catch (e) {
      print('Erro ao buscar usuario localmente: $e');
    }

    // Tentar no Firebase se online
    if (await _hasInternetConnection()) {
      try {
        final querySnapshot = await _firestore
            .collection(_usersCollection)
            .where('email', isEqualTo: email.toLowerCase())
            .limit(1)
            .get();
        
        if (querySnapshot.docs.isNotEmpty) {
          return _firestoreToUserData(querySnapshot.docs.first.data());
        }
      } catch (e) {
        print('Erro ao buscar usuario no Firebase: $e');
      }
    }

    return null;
  }

  /// Verificar se pode fazer login silencioso com Google
  static Future<bool> canSignInGoogleSilently() async {
    try {
      if (kIsWeb) {
        final account = await _googleSignIn.signInSilently();
        return account != null;
      }
      return await _googleSignIn.canAccessScopes(['email']);
    } catch (e) {
      return false;
    }
  }

  // ==================== MÉTODOS EXISTENTES (mantidos) ====================

  // Criptografar senha usando SHA-256
  static String _hashPassword(String password) {
    var bytes = utf8.encode(password);
    var digest = sha256.convert(bytes);
    return digest.toString();
  }

  // Verificar conectividade (simulado - você pode usar connectivity_plus)
  static Future<bool> _hasInternetConnection() async {
    try {
      // Teste rápido de conectividade com Firebase
      await _firestore.collection('test').limit(1).get();
      return true;
    } catch (e) {
      return false;
    }
  }

  // Verificar se email já existe (Local + Firebase)
  static Future<bool> emailExists(String email) async {
    email = email.toLowerCase().trim();
    
    // Primeiro verificar localmente
    if (await _emailExistsLocally(email)) {
      return true;
    }
    
    // Se não encontrou localmente, verificar no Firebase (se online)
    if (await _hasInternetConnection()) {
      return await _emailExistsInFirebase(email);
    }
    
    return false;
  }

  // Verificar email localmente
  static Future<bool> _emailExistsLocally(String email) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final usersJson = prefs.getString(_usersKey) ?? '[]';
      final List<dynamic> usersList = jsonDecode(usersJson);

      return usersList.any((user) => user['email'] == email);
    } catch (e) {
      print('Erro ao verificar email localmente: $e');
      return false;
    }
  }

  // Verificar email no Firebase
  static Future<bool> _emailExistsInFirebase(String email) async {
    try {
      final querySnapshot = await _firestore
          .collection(_usersCollection)
          .where('email', isEqualTo: email)
          .limit(1)
          .get();
      
      return querySnapshot.docs.isNotEmpty;
    } catch (e) {
      print('Erro ao verificar email no Firebase: $e');
      return false;
    }
  }

  // Registrar usuário (Local + Firebase)
  static Future<bool> registerUser(UserRegistrationData userData) async {
    try {
      // Normalizar dados
      userData.email = userData.email.toLowerCase().trim();
      userData.nome = userData.nome.trim();

      // Verificar se email já existe
      if (await emailExists(userData.email)) {
        throw Exception('Este email já está cadastrado');
      }

      String? firebaseUid;
      bool savedToFirebase = false;

    if (await _hasInternetConnection()) {
        try {
          firebaseUid = await _registerInFirebase(userData);
          savedToFirebase = true;
          print('Usuario registrado no Firebase: ${userData.email}');
        } catch (e) {
          print('Falha ao salvar no Firebase, salvando apenas localmente: $e');
        }
      }


      // Sempre salvar localmente (com hash da senha)
      await _registerLocally(userData, firebaseUid);
      print('Usuario registrado localmente: ${userData.email}');

      // Se não conseguiu salvar no Firebase, marcar para sincronização posterior
      if (!savedToFirebase) {
        await _markForSyncLater(userData);
      }

      return true;

    } catch (e) {
      print('Erro ao registrar usuario: $e');
      rethrow;
    }
  }

  // Registrar no Firebase
  static Future<String> _registerInFirebase(UserRegistrationData userData) async {
    // 1. Criar usuário no Firebase Auth
    UserCredential userCredential = await _auth.createUserWithEmailAndPassword(
      email: userData.email,
      password: userData.senha,
    );

    final String uid = userCredential.user!.uid;

    // 2. Atualizar nome no Firebase Auth
    await userCredential.user!.updateDisplayName(userData.nome);

    // 3. Salvar dados no Firestore
    await _firestore.collection(_usersCollection).doc(uid).set({
      'uid': uid,
      'nome': userData.nome,
      'email': userData.email,
      'provider': 'email',
      'idade': userData.idade,
      'sexo': userData.sexo,
      'metas': userData.metas,
      'nivelAtividade': userData.nivelAtividade,
      'areasDesejadas': userData.areasDesejadas,
      'pesoAtual': userData.pesoAtual,
      'pesoDesejado': userData.pesoDesejado,
      'altura': userData.altura,
      'imc': userData.calcularIMC(),
      'imcStatus': userData.getIMCStatus(),
      'tiposTreino': userData.tiposTreino,
      'equipamentos': userData.equipamentos,
      'tempoDisponivel': userData.tempoDisponivel,
      'malaFlexibilidade': userData.malaFlexibilidade,
      'createdAt': FieldValue.serverTimestamp(),
      'updatedAt': FieldValue.serverTimestamp(),
      'syncStatus': 'synced',
    });

    return uid;
  }

  // Registrar localmente
  static Future<void> _registerLocally(UserRegistrationData userData, String? firebaseUid) async {
    final prefs = await SharedPreferences.getInstance();

    // Hash da senha para armazenamento local
    String hashedPassword = _hashPassword(userData.senha);

    // Obter lista de usuários existentes
    final usersJson = prefs.getString(_usersKey) ?? '[]';
    final List<dynamic> usersList = jsonDecode(usersJson);

    // Criar dados do usuário para armazenamento local
    final userDataLocal = userData.toJson();
    userDataLocal['senha'] = hashedPassword;
    userDataLocal['firebaseUid'] = firebaseUid;
    userDataLocal['syncStatus'] = firebaseUid != null ? 'synced' : 'pending';

    // Adicionar à lista
    usersList.add(userDataLocal);

    // Salvar lista atualizada
    await prefs.setString(_usersKey, jsonEncode(usersList));

    // Salvar como usuário atual
    await prefs.setString(_currentUserKey, jsonEncode(userDataLocal));
  }

  // Marcar usuário para sincronização posterior
  static Future<void> _markForSyncLater(UserRegistrationData userData) async {
    final prefs = await SharedPreferences.getInstance();
    final pendingSync = prefs.getStringList('pending_sync') ?? [];
    
    pendingSync.add(userData.email);
    await prefs.setStringList('pending_sync', pendingSync);
    
    print('Usuario marcado para sincronizacao: ${userData.email}');
  }

  // Login (tenta Firebase primeiro, depois local)
 static Future<UserRegistrationData?> loginUser(String email, String password) async {
  email = email.toLowerCase().trim();

  try {
    print('🔥 Iniciando login - tentando Firebase...');
    
    // Tentar login no Firebase Auth
    UserCredential userCredential = await _auth.signInWithEmailAndPassword(
      email: email,
      password: password,
    );

    final String uid = userCredential.user!.uid;
    print('✅ Firebase Auth: Login bem-sucedido - UID: $uid');

    // Buscar dados no Firestore
    DocumentSnapshot userDoc = await _firestore
        .collection(_usersCollection)
        .doc(uid)
        .get();

    UserRegistrationData userData;

    if (!userDoc.exists) {
      print('⚠️ Usuário existe no Auth mas não no Firestore - criando documento...');
      
      // Criar documento básico no Firestore
      userData = UserRegistrationData(
        nome: userCredential.user?.displayName ?? 'Usuário',
        email: email,
        senha: '', // Não armazenar senha
        createdAt: DateTime.now(),
      );
      
      // Salvar no Firestore
      await _firestore.collection(_usersCollection).doc(uid).set({
        'uid': uid,
        'nome': userData.nome,
        'email': userData.email,
        'provider': 'email',
        'createdAt': FieldValue.serverTimestamp(),
        'updatedAt': FieldValue.serverTimestamp(),
        'syncStatus': 'synced',
      });
      
      print('✅ Documento criado no Firestore para: $email');
    } else {
      // Usuário já existe no Firestore
      userData = _firestoreToUserData(userDoc.data() as Map<String, dynamic>);
    }

    await _saveCurrentUserLocally(userData);
    
    print('✅ Login completo: Firebase + Cache local');
    return userData;

  } on FirebaseAuthException catch (e) {
    print('❌ FirebaseAuthException: ${e.code} - ${e.message}');
    
    switch (e.code) {
      case 'user-not-found':
        throw Exception('Email não cadastrado. Faça registro primeiro.');
      case 'wrong-password':
        throw Exception('Senha incorreta.');
      case 'invalid-email':
        throw Exception('Email inválido.');
      case 'user-disabled':
        throw Exception('Usuário desabilitado.');
      case 'network-request-failed':
        throw Exception('Sem conexão com internet.');
      default:
        throw Exception('Erro ao fazer login: ${e.message}');
    }
    
  } catch (e) {
    print('❌ Erro inesperado no login: $e');
    
    if (e is Exception) {
      rethrow;
    }
    
    throw Exception('Erro ao fazer login: $e');
  }
}

  // Login local
  static Future<UserRegistrationData?> _loginLocally(String email, String password) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final usersJson = prefs.getString(_usersKey) ?? '[]';
      final List<dynamic> usersList = jsonDecode(usersJson);

      final hashedPassword = _hashPassword(password);

      for (var userJson in usersList) {
        if (userJson['email'] == email && userJson['senha'] == hashedPassword) {
          final user = UserRegistrationData.fromJson(userJson);
          await prefs.setString(_currentUserKey, jsonEncode(userJson));
          
          print('Login realizado localmente: $email');
          return user;
        }
      }

      return null;

    } catch (e) {
      print('Erro no login local: $e');
      return null;
    }
  }

  // Obter usuário atual (prioriza dados mais recentes)
  static Future<UserRegistrationData?> getCurrentUser() async {
    try {
      // Se online, tentar buscar dados atualizados do Firebase
      if (await _hasInternetConnection()) {
        final firebaseUser = _auth.currentUser;
        if (firebaseUser != null) {
          final userData = await _getCurrentUserFromFirebase(firebaseUser.uid);
          if (userData != null) {
            await _saveCurrentUserLocally(userData);
            return userData;
          }
        }
      }

      // Fallback: dados locais
      return await _getCurrentUserFromLocal();

    } catch (e) {
      print('Erro ao obter usuario atual: $e');
      return await _getCurrentUserFromLocal();
    }
  }

  // Buscar usuário atual no Firebase
  static Future<UserRegistrationData?> _getCurrentUserFromFirebase(String uid) async {
    try {
      DocumentSnapshot userDoc = await _firestore
          .collection(_usersCollection)
          .doc(uid)
          .get();

      if (userDoc.exists) {
        return _firestoreToUserData(userDoc.data() as Map<String, dynamic>);
      }
    } catch (e) {
      print('Erro ao buscar usuario no Firebase: $e');
    }
    return null;
  }

  // Buscar usuário atual localmente
  static Future<UserRegistrationData?> _getCurrentUserFromLocal() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final userJson = prefs.getString(_currentUserKey);

      if (userJson != null) {
        return UserRegistrationData.fromJson(jsonDecode(userJson));
      }
    } catch (e) {
      print('Erro ao buscar usuario localmente: $e');
    }
    return null;
  }

  // Atualizar usuário (Local + Firebase)
  static Future<bool> updateUser(UserRegistrationData userData) async {
    try {
      bool updatedInFirebase = false;

      // Tentar atualizar no Firebase
      if (await _hasInternetConnection()) {
        try {
          await _updateInFirebase(userData);
          updatedInFirebase = true;
          print('Usuario atualizado no Firebase');
        } catch (e) {
          print('Falha ao atualizar no Firebase: $e');
        }
      }

      // Sempre atualizar localmente
      await _updateLocally(userData, updatedInFirebase);
      print('Usuario atualizado localmente');

      return true;

    } catch (e) {
      print('Erro ao atualizar usuario: $e');
      return false;
    }
  }

  // Atualizar no Firebase
  static Future<void> _updateInFirebase(UserRegistrationData userData) async {
    final firebaseUser = _auth.currentUser;
    if (firebaseUser == null) {
      throw Exception('Usuario nao esta logado no Firebase');
    }

    await _firestore.collection(_usersCollection).doc(firebaseUser.uid).update({
      'nome': userData.nome.trim(),
      'idade': userData.idade,
      'sexo': userData.sexo,
      'metas': userData.metas,
      'nivelAtividade': userData.nivelAtividade,
      'areasDesejadas': userData.areasDesejadas,
      'pesoAtual': userData.pesoAtual,
      'pesoDesejado': userData.pesoDesejado,
      'altura': userData.altura,
      'imc': userData.calcularIMC(),
      'imcStatus': userData.getIMCStatus(),
      'tiposTreino': userData.tiposTreino,
      'equipamentos': userData.equipamentos,
      'tempoDisponivel': userData.tempoDisponivel,
      'malaFlexibilidade': userData.malaFlexibilidade,
      'updatedAt': FieldValue.serverTimestamp(),
      'syncStatus': 'synced',
    });
  }

  // Atualizar localmente
  static Future<void> _updateLocally(UserRegistrationData userData, bool syncedWithFirebase) async {
    final prefs = await SharedPreferences.getInstance();
    
    final userDataLocal = userData.toJson();
    userDataLocal['syncStatus'] = syncedWithFirebase ? 'synced' : 'pending';
    
    // Atualizar usuário atual
    await prefs.setString(_currentUserKey, jsonEncode(userDataLocal));

    // Atualizar na lista de usuários
    final usersJson = prefs.getString(_usersKey) ?? '[]';
    final List<dynamic> usersList = jsonDecode(usersJson);

    for (int i = 0; i < usersList.length; i++) {
      if (usersList[i]['email'] == userData.email) {
        usersList[i] = userDataLocal;
        break;
      }
    }

    await prefs.setString(_usersKey, jsonEncode(usersList));
  }

  // Sincronizar dados pendentes
  static Future<void> syncPendingData() async {
    if (!await _hasInternetConnection()) {
      print('Sem conexao - sincronizacao adiada');
      return;
    }

    try {
      final prefs = await SharedPreferences.getInstance();
      final pendingSync = prefs.getStringList('pending_sync') ?? [];

      for (String email in pendingSync) {
        await _syncUserData(email);
      }

      // Limpar lista de pendências
      await prefs.setStringList('pending_sync', []);
      print('Sincronizacao concluida');

    } catch (e) {
      print('Erro na sincronizacao: $e');
    }
  }

  // Sincronizar dados de um usuário específico
  static Future<void> _syncUserData(String email) async {
    // Implementar lógica de sincronização específica
    print('Sincronizando dados de: $email');
  }

  // Logout (funciona para Google e email/senha)
  
  /// Logout melhorado - garante limpeza completa do estado
  static Future<void> logout() async {
    try {
      print('🚀 Iniciando processo de logout...');
      
      // 1. Logout do Google primeiro (se logado via Google)
      try {
        if (await _googleSignIn.isSignedIn()) {
          await _googleSignIn.signOut();
          print('✅ Google Sign-Out realizado');
        }
      } catch (e) {
        print('⚠️ Erro no Google Sign-Out: $e');
      }
      
      // 2. Logout do Firebase Auth
      try {
        if (_auth.currentUser != null) {
          await _auth.signOut();
          print('✅ Firebase Auth Sign-Out realizado');
        }
      } catch (e) {
        print('⚠️ Erro no Firebase Sign-Out: $e');
      }
      
      // 3. Limpar TODOS os dados locais relacionados ao usuário
      final prefs = await SharedPreferences.getInstance();
      
      // Remover usuário atual
      await prefs.remove(_currentUserKey);
      print('✅ Usuário atual removido do cache local');
      
      // OPCIONAL: Limpar também outros dados que podem interferir
      // Descomente se necessário:
      // await prefs.remove(_usersKey); // Remove todos os usuários locais
      // await prefs.clear(); // Limpa TUDO (use com cuidado)
      
      print('✅ Logout realizado com sucesso');
      
    } catch (e) {
      print('❌ Erro crítico no logout: $e');
      
      // Fallback: forçar limpeza mesmo com erro
      try {
        final prefs = await SharedPreferences.getInstance();
        await prefs.remove(_currentUserKey);
        print('✅ Limpeza de emergência realizada');
      } catch (e2) {
        print('❌ Falha na limpeza de emergência: $e2');
      }
    }
  }

  // Verificar se há usuário logado
  static Future<bool> isUserLoggedIn() async {
    try {
      // 1. Verificar Firebase Auth primeiro (mais confiável)
      if (_auth.currentUser != null) {
        print('🔍 Usuario logado no Firebase: ${_auth.currentUser!.uid}');
        return true;
      }
      
      // 2. Se não tem Firebase, verificar local (mas apenas se Firebase não estiver disponível)
      final prefs = await SharedPreferences.getInstance();
      final hasLocalUser = prefs.getString(_currentUserKey) != null;
      
      if (hasLocalUser) {
        print('🔍 Usuario encontrado no cache local (sem Firebase)');
        return true;
      }
      
      print('🔍 Nenhum usuario logado encontrado');
      return false;
    } catch (e) {
      print('❌ Erro ao verificar login: $e');
      return false;
    }
  }
  /// Método para forçar limpeza completa (usar em casos extremos)
  static Future<void> forceCompleteLogout() async {
    try {
      print('🧹 Forçando limpeza completa...');
      
      // Google
      await _googleSignIn.signOut();
      await _googleSignIn.disconnect(); // Desconecta completamente
      
      // Firebase
      await _auth.signOut();
      
      // SharedPreferences - limpar TUDO
      final prefs = await SharedPreferences.getInstance();
      await prefs.clear();
      
      print('✅ Limpeza completa realizada');
    } catch (e) {
      print('❌ Erro na limpeza completa: $e');
    }
  }

  // ==================== SINCRONIZAÇÃO COM DJANGO ====================

/// Enviar dados do perfil para o Django após registro
static Future<bool> syncProfileWithDjango(UserRegistrationData userData) async {
  try {
    // Obter token do Firebase
    final token = await _auth.currentUser?.getIdToken();
    if (token == null) {
      print('❌ Não foi possível obter token do Firebase');
      return false;
    }

    // Mapear dados para formato esperado pelo Django
    final requestData = {
      'nome': userData.nome,
      'email': userData.email,
      'idade': userData.idade,
      'sexo': userData.sexo,
      
      // Mapear objetivo (metas -> objetivo)
      'objetivo': _mapMetaToObjetivo(userData.metas),
      
      // Mapear nível de atividade
      'nivel_atividade': _mapNivelAtividade(userData.nivelAtividade),
      
      // Dados físicos
      'peso_atual': userData.pesoAtual,
      'peso_desejado': userData.pesoDesejado,
      'altura': userData.altura,
      
      // Preferências (converter listas em strings)
      'areas_desejadas': userData.areasDesejadas.join(','),
      'tipos_treino': userData.tiposTreino.join(','),
      'equipamentos': userData.equipamentos,
      'tempo_disponivel': userData.tempoDisponivel,

      'training_frequency': userData.frequenciaSemanal,
      'preferred_training_days': userData.diasPreferidos ?? [],
      'preferred_workout_time': _mapHorarioToEnglish(userData.horarioPreferido),
      'min_rest_days_between_workouts': userData.diasDescanso,
      'physical_limitations': userData.limitacoesFisicas,
    };

    print('📤 Enviando dados para Django: $requestData');

    // Fazer requisição POST para o Django
    final response = await http.post(
      Uri.parse('$_djangoBaseUrl/users/register/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode(requestData),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      print('✅ Perfil sincronizado com Django');
      return true;
    } else {
      print('❌ Erro ao sincronizar com Django: ${response.statusCode}');
      print('Response: ${response.body}');
      return false;
    }
    
  } catch (e) {
    print('❌ Erro ao sincronizar com Django: $e');
    return false;
  }
}

/// Mapear metas do Flutter para objetivo do Django
static String _mapMetaToObjetivo(List<String> metas) {
  if (metas.isEmpty) return 'Manter Forma';
  
  final meta = metas.first;
  
  // Mapeamento exato com o que o Django espera
  final mapeamento = {
    'Emagrecimento': 'Perder peso',
    'Perder peso': 'Perder peso',
    'Ganho Muscular': 'Ganhar massa',
    'Ganhar massa': 'Ganhar massa',
    'Manter Forma': 'Manter forma',
    'Manter forma': 'Manter forma',
    'Bem Estar': 'Manter forma',
  };
  
  return mapeamento[meta] ?? 'Manter forma';
}

/// Mapear nível de atividade
static String _mapNivelAtividade(String nivel) {
  final mapeamento = {
    'Sedentário': 'Sedentário',
    'Moderado': 'Moderado',
    'Ativo': 'Moderado', // Django não tem "Ativo", usa "Moderado"
    'Muito Ativo': 'Intenso',
    'Intenso': 'Intenso',
  };
  
  return mapeamento[nivel] ?? 'Moderado';
}

/// Mapear horário de treino para o formato inglês esperado pelo Django
static String _mapHorarioToEnglish(String horario) {
  final mapeamento = {
    'manha': 'morning',
    'manhã': 'morning',
    'morning': 'morning',
    'tarde': 'afternoon',
    'afternoon': 'afternoon',
    'noite': 'evening',
    'evening': 'evening',
    'flexivel': 'flexible',
    'flexível': 'flexible',
    'flexible': 'flexible',
  };
  
  return mapeamento[horario.toLowerCase()] ?? 'flexible';
}
/// Atualizar perfil no Django
static Future<bool> updateProfileInDjango(UserRegistrationData userData) async {
  try {
    final token = await _auth.currentUser?.getIdToken();
    if (token == null) {
      print('❌ Não foi possível obter token do Firebase');
      return false;
    }

    final requestData = {
      'nome': userData.nome,
      'idade': userData.idade,
      'sexo': userData.sexo,
      'objetivo': _mapMetaToObjetivo(userData.metas),
      'nivel_atividade': _mapNivelAtividade(userData.nivelAtividade),
      'peso_atual': userData.pesoAtual,
      'peso_desejado': userData.pesoDesejado,
      'altura': userData.altura,
      'areas_desejadas': userData.areasDesejadas.join(','),
      'tipos_treino': userData.tiposTreino.join(','),
      'equipamentos': userData.equipamentos,
      'tempo_disponivel': userData.tempoDisponivel,
    };

    print('📤 Atualizando perfil no Django');

    final response = await http.post(
      Uri.parse('$_djangoBaseUrl/users/register/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode(requestData),
    );

    if (response.statusCode == 200) {
      print('✅ Perfil atualizado no Django');
      return true;
    } else {
      print('❌ Erro ao atualizar Django: ${response.statusCode}');
      return false;
    }
    
  } catch (e) {
    print('❌ Erro ao atualizar Django: $e');
    return false;
  }
}

/// Obter perfil do Django (para carregar na ProfilePage)
static Future<UserRegistrationData?> getProfileFromDjango() async {
  try {
    final token = await _auth.currentUser?.getIdToken();
    if (token == null) {
      print('❌ Não foi possível obter token do Firebase');
      return null;
    }

    final response = await http.get(
      Uri.parse('$_djangoBaseUrl/users/dashboard/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      print('✅ Perfil carregado do Django');
      
      // Converter response do Django para UserRegistrationData
      return _djangoResponseToUserData(data);
    } else {
      print('❌ Erro ao carregar perfil do Django: ${response.statusCode}');
      return null;
    }
    
  } catch (e) {
    print('❌ Erro ao carregar perfil do Django: $e');
    return null;
  }
}

/// Converter resposta do Django para UserRegistrationData
static UserRegistrationData _djangoResponseToUserData(Map<String, dynamic> data) {
  final user = data['user'] ?? {};
  final profile = user['profile'] ?? user; // ✅ Tenta buscar dentro de 'profile' primeiro
  
  // 🔍 DEBUG: Mostrar o que está sendo recebido
  print('🔍 DEBUG - Dados recebidos do Django:');
  print('User keys: ${user.keys.toList()}');
  if (user['profile'] != null) {
    print('Profile keys: ${(user['profile'] as Map).keys.toList()}');
  }
  
  return UserRegistrationData(
    nome: user['first_name'] ?? user['username'] ?? '',
    email: user['email'] ?? '',
    senha: '', 
    
    // ✅ CORRIGIDO: Tenta múltiplas possibilidades de nome de campo
    idade: _parseIntSafely(
      profile['idade'] ?? 
      profile['age'] ?? 
      user['idade'] ?? 
      user['age']
    ),
    
    sexo: profile['sexo'] ?? 
          profile['gender'] ?? 
          profile['genero'] ??
          user['sexo'] ?? 
          user['gender'] ?? 
          '',
    
    metas: _parseGoalToMetas(
      profile['goal'] ?? 
      profile['objetivo'] ?? 
      user['goal']
    ),
    
    nivelAtividade: _parseActivityLevel(
      profile['activity_level'] ?? 
      profile['nivel_atividade'] ?? 
      user['activity_level']
    ),
    
    areasDesejadas: _parseStringToList(
      profile['focus_areas'] ?? 
      profile['areas_desejadas'] ?? 
      user['focus_areas']
    ),
    
    // ✅ CORRIGIDO: Tenta nomes em português e inglês
    pesoAtual: _parseDoubleSafely(
      profile['peso_atual'] ?? 
      profile['current_weight'] ?? 
      user['peso_atual'] ?? 
      user['current_weight']
    ),
    
    pesoDesejado: _parseDoubleSafely(
      profile['peso_desejado'] ?? 
      profile['target_weight'] ?? 
      user['peso_desejado'] ?? 
      user['target_weight']
    ),
    
    altura: _parseDoubleSafely(
      profile['altura'] ?? 
      profile['height'] ?? 
      profile['altura_cm'] ??
      user['altura'] ?? 
      user['height']
    ),
    
    tiposTreino: _parseStringToList(
      profile['tipos_treino'] ?? 
      user['tipos_treino']
    ),
    
    equipamentos: profile['equipamentos'] ?? 
                  user['equipamentos'] ?? 
                  '',
    
    tempoDisponivel: profile['tempo_disponivel'] ?? 
                     user['tempo_disponivel'] ?? 
                     '',
    
    malaFlexibilidade: profile['mala_flexibilidade'] ?? 
                       user['mala_flexibilidade'] ?? 
                       false,
    
    createdAt: DateTime.now(),
  );
}

// Helpers de conversão
static int _parseIntSafely(dynamic value) {
  if (value == null) return 0;
  if (value is int) return value;
  if (value is String) return int.tryParse(value) ?? 0;
  return 0;
}

static double _parseDoubleSafely(dynamic value) {
  if (value == null) return 0.0;
  if (value is double) return value;
  if (value is int) return value.toDouble();
  if (value is String) return double.tryParse(value) ?? 0.0;
  return 0.0;
}

static List<String> _parseGoalToMetas(String? goal) {
  if (goal == null) return ['Manter Forma'];
  
  final mapeamento = {
    'lose_weight': 'Perder peso',
    'gain_muscle': 'Ganhar massa',
    'maintain': 'Manter forma',
  };
  
  return [mapeamento[goal] ?? 'Manter forma'];
}

static String _parseActivityLevel(String? level) {
  if (level == null) return 'Moderado';
  
  final mapeamento = {
    'sedentary': 'Sedentário',
    'light': 'Leve',
    'moderate': 'Moderado',
    'very_active': 'Intenso',
  };
  
  return mapeamento[level] ?? 'Moderado';
}

static List<String> _parseStringToList(String? value) {
  if (value == null || value.isEmpty) return [];
  return value.split(',').map((e) => e.trim()).toList();
}
  // === MÉTODOS AUXILIARES ===

  // Converter dados do Firestore para UserRegistrationData
  static UserRegistrationData _firestoreToUserData(Map<String, dynamic> data) {
    return UserRegistrationData(
      nome: data['nome'] ?? '',
      email: data['email'] ?? '',
      senha: '', // Não armazenar senha
      idade: data['idade'] ?? 0,
      sexo: data['sexo'] ?? '',
      metas: List<String>.from(data['metas'] ?? []),
      nivelAtividade: data['nivelAtividade'] ?? '',
      areasDesejadas: List<String>.from(data['areasDesejadas'] ?? []),
      pesoAtual: (data['pesoAtual'] ?? 0.0).toDouble(),
      pesoDesejado: (data['pesoDesejado'] ?? 0.0).toDouble(),
      altura: (data['altura'] ?? 0.0).toDouble(),
      tiposTreino: List<String>.from(data['tiposTreino'] ?? []),
      equipamentos: data['equipamentos'] ?? '',
      tempoDisponivel: data['tempoDisponivel'] ?? '',
      malaFlexibilidade: data['malaFlexibilidade'] ?? false,
      createdAt: data['createdAt'] != null 
          ? (data['createdAt'] as Timestamp).toDate()
          : DateTime.now(),
    );
  }

  // Salvar usuário atual localmente
  static Future<void> _saveCurrentUserLocally(UserRegistrationData userData) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_currentUserKey, jsonEncode(userData.toJson()));
  }

  // === MÉTODOS PARA DEBUG ===

  // Status da sincronização
  static Future<Map<String, dynamic>> getSyncStatus() async {
    final prefs = await SharedPreferences.getInstance();
    final pendingSync = prefs.getStringList('pending_sync') ?? [];
    final hasInternet = await _hasInternetConnection();
    final firebaseUser = _auth.currentUser;

    return {
      'hasInternet': hasInternet,
      'firebaseLoggedIn': firebaseUser != null,
      'pendingSync': pendingSync,
      'pendingCount': pendingSync.length,
    };
  }

  // Forçar sincronização manual
  static Future<void> forceSyncNow() async {
    print('Iniciando sincronizacao manual...');
    await syncPendingData();
  }

  // === NOVOS MÉTODOS PARA COMPATIBILIDADE ===
  
  /// Usuário atual (Firebase)
  static User? get currentUser => _auth.currentUser;

   /// Stream melhorado de mudanças de autenticação
  static Stream<User?> get authStateChanges {
    return _auth.authStateChanges().distinct(); // Evita eventos duplicados
  }

  /// Verificar estado atual detalhado (para debug)
  static Future<Map<String, dynamic>> getAuthDebugInfo() async {
    final prefs = await SharedPreferences.getInstance();
    final localUser = prefs.getString(_currentUserKey);
    final firebaseUser = _auth.currentUser;
    
    return {
      'firebase': {
        'isLoggedIn': firebaseUser != null,
        'uid': firebaseUser?.uid,
        'email': firebaseUser?.email,
        'displayName': firebaseUser?.displayName,
      },
      'local': {
        'hasData': localUser != null,
        'data': localUser != null ? 'exists' : 'null',
      },
      'google': {
        'isSignedIn': await _googleSignIn.isSignedIn(),
        'currentAccount': (await _googleSignIn.signInSilently())?.email,
      },
    };
  }

  /// Verificar se usuário está logado
  static bool get isLoggedIn => currentUser != null;

  /// Obter informações do usuário atual
  static Map<String, dynamic>? get currentUserInfo {
    final user = currentUser;
    if (user == null) return null;
    
    return {
      'uid': user.uid,
      'email': user.email,
      'name': user.displayName,
      'photoUrl': user.photoURL,
      'emailVerified': user.emailVerified,
      'providers': user.providerData.map((p) => p.providerId).toList(),
    };
  }
}