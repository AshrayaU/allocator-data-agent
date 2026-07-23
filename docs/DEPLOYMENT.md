# Deployment (CTO)

Production deployment of this companion app to Allocator's private Heroku instance.
**This is the CTO's job** — the app builder stops at handover.

Every block below is **copy-paste runnable** — no helper functions to define, every
`heroku`/`dnsimple` command is spelled out inline where it runs. Run the setup blocks
at the top first (0a auth → 0b variables → 0c secrets), then paste the numbered steps
in order. Blocks 0b/0c export everything the rest of the file uses, so **gather your
secrets once up front** (block 0c) rather than stopping mid-run to go generate an API
key. Commands are idempotent (`… || true`, existence checks) — safe to re-run if a
step half-finished. `$APP_NAME` is the frontend app / repo name; the backend app is
`$APP_NAME-backend`. (Heroku caps app names at 30 chars and `-backend` adds 8, so
`$APP_NAME` is ≤ 22 chars — enforced when the app was named.)

Prereqs installed: `heroku`, `dnsimple`, `dig`, `curl`.

> **Run this auth check FIRST — before anything else.** Every command below calls
> `heroku` or `dnsimple`; if either CLI isn't logged in, they all fail. This block
> just confirms a session exists (it does not matter *who* is logged in), and stops
> immediately if not.

```bash
# 0a. AUTH PREFLIGHT — must pass before any other block is run
heroku whoami   || { echo "✗ Heroku not authenticated — run: heroku login,   then re-run this block";       return 1 2>/dev/null || exit 1; }
dnsimple whoami || { echo "✗ DNSimple not authenticated — run: dnsimple auth login, then re-run this block"; return 1 2>/dev/null || exit 1; }
echo "✓ both CLIs authenticated — safe to continue"
```

```bash
# 0b. Set variables — the ONLY line you edit is APP_NAME
export APP_NAME=allocator-qa          # e.g. fund-monitor
export HEROKU_TEAM=allocator-companion-apps
export DNS_ZONE=allocator.com

export BACKEND="$APP_NAME-backend"
export FRONTEND="$APP_NAME"
export BACKEND_FQDN="$BACKEND.$DNS_ZONE"
export FRONTEND_FQDN="$FRONTEND.$DNS_ZONE"
```

> **Gather every secret NOW, before you start.** These are the values you'd
> otherwise have to stop and go generate/look up in the middle of the run. Fill in
> the ones this app actually uses (check `backend/.env.example` for the full list)
> and leave the rest blank. Step 3 reads these variables, so you set them once here.

First generate the JWT signing secret as its **own** command and eyeball the output — do not trust
an inline `$(openssl …)` inside the export, which can evaluate to empty under some shells/quoting
and leave `APP_SECRET` blank:

```bash
openssl rand -hex 32          # prints 64 hex chars — copy them into APP_SECRET below
```

```bash
# 0c. Secrets this app actually uses (no SSO, no S3 — this app never touches AWS).
export APP_SECRET=""                             # PASTE the 64-char hex from `openssl rand -hex 32` above — must NOT be empty
export ALLOCATOR_ADMIN_SECRET_KEY=""             # Admin API (GET-only) — from Allocator admin
export ALLOCATOR_ADMIN_AUTH_TOKEN=""             # Admin API (GET-only) — from Allocator admin
export ANTHROPIC_API_KEY=""                      # Claude API — generate at console.anthropic.com
export GITHUB_TOKEN=""                            # FRONTEND build (@allocator/design-system): read-only PAT scoped to allctr/allocator-design-system only
```

---

## Checklist

- [ ] 0. **FIRST:** `heroku whoami` + `dnsimple whoami` pass (block 0a); variables + secrets exported (blocks 0b, 0c)
- [ ] 1. Both apps exist under the `allocator-companion-apps` team
- [ ] 2. Buildpacks set on both (monorepo first, language second)
- [ ] 3. Config vars set (backend + frontend) — `VITE_API_URL` set **before** first build
- [ ] 4. Postgres attached (if the app needs a DB), `pg:wait` done, `DATABASE_URL` present
- [ ] 5. Domains added + DNSimple CNAMEs created via CLI + resolving
- [ ] 6. ACM (auto-cert) issued on both domains
- [ ] 7. Repo connected in the Heroku dashboard, backend deployed first, then frontend
- [ ] 8. Smoke test green

---

## 0. Authenticate (preflight)

Already done at the very top (block **0a**) — the `heroku whoami` / `dnsimple whoami`
check must pass before any step here runs. If you skipped ahead, scroll up and run
0a first; otherwise every command below will fail on auth.

