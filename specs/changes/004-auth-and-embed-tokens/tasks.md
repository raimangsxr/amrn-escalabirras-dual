# Tasks: 004-auth-and-embed-tokens

## Tasks

### Phase 0 — SDD

- [x] Update `specs/manifest.yml` (add `auth` + `004`).
- [x] Update `specs/contracts/api-rest/contract.md` (auth section,
      new endpoints, error codes).
- [x] Update `specs/contracts/persistence-postgres/contract.md`
      (`embed_tokens` table).
- [x] Update `specs/contracts/frontend-angular/contract.md` (auth
      flow, AuthService, login, tokens).
- [x] Create `specs/contracts/auth/contract.md`.
- [x] Create `specs/changes/004-auth-and-embed-tokens/spec.md`.
- [x] Create `specs/changes/004-auth-and-embed-tokens/plan.md`.
- [x] Create this task list.
- [x] Create `specs/changes/004-auth-and-embed-tokens/context-pack.md`.

### Phase 1 — Backend

- [x] Update `backend/app/config.py` (Settings with
      admin_password, jwt_secret, jwt_ttl_seconds, frame_ancestors).
- [x] Update `.env.example` with the new env vars.
- [x] Add `backend/app/auth.py` (token + hash helpers).
- [x] Add `backend/app/security.py` (get_current_session).
- [x] Update `backend/app/models.py` (EmbedToken).
- [x] Add `backend/alembic/versions/0002_add_embed_tokens.py`.
- [x] Update `backend/app/schemas.py` (auth/token DTOs).
- [x] Add `backend/app/routers/auth.py`.
- [x] Add `backend/app/routers/tokens.py`.
- [x] Add `backend/app/middleware/frame_ancestors.py`.
- [x] Update `backend/app/main.py` (mount routers, middleware,
      update exception handler for 401).
- [x] Update `backend/app/routers/participants.py` and
      `backend/app/routers/leaderboard.py` to require Bearer.
- [x] Update `backend/tests/conftest.py` (auth_token fixture).
- [x] Update existing tests to send Bearer.
- [x] Add `backend/tests/test_auth.py`.
- [x] Add `backend/tests/test_embed_tokens.py`.
- [x] Add `backend/tests/test_protected_endpoints.py`.
- [x] Add `backend/tests/test_frame_ancestors.py`.
- [x] Run `pytest backend -v` until green.

### Phase 2 — Frontend

- [x] Update `src/environments/environment.ts` (and prod).
- [x] Add `src/app/auth/auth.service.ts`.
- [x] Add `src/app/auth/auth.interceptor.ts`.
- [x] Add `src/app/auth/auth.guard.ts`.
- [x] Add `src/app/login/login.component.{ts,html,css}`.
- [x] Add `src/app/main-view/main-view.component.{ts,html,css}`.
- [x] Add `src/app/tokens/tokens.component.{ts,html,css}`.
- [x] Update `src/app/app.component.{ts,html}` to bootstrap auth
      and render `<router-outlet>`.
- [x] Update `src/app/app-routing.module.ts` (routes + guard).
- [x] Update `src/app/app.module.ts` (interceptor + new
      components).
- [x] Run `tsc --noEmit -p tsconfig.app.json` until exit 0.
- [x] Run `ng build --configuration production --output-path
      /tmp/...` until green.

### Phase 3 — Validation

- [x] End-to-end smoke (curl) covering all the auth flows in
      R24.
- [x] Final consistency sweep (no `TODO`, no `localStorage`, no
      dead code, manifest consistent).

## Out of scope (recorded for future changes)

- Refresh tokens / sliding sessions.
- Rate limiting on `/v1/auth/login` (mitigated at the deployment
  layer).
- Multi-operator accounts.
- OAuth / external identity providers.
- Per-endpoint scope on embed tokens.
- Audit log of who pressed what.
- HTTPS / Nginx / custom domain / production deployment.
- Frontend unit tests (Karma specs for `AuthService`,
  `AppService`, components).
- Embed-token `expires_at` column and a cleanup job.