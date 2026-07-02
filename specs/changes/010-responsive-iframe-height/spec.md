# Spec: 010-responsive-iframe-height

## Problem

The Angular frontend's responsive layout (introduced by
`005-responsive-iframe`) only adapts to the **width** of its
container. The `LayoutService` observes the document body, computes
one of three width buckets (`layout-compact` < 480, `layout-narrow`
480–767, `layout-wide` ≥ 768) and writes it to `<html>`. Templates
react via Tailwind responsive variants and `clamp()`-based fluid
type, all driven by viewport **width**.

When the app is embedded in an iframe whose height is also
constrained (the typical case for the projector / sidebar / widget
deployments described in `004-auth-and-embed-tokens`), the height
is ignored and several things break:

- A 1024×150 projector strip and a 1024×1080 desktop embed share
  the same `layout-wide` bucket, even though the strip has only
  enough vertical space for one row of text.
- The celebration overlay (`WinnerComponent`) uses `h-full` plus
  fluid margins (`mt-12`, `mt-48`, `mt-20`). In a 1024×150 strip
  the overlay renders, but the three text lines stack below the
  bottom of the iframe and become invisible.
- `MainViewComponent`'s header keeps the logo + title + subtitle
  block visible at any height, so the team panels and the Top 3
  list end up squeezed (or clipped) when the iframe is short.
- The Top 3 list and the manager columns compete for vertical
  space; in a short iframe neither wins.

This change makes the application responsive in **both** axes at
once, by promoting the `LayoutService` from a one-dimensional
bucket to a two-dimensional (width × height) bucket.

## Goals

- Extend `LayoutService` so it emits one of nine combined buckets
  (`layout-{width}-{height}`) computed from the iframe's current
  width **and** height. The width thresholds (480, 768) stay as
  `005` set them. The height thresholds are 384 and 576.
- Apply the resulting class to `<html>` and mirror it to
  `document.documentElement.dataset.layout`, same as today.
- Adapt `MainViewComponent` so short iframes collapse the header,
  hide the Top 3 list, and reduce the manager padding, freeing
  vertical space for the team panels and the input row.
- Adapt `WinnerComponent` so short iframes drop the
  `mt-`/`-mt-` margins and shrink the fluid text, so the three
  lines fit vertically.
- Update the `frontend-angular` contract to document the new
  buckets, the layout shifts table, and the manual iframe test.
- Keep all 58 backend tests, the `004`/`008`/`009` acceptance
  criteria, and the existing `005` width behavior unchanged for
  tall iframes.

## Non-Goals

- No redesign of the visual language. Same colors, same copy, same
  icons.
- No backend changes.
- No new dependencies. The `ResizeObserver` already observes
  `contentRect` which exposes both `width` and `height`.
- No Tailwind plugin / preset. The new bucket classes are consumed
  with arbitrary Tailwind variants (`layout-compact-short:flex-row`
  is not needed — the change sticks to component-level
  `*ngIf` / `[ngClass]` checks against `layoutClass$` for the few
  height-sensitive pieces, and to additional CSS rules in
  `styles.css` keyed off the bucket class).
- No new routes or new components. Only `LayoutService`,
  `MainViewComponent`, `WinnerComponent`, `styles.css`, and the
  contract SDD files are touched.
- No SSR / responsive hydration concerns.

## Requirements

### Functional

- **R1.** `src/app/services/layout.service.ts` exposes
  `layoutClass$: Observable<LayoutBucket>` where `LayoutBucket`
  is the union of the nine literal strings
  `'layout-compact-short' | 'layout-compact-medium' | 'layout-compact-tall' | 'layout-narrow-short' | 'layout-narrow-medium' | 'layout-narrow-tall' | 'layout-wide-short' | 'layout-wide-medium' | 'layout-wide-tall'`.
- **R2.** The bucket is computed from the iframe's content rect:
  - `widthBucket`: `< 480 → 'compact'`, `< 768 → 'narrow'`, else
    `'wide'`.
  - `heightBucket`: `< 384 → 'short'`, `< 576 → 'medium'`, else
    `'tall'`.
  - The combined bucket is `'layout-' + widthBucket + '-' + heightBucket`.
