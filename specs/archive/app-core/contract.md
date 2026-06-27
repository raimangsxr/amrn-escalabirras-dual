# app-core Contract (ARCHIVED)

> **Status:** superseded. This contract described the `localStorage`-backed
> Angular SPA that existed before changes `002-backend-foundation` and
> `003-migrate-storage` rewired the project onto FastAPI + PostgreSQL.
>
> The live contract is now `specs/contracts/frontend-angular/contract.md`
> (introduced by change `003-migrate-storage`). It is the source of truth
> for the current Angular frontend behavior.
>
> This file is kept for historical reference: it documents what the app
> did before the backend migration. Do **not** update it as if it were
> current; it is frozen.

## Purpose

Describe the current behavior of the **amrn-escalabirras-team** single-page web
application as observed from the source under `src/`. This contract is the
source of truth for what the app already does; it is not a proposal.

## Current Behavior

The application is a Spanish-language Angular 16 single-page app used at a live
motorcycle club event ("II Torneo Motero de Escalabirras" / "XV Concentración
Motera Ría de Noia") to count how many beer crates each participant drinks in a
two-team head-to-head drinking game.

- It is a fully client-side SPA: no backend, no HTTP calls, no routing.
- All persistent state lives in the browser's `localStorage` and is
  per-origin (moving the app to a new origin effectively resets state).
- The user interface is a single screen divided into three vertical
  columns: a participant history list on the left, a "Torre Roja" (red
  team) panel in the middle, and a "Torre Azul" (blue team) panel on the
  right.
- Two players are active simultaneously, one per team. While the focus
  is on the central "Focus para jugar" button, the operator drives the
  scoring with keyboard shortcuts (see *APIs / Interfaces*). There is
  **no automatic focus management** after typing a name — after pressing
  Enter in a team input, focus stays on that input and the operator
  must click the focus button to use keyboard shortcuts.
- A confetti-driven "NUEVO RECORD!!" overlay appears for ~12 seconds
  whenever a new top crates count is reached. The overlay's background
  flips between two indigo shades at every change-detection pass via a
  `Math.random()` call bound in `[ngClass]`, so the colour can flicker
  while it is shown.

## User Flows

1. **App load.**
   - `AppService` constructor reads `localStorage.getItem('allParticipants')`
     and `localStorage.getItem('winnerParticipants')`.
   - If either key is missing, both lists are seeded with 10 placeholder
     `Participant` entries (`{ id: 0, name: '- - -', crates: 0 }`).
   - Two `currentParticipants` slots (red = index 0, blue = index 1) start
     as placeholders.

2. **Register a participant on a team.**
   - Operator types a name (max 20 characters, enforced by the HTML
     `maxlength` attribute) in the red or blue team input field and
     presses Enter.
   - If the name is non-empty, a new `Participant` is created via
     `AppService.createParticipant(name)` (assigns the next monotonic
     `id`), and the corresponding `currentParticipants` slot is
     replaced with it through the `newParticipantEvent` `@Output()` of
     the team component.
   - The input's `[(ngModel)]` is bound to a component-local `name`
     string that **is not reset** after `createParticipant()` runs.
     The typed text therefore stays visible in the input field, focus
     stays on the input, and a second Enter press without changes
     would create another participant with the same name and silently
     replace the slot. To use keyboard shortcuts, the operator must
     click the "Focus para jugar" button first.

3. **Score crates live.**
   - Operator clicks the central "Focus para jugar" button to give it focus,
     then uses keyboard shortcuts: `a`/`z` for red (`+`/`-` crate),
     `s`/`x` for blue, `q` to finalize the red player, `w` to finalize the
     blue player.
   - Each `+` increments `crates`; each `-` decrements but never below 0.
   - Pressing the shortcuts while no participant is loaded on a team is a
     no-op (guarded by `id === 0`).

4. **Finish a player's run.**
   - Pressing `q` or `w` calls `AppService.finishGame(participant, team)`,
     which:
     - returns immediately if the slot is still the placeholder (`id === 0`);
     - appends the player to `allParticipants` (persisted);
     - appends the player to `winnerParticipants` (persisted);
     - if the run produced a new max crates count, schedules
       `setNewRecord(participant)` which launches the confetti overlay;
     - resets the team slot to the placeholder so a new player can be loaded.

5. **Display top 3 and history.**
   - The top center always shows the Top 3 by crates descending (gold,
     silver, bronze), recomputed on every change detection cycle from
     `winnerParticipants`. Because `winnerParticipants` is append-only
     and is seeded with 10 placeholder entries on first run, the Top 3
     displays `- - -` until the first real participant ties or beats
     `crates: 0`. The placeholder seed is never cleaned out.
   - The left column shows the last 10 participants from
     `allParticipants`, sorted by `id` descending, plus a total count
     that excludes placeholders (`p.id > 0`). The same placeholder seed
     means the history list shows `- - -` entries until there are at
     least 10 real participants.
   - `allParticipants` and `winnerParticipants` are kept in sync
     because `finishGame` calls both `saveParticipant` and
     `saveWinnerParticipant` on every finalized run. The Top 3 is
     therefore the all-time Top 3; there is no time-window or
     per-event scoping despite the "winner" naming.

6. **New record overlay.**
   - When triggered, the main UI is hidden and `WinnerComponent` is shown
     full-screen with the participant's name and crate count, plus a
     `js-confetti` animation that runs for ~10 s with 2 s bursts of mixed
     confetti shapes and emojis, and then clears itself after ~12 s.

## Data and State

### Domain model

```ts
interface Participant {
  id: number;       // 0 means "empty slot / placeholder"; > 0 is monotonic
  name: string;     // up to 20 chars (UI enforced via maxlength)
  crates: number;   // non-negative integer; number of beer crates consumed
}
```

The placeholder sentinel is `{ id: 0, name: '- - -', crates: 0 }`. Any entry
with `id === 0` is considered "no player loaded on this team slot" and is
skipped or guarded in mutating operations.

### In-memory state (owned by `AppService`, root-provided singleton)

| Field | Type | Description |
| --- | --- | --- |
| `currentParticipants` | `Participant[2]` | `[0]` is the red team slot, `[1]` is the blue team slot. Starts as two placeholders. |
| `allParticipants` | `Participant[]` | Append-only history of every finished run. Seeded with 10 placeholders on first run. |
| `winnerParticipants` | `Participant[]` | Same as above but used for the Top 3 leaderboard. Seeded with 10 placeholders on first run. |
| `newRecord` | `Participant \| null` | Non-null while the celebration overlay is shown. |
| `confettiTime` | `number` | `10000` ms of total celebration duration. |
| `confettiInterval` | `number` | `2000` ms between confetti bursts. |
| `jsConfetti` | `JSConfetti` | `js-confetti` instance used to render the celebration. |

### Persistence

- Storage: browser `localStorage`, JSON-encoded.
- Storage is per-origin; serving the built app from a different origin
  effectively resets all state for that browser.
- Keys written by `AppService`:
  - `allParticipants` -> `JSON.stringify(allParticipants)`
  - `winnerParticipants` -> `JSON.stringify(winnerParticipants)`
- Writes happen on every `saveParticipant` and `saveWinnerParticipant`,
  i.e. on every `finishGame` call. There is no debouncing, no quota
  handling, and no migration.
- Reads happen once in the `AppService` constructor; after that, the
  in-memory copy is the source of truth within the session.
- Both `localStorage.getItem(...)` calls use a non-null assertion (`!`),
  which would throw if the keys were ever read before the seed branch.
  In practice the constructor guards with `if (!allParticipants)`
  first, so the assertion only runs when a value is present.
- Malformed JSON in either key would throw an uncaught `SyntaxError`
  at app bootstrap, leaving the app unusable until the offending key
  is cleared manually from devtools.

### Save semantics

`saveParticipant` and `saveWinnerParticipant` both follow the same pattern:

1. If the last element in the target array has `crates === 0`, it is popped
   first (this trims trailing placeholders that were never replaced).
2. A fresh `id` is reassigned via `getNextId()` (max existing id + 1, or 0
   if the list is empty).
3. A shallow copy (`Object.assign({}, participant)`) is appended.
4. The full array is persisted to `localStorage`.

### New-record detection

In `saveWinnerParticipant` after persisting:

```
bestCrates = max(winnerParticipants.map(p => p.crates))
best       = winnerParticipants.find(p => p.crates === bestCrates)
if (!best || justSaved.id == best.id) -> setNewRecord(justSaved)
```

The comparison uses `==` (loose) between the just-assigned `participant.id`
and `best.id`. Because the just-saved entry is itself in
`winnerParticipants`, this branch fires on every finish as long as the
saved entry ties or tops the previous best — it is not strictly "only
when strictly greater". A run of `0` crates after the seed (which is
itself all zeros) will therefore also trigger the celebration once.

