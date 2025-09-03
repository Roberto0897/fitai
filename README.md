# 🏋️‍♂️ FitAI - Plataforma de Treinos com IA

O **FitAI** é um sistema de apoio a treinos e saúde, com foco em **personalização através de inteligência artificial** e **chatbot especializado em fitness**.  
O backend foi desenvolvido em **Django + Django REST Framework**, com APIs robustas e seguras, já prontas para integração com o frontend em **Flutter**.

---

## 🚀 Status Atual
- ✅ Backend completo e funcional
- ✅ 55+ APIs REST implementadas
- ✅ Chatbot fitness com integração OpenAI (com fallbacks inteligentes)
- ✅ Autenticação e rate limiting configurados
- ✅ Banco pronto para PostgreSQL (produção) e SQLite (desenvolvimento)
- 🔜 Próxima etapa: Desenvolvimento do frontend em **Flutter**

---

## 📊 Estrutura do Projeto

### Apps Django
- **users** → Autenticação e perfis  
- **exercises** → Biblioteca de exercícios  
- **workouts** → Sistema de treinos e sessões  
- **recommendations** → Recomendação personalizada (IA híbrida)  
- **notifications** → Notificações do sistema  
- **chatbot** → Chatbot fitness com IA  
- **core** → Configurações centrais  

### Tecnologias Core
- Django 4.2.7 + Django REST Framework 3.14.0  
- OpenAI GPT (com fallbacks automáticos)  
- Redis / LocMemCache  
- Token Authentication  
- PostgreSQL (produção) / SQLite (dev)  

---

## 🤖 APIs do Chatbot

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET    | `/api/v1/chat/test/` | Status do sistema |
| POST   | `/api/v1/chat/conversations/start/` | Iniciar conversa |
| POST   | `/api/v1/chat/conversations/{id}/message/` | Enviar mensagem |
| GET    | `/api/v1/chat/conversations/{id}/history/` | Ver histórico |
| POST   | `/api/v1/chat/conversations/{id}/end/` | Finalizar conversa |
| GET    | `/api/v1/chat/conversations/` | Listar conversas |
| POST   | `/api/v1/chat/messages/{id}/feedback/` | Feedback da mensagem |
| GET    | `/api/v1/chat/analytics/` | Analytics do usuário |

---

## ⚙️ Como Rodar o Projeto

### 1. Clonar repositório
# 🏋️‍♂️ FitAI - Plataforma de Treinos com IA

O **FitAI** é um sistema de apoio a treinos e saúde, com foco em **personalização através de inteligência artificial** e **chatbot especializado em fitness**.  
O backend foi desenvolvido em **Django + Django REST Framework**, com APIs robustas e seguras, já prontas para integração com o frontend em **Flutter**.

---

## 🚀 Status Atual
- ✅ Backend completo e funcional
- ✅ 55+ APIs REST implementadas
- ✅ Chatbot fitness com integração OpenAI (com fallbacks inteligentes)
- ✅ Autenticação e rate limiting configurados
- ✅ Banco pronto para PostgreSQL (produção) e SQLite (desenvolvimento)
- 🔜 Próxima etapa: Desenvolvimento do frontend em **Flutter**

---

## 📊 Estrutura do Projeto

### Apps Django
- **users** → Autenticação e perfis  
- **exercises** → Biblioteca de exercícios  
- **workouts** → Sistema de treinos e sessões  
- **recommendations** → Recomendação personalizada (IA híbrida)  
- **notifications** → Notificações do sistema  
- **chatbot** → Chatbot fitness com IA  
- **core** → Configurações centrais  

### Tecnologias Core
- Django 4.2.7 + Django REST Framework 3.14.0  
- OpenAI GPT (com fallbacks automáticos)  
- Redis / LocMemCache  
- Token Authentication  
- PostgreSQL (produção) / SQLite (dev)  

---

## 🤖 APIs do Chatbot

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET    | `/api/v1/chat/test/` | Status do sistema |
| POST   | `/api/v1/chat/conversations/start/` | Iniciar conversa |
| POST   | `/api/v1/chat/conversations/{id}/message/` | Enviar mensagem |
| GET    | `/api/v1/chat/conversations/{id}/history/` | Ver histórico |
| POST   | `/api/v1/chat/conversations/{id}/end/` | Finalizar conversa |
| GET    | `/api/v1/chat/conversations/` | Listar conversas |
| POST   | `/api/v1/chat/messages/{id}/feedback/` | Feedback da mensagem |
| GET    | `/api/v1/chat/analytics/` | Analytics do usuário |

---

## ⚙️ Como Rodar o Projeto

### 1. Clonar repositório
```bash
git clone https://github.com/seu-usuario/fitai-tcc.git
cd fitai-tcc

git clone https://github.com/seu-usuario/fitai-tcc.git
cd fitai-tcc
