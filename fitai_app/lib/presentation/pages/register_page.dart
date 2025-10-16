// ====== REGISTER PAGE OTIMIZADO - SEM ERROS ======
import 'package:flutter/material.dart';
import '../../../core/router/app_router.dart';
import '../../service/user_service.dart';
import '../../models/user_model.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../../service/ai_workout_generator_service.dart';


class RegisterPageOptimized extends StatefulWidget {
  const RegisterPageOptimized({super.key});

  @override
  State<RegisterPageOptimized> createState() => _RegisterPageOptimizedState();
}

class _RegisterPageOptimizedState extends State<RegisterPageOptimized> {
  final PageController _pageController = PageController();
  final UserRegistrationData _userData = UserRegistrationData();
  int _currentPage = 0;
  bool _isLoading = false;

  // Controllers lazy initialization
  late final TextEditingController _nomeController;
  late final TextEditingController _emailController;
  late final TextEditingController _senhaController;
  late final TextEditingController _idadeController;
  late final TextEditingController _pesoAtualController;
  late final TextEditingController _pesoDesejadoController;
  late final TextEditingController _alturaController;

  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();

  @override
  void initState() {
    super.initState();
    _initControllers();
  }

  void _initControllers() {
    _nomeController = TextEditingController();
    _emailController = TextEditingController();
    _senhaController = TextEditingController();
    _idadeController = TextEditingController();
    _pesoAtualController = TextEditingController();
    _pesoDesejadoController = TextEditingController();
    _alturaController = TextEditingController();
  }

