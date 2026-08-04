# CLAUDE.md

This file provides guidance to Claude Code (and contributors) when working in this repository.

## Overview

A "Meeting Minutes API" — a full-stack web app where a user uploads a meeting transcript and the system
asynchronously summarizes it into **a summary, action items, and decisions**. It showcases a composable
AI-provider layer (Mock → Groq → HuggingFace), an async job pipeline, JWT auth with role-based access,
and Docker-compose deployment. Suitable as a portfolio/resume project.

**Stack:** FastAPI · async SQLAlchemy 2.0 · PostgreSQL (asyncpg) · Redis · Celery · JWT (python-jose + passlib/bcrypt) ·
React 19 · Vite · Tailwind CSS v4 · axios · react-router v7.

```
React (frontend/) ── /api/v1 ──► FastAPI (src/app/) ──► Celery worker ──► Summarizer (Mock | Groq | HuggingFace)
                                      │                        │
                                      └── PostgreSQL ◄─────────┘   (Redis = queues, rate-limit, token blacklist, cache)
```

For a visual reference see [docs/architecture.svg](docs/architecture.svg).

## Repository layout

```
src/                         FastAPI backend package
  app/
    main.py                  App factory, lifespan, CORS, middleware, router mounting
    config.py                pydantic-settings singleton (env-driven)
    models.py                SQLAlchemy models + custom GUID type
    core/                    security (JWT/bcrypt), dependencies, redis cache, slowapi limiter, logging
    db/session.py            async SQLAlchemy engine + get_db dependency
    middleware/correlation.py  X-Correlation-ID request middleware + logging
    routes/                  auth, minutes, admin, health routers
    schemas/                 Pydantic request/response models (auth, minutes)
    services/                celery_app.py, summarizer.py (provider abstraction)
    tasks/summarize.py       Celery worker task (uses a sync psycopg2 engine)
frontend/                    React 19 + Vite + Tailwind v4 SPA
  src/
    main.jsx                 BrowserRouter > AuthProvider > App
    App.jsx                  Route definitions + role guards
    api/axios.js             axios instance (baseURL /api/v1, JWT + 401 interceptors)
    context/AuthContext.jsx  Auth state, localStorage tokens
    components/              Navbar, ProtectedRoute, MeetingCard, StatusBadge, Loader
    pages/                   Login, Dashboard, Upload, MinuteDetail, Admin
alembic/ + alembic.ini       DB migrations (initial schema; full-text search_vector)
tests/                       pytest (SQLite/aiosqlite; mocked Redis & Celery)
```

## Commands

All paths assume you are in the repo root unless noted.

### Backend (local, no Docker)
```bash
# 1. Set up env (copy .env.example to .env, fill required vars)
cp .env.example .env

# 2. Database: PostgreSQL + Redis must be running (or use Docker below).

# 3. Run API (dev) — PYTHONPATH must resolve the `app` package under src/
PYTHONPATH=src uvicorn app.main:app --reload --port 8000
# (run.sh does exactly this)

# 4. Celery worker (worker process) — consumes the summarize tasks
PYTHONPATH=src celery -A app.services.celery_app.celery_app worker --loglevel=info

# 5. Migrations
alembic upgrade head

# 6. Tests + lint
pytest                                  # SQLite-backed, mocks Redis/Celery
pytest --cov=app --cov-report=term-missing
ruff check src tests                     # lint
ruff format --check src                  # format check
```

### Frontend
```bash
cd frontend
npm install
npm run dev          # Vite dev server, proxies /api -> http://localhost:8000
npm run build        # production build -> dist/
npm run lint         # eslint
```

### Docker (full stack)
```bash
docker compose up --build          # db + redis + api + celery_worker + nginx
docker compose down                # stop
```
The compose hardcodes local dev credentials — see Security notes.

## Configuration (`src/app/config.py`)

`Settings` is a `pydantic-settings.BaseSettings` singleton, read from `.env` (`extra="ignore"`).

**Required (no default):**
- `SECRET_KEY` — JWT signing secret
- `DATABASE_URL` — async SQLAlchemy URL, e.g. `postgresql+asyncpg://user:pass@localhost:5432/meeting_minutes_db`
- `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` — Redis URLs (e.g. `redis://localhost:6379/0`)

**Optional (have defaults):**
- `REDIS_URL` (default `redis://localhost:6379/0`)
- `SUMMARIZER_TYPE` — `mock` (default) | `groq` | `huggingface`
- `ACCESS_TOKEN_EXPIRE_MINUTES` (60), `REFRESH_TOKEN_EXPIRE_DAYS` (7)
- `GROQ_API_KEY`, `HF_API_TOKEN` (empty by default)

