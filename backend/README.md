# Backend — Dataset Request Desk API

FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL.

## Layout

```
app/
  main.py            app factory (middleware, routers)
  api/router.py      registers all route modules
  api/routes/        HTTP layer only: parse input, call a service, shape output
  services/          domain rules (workflow, assignments, import, analytics)
  models/            SQLAlchemy ORM tables
  schemas/           Pydantic request/response models
  core/              config, logging, security
  db/                engine, session, declarative base
  middleware/        request logging
alembic/             migrations
tests/               pytest suite
```

## Run locally (no Docker)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements-dev.txt
copy .env.example .env           # then edit DATABASE_URL / JWT_SECRET
createdb dataset_desk            # or create it in pgAdmin
alembic upgrade head
uvicorn app.main:app --reload    # http://localhost:8000/docs
```

## Tests

```bash
pytest
```
