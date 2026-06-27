# Context Pack: 003-migrate-storage

## Goal

Rewire the Angular frontend under `src/` from `localStorage` to the
FastAPI backend introduced by `002-backend-foundation`. At the end
of this change the frontend is fully online against the backend,
all `localStorage` references are gone, and `app-core` is archived.

## Relevant Contracts

- `specs/contracts/api-rest/contract.md` (live, owned by `002`)
- `specs/contracts/persistence-postgres/contract.md` (live, owned
  by `002`)
- `specs/contracts/frontend-angular/contract.md` (new, owned by
  this change)

`specs/contracts/app-core/contract.md` becomes archived at the end
of this change; it is not modified during the change.

## Current Understanding

- The Angular 16 SPA under `src/` has a single `AppService` that
  owns all state as plain mutable arrays and reads/writes
  `localStorage` directly in its constructor and in `saveParticipant`
  / `saveWinnerParticipant`.
- The components call getters on `AppService` from templates, so
  every change-detection pass re-reads the state.
- There is no HttpClient wiring; the only network code is the
  implicit zone.js handling.
- `tsc --noEmit -p tsconfig.app.json` is currently red because of
  the `js-confetti` default import. Adding `esModuleInterop: true`
  to `compilerOptions` fixes it.
- A FastAPI + Postgres backend is available on `localhost:8000`
  (introduced by `002-backend-foundation`), with `pytest backend`
  reporting 28/28 green and the API smoke-tested via `curl`.

## Files / Areas Likely Involved

### To be modified

- `src/app/app.module.ts` — add `HttpClientModule`, drop
  `MatIconModule`.
- `src/app/app.component.ts` and `src/app/app.component.html` —
  consume observables, render error banner.
- `src/app/app.component.css` — small style for the banner.
- `src/app/services/app.service.ts` — rewritten as an HTTP client
  with `BehaviorSubject`s.
- `src/app/manager/manager.component.ts` and
  `src/app/manager/manager.component.html` — bind focus button,
  drop the empty `createParticipant()`.
- `src/app/team-manager-red/team-manager-red.component.ts` and
  `.html` — read the current slot from `AppService`, emit
  `newParticipantEvent` on Enter.
- `src/app/team-manager-blue/team-manager-blue.component.ts` and
  `.html` — same as red, blue styling.
- `src/app/participant-list/participant-list.component.ts` and
  `.html` — consume `history$`.
- `src/app/top3/top3.component.ts` and `.html` — consume `top3$`.
- `src/app/winner/winner.component.ts` and `.html` — take a
  participant `@Input`, render confetti.
- `tsconfig.json` — add `esModuleInterop: true`.

### To be added

- `src/environments/environment.ts` —
  `{ apiBaseUrl: 'http://localhost:8000/v1' }`.
- `src/environments/environment.prod.ts` — same value (production
  overrides live in a future change).

### To be deleted

- `src/app/services/team.service.ts` (dead code).

### Untouched

- `src/main.ts`, `src/index.html`, `src/styles.css`.
- `src/app/participant/participant.ts`,
  `src/app/participant/participant.component.{ts,html,css}` (the
  pure presentational `<n> cajas - <name>` line is unchanged).
- `src/app/app-routing.module.ts` (still has an empty routes
  array; no navigation is in scope).
- `src/assets/**` (logos and award icons are unchanged).
- `backend/**`, `docker-compose.yml`, `.env.example` (owned by
  `002`).
- `specs/contracts/api-rest/contract.md`,
  `specs/contracts/persistence-postgres/contract.md` (owned by
  `002`).
- `specs/changes/001-current-behavior-baseline/**` (historical).
- `specs/changes/002-backend-foundation/**` (already closed).

## Constraints

- **TypeScript strict + strict templates.** Existing
  `tsconfig.json` flags must stay green; the
  `esModuleInterop: true` addition must not introduce other
  warnings.
- **Angular 16.** No signals, no standalone components, no new
  features from later major versions.
- **Spanish UI strings.** Hardcoded Spanish remains the user-
  facing language. Errors surfaced through `error$` are also
  Spanish.
- **No authentication.** The backend is open. The frontend does
  not implement auth either.
- **Online-only.** The frontend cannot function without the
  backend. There is no offline cache in `003`.
- **No frontend tests.** `npm test` still runs against an empty
  Karma suite.
- **Single API base URL.** Read from
  `src/environments/environment.ts` at construction time.

## Validation Plan

Run narrow checks first, then broader ones.

