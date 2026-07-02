# Plan: 010-responsive-iframe-height

## Approach

Promote the existing `LayoutService` from a one-dimensional (width
only) bucket to a two-dimensional (width × height) bucket. The
nine combined buckets let components and global CSS rules react
to **both** axes at once. The change is local to:

- `src/app/services/layout.service.ts` — the bucket computation
  and the `LayoutBucket` type.
- `src/app/main-view/main-view.component.{ts,html}` — react to
  `heightBucket === 'short'` by hiding the logos and the Top 3
  block, and to `heightBucket === 'medium'` by tightening the
  header fluid type.
- `src/app/winner/winner.component.{ts,html}` — react to
  `heightBucket === 'short'` by zeroing the vertical margins and
  shrinking the fluid text.
- `src/styles.css` — `@layer components` rules keyed off the
  bucket classes (the rule order: `html.layout-wide-tall` → reset
  → `html.layout-*-short` → override).
- `specs/contracts/frontend-angular/contract.md` — the
  "Responsive / iframe sizing" section and the manual test.
- `specs/manifest.yml` — point `active:` at
  `010-responsive-iframe-height`.

No backend changes. No new dependencies. No new components. No new
tests. The existing acceptance criteria from `005`,
`004-auth-and-embed-tokens`, `008-angular-22-migration`, and
`009-admin-event-config` continue to apply.

## Steps

### Phase 0 — SDD

1. Update `specs/manifest.yml` to add
   `010-responsive-iframe-height` (active) and to point
   `active:` at this change.
2. Update the "Responsive / iframe sizing" section of
   `specs/contracts/frontend-angular/contract.md` (done as part of
   the SDD policy rule 7 — the contract is updated **before**
   implementation begins).
3. Write `specs/changes/010-responsive-iframe-height/spec.md`,
   `plan.md`, `tasks.md`, `context-pack.md`, `change.md`.

### Phase 1 — Layout service

4. Rewrite `src/app/services/layout.service.ts`:
   - Replace `LayoutBucket` with the union of the nine combined
     bucket strings.
   - Replace `bucketFor(width)` with two helpers,
     `widthBucketFor(width)` and `heightBucketFor(height)`, plus a
     `combinedBucketFor(width, height)` that joins them.
   - Update `apply(bucket)` to add the current class and remove the
     other eight (the previous three width-only classes are no
     longer emitted).
   - Update `computeInitial()` to read both `document.body` width
     **and** `document.body` height (fallback to `window.innerWidth`
     / `window.innerHeight` for cross-browser parity, then
     `1024 × 768`).
   - Update `start()` so the observer reads
     `entry.contentRect.width` **and** `entry.contentRect.height`.

### Phase 2 — `MainViewComponent`

5. Inject `LayoutService` into `MainViewComponent`.
6. Expose `layoutClass$ = layoutService.layoutClass$`.
7. In the template, wrap the logos and `<app-top3>` block in
   `@if (heightBucket !== 'short')` checks. The width-driven
   `xl:flex-row` / `md:flex-row` classes are preserved unchanged
   so the `005` width shifts still apply.
8. On `heightBucket === 'short'`:
   - The whole header collapses to a single horizontal row with
     title + subtitle only.
   - The second logo + `<app-top3>` block is not rendered.
   - The remaining `<app-manager>` is allowed to fill the
     remaining vertical space (`flex-1 min-h-0`).
9. On `heightBucket === 'medium'`: tighten the title/subtitle
   `clamp()` values via CSS rules in `styles.css` (see Phase 4).

### Phase 3 — `WinnerComponent`

10. Inject `LayoutService` into `WinnerComponent`.
11. Expose `layoutClass$ = layoutService.layoutClass$`.
12. In the template, bind `isShort = heightBucket === 'short'`
    through an `async`-bound local. When `isShort` is true:
    - Replace `mt-12`, `mt-48`, `mt-20` with `mt-0`.
    - Replace `-mt-4`, `-mt-20` with `mt-0`.
    - Replace the `md:`-suffixed margins with `md:mt-0` (still
      `md:mt-0` is a no-op, so we can just drop them).
    - Reduce the fluid text to `clamp()` values that fit a 200 px
      tall iframe: title `clamp(1rem, 4vw, 2rem)`, name
      `clamp(1.25rem, 5vw, 2.5rem)`, counter
      `clamp(1.25rem, 5vw, 2.5rem)`.

### Phase 4 — Global styles

13. Update `src/styles.css` with an `@layer components` block
    that:
    - Tightens `h1` / `h2` fluid type when `html.layout-*-medium`.
    - Hides the `<app-root>` decoration on the short bucket (the
      component templates own the actual hide rules, so the
      stylesheet only needs to tighten fluid type).

### Phase 5 — Validation

14. Run `tsc --noEmit -p tsconfig.app.json` until exit 0.
15. Run `ng build --configuration production --output-path
    /tmp/escalabirras-fe-prod` until green.
16. Run `pytest backend -v` (or the equivalent) to confirm no
    regression (the backend is not touched, so the count must
    stay the same).
17. Run `curl` smoke against `ng serve` for `/`,
    `/?embed_token=…`, `/login`, `/admin` (best-effort; the actual
    bucket assertion requires a browser).
18. Final consistency sweep:
    - No `TODO` in the new SDD files.
    - `git status frontend/src/` shows only the intended
      modifications.
    - `grep -nR "layout-compact\b\|layout-narrow\b\|layout-wide\b"
      frontend/src` returns no remaining references to the old
      width-only class names **outside** of the contract file
      (where the historical reference is intentional).

## Risks

- **Nine buckets is a lot.** Some combinations may be rare in
  practice (e.g. `layout-narrow-short`, `layout-compact-medium`).
  The CSS rules are intentionally defensive: the medium bucket
  inherits from the regular layout, and the short bucket is the
  only one that requires significant overrides.
- **`document.body` height** is sometimes reported as `0` by
  `ResizeObserver` when the body has no explicit height. The
  global stylesheet already sets `html, body { height: 100% }`,
  so the body should always equal the iframe content rect; we
  fall back to `window.innerHeight` if `body.clientHeight` is
  falsy, and finally to `768`.
- **First-paint flicker.** The service computes the initial
  bucket synchronously in the constructor, so the correct class
  is on `<html>` before Angular renders the first frame. No
  flash of wrong layout.
- **Bucket churn.** Resizing the iframe generates one or two
  observer callbacks per axis transition. `LayoutService`
  compares the new bucket against the current one before pushing,
  so identical buckets do not trigger an observable emission.
- **Reading `entry.contentRect.height` while the iframe is
  hidden.** Some browsers report `0` when the iframe is in a
  background tab. The fallback to `window.innerHeight` (when the
  page is visible) and the conservative `768` default keep the
  bucket meaningful even in degraded conditions.
- **`mt-0` collision.** Tailwind's `mt-0` is
  `margin-top: 0`. Replacing `mt-12` / `mt-48` / `mt-20` with
  `mt-0` is straightforward; the `md:`-suffixed variants become
  `md:mt-0` (a no-op that still wins specificity over `mt-0`).
