# 🩺 GenPAI — Generative Physician AI

**GenPAI** is a multi-component medical AI system designed to assist patients with non-emergency general health questions.  
It combines a modern Angular frontend, a .NET Core API backend, a Python FastAPI microservice powered by OpenAI + LangChain, and Redis for advanced similarity search.

---

## 🌟 Project Structure

/genpai/
/frontend/ → Angular app (chat UI)
/api-server/ → .NET Core Web API (routing + orchestration)
/llm-server/ → Python FastAPI LLM service (OpenAI + LangChain)
/redis/ → Redis vector store (RediSearch)


---

## 📦 Components

### 🖼 Frontend (Angular)
- Chat UI for users to submit symptoms and queries
- Displays live AI responses, dynamic loading dots, and conversation history
- Connects to the backend API via HTTP

### ⚙ Backend API (C# / .NET Core)
- Receives patient queries from the Angular frontend
- Calls Python FastAPI LLM service for generative responses
- Acts as the secure middle layer between frontend and AI logic

### 🧠 LLM Service (Python / FastAPI)
- Handles natural language questions and symptom queries
- Uses OpenAI GPT (with LangChain RAG support)
- Connects to Redis vector search for embedding-based retrieval

### 🏪 Redis (Vector Store)
- Stores medical knowledge chunks + embeddings
- Provides fast KNN similarity search (using RediSearch)

---

## 🔑 Environment & Config

### ✅ Included in version control:
- Angular app source
- .NET Core API (excluding sensitive configs)
- Python LLM FastAPI service (excluding `.env`)
- Example configs

### ❌ Ignored via `.gitignore`:
- `llm-server/.env` → holds your `OPENAI_API_KEY`
- `llm-server/venv/` → Python virtual environment
- `api-server/PhysicianAI.Api/bin/` and `obj/` → .NET build artifacts
- `api-server/PhysicianAI.Api/appsettings.Development.json` → local dev secrets

---

## ⚡ Quick Start

### 1️⃣ Frontend (Angular)
```bash
cd frontend
npm install
npm run start
