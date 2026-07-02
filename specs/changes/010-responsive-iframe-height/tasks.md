# Tasks: 010-responsive-iframe-height

## Tasks

### Phase 0 — SDD

- [x] Update `specs/contracts/frontend-angular/contract.md` with
      the nine-bucket table, the new layout shifts, and the
      expanded manual iframe test.
- [x] Write `specs/changes/010-responsive-iframe-height/spec.md`.
- [x] Write `specs/changes/010-responsive-iframe-height/plan.md`.
- [x] Write this task list.
- [x] Write `specs/changes/010-responsive-iframe-height/context-pack.md`.
- [x] Write `specs/changes/010-responsive-iframe-height/change.md`.
- [x] Update `specs/manifest.yml` (point `active:` at `010`).

### Phase 1 — Layout service

- [ ] Rewrite `src/app/services/layout.service.ts`:
      - `LayoutBucket` is the union of nine combined strings.
      - `widthBucketFor(width)` returns `'compact' | 'narrow' | 'wide'`.
      - `heightBucketFor(height)` returns `'short' | 'medium' | 'tall'`.
      - `combinedBucketFor(width, height)` joins them with `-`.
      - `apply(bucket)` adds the current class and removes the
        other eight (the old width-only classes are no longer
        emitted).
      - `computeInitial()` reads both width and height.
      - `start()` reads both axes from each observer entry.

### Phase 2 — `MainViewComponent`

- [ ] Inject `LayoutService` and expose `layoutClass$`.
- [ ] Wrap the second logo + `<app-top3>` block in an
      `@if (heightBucket !== 'short')` check.
- [ ] Wrap the first logo in an
      `@if (heightBucket !== 'short')` check (header collapses to
      title + subtitle only).
- [ ] Keep the existing `md:flex-row` / `xl:flex-row` width
      shifts intact.

### Phase 3 — `WinnerComponent`

- [ ] Inject `LayoutService` and expose `layoutClass$`.
- [ ] On `heightBucket === 'short'`, replace the fluid margins
      and reduce the fluid text clamps so the three lines fit a
      200 px tall iframe.
- [ ] On `heightBucket === 'medium'`, keep the layout but rely on
      the global stylesheet to tighten fluid type.

### Phase 4 — Global styles

- [ ] Update `src/styles.css` with the `@layer components` block
      that tightens `h1` / `h2` fluid type on
      `html.layout-*-medium`.

### Phase 5 — Validation

- [ ] Run `node_modules/.bin/tsc --noEmit -p tsconfig.app.json`
      until exit 0.
- [ ] Run `node_modules/.bin/ng build --configuration production
      --output-path /tmp/escalabirras-fe-prod` until green.
- [ ] Run `pytest backend -v` (same count as before).
- [ ] Run a `curl` smoke against `ng serve` for `/`, `/login`,
      `/admin`, `/?embed_token=…`.
- [ ] Final consistency sweep:
      - No `TODO` placeholders in the new SDD files.
      - `git status frontend/src/` shows only the intended
        modifications.
      - `grep -nR "layout-compact\b\|layout-narrow\b\|layout-wide\b"
        frontend/src` returns no remaining references to the
        old width-only class names.

## Out of scope (recorded for future changes)

- Playwright / Cypress visual regression tests for the nine
  buckets.
- A Tailwind plugin that bakes the nine buckets into semantic
  variants (`@responsive short:flex-row`).
- A "size presets" switcher in the operator UI to preview the
  different layouts without resizing the iframe.
- Adaptive iframe height sent to the parent via `postMessage`.
- Replacing the height observation with the `ResizeObserverEntry`
  `devicePixelContentBoxSize` for higher-precision scaling.
