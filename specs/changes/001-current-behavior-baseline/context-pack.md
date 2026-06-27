# Context Pack: 001-current-behavior-baseline

## Goal

Establish the initial SDD baseline for this project by documenting what the
**amrn-escalabirras-team** Angular 16 SPA already does, without proposing
any functional changes.

## Relevant Contract

- `specs/contracts/app-core/contract.md`

## Current Understanding

The repository is a single-page Angular 16 application used at a live
motorcycle rally event to count beer crates ("escalabirras") consumed by
participants in a two-team drinking game. It is fully client-side: there
is no backend, no HTTP traffic, and no routing. All state lives in the
browser's `localStorage`, with two JSON-encoded keys (`allParticipants`
and `winnerParticipants`) that are read once at app bootstrap and
rewritten on every finished game.

The app is driven almost entirely by a single screen split into three
columns (history list, red team, blue team) plus a full-screen
"NUEVO RECORD!!" overlay that hijacks the view when a new maximum is
reached. The actual scoring happens through keyboard shortcuts bound to
the central "Focus para jugar" button: `a`/`z` adjust the red team's
crates, `s`/`x` adjust the blue team's crates, and `q`/`w` finalize the
respective player. Top 3 and recent history are recomputed from the
service state on every change-detection pass.

## Files / Areas Likely Involved

### Bootstrap and shell

- `src/main.ts` — bootstraps `AppModule` via `platformBrowserDynamic`.
- `src/index.html` — sets `<html lang="es">`, page title "Torneo de
  Escalabirras por equipos", loads Roboto + Material Icons from Google
  Fonts, mounts `<app-root>`.
- `src/styles.css` — minimal global styles + Tailwind base/components/
  utilities.
- `src/app/app.module.ts` — single NgModule declaring all 8 components
  and importing `BrowserModule`, `AppRoutingModule`, `FormsModule`,
  `BrowserAnimationsModule`, `MatIconModule`. `MatIconModule` is
  imported but no `mat-icon` is currently used in any template.
- `src/app/app-routing.module.ts` — empty `routes: Routes = []`; the
  router is wired but has no navigable URLs.
- `src/app/app.component.{ts,html,css}` — root component; sets the
  tournament title/subtitle and conditionally renders
  `<app-winner>` when a new record is active, otherwise renders header
  + `<app-top3>` + `<app-manager>`.

### Domain and services

- `src/app/participant/participant.ts` — `Participant { id, name, crates }`
  interface. Placeholder sentinel: `{ id: 0, name: '- - -', crates: 0 }`.
- `src/app/services/app.service.ts` — single root-provided singleton
  (`@Injectable({ providedIn: 'root' })`) that owns **all** mutable
  state. Persistence, scoring, leaderboard and confetti all live here.
  Key methods: `createParticipant`, `saveParticipant`,
  `saveWinnerParticipant`, `finishGame`, `addCrate`, `removeCrate`,
  `addParticipantToGame`, `getParticipants`, `getWinnerParticipants`,
  `getNewRecord`, `setNewRecord`, `launchConfetti`.
- `src/app/services/team.service.ts` — empty class named
  `TeamServiceService` (note the duplicated `Service` suffix). Declared
  in `AppModule`? No — it is not in the `declarations` array and not
  imported anywhere. Effectively dead code; no production code path
  references it.

### Feature components

- `src/app/manager/manager.component.{ts,html,css}` — orchestrator for
  the 3-column play screen and the central focus button. Subscribes to
  `@Output() newParticipantEvent` from both team panels to push a
  participant onto `currentParticipants[team]`.
- `src/app/team-manager-red/team-manager-red.component.{ts,html,css}` —
  red team panel. Holds a local `name` string bound with `ngModel`,
  emits the newly created participant on Enter. Name input has
  `maxlength="20"` and `autocomplete="off"`.
- `src/app/team-manager-blue/team-manager-blue.component.{ts,html,css}` —
  mirror of the red component, indigo color scheme instead of red,
  no functional difference.
- `src/app/participant-list/participant-list.component.{ts,html,css}` —
  shows the last 10 finished runs (by descending `id`) and the total
  count of players with `id > 0`.
