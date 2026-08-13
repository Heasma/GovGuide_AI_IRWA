# GovGuide AI

**IT3041 – Information Retrieval and Web Analytics**

> An Agentic AI-Based Government Service Discovery, Eligibility and Information Retrieval Platform

---

## ⚠️ Dataset Integration Status

> **Government dataset integration is pending.**
>
> The actual government-service dataset has not yet been received. All government-related database tables are preliminary placeholders. No government service data, eligibility rules, procedures, or official documents have been fabricated or inserted. The system is designed to accept the real dataset without architectural redesign.

---

## Problem Statement

Citizens often struggle to discover, understand, and navigate government services. Information is fragmented across multiple portals, written in complex language, and difficult to search effectively. GovGuide AI aims to provide a single, intelligent, evidence-grounded assistant that can help users discover services, understand eligibility, and locate official procedures — without fabricating information.

---

## Architecture Overview

```
User → React Frontend → FastAPI Backend → Security Layer → Agent Orchestrator
     → Research Agent (NLP + IR) → Government Knowledge Base
     → Advisory Agent (LLM, evidence-grounded) → Response Validator
     → Final Answer with Sources → User
```

Two cooperating AI agents:
- **Research Agent** — Processes queries through NLP, performs information retrieval, returns structured evidence
- **Advisory Agent** — Generates answers *only* from retrieved evidence, with source attribution and confidence scoring

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite |
| Backend | Python 3.11 + FastAPI |
| Database | PostgreSQL 16 + pgvector |
| Auth | JWT + bcrypt + RBAC |
| NLP | spaCy + NLTK (interfaces ready) |
| IR | BM25 + Semantic Search (interfaces ready) |
| LLM | Adapter pattern (OpenAI / local LLM) |
| Container | Docker + Docker Compose |

---

## Project Structure

```
govguide-ai/
├── frontend/          # React + Vite SaaS UI
├── backend/           # FastAPI application
├── agents/            # Research Agent + Advisory Agent
├── orchestrator/      # Agent orchestration layer
├── nlp/               # NLP pipeline (stubs in Phase 1)
├── retrieval/         # IR layer (stubs in Phase 1)
├── llm/               # LLM abstraction (stubs in Phase 1)
├── security/          # JWT, RBAC, rate limiting, audit
├── database/          # ORM models, schema, repositories
├── responsible_ai/    # Confidence, uncertainty, attribution
├── tests/             # Unit + integration + evaluation
├── documentation/     # Architecture docs
├── data/
│   ├── raw/           # ← Real dataset goes here (gitignored)
│   └── processed/     # ← Chunked/embedded docs (gitignored)
├── docker-compose.yml
└── .env.example
```

---

## Setup Instructions

### Prerequisites

- Docker Desktop (recommended) OR Python 3.11+ and Node.js 20+
- PostgreSQL 16 (if not using Docker)

### 1. Clone and configure

```bash
git clone <your-repo-url>
cd govguide-ai
cp .env.example .env
# Edit .env with your values (JWT_SECRET_KEY is required)
```

### 2. Start the database

```bash
# Docker (recommended)
docker-compose up -d postgres

# Or use a local PostgreSQL instance and set DATABASE_URL in .env
```

### 3. Run the backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

pip install -r requirements.txt

# Apply database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API documentation available at: `http://localhost:8000/docs`

### 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: `http://localhost:5173`

### 5. Start everything with Docker

```bash
docker-compose up
```

---

## Environment Variables

See [`.env.example`](.env.example) for all available variables. Critical ones:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | Async PostgreSQL connection string |
| `JWT_SECRET_KEY` | Yes | Random secret (min 32 chars) |
| `LLM_API_KEY` | Phase 2 | LLM provider API key |
| `EMBEDDING_MODEL` | Phase 2 | Embedding model name (dimension TBD) |
| `CORS_ORIGINS` | Yes | Allowed frontend origins |

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## API Documentation

After starting the backend, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Current Phase Status

| Component | Status |
|---|---|
| Project scaffold | ✅ Complete |
| Database schema (preliminary) | ✅ Complete |
| JWT Authentication + RBAC | ✅ Complete |
| FastAPI API layer | ✅ Complete |
| Agent message schema | ✅ Complete |
| Agent orchestrator | ✅ Complete |
| Research Agent skeleton | ✅ Complete |
| Advisory Agent skeleton | ✅ Complete |
| React frontend foundation | ✅ Complete |
| NLP pipeline | 🔧 Interface/stub — awaiting dataset |
| Information Retrieval | 🔧 Interface/stub — awaiting dataset |
| LLM integration | 🔧 Interface/stub — awaiting API key |
| Government dataset | ⏳ Pending |
| Vector embeddings | ⏳ Pending (model TBD) |
| Evaluation benchmarks | ⏳ Pending (requires dataset) |

---

## Academic Notice

This project is developed for **IT3041 – Information Retrieval and Web Analytics**.

All government-related data presented in the UI is clearly marked as demo/placeholder data. No government information has been fabricated, invented, or assumed. The system architecture is designed to accept the real government dataset without redesigning the application.

---

## License

Academic project — IT3041, 2026
