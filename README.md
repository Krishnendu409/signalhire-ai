# SignalHire AI - Multi-Agent Talent Intelligence Platform

SignalHire AI is a production-grade talent intelligence platform that goes beyond keyword matching to identify top talent using multi-level AI reasoning, semantic retrieval, and career trajectory analysis.

## 🚀 Key Features

- **Multi-Agent Ranking Engine**: Combines dense retrieval (embeddings) with cross-encoder reranking and LLM-based dimension scoring.
- **Deep Resume Parsing**: Extracts structured data using DeepSeek-V3 with local Ollama fallback.
- **Career Trajectory Intelligence**: Classifies candidates into archetypes like "Fast Climber" or "Stable Performer" using deterministic heuristics.
- **Resilient AI Pipeline**: Multi-tiered fallback system (DeepSeek -> Ollama -> Heuristic Mock) ensuring 100% uptime.
- **FCRA-Compliant Audit Trail**: Verifiable multi-agent decision logs stored for legal defensibility.
- **Async Task Orchestration**: Persistent queuing via Redis and SAQ for heavy processing.

## 🛠 Tech Stack

- **Backend**: FastAPI, SQLAlchemy (PostgreSQL), AsyncPG, Qdrant (Vector DB), Redis, SAQ.
- **Frontend**: Next.js 14, Tailwind CSS, Framer Motion, Lucide Icons.
- **AI**: DeepSeek V3, Google Gemini (Embeddings), Ollama (Local Fallback).

## 🏃 Local Development

### 1. Requirements
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Ollama (optional, for local fallback)

### 2. Setup
1. Clone the repository.
2. Create `.env` in `/backend` using `.env.example`.
3. Create `.env.local` in `/frontend` using `NEXT_PUBLIC_API_URL=http://localhost:8000`.

### 3. Run with Docker
```bash
docker-compose up --build
```

### 4. Run Manually
**Backend:**
```bash
cd backend
pip install -r requirements.txt
python run_server.py
```
**Worker:**
```bash
cd backend
python -m app.tasks.worker
```
**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 🔒 Security & Compliance
- **JWT Auth**: Full user isolation with JWT validation.
- **Audit Logs**: Every AI decision is logged to `backend/logs/audit_trail.log`.
- **CORS**: Strict CORS policies for production-ready deployment.

## 📝 License
Proprietary. Built for SignalHire AI platform transition.
