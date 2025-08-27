# FitAI - Sistema Inteligente de Fitness

## Descrição
Sistema de fitness com inteligência artificial para recomendações personalizadas, geração de treinos e análise de progresso.

## Tecnologias
- **Backend**: Django 4.2.7 + Django REST Framework
- **IA**: OpenAI GPT-3.5-turbo
- **Banco**: SQLite3 (desenvolvimento)
- **Cache**: Redis (opcional)

## Status do Projeto
- ✅ **PRIORIDADE 1**: Sistema de IA (100% concluída)
- 🚧 **PRIORIDADE 2**: Notificações e Gamificação (próxima)
- 📱 **PRIORIDADE 4**: App Flutter (futuro)

## APIs Implementadas
- 35 endpoints REST funcionais
- 7 APIs de IA avançadas
- Sistema híbrido com fallbacks
- Rate limiting profissional

## Instalação
```bash
# Clone o repositório
git clone <url-do-repositorio>

# Entre na pasta
cd fitai_backend

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env

# Execute migrações
python manage.py migrate

# Inicie o servidor
python manage.py runserver