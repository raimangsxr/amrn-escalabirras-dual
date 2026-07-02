# 010 — Responsive iframe height

## Status

Active. The single source of truth lives in
`specs/manifest.yml`.

## What this change delivers

- A two-dimensional (width × height) bucket scheme in
  `LayoutService`. The service now emits one of nine combined
  buckets (`layout-compact-short`, `layout-compact-medium`,
  `layout-compact-tall`, `layout-narrow-short`,
  `layout-narrow-medium`, `layout-narrow-tall`, `layout-wide-short`,
  `layout-wide-medium`, `layout-wide-tall`) instead of the three
  width-only buckets introduced by `005-responsive-iframe`.
- `MainViewComponent` reacts to the height bucket: short iframes
  hide the two logos and the Top 3 list and collapse the header
  to title + subtitle only; medium iframes use the regular layout
  with slightly tighter fluid type.
- `WinnerComponent` reacts to the height bucket: short iframes
  drop the `mt-`/`-mt-` margins and shrink the fluid text so the
  three celebration lines fit a 200 px tall iframe.
- An expanded manual iframe test in
  `specs/contracts/frontend-angular/contract.md` that covers the
  nine combined buckets.
- The `frontend-angular` contract updated to document the nine
  buckets, the height-driven layout shifts, and the new manual
  test.

## What this change does NOT do

- No backend changes. No new endpoints, no new migrations.
- No new Angular components. Only `LayoutService`,
  `MainViewComponent`, `WinnerComponent`, and `styles.css` are
  touched.
- No new dependencies. `ResizeObserver` already reports both
  width and height.
- No automated visual regression tests. The manual iframe test in
  the contract is the verification.
- No `postMessage` from the iframe to the parent (no adaptive
  height sent upwards).
