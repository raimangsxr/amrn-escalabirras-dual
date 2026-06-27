# Plan: 006-production-readiness

## Approach

This change adds deployable artifacts (Dockerfiles, production
compose, security headers, fileReplacements, PRODUCTION.md)
without changing any application behavior. The order:

1. SDD scaffolding.
2. Backend: middleware, start.sh, Dockerfile, requirements files.
3. Frontend: env prod override, angular.json fileReplacements,
   Dockerfile, nginx.conf.
4. Compose: production compose, optional dev compose.
5. Documentation: PRODUCTION.md, .env.example, backend README
   pointer.
6. Cleanup: remove `backend/dev.db`.
7. Validate everything end to end against real Postgres.

## Steps

### Phase 0 — SDD

1. Update `specs/manifest.yml` (add `006-production-readiness`).
2. Update `specs/contracts/api-rest/contract.md` (production
   security headers).
3. Update `specs/contracts/auth/contract.md` (Configuration table).
4. Update `specs/contracts/frontend-angular/contract.md`
   (Configuration subsection).
5. Write `specs/changes/006-production-readiness/spec.md`,
   `plan.md`, `tasks.md`, `context-pack.md`.

### Phase 1 — Backend artifacts

6. Write `backend/app/middleware/security_headers.py` with the new
   middleware. It computes the request scheme from `request.url.scheme`
   (or the `X-Forwarded-Proto` header) and adds the headers.
7. Wire the middleware into `backend/app/main.py`.
8. Add a test for the new middleware in
   `backend/tests/test_security_headers.py`.
9. Write `backend/start.sh` (`#!/usr/bin/env bash`):
   - `set -euo pipefail`.
   - `alembic upgrade head`.
   - `exec uvicorn app.main:app --host 0.0.0.0 --port 8000
     --workers "${API_WORKERS:-2}" --proxy-headers
     --forwarded-allow-ips="*" --log-level "${API_LOG_LEVEL:-info}"`.
10. Write `backend/Dockerfile`:
    - Stage 1 (`builder`): `python:3.12-slim`, install `build` and
      `pip-tools`, copy `pyproject.toml` + `backend/`, build the
      wheel and a `requirements.txt`.
    - Stage 2 (`runtime`): `python:3.12-slim`, copy the wheel and
      install it, copy `backend/`, copy `start.sh`, create a
      non-root user, expose 8000, `HEALTHCHECK CMD curl -fsS
      http://127.0.0.1:8000/healthz || exit 1`.
11. Generate `backend/requirements.txt` from the working venv with
    `pip freeze`.
12. Generate `backend/requirements-dev.txt` (pytest, pytest-asyncio,
    httpx, alembic).
13. Add `API_WORKERS` and `API_LOG_LEVEL` to `Settings` in
    `backend/app/config.py`.

### Phase 2 — Frontend artifacts

14. Update `src/environments/environment.prod.ts` with a clear
    `// TODO-PROD: replace apiBaseUrl with the public origin of the
    backend` placeholder and `apiBaseUrl: ''`.
15. Update `angular.json` to add `fileReplacements` in the
    `production` configuration that swaps `environment.ts` for
    `environment.prod.ts`.
16. Write `frontend/Dockerfile` (multi-stage node + nginx).
17. Write `frontend/nginx.conf` with SPA fallback, gzip, and
    security headers.
18. (Optional) Update the root `docker-compose.yml` to add a `web`
    service that builds the frontend and serves it via nginx.

### Phase 3 — Compose

19. Rename the current `docker-compose.yml` (dev) to
    `docker-compose.dev.yml` (or document the existing one as
    dev-only in a comment and add a new production compose).
    Decision: keep both files side-by-side.
20. Write the new production `docker-compose.yml` with `db`,
    `api`, optional `adminer` (in a `tools` profile).
21. Add a `compose.override.example.yml` (commented) so operators
    can extend the production compose for HTTPS / Caddy / nginx
    without editing the main file.

### Phase 4 — Documentation

22. Write `PRODUCTION.md` with the deploy checklist.
23. Update `.env.example` with `API_WORKERS` and `API_LOG_LEVEL`.
24. Update `backend/README.md` to point at `PRODUCTION.md`.

### Phase 5 — Cleanup

25. Remove `backend/dev.db` (and `backend/dev.db-journal` if any)
    from the working tree.

### Phase 6 — Validation

26. Run `pytest backend -v` (must stay 58/58).
27. Run `tsc --noEmit -p tsconfig.app.json` (exit 0).
28. Run `ng build --configuration production --output-path
    /tmp/...` and verify the bundle contains the prod env values.
29. Run `docker-compose config` against the production compose.
30. Run `alembic upgrade head` against a real Postgres (Docker) from a
    clean state.
31. Boot the API container, hit `/healthz`, verify the four security
    headers.
32. Final consistency sweep.

## Risks

- **`fileReplacements` requires the production env file to exist
  in the repo.** We commit a placeholder `environment.prod.ts` with
  `apiBaseUrl: ''`. The build still succeeds, but the bundle will
  have an empty URL until the operator overrides the file. PRODUCTION.md
  calls this out and suggests using a CI variable or a sed step.
- **Docker build context.** The backend `Dockerfile` is under
  `backend/`; the build context must be `backend/`. We document this
  in `docker-compose.yml`.
- **`psycopg[binary]` wheel.** Already pinned in `pyproject.toml`.
  The runtime image needs `libpq` only if we drop `binary`; we keep
  `binary` for simplicity.
- **`--proxy-headers --forwarded-allow-ips=*`.** Required so the
  scheme detection (`https`) works behind a TLS-terminating proxy.
  The wildcard is acceptable because the API only trusts `Host`
  headers from the proxy; combined with HSTS-on-HTTPS-only this is
  safe. Documented in PRODUCTION.md.
- **No HTTPS at the application layer.** The middleware only sets
  HSTS when the request is `https`. Behind a plain HTTP proxy, HSTS
  is suppressed — that's correct, you shouldn't promise HSTS over
  HTTP.
- **`docker compose` v2.** We assume Docker Compose v2 (the modern
  default on Docker Desktop and most Linux installs). The compose
  file uses the v2 format.
- **Container user.** The runtime image uses a non-root user
  (`app`) for defense in depth. Uvicorn binds to `0.0.0.0` inside
  the container; the port mapping (`8000:8000`) is what exposes
  it.
- **Frontend `nginx.conf`.** We serve the SPA from nginx. nginx is
  not a TLS terminator in our setup (PRODUCTION.md documents this is
  the responsibility of the deployment layer). HSTS at the API
  layer is set when the request arrives over HTTPS, which requires
  the proxy to forward `X-Forwarded-Proto: https`.

## Recommendations (do not create in this change)

- **`observability` contract** (not created): would document
  Prometheus metrics, structured logging, and request tracing.
- **`backup-restore` contract** (not created): would document the
  `pg_dump` cadence and the restore procedure.
- **`multi-env` contract** (not created): would document staging /
  canary / production promotion.
- **`ci-cd` contract** (not created): would document the build,
  test, and deploy pipeline.