# Production deploy

This document covers the end-to-end steps to deploy the escalabirras
app to production. The code in this repo is the **deployable
artifact**; this file is the **deploy playbook**.

The scope is intentionally narrow: production means a public
internet deploy behind a TLS-terminating proxy. There is no CI/CD,
no canary, no staging environment, no observability stack. Those
are out of scope per the planning pass.

## Architecture

```
            ┌──────────────────────────────────────────────────────────┐
            │ Public internet                                          │
            └──────────────────────────────────────────────────────────┘
                                  │   HTTPS
                                  ▼
            ┌──────────────────────────────────────────────────────────┐
            │ Reverse proxy (nginx / Caddy / cloud LB)                │
            │  - terminates TLS                                         │
            │  - forwards X-Forwarded-Proto: https                     │
            │  - serves the SPA build (/usr/share/nginx/html/dist)     │
            │  - proxies /v1/* to the API container                     │
            └──────────────────────────────────────────────────────────┘
                          │                       │
              /v1/*       │                       │  serves dist/
                          ▼                       ▼
            ┌─────────────────────┐    ┌──────────────────────┐
            │ API (docker)        │    │ Web (docker, nginx)  │
            │  FastAPI + uvicorn   │    │  static SPA           │
            │  port 8000           │    │  port 80               │
            └─────────────────────┘    └──────────────────────┘
                          │
                          ▼
            ┌─────────────────────┐
            │ Postgres 16          │
            │  escalabirras-pgdata │
            └─────────────────────┘
```

The escalabirras frontend is also delivered as an embed
(`<iframe src="https://app.example.com/?embed_token=...">`); the
parent app lives at a separate origin and is the value of
`FRAME_ANCESTORS`.

## Pre-deploy checklist

- [ ] **Provision a host** with Docker Engine >= 24 and Docker
      Compose v2.
- [ ] **Provision Postgres** (managed service or self-hosted 16+).
- [ ] **Provision a TLS-terminating reverse proxy** (Caddy, nginx,
      Cloudflare, AWS ALB, etc.) with a valid certificate for
      `app.example.com`.
- [ ] **Generate secrets:**
      ```bash
      python3 -c "import secrets; print(secrets.token_urlsafe(48))"  # JWT_SECRET
      openssl rand -hex 16                                          # ADMIN_PASSWORD
      openssl rand -hex 16                                          # POSTGRES_PASSWORD
      ```
- [ ] **Decide the public origin** of the app (`https://app.example.com`).
- [ ] **Decide the parent origin** that will iframe the app
      (`https://parent.example.com`).
- [ ] **Build the production env file:**
      ```bash
      cp .env.example .env
      $EDITOR .env
      ```
      Set `ADMIN_PASSWORD`, `JWT_SECRET`, `POSTGRES_PASSWORD`,
      `CORS_ORIGINS`, `FRAME_ANCESTORS`. Leave the others at their
      defaults unless you know you need to change them.
- [ ] **Build the production frontend bundle** with the right
      `apiBaseUrl` (see "Frontend build" below).
- [ ] **Backups:** configure `pg_dump` of the `escalabirras` database
      to run daily and ship the dump off-host.

## First deploy

```bash
# 1. Clone on the host (or sync via rsync / your CI).
git clone <repo> /opt/escalabirras
cd /opt/escalabirras

# 2. Configure env.
cp .env.example .env
$EDITOR .env

# 3. Build and start the API + DB.
docker compose pull
docker compose build api
docker compose up -d db api

# 4. Confirm migrations ran (start.sh runs alembic upgrade head).
docker compose logs api | grep "alembic upgrade head"

# 5. Smoke test the API.
curl -fsS http://127.0.0.1:8000/healthz
# {"status":"ok"}

# 6. Build the frontend image.
docker build -f frontend/Dockerfile -t escalabirras-web:latest .

# 7. Run the frontend container.
docker run -d --name escalabirras-web --restart unless-stopped \
    -p 8080:80 escalabirras-web:latest

# 8. Configure your reverse proxy:
#    - app.example.com/ -> http://127.0.0.1:8080/
#    - app.example.com/v1/* -> http://127.0.0.1:8000/v1/*
#    - Forward X-Forwarded-Proto: https
#    - Forward X-Forwarded-For: <client ip>
#    - Set HSTS at the proxy OR rely on the API's Strict-Transport-Security header.

# 9. From a browser, load https://app.example.com/, log in with
#    ADMIN_PASSWORD, create an embed token, and verify the iframe flow.
```