If `winnerParticipants` were ever empty (it cannot be in the current
flow because the constructor seeds 10 placeholders, but the code does
not guard against it), `Math.max(...[])` returns `-Infinity` and
`.find(...)` returns `undefined`. The `!best` branch would then call
`setNewRecord` with the just-saved participant, so behaviour would be
benign.

### Reactivity model

`AppService` exposes its state through plain mutable references: it
returns the live `currentParticipants` / `allParticipants` /
`winnerParticipants` arrays and a plain `newRecord` property. There
are no RxJS `BehaviorSubject`s or signals. The Angular template
re-evaluation relies on zone.js patching of DOM events (clicks,
keydown, `setTimeout`) so that change detection runs after each
mutation triggered by user input or by the celebration `setTimeout`.

## APIs / Interfaces

### npm scripts (`package.json`)

| Script | Command | Notes |
| --- | --- | --- |
| `npm start` | `ng serve` | Local dev server (default Angular port 4200). |
| `npm run build` | `ng build` | Production build (default). |
| `npm run watch` | `ng build --watch --configuration development` | Rebuild on change, dev mode. |
| `npm test` | `ng test` | Karma + Jasmine. No specs exist yet, so it runs an empty suite. |

### Angular components (all `selector` prefixed `app-`)

| Component | Selector | Inputs / Outputs | Responsibility |
| --- | --- | --- | --- |
| `AppComponent` | `app-root` | — | Top-level layout; branches the view on `newRecord == null`. |
| `ManagerComponent` | `app-manager` | — | Orchestrates the 3-column play screen and the focus button. |
| `TeamManagerRedComponent` | `app-team-manager-red` | `@Output() newParticipantEvent: EventEmitter<Participant>` | Red team slot: shows current player + crates, captures new player name. |
| `TeamManagerBlueComponent` | `app-team-manager-blue` | `@Output() newParticipantEvent: EventEmitter<Participant>` | Blue team slot: identical contract to red, different styling. |
| `ParticipantListComponent` | `app-participant-list` | — | Renders the last 10 finished runs and the total count. |
| `Top3Component` | `app-top3` | — | Renders the leaderboard (Top 3 by crates desc). |
| `ParticipantComponent` | `app-participant` | `@Input() participant: Participant` | Pure presentational line: `<n> cajas - <name>`. |
| `WinnerComponent` | `app-winner` | — | Full-screen new-record overlay with confetti. |

