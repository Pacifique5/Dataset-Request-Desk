# Frontend — Dataset Request Desk

Next.js 16 (App Router) + TypeScript + Tailwind CSS v4.

## Layout

```
src/
  app/          routes (App Router)
  components/   reusable UI
  lib/api.ts    typed fetch client (ApiError, JSON handling)
  lib/types.ts  domain types mirroring the backend schemas
```

Browser requests go to `/api/*`, which `next.config.ts` rewrites to the FastAPI
backend (`API_URL`). The app and API are therefore same-origin: no CORS, and the
auth cookie can be `HttpOnly` + `SameSite=Lax`.

## Run locally

```bash
cd frontend
npm install
copy .env.example .env.local     # macOS/Linux: cp
npm run dev                      # http://localhost:3000
```

## Checks

```bash
npm run lint
npm run typecheck
npm run build
```
