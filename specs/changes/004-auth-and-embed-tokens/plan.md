# Plan: 004-auth-and-embed-tokens

## Approach

The change has two layers (backend, frontend) that are tightly
coupled — both rely on the same JWT shape and the same
`embed_tokens` schema. We implement them in this order:

1. Update SDD: contracts first, then change files (per AGENTS.md
   rule 7).
2. Backend: settings → auth/security modules → models + migration
   → routers → middleware → wire-up in `main.py` → tests.
3. Frontend: `AuthService` + interceptor + guard → login +
   main-view + tokens components → routing → wire-up in
   `AppModule` and `AppComponent`.
4. Validation: pytest, tsc, ng build, end-to-end smoke.

The backend is validated against SQLite for tests and the same
SQLite for the smoke (Postgres is reachable via `docker compose`
but the SQLite path is sufficient for v1).

## Steps

### Phase 0 — SDD update

1. Update `specs/manifest.yml` to add `auth` contract and
   `004-auth-and-embed-tokens` change.
2. Update `specs/contracts/api-rest/contract.md`:
   - Add auth section explaining JWT, public/protected endpoints,
     new error codes.
   - Add 4 auth endpoints and 3 token endpoints.
   - Mark each existing endpoint as Bearer-protected.
3. Update `specs/contracts/persistence-postgres/contract.md`:
   - Add the `embed_tokens` table DDL.
   - Add the SQLAlchemy model.
   - Reference the new migration `0002_add_embed_tokens`.
4. Update `specs/contracts/frontend-angular/contract.md`:
   - Add the auth flow and `AuthService`.
   - Add the interceptor and guard.
   - Add login + main-view + tokens components.
   - Update user flows and lifecycle.
5. Write `specs/contracts/auth/contract.md`.
6. Write `specs/changes/004-auth-and-embed-tokens/{spec, plan,
   tasks, context-pack}.md`.

### Phase 1 — Backend

7. Update `backend/app/config.py` (`Settings`) with `admin_password`,
   `jwt_secret`, `jwt_ttl_seconds`, `frame_ancestors`. Validate
   `jwt_secret` length on startup.
8. Update `backend/.env.example` (created at the repo root in
   `002`) with the four new env vars. Add a `JWT_SECRET` example
   that is ≥ 32 chars.
9. Add `backend/app/auth.py` with:
   - `create_session_token(subject) -> str`
   - `decode_session_token(token) -> dict` (raises on invalid)
   - `hash_embed_token(plaintext) -> str`
   - `generate_embed_token() -> str` (returns `embed_xxx`)
   - `verify_embed_token(plaintext, db) -> EmbedToken | None`
10. Add `backend/app/security.py` with `get_current_session`
    dependency.
11. Update `backend/app/models.py` to add the `EmbedToken` model.
12. Add `backend/alembic/versions/0002_add_embed_tokens.py`
    hand-written (creates table + index).
13. Add `backend/app/schemas.py` updates for `LoginRequest`,
    `LoginResponse`, `EmbedTokenExchangeRequest`,
    `EmbedTokenExchangeResponse`, `CreateEmbedTokenRequest`,
    `EmbedTokenCreatedResponse`, `EmbedTokenListItem`,
    `EmbedTokenListResponse`, `MeResponse`.
14. Add `backend/app/routers/auth.py`.
15. Add `backend/app/routers/tokens.py`.
16. Add `backend/app/middleware/frame_ancestors.py`.
17. Update `backend/app/main.py`:
    - Mount `auth.router` and `tokens.router`.
    - Add the frame-ancestors middleware.
18. Update `backend/app/routers/participants.py` and
    `backend/app/routers/leaderboard.py` to depend on
    `get_current_session`.
19. Update `backend/tests/conftest.py` to provide an
    `auth_token(client)` fixture that logs in and returns a valid
    JWT.
20. Update `backend/tests/test_participants.py`,
    `test_crates.py`, `test_leaderboard.py`, `test_history.py`
    to use the fixture.