### Public service surface (`AppService`)

| Method | Signature | Notes |
| --- | --- | --- |
| `getCurrentParticipants()` | `() => Participant[]` | Returns the `[red, blue]` array (mutable reference; do not mutate). |
| `createParticipant(name)` | `(name: string) => Participant` | Builds a new `Participant` with the next monotonic `id`. |
| `saveParticipant(p)` | `(p: Participant) => void` | Appends to `allParticipants`, persists. |
| `saveWinnerParticipant(p)` | `(p: Participant) => void` | Appends to `winnerParticipants`, persists, may call `setNewRecord`. |
| `finishGame(p, team)` | `(p: Participant, team: 0\|1) => void` | Calls both `saveParticipant` and `saveWinnerParticipant`, resets the slot. No-op if `p.id === 0`. |
| `addCrate(team)` | `(team: 0\|1) => void` | `crates += 1`. No-op if the slot's `id === 0`. |
| `removeCrate(team)` | `(team: 0\|1) => void` | `crates -= 1` only if `crates > 0`. No-op if slot's `id === 0`. |
| `addParticipantToGame(p, team)` | `(p: Participant, team: 0\|1) => void` | Replaces the slot's `currentParticipants[team]` with `p`. |
| `getParticipants()` | `() => Participant[]` | Returns `allParticipants`. |
| `getWinnerParticipants()` | `() => Participant[]` | Returns `winnerParticipants`. |
| `getNewRecord()` | `() => Participant \| null` | Returns `newRecord`. |
| `setNewRecord(p)` | `(p: Participant) => void` | Sets `newRecord`, launches confetti, clears `newRecord` after `confettiTime + confettiInterval` ms. |

There is also `TeamServiceService` (`src/app/services/team.service.ts`) which
is empty and not referenced anywhere; it is dead code.

### Keyboard contract

Bound on the central `<button #fin>` inside `manager.component.html`.
They only fire when that button has keyboard focus; the team input
fields do not trigger them.

| Key | Effect |
| --- | --- |
| `a` | `addCrate(0)` — red team crate +1 |
| `z` | `removeCrate(0)` — red team crate -1 (clamped at 0) |
| `s` | `addCrate(1)` — blue team crate +1 |
| `x` | `removeCrate(1)` — blue team crate -1 (clamped at 0) |
| `q` | `finishGame(getParticipantRed(), 0)` |
| `w` | `finishGame(getParticipantBlue(), 1)` |

There is no in-app visual cue for the active focus on the button —
keyboard shortcuts only work because the operator remembers to click
the button (or `Tab` to it).

### Routing

`AppRoutingModule` declares an empty `routes` array. The router is wired but
no routes exist; navigation is not part of the current behavior.

## Non-functional characteristics

- **Browser support.** Targets the Angular 16 default browser support
  set (`browserslist` defaults plus whatever Angular CLI infers).
  No explicit `browserslist` field is configured, so it falls back to
  the Angular CLI default.
