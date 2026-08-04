# Project Review — Meeting Minutes API

A consolidated report of **bugs**, **security concerns**, **engineering improvements**, and **feature ideas**
found during a full codebase review. Line references use the state at review time.

Priorities: 🔴 = fix first (correctness/security), 🟡 = should improve, 🟢 = nice to have / roadmap.

---

## 1. Bugs / correctness

### 🔴 1.1 `ProtectedRoute` admin-guard `ReferenceError` — **FIXED**
`frontend/src/components/ProtectedRoute.jsx`
- Line 5 destructured a **nonexistent** `isadmin` (lowercase) from `useAuth()`; `AuthContext` exposes `isAdmin`.
- Line 9 referenced `isAdmin`, which was **not defined in scope** → `ReferenceError: isAdmin is not defined` whenever the `adminOnly` guard evaluated (non-admin hitting `/admin`, or an admin navigating to a protected route).
- Also made the admin-role check unreliable even when it didn't throw.
- **Fix applied:** `const { isAuthenticated, isAdmin } = useAuth();`.

### 🔴 1.2 `Task.status` case mismatch on upload
`src/app/routes/minutes.py` writes `Task(status="PENDING")` (uppercase) while the model default and the rest of the
app use lowercase `"pending"`. `StatusBadge`/status handling keys off lowercase → the initial task state can render as
"unknown" and status compares are inconsistent.
- **Fix:** use `"pending"` (and/or centralize statuses in a shared enum/constant).

### 🟡 1.3 Wrong error message + inconsistent summarizer allow-list in admin `model/switch`
`src/app/routes/admin.py`
- The rejection branch returns the message **"Invalid token type"** (copy-paste error) instead of something like
  "Invalid summarizer type".
- The endpooint only accepts `mock` / `huggingface` and **rejects `groq`** even though `GroqSummarizer` exists.
  The allow-list should match the factory in `services/summarizer.py`.

### 🟡 1.4 Non-deterministic pagination
`GET /api/v1/minutes/` has no `.order_by(...)` → row order (and thus page contents) is unstable across requests.
- **Fix:** add an explicit sort (e.g. `order_by(MeetingMinutes.created_at.desc())`).

### 🔴 1.5 Refresh token can authenticate as an access token
`src/app/core/dependencies.py` — `get_current_user` decodes the token and uses `payload["sub"]` but never checks
`payload["type"]`. Any JWT signed with `SECRET_KEY` — **including a `refresh` token** — passes on access-protected routes.
- **Fix:** in `get_current_user`, require `payload.get("type") == "access"` (mirror what `/auth/refresh` already does for refresh tokens).

### 🟡 1.6 Logout blacklist (`jti`) is never enforced
`POST /api/v1/auth/logout` writes the token's `jti` to Redis with a TTL, but no dependency consults this blacklist.
A logged-out/revoked token remains valid until it expires.
- **Fix:** in `get_current_user` (per-request or via a fast dependency), reject tokens whose `jti` is present in the Redis key.

### 🟡 1.7 HuggingFace summarizer has no request timeout
`src/app/services/summarizer.py` — `GroqSummarizer` passes `timeout=...`; `HuggingFaceSummarizer` does not, so a hung
Inference call can stall the worker indefinitely.
- **Fix:** add an explicit `timeout` to the HF `requests.post(...)`.

---

## 2. Security

### 🔴 2.1 Live secrets in the working tree (gitignored but real)
A real `GROQ_API_KEY` (and real `SECRET_KEY`) sit in the on-disk `.env`. It's correctly gitignored, but a portfolio
repo can leak these trivially (screenshots, ZIP export, `docker-compose` captures). **Rotate/remove the Groq key and
use a placeholder for `SECRET_KEY` in any shared copy.**

### 🔴 2.2 Hardcoded DB credentials in tracked config
- `docker-compose.yml` — `DATABASE_URL`/`REDIS_URL`/`CELERY_*` block hardcodes `meetinguser:meetingpass`.
- `alembic.ini` line 89 — `sqlalchemy.url = postgresql+psycopg2://meetinguser:meetingpass@...` fallback.
- **Fix:** drive all of these from env / `.env` (`${POSTGRES_USER}` etc.), and make `alembic.ini`'s URL a non-secret or read from env.

