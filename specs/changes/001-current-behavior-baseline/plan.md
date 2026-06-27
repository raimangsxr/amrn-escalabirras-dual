# Plan: 001-current-behavior-baseline

## Approach

This is a documentation-only change, structured in two passes:

1. **Initial baseline.** Read `src/` top to bottom and fill the
   contract, context pack, spec, plan, and tasks with the observable
   current behavior.
2. **Refinement pass.** Re-scan the codebase for things that were
   under- or mis-documented in the initial pass (e.g., reactivity
   model, focus management, leaderboard seed behaviour, non-functional
   characteristics, project-level tooling directories), confirm the
   build pipeline actually works (development + production), and
   update the SDD files so they form a baseline strong enough to
   anchor the next real change.

We deliberately do **not** modify any file under `src/`, install new
dependencies, or write any committed build artifacts. The Angular
build outputs used for validation are written under `/tmp/` and
removed afterwards.

We follow the AGENTS.md flow:

```
specify  -> (this document covers spec + plan)
clarify  -> not needed; the prompt is explicit
checklist-> not needed; trivial change
plan     -> this file
tasks    -> tasks.md
analyze  -> performed during both read passes
implement-> the SDD file writes
```

## Steps

### Pass 1 — Initial baseline

1. **Review the current application structure.**
   - Read `package.json`, `angular.json`, `tsconfig*.json`,
     `tailwind.config.js`, `prettier.config.js`, `.gitignore`,
     `README.md` to lock in the stack and tooling.
   - Read `src/main.ts`, `src/index.html`, `src/styles.css`,
     `src/app/app.module.ts`, `src/app/app-routing.module.ts`,
     `src/app/app.component.{ts,html,css}` for the bootstrap and shell.
   - Read `src/app/services/app.service.ts` and
     `src/app/services/team.service.ts` for the data/service layer.
   - Read `src/app/participant/participant.ts` and every
     `*.component.{ts,html,css}` to capture inputs/outputs, templates,
     and styling conventions.
   - Confirm absence of tests with `find src -name '*.spec.ts'`.

2. **Validate the narrowest check.**
   - Run `node_modules/.bin/tsc --noEmit -p tsconfig.app.json`.
   - Capture the resulting error (`TS1259` on the `js-confetti` default
     import) so the contract and context pack can state it explicitly
     instead of pretending the typecheck is green.

3. **Fill in the active contract.**
   - Replace every populated-section `TODO` in
     `specs/contracts/app-core/contract.md` with the observed
     behavior.

4. **Fill in the context pack.**
   - Replace every populated-section `TODO` in
     `specs/changes/001-current-behavior-baseline/context-pack.md`
     with goal, current understanding, files / areas likely involved,
     constraints, validation plan (narrow to broad), risks, and a
     *Recommendations* section listing additional areas that could
     justify their own contract in a future change, without creating
     those contracts now.

5. **Coherent spec, plan, and tasks.**
   - Rewrite `spec.md` with explicit functional and structural
     requirements plus acceptance criteria derived from the contract.
   - Rewrite `plan.md` (this file) with the approach, steps, and
     risks so it reflects what was actually done.
   - Rewrite `tasks.md` so each step has a task and is checked off.

6. **Keep `specs/manifest.yml` synchronized.**
   - Verify `specs/manifest.yml` still points at the active contract
     and change folder. No edits expected.

### Pass 2 — Refinement

7. **Re-scan for under-documented behaviors.**
   - Confirm via direct read that:
     - The team input does not reset its `name` after Enter.
     - Focus stays on the team input after Enter.
     - `allParticipants` and `winnerParticipants` are kept in sync via
       `finishGame`.
     - The Top 3 and history list both render placeholder `- - -`
       entries from the seed.
     - `WinnerComponent` calls `Math.random()` inside `[ngClass]`,
       causing background flicker.
     - State is exposed through plain mutable references with no
       `Observable` / signal.
   - Identify project-level tooling directories that exist on disk
     but were not described (`.specify/`, `.opencode/`,
     `setup-sdd.sh`).

8. **Confirm build pipeline actually works.**
   - Run `node_modules/.bin/ng build --configuration development
     --output-path /tmp/escalabirras-dev` and record the success +
     bundle size.
   - Run `node_modules/.bin/ng build --configuration production
     --output-path /tmp/escalabirras-prod` and record the success +
     bundle size (and check it stays under the 500 kB warn budget).
   - Clean up `/tmp/escalabirras-dev` and `/tmp/escalabirras-prod`.

9. **Refine the contract.**
   - Add the under-documented behaviors to the relevant sections
     (User Flows, Data and State, APIs/Interfaces, Error Handling).
   - Add a new "Non-functional characteristics" section (browser
     support, performance, accessibility, i18n, telemetry).
   - Update the Validation section with the actually-observed build
     results.

10. **Refine the context pack.**
    - Add `.specify/`, `.opencode/`, and `setup-sdd.sh` to the
      tooling section.
    - Replace the validation plan with the concrete commands that
      have been executed, including the `--output-path` overrides.
    - Add the refinement-pass risks (no focus management, permanent
      seed, `WinnerComponent` flicker, implicit reactivity on
      zone.js).

11. **Refine the spec, plan, and tasks.**
    - Add `R8` (non-functional characteristics), `R14` (manifest
      unchanged), and update `AC1`/`AC6` to mention the build
      commands used and `/tmp/` cleanup.
    - Update `plan.md` (this file) to record the refinement pass.
    - Update `tasks.md` with refinement tasks.

12. **Final consistency sweep.**
    - Re-read all five SDD files and confirm:
      - No `TODO` placeholders remain in the populated sections.
      - No claims contradict what is actually in `src/` or in the
        output of the validation commands.
      - Recommendations are clearly marked as not-yet-implemented.

## Risks

- **Documentation drift.** If a future change updates `src/` without
  updating `specs/contracts/app-core/contract.md`, the contract
  becomes stale. The active change workflow in `AGENTS.md` (rule 7:
  update the affected contract before implementation) is the
  mitigation.
- **Misreading the `js-confetti` import error** as a regression
  caused by this change. It is a pre-existing condition; the change
  only *documents* it. Mitigation: spell out the cause (missing
  `esModuleInterop` in `compilerOptions`) in the contract and
  context pack, not just the symptom.
- **Recommending future contracts in the context pack** could be
  mistaken for an instruction to create them. Mitigation: place them
  under an explicit *Recommendations* header at the bottom of the
  context pack and use phrasing like "do not create in this change".
- **Hardcoded WSL output path in `angular.json`.** Not modified
  here. The refinement pass documents the `--output-path` override
  workaround so future validation can succeed on macOS / native
  Windows.
- **Validation commands are non-trivial.** The Angular production
  build takes ~9 s and writes several MB to `/tmp/`. This is
  acceptable because the directories are explicitly cleaned up
  afterwards and are outside the working tree.
- **No tests.** Validation relies on a `tsc` typecheck plus the
  Angular build plus manual reasoning. A future change should add
  at least smoke tests for `AppService`, but that is out of scope
  for this baseline.
- **Refinement pass could miss newly-introduced behaviors.** The
  refinement only re-reads what was already read once; if the
  implementation changes between the two passes the docs will
  still lag. Mitigation: AGENTS.md rule 7 forces contract updates
  on any behavior change.