1. **Standalone `tsc` typecheck (narrow, currently red).**

   ```bash
   node_modules/.bin/tsc --noEmit -p tsconfig.app.json
   ```

   Expectation after the change: exit 0. The `TS1259` error from
   `app-core` is gone.

2. **Angular development build (narrow).**

   ```bash
   node_modules/.bin/ng build --configuration development \
       --output-path /tmp/escalabirras-fe-dev
   ```

   Expectation: bundle produced; no template errors.

3. **Angular production build (narrow).**

   ```bash
   node_modules/.bin/ng build --configuration production \
       --output-path /tmp/escalabirras-fe-prod
   ```

   Expectation: bundle under the configured budgets (the
  `outputPath` override is required because of the WSL path).

4. **End-to-end smoke against the running backend (broad).**

   ```bash
   # Terminal 1: backend on SQLite
   cd backend
   DATABASE_URL=sqlite:///./dev.db alembic upgrade head
   DATABASE_URL=sqlite:///./dev.db \
       uvicorn app.main:app --host 127.0.0.1 --port 8000

   # Terminal 2: frontend dev server
   cd <repo>
   npm start
   ```

   Then in the browser at `http://localhost:4200`:

   1. Type "Ana" in the red input, press Enter. Red slot shows
      "Ana" and "0 cajas!".
   2. Click "Focus para jugar".
   3. Press `a` three times. Red slot shows "3 cajas!".
   4. Press `q`. Red slot resets to `- - -`.
   5. Type "Bea" in the blue input, press Enter. Press `s` four
      times. The "NUEVO RECORD!!" overlay fires once for the 4th
      increment (Bea overtakes Ana's 3).
   6. Stop the backend (`Ctrl-C` in terminal 1). Press `a` on the
      red slot again. The error banner appears with "No se pudo
      contactar con el servidor".

5. **Persistence smoke (broad).**

   1. With the backend up, register Ana and score some crates.
   2. Reload the browser. Ana is still in the history and Top 3
      (data is in Postgres, not `localStorage`).

6. **Dead-code sweep (broad).**

   ```bash
   git grep localStorage src/    # -> empty
   git grep TeamServiceService src/   # -> empty
   git grep "MatIconModule" src/      # -> empty
   ```

## Risks

- **HTTP latency on every keystroke.** Each `a`/`z`/`s`/`x` press
  is now a round-trip. On `localhost` the latency is single-digit
  ms; on a remote backend the operator could outrun the network.
  Mitigation: not in scope; documented in `frontend-angular`.
- **Race conditions on rapid presses.** The backend serializes per-
  participant via `SELECT ... FOR UPDATE`. The frontend's slot
  state reflects the most recent response. If two presses cross in
  flight, the older response wins the slot; the operator presses
  again to catch up. Documented.
- **No retry on transient errors.** The operator must click
  "Dismiss" and retry manually. A future change can add automatic
  retry with exponential backoff.
- **No frontend tests.** Manual smoke is the only verification.
  Acceptable for v1.
- **`tsconfig.json` change touches every TS file.** Adding
  `esModuleInterop: true` is harmless for the existing Angular
  libraries but could shift typings for a third-party package.
  Mitigation: `tsc --noEmit` is the gate.
- **Archive move is a structural change.** If we ever need to
  revive `app-core`, we move the file back and update the manifest.
- **`app-core` references in other SDD files stay valid.**
  `001`'s context pack describes `app-core` as historical, and
  `002`'s context pack mentions it as the pre-Postgres baseline.
  Neither needs editing.
- **No `Event` / `Tournament` scoping.** The flat `Participant`
  model limits the app to one event. A future change can introduce
  event scoping on both sides.

## Recommendations (do not create in this change)

- **`frontend-angular` contract** is created as part of `003`; the
  remaining areas that could become their own contracts are listed
  in `001-current-behavior-baseline/context-pack.md`'s
  Recommendations section and remain deferred.
- **`api-client-angular` contract** (not created): would document
  the Angular `HttpClient` usage, retry policies, and error
  mapping. Today those live in `frontend-angular`; a future change
  could split them out if they grow.
- **`celebration-overlay` contract** (not created): would own
  `js-confetti` timing, the `WinnerComponent` layout, and the
  cancellation behavior. Today it lives in `frontend-angular` and
  the `AppService` celebration stream.
- **`keyboard-input` contract** (not created): would own the
  key bindings on the focus button. Today it lives in
  `frontend-angular` and `ManagerComponent`'s template.