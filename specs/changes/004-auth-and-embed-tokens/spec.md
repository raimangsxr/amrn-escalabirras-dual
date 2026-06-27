# Spec: 004-auth-and-embed-tokens

## Problem

The app is being published to the public internet and will also be
embedded in iframes of unrelated origins. Today it has no
authentication and no notion of embed credentials: anyone reaching
the backend can score crates, create participants, and read the
leaderboard. That is acceptable for a single laptop on the venue
network but not for an internet-facing deployment.

This change adds (1) a single-operator login using a password
configured at the backend and (2) a token-issuance system so the
operator can hand out a long-lived credential to a parent
application; the parent embeds the escalabirras app in an iframe
with that credential in the URL and the iframe loads the operator
session directly, without showing the login screen.

## Goals

- Add `POST /v1/auth/login` that exchanges the operator password
  (from `ADMIN_PASSWORD` env var) for a 24 h JWT.
- Add `POST /v1/auth/embed-token` that exchanges an embed token
  (from a new `embed_tokens` table) for a 24 h JWT, used by the
  iframe bootstrap.
- Add `POST /v1/tokens`, `GET /v1/tokens`, and
  `DELETE /v1/tokens/{id}` so the operator can issue, list, and
  revoke embed tokens from the UI.
- Protect every existing `/v1/*` endpoint (except
  `/v1/auth/login`, `/v1/auth/embed-token`, and `/healthz`) with
  `Authorization: Bearer <jwt>`.
- Add a CSP `frame-ancestors` middleware so the backend can be
  iframe'd from any configured origin.
- Add an Angular login screen (`LoginComponent`), routing with
  `authGuard`, an HTTP interceptor that adds `Bearer` and handles
  `401`s, and a `TokensComponent` for managing embed tokens.
- Make the iframe bootstrap path (`?embed_token=…`) work end to
  end: on first load, the frontend reads the query param,
  exchanges it for a JWT, stores it in `sessionStorage`, and
  removes the query parameter from the URL.

## Non-Goals

- Multi-operator accounts. There is exactly one operator, gated by
  a single password.
- OAuth / external identity providers.
- Refresh tokens. The JWT lasts 24 h; on expiry the operator is
  bounced to `/login`.
- Per-endpoint scope on embed tokens. All embed tokens grant full
  access in v1.
- Rate limiting on `/v1/auth/login`. Documented as a deployment-
  layer concern.
- Audit log beyond `created_at`, `last_used_at`, `revoked_at` on
  the `embed_tokens` rows.
- HTTPS termination, Nginx config, custom domain, production
  deployment. Documented as out of scope per the planning pass.

## Requirements

### Backend

- **R1.** `backend/app/settings.py` (existing `config.py`) reads
  four new env vars: `ADMIN_PASSWORD` (required), `JWT_SECRET`
  (required, length-validated), `JWT_TTL_SECONDS` (default
  `86400`), `FRAME_ANCESTORS` (default `*`).
- **R2.** A new Alembic migration `0002_add_embed_tokens` creates
  the `embed_tokens` table with `id`, `name`, `token_hash`,
  `created_at`, `last_used_at`, `revoked_at` and the
  `ix_embed_tokens_token_hash` index.
- **R3.** `backend/app/auth.py` exposes
  `create_session_token(subject)`,
  `decode_session_token(token)`,
  `hash_embed_token(plaintext)`, and
  `verify_embed_token(plaintext, db) -> EmbedToken | None`.
- **R4.** `backend/app/security.py` exposes the FastAPI
  dependency `get_current_session` that reads
  `Authorization: Bearer …`, decodes the JWT, validates `iss`,
  `aud`, `exp`, and returns the session info or raises
  `HTTPException(401, "unauthorized")`.
- **R5.** `backend/app/routers/auth.py` mounts at `/v1/auth` with
  `login`, `embed-token`, `logout`, `me`.
- **R6.** `backend/app/routers/tokens.py` mounts at `/v1/tokens`
  with `POST`, `GET`, and `DELETE /{token_id}`. All three depend
  on `get_current_session`.
- **R7.** `backend/app/middleware/frame_ancestors.py` is a Starlette
  middleware that adds `Content-Security-Policy: frame-ancestors
  <value>` and `X-Frame-Options: ALLOW-FROM <value>` to every
  response. `<value>` comes from `Settings.frame_ancestors`.
- **R8.** All existing `/v1/*` routes are protected with
  `Depends(get_current_session)`. `/healthz` remains open.
- **R9.** The 4 existing tests (28 cases) are updated to include
  a Bearer token in their fixtures. A new
  `tests/conftest.py` helper `auth_headers(client)` returns a
  valid JWT for use in tests.
