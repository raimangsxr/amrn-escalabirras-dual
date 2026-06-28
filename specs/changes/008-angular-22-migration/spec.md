# Spec: 008-angular-22-migration

## Problem

The Angular frontend was bumped to Angular 20 in
`007-angular-20-migration`. Angular 20 reaches end-of-support in
May 2026; the current stable line is Angular 22 (released May 2026),
and Angular 21 was released November 2025.

The dev environment is on Node 22.14.0, which does not meet
Angular 22's minimum (`^22.22.3 || ^24.15.0 || >=26.0.0`). The
change therefore also installs Node 24 LTS via Homebrew so the
`ng update` schematics can run.

Scope is intentionally narrow (consistent with `007`): we keep the
existing NgModule-based architecture, RxJS `BehaviorSubject` state,
Karma + Jasmine, and zone.js change detection. The migration is a
version bump + tooling update, not a refactor.

## Goals

- Bump the frontend from Angular 20 to Angular 22.0.4 (latest
  stable as of the change's planning date).
- Bump `@angular/material` and `@angular/cdk` to the matching
  22.x release.
- Bump `typescript` to the version Angular 22 supports.
- Bump `rxjs` to `~7.8.0` (already there; stays).
- Bump `zone.js` if Angular 22 raises the floor (likely no change
  from v20's `~0.15.0`).
- Run `ng update` for `@angular/cli`, `@angular/core`,
  `@angular/material`, and `@angular/cdk` for both v21 and v22.
  The migrations apply the schematics per major.
- Install Node 24 LTS (`node@24`) via Homebrew so `ng update`
  schematics for v21 / v22 can pass their Node version gate.
- Update `specs/contracts/frontend-angular/contract.md` so the
  documented framework version reflects v22.
- Update `specs/manifest.yml` to list `008-angular-22-migration`
  as an active change and mark `007-angular-20-migration` as
  `superseded`.

## Non-Goals

- No architectural rewrite. We do not adopt standalone components,
  signals, the new control flow, or `provide*` functions. Existing
  NgModules, RxJS streams, and constructor injection stay.
- No zoneless change detection. `zone.js` stays.
- No switch to Jest or Vitest. Karma + Jasmine stay.
- No SSR, no hydration, no prerendering. The frontend stays an SPA.
- No backend changes.
- No dependency bumps unrelated to the Angular major.
- No visual changes. Templates, styles, copy, and colors stay.
- No new tests.

## Requirements

### Functional

- **R1.** `package.json` declares `@angular/*`, `@angular/material`,
  `@angular/cdk`, `@angular/cli`, `@angular/compiler-cli`,
  `@angular/build` at the Angular 22 minor that the release notes
  call out as compatible, pinned with `~`.
- **R2.** `package.json` declares `typescript` at the version
  Angular 22 supports (likely `~5.9.0`; confirmed at the
  implementation step).
- **R3.** `package.json` declares `zone.js` at the Angular 22
  floor (likely `~0.15.x`; no change from v20).
- **R4.** `angular.json` keeps the four `@angular/build:*` builders
  (application, dev-server, extract-i18n, karma).
- **R5.** `angular.json` keeps the `production.fileReplacements`
  block for `environment.prod.ts`.
- **R6.** `tsconfig.json` `moduleResolution` stays at `"bundler"`.
  Any new required option that v22 introduces is added.
- **R7.** `src/main.ts` and `src/app/app.module.ts` continue to
  bootstrap the app with `platformBrowserDynamic().bootstrapModule
  (AppModule)`.
- **R8.** `src/styles.css` keeps the prebuilt Material theme import.
- **R9.** `src/environments/environment.ts` and
  `environment.prod.ts` are unchanged in shape.
- **R10.** No changes under `src/app/` components, services, or
  routes, except where a v21 or v22 deprecation in the framework
  forces a one-line change. Document each in the plan.
- **R11.** `specs/contracts/frontend-angular/contract.md` updates:
  - "Angular 20" → "Angular 22" in the Purpose, Current Behavior,
    Browser-support, and Validation subsections.
  - "Angular 20 budgets" → "Angular 22 budgets" in the npm-scripts
    table.
- **R12.** `specs/manifest.yml` lists `008-angular-22-migration` as
  an active change and marks `007-angular-20-migration` as
  `superseded`. The `active:` block points at
  `008-angular-22-migration`.
- **R13.** Node 24 LTS (`node@24`) is installed via Homebrew. The
  change does not commit a `.nvmrc` (out of scope).

### Non-functional

- **R14.** `node_modules/.bin/tsc --noEmit -p tsconfig.app.json`
  exits 0.
- **R15.** `node_modules/.bin/ng build --configuration production
  --output-path /tmp/escalabirras-fe-prod` succeeds.
- **R16.** `node_modules/.bin/ng build --configuration development
  --output-path /tmp/escalabirras-fe-dev` succeeds.
- **R17.** No regression in the 64 backend tests (`pytest backend
  -v`).
- **R18.** `npm install` completes without `ERESOLVE` / peer-
  dependency errors against the new versions.
- **R19.** Manual smoke: `ng serve` boots and `curl -s
  http://localhost:4200/` returns 200 + `<app-root>`.

### SDD / contract

- **R20.** `specs/manifest.yml` is synchronized with the new
  change and the superseded status of `007`.
- **R21.** `specs/changes/008-angular-22-migration/{spec,plan,
  tasks,context-pack}.md` exist and are coherent.

## Acceptance Criteria

- **AC1.** `tsc --noEmit -p tsconfig.app.json` exits 0.
- **AC2.** `ng build --configuration production --output-path
  /tmp/escalabirras-fe-prod` succeeds and produces a `dist/`
  bundle.
- **AC3.** `ng build --configuration development --output-path
  /tmp/escalabirras-fe-dev` succeeds.
- **AC4.** `pytest backend -v` reports 64/64 still passing.
- **AC5.** `git diff package.json package-lock.json` shows version
  bumps only inside the dependency blocks touched by this change.
- **AC6.** `specs/contracts/frontend-angular/contract.md` says
  "Angular 22" in every subsection that previously said
  "Angular 20".
- **AC7.** `specs/manifest.yml` lists
  `008-angular-22-migration` as the active change and marks
  `007-angular-20-migration` as `superseded`.
- **AC8.** Manual smoke: `ng serve` boots without runtime errors
  and `curl -s http://localhost:4200/` returns the production-
  style `<app-root>` HTML.
- **AC9.** `/opt/homebrew/opt/node@24/bin/node --version` returns
  `v24.x.y` with `>= 24.15.0`.