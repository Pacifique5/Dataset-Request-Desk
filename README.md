# Dataset Request Desk

Internal platform that replaces the spreadsheet used to track robot-teleoperation
dataset requests: clients request episodes, operators fulfil them by assigning
episodes, clients accept or reject the delivery.

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16
- **Frontend:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS
- **Ops:** Docker Compose, GitHub Actions

Design decisions, trade-offs and what I would do next are in [NOTES.md](NOTES.md).

## Quick start (Docker)

```bash
docker compose up --build
```

This starts PostgreSQL, runs migrations, seeds the users and imports
`seed/episodes.csv` (all idempotent, safe to re-run), then starts the API and UI.

| | URL |
|---|---|
| Web UI | http://localhost:3000 |
| API docs (OpenAPI) | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

### Seed users

| Role | Email | Password |
|---|---|---|
| admin | admin@example.com | admin123 |
| operator | ops1@example.com | ops123 |
| operator | ops2@example.com | ops123 |
| client | client-a@example.com | client123 |
| client | client-b@example.com | client123 |

Passwords are stored as Argon2id hashes, never in plain text.

## Running locally without Docker

Requires Python 3.10+, Node 20+ and a local PostgreSQL.

```bash
# backend
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env             # macOS/Linux: cp; adjust DATABASE_URL if needed
createdb -U postgres dataset_desk
createdb -U postgres dataset_desk_test
alembic upgrade head
python -m app.cli seed-users
python -m app.cli import-episodes
uvicorn app.main:app --reload      # http://localhost:8000

# frontend (second terminal)
cd frontend
npm install
copy .env.example .env.local
npm run dev                        # http://localhost:3000
```

## Tests

```bash
cd backend && pytest               # needs the dataset_desk_test database
cd frontend && npm run lint && npm run typecheck && npm run build
```

Backend tests run against a **real PostgreSQL** (override with `TEST_DATABASE_URL`),
because the rules that matter most are enforced by the database: unique
constraints, CHECKs and row locks. The schema is rebuilt from the migrations at the
start of every run, and each test runs in a transaction that is rolled back.

What is covered, by priority:

| Area | Examples |
|---|---|
| Authorization | clients see only their own requests (404 for others'), role checks on every endpoint, deactivated users lose access immediately, admin self-lockout guard |
| Status transitions | every `(from, to, role)` combination (75 cases) checked against the transition table; delivery blocked until enough episodes are assigned; full lifecycle with rejection and rework; audit history |
| Assignment rules | only good/usable episodes, one request per episode (service check **and** DB constraint), all-or-nothing batches, assignments frozen outside `in_progress`, a real two-thread race with exactly one winner |
| Import | every messy-row category from the seed file, idempotent re-import, conflicting duplicates, bad headers, API permissions |
| Analytics | inclusive UTC date boundaries, top-5 ordering, median using the first delivery |

CI (`.github/workflows/ci.yml`) runs backend lint + tests on Postgres, frontend
lint/typecheck/format/build, and a Docker image build on every push and PR.

## Importing episodes

```bash
python -m app.cli import-episodes --file path/to/export.csv
```

or upload through the UI (**Import** page) / `POST /episodes/import`. The report lists
rows read, imported and skipped, with a reason and line number for every skipped row.
A large clean file for load testing can be generated with
`python seed/generate_episodes.py 200000 > seed/episodes_large.csv`.

## API overview

| Method | Path | Who |
|---|---|---|
| POST | `/auth/login`, `/auth/logout` · GET `/auth/me` | anyone / authenticated |
| GET, POST | `/requests` | list: all roles (clients see their own) · create: client |
| GET | `/requests/{id}` | owner client, staff |
| POST | `/requests/{id}/transitions` | role that owns the step |
| GET, POST | `/requests/{id}/assignments` | view: owner client, staff · assign: staff |
| DELETE | `/requests/{id}/assignments/{episode_id}` | staff |
| GET | `/episodes` · POST `/episodes/import` | staff |
| GET | `/analytics?from=YYYY-MM-DD&to=YYYY-MM-DD` | staff |
| GET, POST, PATCH | `/users` | admin |
| GET | `/health` | anyone |

Errors always have the shape `{"detail": "...", "code": "..."}`. Every request is
logged as one JSON line with method, path, status, duration and user id.

## Repository layout

```
backend/
  app/api/        HTTP layer (routes, auth dependencies)
  app/services/   domain rules: workflow, assignments, import, analytics
  app/models/     SQLAlchemy tables
  app/schemas/    Pydantic request/response models
  alembic/        migrations
  tests/
frontend/
  src/app/        pages (App Router)
  src/components/ shared UI
  src/lib/        typed API client, types
seed/             provided seed data
```
