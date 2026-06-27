# Context Pack: 005-responsive-iframe

## Goal

Make the Angular frontend responsive so it adapts to the shape of
the iframe it is embedded in. The previous contracts assume a
desktop-sized viewport; the actual deployment (introduced by
`004-auth-and-embed-tokens`) embeds the app inside iframes of
unrelated origins, at sizes we do not control.

## Relevant Contracts

- `specs/contracts/frontend-angular/contract.md` (live; updated to
  add the "Responsive / iframe sizing" section).

## Current Understanding

- The Angular SPA currently uses fixed font sizes
  (`text-9xl`, `text-6xl`), fixed widths (`w-72` for the logo,
  `w-96` for the login form), and a three-column layout that
  collapses below ~700 px.
- The celebration overlay uses `h-screen` (= 100vh) which fills
  the viewport. In an iframe, the viewport IS the iframe, so this
  is technically correct, but the text at `text-9xl` overflows on
  short iframes.
- Tailwind 3 supports arbitrary values with `clamp()` via
  `text-[clamp(...)]` etc., no plugin required.
- `ResizeObserver` is universally available in the Angular 16
  browser set; no polyfill needed.
- No tests cover the visual layout. The 58 backend tests are
  unchanged.

## Files / Areas Likely Involved

### New

- `src/app/services/layout.service.ts` — `BehaviorSubject` of the
  size bucket, `ResizeObserver` on `document.body`, applies the
  class to `<html>`.

### Modified

- `src/styles.css` — global flex / overflow rules, prefers-reduced-
  motion block.
- `src/index.html` — drop conflicting body class.
- `src/app/app.component.ts` — instantiate `LayoutService` on init,
  stop on destroy.
- `src/app/main-view/main-view.component.html` — stack on narrow,
  fluid type.
- `src/app/manager/manager.component.html` — three columns → stack on
  narrow.
- `src/app/team-manager-red/team-manager-red.component.html` and
  blue — fluid type.
- `src/app/top3/top3.component.html` — fluid type.
- `src/app/participant-list/participant-list.component.html` —
  fluid type.
- `src/app/winner/winner.component.html` — `h-full`, fluid text.
- `src/app/login/login.component.html` — full-width on narrow.
- `src/app/tokens/tokens.component.html` — full-width on narrow.

### Untouched

- All `*.component.ts` files. The responsive refactor only
  touches templates; the TypeScript classes keep their public
  surface intact.
- All backend code, migrations, tests.
- All SDD files other than `frontend-angular/contract.md` and this
  change's files.

## Constraints

- **Angular 16 + Tailwind 3.3.** No new dependencies.
- **Strict TypeScript** stays green.
- **No new tests**; the manual iframe test from the contract
  suffices for v1.
- **`overflow: hidden` on body** to keep the iframe chrome tidy.
- **`min-h-0`** on flex children that must shrink below their
  content size.
- **Fluid type via `clamp()`** rather than a JS-driven font scale,
  to keep the change minimal.
- **Tailwind responsive variants** (`sm:`, `md:`, `lg:`, `xl:`)
  for layout shifts. These key off the viewport (= iframe) width
  in iframes, so they work correctly.

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

   Expectation: bundle produced.

3. **Backend regression** (broad).

   ```bash
   /tmp/venv-002/bin/pytest backend -v
   ```

   Expectation: 58/58 green.

4. **Dev-server smoke** (broad).

   ```bash
   node_modules/.bin/ng serve --host 127.0.0.1 --port 4200
   curl -s -o /dev/null -w "/                  HTTP %{http_code}\n" http://127.0.0.1:4200/
   curl -s -o /dev/null -w "/?embed_token=xxx  HTTP %{http_code}\n" "http://127.0.0.1:4200/?embed_token=embed_xxx"
   ```

   Expectation: both 200; the SPA boots and the URL with the embed
   token reaches the app (the actual exchange happens client-side
   after the JS bundle loads).

5. **Manual iframe test** (broad, browser required). Document the
   iframes in `frontend-angular/contract.md` under "Manual test".

6. **Final consistency sweep** (broad).

   ```bash
   grep -nR "TODO" specs/contracts/frontend-angular/contract.md specs/changes/005-responsive-iframe
   git status src/
   ```

   Expectation: no `TODO` outside backticks; only the intended
   changes under `src/`.

## Risks

- **`vh` vs `%`.** We deliberately use `vw` for type and `h-full`
  for layout containers. The combination scales fluidly on width
  and stays within the iframe height.
- **`ResizeObserver` on hidden iframe.** Initial value emitted on
  construction; subsequent updates fire as expected. If the parent
  hides the iframe before the observer is registered, the
  observer still receives the initial size on first paint.
- **Safari iOS body overflow.** Mitigated by `min-h-0` on flex
  children so overflow is contained inside the parent.
- **No visual regression tests.** Documented; the manual iframe
  test in the contract is the verification.
- **CSS arbitrary values are verbose.** Accepted in v1; a future
  change can introduce a Tailwind preset.
- **CLS on first paint.** The `LayoutService` emits the initial
  bucket synchronously, so the templates render with the correct
  classes on the first change-detection cycle. No flash of wrong
  layout.

## Recommendations (do not create in this change)

- **`responsive-tokens` contract** (not created): would own a
  token-based design system (e.g. spacing, color, type scale)
  that components consume. Today the fluid type is hardcoded per
  template via `clamp()`; a future change could centralize it.
- **`iframe-host` contract** (not created): would document the
  shape, sandbox flags, and postMessage contract between the
  parent and the escalabirras iframe. Today the only contract is
  the `?embed_token=` URL parameter.