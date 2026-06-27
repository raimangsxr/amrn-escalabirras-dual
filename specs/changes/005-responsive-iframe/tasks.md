# Tasks: 005-responsive-iframe

## Tasks

### Phase 0 — SDD

- [x] Update `specs/manifest.yml` (point `active:` at `005`).
- [x] Add "Responsive / iframe sizing" section to
      `specs/contracts/frontend-angular/contract.md`.
- [x] Write `specs/changes/005-responsive-iframe/spec.md`.
- [x] Write `specs/changes/005-responsive-iframe/plan.md`.
- [x] Write this task list.
- [x] Write `specs/changes/005-responsive-iframe/context-pack.md`.

### Phase 1 — Global layout

- [x] Update `src/styles.css` (full-height, overflow,
      `prefers-reduced-motion`).
- [x] Update `src/index.html` (drop conflicting body classes).

### Phase 2 — Layout service

- [x] Add `src/app/services/layout.service.ts` (BehaviorSubject +
      ResizeObserver).
- [x] Wire into `AppComponent` (start on init, stop on destroy).

### Phase 3 — Component refactor

- [x] Refactor `MainViewComponent` (header stack, top3+manager
      stack, button stack, fluid type).
- [x] Refactor `ManagerComponent` (3 columns → 1 column on narrow).
- [x] Refactor `TeamManagerRedComponent` and
      `TeamManagerBlueComponent` (fluid type).
- [x] Refactor `Top3Component` (fluid type, smaller icons on
      narrow).
- [x] Refactor `ParticipantListComponent` (fluid type).
- [x] Refactor `WinnerComponent` (`h-full`, fluid text, fluid
      margins).
- [x] Refactor `LoginComponent` (`w-full max-w-sm mx-4`, smaller
      padding on narrow).
- [x] Refactor `TokensComponent` modal (full-width on narrow,
      `max-h-full`).

### Phase 4 — Validation

- [x] Run `tsc --noEmit -p tsconfig.app.json` until exit 0.
- [x] Run `ng build --configuration production --output-path
      /tmp/...` until green.
- [x] Run `pytest backend -v` (58/58 still green).
- [x] Run `curl` smoke against `ng serve` for `/`,
      `/?embed_token=…` (best-effort).
- [x] Final consistency sweep (no `TODO`, only intended
      modifications).

## Out of scope (recorded for future changes)

- Automated visual regression tests (Playwright / Cypress) for
  iframe sizes.
- Tailwind plugin / preset that bakes the fluid scale into
  semantic class names.
- A "size presets" switcher in the operator UI to preview the
  different layouts without resizing the iframe.
- Server-side rendering for tighter iframe integration (e.g.
  AMP).
- Different layouts for ultra-wide (≥ 1920 px) iframes; the wide
  layout already works there.