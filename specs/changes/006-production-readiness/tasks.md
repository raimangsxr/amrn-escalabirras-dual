# Tasks: 006-production-readiness

## Tasks

### Phase 0 — SDD

- [x] Update `specs/manifest.yml` (add `006-production-readiness`).
- [x] Update `specs/contracts/api-rest/contract.md` (production
      security headers + CORS prod note).
- [x] Update `specs/contracts/auth/contract.md` (Configuration
      table).
- [x] Update `specs/contracts/frontend-angular/contract.md`
      (Configuration subsection).
- [x] Write `specs/changes/006-production-readiness/spec.md`.
- [x] Write `specs/changes/006-production-readiness/plan.md`.
- [x] Write this task list.
- [x] Write `specs/changes/006-production-readiness/context-pack.md`.

### Phase 1 — Backend artifacts

- [x] Add `backend/app/middleware/security_headers.py`.
- [x] Wire the middleware into `backend/app/main.py`.
- [x] Add `backend/tests/test_security_headers.py`.
- [x] Add `backend/start.sh` (alembic upgrade + uvicorn).
- [x] Add `backend/Dockerfile` (multi-stage).
- [x] Generate `backend/requirements.txt`.
- [x] Generate `backend/requirements-dev.txt`.
- [x] Add `API_WORKERS` and `API_LOG_LEVEL` to `Settings`.

### Phase 2 — Frontend artifacts

- [x] Update `src/environments/environment.prod.ts` (placeholder).
- [x] Update `angular.json` (fileReplacements for production).
- [x] Add `frontend/Dockerfile`.
- [x] Add `frontend/nginx.conf`.

### Phase 3 — Compose

- [x] Rename dev compose to `docker-compose.dev.yml`.
- [x] Add production `docker-compose.yml`.
- [x] Add `compose.override.example.yml` (commented template).

### Phase 4 — Documentation

- [x] Write `PRODUCTION.md`.
- [x] Update `.env.example` (add `API_WORKERS`, `API_LOG_LEVEL`).
- [x] Update `backend/README.md` to point at `PRODUCTION.md`.

### Phase 5 — Cleanup

- [x] Remove `backend/dev.db` from the working tree.

### Phase 6 — Validation

- [x] `pytest backend -v` (58/58).
- [x] `tsc --noEmit -p tsconfig.app.json`.
- [x] `ng build --configuration production`.
- [x] `docker-compose config` validates the production compose.
- [x] `alembic upgrade head` against a real Postgres from clean.
- [x] API container boots, `/healthz` returns OK with security headers.
- [x] Final consistency sweep.

## Out of scope (recorded for future changes)

- HTTPS termination at the proxy layer (nginx / Caddy / cloud LB).
- Rate limiting at the proxy / WAF layer.
- CI/CD pipeline (operator-driven deploy via `docker compose`).
- Observability: Prometheus metrics, structured logging,
  OpenTelemetry, Sentry.
- Backups automation.
- Multi-environment promotion.
- Canary / blue-green deploys.