// user_model.dart


class UserRegistrationData {
  String nome;
  String email;
  String senha;
  int idade;
  String sexo;
  List<String> metas;
  String nivelAtividade;
  List<String> areasDesejadas;
  double pesoAtual;
  double pesoDesejado;
  double altura;
  List<String> tiposTreino;
  String equipamentos;
  String tempoDisponivel;
  bool malaFlexibilidade;
  DateTime createdAt;

  // Construtor com valores padrão
  UserRegistrationData({
    this.nome = '',
    this.email = '',
    this.senha = '',
    this.idade = 0,
    this.sexo = '',
    List<String>? metas,
    this.nivelAtividade = '',
    List<String>? areasDesejadas,
    this.pesoAtual = 0.0,
    this.pesoDesejado = 0.0,
    this.altura = 0.0,
    List<String>? tiposTreino,
    this.equipamentos = '',
    this.tempoDisponivel = '',
    this.malaFlexibilidade = false,
    DateTime? createdAt,
  }) : 
    metas = metas ?? [],
    areasDesejadas = areasDesejadas ?? [],
    tiposTreino = tiposTreino ?? [],
    createdAt = createdAt ?? DateTime.now();

  // Método para calcular IMC
  double calcularIMC() {
    if (altura > 0 && pesoAtual > 0) {
      double alturaM = altura / 100; // converter cm para metros
      return pesoAtual / (alturaM * alturaM);
    }
    return 0.0;
  }

  String getIMCStatus() {
    double imc = calcularIMC();
    if (imc == 0) return 'Não calculado';
    if (imc < 18.5) return 'Abaixo do peso';
    if (imc < 25) return 'Peso normal';
    if (imc < 30) return 'Sobrepeso';
    return 'Obesidade';
  }

  // Validações
  bool validarDadosBasicos() {
    return nome.isNotEmpty && 
           email.isNotEmpty && 
           senha.isNotEmpty && 
           idade > 0 && 
           sexo.isNotEmpty;
  }

  bool validarEmail() {
    return RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(email);
  }

  bool validarMetas() {
    return metas.isNotEmpty;
  }

  bool validarDadosFisicos() {
    return pesoAtual > 0 && pesoDesejado > 0 && altura > 0;
  }
  Map<String, dynamic> toMap() {
    return {
      'nome': nome,
      'email': email,
      'idade': idade,
      'sexo': sexo,
      'peso_atual': pesoAtual,
      'peso_desejado': pesoDesejado,
      'altura': altura,
      'metas': metas,
      'nivel_atividade': nivelAtividade,
      'areas_desejadas': areasDesejadas,
      'tipos_treino': tiposTreino,
      'equipamentos': equipamentos,
      'tempo_disponivel': tempoDisponivel,
      'mala_flexibilidade': malaFlexibilidade,
    };
  }

  // ✅ NOVO: Conversão específica para Firebase (sem senha)
  Map<String, dynamic> toFirebaseMap() {
    return {
      'nome': nome,
      'email': email,
      'idade': idade,
      'sexo': sexo,
      'peso_atual': pesoAtual,
      'peso_desejado': pesoDesejado,
      'altura': altura,
      'imc': calcularIMC(),
      'imc_status': getIMCStatus(),
      'metas': metas,
      'nivel_atividade': nivelAtividade,
      'areas_desejadas': areasDesejadas,
      'tipos_treino': tiposTreino,
      'equipamentos': equipamentos,
      'tempo_disponivel': tempoDisponivel,
      'mala_flexibilidade': malaFlexibilidade,
      'created_at': createdAt.toIso8601String(),
    };
  }
  // Conversão para JSON (para salvar dados)
  Map<String, dynamic> toJson() {
    return {
      'nome': nome,
      'email': email,
      'senha': senha, // Em produção, criptografar antes de salvar
      'idade': idade,
      'sexo': sexo,
      'metas': metas,
      'nivelAtividade': nivelAtividade,
      'areasDesejadas': areasDesejadas,
      'pesoAtual': pesoAtual,
      'pesoDesejado': pesoDesejado,
      'altura': altura,
      'imc': calcularIMC(),
      'imcStatus': getIMCStatus(),
      'tiposTreino': tiposTreino,
      'equipamentos': equipamentos,
      'tempoDisponivel': tempoDisponivel,
      'malaFlexibilidade': malaFlexibilidade,
      'createdAt': createdAt.toIso8601String(),
    };
  }

  // Conversão do JSON (para carregar dados salvos)
  factory UserRegistrationData.fromJson(Map<String, dynamic> json) {
    return UserRegistrationData(
      nome: json['nome'] ?? '',
      email: json['email'] ?? '',
      senha: json['senha'] ?? '',
      idade: json['idade'] ?? 0,
      sexo: json['sexo'] ?? '',
      metas: List<String>.from(json['metas'] ?? []),
      nivelAtividade: json['nivelAtividade'] ?? '',
      areasDesejadas: List<String>.from(json['areasDesejadas'] ?? []),
      pesoAtual: (json['pesoAtual'] ?? 0.0).toDouble(),
      pesoDesejado: (json['pesoDesejado'] ?? 0.0).toDouble(),
      altura: (json['altura'] ?? 0.0).toDouble(),
      tiposTreino: List<String>.from(json['tiposTreino'] ?? []),
      equipamentos: json['equipamentos'] ?? '',
      tempoDisponivel: json['tempoDisponivel'] ?? '',
      malaFlexibilidade: json['malaFlexibilidade'] ?? false,
      createdAt: json['createdAt'] != null 
          ? DateTime.parse(json['createdAt']) 
          : DateTime.now(),
    );
  }

  // Método para criar cópia do objeto
  UserRegistrationData copyWith({
    String? nome,
    String? email,
    String? senha,
    int? idade,
    String? sexo,
    List<String>? metas,
    String? nivelAtividade,
    List<String>? areasDesejadas,
    double? pesoAtual,
    double? pesoDesejado,
    double? altura,
    List<String>? tiposTreino,
    String? equipamentos,
    String? tempoDisponivel,
    bool? malaFlexibilidade,

    
  }) {
    return UserRegistrationData(
      nome: nome ?? this.nome,
      email: email ?? this.email,
      senha: senha ?? this.senha,
      idade: idade ?? this.idade,
      sexo: sexo ?? this.sexo,
      metas: metas ?? List.from(this.metas),
      nivelAtividade: nivelAtividade ?? this.nivelAtividade,
      areasDesejadas: areasDesejadas ?? List.from(this.areasDesejadas),
      pesoAtual: pesoAtual ?? this.pesoAtual,
      pesoDesejado: pesoDesejado ?? this.pesoDesejado,
      altura: altura ?? this.altura,
      tiposTreino: tiposTreino ?? List.from(this.tiposTreino),
      equipamentos: equipamentos ?? this.equipamentos,
      tempoDisponivel: tempoDisponivel ?? this.tempoDisponivel,
      malaFlexibilidade: malaFlexibilidade ?? this.malaFlexibilidade,
      createdAt: this.createdAt,
    );
    
  }

  @override
  String toString() {
    return 'UserRegistrationData(nome: $nome, email: $email, idade: $idade, imc: ${calcularIMC().toStringAsFixed(2)})';
  }
}