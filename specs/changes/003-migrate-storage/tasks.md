# Tasks: 003-migrate-storage

## Tasks

- [x] Write `specs/contracts/frontend-angular/contract.md`.
- [x] Write `specs/changes/003-migrate-storage/spec.md`.
- [x] Write `specs/changes/003-migrate-storage/plan.md`.
- [x] Write `specs/changes/003-migrate-storage/context-pack.md`.
- [x] Write this task list.
- [x] Add `src/environments/environment.ts` and
      `src/environments/environment.prod.ts`.
- [x] Add `HttpClientModule` to `src/app/app.module.ts`.
- [x] Remove `MatIconModule` from `src/app/app.module.ts`.
- [x] Add `esModuleInterop: true` to `tsconfig.json` compilerOptions.
- [x] Rewrite `src/app/services/app.service.ts` as an HTTP client
      with `BehaviorSubject` streams.
- [x] Update `src/app/app.component.ts` and
      `src/app/app.component.html` to consume observables.
- [x] Update `src/app/manager/manager.component.ts` and
      `.html` to bind focus-button events and remove the empty
      `createParticipant()`.
- [x] Update `src/app/team-manager-red/team-manager-red.component.ts`
      and `.html`.
- [x] Update `src/app/team-manager-blue/team-manager-blue.component.ts`
      and `.html`.
- [x] Update `src/app/participant-list/participant-list.component.ts`
      and `.html`.
- [x] Update `src/app/top3/top3.component.ts` and `.html`.
- [x] Update `src/app/winner/winner.component.ts` and `.html`.
- [x] Add the error banner UI (in `AppComponent`'s template).
- [x] Delete `src/app/services/team.service.ts`.
- [x] Run `tsc --noEmit -p tsconfig.app.json` and confirm it exits 0.
- [x] Run `ng build --configuration development --output-path
      /tmp/escalabirras-fe-dev` and confirm success.
- [x] Run `ng build --configuration production --output-path
      /tmp/escalabirras-fe-prod` and confirm success.
- [x] End-to-end smoke against the running backend (SQLite is fine).
- [x] Move `specs/contracts/app-core/` to `specs/archive/app-core/`
      and prepend a "superseded by frontend-angular" note.
- [x] Update `specs/manifest.yml` to reflect `frontend-angular`,
      `003-migrate-storage`, archived `app-core`, and superseded
      `001`.
- [x] Final consistency sweep: no `localStorage`, no
      `TeamServiceService`, no `MatIconModule`, no `TODO` placeholders
      in the new SDD files.

## Out of scope (recorded for future changes)

- Frontend unit tests (Karma + Jasmine). `003` accepts the lack of
  automated coverage.
- Optimistic local cache for offline tolerance.
- Automatic retry with exponential backoff on transient HTTP errors.
- Polling or SSE for live updates across multiple clients.
- Auth, multi-user, multi-event scoping.
- `Event` / `Tournament` domain expansion.
- Production deployment of the API and the frontend.
- Removing the `@angular/material` package entirely (the unused
  `MatIconModule` import is gone, but the dep stays installed).