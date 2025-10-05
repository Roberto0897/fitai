/// ProfilePage adaptada para usar UserRegistrationData

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../../../core/router/app_router.dart';
import 'package:flutter_svg/flutter_svg.dart';
import '../../../providers/user_profile_provider.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({Key? key}) : super(key: key);

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<UserProfileProvider>().loadProfile();
    });
  }

  Color _getImcColor(double imc) {
    if (imc < 18.5) return Colors.blue;
    if (imc < 25) return const Color(0xFF00BCD4);
    if (imc < 30) return Colors.orange;
    return Colors.red;
  }

  void _showEditMetricsDialog(UserProfileProvider provider) {
    final pesoController = TextEditingController(text: provider.pesoAtual.toString());
    final pesoDesejaController = TextEditingController(text: provider.pesoDesejado.toString());
    final alturaController = TextEditingController(text: provider.altura.toString());

    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        backgroundColor: const Color(0xFF2A2A2A),
        title: Text('Atualizar Métricas', style: GoogleFonts.jockeyOne(color: Colors.white)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildTextField(pesoController, 'Peso Atual (kg)'),
              const SizedBox(height: 16),
              _buildTextField(pesoDesejaController, 'Peso Desejado (kg)'),
              const SizedBox(height: 16),
              _buildTextField(alturaController, 'Altura (cm)'),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancelar', style: TextStyle(color: Color(0xFF9E9E9E))),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(dialogContext);
              
              final success = await provider.updateMetrics(
                pesoAtual: double.tryParse(pesoController.text),
                pesoDesejado: double.tryParse(pesoDesejaController.text),
                altura: double.tryParse(alturaController.text),
              );
              
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(success ? 'Métricas atualizadas!' : 'Erro ao atualizar'),
                    backgroundColor: success ? Colors.green : Colors.red,
                  ),
                );
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF00BCD4)),
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
      builder: (dialogContext) => AlertDialog(
        backgroundColor: const Color(0xFF2A2A2A),
        title: Text('Editar $title', style: GoogleFonts.jockeyOne(color: Colors.white)),
        content: _buildTextField(controller, title),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancelar', style: TextStyle(color: Color(0xFF9E9E9E))),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(dialogContext);
              await onSave(controller.text);
              
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('$title atualizado!')),
                );
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF00BCD4)),
            child: const Text('Salvar'),
          ),
        ],
      ),
    );
  }

  void _showSelectDialog(String title, List<String> options, String currentValue, Function(String) onSelect) {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        backgroundColor: const Color(0xFF2A2A2A),
        title: Text('Selecionar $title', style: GoogleFonts.jockeyOne(color: Colors.white)),
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
                onChanged: (value) async {
                  if (value != null) {
                    Navigator.pop(dialogContext);
                    await onSelect(value);
                    
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('$title atualizado!')),
                      );
                    }
                  }
                },
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  void _showDeleteAccountDialog() {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        backgroundColor: const Color(0xFF2A2A2A),
        title: Text('Deletar Conta', style: GoogleFonts.jockeyOne(color: Colors.red)),
        content: const Text(
          'Tem certeza? Esta ação é irreversível.',
          style: TextStyle(color: Colors.white),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancelar', style: TextStyle(color: Color(0xFF9E9E9E))),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(dialogContext);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Deleção em desenvolvimento')),
              );
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Deletar'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1A1A1A),
      body: Consumer<UserProfileProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading && !provider.hasUserData) {
            return const Center(
              child: CircularProgressIndicator(color: Color(0xFF00BCD4)),
            );
          }

          if (!provider.hasUserData) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 80, color: Colors.red),
                  const SizedBox(height: 16),
                  const Text('Erro ao carregar perfil', style: TextStyle(color: Colors.white, fontSize: 18)),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: () => provider.loadProfile(),
                    child: const Text('Tentar Novamente'),
                  ),
                ],
              ),
            );
          }

          return SafeArea(
            child: RefreshIndicator(
              onRefresh: () => provider.refreshProfile(),
              color: const Color(0xFF00BCD4),
              child: Column(
                children: [
                  Expanded(
                    child: SingleChildScrollView(
                      physics: const AlwaysScrollableScrollPhysics(),
                      child: Column(
                        children: [
                          _buildHeader(),
                          const SizedBox(height: 24),
                          _buildProfileHeader(provider),
                          const SizedBox(height: 32),
                          _buildBodyMetrics(provider),
                          const SizedBox(height: 24),
                          _buildPersonalInfo(provider),
                          const SizedBox(height: 24),
                          _buildGoalsSection(provider),
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
        },
      ),
    );
  }

  Widget _buildTextField(TextEditingController controller, String label) {
    return TextField(
      controller: controller,
      keyboardType: TextInputType.number,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(color: Color(0xFF9E9E9E)),
        enabledBorder: const OutlineInputBorder(
          borderSide: BorderSide(color: Color(0xFF00BCD4)),
        ),
        focusedBorder: const OutlineInputBorder(
          borderSide: BorderSide(color: Color(0xFF00BCD4), width: 2),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.only(top: 40.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SvgPicture.asset("assets/images/iconeFitai.svg", width: 40, height: 40),
          const SizedBox(width: 16),
          Text('FitAI', style: GoogleFonts.jockeyOne(fontSize: 40, color: const Color(0xFF00BCD4))),
        ],
      ),
    );
  }

  Widget _buildProfileHeader(UserProfileProvider provider) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        children: [
          Stack(
            children: [
              CircleAvatar(
                radius: 60,
                backgroundColor: const Color(0xFF2A2A2A),
                child: const Icon(Icons.person, size: 60, color: Color(0xFF00BCD4)),
              ),
              Positioned(
                bottom: 0,
                right: 0,
                child: Container(
                  decoration: BoxDecoration(
                    color: const Color(0xFF00BCD4),
                    shape: BoxShape.circle,
                    border: Border.all(color: const Color(0xFF1A1A1A), width: 3),
                  ),
                  child: IconButton(
                    icon: const Icon(Icons.camera_alt, size: 20),
                    color: Colors.white,
                    onPressed: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Upload em desenvolvimento')),
                      );
                    },
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(provider.nome, style: GoogleFonts.jockeyOne(fontSize: 24, color: Colors.white)),
          const SizedBox(height: 4),
          Text(provider.email, style: const TextStyle(color: Color(0xFF9E9E9E), fontSize: 14)),
        ],
      ),
    );
  }

  Widget _buildBodyMetrics(UserProfileProvider provider) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Métricas Corporais', style: GoogleFonts.jockeyOne(color: Colors.white, fontSize: 20)),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: const Color(0xFF2A2A2A),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFF00BCD4), width: 1.5),
            ),
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(child: _buildMetricItem('Peso Atual', '${provider.pesoAtual.toStringAsFixed(1)} kg', Icons.monitor_weight)),
                    const SizedBox(width: 16),
                    Expanded(child: _buildMetricItem('Peso Desejado', '${provider.pesoDesejado.toStringAsFixed(1)} kg', Icons.flag)),
                  ],
                ),
                const SizedBox(height: 20),
                const Divider(color: Color(0xFF404040)),
                const SizedBox(height: 20),
                Row(
                  children: [
                    Expanded(child: _buildMetricItem('Altura', '${provider.altura.toStringAsFixed(0)} cm', Icons.height)),
                    const SizedBox(width: 16),
                    Expanded(child: _buildImcMetric(provider.imc, provider.imcCategoria)),
                  ],
                ),
                const SizedBox(height: 20),
                ElevatedButton(
                  onPressed: () => _showEditMetricsDialog(provider),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF00BCD4),
                    minimumSize: const Size(double.infinity, 45),
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
            Icon(icon, color: const Color(0xFF00BCD4), size: 20),
            const SizedBox(width: 8),
            Text(label, style: const TextStyle(color: Color(0xFF9E9E9E), fontSize: 12)),
          ],
        ),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
      ],
    );
  }

  Widget _buildImcMetric(double imc, String categoria) {
    final color = _getImcColor(imc);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(Icons.analytics, color: color, size: 20),
            const SizedBox(width: 8),
            const Text('IMC', style: TextStyle(color: Color(0xFF9E9E9E), fontSize: 12)),
          ],
        ),
        const SizedBox(height: 4),
        Text(imc.toStringAsFixed(1), style: TextStyle(color: color, fontSize: 24, fontWeight: FontWeight.bold)),
        Text(categoria, style: TextStyle(color: color, fontSize: 11)),
      ],
    );
  }

  Widget _buildPersonalInfo(UserProfileProvider provider) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Informações Pessoais', style: GoogleFonts.jockeyOne(color: Colors.white, fontSize: 20)),
          const SizedBox(height: 16),
          _buildEditableInfoCard('Nome Completo', provider.nome, Icons.person_outline, () {
            _showEditDialog('Nome', provider.nome, (value) async {
              await provider.updatePersonalInfo(nome: value);
            });
          }),
          const SizedBox(height: 12),
          _buildEditableInfoCard('Email', provider.email, Icons.email_outlined, () {
            _showEditDialog('Email', provider.email, (value) async {
              await provider.updatePersonalInfo(email: value);
            });
          }),
          const SizedBox(height: 12),
          _buildEditableInfoCard('Idade', '${provider.idade} anos', Icons.cake_outlined, () {
            _showEditDialog('Idade', provider.idade.toString(), (value) async {
              await provider.updatePersonalInfo(idade: int.tryParse(value));
            });
          }),
          const SizedBox(height: 12),
          _buildEditableInfoCard('Gênero', provider.genero, Icons.wc, () {
            _showSelectDialog('Gênero', ['Masculino', 'Feminino', 'Outro'], provider.genero, (value) async {
              await provider.updatePersonalInfo(sexo: value);
            });
          }),
        ],
      ),
    );
  }

  Widget _buildGoalsSection(UserProfileProvider provider) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Objetivos e Metas', style: GoogleFonts.jockeyOne(color: Colors.white, fontSize: 20)),
          const SizedBox(height: 16),
          _buildEditableInfoCard('Objetivo', provider.objetivo, Icons.track_changes, () {
            _showSelectDialog('Objetivo', ['Perder peso', 'Ganhar massa', 'Manter forma'], provider.objetivo, (value) async {
              await provider.updateGoals(objetivo: value);
            });
          }),
          const SizedBox(height: 12),
          _buildEditableInfoCard('Nível de Atividade', provider.nivelAtividade, Icons.directions_run, () {
            _showSelectDialog('Nível', ['Sedentário', 'Leve', 'Moderado', 'Intenso'], provider.nivelAtividade, (value) async {
              await provider.updateGoals(nivelAtividade: value);
            });
          }),
          const SizedBox(height: 12),
          _buildEditableInfoCard('Preferências', provider.preferenciaTreino, Icons.fitness_center, () {
            _showEditDialog('Preferências', provider.preferenciaTreino, (value) async {
              await provider.updateGoals(preferenciaTreino: value);
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
          Text('Configurações', style: GoogleFonts.jockeyOne(color: Colors.white, fontSize: 20)),
          const SizedBox(height: 16),
          _buildSettingItem('Notificações', Icons.notifications_outlined, () {}),
          _buildSettingItem('Unidades', Icons.straighten, () {}),
          _buildSettingItem('Idioma', Icons.language, () {}),
          _buildSettingItem('Tema', Icons.palette_outlined, () {}),
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
          Text('Configurações de IA', style: GoogleFonts.jockeyOne(color: Colors.white, fontSize: 20)),
          const SizedBox(height: 16),
          _buildSettingItem('Personalização', Icons.tune, () {}),
          _buildSettingItem('Tom das Respostas', Icons.psychology, () {}),
          _buildSettingItem('Histórico', Icons.history, () {}),
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
          Text('Gestão de Conta', style: GoogleFonts.jockeyOne(color: Colors.white, fontSize: 20)),
          const SizedBox(height: 16),
          _buildSettingItem('Alterar Senha', Icons.lock_outline, () {}),
          _buildSettingItem('Plano', Icons.card_membership, () {}),
          _buildSettingItem('Privacidade', Icons.privacy_tip_outlined, () {}),
          const SizedBox(height: 12),
          _buildDangerButton('Sair da Conta', Icons.logout, () => AppRouter.logout()),
          const SizedBox(height: 8),
          _buildDangerButton('Deletar Conta', Icons.delete_forever, _showDeleteAccountDialog, isDelete: true),
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
          border: Border.all(color: const Color(0xFF404040)),
        ),
        child: Row(
          children: [
            Icon(icon, color: const Color(0xFF00BCD4), size: 24),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label, style: const TextStyle(color: Color(0xFF9E9E9E), fontSize: 12)),
                  const SizedBox(height: 4),
                  Text(value, style: const TextStyle(color: Colors.white, fontSize: 16)),
                ],
              ),
            ),
            const Icon(Icons.edit, color: Color(0xFF00BCD4), size: 20),
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
          border: Border(bottom: BorderSide(color: Color(0xFF404040))),
        ),
        child: Row(
          children: [
            Icon(icon, color: const Color(0xFF00BCD4), size: 24),
            const SizedBox(width: 16),
            Expanded(child: Text(title, style: const TextStyle(color: Colors.white, fontSize: 16))),
            const Icon(Icons.chevron_right, color: Color(0xFF9E9E9E)),
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
          border: Border.all(color: isDelete ? Colors.red : Colors.orange, width: 1.5),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: isDelete ? Colors.red : Colors.orange, size: 24),
            const SizedBox(width: 12),
            Text(title, style: TextStyle(color: isDelete ? Colors.red : Colors.orange, fontSize: 16, fontWeight: FontWeight.w600)),
          ],
        ),
      ),
    );
  }

  Widget _buildBottomNavigation() {
    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFF2A2A2A),
        border: Border(top: BorderSide(color: Color(0xFF424242))),
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 12),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildNavItem('Inicio', Icons.home, false, AppRouter.goToDashboard),
              _buildNavItem('Treinos', Icons.fitness_center, false, AppRouter.goToWorkouts),
              _buildNavItem('Relatórios', Icons.bar_chart, false, AppRouter.goToReports),
              _buildNavItem('Chatbot', Icons.chat_bubble_outline, false, AppRouter.goToChatBot),
              _buildNavItem('Perfil', Icons.person, true, AppRouter.goToProfile),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(String label, IconData icon, bool isActive, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: isActive ? const Color(0xFF00BCD4) : const Color(0xFF9E9E9E), size: 24),
          const SizedBox(height: 4),
          Text(label, style: TextStyle(color: isActive ? const Color(0xFF00BCD4) : const Color(0xFF9E9E9E), fontSize: 10)),
        ],
      ),
    );
  }
}