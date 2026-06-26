# Patient Intake System with AI-Assisted Triage

A receptionist-facing web application for clinic patient registration with AI-suggested triage. Built as a project assignment demonstrating full-stack development, AI integration patterns, and production-grade API design.

**Demo-ready:** `git clone` → `docker-compose up` → fully running in under 5 minutes.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Manual Setup](#manual-setup-without-docker)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Assumptions](#assumptions)
- [Known Limitations](#known-limitations)
- [Project Phases](#project-phases)

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| **Backend framework** | **FastAPI** | Native async (critical for LLM calls), Pydantic validation built-in, auto-generated OpenAPI docs, type-safe endpoints |
| **Database** | **PostgreSQL 16** | Native ENUM type with `ALTER TYPE ADD VALUE`, real JSONB, enforced CHECK constraints, `pg_trgm` for case-insensitive name search |
| **ORM** | **SQLAlchemy 2.0 (async)** | Parameterized queries by default (SQL injection safety), async support for concurrent LLM calls, Alembic migrations |
| **Frontend build** | **Vite + React + TypeScript** | Near-instant HMR in dev, native ES modules, type safety end-to-end |
| **Server state** | **TanStack Query v5** | Fetch/cache/loading/error in one line; automatic refetch on mutation; cache invalidation on save |
| **Containerisation** | **Docker Compose** | Reproducible demo; single command starts Postgres, backend, and frontend with proper health checks |
| **LLM Provider** | **Groq LPU + Google Gemini** | Hybrid: Groq primary (fastest inference, 30 RPM free) with Gemini fallback for demo reliability; production-ready cost optimization |
| **Web server** | **nginx (Alpine)** | Production-ready static asset serving; API proxy; SPA routing support |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    React SPA (Vite + TypeScript)                │
│  - Dashboard (daily stats, charts, mini-table)                  │
│  - All Patients (search, filter, pagination)                    │
│  - Patient Detail Modal (URL-synced via ?id=<uuid>)             │
│  - Intake Form Modal (Analyze → Review → Save state machine)    │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS/JSON via /api/v1/*
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI (Python 3.12)                        │
│  /api/v1/triage/analyze  ← side-effect-free AI call             │
│  /api/v1/intake          ← patient registration (POST/GET)      │
│  /api/v1/dashboard       ← daily summary aggregates             │
│  /api/v1/meta            ← reference lists (enum values)        │
│                                                                 │
│  Triage Service: rule engine → LLM → validation → fallback      │
│  Rate Limiter: slowapi 10/min per IP on /triage/analyze         │
│  Security: CORS, headers, input validation, error envelope      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL 16                                │
│  - patients: name, age (CHECK 0-130), gender, contact           │
│  - intake_records: symptoms, AI snapshot, final decision        │
│  - Override flags: urgency_overridden, department_overridden    │
│  - Indexes: created_at, urgency, department, pg_trgm (name)     │
└─────────────────────────────────────────────────────────────────┘
```

### Key Architectural Decisions

| Decision | Rationale |
|---|---|
| **`/triage/analyze` is pure compute (no DB write)** | AI suggestion lives in React state until human confirms Save; prevents littering DB with abandoned drafts when receptionist refines symptoms |
| **Rule engine short-circuits LLM** | Red-flag keywords (chest pain, seizure) bypass LLM entirely — deterministic safety net for unambiguous emergencies |
| **Two independent override flags** | Urgency and department can be overridden separately (e.g., agree with department but bump urgency after observing patient) |
| **URL-synced patient detail modal** | `/patients?id=<uuid>` enables deep-linking, bookmarking, browser back button; list context preserved |
| **Four-layer enum validation** | LLM schema → code membership check → Pydantic → DB ENUM; defense-in-depth against invalid output |
| **Override flags computed server-side** | Frontend never sends `urgency_overridden`; backend compares `ai_suggested_*` to `final_*` — prevents manipulation |

---

## Quick Start

### Prerequisites

- **Docker Desktop** (or Docker Engine + Compose v2)
- **Git**
- **Groq API key** (free tier: https://console.groq.com/keys)
- **Google Gemini API key** (fallback, free tier: https://aistudio.google.com/app/apikey)

### Step-by-Step

```bash
# 1. Clone the repository
git clone <repo-url>
cd patient-intake-with-ai-triage

# 2. Copy environment template and fill in your API keys
cp .env.example .env
# Edit .env with your actual keys:
#   - GROQ_API_KEY=gsk-your-groq-key (primary, fastest)
#   - GEMINI_API_KEY=your-gemini-key (fallback, for reliability)

# 3. Start all services (Postgres, backend, frontend)
docker-compose up

# Wait ~30 seconds for:
# - Postgres to initialize (runs init.sql for pg_trgm extension)
# - Alembic migrations to run (creates tables, indexes)
# - Backend to start (healthcheck passes)
# - Frontend nginx to serve static assets

# 4. (Optional) Seed database with 15 synthetic patients
# This makes dashboard charts visually meaningful on first load
docker-compose exec backend python scripts/seed_data.py

# 5. Open the application
# Frontend:  http://localhost:3000
# API docs:  http://localhost:8000/docs
# Health:    http://localhost:8000/health
```

### LLM Configuration (Hybrid: Groq + Gemini)

The system uses **Groq LPU** as primary (free tier: 30 RPM, 10K requests/day, ~100ms response)
with **Google Gemini Flash** as fallback when rate limits are hit. This ensures:

- ✅ **Fastest demo** — Groq LPU inference (~100ms, 3x faster than others)
- ✅ **Zero interruptions** — automatic fallback to Gemini if Groq quota exceeded
- ✅ **Cost-effective** — Both free tiers sufficient for most demos and production
- ✅ **Production-ready** — Seamless failover, no manual intervention needed

**Get Your API Keys:**

1. **Groq (Primary):** https://console.groq.com/keys
   - Free tier: 30 RPM, 10K requests/day
   - Model: `llama-3.1-70b-versatile` (balanced) or `llama-3.2-3b-preview` (fastest)
   - Sign up takes 2 minutes, instant key generation

2. **Gemini (Fallback):** https://aistudio.google.com/app/apikey
   - Free tier: 15 RPM, 1M tokens/month
   - Model: `gemini-2.0-flash-exp` (latest) or `gemini-1.5-flash` (stable)
   - Sign up with Google account, instant key

### Verify It Works

1. **Dashboard** loads with today's stats (empty initially)
2. Click **"Register Patient"** → form modal opens
3. Fill patient details + symptoms (e.g., "chest pain for 2 hours")
4. Click **"Analyze"** → AI suggests urgency/department
5. Accept or override → click **"Save"**
6. Dashboard refreshes; patient appears in mini-table

### Seed Data (Optional)

To populate the database with 15 synthetic patients for demo purposes:

```bash
docker-compose exec backend python scripts/seed_data.py
```

This creates patients covering all four override scenarios:
- **Manual** (3 patients): No AI involvement
- **AI Accepted** (4 patients): Receptionist agrees with AI suggestion
- **Fully Overridden** (3 patients): Both urgency and department changed
- **Partially Overridden** (5 patients): One field changed, one accepted

After seeding, the dashboard will show:
- Meaningful urgency distribution chart (routine/priority/urgent)
- Department breakdown across all 9 specialties
- Source column showing Manual/AI Accepted/Overridden mix
- Recent patients table with varied cases

### Stop & Reset

```bash
# Stop all services
docker-compose down

# Stop and delete all data (for fresh start)
docker-compose down -v
```

---

## Manual Setup (Without Docker)

### Backend

```bash
cd backend

# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp ../.env.example .env
# Edit .env: set DATABASE_URL to your local Postgres

# 4. Run migrations
alembic upgrade head

# 5. Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Start dev server (with hot-reload)
npm run dev

# Opens at http://localhost:3000
# Proxies /api/* to http://localhost:8000
```

### Postgres (Local)

```bash
# Install PostgreSQL 16+ (platform-specific)
# macOS: brew install postgresql@16
# Ubuntu: sudo apt install postgresql-16

# Create database
createdb patient_intake

# Enable extensions
psql -d patient_intake -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
psql -d patient_intake -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
```

---

## API Documentation

Interactive API docs are available at:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Key Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/triage/analyze` | Analyze symptoms → AI suggestion (no DB write) |
| `POST` | `/api/v1/intake` | Register patient + intake record |
| `GET` | `/api/v1/intake` | List/search with filters (paginated) |
| `GET` | `/api/v1/intake/{id}` | Get single record by UUID |
| `GET` | `/api/v1/dashboard/summary` | Daily aggregates (total, by_urgency, by_department) |
| `GET` | `/api/v1/meta/departments` | List of 9 department enum values |
| `GET` | `/api/v1/meta/urgency-levels` | List of 3 urgency enum values |

### Error Envelope

All errors return unified format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Field required",
    "field": "body.final_urgency"
  }
}
```

---

## Testing

### Run All Tests

```bash
cd backend
pytest -v
```

### Test Coverage by File

| File | Tests | Coverage |
|---|---|---|
| `test_rule_engine.py` | 35 | Red-flag keywords, case-insensitive, partial match |
| `test_triage_service.py` | 21 | LLM mock, validation, retry, confidence clamp |
| `test_triage_api.py` | 8 | HTTP triage endpoint, 503 fallback |
| `test_intake_api.py` | 22 | CRUD, override flags, pagination, filters |
| `test_edge_cases.py` | 21 | Boundaries, special chars, division-by-zero |
| `test_schema.py` | 20 | DB constraints, enums, CHECK constraints |
| `test_health.py` | 15 | Smoke tests, meta endpoints |
| `test_api.py` | 17 | Repo-level create, override computation |
| **Total** | **159** | **All Phase 11 requirements** |

### Zero Real LLM Calls

All tests use mocked LLM client — safe to run in CI without API key:

```python
@pytest.mark.asyncio
async def test_llm_valid_response_returned(self, client, db_session):
    with patch("app.services.llm_client.call_llm", new_callable=AsyncMock) as mock:
        mock.return_value = {"urgency": "priority", "department": "neurology", "confidence": 0.85}
        result = await analyze("mild headache")
        assert result.urgency == UrgencyLevel.priority
```

---

## Assumptions

1. **Department list** (fixed, documented as single source of truth):
   - General Medicine, Cardiology, Neurology, Orthopedics, Dermatology, ENT, Pulmonology, Gastroenterology, Emergency

2. **Single visit per session UI**:
   - Receptionist registers one patient at a time
   - Schema supports multiple visits per patient over time (one-to-many)

3. **Synthetic demo data only**:
   - No real PHI (Protected Health Information)
   - Not HIPAA-compliant; Section 11 of design doc lists requirements for real PHI

4. **No authentication layer**:
   - Single-receptionist, single-clinic use case per spec
   - Auth is explicitly out of scope (Phase 2 item)

5. **English-only symptoms**:
   - Non-English input is best-effort; documented limitation
   - Multilingual support is a stated "next phase" item

---

## Known Limitations

1. **No multilingual support**
   - Non-English symptoms are best-effort; low confidence reflects uncertainty
   - Full i18n is a Phase 2 item

2. **Keyword list not exhaustive**
   - Rule engine red-flag list is hand-maintained (~20 keywords)
   - Override log is the data that would surface missing terms

3. **No PHI-grade security**
   - No encryption at rest, no TLS enforcement, no RBAC
   - Section 11 of design doc lists: encryption at rest, TLS everywhere, audit logging, HIPAA review

4. **Offset pagination only**
   - Fine for single-clinic volume (<100k records)
   - Cursor-based pagination is a stated next step for very large datasets

5. **AI accuracy not clinically validated**
   - No labeled clinical dataset exists for take-home assignment
   - Mitigation: rule-engine safety net + mandatory human override

6. **Dev dependencies have known vulnerabilities**
   - `npm audit` shows 2 moderate/high vulns in `esbuild` and `vite`
   - Both are dev-server only; not present in production nginx build
   - Fix requires breaking upgrade (`vite@8.1.0`)

---

## Project Phases

| Phase | Deliverable | Status |
|---|---|---|
| 0 | Scaffolding, Docker, env | ✅ Complete |
| 1 | Database schema, models, migrations | ✅ Complete |
| 2 | Pydantic schemas, error handling, meta endpoints | ✅ Complete |
| 3 | Triage service (rule engine + LLM + validation) | ✅ Complete |
| 4 | All backend API endpoints | ✅ Complete |
| 5 | Frontend infrastructure (API client, hooks, routing) | ✅ Complete |
| 6 | Intake form + triage state machine | ✅ Complete |
| 7 | Dashboard page (stats, charts, mini-table) | ✅ Complete |
| 8 | All Patients page (search, filter, pagination) | ✅ Complete |
| 9 | Patient detail modal (URL-synced) | ✅ Complete |
| 10 | Security hardening (10 items) | ✅ Complete |
| 11 | Full test suite (159 tests) | ✅ Complete |
| 12 | Docker Compose + README polish | ✅ Complete |
| 13 | Seed data, UI polish, demo prep | ✅ Complete |

---

## Pre-Demo Checklist

- [ ] `docker-compose down -v && docker-compose up` on clean checkout — verify under 5 minutes
- [ ] LLM API key is valid and has credits
- [ ] Test full flow: Register → Analyze → Override one field → Save → verify in dashboard + All Patients
- [ ] Test LLM fallback: temporarily set invalid API key → verify manual dropdowns appear
- [ ] Verify all 159 tests pass: `pytest -v`

---

**Built with:** FastAPI · PostgreSQL · SQLAlchemy · React · TypeScript · TanStack Query · Vite · nginx · Docker