- `src/app/top3/top3.component.{ts,html,css}` — sorts
  `winnerParticipants` by crates descending and renders the top three
  with gold/silver/bronze backgrounds defined in the local CSS.
- `src/app/winner/winner.component.{ts,html,css}` — full-screen
  "NUEVO RECORD!!" overlay. Background flips between `bg-indigo-200`
  and `bg-indigo-900` randomly on every change-detection pass via
  `getBackgroundColor()`.
- `src/app/participant/participant.component.{ts,html,css}` — pure
  presentational `<n> cajas - <name>` line used inside the history list
  and the Top 3.

### Assets and styling

- `src/assets/` — PNG assets (`logo-escalabirras.png`,
  `logo-motoclub.png`, `first-award.png`, `second-award.png`,
  `third-award.png`) referenced directly from the templates.
- `tailwind.config.js` — scans `src/**/*.{html,ts}`, no plugins.
- `prettier.config.js` — uses `prettier-plugin-tailwindcss`.
- `src/styles.css` — Angular Material indigo-pink prebuilt theme is
  loaded via `angular.json` (`build.styles`).

### Build / tooling

- `package.json` — Angular 16.1, Angular Material 16.1, Angular CDK
  16.1, `js-confetti@0.11`, RxJS 7.8, zone.js 0.13, TypeScript 5.1
  (note: TS 5.1 is over the Angular 16 supported TS range — see
  Constraints).
- `angular.json` — single project `amrn-escalabirras-team`. `outputPath`
  is hardcoded to `/mnt/c/Users/raima/Documents/dist/amrn-escalabirras-dual`,
  a WSL path that will not resolve on macOS or native Windows outside
  that environment. Production budgets: 500 kB warn / 1 MB error for
  the initial bundle, 2 kB / 4 kB for any component style. No
  `browserslist` field is configured; the project inherits Angular
  CLI defaults.
- `tsconfig.json` — strict mode, `noImplicitOverride`,
  `noPropertyAccessFromIndexSignature`, `noImplicitReturns`,
  `noFallthroughCasesInSwitch`, `strictTemplates`. **Missing**
  `esModuleInterop` and (in `compilerOptions`) `allowSyntheticDefaultImports`,
  which is why the standalone `tsc` typecheck fails on the
  `js-confetti` default import — see Risks.
- `tsconfig.app.json`, `tsconfig.spec.json` — standard Angular
  configurations. The spec config references jasmine types but no
  `*.spec.ts` files exist.
- `.gitignore` — standard Angular ignores plus `.angular/`,
  `.vscode/`. `dist/` is ignored, so the WSL output path is moot for
  committed artifacts.
- `.specify/` — speckit SDD scaffolding and templates
  (`templates/`, `workflows/`, `extensions.yml`,
  `integrations/`, `memory/constitution.md`). Not part of the
  application; included for completeness because it sits in the repo
  root.
- `.opencode/` — opencode integration for the SDD workflow
  (`commands/speckit.*.md`, its own `package.json`). Not part of the
  application; likewise tooling.
- `setup-sdd.sh` — the helper script that bootstrapped the SDD
  scaffolding in this repo (created `specs/`, `AGENTS.md`,
  `specs/manifest.yml`). Re-running it with arguments is safe but
  would overwrite the current SDD files.

## Constraints

- **No backend.** The app is intentionally offline-first; do not
  introduce network dependencies in the baseline contract.
- **No authentication / multi-user separation.** Everything is per
  browser. The event is run on a single operator's laptop at the venue.
- **Strict TypeScript and Angular templates.** `tsconfig.json` enables
  `strict`, `strictTemplates`, `noImplicitOverride`,
  `noPropertyAccessFromIndexSignature`, `noImplicitReturns`,
  `noFallthroughCasesInSwitch`. New code must keep these flags green.
- **Standalone `tsc` typecheck is currently red** because the
  `js-confetti` default import needs `esModuleInterop` or
  `allowSyntheticDefaultImports` in `compilerOptions`. The Angular
  build still works because the Angular template compiler accepts the
  default import, but this is an observable inconsistency that future
  changes should preserve awareness of.
