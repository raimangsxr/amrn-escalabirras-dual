# Context Pack: 009-admin-event-config

## Goal

Move the operator-only configuration (event info + embed tokens +
logout) out of the public tournament view into a dedicated `/admin`
route. The tournament page (`/`) becomes a pure, buttonless public
view with no navigation to admin. Event info (title, subtitle)
becomes editable and persisted on the backend, shared by every
client.

## Relevant Contracts

- `specs/contracts/api-rest/contract.md` (updated — new
  `/v1/event` resource)
- `specs/contracts/persistence-postgres/contract.md` (updated —
  new `event` singleton table)
- `specs/contracts/frontend-angular/contract.md` (updated — new
  `/admin` route, `EventService`, removal of the Tokens/Salir
  buttons from `MainViewComponent`)

## Current Understanding

- `MainViewComponent` currently exposes:
  - Hardcoded `title = "II Torneo Motero de Escalabirras"` and
    `subtitle = "XV Concentración Motera Ría de Noia"`.
  - A "Tokens" button that opens `TokensComponent` as an in-page
    modal.
  - A "Salir" button that calls `AuthService.logout()` and navigates
    to `/login`.
- The `App` routing has three entries: `/login`, `/` (main view,
  guarded), and `**` → `/`.
- The frontend has no concept of an "admin" route. Tokens and
  logout are reachable from inside the main view, which makes the
  main view inappropriate for unattended public displays.
- The tournament display (logos, top-3, history) is meant to be
  shown on a venue projector. The operator must not need to be
  present at the projector to manage tokens or change event
  info; they should be able to do it from any client pointed at
  `/admin`.
- The event info is currently the same string for every client and
  every event. Persisting it on the backend lets the operator set
  it once and have every connected display pick it up.

## User-facing decisions

- `/admin` is a separate route, protected by `authGuard` (same
  guard as `/`). The operator navigates to it directly in the URL
  bar (or via a bookmark); there is **no** link, button, or any
  other navigation affordance from `/` to `/admin`.
- The login flow continues to land on `/` after a successful
  login (unchanged).
- The `/admin` page hosts three sections in a single scrollable
  card:
  1. **Info del evento** — title + subtitle inputs and a "Guardar"
     button. `EventService` PUTs the change.
  2. **Tokens de embed** — the existing `TokensComponent`
     (create / list / revoke) is embedded inline, no longer in a
     modal.
  3. **Sesión** — a "Salir" button that calls
     `AuthService.logout()` and navigates to `/login`.
- The tournament page at `/` removes the Tokens and Salir buttons
  entirely. Its title/subtitle are no longer hardcoded: they are
  fetched by `EventService.bootstrap()` (called once at app
  startup) and rendered from `EventService.event$`.

## Files / Areas Likely Involved

### Backend — new

- `backend/app/models.py` — add `Event` singleton model
  (`id=1`, `title`, `subtitle`, `updated_at`).
- `backend/app/schemas.py` — add `EventRead`, `EventUpdate`.
- `backend/app/routers/event.py` — `GET /v1/event` (Bearer) and
  `PUT /v1/event` (Bearer).
- `backend/alembic/versions/0003_add_event.py` — new migration;
  seeds the singleton row with the current hardcoded values so
  fresh installs render the same text the app has been showing
  until now.
- `backend/tests/test_event.py` — covers GET (no row → 404,
  with row → 200), PUT (rejects empty/long strings), and Bearer
  enforcement.

### Backend — modified

- `backend/app/main.py` — register the new router.

### Frontend — new

- `src/app/services/event.service.ts` — `event$` stream, `bootstrap()`
  fetches once, `update(title, subtitle)` PUTs.
- `src/app/admin/admin.component.{ts,html,css}` — three-section
  admin page; embeds `<app-tokens>`; handles logout.

### Frontend — modified

- `src/app/app-routing.module.ts` — add `{ path: 'admin',
  component: AdminComponent, canActivate: [authGuard] }`.
- `src/app/app.module.ts` — declare `AdminComponent`.
- `src/app/main-view/main-view.component.{ts,html}` — drop
  `title`/`subtitle` hardcoded fields, drop `showTokens`,
  `openTokens`, `closeTokens`, `logout` methods, drop the Tokens
  and Salir buttons, drop the modal wrapper around
  `<app-tokens>`. Subscribe to `EventService.event$` for the
  header text.
- `src/app/app.component.ts` — call `EventService.bootstrap()` at
  startup (in addition to `AuthService.bootstrap()`).

### Untouched

- `src/app/tokens/...` — same component, just hosted under `/admin`
  instead of in a modal in `MainViewComponent`.
