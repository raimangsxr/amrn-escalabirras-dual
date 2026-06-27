# Plan: 005-responsive-iframe

## Approach

The change is purely a CSS + Angular refactor. We do not touch the
backend, the auth flow, the embed-token flow, the keyboard
shortcuts, or the data model. We add one tiny service
(`LayoutService`), update the global stylesheet so the iframe
becomes a true flex container, and rewrite every component's
template to use Tailwind arbitrary `clamp()` sizes plus
breakpoint-driven layout shifts.

The implementation order:

1. SDD scaffolding (this change's spec / plan / tasks /
   context-pack, plus the `frontend-angular` update).
2. Global styles (`src/styles.css`, `src/index.html`).
3. `LayoutService` and bootstrap in `AppComponent`.
4. Refactor each component, smallest first.
5. Validate: `tsc`, `ng build`, `pytest backend`, manual iframe
   test (best-effort via `ng serve` + `curl` to confirm the bundle
   is the same regardless of iframe size).

## Steps

### Phase 0 — SDD

1. Update `specs/manifest.yml` to point `active:` at
   `005-responsive-iframe`.
2. Add the "Responsive / iframe sizing" section to
   `specs/contracts/frontend-angular/contract.md`.
3. Write `specs/changes/005-responsive-iframe/spec.md`,
   `plan.md`, `tasks.md`, `context-pack.md`.

### Phase 1 — Global layout

4. Update `src/styles.css`:
   - `html, body { height: 100%; margin: 0; overflow: hidden; }`
   - `app-root { display: flex; flex-direction: column;
     height: 100%; }`
   - Add a `@media (prefers-reduced-motion: reduce)` block that
     disables the random background flip in the celebration.
5. Update `src/index.html` to drop the global body classes that
   conflict with full-height.

### Phase 2 — Layout service

6. Add `src/app/services/layout.service.ts` with:
   - `layoutClass$ = new BehaviorSubject<'layout-compact' |
     'layout-narrow' | 'layout-wide'>('layout-wide')`.
   - `start(): void` that subscribes a `ResizeObserver` on
     `document.body` and pushes the bucket.
   - `stop(): void` for cleanup.
   - The bucket function: `width < 480 → compact`;
     `width < 768 → narrow`; else `wide`.
   - The class is also applied to `document.documentElement` so
     plain CSS rules can key off it.
7. Update `AppComponent` to inject `LayoutService`, call `start()`
   on init, and `stop()` on destroy.

### Phase 3 — Component refactor

8. `MainViewComponent`:
   - Header: `flex-col md:flex-row` so the logo stacks under the
     title on narrow widths.
   - Logo: `w-32 md:w-72` so it shrinks.
   - Title: `text-[clamp(1.5rem,4vw,3.75rem)]`.
   - Subtitle: `text-[clamp(1rem,3vw,2.25rem)]`.
   - Top3 + manager row: `flex-col xl:flex-row` so it stacks until
     XL.
   - Tokens / Salir buttons: keep at bottom, `flex-col sm:flex-row`
     so they stack on narrow.
   - Error banner stays at top.
9. `ManagerComponent`:
   - Three columns become `flex-col lg:flex-row`.
   - Each column gets `basis` only on wide: `lg:basis-4/12`.
   - Focus button stays in its own row, `w-full sm:w-auto`.
10. `TeamManagerRedComponent` / `TeamManagerBlueComponent`:
    - "Torre Roja"/"Torre Azul" label: `text-[clamp(1.25rem,4vw,3.75rem)]`.
    - Name: `text-[clamp(1.25rem,3.5vw,3.75rem)]`.
    - Counter: `text-[clamp(2rem,6vw,6rem)]`.
    - Input remains `maxlength="20"` but width adjusts.
11. `Top3Component`:
    - Header: `text-[clamp(1rem,2.5vw,2.25rem)]`.
    - Per-entry: `text-[clamp(0.875rem,2vw,3rem)]`.
    - Award icons: `w-16 md:w-20`.
12. `ParticipantListComponent`:
    - Header: `text-[clamp(1rem,2.5vw,1.875rem)]`.
    - Per-entry: `text-[clamp(0.875rem,1.5vw,1.25rem)]`.
13. `WinnerComponent`:
    - `h-screen` → `h-full` so the overlay fills the iframe.
    - All three text spans use `clamp()`.
    - `mt-20` and `-mt-20` become fluid `mt-[clamp(1rem,4vh,5rem)]`.
14. `LoginComponent`:
    - `w-96` → `w-full max-w-sm mx-4`.
    - Form padding shrinks on narrow: `p-6 md:p-10`.
15. `TokensComponent`:
    - Modal: `w-full max-w-2xl mx-4` and `max-h-full md:max-h-[90%]`
      on the inner card.
    - Padding shrinks: `p-4 md:p-6`.

### Phase 4 — Validation

16. Run `tsc --noEmit -p tsconfig.app.json` until exit 0.
17. Run `ng build --configuration production --output-path
    /tmp/escalabirras-fe-prod` until green.
18. Run `pytest backend -v` to confirm no regression.
19. Run a `curl` smoke against `ng serve` at `/`, `/login`, and
    `/?embed_token=...` (best-effort; the actual rendering test
    requires a browser).
20. Final consistency sweep:
    - No `TODO` placeholders in the new SDD files.
    - `git status src/` shows only the intended modifications.

## Risks

- **`vh` vs `%` in clamp.** We use `vw` for fluid type because it
  scales with the iframe width, which is the dimension that matters
  for legibility. The celebration overlay uses `h-full` (parent
  height) instead of `h-screen` (viewport height), so the overlay
  always fills the iframe even if the iframe is very short.
- **ResizeObserver in a hidden iframe.** If the iframe is in a
  background tab, `ResizeObserver` may not fire immediately. The
  service emits the initial value on construction so the layout is
  correct on first paint; subsequent updates fire as expected.
- **`overflow: hidden` on body.** Some browsers (Safari iOS)
  refuse to honor `overflow: hidden` on `body`. We mitigate by
  using `min-h-0` on flex children so any overflow can be
  contained; if the parent refuses to clip, content can still
  scroll inside its own container.
- **`min-h-0` requirement.** Flex children that need to shrink
  below their content size require `min-h-0`. We add it where
  needed (the main view flex column, the celebration container).
- **Aspect ratio changes.** Switching from landscape to portrait
  triggers a `ResizeObserver` callback; the layout service
  re-emits the new class and Angular re-applies the templates.
  Performance is fine for the few components involved.
- **No SSR concerns.** This is a plain Angular SPA; the service
  uses `document` which is safe in the browser.
- **Tailwind arbitrary values are verbose.** We accept this in
  exchange for the explicit min/max clamps. A future change can
  extract a custom plugin or a Tailwind preset.
- **No automated visual regression tests.** The iframe-size
  verification is manual; documented in the contract's "Manual
  test" block.