21. Add `backend/tests/test_auth.py`,
    `backend/tests/test_embed_tokens.py`,
    `backend/tests/test_protected_endpoints.py`,
    `backend/tests/test_frame_ancestors.py`.

### Phase 2 — Frontend

22. Update `src/environments/environment.ts` and
    `src/environments/environment.prod.ts` to add `loginPath`
    and `embedTokenQueryParam`.
23. Add `src/app/auth/auth.service.ts`.
24. Add `src/app/auth/auth.interceptor.ts`.
25. Add `src/app/auth/auth.guard.ts`.
26. Add `src/app/auth/auth.service.spec.ts`? — out of scope;
    manually smoke-tested.
27. Add `src/app/login/login.component.{ts,html,css}`.
28. Add `src/app/main-view/main-view.component.{ts,html,css}` that
    wraps the existing header/top3/manager/participant-list
    layout. Migrate the inline template from `app.component.html`
    into here.
29. Add `src/app/tokens/tokens.component.{ts,html,css}`.
30. Update `src/app/app.component.{ts,html}` to invoke
    `AuthService.bootstrap()` on init and render
    `<router-outlet>`.
31. Update `src/app/app-routing.module.ts` to define the routes
    listed in R18.
32. Update `src/app/app.module.ts` to register the HTTP
    interceptor and the new components.

### Phase 3 — Validation

33. Run `pytest backend -v` until green.
34. Run `tsc --noEmit -p tsconfig.app.json` until exit 0.
35. Run `ng build --configuration production --output-path
    /tmp/escalabirras-fe-prod` until green.
36. Run an E2E smoke against a real backend + frontend:
    - Boot `alembic upgrade head` against SQLite.
    - Boot uvicorn with `ADMIN_PASSWORD` and `JWT_SECRET` env vars.
    - Boot `ng serve`.
    - Hit `/healthz`, then `POST /v1/auth/login` with curl, then
      the protected endpoints with the Bearer.
    - Run a Node script that simulates the iframe: loads the SPA
      HTML and verifies that `?embed_token=xxx` would lead to a
      Bearer-authenticated session (this is hard to test without a
      browser; documented as best-effort manual).
37. Final consistency sweep:
    - No `TODO` in the new SDD files.
    - No `localStorage`, no `TeamServiceService`, no `MatIconModule`
      regressions.
    - `git status src/` shows the expected diff.

## Risks

- **JWT secret rotation.** Rotating `JWT_SECRET` invalidates all
  active sessions. Documented; no automatic rotation in v1.
- **`ADMIN_PASSWORD` and `JWT_SECRET` must be present** at startup.
  If they are missing, the backend fails fast with a clear error.
- **Brute-force on `/v1/auth/login`.** No rate limit in v1.
  Documented as a deployment-layer concern (Cloudflare/WAF).
- **`sessionStorage` vs `localStorage`.** We chose
  `sessionStorage` to limit XSS exposure. Trade-off: closing the
  tab logs the operator out. The operator can re-login by typing
  the password.
- **Embed tokens never expire automatically.** An operator must
  revoke them manually. A future change can add `expires_at` and a
  cleanup job.
- **Cross-origin iframe privacy.** The `embed_token` is exposed in
  the iframe's URL bar (briefly, until `history.replaceState`).
  Anyone with access to the parent page's DOM can read it before
  the URL is cleaned. Mitigation: clean up as fast as possible
  after the exchange.
- **Backend tests run against SQLite.** `JSONWebSignature` is
  Python-only, no SQL impact; SQLite is sufficient for auth tests.
- **No rate limit means login is brute-forceable.** A 6-character
  password would be cracked in minutes. Document a minimum
  password length in `.env.example` and the backend README.
- **CORS unchanged.** Frontend on `:4200`, backend on `:8000`,
  `CORS_ORIGINS` already includes `http://localhost:4200`. Bearer
  auth does not require `allow_credentials=True`. No change.
- **`X-Frame-Options: ALLOW-FROM` is deprecated in modern browsers**
  but still respected as a fallback. The `Content-Security-Policy:
  frame-ancestors` is the authoritative directive.