import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/router/app_router.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:flutter/foundation.dart';
// Import do UserService atualizado
import '../../service/user_service.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isPasswordVisible = false;
  bool _isLoading = false;
  bool _isGoogleLoading = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    
    // Para web, tenta login silencioso primeiro
    if (kIsWeb) {
      _trySignInSilently();
    }
  }

  Future<void> _trySignInSilently() async {
    try {
      if (await UserService.canSignInGoogleSilently()) {
        final userData = await UserService.signInWithGoogle();
        if (userData != null && mounted) {
          _showSuccessMessage('Login automático realizado!');
          // O AuthRouter vai detectar a mudança e redirecionar automaticamente
        }
      }
    } catch (e) {
      // Ignore erros do login silencioso
      debugPrint('Login silencioso falhou: $e');
    }
  }

  void _togglePasswordVisibility() {
    setState(() {
      _isPasswordVisible = !_isPasswordVisible;
    });
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    try {
      // Usar UserService em vez de Firebase diretamente
      final userData = await UserService.loginUser(
        _emailController.text.trim(),
        _passwordController.text.trim(),
      );

      if (userData != null) {
        debugPrint('Login realizado com sucesso! User: ${userData.email}');
        
        if (mounted) {
          _showSuccessMessage('Login realizado com sucesso!');
          AppRouter.goToDashboard();
        }
      } else {
        if (mounted) {
          _showErrorMessage('Credenciais inválidas. Verifique email e senha.');
        }
      }
    } on FirebaseAuthException catch (e) {
      String errorMessage;
      if (e.code == 'user-not-found') {
        errorMessage = 'Nenhum usuário encontrado para este email.';
      } else if (e.code == 'wrong-password') {
        errorMessage = 'Senha incorreta. Por favor, tente novamente.';
      } else {
        errorMessage = 'Erro no login. Verifique suas credenciais.';
      }
      
      debugPrint('Erro no login: ${e.code}');
      if (mounted) {
        _showErrorMessage(errorMessage);
      }
    } catch (e) {
      debugPrint('Erro inesperado no login: $e');
      if (mounted) {
        _showErrorMessage('Ocorreu um erro inesperado. Tente novamente.');
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  // Google Sign-In - Método corrigido usando UserService
  Future<void> _handleGoogleLogin() async {
    setState(() => _isGoogleLoading = true);

    try {
      final userData = await UserService.signInWithGoogle();
      
      if (userData != null) {
        debugPrint('Login Google bem-sucedido: ${userData.email}');
        
        if (mounted) {
          _showSuccessMessage('Login com Google realizado com sucesso!');
          // O AuthRouter vai detectar a mudança e redirecionar automaticamente
        }
      } else {
        if (mounted) {
          _showErrorMessage('Login cancelado pelo usuário.');
        }
      }
      
    } catch (error) {
      debugPrint('Erro Google Login: $error');
      
      String errorMessage = _getGoogleErrorMessage(error.toString());
      
      if (mounted) {
        _showErrorMessage(errorMessage);
      }
    } finally {
      if (mounted) {
        setState(() => _isGoogleLoading = false);
      }
    }
  }

  String _getGoogleErrorMessage(String error) {
    if (error.contains('popup_closed')) {
      return 'Popup fechado. Tente novamente e mantenha a janela aberta.';
    } else if (error.contains('popup_blocked')) {
      return 'Popup bloqueado. Permita popups para este site.';
    } else if (error.contains('unknown_reason')) {
      return 'Erro na autenticação. Aguarde alguns minutos e tente novamente.';
    } else if (error.contains('network')) {
      return 'Erro de conexão. Verifique sua internet.';
    } else if (error.contains('invalid_client')) {
      return 'Configuração incorreta. Entre em contato com o suporte.';
    } else if (error.contains('access_denied')) {
      return 'Acesso negado pelo Google.';
    }
    
    return 'Erro no login com Google. Tente novamente em alguns minutos.';
  }

  void _showSuccessMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.check_circle_outline, color: Colors.white),
            const SizedBox(width: 8),
            Expanded(child: Text(message)),
          ],
        ),
        backgroundColor: Colors.green.shade600,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  void _showErrorMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.error_outline, color: Colors.white),
            const SizedBox(width: 8),
            Expanded(child: Text(message)),
          ],
        ),
        backgroundColor: Colors.red.shade600,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        duration: const Duration(seconds: 4),
      ),
    );
  }

  void _navigateToRegister() {
    if (_isLoading || _isGoogleLoading) return;
    AppRouter.goToRegister();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1A1A1A),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32.0),
          child: Form(
            key: _formKey,
            child: Column(
              children: [
                const SizedBox(height: 80),
                _buildHeader(),
                const SizedBox(height: 60),
                _buildInputFields(),
                const SizedBox(height: 12),
                _buildForgotPasswordLink(),
                const SizedBox(height: 40),
                _buildLoginButton(),
                const SizedBox(height: 30),
                _buildDivider(),
                const SizedBox(height: 30),
                _buildGoogleButton(),
                // Aviso para Web se necessário
                if (kIsWeb) ...[
                  const SizedBox(height: 12),
                  const Text(
                    'Permita popups para este site para usar Google Sign-In',
                    style: TextStyle(
                      fontSize: 12,
                      color: Color(0xFF666666),
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
                const Spacer(),
                _buildRegisterLink(),
                const SizedBox(height: 40),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Column(
      children: [
        // Logo FITAI com ícone + título lado a lado
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [ 
            Container(
              width: 90,
              height: 90,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(24),
              ),
              child: SvgPicture.asset(
                "assets/images/iconeFitai.svg",
                width: 48,
                height: 48,
              ),
            ),
            const SizedBox(width: 16), // Espaço entre logo e texto
            
            // Título FITAI
            Text(
              'FitAI',
              style: GoogleFonts.jockeyOne(
                fontSize: 60,
                fontWeight: FontWeight.bold,
                color: const Color(0xFF00BCD4), // Cor ciano
                letterSpacing: 1,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        
        // Subtítulo
        const Column(
          children: [
            Text(
              'Entre no FitAI',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w500,
                color: Colors.white,
              ),
            ),
            SizedBox(height: 4),
            Text(
              'Seu personal trainer inteligente',
              style: TextStyle(
                fontSize: 14,
                color: Color(0xFF888888),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildInputFields() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Campo Email
        const Text(
          'Email:',
          style: TextStyle(
            color: Colors.white,
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 8),
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(25),
          ),
          child: TextFormField(
            controller: _emailController,
            enabled: !_isLoading && !_isGoogleLoading,
            keyboardType: TextInputType.emailAddress,
            textInputAction: TextInputAction.next,
            decoration: const InputDecoration(
              hintText: 'Digite seu email',
              hintStyle: TextStyle(color: Color(0xFF888888)),
              border: InputBorder.none,
              contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            ),
            style: const TextStyle(color: Colors.black),
            validator: (value) {
              if (value == null || value.trim().isEmpty) {
                return 'Email é obrigatório';
              }
              if (!RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(value)) {
                return 'Email inválido';
              }
              return null;
            },
          ),
        ),
        
        const SizedBox(height: 24),
        
        // Campo Senha
        const Text(
          'Senha:',
          style: TextStyle(
            color: Colors.white,
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 8),
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(25),
          ),
          child: TextFormField(
            controller: _passwordController,
            enabled: !_isLoading && !_isGoogleLoading,
            obscureText: !_isPasswordVisible,
            textInputAction: TextInputAction.done,
            onFieldSubmitted: (_) => _handleLogin(),
            decoration: InputDecoration(
              hintText: 'Digite sua senha',
              hintStyle: const TextStyle(color: Color(0xFF888888)),
              border: InputBorder.none,
              contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              suffixIcon: IconButton(
                icon: Icon(
                  _isPasswordVisible ? Icons.visibility_off : Icons.visibility,
                  color: const Color(0xFF888888),
                ),
                onPressed: _togglePasswordVisibility,
              ),
            ),
            style: const TextStyle(color: Colors.black),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Senha é obrigatória';
              }
              if (value.length < 6) {
                return 'Senha deve ter pelo menos 6 caracteres';
              }
              return null;
            },
          ),
        ),
      ],
    );
  }

  Widget _buildForgotPasswordLink() {
    return Align(
      alignment: Alignment.centerLeft,
      child: TextButton(
        onPressed: (_isLoading || _isGoogleLoading) ? null : () {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Funcionalidade em desenvolvimento'),
              backgroundColor: Colors.orange,
              behavior: SnackBarBehavior.floating,
            ),
          );
        },
        style: TextButton.styleFrom(
          padding: EdgeInsets.zero,
        ),
        child: const Text(
          'Esqueceu sua senha?',
          style: TextStyle(
            color: Color(0xFF888888),
            fontSize: 12,
            decoration: TextDecoration.underline,
            decorationColor: Color(0xFF888888),
          ),
        ),
      ),
    );
  }

  Widget _buildLoginButton() {
    return SizedBox(
      width: double.infinity,
      height: 50,
      child: ElevatedButton(
        onPressed: (_isLoading || _isGoogleLoading) ? null : _handleLogin,
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF00BCD4),
          disabledBackgroundColor: const Color(0xFF666666),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(25),
          ),
          elevation: 0,
        ),
        child: _isLoading
            ? const SizedBox(
                height: 20,
                width: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : const Text(
                'Entrar',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                  fontSize: 16,
                ),
              ),
      ),
    );
  }

  Widget _buildDivider() {
    return const Row(
      children: [
        Expanded(
          child: Divider(
            color: Color(0xFF444444),
            thickness: 1,
          ),
        ),
        Padding(
          padding: EdgeInsets.symmetric(horizontal: 16),
          child: Text(
            'ou',
            style: TextStyle(
              color: Color(0xFF888888),
              fontSize: 14,
            ),
          ),
        ),
        Expanded(
          child: Divider(
            color: Color(0xFF444444),
            thickness: 1,
          ),
        ),
      ],
    );
  }

  Widget _buildGoogleButton() {
    return SizedBox(
      width: double.infinity,
      height: 50,
      child: ElevatedButton.icon(
        onPressed: (_isLoading || _isGoogleLoading) ? null : _handleGoogleLogin,
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.white,
          disabledBackgroundColor: const Color(0xFFEEEEEE),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(25),
          ),
          elevation: 0,
        ),
        icon: _isGoogleLoading 
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF666666)),
                ),
              )
            : const FaIcon(
                FontAwesomeIcons.google,
                color: Colors.black,
                size: 20,
              ),
        label: Text(
          _isGoogleLoading ? 'Entrando...' : 'Entrar com Google',
          style: TextStyle(
            color: _isGoogleLoading ? const Color(0xFF666666) : Colors.black,
            fontWeight: FontWeight.w500,
            fontSize: 14,
          ),
        ),
      ),
    );
  }

  Widget _buildRegisterLink() {
    return TextButton(
      onPressed: (_isLoading || _isGoogleLoading) ? null : _navigateToRegister,
      child: const Text(
        'Não tem conta ? Inscreva-se',
        style: TextStyle(
          color: Color(0xFF888888),
          fontSize: 14,
          decoration: TextDecoration.underline,
          decorationColor: Color(0xFF888888),
        ),
      ),
    );
  }
}