## 1. Create both apps

Both under the `allocator-companion-apps` team. `|| true` makes it a no-op if the app
already exists.

```bash
heroku create "$BACKEND"  --team "$HEROKU_TEAM" 2>/dev/null || true
heroku create "$FRONTEND" --team "$HEROKU_TEAM" 2>/dev/null || true

heroku apps:info -a "$BACKEND"  >/dev/null && echo "✓ $BACKEND ready"
heroku apps:info -a "$FRONTEND" >/dev/null && echo "✓ $FRONTEND ready"
```

## 2. Buildpacks (monorepo first, language second)

The `lstoll/heroku-buildpack-monorepo` buildpack reads `APP_BASE` to pick the
subdirectory. `heroku buildpacks:clear` first makes this re-runnable in the right order.

```bash
heroku buildpacks:clear -a "$BACKEND"
heroku buildpacks:add -a "$BACKEND" https://github.com/lstoll/heroku-buildpack-monorepo
heroku buildpacks:add -a "$BACKEND" heroku/python

heroku buildpacks:clear -a "$FRONTEND"
heroku buildpacks:add -a "$FRONTEND" https://github.com/lstoll/heroku-buildpack-monorepo
heroku buildpacks:add -a "$FRONTEND" heroku/nodejs
```

## 3. Config vars

Backend — always-set vars first, then the secrets from block 0c (only the ones you
filled in). Everything reads the variables you already exported, so there's nothing
to paste by hand here.

Always-required backend vars. The guard on the first line **stops the deploy** if `APP_SECRET` is
empty — an empty JWT signing key is a silent killer: SSO/login decrypt fine but every request dies
at the final `jwt.encode` with `InvalidKeyError: HMAC key must not be empty`.

```bash
[ -n "$APP_SECRET" ] || { echo "✗ APP_SECRET is empty — go back to block 0c and paste the openssl output"; return 1 2>/dev/null || exit 1; }

heroku config:set -a "$BACKEND" APP_BASE=backend SERVER_TYPE=production APP_SECRET="$APP_SECRET" ALLOCATOR_API_BASE=https://secure.allocator.com/admin/api CORS_ORIGINS="https://$FRONTEND_FQDN"

# Confirm it actually landed (should print 64 hex chars, not a blank line):
heroku config:get APP_SECRET -a "$BACKEND"
```

Then the secrets from block 0c — each runs only if you filled that value in:

```bash
[ -n "$ALLOCATOR_ADMIN_SECRET_KEY" ] && heroku config:set -a "$BACKEND" ALLOCATOR_ADMIN_SECRET_KEY="$ALLOCATOR_ADMIN_SECRET_KEY"
[ -n "$ALLOCATOR_ADMIN_AUTH_TOKEN" ] && heroku config:set -a "$BACKEND" ALLOCATOR_ADMIN_AUTH_TOKEN="$ALLOCATOR_ADMIN_AUTH_TOKEN"
[ -n "$ANTHROPIC_API_KEY" ] && heroku config:set -a "$BACKEND" ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"
```

> If `backend/.env.example` lists a secret not covered by block 0c, add it to 0c and
> to the lines above. Don't set `DATABASE_URL` by hand — the addon injects it in step 4.
> Re-running `config:set` is safe; it overwrites in place.

Frontend:

```bash
heroku config:set -a "$FRONTEND" APP_BASE=frontend SERVER_TYPE=production VITE_API_URL="https://$BACKEND_FQDN/api"
[ -n "$GITHUB_TOKEN" ] && heroku config:set -a "$FRONTEND" GITHUB_TOKEN="$GITHUB_TOKEN"
```

> `VITE_API_URL` is baked into the bundle at Vite **build** time — it must be set
> before the first deploy (step 7). Changing it later requires a rebuild, not just
> a `config:set`.
>
> **`GITHUB_TOKEN` is required if this app uses `@allocator/design-system`** — the
> frontend build clones that private repo, and the `heroku-prebuild` script uses this
> token to authenticate. It's a read-only PAT scoped to `allctr/allocator-design-system`
> only. Without it, the first frontend build fails on `npm install`.

## 4. Database (only if the app needs one)

Skip the whole step if the app has no server-side persistence. `|| true` skips the
attach if a DB is already there; `pg:wait` blocks until provisioning finishes (async).

```bash
heroku addons:create -a "$BACKEND" heroku-postgresql:essential-0 2>/dev/null || true
heroku pg:wait -a "$BACKEND"
heroku config:get -a "$BACKEND" DATABASE_URL
```

