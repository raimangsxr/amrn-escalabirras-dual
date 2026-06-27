# Context Pack: 004-auth-and-embed-tokens

## Goal

Add single-operator password login and a long-lived embed-token
mechanism so the escalabirras app can be published to the public
internet and embedded in iframes of unrelated origins without
prompting the operator for the password each time the iframe
loads.

## Relevant Contracts

- `specs/contracts/auth/contract.md` (new, owned by this change)
- `specs/contracts/api-rest/contract.md` (updated)
- `specs/contracts/persistence-postgres/contract.md` (updated)
- `specs/contracts/frontend-angular/contract.md` (updated)

## Current Understanding

- Backend (`backend/`) is FastAPI 0.115 + SQLAlchemy 2.0 + Alembic +
  Postgres 16 (with SQLite for tests). All `/v1/*` endpoints are
  currently open.
- Frontend (`src/`) is Angular 16, calls the backend via
  `HttpClient`, stores nothing locally except session memory. No
  auth, no iframe support.
- The app is going public on the internet; the current "no auth"
  posture is unacceptable.
- The app will sometimes render inside an iframe of a parent
  application at a different origin. The parent has no way to set
  HTTP headers on the iframe's initial GET, so the embed token
  rides in `?embed_token=…` and the frontend exchanges it for a
  JWT.
- A single operator runs the venue. There is no need for
  multi-operator in v1.

## Files / Areas Likely Involved

### Backend — new

- `backend/app/auth.py` — JWT create/decode, embed-token hash and
  generation.
- `backend/app/security.py` — FastAPI dependency
  `get_current_session`.
- `backend/app/routers/auth.py` — `/v1/auth/login`,
  `/v1/auth/embed-token`, `/v1/auth/logout`, `/v1/auth/me`.
- `backend/app/routers/tokens.py` — `/v1/tokens` CRUD.
- `backend/app/middleware/frame_ancestors.py` — CSP /
  X-Frame-Options middleware.
- `backend/alembic/versions/0002_add_embed_tokens.py` — initial
  `embed_tokens` migration.
- `backend/tests/test_auth.py`,
  `backend/tests/test_embed_tokens.py`,
  `backend/tests/test_protected_endpoints.py`,
  `backend/tests/test_frame_ancestors.py`.

### Backend — modified

- `backend/app/config.py` — new env vars.
- `backend/app/models.py` — add `EmbedToken`.
- `backend/app/schemas.py` — auth + token DTOs.
- `backend/app/main.py` — register new routers + middleware.
- `backend/app/routers/participants.py`,
  `backend/app/routers/leaderboard.py` — add
  `Depends(get_current_session)`.
- `backend/tests/conftest.py` — add `auth_token` fixture.
- `backend/tests/test_participants.py`, `test_crates.py`,
  `test_leaderboard.py`, `test_history.py` — use the fixture.
- `.env.example` — document the new env vars.

### Frontend — new

- `src/app/auth/auth.service.ts` — session state, bootstrap,
  login, logout, exchangeEmbedToken.
- `src/app/auth/auth.interceptor.ts` — add Bearer, handle 401.
- `src/app/auth/auth.guard.ts` — `CanActivateFn`.
- `src/app/login/login.component.{ts,html,css}` — password form.
- `src/app/main-view/main-view.component.{ts,html,css}` — wraps
  the current app view + Tokens + Salir buttons.
- `src/app/tokens/tokens.component.{ts,html,css}` — list / create
  / revoke embed tokens.

### Frontend — modified

- `src/app/app.component.{ts,html}` — bootstrap auth, render
  `<router-outlet>`.
- `src/app/app-routing.module.ts` — routes + guard.
- `src/app/app.module.ts` — register interceptor, new components.
- `src/environments/environment.ts` + `.prod.ts` — `loginPath`,
  `embedTokenQueryParam`.

### Untouched

- `src/app/services/app.service.ts`, `src/app/manager/...`,
  `src/app/team-manager-*/...`, `src/app/top3/...`,
  `src/app/participant-list/...`, `src/app/participant/...`,
  `src/app/winner/...`. These keep their behaviour and continue
  to talk to the backend via `AppService`. They are now hosted
  inside `MainViewComponent` instead of `AppComponent`, but no
  source change is required inside them.
- `src/styles.css`, `src/index.html`, `src/main.ts`.
- `backend/alembic/versions/0001_create_participants.py`,
  `docker-compose.yml`, `backend/README.md` (only the README may
  need a one-line update; tracked as out-of-scope here to avoid
  drift between contract and implementation).

## Constraints

- **Strict TypeScript** with `strictTemplates` stays green; the
  interceptor must be a proper `HttpInterceptorFn`.
- **Angular 16.** No signals, no standalone APIs.
- **JWT secret ≥ 32 chars.** Backend refuses to start otherwise.
- **No cookies.** All auth flows use `Authorization: Bearer`.
- **CORS unchanged** in dev (`localhost:4200` → `localhost:8000`).
- **`sessionStorage`, not `localStorage`**, for the JWT.
- **`frame-ancestors` configurable** via `FRAME_ANCESTORS` env var.
- **No rate limiting in v1.** Documented.
- **Single operator.** No operator table.
- **Embed tokens grant full access.** No scopes in v1.
- **CSP `frame-ancestors` and `X-Frame-Options` are both set.**
  `ALLOW-FROM` is deprecated but still respected as a fallback by
  older browsers.

## Validation Plan

Run narrow checks first, then broader ones.