- **localStorage schema is implicit.** Any change to `Participant`
  shape or storage keys is a breaking change for existing browsers —
  no migration code exists today.
- **Keyboard-only scoring flow.** Removing or breaking the focus
  button would disable the only input mechanism for live scoring.
- **`outputPath` in `angular.json` is hardcoded to a WSL path.** Any
  production build outside the original WSL setup will need that
  path changed first.
- **Angular 16 + TS 5.1.** Officially Angular 16 supports TS 4.9.
  TS 5.1 compiles in practice but is not supported; any toolchain
  upgrade must be evaluated.
- **Spanish UI strings are hardcoded in templates.** Changing them is
  a behavior change.

## Validation Plan

Run narrow checks first, then broader ones. None of these commands
mutate files under `src/`.

1. **Standalone TypeScript typecheck (narrow, currently red).**

   ```bash
   node_modules/.bin/tsc --noEmit -p tsconfig.app.json
   ```

   Expectation today: exit non-zero with `TS1259` on the
   `js-confetti` default import. This documents the current state, not
   a regression introduced by the baseline. Run it to confirm the
   message is still exactly as documented in the contract before any
   future change touches `app.service.ts`.

2. **Angular development build (narrow, currently green).**

   ```bash
   node_modules/.bin/ng build --configuration development \
       --output-path /tmp/escalabirras-dev
   ```

   Override the hardcoded WSL `outputPath` with a temp directory.
   Expectation today: succeeds in ~3 s with an initial bundle around
   3.24 MB (no budgets applied in development).

3. **Angular production build (narrow, currently green).**

   ```bash
   node_modules/.bin/ng build --configuration production \
       --output-path /tmp/escalabirras-prod
   ```

   Expectation today: succeeds in ~9 s with an initial bundle around
   475 kB, which is under the 500 kB warn threshold. After running,
   delete the temp directory.

4. **Unit tests (broad, currently empty).**

   ```bash
   npm test
   ```

   Expectation today: Karma launches and reports 0 specs. New specs
   added under `src/**/__tests__/` or alongside components must follow
   Karma + Jasmine conventions because `tsconfig.spec.json` only
   configures Jasmine.

5. **Manual smoke (broad, validates behavior end-to-end).**

   1. `npm install` (if needed) then `npm start`.
   2. Open the printed `http://localhost:4200`.
   3. Type "Ana" in the red input, press Enter — the red slot shows
      "Ana" and "0 cajas!", but the typed name remains in the input
      field and focus stays on it.
   4. Click "Focus para jugar".
   5. Press `a` three times — counter shows "3 cajas!".
   6. Press `q` — Ana appears in the history list and (because the
      seed was all zeros) the "NUEVO RECORD!!" overlay plays for
      ~12 s with a flickering indigo background.
   7. Hard-reload the page; Ana must still be in the history list and
      the Top 3 must still reflect "Ana 3 cajas!" in first place.

6. **Browser compatibility smoke (broad, optional).**

   The application declares `<html lang="es">` and depends only on
   widely-available browser APIs (`localStorage`, `Math.random`,
   standard DOM events). Spot-check in Chrome and Safari (including
   Safari private mode if relevant) to confirm the baseline flow.

## Risks

- **`tsc` typecheck is red.** Standalone `tsc --noEmit` fails on
  `app.service.ts` because of how `js-confetti` is imported. The
  Angular build accepts it; the standalone typecheck does not. Any
  future change that runs `tsc` for CI must either add
  `esModuleInterop: true` to `compilerOptions` or rewrite the import
  (e.g. `import * as JSConfettiNS from 'js-confetti'`). Either is a
  behavior contract change and should go through its own SDD change.
- **New-record detection uses `==` loose equality** and matches the
  just-saved entry, so a tie on `crates` triggers the celebration as
  if it were a new record. Documented, not a bug, but easy to
  misinterpret later.