`pg:wait` blocks until provisioning finishes (async). The last line should print a
`postgres://…` URL — if it's blank, run `heroku pg:info -a "$BACKEND"` to check.

## 5. Domains + DNS (Heroku → DNSimple → wait for propagation)

DNS is created **from the command line with the `dnsimple` CLI — never by hand in the
DNSimple dashboard**. Do it one app at a time, in two steps: first print the DNS target
Heroku assigns, then paste that target into the `dnsimple` command. No JSON, no piping.

**Backend — step 1: add the domain and print its target.**

```bash
heroku domains:add -a "$BACKEND" "$BACKEND_FQDN" 2>/dev/null || true
heroku domains -a "$BACKEND"
```

That prints a table. Copy the **DNS Target** for `$BACKEND_FQDN` — it looks like
`something.herokudns.com`.

**Backend — step 2: create the CNAME, pasting that target after `--content`.**

```bash
dnsimple records create "$DNS_ZONE" --name "$BACKEND" --type CNAME --content PASTE_BACKEND_TARGET_HERE --ttl 3600
```

**Frontend — step 1: add the domain and print its target.**

```bash
heroku domains:add -a "$FRONTEND" "$FRONTEND_FQDN" 2>/dev/null || true
heroku domains -a "$FRONTEND"
```

Copy the **DNS Target** for `$FRONTEND_FQDN`.

**Frontend — step 2: create the CNAME, pasting that target after `--content`.**

```bash
dnsimple records create "$DNS_ZONE" --name "$FRONTEND" --type CNAME --content PASTE_FRONTEND_TARGET_HERE --ttl 3600
```

Wait until both resolve (re-run if it prints nothing yet):

```bash
until dig +short CNAME "$BACKEND_FQDN" | grep -q .; do sleep 10; done; echo "✓ backend resolves"
until dig +short CNAME "$FRONTEND_FQDN" | grep -q .; do sleep 10; done; echo "✓ frontend resolves"
```

> `--name` is the subdomain label (e.g. `fund-monitor-backend`), not the full hostname.
> `--content` is the `something.herokudns.com` target you copied from the table above.

## 6. ACM (auto-cert) — enable, then wait for issuance

Only meaningful once step 5's DNS resolves (ACM validates over the live record). Enable
on both, then poll until each cert is issued.

Enable on both:

```bash
heroku certs:auto:enable -a "$BACKEND"
heroku certs:auto:enable -a "$FRONTEND"
```

Wait until each cert is issued (one line each — re-run if still pending):

```bash
until heroku certs:auto -a "$BACKEND" | grep -qi 'cert issued'; do sleep 15; done; echo "✓ backend cert issued"
until heroku certs:auto -a "$FRONTEND" | grep -qi 'cert issued'; do sleep 15; done; echo "✓ frontend cert issued"
```

## 7. Connect repo + first deploy (Heroku dashboard)

Do this in the dashboard, not the CLI:

1. Connect both apps to the GitHub repo, branch `current_production`.
2. Enable automatic deploys on both.
3. Manually trigger the first deploy — **backend first, then frontend** (Deploy tab → Manual deploy).
4. Confirm the backend release phase ran Alembic migrations cleanly in the build log.

> This app has no scheduled/recurring background work — the only sync path is the
> "Sync now" button in the UI (POST /api/sync), which runs in a background task
> within the web dyno. No Heroku Scheduler add-on is needed.

## 8. Smoke test

```bash
curl -fsS "https://$BACKEND_FQDN/api/healthz" && echo   # → {"status":"ok"}
heroku logs --tail -a "$BACKEND"                          # confirm `alembic upgrade head` ran clean

# Signing key present? A blank line here means every login will 500 with
# "HMAC key must not be empty" — set APP_SECRET (step 3) before going further.
heroku config:get APP_SECRET -a "$BACKEND" | grep -qE '^.{32,}$' && echo "✓ APP_SECRET set" || echo "✗ APP_SECRET EMPTY"
```

Open `https://$FRONTEND_FQDN`, log in, and confirm in DevTools that Local Storage
has `session_token` and API calls carry `Authorization: Bearer …`. A **500** on login
(`/api/login` or `/api/auth/sso`) with `InvalidKeyError: HMAC key must not be empty` in the backend
logs means `APP_SECRET` is empty — the single most common cause is inlining `$(openssl rand -hex 32)`
into `config:set` and having the shell expand it to nothing. Fix per step 3 and retry.