1. **Backend unit tests (narrow).**

   ```bash
   source /tmp/venv-002/bin/activate
   pytest backend -v
   ```

   Expectation: full suite green, including the new auth tests and
   the updated existing tests that send Bearer.

2. **Standalone `tsc` typecheck (narrow).**

   ```bash
   node_modules/.bin/tsc --noEmit -p tsconfig.app.json
   ```

   Expectation: exit 0.

3. **Angular production build (narrow).**

   ```bash
   node_modules/.bin/ng build --configuration production \
       --output-path /tmp/escalabirras-fe-prod
   ```

   Expectation: bundle produced; no template errors.

4. **End-to-end smoke against the running backend (broad).**

   ```bash
   cd backend
   DATABASE_URL=sqlite:///./dev.db \
       ADMIN_PASSWORD=secret123 \
       JWT_SECRET=$(head -c 48 /dev/urandom | base64) \
       alembic upgrade head
   DATABASE_URL=sqlite:///./dev.db \
       ADMIN_PASSWORD=secret123 \
       JWT_SECRET=$(head -c 48 /dev/urandom | base64) \
       uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

   Then in another shell:

   ```bash
   # 1. healthz is open
   curl -i http://127.0.0.1:8000/healthz

   # 2. protected endpoint without Bearer -> 401
   curl -i http://127.0.0.1:8000/v1/participants/1

   # 3. login with wrong password -> 401
   curl -i -X POST http://127.0.0.1:8000/v1/auth/login \
       -H 'Content-Type: application/json' \
       -d '{"password":"wrong"}'

   # 4. login with right password -> 200 + JWT
   TOKEN=$(curl -s -X POST http://127.0.0.1:8000/v1/auth/login \
       -H 'Content-Type: application/json' \
       -d '{"password":"secret123"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["session_token"])')

   # 5. protected endpoint with Bearer -> 200/404 (depending on data)
   curl -i -H "Authorization: Bearer $TOKEN" \
       http://127.0.0.1:8000/v1/history

   # 6. create an embed token
   ET=$(curl -s -X POST http://127.0.0.1:8000/v1/tokens \
       -H "Authorization: Bearer $TOKEN" \
       -H 'Content-Type: application/json' \
       -d '{"name":"dashboard"}' \
       | python3 -c 'import sys,json; print(json.load(sys.stdin)["token"])')

   # 7. exchange embed token for a fresh JWT
   TOKEN2=$(curl -s -X POST http://127.0.0.1:8000/v1/auth/embed-token \
       -H 'Content-Type: application/json' \
       -d "{\"token\":\"$ET\"}" \
       | python3 -c 'import sys,json; print(json.load(sys.stdin)["session_token"])')

   # 8. the new JWT also works on protected endpoints
   curl -i -H "Authorization: Bearer $TOKEN2" http://127.0.0.1:8000/v1/history

   # 9. CSP / X-Frame-Options present
   curl -i http://127.0.0.1:8000/v1/auth/login \
       -H 'Origin: http://localhost:4200' \
       -X OPTIONS
   ```

5. **Iframe-like URL test (broad, manual).** Open
   `http://localhost:4200/?embed_token=$ET` in a browser. The
   app should load directly into the main view without showing
   the login screen. (Documented as a manual step; not
   automatable in CI without a headless browser.)

6. **Final consistency sweep (broad).**

   ```bash
   grep -nR "TODO" specs/contracts/auth specs/changes/004-auth-and-embed-tokens
   git grep localStorage src/
   git grep TeamServiceService src/
   git grep MatIconModule src/
   ```

   All should return nothing.

## Risks

- **`ADMIN_PASSWORD` and `JWT_SECRET` are required env vars.** If
  either is missing, the backend fails to start. The README and
  `.env.example` document both.
- **JWT secret rotation invalidates sessions.** Documented.
- **Embed tokens never auto-expire.** An operator must revoke them
  manually. Documented.
- **`X-Frame-Options: ALLOW-FROM` is deprecated in modern
  browsers** but kept as a fallback. `Content-Security-Policy:
  frame-ancestors` is the authoritative directive.
- **No rate limit on login.** A 6-character password can be brute-
  forced in minutes. Document minimum length in the README.
- **`sessionStorage` trade-off.** Closing the tab logs the
  operator out. The operator re-authenticates by typing the
  password. Documented.
- **Cross-origin URL visibility.** The `embed_token` is briefly
  visible in the iframe's URL bar before `history.replaceState`.
  Anyone with access to the parent's DOM could read it during
  that window. Mitigation: the exchange happens on bootstrap; the
  URL is cleaned synchronously after the response.
- **SQLite vs Postgres for tests.** Auth code is pure-Python
  (HS256, sha256, ORM), so SQLite is sufficient for the tests.
- **No frontend unit tests.** Manual smoke + backend tests cover
  the auth logic; the frontend wiring is verified by the E2E
  smoke.

## Recommendations (do not create in this change)

- **`audit-log` contract** (not created): would own a log of
  failed logins, embed-token creations/revocations, and operator
  actions. Today the only audit data is `created_at`,
  `last_used_at`, `revoked_at` on `embed_tokens`. A future change
  could add a dedicated audit table.
- **`refresh-token` contract** (not created): would document a
  sliding-session mechanism. v1 uses 24 h JWT only; on expiry the
  operator re-authenticates.
- **`rate-limit` contract** (not created): would document limits
  on `/v1/auth/login` and `/v1/auth/embed-token`. v1 delegates
  this to the deployment layer (Cloudflare / WAF).
- **`operator-account` contract** (not created): would document
  multi-operator support. v1 has a single password.