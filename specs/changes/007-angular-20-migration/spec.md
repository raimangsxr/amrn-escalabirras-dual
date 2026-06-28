# Spec: 007-angular-20-migration

## Problem

The Angular frontend is on Angular 16.1 (`@angular/core ^16.1.0`,
`@angular/cli ~16.1.5`, `@angular/material ^16.1.5`,
`@angular/cdk ^16.1.5`, `typescript ~5.1.3`, `zone.js ~0.13.0`).

Angular 16 is two majors behind the current stable line (Angular 20).
Angular 16 reached end-of-support and no longer receives security
fixes. Several breaking changes that landed between v17 and v20
become the default in v20 and the deprecation warnings emitted by
v17-v19 would eventually turn into hard errors in v21+. Material 16
also tracks that major, so Material's own fixes and improvements
require v18+.

Scope is intentionally narrow (clarified with the user): we keep the
existing NgModule-based architecture, RxJS `BehaviorSubject` state,
Karma + Jasmine, and zone.js change detection. The migration is a
version bump + builder + tooling update, not a refactor.

## Goals

- Bump the frontend to Angular 20 (latest stable as of the change's
  planning date).
- Bump `@angular/material` and `@angular/cdk` to the matching 20.x
  releases.
- Bump `typescript` to the version Angular 20 supports
  (`~5.8.0`).
- Bump `rxjs` to `~7.8.0` (already there; stays).
- Bump `zone.js` to `~0.15.0` (Angular 18+ requirement; v18 lifted
  the floor).
- Migrate `angular.json` to the new `@angular/build:application`
  builder (the v17-deprecated `@angular-devkit/build-angular:browser`
  builder is removed in v20).
- Migrate `karma.conf.js` / `tsconfig.spec.json` to the new test
  builder (`@angular/build:karma`).
- Update the prebuilt Material theme import (Angular Material 20
  ships the new M3 token API; the legacy `indigo-pink` prebuilt is
  still present but deprecated).
- Update `specs/contracts/frontend-angular/contract.md` so the
  documented framework version reflects v20 and the builder names
  reflect the new builders.
- Update `specs/manifest.yml` to list the new change and set the
  active block.

## Non-Goals

- No architectural rewrite. We do not adopt standalone components,
  signals, the new control flow (`@if`/`@for`/`@switch`), or
  `provide*` functions. Existing NgModules, RxJS streams, and
  constructor injection stay.
- No zoneless change detection. `zone.js` stays.
- No switch to Jest or Vitest. Karma + Jasmine stay.
- No SSR, no hydration, no prerendering. The frontend stays an SPA.
- No backend changes.
- No dependency bumps unrelated to the Angular major (no new
  Tailwind, no new Karma plugins, no PostCSS changes).
- No visual changes. Templates, styles, copy, and colors stay.
- No new tests. The frontend still has zero Karma specs (matches
  the existing contract).

## Requirements

### Functional

- **R1.** `package.json` declares `@angular/*` at the v20 minor that
  Angular's release notes call out as compatible, pinned with `~` so
  patch updates flow in but minor bumps are explicit.
- **R2.** `package.json` declares `@angular/material` and
  `@angular/cdk` at the matching v20 minor.
- **R3.** `package.json` declares `typescript` at the version
  Angular 20 supports (`~5.8.0`) and `zone.js` at `~0.15.0`.
- **R4.** `angular.json` declares `build.builder` as
  `@angular/build:application` (or
  `@angular-devkit/build-angular:application` if `@angular/build` is
  not yet published for v20 — confirmed at the implementation
  step).
- **R5.** `angular.json` `serve.configurations.{production,
  development}` reference `buildTarget` (renamed from
  `browserTarget`).
- **R6.** `angular.json` `test.builder` is
  `@angular/build:karma` (or its devkit equivalent).
- **R7.** `angular.json` keeps the `production.fileReplacements`
  block for `environment.prod.ts`. The `defaultConfiguration`
  remains `"production"`.
