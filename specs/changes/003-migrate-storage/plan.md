# Plan: 003-migrate-storage

## Approach

The frontend keeps the same component tree (`src/app/**`) and the
same visual layout. Only `AppService` changes substantively: it
becomes an HTTP client that owns reactive streams. Components switch
from "call getters on every change-detection pass" to "subscribe via
the `async` pipe".

The work is structured so each step is independently verifiable:

1. SDD scaffolding (this change's own spec / plan / tasks /
   context-pack, plus the new `frontend-angular` contract).
2. Add `HttpClientModule`, environment files, and the
   `esModuleInterop` fix.
3. Rewrite `AppService` as an HTTP client with `BehaviorSubject`
   streams. Keep the public surface small and stable.
4. Update each component to consume observables via the `async`
   pipe. Remove the in-template method calls.
5. Add the error banner.
6. Delete dead code.
7. End-to-end smoke: backend up + Angular dev server + manual
   flow.
8. Archive `app-core`, update the manifest.

The frontend keeps using the existing celebration timer logic
(`confettiTime = 10000`, `confettiInterval = 2000`), but the
trigger moves from "any non-empty `setNewRecord`" to "an HTTP
response with `is_new_record: true`". The pre-existing bug where
the timer did not cancel prior timers is fixed: each new record
clears the previous timer.

## Steps

1. **Update `specs/manifest.yml`**:
   - Add `frontend-angular` to `contracts:`.
   - Add `003-migrate-storage` to `changes:` and mark it active.
   - Mark `app-core` for archival (move step at the end).
2. **Write `specs/contracts/frontend-angular/contract.md`**.
3. **Write `specs/changes/003-migrate-storage/{spec, plan, tasks,
   context-pack}.md`**.
4. **Add `src/environments/environment.ts`** with
   `{ apiBaseUrl: 'http://localhost:8000/v1' }`. Also
   `environment.prod.ts` so `ng build --configuration production`
   keeps working.
5. **Update `src/app/app.module.ts`**:
   - Add `HttpClientModule` to `imports`.
   - Remove `MatIconModule`.
6. **Update `tsconfig.json`** so `compilerOptions` includes
   `esModuleInterop: true`. Verify `tsc --noEmit` exits 0.
7. **Rewrite `src/app/services/app.service.ts`**:
   - Inject `HttpClient`.
   - Read `apiBaseUrl` from `environment`.
   - Define `currentSlots$`, `top3$`, `history$`, `celebrating$`,
     `error$` backed by `BehaviorSubject`s.
   - Implement `createParticipant(name, team)`, `addCrate(team)`,
     `removeCrate(team)`, `clearSlot(team)`, `dismissError()`.
   - Central HTTP error handler that maps backend `code` to a
     Spanish message and pushes it on `error$`.
   - Celebration timer that cancels on a new record.
8. **Update each component**:
   - `AppComponent`: subscribe via `async` to `currentSlots$` and
     `celebrating$`; render the error banner from `error$`.
   - `ManagerComponent`: bind slot events from team components to
     `AppService.addCrate/removeCrate/clearSlot`; remove the empty
     `createParticipant()`. Render the focus button with the
     existing keyboard bindings.
   - `TeamManagerRedComponent` / `TeamManagerBlueComponent`:
     subscribe to the corresponding slot; emit `newParticipantEvent`
     on Enter. Remove the silent-replace bug: do not emit if the
     slot is already occupied.
   - `ParticipantListComponent`: subscribe to `history$`.
   - `Top3Component`: subscribe to `top3$`.
   - `WinnerComponent`: take a participant `@Input`; receive it
     from the parent via `(celebrating$ | async)`.
9. **Delete dead code**:
   - `src/app/services/team.service.ts`.
   - `ManagerComponent.createParticipant()`.
10. **Validate**:
    - `node_modules/.bin/tsc --noEmit -p tsconfig.app.json` exits 0.
    - `node_modules/.bin/ng build --configuration development
      --output-path /tmp/escalabirras-fe-dev` succeeds.
    - `node_modules/.bin/ng build --configuration production
      --output-path /tmp/escalabirras-fe-prod` succeeds.
    - With the backend up on `localhost:8000` and `npm start` on
      the frontend, the manual flow from AC3 works.
11. **Archive `app-core`**:
    - `mkdir -p specs/archive` (it may already exist from earlier).
    - `mv specs/contracts/app-core specs/archive/app-core`.
    - Add a header note at the top of the archived contract pointing
      at `frontend-angular`.
    - Update `specs/manifest.yml`: remove `app-core` from
      `contracts:`, mark `001-current-behavior-baseline` as
      `status: superseded`.
12. **Final consistency sweep**:
    - `git grep localStorage src/` returns nothing.
    - `git grep TeamServiceService src/` returns nothing.
    - `git grep "MatIconModule" src/` returns nothing.
    - `grep -nR "TODO" specs/contracts/frontend-angular
      specs/changes/003-migrate-storage` returns nothing (except
      inside backticks describing the sweep).
    - `specs/manifest.yml` still points at `003-migrate-storage` as
      the active change.

## Risks

- **HTTP latency on every keystroke.** Each `a`/`z`/`s`/`x` press
  is now an HTTP round-trip. On `localhost` this is fine; on a
  remote backend the operator could outrun the network. Mitigation:
  if this becomes a problem, add an optimistic local cache. Out of
  scope for `003`.
- **Race conditions on rapid presses.** The backend serializes
  increments per participant via `SELECT ... FOR UPDATE`, so the
  server-side state is consistent. The client's `currentSlots$`
  is updated from the response, so it also stays consistent with
  the server's view after each press. If two presses cross in
  flight, the older response wins the slot; the operator will
  press `a` again to catch up.
- **Error recovery is manual.** If a request fails, the operator
  must retry. No automatic retry, no offline queue. Documented as
  a known limitation in `frontend-angular`.
- **No frontend tests.** This change accepts the existing lack of
  Karma specs. Manual smoke covers the critical flows.
- **`tsconfig.json` change touches every TS file.** Adding
  `esModuleInterop: true` is harmless (Angular already handles
  default imports), but if a downstream library used
  `import * as foo from ...` semantics differently it could shift
  types. Mitigation: rely on the existing `tsc --noEmit` to
  confirm nothing else breaks.
- **Archive move is irreversible at the file level.** The archived
  contract stays at `specs/archive/app-core/contract.md`. If we
  ever need to revive it as the live contract, we move the file
  back and update the manifest.
- **The legacy `app-core` contract is still referenced from the
  context packs of `001` and `002`.** Those references remain
  valid: `001` describes what `app-core` used to be, and `002`'s
  context pack mentions `app-core` as historical. No edits needed
  in those files.