# Tasks: 001-current-behavior-baseline

## Tasks

### Pass 1 — Initial baseline

- [x] Review the project structure (stack, entrypoints, modules,
      components, services, routing, assets, build tooling).
- [x] Run narrow validation: `node_modules/.bin/tsc --noEmit -p
      tsconfig.app.json` and record the resulting `TS1259` on the
      `js-confetti` default import.
- [x] Confirm there are no `*.spec.ts` files in `src/` and therefore
      no unit tests exist today.
- [x] Document current behavior in
      `specs/contracts/app-core/contract.md` (purpose, current
      behavior, user flows, data and state, APIs / interfaces,
      permissions and access, error handling, validation).
- [x] Complete `specs/changes/001-current-behavior-baseline/context-pack.md`
      (goal, current understanding, files / areas, constraints,
      validation plan, risks, recommendations).
- [x] Complete `specs/changes/001-current-behavior-baseline/spec.md`
      (problem, goals, non-goals, requirements, acceptance criteria).
- [x] Complete `specs/changes/001-current-behavior-baseline/plan.md`
      (approach, steps, risks).
- [x] Mark all tasks in this file as completed once the steps above
      land.
- [x] Verify `specs/manifest.yml` is still consistent with the files
      on disk (no path or status changes were needed for this
      change).

### Pass 2 — Refinement

- [x] Re-read the team components and confirm: no input reset on
      Enter, focus stays on the input, repeated Enter silently
      replaces the in-progress player.
- [x] Re-read `WinnerComponent` and confirm the `[ngClass]`
      background binding re-evaluates `Math.random()` on every
      change-detection pass.
- [x] Trace `finishGame` and confirm `allParticipants` and
      `winnerParticipants` are kept in sync and that the placeholder
      seed is never cleaned out.
- [x] Confirm the reactivity model: plain mutable references, no
      `Observable` / signal; change detection depends on zone.js.
- [x] Identify project-level tooling directories on disk
      (`.specify/`, `.opencode/`, `setup-sdd.sh`) and document them
      in the context pack.
- [x] Confirm `node_modules/.bin/ng build --configuration development
      --output-path /tmp/escalabirras-dev` succeeds (record bundle
      size).
- [x] Confirm `node_modules/.bin/ng build --configuration production
      --output-path /tmp/escalabirras-prod` succeeds (record bundle
      size and that it stays under the 500 kB warn budget).
- [x] Remove the `/tmp/escalabirras-dev` and `/tmp/escalabirras-prod`
      build output directories.
- [x] Add a "Non-functional characteristics" section to the
      contract (browser support, performance, accessibility, i18n,
      telemetry).
- [x] Add the under-documented behaviors (focus, placeholder seed,
      leaderboard derivation, per-origin storage, silent-replace,
      background flicker) to the contract and context pack.
- [x] Update the context pack's validation plan with the concrete
      commands that have been executed, including the
      `--output-path` overrides.
- [x] Update `spec.md` with the new requirements (R8, R14) and
      refined acceptance criteria (AC1, AC6) referencing the build
      commands and `/tmp/` cleanup.
- [x] Update `plan.md` with the two-pass approach and the
      refinement-specific risks.
- [x] Mark refinement tasks as completed in this file.
- [x] Final consistency sweep: no `TODO` placeholders in populated
      sections, no claims contradict what is in `src/` or in the
      output of the validation commands.

## Out of scope (recorded for future changes)

- Add `esModuleInterop: true` (or change the import) so the
  standalone `tsc` typecheck is green.
- Remove `TeamServiceService` (dead code).
- Remove the unused `MatIconModule` import.
- Add unit tests under `src/**/__tests__/` or alongside components
  (Karma + Jasmine, per `tsconfig.spec.json`).
- Migrate `localStorage` schema or add quota / corruption handling.
- Fix the hardcoded `outputPath` in `angular.json` so `ng build`
  works outside the original WSL setup without an override.
- Decide whether the new-record celebration should cancel prior
  timers and whether ties should also fire the overlay.
- Decide whether the team input should clear its `name` and move
  focus after Enter.
- Decide whether to freeze or animate the `WinnerComponent`
  background instead of re-rolling on every change-detection pass.
- Extract one or more of the areas recommended at the bottom of the
  context pack into their own contracts (`persistence-localstorage`,
  `scoring-keyboard`, `celebration-record`, `team-slots`,
  `leaderboard-top3`, `participant-history`).