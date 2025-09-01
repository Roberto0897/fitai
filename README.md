# FitAI - Sistema de Fitness Inteligente com IA

**Projeto de TCC - Sistemas de Informação**  
**Desenvolvedor:** Maycon Almeida e Antonio Roberto
**Ano:** 2025  

Sistema backend completo para aplicativo de fitness personalizado que combina inteligência artificial com algoritmos de recomendação tradicionais para criar uma experiência única de treino.

---

## 🎯 Objetivo do Projeto

Democratizar o acesso a orientações de fitness personalizadas através de um sistema híbrido de IA que oferece:

- Recomendações de treinos adaptadas ao perfil individual
- Sistema de notificações contextuais inteligentes  
- Análise de progresso com insights personalizados
- Interface de APIs REST completa para aplicações mobile

---

## 🏗️ Arquitetura do Sistema

### Backend Django REST Framework
```
FitAI Backend/
├── apps/
│   ├── users/           # 8 APIs - Gestão de usuários e perfis
│   ├── exercises/       # 5 APIs - Biblioteca de exercícios
│   ├── workouts/        # 15 APIs - Treinos e sessões
│   ├── recommendations/ # 7 APIs - Sistema de IA híbrido  
│   └── notifications/   # 12 APIs - Notificações inteligentes
├── fitai/settings/      # Configurações por ambiente
└── logs/               # Sistema de logging estruturado
```

### Tecnologias Core
- **Framework:** Django 4.2.7 + Django REST Framework 3.14.0
- **Inteligência Artificial:** OpenAI GPT v1.12.0
- **Autenticação:** Token-based Authentication
- **Banco de Dados:** SQLite (desenvolvimento) / PostgreSQL (produção)
- **Cache:** Django Cache Framework + Redis ready
- **Testes:** 43 testes automatizados com 96% de cobertura

---

## 🧠 Sistema de IA Híbrido

O diferencial técnico do projeto é o algoritmo híbrido que combina:

### Componentes do Sistema (com pesos otimizados):
1. **IA Personalizada (40%)** - OpenAI GPT com contexto do usuário
2. **Baseado em Conteúdo (30%)** - Análise de perfil e histórico
3. **Filtragem Colaborativa (20%)** - Padrões de usuários similares
4. **Algoritmo Híbrido (10%)** - Combinação inteligente de todos

### Características Técnicas:
- **Fallbacks Inteligentes:** Sistema funciona mesmo sem IA disponível
- **Rate Limiting:** 20 requisições/hora geral, 10/hora para IA
- **Cache Multicamada:** Reduz chamadas desnecessárias à API
- **Validação de Qualidade:** Score mínimo para respostas da IA
- **Monitoramento:** Logs detalhados e métricas de performance

---

## 📊 Funcionalidades Implementadas

### Sistema de Usuários (8 APIs)
- Registro e autenticação com token
- Perfis completos (metas, preferências, biometria)
- Sistema de onboarding personalizado
- Análise de progresso e estatísticas

### Biblioteca de Exercícios (5 APIs)  
- Mais de 8 exercícios base implementados
- Categorização (calistenia, musculação, cardio)
- Instruções detalhadas e dicas de execução
- Cálculo automático de calorias queimadas

### Sistema de Treinos (15 APIs)
- Criação e gestão de treinos personalizados
- Templates predefinidos (Iniciante, HIIT, Core)
- Sessões ativas com cronômetro
- Tracking de séries, repetições e cargas
- Histórico completo e análise de evolução

### Recomendações Inteligentes (7 APIs)
- Engine híbrido de recomendações
- Geração de treinos por IA contextual
- Análise de progresso com insights
- Mensagens motivacionais personalizadas
- Sistema de feedback para aprendizado contínuo

### Notificações Contextuais (12 APIs)
- 4 models expandidos com analytics avançadas
- Preferências granulares por usuário
- Agendamento otimizado por padrões individuais
- Sistema de engajamento e métricas
- Templates dinâmicos com variáveis contextuais

---

## 🧪 Qualidade e Testes

### Cobertura de Testes: 43 Testes Automatizados
- **Models:** 12 testes unitários completos
- **APIs:** 23 testes de integração end-to-end
- **Edge Cases:** 5 testes de casos extremos
- **Rate Limiting:** 2 testes de throttling
- **Performance:** 1 teste de otimização

### Métricas de Qualidade
- **Cobertura:** 96% no sistema de notificações, 46% geral
- **Aprovação:** 100% dos testes passando
- **Padrões:** PEP8, documentação inline, type hints

---

## 🚀 Setup e Execução

### Pré-requisitos
- Python 3.8+
- Git
- Conta OpenAI (opcional - sistema tem fallbacks)

### Instalação
```bash
# Clone o repositório
git clone https://github.com/Maaykd/FitAi-TCC.git
cd FitAi-TCC

# Crie ambiente virtual
python -m venv venv

# Ative o ambiente (Windows)
venv\Scripts\activate

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas chaves (OpenAI opcional)

# Execute migrações
python manage.py migrate

# Popule banco com dados de exemplo
python populate_db.py

# Execute servidor de desenvolvimento
python manage.py runserver
```

### Acesso
- **API Base:** http://127.0.0.1:8000/api/v1/
- **Admin Django:** http://127.0.0.1:8000/admin/

---

## 📋 APIs Disponíveis

### Usuários (/api/v1/users/)
- `POST /register/` - Registrar novo usuário
- `POST /login/` - Autenticar usuário
- `GET /profile/` - Obter perfil completo
- `PUT /profile/` - Atualizar perfil
- `GET /statistics/` - Estatísticas do usuário
- `POST /set-goal/` - Definir meta
- `GET /progress/` - Análise de progresso
- `POST /onboarding/` - Completar onboarding

