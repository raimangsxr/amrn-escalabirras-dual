# Tasks: 008-angular-22-migration

## Tasks

### Phase 0 — SDD + tooling

- [x] `brew install node@24`.
- [x] `node@24 --version` is `v24.18.0` (≥ 24.15.0).
- [x] Write `specs/changes/008-angular-22-migration/spec.md`.
- [x] Write `specs/changes/008-angular-22-migration/plan.md`.
- [x] Write this task list.
- [x] Write
      `specs/changes/008-angular-22-migration/context-pack.md`.
- [x] Update `specs/contracts/frontend-angular/contract.md`
      ("Angular 20" → "Angular 22").
- [x] Update `specs/manifest.yml` (add
      `008-angular-22-migration`, mark
      `007-angular-20-migration` as `superseded`, point `active:`
      at `008`).
- [x] Stash the SDD scaffolding so `ng update` sees a clean tree.

### Phase 1 — Major-by-major `ng update`

- [x] `npx ng update @angular/cli@21 @angular/core@21
      --allow-dirty --force` (with `node@24` on `PATH`).
- [x] `npx ng update @angular/material@21 @angular/cdk@21
      --allow-dirty --force`.
- [x] `npx ng update @angular/cli@22 @angular/core@22
      --allow-dirty --force`.
- [x] `npx ng update @angular/material@22 @angular/cdk@22
      --allow-dirty --force`.
- [x] Re-pin all bumped deps with `~`.

### Phase 2 — Material prebuilt sanity

- [x] Confirm `@angular/material/prebuilt-themes/indigo-pink.css`
      is still imported.

### Phase 2.5 — Out-of-spec tweaks

- [x] Added `ignoreDeprecations: "6.0"` to `tsconfig.json` to
      silence TypeScript 6 deprecation errors for `baseUrl` and
      `downlevelIteration` (both are no-op in this codebase).
- [x] v21 migration converted templates from `*ngIf` / `*ngFor`
      to the new block control flow (`@if` / `@for`). Not a
      standalone-components change; pure template syntax.
- [x] v22 migration added `ChangeDetectionStrategy.Eager` to all
      components (explicit now; was implicit in v20).
- [x] v22 migration added `withXhr()` to
      `provideHttpClient(...)` in `AppModule`.

### Phase 3 — Validation

- [x] `tsc --noEmit -p tsconfig.app.json` exits 0.
- [x] `ng build --configuration production --output-path
      /tmp/escalabirras-fe-prod-v22` succeeds (564 kB initial;
      14 kB over the 550 kB warning budget, under the 1 MB error
      budget).
- [x] `ng build --configuration development --output-path
      /tmp/escalabirras-fe-dev-v22` succeeds.
- [x] `pytest backend -v` is 64/64.
- [x] `ng serve --port 4200` boots; `curl -s http://localhost:
      4200/` returns 200 + `<app-root>`.

### Phase 4 — Restore SDD and cleanup

- [x] Restore the SDD scaffolding from the stash.
- [x] Verify the manifest and contract are coherent with the
      bump.
- [x] Final consistency sweep: no "Angular 20" mentions in the
      updated files; no `browserTarget`; no `:browser` builder.

## Out of scope (recorded for future changes)

- Standalone components migration.
- Signals migration.
- Zoneless change detection migration.
- Material 22 M3 `mat.theme` mixin migration.
- Frontend unit tests (Vitest or Karma).
- Per-change CI pipeline.
- SSR / hydration / prerendering.
- `.nvmrc` / `.node-version` pin so contributors pick Node 24
  automatically.
- Bump the prod bundle budget from 550 kB to 600 kB (or trim the
  bundle) to silence the v22 budget warning.