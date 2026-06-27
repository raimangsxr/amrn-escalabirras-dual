# Spec: 001-current-behavior-baseline

## Problem

The repository ships a working Angular 16 SPA but has no formal
description of what it actually does. Without that description, every
future change has to re-derive the current behavior from the code
itself, which is error-prone and blocks a repeatable
specification-driven development workflow.

This change also performs a refinement pass over the initial baseline
to close observable gaps (e.g., reactivity model, focus management,
leaderboard seed behaviour, non-functional characteristics) so that
the baseline is adequate to anchor the next real change.

## Goals

- Capture the **observable** current behavior of the application in
  the active `app-core` contract, including reactivity, focus,
  persistence, validation, and non-functional characteristics.
- Capture the relevant files, constraints, risks, and validation
  commands in the active context pack.
- Establish a baseline change record that future SDD changes can
  reference, so that "what changed and when" is auditable.
- Make the SDD scaffolding (manifest, contract, context pack, spec,
  plan, tasks) consistent and ready for the next real change.

## Non-Goals

- **No functional changes to the application.** This change is
  documentation-only.
- No introduction of new tests, new tooling, or new dependencies.
- No rewrite, refactor, or "improvement" of existing code.
- No creation of additional contracts (see *Recommendations* in the
  context pack for areas that could later warrant their own
  contracts).
- No migration of the `localStorage` schema.

## Requirements

### Functional (documentation requirements)

- **R1.** The active `app-core` contract must describe, in concrete
  terms, every user-facing flow of the app: app load, register a
  participant on a team, live scoring, finalize a player, top 3 and
  history display, and the new-record overlay.
- **R2.** The contract must document the `Participant` data model,
  the placeholder sentinel, the in-memory state owned by
  `AppService` (including its shape, lifetime, and ownership), and
  the reactivity model (plain mutable references, zone.js-driven
  change detection).
- **R3.** The contract must document persistence: the two
  `localStorage` keys (`allParticipants`, `winnerParticipants`),
  when they are written, when they are read, that JSON parsing uses
  a non-null assertion guarded by a presence check, that the seed
  of 10 placeholders is permanent, and that storage is per-origin.
- **R4.** The contract must document every public method of
  `AppService`, every Angular component selector with its
  `@Input`/`@Output` contract, the empty routes array, and the
  keyboard shortcuts (`a`, `z`, `s`, `x`, `q`, `w`) bound to the
  central focus button including the lack of visual focus cue.
- **R5.** The contract must state that there is no authentication,
  no backend, and no routing.
- **R6.** The contract must enumerate error/edge behavior: no-ops on
  empty team slots, no keyboard effect without focus, the observed
  behavior of `setNewRecord` (no cancellation of prior timers), the
  silent replace on repeated Enter without input change, malformed
  JSON failures, and Safari private-mode / quota failures.
- **R7.** The contract must state that no unit tests exist today,
  that the standalone `tsc --noEmit` typecheck is currently red on
  the `js-confetti` default import, and that both the Angular
  development and production builds succeed when the hardcoded WSL
  `outputPath` is overridden.
- **R8.** The contract must include a "Non-functional
  characteristics" section covering browser support, performance,
  accessibility, i18n, and telemetry at the level currently
  observable in the source.

### Structural (process requirements)

- **R9.** The context pack must list the files most likely to be
  involved in any future change, including bootstrap/shell,
  domain/service, feature components, assets, build/tooling, and
  the project-level tooling directories (`.specify/`, `.opencode/`,
  `setup-sdd.sh`).
- **R10.** The context pack must list the technical, product,
  design, migration, and compatibility constraints (strict TS,
  hardcoded output path, Angular 16 + TS 5.1, no tests, etc.).
- **R11.** The context pack must list validation commands in
  narrow-first order that actually work today: standalone `tsc`
  (red, documented), `ng build --configuration development` (green
  with `--output-path` override), `ng build --configuration
  production` (green with `--output-path` override), `npm test`
  (empty Karma), and a manual smoke flow including a hard-reload
  persistence check.
- **R12.** The context pack must list risks that any future change
  should be aware of, including the new ones surfaced by the
  refinement pass (no focus management, permanent placeholder seed,
  `WinnerComponent` background flicker, implicit reactivity on
  zone.js, `allParticipants`/`winnerParticipants` sync, loose
  equality in record detection, dead code, unbounded storage,
  hardcoded WSL path, no tests, Safari private-mode failure).
- **R13.** The plan and tasks files must reflect a documentation-only
  change with all steps (initial baseline + refinement pass)
  completed by this very change.
- **R14.** `specs/manifest.yml` must continue to point at the
  unchanged paths and active status of this change and the
  `app-core` contract.

## Acceptance Criteria

- **AC1.** `specs/contracts/app-core/contract.md` no longer contains
  any `TODO` placeholders in the populated sections and accurately
  describes what the app does today, including the reactivity
  model, the no-focus-management-after-Enter behaviour, the
  permanent placeholder seed, the leaderboard derivation, the
  per-origin storage, the silent-replace on repeated Enter, the
  background flicker on `WinnerComponent`, the non-functional
  characteristics, and the validation results observed during the
  change (verified by reading `src/app/services/app.service.ts`,
  `src/app/manager/manager.component.html`,
  `src/app/team-manager-red/team-manager-red.component.ts`,
  `src/app/winner/winner.component.html`, and the result of running
  `node_modules/.bin/ng build --configuration {development,
  production} --output-path /tmp/escalabirras-{dev,prod}`).
- **AC2.** `specs/changes/001-current-behavior-baseline/context-pack.md`
  no longer contains any `TODO` placeholders and lists concrete file
  paths, real constraints, real risks (including the refinement-pass
  additions), reproducible validation commands that have been
  actually executed during the change, and the deferred
  recommendations for additional contracts.
- **AC3.** `specs/changes/001-current-behavior-baseline/spec.md`,
  `plan.md`, and `tasks.md` are coherent with each other and with
  the contract/context pack: requirements in spec align with steps
  in plan align with tasks, and all tasks for this change (initial
  baseline plus refinement pass) are marked completed by the end
  of the change.
- **AC4.** `specs/manifest.yml` is unchanged in shape (same paths,
  same active statuses) and remains consistent with the files on
  disk.
- **AC5.** No files under `src/` are modified.
- **AC6.** No destructive commands are run during the change; only
  read-only inspection commands, a single non-emitting
  `tsc --noEmit` typecheck, and Angular builds that write to
  `/tmp/escalabirras-*` (which are removed afterwards) are used
  for validation.
- **AC7.** Recommendations for additional contracts (areas that
  could warrant their own contract in a future change) are appended
  to the context pack rather than implemented.