## Frontend build (apiBaseUrl)

The Angular build reads `src/environments/environment.prod.ts` for
the production `apiBaseUrl`. Edit that file before building the
image:

```ts
export const environment = {
  apiBaseUrl: 'https://app.example.com/v1',  // <- set this
  celebrationDurationMs: 12000,
  loginPath: '/login',
  embedTokenQueryParam: 'embed_token',
  sessionStorageKey: 'escalabirras.session',
};
```

Then build:

```bash
docker build -f frontend/Dockerfile -t escalabirras-web:latest .
```

The CI pipeline should assert that `apiBaseUrl` is non-empty and
starts with `https://` before merging.

## Rotating secrets

| Secret | Effect of rotation | How |
| --- | --- | --- |
| `ADMIN_PASSWORD` | Existing JWTs remain valid. Operators must type the new password on next login. | Update `.env`, `docker compose up -d api`. |
| `JWT_SECRET` | **Invalidates all live sessions.** All operators (including iframe embeds) are logged out. | Update `.env`, `docker compose up -d api`. |
| `POSTGRES_PASSWORD` | API container fails to start (the URL it builds uses the new value; the DB still uses the old one). | Update both `.env` and the Postgres user's password (`ALTER USER ... WITH PASSWORD '...'`). |

## Backup and restore

```bash
# Backup
docker compose exec db pg_dump -U escalabirras escalabirras > backup-$(date +%F).sql

# Restore
cat backup-2026-06-27.sql | docker compose exec -T db psql -U escalabirras escalabirras
```

Backups include the `participants` and `embed_tokens` tables. The
`embed_tokens.token_hash` column is non-reversible (one-way
sha256); restoring a backup recovers which tokens existed but not
their plaintext values.

## Logs

```bash
docker compose logs -f api    # API access and error logs
docker compose logs -f db     # Postgres logs
docker logs -f escalabirras-web
```

## Smoke tests after deploy

1. **API health:**
   ```bash
   curl -fsS https://app.example.com/healthz
   ```

2. **Login:**
   ```bash
   curl -i -X POST https://app.example.com/v1/auth/login \
       -H 'Content-Type: application/json' \
       -d '{"password":"<ADMIN_PASSWORD>"}'
   ```

3. **Embed token round-trip:**
   ```bash
   TOKEN=...
   ET=$(curl -s -X POST https://app.example.com/v1/tokens \
       -H "Authorization: Bearer $TOKEN" \
       -H 'Content-Type: application/json' \
       -d '{"name":"smoke-test"}' | jq -r .token)
   curl -s -X POST https://app.example.com/v1/auth/embed-token \
       -H 'Content-Type: application/json' \
       -d "{\"token\":\"$ET\"}"
   ```

4. **Iframe at three sizes:**
   ```html
   <iframe src="https://app.example.com/?embed_token=<ET>" width="320" height="200"></iframe>
   <iframe src="https://app.example.com/?embed_token=<ET>" width="768" height="1024"></iframe>
   <iframe src="https://app.example.com/?embed_token=<ET>" width="1920" height="1080"></iframe>
   ```
   Each must render the operator's actions without overflow.

## Out of scope (documented for the next change)

- HTTPS certificate provisioning (handled by the proxy).
- Rate limiting (use Cloudflare / AWS WAF / a proxy module).
- Observability stack (Prometheus, structured logs, Sentry).
- CI/CD pipeline.
- Canary / blue-green deploys.
- Multi-environment promotion.