# Patient Intake System with AI-Assisted Triage

A receptionist-facing web application for clinic patient registration with AI-suggested triage. Built as a project assignment demonstrating full-stack development, AI integration patterns, and production-grade API design.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend framework | **FastAPI** | Native async (critical for LLM call), Pydantic validation built-in, auto-generated OpenAPI docs |
| Database | **PostgreSQL 16** | Native ENUM type, real JSONB, enforced CHECK constraints, pg_trgm for name search |
| ORM | **SQLAlchemy 2.0 (async)** | Parameterized queries by default (SQL injection safety), Alembic migration story |
| Frontend build | **Vite + React + TypeScript** | Near-instant HMR in dev, native ES modules |
| Server state | **TanStack Query v5** | Fetch/cache/loading/error in one line; cache invalidation on save |
| Containerisation | **Docker Compose** | Reproducible demo; `docker-compose up` = fully running system |
| LLM provider | **OpenAI (gpt-4o-mini)** | Structured JSON output mode; smallest model sufficient for 3×9 classification |

---

## Architecture

```
React SPA (Vite)
     │  /api/v1/*  (proxied by nginx/Vite dev server)
     ▼
FastAPI (Python 3.12)
  ├── /api/v1/triage/analyze   ← side-effect-free AI call
  ├── /api/v1/intake           ← patient registration (POST/GET)
  ├── /api/v1/dashboard        ← daily summary aggregates
  └── /api/v1/meta             ← reference lists (departments, urgency)
        │
        ├── PostgreSQL 16 (patients, intake_records)
        ├── Triage Service (rule engine → LLM → validation → fallback)
        └── slowapi rate limiter (per-session, /triage/analyze only)
```

**Key architectural decisions:**
- `/triage/analyze` is **pure compute — no DB write**. The DB only sees the one record the human confirms.
- Rule engine short-circuits the LLM for obvious red-flag keywords (chest pain, seizure, etc.)
- AI suggestion state lives in React state between Analyze and Save — never persisted until human confirms.
- Override tracking is **two independent booleans** — urgency and department can be overridden separately.

---

## Setup

### Prerequisites
- Docker Desktop (or Docker Engine + Compose v2)
- Git

### Quick Start (Docker — recommended)

```bash
git clone <repo-url>
cd patient-intake-with-ai-triage

# 1. Copy env file and fill in your LLM API key
cp .env.example .env
# Edit .env: set LLM_API_KEY=sk-your-real-key

# 2. Start all services
docker-compose up

# 3. Open the app
# Frontend:  http://localhost:3000
# API docs:  http://localhost:8000/docs
# Health:    http://localhost:8000/health
```

### Manual Setup (without Docker)

**Backend:**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
# Set DATABASE_URL to your local Postgres instance in .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev    # runs on http://localhost:3000
```

---

## Assumptions

1. **Department list** (fixed, documented here as the single source of truth): General Medicine, Cardiology, Neurology, Orthopedics, Dermatology, ENT, Pulmonology, Gastroenterology, Emergency
2. **Single visit per session** — the UI registers one patient at a time; one patient can have multiple intake records over time (the schema supports this)
3. **Synthetic demo data only** — no real PHI; not HIPAA-compliant
4. **No authentication** — single-receptionist, single-clinic use case per the spec; auth is explicitly out of scope
5. **LLM API key required** for AI triage; the system degrades gracefully without it (manual dropdowns shown)

---

## Known Limitations

1. **No multilingual support** — non-English symptoms are best-effort; documented, not silently dropped
2. **Keyword list not exhaustive** — the rule engine's red-flag list is hand-maintained; the override log is the data that would surface missing terms
3. **No PHI-grade security** — no encryption at rest, no TLS enforcement, no RBAC; Section 11 of the design document lists what would be needed for real PHI
4. **Offset pagination only** — fine for single-clinic volume; cursor-based pagination is a stated next step for very large datasets
5. **AI accuracy not clinically validated** — the system is an assistive suggestion layer; human override exists for exactly this reason

---

## Project Phases

| Phase | Deliverable |
|---|---|
| 0 | Scaffolding & infrastructure (this phase) |
| 1 | Database schema & SQLAlchemy models |
| 2 | Pydantic schemas, error handling, meta endpoints |
| 3 | Triage service (rule engine + LLM + validation) |
| 4 | All backend API endpoints |
| 5–9 | Frontend (API client, hooks, intake form, dashboard, all patients, patient detail modal) |
| 10 | Security hardening |
| 11 | Full test suite |
| 12 | Docker Compose + README polish |
| 13 | Seed data, UI polish, demo prep |