- **R3.** The `ResizeObserver` still runs outside Angular's zone;
  bucket changes are pushed through `NgZone.run(...)` so OnPush
  components re-render.
- **R4.** `document.documentElement` always carries exactly one of
  the nine classes; the previous three width-only classes
  (`layout-compact`, `layout-narrow`, `layout-wide`) are no longer
  emitted.
- **R5.** `document.documentElement.dataset.layout` always equals
  the current bucket.
- **R6.** `AppComponent` continues to construct `LayoutService` via
  DI; no call-site change is required.
- **R7.** `MainViewComponent` reacts to the bucket via an
  `async`-bound local property. When `heightBucket === 'short'` it:
  - Hides the logo (`<img src="...logo-motoclub.png">` is not
    rendered).
  - Hides the second logo (`<img src="...logo-escalabirras.png">`
    is not rendered) and the `<app-top3>` block.
  - Tightens the header padding and gaps.
  When `heightBucket === 'medium'` it uses the regular layout but
  with reduced fluid-type clamps on the title / subtitle.
- **R8.** `WinnerComponent` reacts to the bucket via an
  `async`-bound local property. When `heightBucket === 'short'` it:
  - Removes the `mt-12`, `mt-48`, `mt-20`, `-mt-4`, `-mt-20`
    margins (sets them all to `mt-0`).
  - Reduces the fluid type to smaller `clamp()` values so the
    three lines fit a 200 px tall iframe.
  When `heightBucket === 'medium'` the existing `md:`-suffixed
  margins are still applied, but the base margins stay at `mt-4`.
- **R9.** No `*-narrow-short` / `*-compact-short` /
  `*-wide-short` / `*-narrow-medium` / `*-compact-medium` /
  `*-wide-medium` rules are added beyond what's documented in R7
  and R8; the medium bucket only adds the title-type tightening,
  and the short bucket drives the layout collapse.
- **R10.** `src/styles.css` adds a `@layer components` block with
  the documented rules (header/logo hiding, top3 hiding, fluid
  type tightening) keyed off the nine bucket classes. The block
  uses pure CSS; no JS hooks are required.

### Non-functional

- **R11.** `tsc --noEmit -p tsconfig.app.json` exits 0.
- **R12.** `ng build --configuration production --output-path
  /tmp/...` succeeds.
- **R13.** No regressions in any of the existing backend tests.
- **R14.** No regressions in the existing 24-step backend E2E
  smoke.
- **R15.** `document.documentElement.dataset.layout` reflects the
  current bucket within one frame after an iframe resize, without
  visible layout shift on first paint.

### SDD / contract

- **R16.** `specs/contracts/frontend-angular/contract.md`
  documents the nine buckets, the new height-driven layout shifts,
  and the expanded manual iframe test.
- **R17.** `specs/manifest.yml` reflects
  `010-responsive-iframe-height` as the active change.

## Acceptance Criteria

- **AC1.** `tsc --noEmit -p tsconfig.app.json` exits 0.
- **AC2.** `ng build --configuration production --output-path
  /tmp/escalabirras-fe-prod` succeeds.
- **AC3.** `pytest backend -v` reports the same number of passing
  tests as before (no regression).
- **AC4.** The bundle contains the rewritten `LayoutService`,
  `MainViewComponent`, `WinnerComponent`, and `styles.css`.
- **AC5.** Manual iframe test (in the contract) passes: rendering
  the production build in iframes at the nine documented sizes
  shows the operator's actions (scoring, top 3, celebration,
  tokens, logout) without overflow or unreadable text, and
  `document.documentElement.dataset.layout` matches the expected
  bucket from the table.
- **AC6.** `specs/manifest.yml` lists
  `010-responsive-iframe-height` as the active change.
- **AC7.** `specs/contracts/frontend-angular/contract.md` has no
  `TODO` placeholders in the updated "Responsive / iframe sizing"
  section.