- **Performance / responsiveness.** The Top 3 and history list both
  re-read and re-sort their source arrays on every change-detection
  pass. With the current append-only data shape and no time-window
  filter, growth is `O(n)` per pass and `O(n log n)` for the sort.
  No virtualization is in place; the lists render all entries they
  compute.
- **Accessibility.** No ARIA roles, no `aria-live` regions for the
  celebration, no focus management, and keyboard interaction is bound
  to a non-semantic `<button>` for the scoring flow. Screen reader
  behaviour has not been audited.
- **Internationalization.** All visible strings are hardcoded in
  Spanish inside templates (`<html lang="es">` is set in
  `src/index.html`). There is no i18n pipeline.
- **No telemetry.** No analytics, no error reporting, no usage
  tracking.

## Permissions and Access

- No authentication, no authorization, no user accounts.
- All state is shared on the device: anyone using the browser sees and
  mutates the same `localStorage`-backed data.
- No data ever leaves the browser (no network calls).

## Error Handling

- `localStorage` reads use `JSON.parse(localStorage.getItem(...)!)`. The
  non-null assertion is safe in the current flow because the read is
  guarded by `if (!allParticipants)` first, but malformed JSON would
  throw an uncaught `SyntaxError` at construction time, leaving the
  app unusable until the offending key is cleared manually from
  devtools. `localStorage.setItem` can also throw in Safari private
  mode or when the quota is exceeded; `finishGame` does not catch it.
- `addCrate` / `removeCrate` silently no-op when the team slot is empty.
- `finishGame` silently no-ops when the team slot is empty.
- Pressing `q`/`w` without focusing the `#fin` button has no effect —
  the shortcuts are not global hotkeys, only the button's
  `keydown.*` bindings fire.
- `setNewRecord` always schedules a `setTimeout` that clears
  `newRecord`; there is no cancellation path if a newer record
  arrives during the celebration window (the previous `setTimeout`
  still fires and clears the field even though the most recent record
  is what the user just saw).
- Pressing Enter on a team input twice without changing the name
  silently replaces the in-progress participant with a brand new one
  carrying `crates: 0` — the previous run is not saved. There is no
  guard against this in the current flow.

## Validation

- **No unit tests exist.** `find src -name '*.spec.ts'` returns nothing
  and `tsconfig.spec.json` is configured but unused. `npm test` runs
  Karma against an empty suite.

- **Standalone `tsc` typecheck is red today.** Running
  `node_modules/.bin/tsc --noEmit -p tsconfig.app.json` fails with:

  ```
  src/app/services/app.service.ts(3,8): error TS1259:
    Module '"js-confetti"' can only be default-imported using the
    'allowSyntheticDefaultImports' flag
  ```

  The repo sets `allowSyntheticDefaultImports: true` inside
  `angularCompilerOptions` (used by the Angular template compiler) but
  not inside `compilerOptions`, and does not set `esModuleInterop`. The
  `import JSConfetti from 'js-confetti'` line therefore fails the
  standalone `tsc` typecheck even though the Angular build pipeline
  accepts it.

- **Angular build works.** Both configurations build successfully when
  the hardcoded WSL `outputPath` is overridden via `--output-path`:

  ```bash
  node_modules/.bin/ng build --configuration development --output-path /tmp/escalabirras-dev
  # -> success in ~3.3 s, initial bundle 3.24 MB (no budgets applied)

  node_modules/.bin/ng build --configuration production --output-path /tmp/escalabirras-prod
  # -> success in ~9.3 s, initial bundle 475.88 kB (under the 500 kB warn)
  ```

  Production budgets in `angular.json` are 500 kB warn / 1 MB error
  for the initial bundle and 2 kB / 4 kB for any component style. The
  default `npm run build` runs against the hardcoded WSL path and will
  fail outside that environment.

- **Build / dev commands available:**
  - `npm start` -> `ng serve` (dev server)
  - `npm run build` -> `ng build` (production, hardcoded WSL path)
  - `npm run watch` -> `ng build --watch --configuration development`
  - `npm test` -> `ng test` (empty Karma suite)

- **Manual smoke check** (suggested baseline):
  1. `npm install` if `node_modules` is missing.
  2. `npm start` and open the printed `http://localhost:4200`.
  3. Type a name in either team input and press Enter; the slot shows
     the name and `0 cajas!`. The typed name remains visible in the
     input.
  4. Click "Focus para jugar", press `a` several times, then `q`. The
     participant appears in the Top 3 / history and the slot resets to
     `- - -`. If the run produced the highest crates seen so far, the
     "NUEVO RECORD!!" overlay appears for ~12 s with flickering indigo
     background.