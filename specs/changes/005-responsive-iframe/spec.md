# Spec: 005-responsive-iframe

## Problem

The Angular frontend was designed for a single desktop-sized
viewport. Every screen has fixed font sizes (`text-9xl`,
`text-6xl`, `w-72`) and a fixed three-column layout. When the app
is embedded in an iframe of a different parent application — which
is the primary use case introduced by `004-auth-and-embed-tokens` —
the layout breaks:

- The celebration overlay uses `h-screen` (= 100vh) and text up to
  `text-9xl`; in a 320×200 iframe the text overflows horizontally
  and the background flips against a 200 px tall "screen".
- The three-column manager layout collapses below ~700 px wide;
  team panels become unreadable.
- The header (`text-6xl` + a 288 px logo) does not fit in a phone-
  sized iframe.
- The login form (`w-96`) is wider than the iframe on small embeds.

This change makes the application responsive so the operator can
use it inside any reasonable iframe, regardless of size.

## Goals

- Introduce a `LayoutService` that observes the document body and
  exposes the current iframe size bucket (`compact` / `narrow` /
  `wide`) as both a CSS class on `<html>` and an observable.
- Replace fixed font sizes in the celebration overlay, the team
  panels, the Top 3, the participant list, and the header with
  Tailwind arbitrary `clamp()` values that scale with viewport
  width.
- Stack the manager columns on narrow widths so the team panels
  remain legible in phone-sized embeds.
- Make the login form fill the iframe width when the iframe is
  narrower than its 384 px card.
- Make the celebration overlay use `h-full` (parent height) instead
  of `h-screen` (viewport height), so it fills the iframe.
- Make the Tokens modal adapt to small iframes.
- Update `frontend-angular` contract to document the responsive
  behavior and the manual test.
- Keep all 58 backend tests and the existing acceptance criteria
  for `004` green.

## Non-Goals

- No redesign of the visual language. Same colors, same copy, same
  icons.
- No new components. Existing components are refactored only.
- No backend changes.
- No new dependencies. `clamp()` and `ResizeObserver` are
  universally available in the supported browser set.
- No telemetry of viewport size.
- No server-side rendering; this is purely a CSS + Angular
  refactor.

## Requirements

### Functional

- **R1.** `src/app/services/layout.service.ts` is a root-provided
  service with:
  - `layoutClass$: Observable<'layout-compact' | 'layout-narrow' | 'layout-wide'>`
  - The class boundaries: `< 480` → `compact`; `480–767` →
    `narrow`; `>= 768` → `wide`.
  - A `ResizeObserver` on `document.body` that updates the class
    on `<html>` and pushes the value on the observable.
- **R2.** `AppComponent` injects `LayoutService` and starts the
  observer on init.
- **R3.** `html`, `body`, and `<app-root>` are full-height
  flex containers in the global stylesheet so a `h-full` child fills
  the iframe, not the viewport.
- **R4.** Every large text in templates uses a Tailwind arbitrary
  `clamp()` value (or one of the documented semantic scale buckets).
- **R5.** `MainViewComponent` stacks its header and its
  top3 + manager section on narrow widths.
- **R6.** `ManagerComponent` stacks its three columns (history +
  red + blue) on narrow widths and uses horizontal layout on wide.
- **R7.** `TeamManagerRedComponent` and `TeamManagerBlueComponent`
  scale their title, name and counter fonts with the iframe width.
- **R8.** `WinnerComponent` uses `h-full` instead of `h-screen` and
  scales its text with the iframe width.
- **R9.** `LoginComponent` uses `w-full max-w-sm mx-4` instead of
  `w-96` so the form fills the iframe on narrow widths.
- **R10.** `TokensComponent` modal uses `max-w-full` and
  `max-h-full` on narrow widths.
- **R11.** The "Focus para jugar" button remains visible at every
  size; keyboard shortcuts (`a/z/s/x/q/w`) continue to work.

### Non-functional

- **R12.** `tsc --noEmit -p tsconfig.app.json` exits 0.
- **R13.** `ng build --configuration production --output-path
  /tmp/...` succeeds.
- **R14.** No regressions in any of the existing 58 backend tests.
- **R15.** No regressions in the existing 24-step backend E2E
  smoke.

### SDD / contract

- **R16.** `specs/contracts/frontend-angular/contract.md` includes a
  new "Responsive / iframe sizing" section documenting the
  `LayoutService`, the size buckets, the fluid-type scale, and the
  layout shifts table.
- **R17.** `specs/manifest.yml` reflects `005-responsive-iframe` as
  the active change.

## Acceptance Criteria

- **AC1.** `tsc --noEmit -p tsconfig.app.json` exits 0.
- **AC2.** `ng build --configuration production --output-path
  /tmp/escalabirras-fe-prod` succeeds.
- **AC3.** `pytest backend -v` reports 58/58 passing (no
  regression).
- **AC4.** The bundle includes the new `LayoutService` and the
  rewritten templates.
- **AC5.** The frontend-angular contract has no `TODO` in the new
  "Responsive / iframe sizing" section.
- **AC6.** Manual iframe test passes (covered by the contract's
  manual test block): rendering the production build in iframes at
  `300×200`, `768×1024`, and `1920×1080` shows the operator's
  actions (scoring, top 3, celebration, tokens modal, logout)
  without overflow or unreadable text.
- **AC7.** `specs/manifest.yml` lists `005-responsive-iframe` as
  the active change.