> ⚠️ `.env.example` is incomplete — it does not document `GROQ_API_KEY`, `GROQ_MODEL`, `HF_API_TOKEN`, or the `POSTGRES_*` vars the app reads. See config.py for the authoritative list.

## Key flows

### Authentication (JWT)
- `POST /api/v1/auth/register` → creates user, returns access + refresh tokens.
- `POST /api/v1/auth/login` → token pair; rate-limited (`5/minute`) via slowapi.
- `POST /api/v1/auth/refresh` → decodes refresh (`type=="refresh"`), issues a new pair.
- `GET /api/v1/auth/me` → current user (any authed token — see `get_current_user`).
- `POST /api/v1/auth/logout` → blacklists the token's `jti` in Redis (TTL = remaining expiry).
- Tokens carry `sub` (user UUID as str), `type` (`access`|`refresh`), `jti`, `exp`, `iat`.
- `get_current_admin` wraps `get_current_user` and requires `role == "admin"`.

### Upload → summarize pipeline
1. `POST /api/v1/minutes/upload-text` → saves `MeetingMinutes(status="pending")`, creates a
   `Task` (`status="PENDING"`), enqueues `summarize_meeting_task.delay(...)`, returns 202 `{meeting_id, task_id, status}`.
2. Celery worker sets the meeting `status="processing"`, runs `get_summarizer().generate(text)`,
   stores `summary` / `action_items` / `decisions`, sets `status="completed"`. On failure: `failed` + `error`, retries up to 3× (delay 60s).
3. Frontend polls `GET /minutes/:id` every 4s until terminal (`completed`|`failed`).

**Summarizer providers** (`services/summarizer.py`, `BaseSummarizer` ABC → `{summary, action_items, decisions}`):
- `mock` (default) — pure-Python heuristic, **no API call**. Trigger words: `action/will/should/must` → action items; `decided/agreed/approved` → decisions.
- `groq` — Llama-3.3-70b via raw `requests` to Groq's OpenAI-compatible endpoint (`json_object` mode); transcript truncated to 8000 chars.
- `huggingface` — `facebook/bart-large-cnn` via HF Inference; transcript truncated to 1024 chars; returns only a summary (no action items/decisions).

### Minutes lifecycle
- `GET /minutes/` (paged), `GET /minutes/{id}`, `GET /minutes/{id}/status`, `DELETE /minutes/{id}` (soft delete via `deleted_at`).
- All minutes endpoints require auth and enforce **ownership** (403 on cross-user).
- List/get exclude soft-deleted rows (`deleted_at IS NULL`).

### Status values
`pending` → `processing` → `completed` | `failed`. Note: the `Task.status` is written as the uppercase `"PENDING"` on upload while the model default is lowercase `"pending"` (see [docs/PROJECT_REVIEW.md](docs/PROJECT_REVIEW.md)).

## Conventions

- **Async everywhere in the API**: async SQLAlchemy (`AsyncSession`) + `asyncpg`. Routers use `await db.execute(select(...))`.
- **Sync engine in Celery**: `tasks/summarize.py` builds a *synchronous* engine by string-replacing
  `postgresql+asyncpg` → `postgresql+psycopg2` (workers need sync).
- **GUID type**: custom SQLAlchemy `TypeDecorator` — PostgreSQL `UUID` / SQLite `CHAR(36)` — so tests run on SQLite.
- **Routers** live under `/api/v1` (except `/health`). Mounted in `main.py`.
- **Rate limiting** with slowapi: `@limiter.limit(...)` on sensitive routes (declared in `core/limiter.py`).
- **Correlation IDs** via `middleware/correlation.py`, logging JSON formatted (`core/logging.py`).
- **Soft deletes:** `MeetingMinutes.deleted_at`; list/get/delete filter on it.
- **No ORM `relationship()`s** — models are FK-only; joins are done manually via `select(...).join(...)`.

## Testing

Tests live in `tests/` and run against SQLite + aiosqlite (`test.db`), with Redis (`app.routes.auth.redis`)
and Celery (`summarize_meeting_task.delay`) mocked. Async tests use the `pytest-asyncio`-configured httpx ASGI client.
See `tests/conftest.py` for fixtures (auto-fixture `auth_headers` registers a user and returns bearer headers).

- `tests/test_auth.py` — register/login/ref/base, refresh, logout.
- `tests/test_minutes.py` — upload, unauthorized, get/status, cross-user 403, delete + 404.

## Notes / gotchas
- `settings.SUMMARIZER_TYPE` is a global singleton; the admin `/model/switch` route mutates it at runtime (process-wide, not persisted).
- The API technically accepts **text only** (no audio transcription yet); the `SUMMARIZER_TYPE` default is `mock` so no real AI is used unless configured.
- Frontend stores `refresh_token` but has **no refresh-then-retry** flow — an expired access token forces a hard `/login` redirect.