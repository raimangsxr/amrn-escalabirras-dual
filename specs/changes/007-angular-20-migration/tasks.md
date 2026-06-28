# Tasks: 007-angular-20-migration

## Tasks

### Phase 0 — SDD

- [x] Write `specs/changes/007-angular-20-migration/spec.md`.
- [x] Write `specs/changes/007-angular-20-migration/plan.md`.
- [x] Write this task list.
- [x] Write
      `specs/changes/007-angular-20-migration/context-pack.md`.
- [x] Update `specs/contracts/frontend-angular/contract.md`
      ("Angular 16" → "Angular 20").
- [x] Update `specs/manifest.yml` (add
      `007-angular-20-migration`, set `active:` block).

### Phase 1 — Major-by-major `ng update`

- [x] Pre-flight: `node --version` ≥ 18.13, working tree clean.
- [x] `npx ng update @angular/cli@17 @angular/core@17
      @angular/material@17 @angular/cdk@17`.
- [x] `npx ng update @angular/cli@18 @angular/core@18
      @angular/material@18 @angular/cdk@18`.
- [x] `npx ng update @angular/cli@19 @angular/core@19
      @angular/material@19 @angular/cdk@19`.
- [x] `npx ng update @angular/cli@20 @angular/core@20
      @angular/material@20 @angular/cdk@20`.
- [x] Re-pin all bumped deps with `~`.

### Phase 2 — Material prebuilt sanity

- [x] Confirm `@angular/material/prebuilt-themes/indigo-pink.css`
      is still imported (or accept the M3 rewrite).
- [x] Document the Material prebuilt deprecation in the
      contract's Configuration subsection.
- [x] Manual migration to `@angular/build:application`
      (schematic requires Node ≥ 22.22.3, dev env is 22.14).
      See context-pack "Risks" for the diff summary.

### Phase 3 — Validation

- [x] `node_modules/.bin/tsc --noEmit -p tsconfig.app.json`
      exits 0.
- [x] `node_modules/.bin/ng build --configuration production
      --output-path /tmp/escalabirras-fe-prod` succeeds (545 kB
      initial, under the 550 kB warning).
- [x] `node_modules/.bin/ng build --configuration development
      --output-path /tmp/escalabirras-fe-dev` succeeds.
- [x] `/tmp/venv-002/bin/pytest backend -v` is 64/64.
- [x] `ng serve --port 4200` boots; `curl -s http://localhost:
      4200/` returns 200 + `<app-root>`.

### Phase 4 — Cleanup

- [x] Resolve any `// TODO` markers left by `ng update` (none
      found).
- [x] Final consistency sweep: no `browserTarget`; no
      `:browser` builder; `@angular/build:*` everywhere.
- [ ] Mark `007-angular-20-migration` `superseded` in
      `specs/manifest.yml` (deferred — see note below).

> **Supersede note.** Per AGENTS.md rule 7, a change is marked
> `superseded` only when a successor change is opened. The current
> `active:` block points at this change; flipping its status to
> `superseded` here would require opening another change or moving
> `active:` elsewhere. Leave the change `active` and the user (or
> the next change) flips the status when warranted.

## Out of scope (recorded for future changes)

- Standalone components migration.
- Signals migration.
- Zoneless change detection migration.
- Material 20 M3 `mat.theme` mixin migration.
- Frontend unit tests (Vitest or Karma).
- Per-change CI pipeline.
- SSR / hydration / prerendering.