- **`setNewRecord` does not cancel prior timers.** If a new record
  arrives during a celebration, the previous `setTimeout` still fires
  and clears the current `newRecord` early.
- **`TeamServiceService` is dead code** (empty class, no references).
  Removing it is a separate, low-risk cleanup.
- **`createParticipant()` on `ManagerComponent` is empty** — the
  component never creates participants itself; it relies on the team
  sub-components. Harmless today, but easy to confuse.
- **`MatIconModule` is imported but unused** in any template.
- **localStorage growth is unbounded.** Every finished run appends to
  two arrays; there is no cap or rotation.
- **Hardcoded `outputPath`** in `angular.json` blocks
  out-of-the-box `ng build` outside the original WSL environment.
- **No tests.** Any regression in the baseline scoring or persistence
  code will go unnoticed unless a manual smoke is performed.
- **Browser storage quotas / private-mode failures are not handled.**
  `localStorage.setItem` can throw in Safari private mode; the
  current code would surface an uncaught exception in the
  `finishGame` path.
- **No focus management after Enter.** The team input keeps focus
  and its `name` value after `createParticipant()`. Pressing Enter
  twice without changing the name silently replaces the in-progress
  player with a fresh `crates: 0` one; the first run is lost.
- **Placeholder seed is permanent.** The 10 placeholder entries
  prepended on first run are never cleaned out. The Top 3 and the
  history list both display `- - -` entries until enough real
  participants exist.
- **`WinnerComponent` background flickers.** The `[ngClass]` binding
  re-evaluates `Math.random()` on every change-detection pass, so the
  indigo shade flips unpredictably while the overlay is shown.
- **Reactivity is implicit.** `AppService` exposes plain mutable
  arrays and properties; nothing is an `Observable` or a signal.
  Change detection depends on zone.js patching DOM events and
  `setTimeout`. Any future change that swaps the runtime to zoneless
  or moves to signals must keep the existing in-place mutations
  trigger re-renders.

## Recommendations (do not create in this change)

The following areas are clearly observable in the current code and
would each justify its own contract in a future SDD change. They are
listed here for visibility only; no new contract files are being
created as part of `001-current-behavior-baseline`.

- **`persistence-localstorage` contract.** Encapsulates the
  `localStorage` keys (`allParticipants`, `winnerParticipants`), the
  seed-on-missing behavior, the save semantics (pop trailing
  placeholder, reassign `id`, persist full array), the non-null
  assertion on read, and the lack of quota / corruption handling.
  Would own any future migration or storage backend swap.
- **`scoring-keyboard` contract.** Encapsulates the keyboard contract
  bound to the central `<button #fin>` (`a`, `z`, `s`, `x`, `q`, `w`)
  including its focus dependency, the red/blue team indices, the
  clamps on `addCrate`/`removeCrate`, and the no-op-on-empty-slot
  guards. A natural home for any future input mechanism (touch
  buttons, mobile-friendly UI).
- **`celebration-record` contract.** Encapsulates the
  new-record detection logic (loose `==`, ties trigger the overlay),
  the confetti timing (`confettiTime = 10000`,
  `confettiInterval = 2000`), the emoji pool, and the lack of timer
  cancellation when a new record arrives during an ongoing
  celebration.
- **`team-slots` contract.** Encapsulates the
  `currentParticipants: Participant[2]` invariant, the red=0 / blue=1
  indexing convention, the placeholder sentinel
  `{ id: 0, name: '- - -', crates: 0 }`, and the
  `addParticipantToGame` / `finishGame` slot transitions. Would be the
  natural place to introduce more than two teams if that ever became
  a requirement.
- **`leaderboard-top3` contract.** Encapsulates the `Top3` rendering
  derived from `winnerParticipants` and the gold/silver/bronze
  styling in `top3.component.css`, currently duplicated by hand.
- **`participant-history` contract.** Encapsulates the last-10
  rendering and total count from `ParticipantListComponent`,
  including the `slice(-10).reverse()` and the
  `p.id > 0` filter for the total count.

These recommendations should be revisited the first time any future
change touches the corresponding code path; at that point the change
should create the contract first, per AGENTS.md rule 7.