# auth Contract

## Purpose

Define the authentication and embed-token model for the escalabirras
backend and frontend. This contract is owned by change
`004-auth-and-embed-tokens` and consumed by both the FastAPI backend
(`backend/app/auth.py`, `backend/app/security.py`,
`backend/app/routers/auth.py`, `backend/app/routers/tokens.py`) and
the Angular frontend (`src/app/auth/auth.service.ts`,
`src/app/auth/auth.interceptor.ts`, `src/app/auth/auth.guard.ts`).

It builds on `specs/contracts/api-rest/contract.md` (which lists the
endpoints) and `specs/contracts/persistence-postgres/contract.md`
(which owns the `embed_tokens` table).

## Threat model (v1)

- The app will be embedded in iframes of unrelated origins and
  published to the public internet.
- The backend does not use cookies; it authenticates via short-
  lived JWTs sent in `Authorization: Bearer …`. CSRF is therefore
  not a concern (browsers will not auto-attach cross-site
  `Authorization` headers).
- A single operator password, configured by env var
  (`ADMIN_PASSWORD`), gates access to the protected API. There is
  no operator table; rotating the password requires redeploying the
  backend with a new env var.
- Brute-force protection is delegated to the deployment layer
  (Cloudflare, AWS WAF, etc.) — `004` does not implement rate
  limiting.
- The frontend stores the JWT in `sessionStorage` (not
  `localStorage`) so the session ends when the tab closes and XSS
  exposure is bounded.

## Roles

There is exactly one role in v1: `operator`. The JWT carries
`{"sub": "operator"}`. Any non-empty `sub` is treated as
authenticated.

## JWTs

- Algorithm: HS256.
- Secret: read from the `JWT_SECRET` env var. Must be at least 32
  bytes of high-entropy random data; the backend refuses to start
  if it is shorter.
- Lifetime (`exp`): `JWT_TTL_SECONDS` env var, default `86400`
  (24 h).
- Issuer (`iss`): `"escalabirras"`.
- Audience (`aud`): `"escalabirras-web"`.
- Clock skew tolerance: 30 s.
- Algorithm allow-list on decode: only `HS256`. Any other
  algorithm in the token header raises `unauthorized`.

## Operator password

- Source: `ADMIN_PASSWORD` env var.
- Comparison: in-process constant-time string comparison against
  the `password` field of `POST /v1/auth/login`.
- Failed login returns `401` + `{code: "invalid_password"}`.
- No lockout, no rate limit, no audit log of failed logins in v1.

## Session JWT lifecycle

1. Operator POSTs `/v1/auth/login { password }`. The backend
   verifies the password against `ADMIN_PASSWORD` and issues a JWT.
2. The frontend stores the JWT in `sessionStorage` under
   `escalabirras.session`.
3. The HTTP interceptor adds `Authorization: Bearer <jwt>` to
   every subsequent request.
4. When the backend receives a request without a valid JWT (or
   with an expired one) on a protected endpoint, it returns
   `401 unauthorized`.
5. The frontend's HTTP interceptor observes the `401` and calls
   `AuthService.logout()`, which clears `sessionStorage` and
   navigates to `/login`.
6. The operator can also click "Salir" in the UI to log out
   voluntarily.

## Embed tokens

- Lifetime: no automatic expiry. Embed tokens are revoked by the
  operator via `DELETE /v1/tokens/{id}`. There is no scheduled
  rotation in v1.
- Format: `embed_<random>`, where `<random>` is `secrets.token_urlsafe(32)`.
  Example: `embed_qz3VHf8d2K0qJWbT9cN6sF7gH1mL4rP2`.
- Storage: only the sha256 hex digest of the full token is stored
  in `embed_tokens.token_hash`. The plaintext token is returned to
  the operator exactly once at creation and never persisted.
- Verification: on `POST /v1/auth/embed-token { token }`, the
  backend hashes the supplied token, looks up
  `embed_tokens.token_hash = :h AND revoked_at IS NULL`, updates
  `last_used_at`, and issues a fresh JWT.
- Revocation: `DELETE /v1/tokens/{id}` sets `revoked_at = NOW()`
  (soft delete; the row is kept for audit). Subsequent attempts to
  redeem the token fail with `401 invalid_embed_token`.
- Scope: a valid embed token grants the same access as a logged-in
  operator (full read/write on `/v1/participants/*`,
  `/v1/leaderboard/top`, `/v1/history`). There is no read-only or
  per-endpoint scope in v1.

