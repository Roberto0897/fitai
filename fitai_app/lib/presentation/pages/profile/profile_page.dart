import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/router/app_router.dart';
import 'package:flutter_svg/flutter_svg.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({Key? key}) : super(key: key);

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  // Dados do usuário (substituir por dados reais do Firebase/Provider)
  double pesoAtual = 80.0;
  double pesoDesejado = 75.0;
  double altura = 175.0;
  String nome = "João Silva";
  String email = "joao.silva@email.com";
  int idade = 28;
  String genero = "Masculino";
  String objetivo = "Perder peso";
  String nivelAtividade = "Moderado";
  String preferenciaTreino = "Musculação, Cardio";

  // Calcula IMC
  double get imc => pesoAtual / ((altura / 100) * (altura / 100));

  String get imcCategoria {
    if (imc < 18.5) return "Abaixo do peso";
    if (imc < 25) return "Peso normal";
    if (imc < 30) return "Sobrepeso";
    return "Obesidade";
  }

  Color get imcColor {
    if (imc < 18.5) return Colors.blue;
    if (imc < 25) return const Color(0xFF00BCD4);
    if (imc < 30) return Colors.orange;
    return Colors.red;
  }

  // Dialogs de edição
  void _showEditMetricsDialog() {
    final pesoController = TextEditingController(text: pesoAtual.toString());
    final pesoDesejaController = TextEditingController(text: pesoDesejado.toString());
    final alturaController = TextEditingController(text: altura.toString());

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF2A2A2A),
        title: Text(
          'Atualizar Métricas',
          style: GoogleFonts.jockeyOne(color: Colors.white),
        ),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: pesoController,
                keyboardType: TextInputType.number,
                style: const TextStyle(color: Colors.white),
                decoration: const InputDecoration(
                  labelText: 'Peso Atual (kg)',
                  labelStyle: TextStyle(color: Color(0xFF9E9E9E)),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Color(0xFF00BCD4)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Color(0xFF00BCD4), width: 2),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: pesoDesejaController,
                keyboardType: TextInputType.number,
                style: const TextStyle(color: Colors.white),
                decoration: const InputDecoration(
                  labelText: 'Peso Desejado (kg)',
                  labelStyle: TextStyle(color: Color(0xFF9E9E9E)),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Color(0xFF00BCD4)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Color(0xFF00BCD4), width: 2),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: alturaController,
                keyboardType: TextInputType.number,
                style: const TextStyle(color: Colors.white),
                decoration: const InputDecoration(
                  labelText: 'Altura (cm)',
                  labelStyle: TextStyle(color: Color(0xFF9E9E9E)),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Color(0xFF00BCD4)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Color(0xFF00BCD4), width: 2),
                  ),
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar', style: TextStyle(color: Color(0xFF9E9E9E))),
          ),
          ElevatedButton(
            onPressed: () {
              setState(() {
                pesoAtual = double.tryParse(pesoController.text) ?? pesoAtual;
                pesoDesejado = double.tryParse(pesoDesejaController.text) ?? pesoDesejado;
                altura = double.tryParse(alturaController.text) ?? altura;
              });
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Métricas atualizadas!')),
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF00BCD4),
            ),
            child: const Text('Salvar'),
          ),
        ],
      ),
    );
  }

  void _showEditDialog(String title, String currentValue, Function(String) onSave) {
    final controller = TextEditingController(text: currentValue);

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF2A2A2A),
        title: Text(
          'Editar $title',
          style: GoogleFonts.jockeyOne(color: Colors.white),
        ),
        content: TextField(
          controller: controller,
          style: const TextStyle(color: Colors.white),
          decoration: InputDecoration(
            labelText: title,
            labelStyle: const TextStyle(color: Color(0xFF9E9E9E)),
            enabledBorder: const OutlineInputBorder(
              borderSide: BorderSide(color: Color(0xFF00BCD4)),
            ),
            focusedBorder: const OutlineInputBorder(
              borderSide: BorderSide(color: Color(0xFF00BCD4), width: 2),
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar', style: TextStyle(color: Color(0xFF9E9E9E))),
          ),
          ElevatedButton(
            onPressed: () {
              onSave(controller.text);
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('$title atualizado!')),
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF00BCD4),
            ),
            child: const Text('Salvar'),
          ),
        ],
      ),
    );
  }

  void _showSelectDialog(String title, List<String> options, String currentValue, Function(String) onSelect) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF2A2A2A),
        title: Text(
          'Selecionar $title',
          style: GoogleFonts.jockeyOne(color: Colors.white),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: options.map((option) {
            return ListTile(
              title: Text(
                option,
                style: TextStyle(
                  color: option == currentValue ? const Color(0xFF00BCD4) : Colors.white,
                ),
              ),
              leading: Radio<String>(
                value: option,
                groupValue: currentValue,
                activeColor: const Color(0xFF00BCD4),
                onChanged: (value) {
                  if (value != null) {
                    onSelect(value);
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('$title atualizado!')),
                    );
                  }
                },
              ),
            );
          }).toList(),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Fechar', style: TextStyle(color: Color(0xFF9E9E9E))),
          ),
        ],
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
            Expanded(
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildHeader(),
                    const SizedBox(height: 24),
                    _buildProfileHeader(),
                    const SizedBox(height: 32),
                    _buildBodyMetrics(),
                    const SizedBox(height: 24),
                    _buildPersonalInfo(),
                    const SizedBox(height: 24),
                    _buildGoalsSection(),
                    const SizedBox(height: 24),
                    _buildSettingsSection(),
                    const SizedBox(height: 24),
                    _buildAISettings(),
                    const SizedBox(height: 24),
                    _buildAccountManagement(),
                    const SizedBox(height: 100),
                  ],
                ),
              ),
            ),
            _buildBottomNavigation(),
          ],
        ),
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
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(24),
                ),
                child: SvgPicture.asset(
                  "assets/images/iconeFitai.svg",
                  width: 30,
                  height: 30,
                ),
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

  Widget _buildProfileHeader() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        children: [
          Stack(
            children: [
              CircleAvatar(
                radius: 60,
                backgroundColor: const Color(0xFF2A2A2A),
                child: Icon(
                  Icons.person,
                  size: 60,
                  color: const Color(0xFF00BCD4),
                ),
              ),
              Positioned(
                bottom: 0,
                right: 0,
                child: Container(
                  decoration: BoxDecoration(
                    color: const Color(0xFF00BCD4),
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: const Color(0xFF1A1A1A),
                      width: 3,
                    ),
                  ),
                  child: IconButton(
                    icon: const Icon(Icons.camera_alt, size: 20),
                    color: Colors.white,
                    onPressed: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Upload de foto em desenvolvimento')),
                      );
                    },
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            nome,
            style: GoogleFonts.jockeyOne(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            email,
            style: const TextStyle(
              color: Color(0xFF9E9E9E),
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBodyMetrics() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Métricas Corporais',
            style: GoogleFonts.jockeyOne(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: const Color(0xFF2A2A2A),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: const Color(0xFF00BCD4),
                width: 1.5,
              ),
            ),
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: _buildMetricItem(
                        'Peso Atual',
                        '${pesoAtual.toStringAsFixed(1)} kg',
                        Icons.monitor_weight,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: _buildMetricItem(
                        'Peso Desejado',
                        '${pesoDesejado.toStringAsFixed(1)} kg',
                        Icons.flag,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                const Divider(color: Color(0xFF404040)),
                const SizedBox(height: 20),
                Row(
                  children: [
                    Expanded(
                      child: _buildMetricItem(
                        'Altura',
                        '${altura.toStringAsFixed(0)} cm',
                        Icons.height,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(
                                Icons.analytics,
                                color: imcColor,
                                size: 20,
                              ),
                              const SizedBox(width: 8),
                              Text(
                                'IMC',
                                style: const TextStyle(
                                  color: Color(0xFF9E9E9E),
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Text(
                            imc.toStringAsFixed(1),
                            style: TextStyle(
                              color: imcColor,
                              fontSize: 24,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            imcCategoria,
                            style: TextStyle(
                              color: imcColor,
                              fontSize: 11,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                ElevatedButton(
                  onPressed: _showEditMetricsDialog,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF00BCD4),
                    foregroundColor: Colors.white,
                    minimumSize: const Size(double.infinity, 45),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: const Text('Atualizar Métricas'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricItem(String label, String value, IconData icon) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(
              icon,
              color: const Color(0xFF00BCD4),
              size: 20,
            ),
            const SizedBox(width: 8),
            Text(
              label,
              style: const TextStyle(
                color: Color(0xFF9E9E9E),
                fontSize: 12,
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 24,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }

  Widget _buildPersonalInfo() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Informações Pessoais',
            style: GoogleFonts.jockeyOne(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 16),
          _buildEditableInfoCard('Nome Completo', nome, Icons.person_outline, () {
            _showEditDialog('Nome', nome, (value) {
              setState(() => nome = value);
            });
          }),
          const SizedBox(height: 12),
          _buildEditableInfoCard('Email', email, Icons.email_outlined, () {
            _showEditDialog('Email', email, (value) {
              setState(() => email = value);
            });
          }),
          const SizedBox(height: 12),
          _buildEditableInfoCard('Idade', '$idade anos', Icons.cake_outlined, () {
            _showEditDialog('Idade', idade.toString(), (value) {
              setState(() => idade = int.tryParse(value) ?? idade);
            });
          }),
          const SizedBox(height: 12),
          _buildEditableInfoCard('Gênero', genero, Icons.wc, () {
            _showSelectDialog('Gênero', ['Masculino', 'Feminino', 'Outro', 'Prefiro não informar'], genero, (value) {
              setState(() => genero = value);
            });
          }),
        ],
      ),
    );
  }

  Widget _buildGoalsSection() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Objetivos e Metas',
            style: GoogleFonts.jockeyOne(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 16),
          _buildEditableInfoCard('Objetivo Principal', objetivo, Icons.track_changes, () {
            _showSelectDialog('Objetivo', ['Perder peso', 'Ganhar massa', 'Manter forma', 'Definição'], objetivo, (value) {
              setState(() => objetivo = value);
            });
          }),
          const SizedBox(height: 12),
          _buildEditableInfoCard('Nível de Atividade', nivelAtividade, Icons.directions_run, () {
            _showSelectDialog('Nível de Atividade', ['Sedentário', 'Leve', 'Moderado', 'Intenso'], nivelAtividade, (value) {
              setState(() => nivelAtividade = value);
            });
          }),
          const SizedBox(height: 12),
          _buildEditableInfoCard('Preferências de Treino', preferenciaTreino, Icons.fitness_center, () {
            _showEditDialog('Preferências', preferenciaTreino, (value) {
              setState(() => preferenciaTreino = value);
            });
          }),
        ],
      ),
    );
  }

  Widget _buildSettingsSection() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Configurações',
            style: GoogleFonts.jockeyOne(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 16),
          _buildSettingItem('Notificações', Icons.notifications_outlined, () {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Configurações de notificações em desenvolvimento')),
            );
          }),
          _buildSettingItem('Unidades de Medida', Icons.straighten, () {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Configurações de unidades em desenvolvimento')),
            );
          }),
          _buildSettingItem('Idioma', Icons.language, () {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Configurações de idioma em desenvolvimento')),
            );
          }),
          _buildSettingItem('Tema', Icons.palette_outlined, () {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Configurações de tema em desenvolvimento')),
            );
          }),
        ],
      ),
    );
  }

  Widget _buildAISettings() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Configurações de IA',
            style: GoogleFonts.jockeyOne(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 16),
          _buildSettingItem('Preferências de Personalização', Icons.tune, () {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Configurações de IA em desenvolvimento')),
            );
          }),
          _buildSettingItem('Tom das Respostas', Icons.psychology, () {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Configurações de IA em desenvolvimento')),
            );
          }),
          _buildSettingItem('Histórico de Conversas', Icons.history, () {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Histórico em desenvolvimento')),
            );
          }),
        ],
      ),
    );
  }

  Widget _buildAccountManagement() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Gestão de Conta',
            style: GoogleFonts.jockeyOne(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 16),
          _buildSettingItem('Alterar Senha', Icons.lock_outline, () {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Alteração de senha em desenvolvimento')),
            );
          }),
          _buildSettingItem('Plano e Assinatura', Icons.card_membership, () {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Gerenciamento de planos em desenvolvimento')),
            );
          }),
          _buildSettingItem('Privacidade', Icons.privacy_tip_outlined, () {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Configurações de privacidade em desenvolvimento')),
            );
          }),
          const SizedBox(height: 12),
          _buildDangerButton('Sair da Conta', Icons.logout, () {
            AppRouter.logout();
          }),
          const SizedBox(height: 8),
          _buildDangerButton('Deletar Conta', Icons.delete_forever, () {
            _showDeleteAccountDialog();
          }, isDelete: true),
        ],
      ),
    );
  }

  void _showDeleteAccountDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF2A2A2A),
        title: Text(
          'Deletar Conta',
          style: GoogleFonts.jockeyOne(color: Colors.red),
        ),
        content: const Text(
          'Tem certeza que deseja deletar sua conta? Esta ação é irreversível e todos os seus dados serão perdidos.',
          style: TextStyle(color: Colors.white),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar', style: TextStyle(color: Color(0xFF9E9E9E))),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Deleção de conta em desenvolvimento')),
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
            ),
            child: const Text('Deletar'),
          ),
        ],
      ),
    );
  }

  Widget _buildEditableInfoCard(String label, String value, IconData icon, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF2A2A2A),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: const Color(0xFF404040),
            width: 1,
          ),
        ),
        child: Row(
          children: [
            Icon(icon, color: const Color(0xFF00BCD4), size: 24),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: const TextStyle(
                      color: Color(0xFF9E9E9E),
                      fontSize: 12,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    value,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
            const Icon(
              Icons.edit,
              color: Color(0xFF00BCD4),
              size: 20,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSettingItem(String title, IconData icon, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 16),
        decoration: const BoxDecoration(
          border: Border(
            bottom: BorderSide(
              color: Color(0xFF404040),
              width: 1,
            ),
          ),
        ),
        child: Row(
          children: [
            Icon(icon, color: const Color(0xFF00BCD4), size: 24),
            const SizedBox(width: 16),
            Expanded(
              child: Text(
                title,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                ),
              ),
            ),
            const Icon(
              Icons.chevron_right,
              color: Color(0xFF9E9E9E),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDangerButton(String title, IconData icon, VoidCallback onTap, {bool isDelete = false}) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF2A2A2A),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isDelete ? Colors.red : Colors.orange,
            width: 1.5,
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              color: isDelete ? Colors.red : Colors.orange,
              size: 24,
            ),
            const SizedBox(width: 12),
            Text(
              title,
              style: TextStyle(
                color: isDelete ? Colors.red : Colors.orange,
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }

    Widget _buildBottomNavigation() {
    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFF2A2A2A),
        border: Border(
          top: BorderSide(
            color: Color(0xFF424242),
            width: 1,
          ),
        ),
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 12),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildNavItem('Inicio', Icons.home, true),
              _buildNavItem('Treinos', Icons.fitness_center, false),
              _buildNavItem('Relatórios', Icons.bar_chart, false),
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
      } else if (label == 'Relatórios') {
        AppRouter.goToReports(); // ← ADICIONE ESTA LINHA
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