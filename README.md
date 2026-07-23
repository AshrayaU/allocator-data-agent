# allocator-qa

A personal chat assistant for learning the investment-data domain: ask questions like
*"Who has the highest investment with us?"* and get answers grounded in Allocator's own
investor/fund data, with an LLM (Claude) explaining domain terminology along the way.

An Allocator companion app. Frontend (Vite/React) + backend (FastAPI) monorepo.

## Run locally

1. Copy `backend/.env.example` → `backend/.env` and `frontend/.env.example` → `frontend/.env`; fill in values. Generate `APP_SECRET` with `openssl rand -hex 32`.
2. `bin/deploy` — install deps, create the local DB, run migrations.
3. `bin/server start` — start both halves. `bin/logs` to follow logs.

## What's included

- **Database (Postgres)** — `investors`, `funds` (local read-only cache, one row per remote record, keyed by `remote_id`), and `sync_runs` (audit trail of manual syncs).
- **Allocator Admin API** — read-only. `app/services/allocator_admin_service.py` is the *only* file that talks to it, and it is *only* imported by `app/services/data_sync.py` (never by the chat/LLM path). It is structurally GET-only: any attempted POST/PUT/PATCH/DELETE raises a clear `PermissionError` instead of silently sending the request. See `docs/ADMIN_API_NOTES.md` for the credential-order caveat and endpoint scope.
- **Manual sync, not scheduled** — the Admin API is called only when you click "Sync now" in the UI (`POST /api/sync`, runs in a background task so the click doesn't block). There is no recurring/scheduled sync.
- **AI (Claude)** — `POST /api/chat` answers questions using a single tool, `query_data` (`app/services/query_tool.py`), which runs a read-only, regex-validated `SELECT` against the local cache and never touches the live Admin API.
- **Standard Allocator auth** — login verifies credentials against `GET /whoami` on the Admin API and issues a local JWT; every data/chat/sync route requires it.
- **Internal-only protections** — `robots.txt` blocks indexing; ask the CTO about IP-allowlisting to office/VPN ranges if this ever needs the extra layer.
- **Not included, deliberately**: S3/file storage (this app has no files to persist and must never touch AWS), SSO, and a background-task scheduler (no recurring jobs — see above).

## Deployment

Production deployment is the CTO's job. See `docs/DEPLOYMENT.md` — set `APP_NAME` once and follow the checklist to create the Heroku apps, config, database, domains, and certs.

This app was built as a personal learning tool and has **not** been pushed to a shared
GitHub repo or deployed anywhere — see the note left in the conversation that built it
before doing either.

## Built by

Ashraya Udho — to learn Allocator's investment data model by asking it questions directly, with an LLM filling in the domain-education gaps.