- **R8.** `tsconfig.json` `compilerOptions.target` and `module`
  remain `"ES2022"`. `experimentalDecorators` stays
  `true` (NgModules + decorators still required).
- **R9.** `tsconfig.spec.json` references the updated test builder.
- **R10.** `src/main.ts` and the bootstrap module
  (`src/app/app.module.ts`) continue to bootstrap the app with
  `platformBrowserDynamic().bootstrapModule(AppModule)`.
- **R11.** `src/styles.css` keeps the prebuilt Material theme
  import. If Material 20 removes the legacy prebuilt CSS, switch to
  the documented replacement (a `@use '@angular/material' as mat;
  @include mat.core();` block or a `mat.theme(...)` mixin call) and
  document the choice in the contract.
- **R12.** `src/index.html` keeps the same `<app-root>` and meta
  tags. No Material density class is added (the v15-v17 default
  density was removed; v18+ defaults are fine).
- **R13.** `src/environments/environment.ts` and
  `environment.prod.ts` are unchanged in shape; only the file
  contents stay as they are.
- **R14.** No changes under `src/app/` components, services, or
  routes, except where a v20 deprecation in the framework forces a
  one-line change (e.g. a removed type alias). If any such change
  is required, it is documented in the plan with a one-line
  explanation.
- **R15.** `specs/contracts/frontend-angular/contract.md` updates:
  - "Angular 16" → "Angular 20" in the Purpose, Current Behavior,
    and Browser-support subsections.
  - "Angular 16 budgets" → "Angular 20 budgets" in the npm-scripts
    table.
  - Any explicit mention of the legacy browser builder is removed
    in favor of `application`.
- **R16.** `specs/manifest.yml` lists `007-angular-20-migration` as
  an active change and the `active:` block points at it (change,
  contract `frontend-angular`, and the new context pack).

### Non-functional

- **R17.** `node_modules/.bin/tsc --noEmit -p tsconfig.app.json`
  exits 0.
- **R18.** `node_modules/.bin/ng build --configuration production
  --output-path /tmp/escalabirras-fe-prod` succeeds.
- **R19.** `node_modules/.bin/ng build --configuration development`
  succeeds (the dev-mode smoke for the new `application` builder).
- **R20.** No regression in the 64 backend tests (`pytest backend
  -v`).
- **R21.** `npm install` completes without `ERESOLVE` / peer-
  dependency errors against the new versions.
- **R22.** No `npm audit` `high`/`critical` vulns introduced by the
  version bumps (best-effort; record any that surface).

### SDD / contract

- **R23.** `specs/manifest.yml` is synchronized with the new change.
- **R24.** `specs/changes/007-angular-20-migration/{spec,plan,
  tasks,context-pack}.md` exist and are coherent with each other.

## Acceptance Criteria

- **AC1.** `tsc --noEmit -p tsconfig.app.json` exits 0.
- **AC2.** `ng build --configuration production --output-path
  /tmp/escalabirras-fe-prod` succeeds and produces a `dist/`
  bundle that does **not** mention `JS_ANGULAR_MAJOR_VERSION` or
  any "browser builder" log line.
- **AC3.** `ng build --configuration development` succeeds.
- **AC4.** `pytest backend -v` reports 64/64 still passing.
- **AC5.** `git diff package.json package-lock.json` shows version
  bumps only inside the dependency blocks touched by this change;
  no unrelated transitive bumps beyond what `npm install` resolves.
- **AC6.** `specs/contracts/frontend-angular/contract.md` says
  "Angular 20" in every subsection that previously said
  "Angular 16".
- **AC7.** `specs/manifest.yml` lists
  `007-angular-20-migration` as the active change.
- **AC8.** Manual smoke: `ng serve` boots without runtime errors
  and `curl -s http://localhost:4200/` returns the production-
  style `<app-root>` HTML.