- **R10.** New tests cover: login with right/wrong password,
  expired / invalid / missing JWTs, embed-token creation,
  redemption, revocation, listing without exposing values, and
  CSP header presence.

### Frontend

- **R11.** `src/environments/environment.ts` adds
  `loginPath: '/login'` and `embedTokenQueryParam: 'embed_token'`.
- **R12.** `src/app/auth/auth.service.ts` exposes `session$`,
  `isAuthenticated$`, `bootstrap()`, `login()`,
  `exchangeEmbedToken()`, `logout()`, `getToken()`.
- **R13.** `src/app/auth/auth.interceptor.ts` is an `HttpInterceptorFn`
  that adds `Authorization: Bearer <token>` to outgoing requests
  and triggers `AuthService.logout()` on `401`.
- **R14.** `src/app/auth/auth.guard.ts` is a `CanActivateFn` that
  redirects to `/login` when `session$` is `null`.
- **R15.** `src/app/login/login.component.{ts,html,css}` is the
  login form: password input, submit button, error message slot.
- **R16.** `src/app/main-view/main-view.component.{ts,html,css}`
  wraps the current app view (header, top 3, manager, focus
  button) and adds a "Tokens" button and a "Salir" button.
- **R17.** `src/app/tokens/tokens.component.{ts,html,css}` lists
  embed tokens, lets the operator create new ones (showing the
  plaintext once with a copy button), and lets them revoke.
- **R18.** `src/app/app-routing.module.ts` defines:
  ```ts
  const routes: Routes = [
    { path: 'login', component: LoginComponent },
    { path: '', component: MainViewComponent, canActivate: [authGuard] },
    { path: '**', redirectTo: '' },
  ];
  ```
- **R19.** `src/app/app.component.ts` invokes
  `AuthService.bootstrap()` once and renders `<router-outlet>`.
- **R20.** The HTTP interceptor and guard are registered as
  providers in `AppModule`.

### Validation

- **R21.** `pytest backend -v` exits 0 with the new and updated
  tests.
- **R22.** `tsc --noEmit -p tsconfig.app.json` exits 0.
- **R23.** `ng build --configuration production --output-path
  /tmp/...` succeeds.
- **R24.** End-to-end smoke against the running backend covers:
  1. `GET /v1/participants` without Bearer → 401.
  2. `POST /v1/auth/login` with wrong password → 401.
  3. `POST /v1/auth/login` with right password → 200 + JWT.
  4. `GET /v1/participants` with Bearer → 200.
  5. `POST /v1/tokens` with Bearer → 201 + `embed_xxx`.
  6. `POST /v1/auth/embed-token` with `embed_xxx` → 200 + new
     JWT.
  7. Iframe-like URL `http://localhost:4200/?embed_token=embed_xxx`
     loads and immediately calls the protected endpoints
     (verified via the JS bundle reaching the backend with Bearer).

### SDD / contracts

- **R25.** `specs/contracts/api-rest/contract.md` updated with
  auth headers, new endpoints, new error codes.
- **R26.** `specs/contracts/persistence-postgres/contract.md`
  updated with the `embed_tokens` table.
- **R27.** `specs/contracts/frontend-angular/contract.md` updated
  with the auth flow, `AuthService`, interceptor, guard, login
  screen, tokens UI.
- **R28.** `specs/contracts/auth/contract.md` created.
- **R29.** `specs/manifest.yml` updated: `auth` contract active,
  `004-auth-and-embed-tokens` change active.

## Acceptance Criteria

- **AC1.** `pytest backend -v` exits 0 with all old tests
  adapted to send Bearer and the new auth tests passing.
- **AC2.** `tsc --noEmit -p tsconfig.app.json` exits 0.
- **AC3.** `ng build --configuration production --output-path
  /tmp/escalabirras-fe-prod` succeeds.
- **AC4.** With backend + frontend running, the E2E smoke in R24
  passes.
- **AC5.** `git status src/` shows changes only under
  `src/app/auth/`, `src/app/login/`, `src/app/main-view/`,
  `src/app/tokens/`, `src/app/app.component.*`,
  `src/app/app-routing.module.ts`, `src/app/app.module.ts`,
  `src/environments/`, plus the existing components that now live
  inside `MainViewComponent` instead of `AppComponent`.
- **AC6.** `git grep -n "ADMIN_PASSWORD\|JWT_SECRET" backend/` shows
  the new env vars being read; `.env.example` documents them.
- **AC7.** `specs/manifest.yml` lists `auth` and
  `004-auth-and-embed-tokens` as active; the three updated
  contracts have no `TODO` placeholders in their populated
  sections; `auth/contract.md` is fully populated.