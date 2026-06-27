# Spec: 006-production-readiness

## Problem

The codebase is functionally complete (backend API, frontend SPA,
auth, embed tokens, responsive iframe sizing, 58 tests passing), but
the artifacts needed to actually deploy it to production are
incomplete or missing:

- No Dockerfile for the backend (only the dev `docker-compose.yml`
  for Postgres).
- No production docker-compose file that brings up the API + the DB
  with healthchecks, restart policy, and proper env wiring.
- No startup script that runs `alembic upgrade head` before
  `uvicorn`.
- The backend does not emit `Strict-Transport-Security`,
  `X-Content-Type-Options`, or `Referrer-Policy` headers.
- The frontend `environment.prod.ts` ships with the dev
  `apiBaseUrl`, so `ng build --configuration production` would call
  `http://localhost:8000/v1` from the production bundle.
- The frontend has no Dockerfile and no SPA-served artifact.
- No `PRODUCTION.md` checklist.
- No explicit `requirements.txt` for production (the project only
  declares deps in `pyproject.toml`, which works for editable
  installs but is fragile for container builds).
- A stray `backend/dev.db` from earlier auditing is committed to
  the working tree (gitignored but physically present).

This change adds the deployable artifacts and configuration without
introducing any new behavior in the application code.

## Goals

- Add a multi-stage `backend/Dockerfile` that builds the wheel in a
  builder stage and runs uvicorn in a slim runtime stage.
- Add a `backend/start.sh` that runs `alembic upgrade head` and then
  execs `uvicorn`.
- Add a `requirements.txt` (and `requirements-dev.txt`) with pinned
  versions, regenerated from the venv.
- Add a `docker-compose.yml` for production (renamed from the dev
  one, or kept side-by-side as `docker-compose.dev.yml`) that brings
  up the API + DB + optional Adminer with proper healthchecks,
  restart policy, and an `env_file`.
- Add `app/middleware/security_headers.py` that injects HSTS,
  X-Content-Type-Options, Referrer-Policy, and tighter CSP on every
  response (HSTS only when the request scheme is HTTPS).
- Wire the security-headers middleware in `main.py`.
- Add `frontend/Dockerfile` (multi-stage node + nginx) and
  `frontend/nginx.conf` that serves the SPA with SPA fallback,
  gzip, and the security headers at the proxy layer (CSP stays at
  the backend so it can be regenerated per response).
- Configure Angular `fileReplacements` so `environment.prod.ts` is
  the production env file.
- Update `environment.prod.ts` to be a placeholder that production
  builds override.
- Add `PRODUCTION.md` with the full deploy checklist.
- Remove `backend/dev.db` from the working tree (the file is
  gitignored, so this is a cleanup step).
- Update `api-rest`, `auth`, and `frontend-angular` contracts to
  reflect the production headers and configuration.
- Update `specs/manifest.yml` to add `006-production-readiness` as
  the active change.

## Non-Goals

- **No HTTPS termination** at the reverse-proxy layer. PRODUCTION.md
  documents that nginx / Caddy / a cloud LB must terminate TLS. The
  code-only scope (per `004`) keeps proxy config out of the repo.
- **No rate limiting.** Still delegated to the deployment layer
  (Cloudflare, AWS WAF, etc.).
- **No monitoring / observability** (Prometheus, Sentry, OpenTelemetry).
- **No multi-environment promotion** (no staging/prod separation
  beyond `docker-compose.yml` vs `docker-compose.dev.yml`).
- **No CI/CD pipeline.** Documented as out of scope; deploy is
  operator-driven via `docker compose pull && docker compose up -d`.
- **No new application behavior.** This change adds deployable
  artifacts and security headers only.

## Requirements

### Backend artifacts

- **R1.** `backend/Dockerfile` uses a multi-stage build:
  - Builder: `python:3.12-slim` + `pip install --no-cache-dir` of the
    wheel and `requirements.txt`.
  - Runtime: `python:3.12-slim`, non-root user, `start.sh` as
    entrypoint, exposes `8000`, `HEALTHCHECK` against `/healthz`.
- **R2.** `backend/start.sh`:
  - Runs `alembic upgrade head` against `$DATABASE_URL`.
  - Execs `uvicorn app.main:app --host 0.0.0.0 --port 8000
    --workers "${API_WORKERS:-2}" --proxy-headers --forwarded-allow-ips=*`.
- **R3.** `backend/requirements.txt` is generated from the working
  venv and pinned to exact versions.
