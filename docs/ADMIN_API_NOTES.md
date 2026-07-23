# Allocator Admin API — notes for this app

## Credential order — resolved

Two sources disagreed on which value is the Basic-auth username vs password:

- The live Swagger docs page (`secure.allocator.com/admin/api`) says: *"All
  endpoints require HTTP Basic Auth using SECRET_KEY (username) and Admin
  AuthToken (password) from Cms → Admin."*
- The companion-app-guide skill's vendored `allocator_admin_settings.md` /
  `allocator_admin_service.py` templates said the opposite: username = Admin
  AuthToken, password = `SECRET_KEY_FOR_ADMINS`.

Verified empirically against `GET /whoami` with real credentials: the live
Swagger docs were correct. `app/services/allocator_admin_service.py`'s
`_auth()` now sends `ALLOCATOR_ADMIN_SECRET_KEY` as username and
`ALLOCATOR_ADMIN_AUTH_TOKEN` as password.

## Schema uncertainty for investors/funds

The vendored `references/admin-api/openapi.json` (in the companion-app-guide
skill) documents `GET /investors`'s response as `data.investors: string[]` —
i.e. an array of plain strings, not objects. That's almost certainly a gap in
the spec's hand-written schema annotations rather than the real API behavior,
but it means `app/services/data_sync.py`'s `_normalize()` function is
deliberately defensive (falls back to treating a bare string as the whole
record) rather than assuming a confirmed object shape.

**Once real credentials are available**, run a manual sync and inspect a few
rows' `raw` JSONB column in Postgres (`select raw from investors limit 3;`)
to confirm the actual field names, then:

1. Tighten `_normalize()` in `app/services/data_sync.py` to pull out the real
   field names instead of guessing at `id` / `short_token` / `token` and
   `name` / `company_name`.
2. Consider promoting frequently-queried fields (e.g. whatever holds
   commitment/holding totals, if present) from `raw` into real typed columns
   via a new Alembic migration — the chat tool's SQL is much cleaner against
   `investors.total_commitment` than `investors.raw->>'total_commitment'`.

## Endpoints this app uses — and the many it deliberately never will

This app only ever calls two Admin API endpoints, both GET:

- `GET /investors`
- `GET /funds`

The full API has 102 endpoints across 34 groups (see the companion-app-guide
skill's `references/admin-api/admin-api-overview.md`), many of them
POST/PATCH/DELETE — e.g. `POST /cashflow_files/import`, `POST/PATCH/DELETE
/security_master/{id}`, `POST /holding_files/import`. None of those are wired
into `app/services/allocator_admin_service.py`, and that file's
`_AdminAPIClient` structurally refuses any non-GET verb even if a future edit
tried to add one — see the comments in that file.

If a future version of this app needs a holdings/cashflow view (e.g. for
"who has the highest investment with us" to reflect real commitment amounts
rather than just investor/fund names), the natural next endpoints to add —
still GET-only — are likely `GET /holding_totals/{fund_short_token}` and/or
`GET /cashflow_files` (list only, never the `/export` or `/import` actions on
that same resource).
