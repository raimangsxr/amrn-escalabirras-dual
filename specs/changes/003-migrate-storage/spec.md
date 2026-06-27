# Spec: 003-migrate-storage

## Problem

The Angular frontend under `src/` persists all state in the
browser's `localStorage` and has no network code at all. This
restricts the app to a single device and a single operator, and
makes the data brittle (Safari private mode, malformed JSON, no
sharing between devices).

Change `002-backend-foundation` introduced a FastAPI + Alembic +
PostgreSQL backend that exposes a REST contract at `/v1`. The
frontend now needs to be rewired to call that backend instead of
mutating `localStorage`. This is the change that turns the project
into a real client–server app.

## Goals

- Replace every `localStorage` read/write in `src/` with HTTP calls
  to the backend introduced in `002-backend-foundation`.
- Switch `AppService` from a plain mutable state container to an
  RxJS-driven state owner: `BehaviorSubject` per stream, `async`
  pipe in templates, `OnPush` change detection where applicable.
- Introduce loading and error UI (a banner) so the operator can see
  when the backend is unreachable or returns an error.
- Surface the backend's `is_new_record` flag from the increment
  response so the celebration overlay triggers only on real record
  breaks.
- Fix the two pre-existing bugs documented in `app-core` that this
  refactor naturally addresses: (1) `setNewRecord` did not cancel
  prior timers, (2) repeated Enter on the same name silently
  replaced the in-progress participant. The frontend now cancels
  timers and ignores re-creation while the slot is occupied.
- Add `esModuleInterop: true` to `tsconfig.json`'s `compilerOptions`
  so the standalone `tsc --noEmit` typecheck accepts the
  `js-confetti` default import (the `TS1259` baseline red is fixed).
- Remove dead code that becomes obvious once the service is
  refactored: `TeamServiceService`, the empty
  `ManagerComponent.createParticipant()`, and the unused
  `MatIconModule` import.
- Move `specs/contracts/app-core/` to `specs/archive/` and update
  the manifest so the historical baseline no longer claims to be the
  current behavior.

## Non-Goals

- No backend changes. The API and schema are owned by `002`.
- No new endpoints.
- No authentication, no multi-user, no polling/SSE for live updates
  (the frontend refetches after each mutation, which is enough for
  v1).
- No automated frontend tests (no Karma specs). End-to-end behavior
  is validated manually.
- No `Event` / `Tournament` scoping.
- No production deployment of the API or the frontend.

## Requirements

### Functional

- **R1.** `src/app/services/app.service.ts` exposes
  `currentSlots$`, `top3$`, `history$`, `celebrating$`, and
  `error$` as observables. All are hot streams backed by
  `BehaviorSubject`s.
- **R2.** `AppService` issues HTTP calls through the Angular
  `HttpClient`. The base URL comes from
  `src/environments/environment.ts`. On bootstrap it calls
  `GET /v1/history?limit=10` and `GET /v1/leaderboard/top?limit=3`
  in parallel and populates the streams.
- **R3.** `createParticipant(name, team)` issues
  `POST /v1/participants`. On success it sets
  `currentSlots$[team]` to the returned participant and refetches
  `history$` (and `top3$` defensively). It is a no-op when the
  target slot is already occupied.
- **R4.** `addCrate(team)` issues
  `POST /v1/participants/{id}/crates/increment`. On success it
  updates `currentSlots$[team]` and refetches `top3$`. If the
  response's `is_new_record` is `true`, it sets `celebrating$` and
  schedules a 12 s `setTimeout` to clear it, cancelling any prior
  pending timer.
- **R5.** `removeCrate(team)` issues
  `POST /v1/participants/{id}/crates/decrement`. On success it
  updates the slot and refetches `top3$`. On `409 crates_underflow`
  it surfaces an error on `error$` and leaves the slot unchanged.
- **R6.** `clearSlot(team)` sets `currentSlots$[team] = null` and
  does not call the backend.
- **R7.** HTTP errors are mapped through a central handler to
  `error$`. The mapping table is documented in the
  `frontend-angular` contract.
- **R8.** All components consume observables via the `async` pipe.
  No component calls service methods from a template binding that
  returns a value (the `getNewRecord()` pattern is gone).
- **R9.** The root component renders an error banner when
  `error$` is non-null. The banner has a "Dismiss" button that calls
  `AppService.dismissError()`.

### Non-functional

- **R10.** `tsc --noEmit -p tsconfig.app.json` exits 0. The
  `TS1259` error documented in `app-core` is fixed by adding
  `esModuleInterop: true` to `tsconfig.json`'s `compilerOptions`.
- **R11.** `ng build --configuration production --output-path /tmp/...`
  succeeds.
- **R12.** `npm start` (Angular dev server) starts without errors
  and the page renders against the backend.

### Cleanup

- **R13.** `src/app/services/team.service.ts` is deleted.
- **R14.** The empty `ManagerComponent.createParticipant()` method
  is deleted.
- **R15.** `MatIconModule` is removed from `AppModule.imports` and
  the package is left installed (a future change may remove the
  dep entirely).

### SDD / archival

- **R16.** `specs/contracts/app-core/` is moved to
  `specs/archive/app-core/`. A short header note is added at the
  top of the archived contract explaining why it is archived and
  pointing at `frontend-angular` as the live equivalent.
- **R17.** `specs/manifest.yml` removes `app-core` from
  `contracts:`, marks `001-current-behavior-baseline` as
  `status: superseded`, and points `active:` at `003-migrate-storage`.

## Acceptance Criteria

- **AC1.** `tsc --noEmit -p tsconfig.app.json` exits 0. No `TS1259`
  error.
- **AC2.** `ng build --configuration production --output-path
  /tmp/escalabirras-fe-prod` produces a bundle.
- **AC3.** With the backend running on `localhost:8000` and
  `npm start` on the frontend, the operator can register a
  participant, increment crates, finalize a slot, and see the
  celebration trigger exactly once when the participant overtakes the
  previous max.
- **AC4.** Reloading the frontend in the browser after running a
  few participants preserves history and Top 3 (data now lives in
  Postgres, not `localStorage`).
- **AC5.** When the backend is stopped, the frontend shows the
  error banner on the next mutation and does not lose its slot
  state.
- **AC6.** `git grep localStorage src/` returns nothing.
- **AC7.** `git grep TeamServiceService src/` returns nothing.
- **AC8.** `git grep "MatIconModule" src/` returns nothing.
- **AC9.** `git status spec/` shows the `app-core` move and the new
  `frontend-angular` directory; `specs/manifest.yml` reflects
  `003-migrate-storage` as active and `app-core` as archived.
- **AC10.** All four SDD files for `003-migrate-storage`
  (`spec.md`, `plan.md`, `tasks.md`, `context-pack.md`) have no
  `TODO` placeholders in the populated sections.