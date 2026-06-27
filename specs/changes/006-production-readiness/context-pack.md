# Context Pack: 006-production-readiness

## Goal

Make the project production-ready: add Dockerfiles, a production
docker-compose, security headers, fileReplacements for the
frontend, a `PRODUCTION.md` checklist, and clean up stray
artifacts. The application code itself is unchanged.

## Relevant Contracts

- `specs/contracts/api-rest/contract.md` (updated — production
  security headers, CORS prod note).
- `specs/contracts/auth/contract.md` (updated — Configuration table).
- `specs/contracts/frontend-angular/contract.md` (updated —
  Configuration subsection references fileReplacements).

## Current Understanding

- The backend runs locally via `uvicorn app.main:app` and is
  deployable as a Python package (`pyproject.toml`). It has 58
  passing tests, a clean error contract, and a JWT auth flow.
- The frontend is an Angular 16 SPA. `ng build --configuration
  production` produces a `dist/` bundle.
- The current `docker-compose.yml` only brings up Postgres and
  Adminer for local dev. There is no Dockerfile for the backend
  or the frontend.
- The current `environment.prod.ts` carries the dev `apiBaseUrl`,
  which would break in production. The audit documented this as a
  MEDIUM finding.
- `backend/dev.db` exists in the working tree from earlier audits
  and is gitignored but still present.
- The `.env.example` documents `ADMIN_PASSWORD`, `JWT_SECRET`,
  `JWT_TTL_SECONDS`, `FRAME_ANCESTORS`, but not `API_WORKERS` or
  `API_LOG_LEVEL`.

## Files / Areas Likely Involved

### New

- `backend/Dockerfile` — multi-stage Python image.
- `backend/start.sh` — entrypoint (alembic + uvicorn).
- `backend/requirements.txt` — pinned runtime deps.
- `backend/requirements-dev.txt` — pinned dev deps.
- `backend/app/middleware/security_headers.py` — HSTS,
  X-Content-Type-Options, Referrer-Policy.
- `backend/tests/test_security_headers.py`.
- `frontend/Dockerfile` — multi-stage node + nginx image.
- `frontend/nginx.conf` — SPA fallback + gzip.
- `PRODUCTION.md` — deploy checklist.
- `docker-compose.yml` — production compose (api + db + optional
  adminer).
- `docker-compose.dev.yml` — the existing dev compose, renamed.
- `compose.override.example.yml` — extension template.

### Modified

- `backend/app/main.py` — registers `SecurityHeadersMiddleware`.
- `backend/app/config.py` — adds `api_workers`, `api_log_level`.
- `backend/README.md` — points at `PRODUCTION.md`.
- `angular.json` — adds `fileReplacements` for production.
- `src/environments/environment.prod.ts` — placeholder +
  `TODO-PROD` comment.
- `.env.example` — adds `API_WORKERS`, `API_LOG_LEVEL`.
- `specs/manifest.yml`, the three updated contracts, this change's
  files.

### Removed

- `backend/dev.db`, `backend/dev.db-journal` (gitignored,
  physical cleanup).

### Untouched

- All `src/app/` components and services.
- All `backend/app/auth.py`, `crud.py`, `models.py`,
  `routers/*.py`.
- All Alembic migrations.
- All test files other than the new `test_security_headers.py`.

## Constraints

- **No HTTPS at the application layer.** Documented as a proxy-
  layer concern in PRODUCTION.md.
- **No rate limiting** at the application layer (per `004`).
- **No new application behavior.** The change is purely artifacts +
  configuration.
- **Docker Compose v2** syntax (no `version:` field).
- **Python 3.12** for the backend runtime (matches the existing
  dev venv).
- **Node 20 LTS** for the frontend build.
- **`psycopg[binary]`** keeps the runtime image free of `libpq`.
- **`fileReplacements` requires `environment.prod.ts` to exist**
  at build time; we commit a placeholder with `apiBaseUrl: ''`.

## Validation Plan

1. **Backend tests** (narrow).

   ```bash
   /tmp/venv-002/bin/pytest backend -v
   ```

   Expectation: 58+ tests green (58 existing + new
   `test_security_headers` tests).

2. **Frontend typecheck** (narrow).

   ```bash
   node_modules/.bin/tsc --noEmit -p tsconfig.app.json
   ```

   Expectation: exit 0.

3. **Frontend production build** (narrow).

   ```bash
   node_modules/.bin/ng build --configuration production \
       --output-path /tmp/escalabirras-fe-prod
   ```

   Expectation: bundle produced; verify `fileReplacements` swapped
   the env file.

4. **Compose validation** (narrow).

   ```bash
   docker-compose config
   ```

   Expectation: exit 0 with the resolved YAML.

5. **Postgres migration** (broad).

   ```bash
   docker compose up -d db
   DATABASE_URL=postgresql+psycopg://escalabirras:escalabirras@localhost:5432/escalabirras \
       alembic -c backend/alembic.ini upgrade head
   ```

   Expectation: both `0001` and `0002` apply on a fresh database.

6. **API container boot** (broad).

   ```bash
   docker compose up -d db api
   curl -s -i http://localhost:8000/healthz
   ```

   Expectation: 200 + `Content-Security-Policy`, `X-Frame-Options`,
   `X-Content-Type-Options`, `Referrer-Policy` present.

7. **Frontend container boot** (broad).

   ```bash
   docker compose up -d web
   curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8080/
   ```

   Expectation: 200 + `index.html` with `<app-root>`.

8. **Final consistency sweep** (broad).

   ```bash
   find backend -name '*.db' -not -path '*/.pytest_cache/*'
   grep -nR "TODO" specs/changes/006-production-readiness
   docker-compose config
   ```

   Expectation: no stray DB files; no `TODO`; compose valid.

## Risks

- **Production env override.** `environment.prod.ts` ships with an
  empty `apiBaseUrl`. If an operator forgets to set it, the bundle
  will hit `''`. PRODUCTION.md and the inline `// TODO-PROD`
  comment call this out. Mitigation: a CI step that asserts the
  string is non-empty before deploying.
- **`--forwarded-allow-ips=*`.** Required so `request.url.scheme`
  reflects the original scheme behind a TLS proxy. The wildcard is
  safe in this deployment because the API is only exposed behind a
  controlled proxy; documented in PRODUCTION.md.
- **`Strict-Transport-Security` only over HTTPS.** The middleware
  inspects `request.url.scheme` and the `X-Forwarded-Proto` header.
  When the proxy forwards `https`, the header is set. Otherwise
  it is suppressed. We do not promise HSTS over plain HTTP.
- **Container non-root user.** `app` user inside the backend image
  cannot write to `/app`. Volume mounts for `pgdata` are owned by
  Postgres's own user inside the `db` container.
- **Build context.** The backend Dockerfile expects the build
  context to be `backend/`. `docker-compose.yml` sets this
  explicitly via `build: ./backend`.
- **`psycopg[binary]` wheel.** Already pinned in `pyproject.toml`
  and not changing here.
- **No automated visual regression tests.** Documented.

## Recommendations (do not create in this change)

- **`observability` contract** (not created): would own metrics,
  structured logs, tracing.
- **`backup-restore` contract** (not created): would own the
  `pg_dump` cadence and the restore procedure.
- **`ci-cd` contract** (not created): would own the build / test /
  deploy pipeline.
- **`multi-env` contract** (not created): would own staging /
  canary / production promotion.