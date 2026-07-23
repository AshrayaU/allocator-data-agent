# allocator-qa backend

FastAPI backend for `allocator-qa`. Connects to a Postgres database, authenticates
via Allocator's `/whoami` endpoint, and issues HS256 JWTs for subsequent requests.

## Prerequisites

- Python 3.12 (`pyenv install 3.12`)
- PostgreSQL running locally
- An `.env` file (see below)

## First-time setup

```bash
# 1. Create your local .env
cp .env.example .env
# Fill in DATABASE_URL and APP_SECRET at minimum.
# e.g. DATABASE_URL=postgresql+psycopg://localhost/allocator-qa_dev
#      APP_SECRET=$(openssl rand -hex 32)

# 2. Install deps, create the DB, run migrations
bin/deploy
```

## Running the server

```bash
bin/server start     # daemonize uvicorn on port 8001
bin/server stop
bin/server status
bin/server run       # foreground (blocking) — useful for debugging
```

Logs are written to `.run/server.log`. Tail them with:

```bash
bin/logs
```

## Database management

```bash
bin/db migrate       # alembic upgrade head (creates DB automatically in dev)
bin/db seed          # load reference data (idempotent)
bin/db localize      # pull a live dump from Heroku (dev only)
```

## Running background tasks

```bash
bin/task <task_name>   # runs tasks/<task_name>.py's run() function
```

## API

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET    | `/api/healthz`    | public  | Health check |
| POST   | `/api/login`      | public  | Verify credentials, receive JWT |
| GET    | `/api/auth/config`| public  | Auth configuration for the frontend |
| GET    | `/api/things`     | required | List things |
| POST   | `/api/things`     | required | Create a thing |
| DELETE | `/api/things/:id` | required | Delete a thing |

## Environment variables

See `.env.example` for the full list. The required variables are:

- `DATABASE_URL` — Postgres connection string
- `APP_SECRET` — HS256 JWT signing secret (`openssl rand -hex 32`)
- `SERVER_TYPE` — `dev` locally, `production` on Heroku
