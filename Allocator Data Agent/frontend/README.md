# allocator-qa — Frontend

Vite + React + TypeScript SPA. Talks to the backend exclusively over `/api`.

## First-time setup

```bash
cp .env.example .env
# Edit .env and set VITE_API_URL to point at your backend
bin/deploy
```

## Start the dev server

```bash
bin/server start
```

Then open http://localhost:5174.

## Stop

```bash
bin/server stop
```

## Deploy to Heroku

```bash
bin/deploy
```

`heroku-postbuild` in `package.json` runs `npm run build` automatically during push. Set `VITE_API_URL` in Heroku config vars before deploying:

```bash
heroku config:set VITE_API_URL=https://allocator-qa-backend.allocator.com/api --app allocator-qa
```

## Key conventions

- All HTTP requests go through `src/lib/api.ts` — no scattered `fetch()` in components.
- Auth token lives in `localStorage['session_token']`. `RequireAuth` wraps protected routes.
- Route paths are defined in `src/shared/routes.ts`. API URLs are in `src/lib/api.ts` `endpoints`.
- Styling comes from `@allocator/design-system`. It ships raw Tailwind source plus a preset, so the Tailwind + PostCSS toolchain (`tailwindcss`/`postcss`/`autoprefixer` + `tailwind.config.js`/`postcss.config.js`) is installed to compile it — all included in this scaffold. Use the design system's preset and `al-*` classes; don't define your own Tailwind theme or colours.
