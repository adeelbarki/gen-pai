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
```
### 2️⃣ .NET API Server
```bash
cd api-server/PhysicianAI.Api
dotnet run
```
### 3️⃣ Python FastAPI LLM Server
```bash
cd llm-server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 5000
```
### 4️⃣ Redis (with RediSearch)
```bash
docker run -p 6379:6379 redis/redis-stack-server:latest
```

## 🏗 Architecture Overview
```bash
[ Angular Frontend ] → [ .NET API Server ] → [ Python FastAPI LLM Service ] → [ Redis Vector DB ]
```
- Frontend sends HTTP requests to .NET API
- .NET API orchestrates backend calls, forwards queries to FastAPI
- FastAPI runs LLM + RAG pipeline, retrieves data from Redis
- Response flows back to the user chat window

## 🔐 Secrets Handling
- `.env` in Python → holds `OPENAI_API_KEY`
- `appsettings.Development.json` in .NET → holds dev environment configs (ignored in Git)
```bash
OPENAI_API_KEY=your-openai-api-key-here
REDIS_HOST=localhost
REDIS_PORT=6379
```
Example appsettings.Development.json:
```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information"
    }
  },
  "AllowedHosts": "*"
}
```
## ✨ Features
✅ Handles non-emergency symptom Q&A
✅ Provides dynamic AI chat responses
✅ Integrates OpenAI GPT + LangChain RAG pipelines
✅ Uses Redis vector search for embedding queries
✅ Modular microservice architecture for scalability

## 📜 License
This project is under development. License terms will be added in a future release.