- `src/app/login/...`, `src/app/auth/...`,
  `src/app/manager/...`, `src/app/team-manager-*`,
  `src/app/top3/...`, `src/app/participant-list/...`,
  `src/app/participant/...`, `src/app/winner/...`.
- `src/app/services/app.service.ts` — still owns tournament state.
- `src/app/services/layout.service.ts` — unchanged.
- `src/styles.css`, `src/index.html`, `src/main.ts`.
- `backend/alembic/versions/0001_create_participants.py`,
  `backend/alembic/versions/0002_add_embed_tokens.py`.

## Constraints

- **No admin affordance on `/`.** The main view's template must
  contain no anchor, button, routerLink, or other navigation that
  points at `/admin` (or at `AdminComponent`).
- **`/admin` is protected by the same `authGuard` as `/`.** No
  changes to the guard logic; no separate "admin guard".
- **Event info is a singleton.** There is exactly one row
  (`id = 1`). PUT replaces the row's contents in place; the row
  is created on first PUT if it does not exist.
- **Validation mirrors `Participant.name`.** `title` and
  `subtitle` are trimmed; `1 <= len <= 80`. Empty or too-long
  values → `422 invalid_event` (matches the
  `validation_error` shape used elsewhere).
- **No rate limiting in v1.** Documented in the auth contract;
  unchanged.
- **Migration seeds the singleton** so the public view keeps
  showing the same Spanish text out of the box, even before any
  operator has visited `/admin`.
- **No telemetry, no audit log** of who edited the event info.
  `updated_at` is the only metadata.

## Validation Plan

1. **Backend unit tests (narrow).**

   ```bash
   source /tmp/venv-002/bin/activate
   pytest backend/tests/test_event.py -v
   pytest backend -v
   ```

   Expectation: full suite green, including the new event tests
   and the existing tests that depend on the auth fixtures.

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
   TOKEN=$(curl -s -X POST http://127.0.0.1:8000/v1/auth/login \
       -H 'Content-Type: application/json' \
       -d '{"password":"secret123"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["session_token"])')

   # 1. GET event without auth -> 401
   curl -i http://127.0.0.1:8000/v1/event

   # 2. GET event with auth -> 200 + seeded title/subtitle
   curl -i -H "Authorization: Bearer $TOKEN" \
       http://127.0.0.1:8000/v1/event

   # 3. PUT event with new title/subtitle -> 200
   curl -i -X PUT -H "Authorization: Bearer $TOKEN" \
       -H 'Content-Type: application/json' \
       -d '{"title":"Demo","subtitle":"Sub"}' \
       http://127.0.0.1:8000/v1/event

   # 4. PUT event with empty title -> 422 invalid_event
   curl -i -X PUT -H "Authorization: Bearer $TOKEN" \
       -H 'Content-Type: application/json' \
       -d '{"title":"","subtitle":"x"}' \
       http://127.0.0.1:8000/v1/event

   # 5. GET event again -> 200 + updated values
   curl -i -H "Authorization: Bearer $TOKEN" \
       http://127.0.0.1:8000/v1/event
   ```

5. **Manual UI walk-through (broad, manual).**

   1. `npm start`. Open `http://localhost:4200`. Log in.
   2. Confirm the main page (`/`) shows **no** Tokens button,
      **no** Salir button, **no** link to admin.
   3. Manually navigate to `http://localhost:4200/admin`. Confirm
      the page renders the three sections (event info, tokens,
      logout).
   4. Edit the title and subtitle, click Guardar. Refresh the
      page; the main view at `/` now reflects the new values.
   5. Create an embed token from `/admin`. Open
      `http://localhost:4200/?embed_token=<token>` in a private
      tab; the main view loads directly with no login prompt.
   6. Click Salir in `/admin`. The router lands on `/login`.

6. **Final consistency sweep (broad).**

   ```bash
   grep -nR "admin" src/app/main-view
   git grep routerLink src/app/main-view
   git grep "showTokens\|openTokens\|closeTokens" src/
   ```

   All should return nothing.

## Risks

- **Singleton drift.** A future change may want multiple events.
  The schema leaves room for that by giving the table a synthetic
  `id` PK rather than a fixed primary key on `title`.
- **No optimistic concurrency on PUT.** Two operators editing the
  event at the same time will silently overwrite each other.
  Acceptable for v1 (single operator); documented.
- **Empty title would hide the headline on `/`.** Rejected at the
  backend (`422 invalid_event`) and at the frontend
  (`[disabled]` on Guardar when empty).
- **Migration seeds a Spanish string.** If the deployment locale
  changes, the operator can edit it from `/admin`; the seed only
  applies to fresh installs and existing rows are left untouched
  by `upgrade()`.

## Out of scope

- Multi-event support, per-tenant scoping.
- Audit log of event edits.
- Real-time push of event changes (the public display picks up
  the new value on its next page load).
