# Meeting Minutes API

A full-stack application that turns meeting transcripts into structured minutes. Paste or upload a transcript, and an async worker pipeline summarizes it into a **summary, action items, and decisions** — powered by a pluggable AI layer, served through a React dashboard, and secured with JWT auth.

Built as a portfolio project demonstrating a **polyglot persistence** architecture: PostgreSQL for relational auth data, MongoDB for document-style meeting data, with an async Celery job queue connecting them.

## ✨ Features

- **Upload transcripts** — paste text, pick a file, or drag-and-drop
- **Async summarization** — Celery worker processes jobs with retries; poll the status live
- **Pluggable AI providers** — Mock (offline), Groq (Llama-3.3-70B), HuggingFace (bart-large-cnn); switch via the admin panel
- **Full-text search** — MongoDB `$text` index powers `?q=` search on your meetings
- **JWT auth** — access + refresh tokens, logout revocation via Redis blacklist
- **Role-based access** — user dashboard + admin panel (stats, model switching)
- **Ownership + soft-delete** — users only see their own meetings; deletes are recoverable
- **Dockerized** — one `docker compose up` brings up Postgres, MongoDB, Redis, API, Celery worker, nginx

## 🏗️ Architecture

```
React (frontend/) ── /api/v1 ──► FastAPI (src/app/) ──► Celery worker ──► Summarizer (Mock | Groq | HuggingFace)
                                      │                        │
                                      ├── PostgreSQL ◄─────────┘   (Redis = queues, rate-limit, token blacklist)
                                      └── MongoDB  (meetings, tasks, $text search)
```

**Polyglot persistence:**
- **PostgreSQL** — `users` + auth (relational: unique email, roles, transactions)
- **MongoDB** — `meetings` + `tasks` (documents: transcript + nested arrays, growing schema)

## 🛠️ Tech Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, async SQLAlchemy (asyncpg), Pydantic v2 |
| Databases | PostgreSQL 15, MongoDB 7 (motor + pymongo) |
| Queues | Celery + Redis |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Frontend | React 19, Vite, Tailwind CSS v4, axios, react-router v7 |
| Infra | Docker Compose, nginx, GitHub Actions CI |

## 🚀 Quickstart (Docker)

```bash
# 1. Configure env
cp .env.example .env
#    fill in SECRET_KEY, DATABASE_URL, CELERY_*; add GROQ_API_KEY for real AI

# 2. Start the full stack
docker compose up --build
```

- API + Swagger docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
- nginx: http://localhost:80

> Note: if you already run Postgres on 5432, the compose `db` service uses **5433** on the host.

## 🧑‍💻 Local development

### Backend
```bash
PYTHONPATH=src uvicorn app.main:app --reload --port 8000   # API
PYTHONPATH=src celery -A app.services.celery_app worker --loglevel=info   # worker
alembic upgrade head                                        # migrations
```

### Frontend
```bash
cd frontend
npm install
npm run dev          # proxies /api -> localhost:8000
```

### Tests
```bash
# MongoDB must be running (docker compose up -d mongo)
MONGODB_URL=mongodb://localhost:27017 PYTHONPATH=src pytest tests/ -q
```

## 📚 API Overview

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | — | Create user + get tokens |
| POST | `/api/v1/auth/login` | — | Login (rate-limited) |
| POST | `/api/v1/auth/refresh` | refresh | Rotate token pair |
| GET | `/api/v1/auth/me` | access | Current user |
| POST | `/api/v1/auth/logout` | access | Revoke token |
| POST | `/api/v1/minutes/upload-text` | access | Upload transcript (202, async) |
| GET | `/api/v1/minutes/` | access | List + `?q=` search + pagination |
| GET | `/api/v1/minutes/{id}` | access | Get minutes |
| GET | `/api/v1/minutes/{id}/status` | access | Poll summarize status |
| DELETE | `/api/v1/minutes/{id}` | access | Soft delete |
| GET | `/api/v1/admin/stats` | admin | Dashboard stats |
| POST | `/api/v1/admin/model/switch` | admin | Switch summarizer |
| GET | `/health` | — | Health check (DB + Redis + Mongo) |

## ⚙️ Environment Variables

See [.env.example](.env.example). Key ones:

| Variable | Required | Purpose |
|---|---|---|
| `SECRET_KEY` | ✅ | JWT signing |
| `DATABASE_URL` | ✅ | Postgres (asyncpg) |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | ✅ | Redis URLs |
| `MONGODB_URL` / `MONGODB_DB` | ⚠️ | Mongo (defaults to localhost) |
| `SUMMARIZER_TYPE` | — | `mock` (default) / `groq` / `huggingface` |
| `GROQ_API_KEY` | — | For Groq summarizer |

## 📁 Project Structure

```
src/app/
  main.py              FastAPI app + lifespan
  config.py            Settings (env-driven)
  models.py            User (Postgres) — meetings/tasks moved to Mongo
  core/                security (JWT), dependencies, cache, limiter, logging
  db/                  session.py (Postgres), mongo.py (Mongo), mongo_indexes.py
  routes/              auth, minutes, admin, health
  schemas/             Pydantic models
  services/            celery_app, summarizer (Mock | Groq | HuggingFace)
  tasks/               summarize (Celery worker, sync pymongo)
frontend/src/
  pages/               Login, Dashboard, Upload, MinuteDetail, Admin
  components/          Navbar, ProtectedRoute, MeetingCard, StatusBadge, Loader
  context/             AuthContext (JWT in localStorage)
  api/                 axios instance
tests/                 pytest: auth (SQLite) + minutes (real Mongo)
```

## 🤝 Contributing / Notes

- All six original backend bugs were fixed and documented in `docs/PROJECT_REVIEW.md` (refresh-token auth, status enums, admin switch, pagination order, JWT blacklist, HF timeout).
- The frontend stores tokens in `localStorage` (session-only for a portfolio demo).