  // ✅ CORRIGIDO: Conversão para Map
  void _finishRegistration() async {
    setState(() => _isLoading = true);
    
    _updateUserDataFromControllers();
    
    try {
      // 1️⃣ Verificar se email já existe
      if (await UserService.emailExists(_userData.email)) {
        _showErrorMessage('Este email já está cadastrado. Tente fazer login.');
        setState(() => _isLoading = false);
        return;
      }
      
      // 2️⃣ Criar usuário no Firebase Auth
      final userCredential = await FirebaseAuth.instance.createUserWithEmailAndPassword(
        email: _userData.email,
        password: _userData.senha,
      );
      
      debugPrint('✅ Firebase Auth: Usuário criado ${userCredential.user?.uid}');
      
      // 3️⃣ Atualizar display name
      await userCredential.user?.updateDisplayName(_userData.nome);
      
      // 4️⃣ Salvar dados do usuário no Firestore/Firebase
      debugPrint('📤 Salvando dados no Firebase...');
      bool firebaseSuccess = await UserService.registerUser(_userData);
      
      if (!firebaseSuccess) {
        throw Exception('Falha ao salvar dados no Firebase');
      }
      
      // 5️⃣ Sincronizar com Django
      debugPrint('📤 Sincronizando com backend Django...');
      bool djangoSuccess = await UserService.syncProfileWithDjango(_userData);
      
      if (!djangoSuccess) {
        debugPrint('⚠️ Aviso: Falha ao sincronizar com Django (continuando)');
      }
      
      // 6️⃣ 🤖 GERAR TREINO PERSONALIZADO COM IA
      debugPrint('🤖 Gerando treino personalizado com IA...');
      
      if (mounted) {
        setState(() {
          // Atualizar UI para mostrar que está gerando treino
        });
      }
      
      // ✅ CORRIGIDO: Usar .toMap() para converter objeto em Map
      final workoutResult = await AIWorkoutGeneratorService.generatePersonalizedWorkout(
        userData: _userData.toMap(),  // ✅ CORRIGIDO
      );
      
      if (workoutResult != null) {
        debugPrint('✅ Treino personalizado criado! ID: ${workoutResult['workout_id']}');
        
        if (mounted) {
          _showSuccessMessage(
            'Cadastro realizado! Seu treino personalizado está pronto! 🎉'
          );
        }
      } else {
        debugPrint('⚠️ Não foi possível gerar treino automaticamente');
        
        if (mounted) {
          _showSuccessMessage(
            'Cadastro realizado! Você pode gerar seu treino no dashboard.'
          );
        }
      }
      
      // 7️⃣ Aguardar redirect automático do AuthNotifier
      debugPrint('🚀 Cadastro completo, aguardando redirect...');
      
      // Pequeno delay para garantir que a mensagem de sucesso seja vista
      await Future.delayed(const Duration(seconds: 2));
      
    } on FirebaseAuthException catch (e) {
      debugPrint('❌ Erro Firebase: ${e.code}');
      String errorMessage;
      
      switch (e.code) {
        case 'email-already-in-use':
          errorMessage = 'Este email já está sendo usado.';
          break;
        case 'weak-password':
          errorMessage = 'Senha muito fraca. Use pelo menos 6 caracteres.';
          break;
        case 'invalid-email':
          errorMessage = 'Email inválido.';
          break;
        default:
          errorMessage = 'Erro no cadastro: ${e.message}';
      }
      
      if (mounted) _showErrorMessage(errorMessage);
      
    } catch (e) {
      debugPrint('❌ Erro inesperado: $e');
      if (mounted) {
        _showErrorMessage('Erro ao realizar cadastro: ${e.toString()}');
      }
      
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _updateUserDataFromControllers() {
    _userData.nome = _nomeController.text.trim();
    _userData.email = _emailController.text.trim().toLowerCase();
    _userData.senha = _senhaController.text;
    _userData.idade = int.tryParse(_idadeController.text) ?? 0;
    _userData.pesoAtual = double.tryParse(_pesoAtualController.text) ?? 0.0;
    _userData.pesoDesejado = double.tryParse(_pesoDesejadoController.text) ?? 0.0;
    _userData.altura = double.tryParse(_alturaController.text) ?? 0.0;
  }

  bool _validateCurrentStep() {
    switch (_currentPage) {
      case 0:
        // Step 1: Dados básicos
        if (!_formKey.currentState!.validate()) {
          return false;
        }
        _updateUserDataFromControllers();
        return _userData.nome.isNotEmpty && 
               _userData.email.isNotEmpty && 
               _userData.senha.length >= 6 &&
               _userData.idade >= 13 &&
               _userData.sexo.isNotEmpty;
        
      case 1:
        // Step 2: Metas
        return _userData.metas.isNotEmpty;
        
      case 2:
        // Step 3: Nível de atividade
        return _userData.nivelAtividade.isNotEmpty;
        
      case 3:
        // Step 4: Áreas desejadas
        return _userData.areasDesejadas.isNotEmpty;
        
      case 4:
        // Step 5: Dados físicos
        _updateUserDataFromControllers();
        return _userData.pesoAtual > 0 && 
               _userData.pesoDesejado > 0 && 
               _userData.altura > 0;
        
      case 5:
        // Step 6: Preferências de treino
        return _userData.tiposTreino.isNotEmpty &&
               _userData.equipamentos.isNotEmpty &&
               _userData.tempoDisponivel.isNotEmpty;

      case 6:  // 🆕 NOVO - Step 6A: Preferências avançadas
      return _userData.frequenciaSemanal > 0 &&
             _userData.diasDescanso >= 0;
      case 7:
        // Step 7: Finalização (sempre válido)
        return true;
        
      default:
        return true;
    }
  }

  void _showErrorMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        duration: const Duration(seconds: 3),
      ),
    );
  }

  void _showSuccessMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: const Color(0xFF00BCD4),
        duration: const Duration(seconds: 2),
      ),
    );
  }
 
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1A1A1A),
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),
            _buildProgressIndicator(),
            Expanded(
              child: PageView(
                controller: _pageController,
                physics: const NeverScrollableScrollPhysics(),
                onPageChanged: (index) {
                  setState(() {
                    _currentPage = index;
                  });
                },
                children: [
                  _buildStep1(),
                  _buildStep2(),
                  _buildStep3(),
                  _buildStep4(),
                  _buildStep5(),
                  _buildStep6(),
                  _buildStep6A(),
                  _buildStep7(),
                ],
              ),
            ),
            _buildNavigationButtons(),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    const titles = [
      'Criar sua Conta!',
      'Qual sua meta?',
      'Algumas perguntas para\npersonalizar seu treino!',
      'Selecione áreas que\ndeseja focar',
      'Insira seu peso e altura!',
      'Preferências de treino',
      'Mais algumas perguntas!',
      'Gerando treino!'
    ];

    return Padding(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        children: [
          Container(
            width: 60,
            height: 30,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF00BCD4), Color(0xFF0097A7)],
              ),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Center(
              child: Text(
                'FITAI',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
            ),
          ),
          const SizedBox(height: 20),
          Text(
            titles[_currentPage],
            style: const TextStyle(
              color: Colors.white,
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildProgressIndicator() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 40.0),
      child: LinearProgressIndicator(
        value: (_currentPage + 1) / 8,
        backgroundColor: Colors.grey[800],
        valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF00BCD4)),
      ),
    );
  }

  Widget _buildStep1() {
    return Padding(
      padding: const EdgeInsets.all(20.0),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            children: [
              const SizedBox(height: 40),
              _buildTextField('Nome:', _nomeController, validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Nome é obrigatório';
                }
                if (value.trim().length < 2) {
                  return 'Nome deve ter pelo menos 2 caracteres';
                }
                if (value.trim().length > 50) {
                  return 'Nome muito longo (máximo 50 caracteres)';
                }
                return null;
              }),
              const SizedBox(height: 20),
              _buildTextField('Email:', _emailController, validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Email é obrigatório';
                }
                if (!RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(value.trim())) {
                  return 'Email inválido';
                }
                return null;
              }),
              const SizedBox(height: 20),
              _buildTextField('Senha:', _senhaController, isPassword: true, validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Senha é obrigatória';
                }
                if (value.length < 6) {
                  return 'Senha deve ter pelo menos 6 caracteres';
                }
                if (value.length > 50) {
                  return 'Senha muito longa (máximo 50 caracteres)';
                }
                return null;
              }),
              const SizedBox(height: 20),
              _buildTextField('Idade:', _idadeController, isNumber: true, validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Idade é obrigatória';
                }
                int? age = int.tryParse(value);
                if (age == null || age < 13 || age > 100) {
                  return 'Idade deve estar entre 13 e 100 anos';
                }
                return null;
              }),
              const SizedBox(height: 30),
              
              const Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  'Sexo: ',
                  style: TextStyle(color: Colors.white, fontSize: 16),
                ),
              ),
              const SizedBox(height: 10),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _buildGenderOption('Masculino', Icons.man),
                  _buildGenderOption('Feminino', Icons.woman),
                ],
              ),
              const SizedBox(height: 30),
              GestureDetector(
                onTap: AppRouter.goToLogin,
                child: const Text(
                  'Já tenho conta!',
                  style: TextStyle(
                    color: Color(0xFF00BCD4),
                    decoration: TextDecoration.underline,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStep2() {
    return Padding(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        children: [
          const SizedBox(height: 40),
          const Text(
            'FITAI criará os treinos mais\nadequados para seu objetivo!',
            style: TextStyle(color: Colors.grey, fontSize: 14),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 40),
          _buildMetaButton('Manter Forma', _userData.metas.contains('Manter Forma'), () {
            setState(() {
              if (_userData.metas.contains('Manter Forma')) {
                _userData.metas.remove('Manter Forma');
              } else {
                _userData.metas.add('Manter Forma');
              }
            });
          }),
          const SizedBox(height: 15),
          _buildMetaButton('Ganho Muscular', _userData.metas.contains('Ganho Muscular'), () {
            setState(() {
              if (_userData.metas.contains('Ganho Muscular')) {
                _userData.metas.remove('Ganho Muscular');
              } else {
                _userData.metas.add('Ganho Muscular');
              }
            });
          }),
          const SizedBox(height: 15),
          _buildMetaButton('Bem Estar', _userData.metas.contains('Bem Estar'), () {
            setState(() {
              if (_userData.metas.contains('Bem Estar')) {
                _userData.metas.remove('Bem Estar');
              } else {
                _userData.metas.add('Bem Estar');
              }
            });
          }),
          const SizedBox(height: 15),
          _buildMetaButton('Emagrecimento', _userData.metas.contains('Emagrecimento'), () {
            setState(() {
              if (_userData.metas.contains('Emagrecimento')) {
                _userData.metas.remove('Emagrecimento');
              } else {
                _userData.metas.add('Emagrecimento');
              }
            });
          }),
        ],
      ),
    );
  }

  Widget _buildStep3() {
    return Padding(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        children: [
          const SizedBox(height: 40),
          const Text(
            'Qual seu nível de atividade física?',
            style: TextStyle(color: Colors.white, fontSize: 16),
          ),
          const SizedBox(height: 40),
          _buildOptionButton('Sedentário', _userData.nivelAtividade == 'Sedentário', () {
            setState(() {
              _userData.nivelAtividade = 'Sedentário';
            });
          }),
          const SizedBox(height: 5),
          const Text(
            'Pouco ou nenhum exercício',
            style: TextStyle(color: Colors.grey, fontSize: 12),
          ),
          const SizedBox(height: 20),
          _buildOptionButton('Moderado', _userData.nivelAtividade == 'Moderado', () {
            setState(() {
              _userData.nivelAtividade = 'Moderado';
            });
          }),
          const SizedBox(height: 5),
          const Text(
            '1-3 dias por semana',
            style: TextStyle(color: Colors.grey, fontSize: 12),
          ),
          const SizedBox(height: 20),
          _buildOptionButton('Ativo', _userData.nivelAtividade == 'Ativo', () {
            setState(() {
              _userData.nivelAtividade = 'Ativo';
            });
          }),
          const SizedBox(height: 5),
          const Text(
            '3-5 dias por semana',
            style: TextStyle(color: Colors.grey, fontSize: 12),
          ),
          const SizedBox(height: 20),
          _buildOptionButton('Muito Ativo', _userData.nivelAtividade == 'Muito Ativo', () {
            setState(() {
              _userData.nivelAtividade = 'Muito Ativo';
            });
          }),
          const SizedBox(height: 5),
          const Text(
            '5+ dias por semana',
            style: TextStyle(color: Colors.grey, fontSize: 12),
          ),
        ],
      ),
    );
  }

  Widget _buildStep4() {
    return Padding(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        children: [
          const SizedBox(height: 20),
          const Text(
            'Áreas do corpo que deseja trabalhar/melhorar',
            style: TextStyle(color: Colors.grey, fontSize: 14),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 30),
          
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 100,
                height: 200,
                decoration: BoxDecoration(
                  color: Colors.grey[800],
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(
                  Icons.person,
                  size: 80,
                  color: Colors.grey,
                ),
              ),
              const SizedBox(width: 20),
              Container(
                width: 100,
                height: 200,
                decoration: BoxDecoration(
                  color: Colors.grey[800],
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(
                  Icons.person,
                  size: 80,
                  color: Colors.grey,
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 30),
          
          Wrap(
            spacing: 10,
            runSpacing: 10,
            alignment: WrapAlignment.center,
            children: [
              _buildAreaChip('Braços'),
              _buildAreaChip('Peito'),
              _buildAreaChip('Costas'),
              _buildAreaChip('Abdômen'),
              _buildAreaChip('Pernas'),
              _buildAreaChip('Glúteos'),
              _buildAreaChip('Ombros'),
              _buildAreaChip('Core'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStep5() {
    return Padding(
      padding: const EdgeInsets.all(20.0),
      child: SingleChildScrollView(
        child: Column(
          children: [
            const SizedBox(height: 40),
            const Text(
              'Registre seu perfil!',
              style: TextStyle(color: Colors.grey, fontSize: 14),
            ),
            const SizedBox(height: 40),
            
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Peso Atual', style: TextStyle(color: Colors.white)),
                      const SizedBox(height: 8),
                      _buildNumberField(_pesoAtualController, 'KG'),
                    ],
                  ),
                ),
                const SizedBox(width: 20),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Peso Desejado', style: TextStyle(color: Colors.white)),
                      const SizedBox(height: 8),
                      _buildNumberField(_pesoDesejadoController, 'KG'),
                    ],
                  ),
                ),
              ],
            ),
            
            const SizedBox(height: 30),
            
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Altura', style: TextStyle(color: Colors.white)),
                const SizedBox(height: 8),
                _buildNumberField(_alturaController, 'cm'),
              ],
            ),
            
            const SizedBox(height: 40),
            
            // IMC Calculator
            ValueListenableBuilder<TextEditingValue>(
              valueListenable: _pesoAtualController,
              builder: (context, pesoValue, child) {
                return ValueListenableBuilder<TextEditingValue>(
                  valueListenable: _alturaController,
                  builder: (context, alturaValue, child) {
                    double peso = double.tryParse(pesoValue.text) ?? 0;
                    double altura = double.tryParse(alturaValue.text) ?? 0;
                    
                    String imcText = 'IMC: Não calculado';
                    String statusText = '';
                    Color imcColor = Colors.grey;
                    
                    if (peso > 0 && altura > 0) {
                      double alturaM = altura / 100;
                      double imc = peso / (alturaM * alturaM);
                      imcText = 'IMC: ${imc.toStringAsFixed(1)}';
                      
                      if (imc < 18.5) {
                        statusText = 'Abaixo do peso';
                        imcColor = Colors.blue;
                      } else if (imc < 25) {
                        statusText = 'Peso normal';
                        imcColor = Colors.green;
                      } else if (imc < 30) {
                        statusText = 'Sobrepeso';
                        imcColor = Colors.orange;
                      } else {
                        statusText = 'Obesidade';
                        imcColor = Colors.red;
                      }
                    }
                    
                    return Container(
                      padding: const EdgeInsets.all(15),
                      decoration: BoxDecoration(
                        color: Colors.grey[850],
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Column(
                        children: [
                          Text(
                            imcText,
                            style: const TextStyle(
                              color: Colors.white, 
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          if (statusText.isNotEmpty) ...[
                            const SizedBox(height: 5),
                            Text(
                              statusText,
                              style: TextStyle(
                                color: imcColor,
                                fontSize: 14,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ],
                        ],
                      ),
                    );
                  },
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStep6() {
    return Padding(
      padding: const EdgeInsets.all(20.0),
      child: SingleChildScrollView(
        child: Column(
          children: [
            const SizedBox(height: 20),
            const Text(
              'Vamos finalizar personalizando!',
              style: TextStyle(color: Colors.grey, fontSize: 14),
            ),
            const SizedBox(height: 30),
            
            const Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Tipos de treino favoritos?',
                style: TextStyle(color: Colors.white, fontSize: 16),
              ),
            ),
            const SizedBox(height: 15),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: [
                _buildTreinoChip('Musculação'),
                _buildTreinoChip('Cardio'),
                _buildTreinoChip('Calistenia'),
                _buildTreinoChip('Treinos Funcionais'),
                _buildTreinoChip('HIIT'),
                _buildTreinoChip('Yoga'),
              ],
            ),
            
            const SizedBox(height: 30),
            
            const Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Equipamentos Disponíveis?',
                style: TextStyle(color: Colors.white, fontSize: 16),
              ),
            ),
            const SizedBox(height: 15),
            Column(
              children: [
                _buildEquipamentoOption('Sem equipamentos'),
                const SizedBox(height: 10),
                _buildEquipamentoOption('Equipamentos básicos'),
                const SizedBox(height: 10),
                _buildEquipamentoOption('Academia completa'),
              ],
            ),
            
            const SizedBox(height: 30),
            
            const Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Tempo disponível?',
                style: TextStyle(color: Colors.white, fontSize: 16),
              ),
            ),
            const SizedBox(height: 15),
            Column(
              children: [
                _buildTempoOption('15-30 minutos'),
                const SizedBox(height: 10),
                _buildTempoOption('30-45 minutos'),
                const SizedBox(height: 10),
                _buildTempoOption('45-60 minutos'),
                const SizedBox(height: 10),
                _buildTempoOption('60+ minutos'),
              ],
            ),
            
            const SizedBox(height: 30),
            
            Row(
              children: [
                Checkbox(
                  value: _userData.malaFlexibilidade,
                  onChanged: (value) {
                    setState(() {
                      _userData.malaFlexibilidade = value ?? false;
                    });
                  },
                  activeColor: const Color(0xFF00BCD4),
                ),
                const Expanded(
                  child: Text(
                    'Tenho flexibilidade de horário',
                    style: TextStyle(color: Colors.white),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
  Widget _buildStep6A() {  // Preferências avançadas
  return Padding(
    padding: const EdgeInsets.all(20.0),
    child: SingleChildScrollView(
      child: Column(
        children: [
          const Text(
            'Apenas mais algumas perguntas!',
            style: TextStyle(color: Colors.grey, fontSize: 14),
          ),
          const SizedBox(height: 30),

          // 🗓️ Frequência semanal
          const Text(
            'Quantos dias por semana você quer treinar?',
            style: TextStyle(color: Colors.white, fontSize: 16),
          ),
          const SizedBox(height: 15),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildFrequencyOption(2),
              _buildFrequencyOption(3),
              _buildFrequencyOption(4),
              _buildFrequencyOption(5),
              _buildFrequencyOption(6),
            ],
          ),

          const SizedBox(height: 30),

          // 💤 Dias de descanso
          const Text(
            'Precisa descansar entre treinos?',
            style: TextStyle(color: Colors.white, fontSize: 16),
          ),
          const SizedBox(height: 15),
          _buildRestOption('Sim, 1 dia entre treinos', 1),
          const SizedBox(height: 10),
          _buildRestOption('Sim, 2 dias entre treinos', 2),
          const SizedBox(height: 10),
          _buildRestOption('Não, posso treinar seguido', 0),

          const SizedBox(height: 30),

          // ⏰ Horário preferido
          const Text(
            'Qual melhor horário para treinar?',
            style: TextStyle(color: Colors.white, fontSize: 16),
          ),
          const SizedBox(height: 15),
          _buildTimeOption('Manhã (6h-12h)', 'morning'),
          const SizedBox(height: 10),
          _buildTimeOption('Tarde (12h-18h)', 'afternoon'),
          const SizedBox(height: 10),
          _buildTimeOption('Noite (18h-22h)', 'evening'),
          const SizedBox(height: 10),
          _buildTimeOption('Flexível', 'flexible'),

          const SizedBox(height: 30),

          // ⚠️ Limitações (opcional)
          const Text(
            'Tem alguma limitação física? (opcional)',
            style: TextStyle(color: Colors.grey, fontSize: 14),
          ),
          const SizedBox(height: 10),
          TextFormField(
            maxLines: 2,
            style: const TextStyle(color: Colors.black),
            decoration: InputDecoration(
              hintText: 'Ex: dor no joelho, lesão no ombro...',
              filled: true,
              fillColor: Colors.white,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(15),
              ),
            ),
            onChanged: (value) {
              _userData.limitacoesFisicas = value;
            },
          ),
        ],
      ),
    ),
  );
}
// No arquivo register_page.dart

Widget _buildFrequencyOption(int days) {
  bool isSelected = _userData.frequenciaSemanal == days;
  return GestureDetector(
    onTap: () {
      setState(() {
        _userData.frequenciaSemanal = days;
      });
    },
    child: Container(
      width: 50,
      height: 50,
      decoration: BoxDecoration(
        color: isSelected ? const Color(0xFF00BCD4) : Colors.white,
        shape: BoxShape.circle,
        border: Border.all(
          color: isSelected ? const Color(0xFF00BCD4) : Colors.grey,
          width: 2,
        ),
      ),
      child: Center(
        child: Text(
          '$days',
          style: TextStyle(
            color: isSelected ? Colors.white : Colors.black,
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    ),
  );
}

Widget _buildRestOption(String text, int days) {
  bool isSelected = _userData.diasDescanso == days;
  return GestureDetector(
    onTap: () {
      setState(() {
        _userData.diasDescanso = days;
      });
    },
    child: Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(
        color: isSelected ? const Color(0xFF00BCD4) : Colors.white,
        borderRadius: BorderRadius.circular(15),
        border: Border.all(
          color: isSelected ? const Color(0xFF00BCD4) : Colors.grey,
        ),
      ),
      child: Text(
        text,
        textAlign: TextAlign.center,
        style: TextStyle(
          color: isSelected ? Colors.white : Colors.black,
          fontSize: 14,
        ),
      ),
    ),
  );
}

Widget _buildTimeOption(String text, String value) {
  bool isSelected = _userData.horarioPreferido == value;
  return GestureDetector(
    onTap: () {
      setState(() {
        _userData.horarioPreferido = value;
      });
    },
    child: Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(
        color: isSelected ? const Color(0xFF00BCD4) : Colors.white,
        borderRadius: BorderRadius.circular(15),
        border: Border.all(
          color: isSelected ? const Color(0xFF00BCD4) : Colors.grey,
        ),
      ),
      child: Text(
        text,
        textAlign: TextAlign.center,
        style: TextStyle(
          color: isSelected ? Colors.white : Colors.black,
          fontSize: 14,
        ),
      ),
    ),
  );
}
  // ✅ CORRIGIDO: withValues ao invés de withOpacity
  Widget _buildStep7() {
    return Padding(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text(
            'Analisando seu perfil e criando\no treino perfeito para você!',
            style: TextStyle(
              color: Colors.white, 
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ),
          
          const SizedBox(height: 40),
          
          // Animação de loading com ícone de IA
          Stack(
            alignment: Alignment.center,
            children: [
              const SizedBox(
                width: 120,
                height: 120,
                child: CircularProgressIndicator(
                  strokeWidth: 6,
                  valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF00BCD4)),
                ),
              ),
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  color: const Color(0xFF00BCD4).withValues(alpha: 0.2),  // ✅ CORRIGIDO
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.psychology,
                  size: 40,
                  color: Color(0xFF00BCD4),
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 40),
          
          // Indicadores de progresso
          _buildProgressStep('✓ Perfil analisado', true),
          const SizedBox(height: 12),
          _buildProgressStep('✓ Metas identificadas', true),
          const SizedBox(height: 12),
          _buildProgressStep('⟳ IA gerando treino...', false),
          
          const SizedBox(height: 50),
          
          // Card com dica - ✅ CORRIGIDO
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  const Color(0xFF00BCD4).withValues(alpha: 0.2),  // ✅ CORRIGIDO
                  const Color(0xFF0097A7).withValues(alpha: 0.2),  // ✅ CORRIGIDO
                ],
              ),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: const Color(0xFF00BCD4),
                width: 1,
              ),
            ),
            child: const Column(
              children: [
                Icon(
                  Icons.lightbulb_outline,
                  color: Color(0xFF00BCD4),
                  size: 40,
                ),
                SizedBox(height: 12),
                Text(
                  'VOCÊ SABIA?',
                  style: TextStyle(
                    color: Color(0xFF00BCD4),
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                SizedBox(height: 8),
                Text(
                  'Nossa IA analisa mais de 15 fatores do seu\nperfil para criar o treino ideal!',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // Helper widget para steps de progresso
  Widget _buildProgressStep(String text, bool completed) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(
          completed ? Icons.check_circle : Icons.hourglass_empty,
          color: completed ? Colors.green : const Color(0xFF00BCD4),
          size: 20,
        ),
        const SizedBox(width: 10),
        Text(
          text,
          style: TextStyle(
            color: completed ? Colors.green : Colors.white,
            fontSize: 14,
          ),
        ),
      ],
    );
  }

  Widget _buildTextField(String label, TextEditingController controller, {
    bool isPassword = false, 
    bool isNumber = false, 
    String? Function(String?)? validator
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(color: Colors.white, fontSize: 16),
        ),
        const SizedBox(height: 8),
        TextFormField(
          controller: controller,
          obscureText: isPassword,
          keyboardType: isNumber ? TextInputType.number : TextInputType.text,
          style: const TextStyle(color: Colors.black),
          validator: validator,
          decoration: InputDecoration(
            filled: true,
            fillColor: Colors.white,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(25),
              borderSide: BorderSide.none,
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(25),
              borderSide: const BorderSide(color: Colors.red, width: 2),
            ),
            focusedErrorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(25),
              borderSide: const BorderSide(color: Colors.red, width: 2),
            ),
            contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
          ),
        ),
      ],
    );
  }

  Widget _buildNumberField(TextEditingController controller, String suffix) {
    return TextFormField(
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      style: const TextStyle(color: Colors.black),
      decoration: InputDecoration(
        filled: true,
        fillColor: Colors.white,
        suffixText: suffix,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(25),
          borderSide: BorderSide.none,
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
      ),
    );
  }

  Widget _buildGenderOption(String gender, IconData icon) {
    bool isSelected = _userData.sexo == gender;
    return GestureDetector(
      onTap: () {
        setState(() {
          _userData.sexo = gender;
        });
      },
      child: Container(
        width: 80,
        height: 80,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(
            color: isSelected ? const Color(0xFF00BCD4) : Colors.grey,
            width: 3,
          ),
        ),
        child: CircleAvatar(
          radius: 35,
          backgroundColor: Colors.grey[300],
          child: Icon(
            icon,
            size: 40,
            color: isSelected ? const Color(0xFF00BCD4) : Colors.grey[700],
          ),
        ),
      ),
    );
  }

  Widget _buildOptionButton(String text, bool isSelected, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 15),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF00BCD4) : Colors.white,
          borderRadius: BorderRadius.circular(25),
          border: Border.all(
            color: isSelected ? const Color(0xFF00BCD4) : Colors.grey,
          ),
        ),
        child: Text(
          text,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: isSelected ? Colors.white : Colors.black,
            fontSize: 16,
            fontWeight: FontWeight.w500,
          ),
        ),
      ),
    );
  }

  Widget _buildMetaButton(String text, bool isSelected, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 15),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF00BCD4) : Colors.white,
          borderRadius: BorderRadius.circular(25),
          border: Border.all(
            color: isSelected ? const Color(0xFF00BCD4) : Colors.grey,
          ),
        ),
        child: Text(
          text,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: isSelected ? Colors.white : Colors.black,
            fontSize: 16,
            fontWeight: FontWeight.w500,
          ),
        ),
      ),
    );
  }

  Widget _buildAreaChip(String area) {
    bool isSelected = _userData.areasDesejadas.contains(area);
    return GestureDetector(
      onTap: () {
        setState(() {
          if (isSelected) {
            _userData.areasDesejadas.remove(area);
          } else {
            _userData.areasDesejadas.add(area);
          }
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF00BCD4) : Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? const Color(0xFF00BCD4) : Colors.grey,
          ),
        ),
        child: Text(
          area,
          style: TextStyle(
            color: isSelected ? Colors.white : Colors.black,
            fontSize: 14,
          ),
        ),
      ),
    );
  }

  Widget _buildTreinoChip(String treino) {
    bool isSelected = _userData.tiposTreino.contains(treino);
    return GestureDetector(
      onTap: () {
        setState(() {
          if (isSelected) {
            _userData.tiposTreino.remove(treino);
          } else {
            _userData.tiposTreino.add(treino);
          }
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF00BCD4) : Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? const Color(0xFF00BCD4) : Colors.grey,
          ),
        ),
        child: Text(
          treino,
          style: TextStyle(
            color: isSelected ? Colors.white : Colors.black,
            fontSize: 12,
          ),
        ),
      ),
    );
  }

  Widget _buildEquipamentoOption(String equipamento) {
    bool isSelected = _userData.equipamentos == equipamento;
    return GestureDetector(
      onTap: () {
        setState(() {
          _userData.equipamentos = equipamento;
        });
      },
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF00BCD4) : Colors.white,
          borderRadius: BorderRadius.circular(15),
          border: Border.all(
            color: isSelected ? const Color(0xFF00BCD4) : Colors.grey,
          ),
        ),
        child: Text(
          equipamento,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: isSelected ? Colors.white : Colors.black,
            fontSize: 14,
          ),
        ),
      ),
    );
  }

  Widget _buildTempoOption(String tempo) {
    bool isSelected = _userData.tempoDisponivel == tempo;
    return GestureDetector(
      onTap: () {
        setState(() {
          _userData.tempoDisponivel = tempo;
        });
      },
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF00BCD4) : Colors.white,
          borderRadius: BorderRadius.circular(15),
          border: Border.all(
            color: isSelected ? const Color(0xFF00BCD4) : Colors.grey,
          ),
        ),
        child: Text(
          tempo,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: isSelected ? Colors.white : Colors.black,
            fontSize: 14,
          ),
        ),
      ),
    );
  }

  void _nextPage() {
    if (_validateCurrentStep()) {
      if (_currentPage < 6) {
        _pageController.nextPage(
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeInOut,
        );
      }
    } else {
      _showErrorMessage('Por favor, preencha todos os campos obrigatórios');
    }
  }

  void _previousPage() {
    if (_currentPage > 0) {
      _pageController.previousPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    }
  }

  Widget _buildNavigationButtons() {
    return Padding(
      padding: const EdgeInsets.all(20.0),
      child: Row(
        children: [
          if (_currentPage > 0)
            Expanded(
              child: ElevatedButton(
                onPressed: _isLoading ? null : _previousPage,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.grey[700],
                  padding: const EdgeInsets.symmetric(vertical: 15),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(25),
                  ),
                ),
                child: const Text(
                  'Voltar',
                  style: TextStyle(color: Colors.white),
                ),
              ),
            ),
          if (_currentPage > 0) const SizedBox(width: 15),
          Expanded(
            child: ElevatedButton(
              onPressed: _isLoading ? null : (_currentPage == 7 ? _finishRegistration : _nextPage),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF00BCD4),
                padding: const EdgeInsets.symmetric(vertical: 15),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(25),
                ),
              ),
              child: _isLoading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    )
                  : Text(
                      _currentPage == 7 ? 'Finalizar' : 'Continuar',
                      style: const TextStyle(color: Colors.white, fontSize: 16),
                    ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _pageController.dispose();
    _nomeController.dispose();
    _emailController.dispose();
    _senhaController.dispose();
    _idadeController.dispose();
    _pesoAtualController.dispose();
    _pesoDesejadoController.dispose();
    _alturaController.dispose();
    super.dispose();
  }
}