### 🟡 2.3 CORS misconfiguration
`src/app/main.py` sets `allow_origins=["*"]` together with `allow_credentials=True` — invalid per the CORS spec with
credentials and needlessly permissive. Scope it to the frontend origin(s) and drop credentials (bearer tokens don't use cookies).

### 🟡 2.4 Admin `model/switch` mutates a global singleton
`admin.py` does `settings.SUMMARIZER_TYPE = ...` at runtime — a process-wide side effect that is **not persisted**
(restart resets it), not concurrency-safe, and surprising in a stateless API. Prefer a persistent setting (DB row / Redis key)
read by the worker at execution time.

---

## 3. Scope / engineering improvements

- **🔴 No README.** Root `README.md` is 23 bytes (a heading). The strong architecture artifacts
  (`docs/architecture.svg`, `architecture_reference.html`, `auth_jwt_lifecycle.html`, `meeting_minutes_api_architecture.svg`,
  `deployment_topology_ec2.svg`) are orphaned/unlinked. Write a README that pitches the project, links the diagrams, and
  documents setup — this is the single biggest visibility win for a resume repo.
- **🟡 `.env.example` incomplete.** Missing `GROQ_API_KEY`, `GROQ_MODEL`, `HF_API_TOKEN`, `POSTGRES_*` — an evaluator
  can't fully bootstrap from it. Mirror the fields in `config.py`.
- **🟡 No token-refresh flow on the frontend.** `refresh_token` is stored but never used (`context/AuthContext.jsx`,
  `api/axios.js`); a 401 does a hard `window.location` to `/login` instead of refresh-then-retry. Implement an axios
  401 handling that calls `/auth/refresh`, retries the request, and only logs out on refresh failure (single-flight guard).
- **🟡 Frontend not deployable in the stack.** No frontend Dockerfile; compose `nginx` proxies to the API but nothing
  serves the SPA bundle. Add a frontend build stage (multi-stage Dockerfile or build + serve via nginx) and generate SSL-less TLS config.
- **🟡 Frontend has no CI/lint/test wiring.** CI job covers backend lint+test only. Add a frontend job (`npm ci && npm run lint && npm run build`, plus unit/RTL smoke tests).
- **🟡 `requirements.txt` mixes runtime + dev tools.** black/ruff/pytest/mypy/coverage ship into the runtime image.
  Split into `requirements.txt` (runtime) + `requirements-dev.txt`, and `pip install` only runtime in the Dockerfile.
- **🟡 Not installable as a package.** `pyproject.toml` has no `[project]` metadata → no `pip install -e .`, no version
  metadata. Add minimal `[project]` fields (name, version, dependencies from requirements) for a PEP 621 package.
- **🟡 Committed noise artifacts.** `test.db` and `coverage.xml` are tracked at root; `.dockerignore` excludes them but they
  still pollute the repo. Add to `.gitignore` and `git rm --cached`.
- **🟡 No coverage gate.** CI runs `pytest --cov` but has no `fail_under`; add a threshold (e.g. 70–80%) so regressions trip CI.
- **🟢 No ORM relationships.** Models are FK-only with manual `select(...).join(...)`. Adding `relationship()`s + lazy/joined
  loading would simplify queries (and is a good talking point in interviews).
- **🟢 No centralized status values.** `pending`/`PENDING`/`processing`/`completed`/`failed` are ad-hoc strings across
  backend models, routes, and frontend `StatusBadge`. Centralize as a Python `enum` and a JS constant map.
- **🟢 Full-text search migration exists but is unused.** Alembic added a `search_vector tsvector` GENERATED column + GIN
  index, and `GET /minutes/` never queries it. Wiring it to a `?q=` filter on the Dashboard makes the FTS real (see 4.x).

---

## 4. Feature ideas (roadmap)

Pick the highest-leverage ones for a fresher portfolio; each is roughly independent.

### 🔴 4.1 Real audio transcription → the core claim becomes true
The project is pitched as "transcribe + summarize," but input is **text-only** and the default provider is a no-API
`mock`. Add audio/video upload → **Whisper transcription** (e.g. Groq's `whisper-large-v3` via its OpenAI-compatible
endpoint, reusing the existing `requests` pattern and `GROQ_API_KEY`). Then the `upload` → *transcription* → *summarization*
>>> pipeline is genuinely AI-driven. (Medium effort: new upload field, transcription step, frontend file input for media.)

### 🟡 4.2 Add an Anthropic Claude summarizer
`services/summarizer.py` is a clean `BaseSummarizer` ABC — add a `ClaudeSummarizer` hitting the Anthropic Messages API
(e.g. `claude-haiku-4-5` or `claude-sonnet-5`) with the same JSON contract. Diversifies providers and is a strong
"LLM integration" bullet for the resume. (Small: ~30 lines + a key/config + allow-list update.)

### 🟡 4.3 Full-text search on the Dashboard
Leverage the already-migrated `search_vector` tsvector/GIN index: extend `GET /minutes/` with a `?q=` that queries the
vector, and add a search input to `Dashboard`. Showcases Postgres FTS with minimal new work.

### 🟡 4.4 Robust session handling
Implement real token refresh (axios 401 → `/auth/refresh` → retry) + a "Remember me" that persists the refresh token vs
session-only. Closes the biggest UX gap and a frequent interview question.

### 🟢 4.5 Export capabilities
Add "Download" on `MinuteDetail`: render minutes as **Markdown / PDF** (e.g. `weasyprint` or a lightweight HTML→PDF)
and a CSV of action items. Small, user-visible, and easy to demo.

### 🟢 4.6 Admin hardening & model telemetry
Persist the selected summarizer (instead of mutating the global), and record per-meeting metadata (provider used, latency,
char counts, success/failure) so the Admin panel can show adoption/quality stats. Turns the admin page into a real value-add.

### 🟢 4.7 Observability polish
Structured JSON logging already exists (`core/logging.py`); add:
- a request enricher (method, path, status, duration) in the correlation middleware,
- richer `/health` (per-service breakdown instead of just overall 503),
- structured error responses (consistent `{detail}`) rather than ad-hoc strings,
- optional OpenTelemetry/traces for the async pipeline.

### 🟢 4.8 Test expansion
- Backend: add cases for ownership edge cases, refresh-token-does-not-authenticate (see §1.5), status-case consistency,
  summarizer provider behavior via mocks, and the blacklist path (§1.6).
- Frontend: add Vitest + React Timing Library smoke tests for ProtectedRoute admin redirects, Login toggle, Dashboard render.
- CI: add the frontend job (scope §3) and a coverage `fail_under`.

---

## 5. Suggested action order
1. **Do first (small, high value):** §1.2, §1.3, §1.4, §1.5 (security + correctness), §2.2 (env-driven creds), write the README (§3), complete `.env.example` (§3).
2. **Then (medium):** §1.6 blacklist enforcement, §2.4 persistent summarizer config, token-refresh UX (§3/§4.4), frontend CI + Dockerfile (§3).
3. **Roadmap (bigger feature showcases):** §4.1 audio transcription, §4.2 Claude provider, §4.3 full-text search, §4.5 export.