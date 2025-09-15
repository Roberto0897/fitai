# 🏋️‍♂️ FitAI - Assistente Fitness Inteligente

> **Projeto de TCC:** Sistema de treinos personalizado com Inteligência Artificial  
> **Foco:** Algoritmos de recomendação e chatbot inteligente para fitness

[![Flutter](https://img.shields.io/badge/Flutter-02569B?style=for-the-badge&logo=flutter&logoColor=white)](https://flutter.dev/)
[![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)

---

## 🎯 Objetivo do Projeto

O **FitAI** é um assistente fitness inteligente que utiliza **algoritmos de Machine Learning** e **processamento de linguagem natural** para personalizar treinos e fornecer orientação fitness através de um chatbot especializado.

### Problema Resolvido
- **Falta de personalização** em apps de fitness convencionais
- **Dificuldade de aderência** a programas de exercícios
- **Ausência de orientação inteligente** em tempo real

### Solução Proposta
Sistema híbrido que combina:
- **Algoritmos de recomendação** baseados no perfil do usuário
- **Chatbot com IA** para orientação personalizada
- **Interface intuitiva** para acompanhamento de progresso

---

## 🚀 Status Atual

### ✅ Implementado
- **Backend Django completo** (55+ APIs REST)
- **Sistema de autenticação** com token-based security
- **Chatbot com OpenAI integration** + fallbacks inteligentes
- **Frontend Flutter** com dashboard e sistema de treinos
- **Design system** moderno e responsivo
- **Arquitetura Clean** com componentes reutilizáveis

### 🚧 Em Desenvolvimento
- Algoritmos de recomendação avançados
- Métricas de performance da IA
- Integração completa backend-frontend
- Analytics de uso e eficácia

---

## 🏗️ Arquitetura

```
FitAI/
├── fitai_backend/          # Django REST API
│   ├── apps/
│   │   ├── users/          # Autenticação e perfis
│   │   ├── exercises/      # Biblioteca de exercícios  
│   │   ├── workouts/       # Sistema de treinos
│   │   ├── recommendations/# IA de recomendação
│   │   ├── chatbot/        # Chatbot com OpenAI
│   │   └── notifications/  # Sistema de notificações
│   └── core/              # Configurações centrais
│
├── fitai_app/             # Flutter Mobile App
│   ├── lib/
│   │   ├── core/          # Theme, routing, DI
│   │   ├── data/          # Models, repositories  
│   │   ├── domain/        # Entities, use cases
│   │   └── presentation/  # Pages, widgets, BLoC
│   └── test/
│
└── docs/                  # Documentação do TCC
```

---

## 🔧 Tecnologias

### Backend
- **Django 4.2.7** + Django REST Framework
- **PostgreSQL** (produção) / SQLite (desenvolvimento)
- **OpenAI GPT** para processamento de linguagem natural
- **Redis** para cache e rate limiting
- **Token Authentication** para segurança

### Frontend
- **Flutter 3.x** com Material Design 3
- **GoRouter** para navegação declarativa
- **BLoC** para gerenciamento de estado
- **Clean Architecture** para escalabilidade
- **Dio/Retrofit** para comunicação com APIs

### IA/ML
- **OpenAI GPT-4** para chatbot inteligente
- **Algoritmos de Collaborative Filtering** para recomendações
- **Content-Based Filtering** para personalização
- **Hybrid Recommendation System** combinando múltiplas abordagens

---

## 📱 Funcionalidades

### Dashboard Inteligente
- Métricas personalizadas (peso, IMC, progresso)
- Recomendações de treinos baseadas em IA
- Ações rápidas para iniciar treinos ou chat

### Sistema de Treinos
- Catálogo completo com filtros inteligentes
- Busca em tempo real por exercícios
- Detalhes completos com instruções e dicas
- Timer funcional para execução de treinos

### Chatbot Fitness
- Conversas naturais sobre fitness e nutrição
- Contextualização baseada no perfil do usuário
- Recomendações personalizadas em tempo real
- Sistema de feedback para melhoria contínua

### Analytics (Diferencial Acadêmico)
- Métricas de performance dos algoritmos de IA
- Gráficos de acurácia das recomendações
- Análise comparativa de diferentes métodos de ML
- Dashboard de eficácia do sistema

---

## 🚀 Como Executar

### Pré-requisitos
- Python 3.11+
- Flutter SDK 3.x
- PostgreSQL (opcional para produção)

### Backend Django

```bash
# Clonar repositório
git clone https://github.com/seu-usuario/fitai-tcc.git
cd fitai-tcc

# Configurar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar banco de dados
cd fitai_backend
python manage.py migrate
python manage.py populate_db_fixed

# Executar servidor
python manage.py runserver
```

### Frontend Flutter

```bash
# Navegar para o app Flutter
cd fitai_app

# Instalar dependências
flutter pub get

# Executar aplicativo
flutter run
```

### Variáveis de Ambiente

```env
# .env no fitai_backend/
OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your_django_secret_key
DEBUG=True
DATABASE_URL=postgresql://user:pass@localhost/fitai  # Opcional
```

---

## 📊 APIs Principais

### Autenticação e Usuários
```http
POST /api/v1/users/register/     # Registro de usuário
POST /api/v1/users/login/        # Login
GET  /api/v1/users/dashboard/    # Dashboard personalizado
```

### Sistema de Treinos
```http
GET  /api/v1/workouts/           # Listar treinos
GET  /api/v1/workouts/{id}/      # Detalhes do treino
POST /api/v1/workouts/{id}/start/ # Iniciar sessão
```

### Chatbot Inteligente
```http
POST /api/v1/chat/conversations/start/         # Iniciar conversa
POST /api/v1/chat/conversations/{id}/message/  # Enviar mensagem
GET  /api/v1/chat/conversations/{id}/history/  # Histórico
```

### Recomendações com IA
```http
GET  /api/v1/recommendations/personalized/     # Recomendações do usuário
POST /api/v1/recommendations/ai/generate-workout/ # Gerar treino com IA
```

---

## 🧪 Aspectos Acadêmicos

### Algoritmos Implementados
1. **Collaborative Filtering** - Recomendações baseadas em usuários similares
2. **Content-Based Filtering** - Personalização por características do conteúdo  
3. **Hybrid Approach** - Combinação de múltiplas técnicas de ML
4. **Natural Language Processing** - Compreensão de contexto no chatbot

### Métricas de Avaliação
- **Precision/Recall** para recomendações
- **User Satisfaction Score** baseado em feedback
- **Algorithm Performance Metrics** comparando diferentes abordagens
- **Response Quality Score** para chatbot

### Contribuições Técnicas
- Framework de recomendação híbrida para fitness
- Sistema de contextualização para chatbots especializados
- Análise comparativa de algoritmos de ML em aplicações fitness
- Arquitetura escalável para sistemas de IA móveis

---

## 📈 Próximas Etapas

### Semana 2: Core da IA
- [ ] Implementar algoritmos de recomendação avançados
- [ ] Sistema de NLP para chatbot contextualizado  
- [ ] Analytics de performance da IA

### Semana 3: Integração e Testes
- [ ] Conectar frontend com APIs reais
- [ ] Sistema de feedback loop para ML
- [ ] Testes automatizados dos algoritmos

### Semana 4: Documentação TCC
- [ ] Análise comparativa de algoritmos
- [ ] Documentação técnica completa
- [ ] Preparação da apresentação

---

## 👨‍💻 Autor

Maycon Douglas e Antonio Roberto 
🎓 Tecnologia em Sistemas para internet
📅 TCC 2025

---

## 📄 Licença

Este projeto é desenvolvido para fins acadêmicos como parte do Trabalho de Conclusão de Curso.

---

## 🤝 Orientação

**Orientador:** Francisco Euder

---

<div align="center">

**FitAI - Transformando Fitness com Inteligência Artificial**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/seu-perfil)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/seu-usuario)

</div>