- **R4.** `backend/requirements-dev.txt` adds pytest, pytest-asyncio,
  httpx (already in `pyproject.toml[dev]` but also pinned here for
  container builds that install dev deps).

### Security headers

- **R5.** `backend/app/middleware/security_headers.py` adds to every
  response:
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: no-referrer`
  - `Strict-Transport-Security: max-age=63072000; includeSubDomains`
    (only when `request.url.scheme == "https"`).
  - Keeps the existing `Content-Security-Policy: frame-ancestors
    <FRAME_ANCESTORS>` and `X-Frame-Options: ALLOW-FROM
    <FRAME_ANCESTORS>` headers.
- **R6.** `backend/app/main.py` registers `SecurityHeadersMiddleware`
  alongside `FrameAncestorsMiddleware`.

### Frontend artifacts

- **R7.** `frontend/Dockerfile` (under `src/dist/` after build):
  - Builder: `node:20-alpine` + `npm ci && npm run build --
    --configuration production`.
  - Runtime: `nginx:1.27-alpine`, copies `nginx.conf` and the
    built `dist/` from the builder.
- **R8.** `frontend/nginx.conf`:
  - `try_files $uri $uri/ /index.html` for SPA fallback.
  - `gzip` for text assets.
  - Forwards `X-Forwarded-Proto` and `X-Forwarded-For` headers
    (the backend reads `proxy-headers`).
- **R9.** `angular.json` `production` configuration uses
  `fileReplacements` to swap `src/environments/environment.ts` for
  `src/environments/environment.prod.ts`.
- **R10.** `src/environments/environment.prod.ts` carries a
  placeholder `apiBaseUrl: ''` plus a clear `// TODO-PROD` comment;
  PRODUCTION.md explains the override.

### Compose

- **R11.** `docker-compose.yml` is the production compose. It
  brings up:
  - `db`: `postgres:16`, named volume, healthcheck.
  - `api`: built from `backend/Dockerfile`, depends on `db` being
    healthy, `env_file: .env`, restart `unless-stopped`, exposes
    `8000:8000`.
  - `adminer`: optional profile `tools`, exposes `8080:8080`.
- **R12.** `docker-compose.dev.yml` keeps the previous dev-only
  compose for local Postgres + Adminer without the API container.

### Documentation

- **R13.** `PRODUCTION.md` (root of the repo) walks through:
  - Pre-deploy checklist (env vars, secrets, secrets in transit).
  - Backend `docker compose up -d db api`.
  - Database migration (`alembic upgrade head`, automatic via
    `start.sh`).
  - Frontend build (`npm ci && npm run build -- --configuration
    production`) and `docker compose up -d web` (or static
    `dist/` behind any HTTPS proxy).
  - Smoke tests after deploy: `curl /healthz`, login, embed token,
    iframe at three sizes.
  - Rotating `JWT_SECRET` and `ADMIN_PASSWORD` (both require
    redeploy; rotating `JWT_SECRET` invalidates all live sessions).
  - Backups: `pg_dump` of the `escalabirras` database.
  - Logs: `docker compose logs -f api`.
- **R14.** `.env.example` documents `API_WORKERS` and
  `API_LOG_LEVEL` in addition to the existing vars.
- **R15.** `backend/README.md` points at `PRODUCTION.md`.

### Cleanup

- **R16.** `backend/dev.db` and any other accidental SQLite file
  under `backend/` are removed from the working tree.

### SDD

- **R17.** `specs/contracts/api-rest/contract.md` gains a
  "Production security headers" subsection.
- **R18.** `specs/contracts/auth/contract.md` `Configuration` table
  is updated.
- **R19.** `specs/contracts/frontend-angular/contract.md` Configuration
  subsection references the fileReplacements + production override.
- **R20.** `specs/manifest.yml` lists `006-production-readiness` as
  active.

## Acceptance Criteria

- **AC1.** `pytest backend -v` reports 58/58 passing (no
  regression).
- **AC2.** `tsc --noEmit -p tsconfig.app.json` exits 0.
- **AC3.** `ng build --configuration production --output-path
  /tmp/...` succeeds and uses `fileReplacements` to swap the env
  file.
- **AC4.** `docker-compose config` validates the production
  compose.
- **AC5.** The production API image (built locally) boots and
  `/healthz` returns `{status:"ok"}` with all four security headers
  present.
- **AC6.** `alembic upgrade head` against a real Postgres succeeds
  from a clean database.
- **AC7.** `PRODUCTION.md` exists and covers the checklist items in
  R13.
- **AC8.** No stray `*.db` files in `backend/`.