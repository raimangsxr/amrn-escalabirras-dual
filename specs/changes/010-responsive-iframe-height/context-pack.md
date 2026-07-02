# Context Pack: 010-responsive-iframe-height

## Goal

Extend the responsive layout introduced by
`005-responsive-iframe` so the Angular frontend adapts to **both**
the width **and** the height of its container (the iframe). Today
`LayoutService` emits one of three width buckets; this change
promotes it to one of nine combined buckets and adapts
`MainViewComponent` and `WinnerComponent` so the operator's
actions remain usable inside very short iframes (projector strips,
sidebar widgets, square embeds).

## Relevant Contracts

- `specs/contracts/frontend-angular/contract.md` (live; updated to
  add the height dimension to the "Responsive / iframe sizing"
  section).

## Current Understanding

- `LayoutService` (`src/app/services/layout.service.ts`) currently
  observes only the iframe **width** and emits `'layout-compact' |
  'layout-narrow' | 'layout-wide'` based on `< 480`, `< 768`, and
  `>= 768` px. It applies the class to
  `document.documentElement` and mirrors it to
  `document.documentElement.dataset.layout`.
- `ResizeObserver` already reports
  `entry.contentRect.{width,height}`, so the service can read both
  axes without any new dependencies.
- The width-only class names are not yet consumed by any CSS
  rule (they are only applied to `<html>`); the v1 responsive work
  is done with Tailwind variants. Replacing the width-only classes
  with the new combined ones is therefore safe.
- `MainViewComponent` keeps the header (logo + title + subtitle)
  visible at any height; in a 1024×200 iframe the header eats half
  the vertical space and the team panels / Top 3 list are clipped.
- `WinnerComponent` uses `h-full` plus fluid `mt-`/`-mt-` margins
  and `clamp()` text sizes that scale with viewport **width**. In a
  short iframe the three text lines stack past the bottom of the
  overlay.
- The angular reactive layer uses `async` pipes in templates and
  `OnPush` change detection in the components, so subscribing to
  the bucket observable in the components is cheap.
- No backend changes.
- No new dependencies.

## Files / Areas Likely Involved

### Modified

- `src/app/services/layout.service.ts` — emit the nine combined
  buckets; read both width and height.
- `src/app/main-view/main-view.component.{ts,html}` — inject
  `LayoutService`, hide the logos and the `<app-top3>` block on
  `*-short`; collapse the header to title + subtitle on `*-short`;
  tighten fluid type on `*-medium`.
- `src/app/winner/winner.component.{ts,html}` — inject
  `LayoutService`, drop the `mt-`/`-mt-` margins and shrink the
  fluid text on `*-short`.
- `src/styles.css` — `@layer components` rules keyed off the
  bucket classes (medium → tighter fluid type).

### New

- `specs/changes/010-responsive-iframe-height/change.md` — short
  status file matching the style of `009-admin-event-config`.
- `specs/changes/010-responsive-iframe-height/spec.md`,
  `plan.md`, `tasks.md`, `context-pack.md` — SDD artifacts.

### Untouched

- Backend code, migrations, tests.
- All other Angular components: `LoginComponent`,
  `AdminComponent`, `ManagerComponent`,
  `TeamManagerRedComponent`, `TeamManagerBlueComponent`,
  `Top3Component`, `ParticipantListComponent`,
  `TokensComponent`, `LoginComponent`,
  `AuthService`, `AppService`, `EventService`.
- `AppComponent`, `AppRoutingModule`, `AppModule`,
  `index.html`, `main.ts`.
- `src/environments/*`.

## Constraints

- **No new dependencies.** `ResizeObserver` is universally
  available in the Angular 22 browser set.
- **Strict TypeScript** stays green.
- **No new tests.** The manual iframe test in the contract is
  the verification.
- **`overflow: hidden` on body** stays in place (introduced by
  `005`).
- **`min-h-0`** on flex children that must shrink below their
  content size (`app-root`, `MainViewComponent`).
- **Combined bucket naming.** Single class string of the form
  `layout-{width}-{height}`. Tailwind arbitrary variants
  (`layout-compact-short:flex-row`) are intentionally **not**
  used; the height-sensitive pieces are guarded in the templates
  with `@if` / `[ngClass]`, and the medium tightening lives in
  `styles.css`.
- **First-paint correctness.** `LayoutService.computeInitial()`
  reads the size synchronously in the constructor so the bucket
  is on `<html>` before Angular renders the first frame.

## Validation Plan

1. **TypeScript** (narrow).

   ```bash
   node_modules/.bin/tsc --noEmit -p tsconfig.app.json
   ```

   Expectation: exit 0.

2. **Angular production build** (narrow).

   ```bash
   node_modules/.bin/ng build --configuration production \
       --output-path /tmp/escalabirras-fe-prod
   ```

   Expectation: bundle produced; no template errors.

3. **Backend regression** (broad).

   ```bash
   pytest backend -v
   ```

   Expectation: same number of passing tests as before (no
   regression).

4. **Dev-server smoke** (broad).

   ```bash
   node_modules/.bin/ng serve --host 127.0.0.1 --port 4200
   curl -s -o /dev/null -w "/                  HTTP %{http_code}\n" http://127.0.0.1:4200/
   curl -s -o /dev/null -w "/?embed_token=xxx  HTTP %{http_code}\n" "http://127.0.0.1:4200/?embed_token=embed_xxx"
   ```

   Expectation: both 200.

5. **Manual iframe test** (broad, browser required). Document
   the nine iframes in `frontend-angular/contract.md` under
   "Manual test".

6. **Final consistency sweep** (broad).

   ```bash
   grep -nR "TODO" specs/contracts/frontend-angular/contract.md specs/changes/010-responsive-iframe-height
   git status frontend/src/
   grep -nR "layout-compact\b\|layout-narrow\b\|layout-wide\b" frontend/src
   ```

   Expectation: no `TODO` outside backticks; only the intended
   changes under `frontend/src/`; no remaining references to the
   old width-only class names outside the contract.

## Risks

- **Bucket churn.** Resizing the iframe generates one observer
  callback per axis transition; `LayoutService` compares against
  the current bucket before pushing, so identical buckets do not
  emit.
- **`document.body.clientHeight` reported as `0`.** Mitigated by
  falling back to `window.innerHeight`, then `768`.
- **Nine buckets is a lot.** The CSS rules are intentionally
  defensive: the medium bucket inherits from the regular layout,
  and only the short bucket drives significant overrides.
- **`mt-0` collision with `md:mt-0`.** Tailwind's `md:mt-0` keeps
  the same specificity order; we drop both modifiers when
  `isShort` is true.
- **No automated visual regression tests.** The iframe-size
  verification is manual; documented in the contract's "Manual
  test" block.
- **Confusion with the legacy width-only buckets.** The contract
  is explicit that the width-only scheme from `005` is
  superseded; a future change may want to delete the historical
  reference. Documented as "out of scope" in `tasks.md`.

## Recommendations (do not create in this change)

- **`responsive-tokens` contract** (not created): would own a
  token-based design system (spacing, color, type scale) that
  components consume. The fluid type is hardcoded per template
  via `clamp()`; a future change can centralize it.
- **`iframe-host` contract** (not created): would document the
  shape, sandbox flags, and `postMessage` contract between the
  parent and the escalabirras iframe.
- **Playwright / Cypress visual regression tests** for the nine
  buckets.
- **Adaptive iframe height** sent to the parent via `postMessage`,
  so the parent can fit the iframe's natural height on first
  paint.