### Exercícios (/api/v1/exercises/)
- `GET /` - Listar exercícios
- `GET /{id}/` - Detalhes do exercício
- `GET /by-muscle-group/` - Filtrar por grupo muscular
- `GET /by-category/` - Filtrar por categoria
- `GET /search/` - Buscar exercícios

### Treinos (/api/v1/workouts/)
- `GET /` - Listar treinos
- `POST /` - Criar treino personalizado
- `GET /templates/` - Templates predefinidos
- `POST /sessions/start/` - Iniciar sessão
- `PUT /sessions/{id}/complete/` - Finalizar sessão
- `GET /history/` - Histórico de treinos
- `GET /statistics/` - Estatísticas detalhadas
- E mais 8 endpoints avançados...

### Recomendações (/api/v1/recommendations/)
- `GET /personalized/` - Recomendações híbridas
- `POST /generate-workout/` - Gerar treino por IA
- `GET /progress-analysis/` - Análise inteligente
- `GET /motivation/` - Mensagem motivacional
- `POST /feedback/` - Enviar feedback
- `GET /history/` - Histórico de recomendações
- `GET /test-system/` - Status do sistema

### Notificações (/api/v1/notifications/)
- `GET /` - Listar notificações
- `POST /preferences/` - Configurar preferências
- `POST /mark-as-read/` - Marcar como lida
- `POST /test-notification/` - Enviar teste
- `GET /stats/` - Analytics completas
- E mais 7 endpoints especializados...

---

## 🧪 Executar Testes

```bash
# Todos os testes
python manage.py test

# Testes específicos por app
python manage.py test apps.notifications.tests
python manage.py test apps.users.tests

# Com cobertura detalhada
pip install coverage
coverage run --source='.' manage.py test
coverage report -m
```

---

## 📈 Dados de Demonstração

O script `populate_db.py` cria automaticamente:

### Usuários de Teste
- **joao_silva** - Foco ganho muscular, nível moderado
- **maria_santos** - Foco bem-estar, nível ativo  
- **ana_costa** - Foco emagrecimento, nível sedentário

### Exercícios Base (8 implementados)
- Flexão de Braço, Agachamento Livre, Prancha
- Burpee, Jumping Jacks, Abdominal Tradicional
- Mountain Climber, Glute Bridge

### Treinos Template (3 funcionais)
- **Iniciante - Corpo Todo** (30min, 200 cal)
- **HIIT Cardio Explosivo** (20min, 300 cal)
- **Core & Abdômen** (25min, 150 cal)

**Login de teste:** Qualquer usuário acima + senha `123456`

---

## 🔐 Configurações de Segurança

### Autenticação
- Token-based authentication em todas as APIs
- Rate limiting preventivo por categoria
- Validação rigorosa de inputs
- CORS configurado para Flutter

### Variáveis de Ambiente (.env)
```env
SECRET_KEY=sua-chave-django-aqui
DEBUG=True
OPENAI_API_KEY=sk-sua-chave-openai-aqui
OPENAI_MODEL=gpt-3.5-turbo
DB_NAME=fitai_db
DB_USER=postgres
DB_PASSWORD=senha-do-banco
```

---

## 📱 Próximos Passos (Roadmap TCC)

### Fase 1 - Frontend Flutter (8 semanas)
- [ ] 7 telas principais (Dashboard, Treinos, Perfil, etc.)
- [ ] Integração completa com 47 APIs
- [ ] Sistema offline com sincronização
- [ ] Interface moderna e intuitiva

### Fase 2 - Deploy e Documentação (2 semanas)
- [ ] Deploy em produção (Railway/Heroku)
- [ ] Documentação técnica completa
- [ ] Diagramas de arquitetura
- [ ] Manual de usuário

### Fase 3 - Finalização TCC (2 semanas)
- [ ] Análise de resultados
- [ ] Comparação com soluções existentes
- [ ] Preparação da apresentação
- [ ] Defesa perante banca

---

## 📊 Métricas do Projeto

### Linhas de Código
- **Total:** ~15.000 linhas
- **Python/Django:** ~12.000 linhas
- **Testes:** ~2.000 linhas
- **Configurações:** ~1.000 linhas

### APIs REST
- **Total:** 47 endpoints funcionais
- **Autenticadas:** 39 endpoints
- **Públicas:** 8 endpoints
- **Com IA:** 12 endpoints

### Funcionalidades
- **CRUD Completo:** Users, Exercises, Workouts
- **IA Integrada:** Recomendações, Análises, Motivação
- **Analytics:** Progresso, Engajamento, Estatísticas
- **Notificações:** Templates, Scheduling, Tracking

---

## 🤝 Contribuição e Desenvolvimento

### Estrutura de Commits
- `feat:` nova funcionalidade
- `fix:` correção de bug  
- `test:` adição de testes
- `docs:` documentação
- `refactor:` refatoração de código

### Padrões de Código
- PEP8 para Python
- Docstrings em inglês
- Type hints quando possível
- Nomes descritivos em português

---

## 📄 Licença e Uso Acadêmico

Este projeto foi desenvolvido como Trabalho de Conclusão de Curso (TCC) para o curso de Sistemas de Informação. O código é disponibilizado para fins educacionais e de demonstração das competências técnicas adquiridas.

### Funcionalidades Demonstradas
- **Desenvolvimento Full-Stack:** Backend robusto com APIs REST
- **Integração com IA:** Uso prático de Large Language Models
- **Engenharia de Software:** Testes, arquitetura, padrões
- **Inovação Técnica:** Sistema híbrido único no mercado

---


*Desenvolvido com Django REST Framework, OpenAI GPT e muita dedicação para democratizar o acesso a fitness personalizado através da tecnologia.*