## Endpoints summary

| Endpoint | Auth | Notes |
| --- | --- | --- |
| `POST /v1/auth/login` | public | `{password}` → JWT (24 h). |
| `POST /v1/auth/embed-token` | public | `{token}` → JWT (24 h). Updates `last_used_at`. |
| `POST /v1/auth/logout` | Bearer | Server-side no-op. Returns 204. |
| `GET /v1/auth/me` | Bearer | `{authenticated: true, operator: "operator"}`. |
| `POST /v1/tokens` | Bearer | `{name}` → `{id, name, token, created_at}`. Plaintext returned once. |
| `GET /v1/tokens` | Bearer | `{tokens: [...]}` without values. |
| `DELETE /v1/tokens/{id}` | Bearer | Soft-revoke. Returns 204. |

Full request/response shapes and error codes are in
`specs/contracts/api-rest/contract.md`.

## HTTP header behaviour

- The backend never sets cookies. The frontend uses `Authorization`
  headers exclusively.
- CORS `allow_credentials` stays `false` (the value does not
  matter for Bearer auth but is documented for clarity).
- The backend always responds with
  `Content-Security-Policy: frame-ancestors <value>` and
  `X-Frame-Options: ALLOW-FROM <value>`, where `<value>` comes
  from the `FRAME_ANCESTORS` env var (default `*`). This is the
  minimum needed for the app to be iframe-able from any origin.
- All auth endpoints and `/healthz` are reachable without
  `Authorization`. All other `/v1/*` endpoints require it.

## Frontend auth flow

- `AuthService.bootstrap()`:
  1. Read `sessionStorage['escalabirras.session']`. If present
     and not expired, restore and emit on `session$`.
  2. Else, scan `window.location.search` for `embed_token`. If
     present, call `AuthService.exchangeEmbedToken(...)`. On 200,
     store and emit; remove the query parameter via
     `history.replaceState`. On 401, leave `session$` as `null`,
     remove the query parameter, and let the router redirect to
     `/login` with a hint message.
  3. Else, leave `session$` as `null`.
- HTTP interceptor (`authInterceptor`):
  - On every outgoing request, if `AuthService.getToken()` is
    non-null, add `Authorization: Bearer <token>`.
  - On 401 responses, call `AuthService.logout()` and navigate to
    `/login`.
- `authGuard`:
  - `CanActivateFn` that returns `true` when
    `AuthService.isAuthenticated$` is `true`, otherwise navigates
    to `/login` (with a `returnUrl` query parameter if desired;
    not required in v1).

## Configuration

| Env var | Required | Default | Description |
| --- | --- | --- | --- |
| `ADMIN_PASSWORD` | yes | — | Operator password. Compared in-process. Min 12 chars recommended; rotate by redeploy. |
| `JWT_SECRET` | yes | — | HS256 signing secret. Backend refuses to start if < 32 chars. Generate with `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`. Rotating it invalidates all live sessions. |
| `JWT_TTL_SECONDS` | no | `86400` | Session JWT lifetime (default 24 h). |
| `FRAME_ANCESTORS` | no | `*` | CSP `frame-ancestors` and `X-Frame-Options: ALLOW-FROM` value. **Must be set to the parent app's origin in production** (e.g. `https://parent.example.com`). |
| `CORS_ORIGINS` | no | `http://localhost:4200` | Comma-separated list of allowed CORS origins. **Must be set to the public origin of the escalabirras frontend in production**. |
| `DATABASE_URL` | yes | `postgresql+psycopg://...` | SQLAlchemy URL. Production should point at a managed Postgres with TLS. |
| `API_WORKERS` | no | `2` | Number of uvicorn workers. Set to `(2 * CPU) + 1` for a dedicated host. |
| `API_LOG_LEVEL` | no | `info` | Uvicorn log level. `warning` in production. |

These are documented in `.env.example`, `backend/README.md`, and
`PRODUCTION.md`.

## What is NOT in this contract

- Multi-tenant / multi-operator: a single operator only.
- OAuth / external identity providers.
- Refresh tokens: 24 h JWT is the only session mechanism.
- Per-endpoint scopes on embed tokens (full access only).
- Rate limiting on `/v1/auth/login`.
- Audit log of who created / revoked which embed tokens beyond
  `created_at`, `last_used_at`, `revoked_at`.
- Password reset / rotation flow (rotate by redeploying with a
  new `ADMIN_PASSWORD`; existing JWTs remain valid until expiry).