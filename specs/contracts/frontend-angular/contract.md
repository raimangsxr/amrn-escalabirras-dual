# frontend-angular Contract

## Purpose

Describe the Angular 22 frontend after the migration from
`localStorage` to the FastAPI backend introduced in change
`002-backend-foundation`, after the addition of operator login +
embed-token bypass introduced by change `004-auth-and-embed-tokens`,
after the framework-version bump to v20 introduced by change
`007-angular-20-migration`, after the framework-version bump to
v22 introduced by change `008-angular-22-migration`, after the
operator-only configuration (event info, tokens, logout) was
moved to the `/admin` route introduced by change
`009-admin-event-config`, and after the two-dimensional
(width × height) responsive layout scheme was introduced by
change `010-responsive-iframe-height`. The frontend lives under
`src/`. It is the primary consumer of
`specs/contracts/api-rest/contract.md`,
`specs/contracts/persistence-postgres/contract.md`, and
`specs/contracts/auth/contract.md`.

This contract supersedes the historical `specs/contracts/app-core/contract.md`,
which describes the `localStorage`-backed version and is moved to
`specs/archive/` at the close of change `003-migrate-storage`.

## Current Behavior

The frontend is a Spanish-language Angular 22 SPA that drives the
escalabirras tournament. On first load the app asks the operator
for the password configured at the backend (`ADMIN_PASSWORD`); once
authenticated it behaves as in `003`. If the app is embedded in an
iframe of another application, the parent can pass the operator's
embed token via `?embed_token=…`; the app exchanges it for a session
JWT automatically and the operator never sees the login screen.

Every mutation goes through the FastAPI backend at
`http://localhost:8000` (configurable via
`src/environments/environment.ts`). All requests except the auth
endpoints and `/healthz` carry `Authorization: Bearer <jwt>` set by
the HTTP interceptor.

The application is online-only against the backend. There is no
offline cache. The session JWT lives in `sessionStorage`, so closing
the tab ends the session.

## Reactive state model

Three services own frontend state. `AuthService` (under
`src/app/auth/auth.service.ts`) owns the operator session.
`AppService` (under `src/app/services/app.service.ts`) owns
tournament state. `EventService` (under
`src/app/services/event.service.ts`) owns the singleton event
info (title, subtitle) and is the only writer/reader of
`/v1/event`. All three expose RxJS streams backed by
`BehaviorSubject`s.

### `AuthService`

| Member | Type | Notes |
| --- | --- | --- |
| `session$` | `Observable<Session \| null>` | `null` when logged out. `Session = { token: string, expiresAt: Date }`. |
| `isAuthenticated$` | `Observable<boolean>` | Convenience derived from `session$`. |
| `bootstrap()` | `Promise<void>` | Reads `sessionStorage`; if absent, scans the URL for `?embed_token=…` and exchanges it. |
| `login(password)` | `Observable<Session>` | `POST /v1/auth/login`. |
| `logout()` | `void` | Clears `sessionStorage` and the `session$` subject. |
| `exchangeEmbedToken(token)` | `Observable<Session>` | `POST /v1/auth/embed-token`. |
| `getToken()` | `string \| null` | Synchronous accessor used by the HTTP interceptor. |

### `EventService`

Introduced by change `009-admin-event-config`. Owns the singleton
event info (`title`, `subtitle`) the operator configures from
`/admin` and that `MainViewComponent` renders in its header.
There is at most one row on the backend, so the service holds a
single `event$` stream rather than a collection.

| Member | Type | Notes |
| --- | --- | --- |
| `event$` | `Observable<Event \| null>` | `null` until the first `bootstrap()` resolves. `Event = { id: 1, title: string, subtitle: string, updated_at: string }`. |
| `bootstrap()` | `Promise<void>` | `GET /v1/event`. Called once at app startup. Sets `event$` to the response, or to `null` on `404`. Other errors propagate and are not retried automatically. |
| `update(title, subtitle)` | `Observable<Event>` | `PUT /v1/event` with the trimmed values. On 2xx, updates `event$` and returns the response. |

Sessions live in `sessionStorage` under the key
`escalabirras.session` so they are scoped to the tab. Closing the
tab ends the session. The iframe's `sessionStorage` is independent
of the parent's, so the iframe must be issued its own session via
the embed-token flow.

### `AppService`

| Stream | Type | Source |
| --- | --- | --- |
| `currentSlots$` | `Observable<[Participant \| null, Participant \| null]>` | Local-only state. `[0]` is the red slot, `[1]` is the blue slot. |
| `top3$` | `Observable<Participant[]>` | Refetched from `GET /v1/leaderboard/top?limit=3` after every `+1` and on bootstrap. |
| `history$` | `Observable<Participant[]>` | Refetched from `GET /v1/history?limit=10` after every `POST /v1/participants` and on bootstrap. |
| `celebrating$` | `Observable<Participant \| null>` | Set to the participant when an `+1` returns `is_new_record: true`. Cleared after the celebration window. |
| `error$` | `Observable<string \| null>` | Set to a human-readable message when any HTTP call fails. Cleared on next success. |

There are no plain mutable arrays or `Subject`s exposed directly.
Components subscribe via the `async` pipe in templates.

## Lifecycle and change detection

- `AuthService` and `AppService` are both `@Injectable({ providedIn:
  'root' })`, so they are singletons.
- On bootstrap, `AppComponent` calls `AuthService.bootstrap()`:
  1. Reads `sessionStorage['escalabirras.session']`. If present,
     restores it and sets `session$` accordingly.
  2. Else, scans `window.location.search` for `embed_token=…`. If
     found, calls `AuthService.exchangeEmbedToken(...)`, stores the
     result, and removes the query parameter via
     `history.replaceState`.
  3. Else, leaves `session$` as `null`; the router redirects to
     `/login`.
- Components do **not** call service methods on every change-detection
  pass. They consume observables via `async` and rely on Angular's
  `OnPush` change detection where applicable.
- The keyboard shortcuts (`a`, `z`, `s`, `x`, `q`, `w`) remain bound
  to the central `<button #fin>` element. They continue to call into
  `AppService`, which now performs the HTTP round-trip.
- An HTTP interceptor adds `Authorization: Bearer <token>` from
  `AuthService.getToken()` to every outgoing request. On a `401`
  response, `AuthService.logout()` is called and the router redirects
  to `/login`.

## Data model

The frontend mirrors the backend's `Participant`:

```ts
interface Participant {
  id: number;       // server-assigned
  name: string;     // 1-20 chars
  crates: number;   // non-negative integer
  created_at: string; // ISO 8601 UTC, e.g. "2026-06-27T12:34:56.789Z"
}
```

The empty-slot sentinel `id: 0, name: '- - -', crates: 0` no longer
exists in storage. The frontend uses `Participant | null` per slot
instead; the team input shows `'- - -'` when the slot is `null`.

## User Flows

1. **App load (operator at `/login`).**
   - `AuthService.bootstrap()` finds no session and no
     `embed_token`. The router stays on `/login`.
   - `LoginComponent` shows a password input and a "Entrar" button.
   - On submit, `AuthService.login(password)` calls
     `POST /v1/auth/login`. On 200 the JWT is stored in
     `sessionStorage` and `session$` is set; the router navigates to
     `/`. On 401 the form shows "Contraseña incorrecta".

2. **App load (iframe with `?embed_token=…`).**
   - `AuthService.bootstrap()` finds no session, finds
     `embed_token=xxx` in the URL, calls
     `AuthService.exchangeEmbedToken(xxx)`. On 200 the JWT is stored
     and `session$` is set; `history.replaceState` removes the
     `embed_token` query parameter. The router navigates directly to
     `/`. The operator never sees the login screen.
   - On 401 the embed token is unknown or revoked; the operator is
     shown the login screen with a "Token no válido" hint and the
     URL is still cleaned up.

3. **App load (already logged in).** `AuthService.bootstrap()`
   finds a valid JWT in `sessionStorage`; the router navigates
   directly to `/`. The HTTP interceptor includes the JWT on every
   subsequent request.

4. **Register a participant on a team.** (unchanged from `003`)
   - Operator types a name (1–20 chars, enforced by the HTML
     `maxlength` and the backend) in the red or blue team input
     field and presses Enter.
   - `AppService.createParticipant(name)` issues
     `POST /v1/participants` with `{name}`. On success it sets
     `currentSlots$[team] = participant` and refetches `history$`
     and `top3$`.
   - The slot is locked while occupied; a second Enter is a no-op.

5. **Score crates live.** Keyboard shortcuts call
   `AppService.addCrate(team)` / `removeCrate(team)`. Each call
   issues `POST /v1/participants/{id}/crates/increment` (or
   `decrement`):
   - On `200`, the response's `participant` is stored as the new
     slot state. `top3$` is refetched.
   - If `is_new_record` is `true`, `celebrating$` is set to that
     participant and a 12-second `setTimeout` is scheduled to clear
     it. If another record arrives during an ongoing celebration, the
     previous timer is cleared and a fresh 12-second window starts
     with the new participant.
   - On `401` the interceptor clears the session and the router
     redirects to `/login`.
   - On `404` or `409` the HTTP error handler in `AppService` sets
     `error$` with the backend's `detail`; the slot state is not
     mutated.

6. **Clear a slot.** Pressing `q` or `w` sets
   `currentSlots$[team] = null`. There is no HTTP call; the
   participant row remains in the database and in the history list.

7. **Display top 3 and history.** Both lists are bound to `top3$` and
   `history$` respectively via the `async` pipe. They update
   automatically after each mutation.

8. **Celebration overlay.** While `celebrating$` is non-null, the
   `<app-root>` template hides the main UI and renders
   `<app-winner [participant]="(celebrating$ | async)">`.
   `WinnerComponent` renders the participant's name and crate count
   plus a `js-confetti` animation. The confetti still runs for
   `confettiTime` (10 s) with `confettiInterval` (2 s) bursts.

9. **Error banner.** While `error$` is non-null, a small banner
   appears at the top of the screen with the message and a "Dismiss"
   button. Dismissing sets `error$` back to `null`. Successful HTTP
   calls also clear `error$`.

10. **Manage embed tokens.** Introduced by change
    `009-admin-event-config`. The `TokensComponent` is hosted
    inside `AdminComponent` at `/admin`, not inside
    `MainViewComponent`. The operator navigates to `/admin`
    directly (bookmark, separate tab, manual URL); there is no
    button or link from `/` to `/admin`. From `/admin` the same
    UI is available: list of embed tokens (id, name, created_at,
    last_used_at, revoked_at), a "Crear token" input that asks
    for a name, an "Revocar" button per row, and the same
    copy-once UX for the plaintext token.

11. **Edit event info.** From `/admin`, the "Info del evento"
    section shows two text inputs (title, subtitle) bound to
    `EventService.event$`. "Guardar" calls
    `EventService.update(title, subtitle)` which `PUT /v1/event`s
    the trimmed values. On success the inputs keep the new
    values and a transient confirmation appears. On `422
    invalid_event` the inputs are not changed and the error
    banner surfaces the message.

12. **Log out.** From `/admin`, click "Salir" →
    `AuthService.logout()`. `sessionStorage` is cleared, `session$`
    is set to `null`, the router navigates to `/login`. The backend
    `/v1/auth/logout` is called as a courtesy but is a no-op server-
    side. The main view at `/` does **not** expose a Salir button;
    logging out requires visiting `/admin` (or waiting for the JWT
    to expire / closing the tab).

## APIs / Interfaces

### npm scripts (`package.json`)

| Script | Command | Notes |
| --- | --- | --- |
| `npm start` | `ng serve` | Local dev server on `http://localhost:4200`. |
| `npm run build` | `ng build` | Production build (Angular 22 budgets apply). |
| `npm run watch` | `ng build --watch --configuration development` | Rebuild on change, dev mode. |
| `npm test` | `ng test` | Karma + Jasmine. No specs added in `003`. |

### Public service surface (`AppService`)

| Member | Type | Notes |
| --- | --- | --- |
| `currentSlots$` | `Observable<[Participant \| null, Participant \| null]>` | `[0]` red, `[1]` blue. |
| `top3$` | `Observable<Participant[]>` | Backend Top 3. |
| `history$` | `Observable<Participant[]>` | Backend history (last 10). |
| `celebrating$` | `Observable<Participant \| null>` | Active celebration. |
| `error$` | `Observable<string \| null>` | Active error message. |
| `createParticipant(name: string, team: 0 \| 1)` | `void` | `POST /v1/participants`. |
| `addCrate(team: 0 \| 1)` | `void` | `POST .../crates/increment`. |
| `removeCrate(team: 0 \| 1)` | `void` | `POST .../crates/decrement`. |
| `clearSlot(team: 0 \| 1)` | `void` | Local-only. |
| `dismissError()` | `void` | Clears `error$`. |

### Public service surface (`AuthService`)

| Member | Type | Notes |
| --- | --- | --- |
| `session$` | `Observable<Session \| null>` | Current session or `null`. |
| `isAuthenticated$` | `Observable<boolean>` | Convenience. |
| `bootstrap()` | `Promise<void>` | Restores session from `sessionStorage` or exchanges an embed token from the URL. |
| `login(password: string)` | `Observable<Session>` | `POST /v1/auth/login`. |
| `logout()` | `void` | Local + courtesy `POST /v1/auth/logout`. |
| `exchangeEmbedToken(token: string)` | `Observable<Session>` | `POST /v1/auth/embed-token`. |
| `getToken()` | `string \| null` | Synchronous accessor used by the HTTP interceptor. |

### Public service surface (`EventService`)

| Member | Type | Notes |
| --- | --- | --- |
| `event$` | `Observable<Event \| null>` | `null` until first `bootstrap()` resolves. |
| `bootstrap()` | `Promise<void>` | `GET /v1/event`. |
| `update(title: string, subtitle: string)` | `Observable<Event>` | `PUT /v1/event`; updates `event$` on success. |

### Routing

`AppRoutingModule` defines:

```ts
const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: '', component: MainViewComponent, canActivate: [authGuard] },
  { path: 'admin', component: AdminComponent, canActivate: [authGuard] },
  { path: '**', redirectTo: '' },
];
```

`authGuard` is a `CanActivateFn` that returns `true` when
`AuthService.isAuthenticated$` is `true`, otherwise redirects to
`/login`.

The `/admin` route was introduced by `009-admin-event-config`.
It uses the same `authGuard` as `/`; there is no separate "admin
guard" and there is no role distinction (a single operator is
the only authenticated principal in v1). The `MainViewComponent`
template at `/` contains **no** navigation affordance to
`/admin` — no `routerLink`, no button, no anchor. The operator
reaches `/admin` by typing the URL in the address bar or by
using a bookmark.

The legacy `finishGame`, `addParticipantToGame`, `saveParticipant`,
`saveWinnerParticipant`, `setNewRecord`, `getNewRecord`,
`getParticipants`, `getWinnerParticipants` are **removed** in
`003-migrate-storage`. Components consume observables instead.

### Configuration

- `src/environments/environment.ts` exports
  `{ apiBaseUrl: 'http://localhost:8000/v1' }`.
- `src/environments/environment.prod.ts` is produced by Angular
  CLI's `fileReplacements` at build time. In `angular.json` the
  production build swaps `environment.ts` for
  `environment.prod.ts`. Production builds must override
  `apiBaseUrl` in `environment.prod.ts` to the public origin of the
  FastAPI backend (e.g. `https://api.example.com/v1`).
- The `apiBaseUrl` is read by `AppService` at construction time and
  passed to every `HttpClient` call.
- The Material theme is the prebuilt
  `@angular/material/prebuilt-themes/indigo-pink.css`, imported via
  `angular.json`'s `styles` array. Material 22 still ships the file
  but logs a deprecation; a future change can migrate to the M3
  `mat.theme` mixin. The framework version is Angular 22, built
  through `@angular/build:application`.

### HTTP error mapping

The `AppService` central HTTP error handler maps non-2xx responses to
`error$`:

| HTTP | `code` from backend | Surfaced message |
| --- | --- | --- |
| `404` | `participant_not_found` | `Participante no encontrado` |
| `409` | `crates_underflow` | `No se puede bajar de 0 cajas` |
| `422` | `invalid_name` | `Nombre inválido (1-20 caracteres)` |
| `422` | `validation_error` | `Solicitud inválida` |
| `0` (network) | — | `No se pudo contactar con el servidor` |
| other | — | `Error inesperado` |

On success after an error, `error$` is cleared.

### Keyboard contract

Unchanged from `app-core`:

| Key | Effect |
| --- | --- |
| `a` | `addCrate(0)` |
| `z` | `removeCrate(0)` |
| `s` | `addCrate(1)` |
| `x` | `removeCrate(1)` |
| `q` | `clearSlot(0)` |
| `w` | `clearSlot(1)` |

The shortcuts only fire when the central `<button #fin>` element
has keyboard focus. There is still no visual cue for that focus.

## Permissions and Access

- One operator account. The password is configured at the backend
  via `ADMIN_PASSWORD`; the frontend never sees it directly.
- Embed tokens are issued by the operator and grant the same access
  as a logged-in operator. They are scoped per-token (one
  credential = one bypass) but not per-endpoint (full access in v1).
- All data is shared across all clients connected to the backend.
- The session JWT lives in `sessionStorage`. Closing the tab ends
  the session. There is no automatic refresh: a 24 h JWT lasts
  until expiry or until the operator clicks "Salir".

## Error Handling

- HTTP errors from the backend are mapped to `error$` (see table
  above). The slot state is never updated on failure: the operator
  sees the last-known state.
- Network failures (status 0) are surfaced the same way. There is no
  automatic retry.
- Malformed JSON in any backend response is logged to `console.error`
  and surfaces as `Error inesperado` on `error$`.
- The celebration timer is cancelled when a new `is_new_record`
  arrives during an ongoing celebration. The previous participant's
  overlay is replaced by the new one.

## Non-functional characteristics

- **Browser support.** Same Angular 22 default as `app-core`. The
  app now also requires `fetch` / `XMLHttpRequest` to reach the
  backend; the dev assumption is `localhost`.
- **Performance.** Top 3 and history re-fetch from the backend after
  each mutation. Latency is dominated by the HTTP round-trip; on
  `localhost` it is in the single-digit milliseconds.
- **Accessibility.** Still no ARIA roles, no `aria-live` regions, no
  focus management. The error banner is a `<div>` with `role="alert"`
  added in `003`.
- **Internationalization.** Still hardcoded Spanish in templates.
- **No telemetry.** No analytics, no error reporting.

## Responsive / iframe sizing

Introduced by change `005-responsive-iframe`. The two-dimensional
(width × height) bucket scheme introduced by change
`010-responsive-iframe-height` supersedes the width-only scheme
from `005`. The service still observes the iframe size via a
`ResizeObserver` on `document.body` and applies the resulting
class to `<html>`. The set of emitted classes is now the cartesian
product of width and height buckets, not a single axis.

The application must look correct and remain fully usable when
embedded in an iframe at any reasonable aspect ratio (portrait,
landscape, square, very small widgets, full-screen takeover),
including both axes at once.

### Layout service

`src/app/services/layout.service.ts` exposes a single
`layoutClass$: Observable<string>` that emits one of nine
combined buckets:

| Class | Width | Height | Typical use |
| --- | --- | --- | --- |
| `layout-compact-short` | `< 480px` | `< 384px` | Tiny sidebar widget. |
| `layout-compact-medium` | `< 480px` | `384–575px` | Cramped phone-portrait. |
| `layout-compact-tall` | `< 480px` | `>= 576px` | Phone-portrait, narrow. |
| `layout-narrow-short` | `480–767px` | `< 384px` | Landscape widget. |
| `layout-narrow-medium` | `480–767px` | `384–575px` | Tablet-portrait, small. |
| `layout-narrow-tall` | `480–767px` | `>= 576px` | Tablet-portrait, comfortable. |
| `layout-wide-short` | `>= 768px` | `< 384px` | Landscape projector strip. |
| `layout-wide-medium` | `>= 768px` | `384–575px` | Landscape small desktop. |
| `layout-wide-tall` | `>= 768px` | `>= 576px` | Full-screen, default. |

Width thresholds (`480`, `768`) match the v1 layout (introduced by
`005-responsive-iframe`). Height thresholds (`384`, `576`) are
intentionally lower because the deployed iframes are often shorter
than they are wide; the chosen values keep the three buckets
balanced for the embedding scenarios documented in `004`.

`document.documentElement` always carries exactly one of these
nine classes and the value is mirrored to
`document.documentElement.dataset.layout` for tests / debugging.
The class is also exposed through `layoutClass$` so Angular
components can subscribe if needed.

### Fluid type

All large headlines and counters use Tailwind arbitrary `clamp()`
values so they scale with the iframe width while staying legible:

- Headlines (`h1`, `h2`): `clamp(1.5rem, 4vw, 4rem)`.
- Counters (`X cajas!`): `clamp(2rem, 6vw, 6rem)`.
- Celebration text: `clamp(2.25rem, 7vw, 7rem)`.

### Layout shifts

The height dimension adds two extra rules on top of the width
buckets introduced by `005`:

- In any `*-short` bucket (`< 384px` tall), the header collapses
  to a single line (logo hidden, title and subtitle only, smaller
  fluid type), the Top 3 list is hidden so the team panels can
  occupy the vertical space, and the celebration overlay shrinks
  every line of text and removes its vertical margins.
- In any `*-tall` bucket (`>= 576px` tall), the regular layout
  described below is restored.
- The `*-medium` bucket is the intermediate band; it inherits the
  regular layout, with slightly tighter fluid-type clamps so the
  content fits.

| Component | `*-tall` (`>= 576px` tall) | `*-short` (`< 384px` tall) |
| --- | --- | --- |
| Header (logo + title) | Logo + title side-by-side (or stacked on `*-compact`) | Logo hidden, title + subtitle only |
| Top 3 list | Visible | Hidden |
| Manager columns | `flex-row` on `*-wide`/`*-narrow`; `flex-col` on `*-compact` | `flex-col` with reduced padding |
| Team panel name + counter | Fluid type per the v1 scale | Smaller fluid type |
| Celebration overlay | `h-full`, fluid text, normal margins | `h-full`, fluid text, no `mt-*` |
| Login form | `w-full max-w-sm mx-4` (or `w-96` on `*-wide-tall`) | `w-full max-w-sm mx-2` |
| Tokens modal | `max-w-2xl`, `max-h-[90%]` | `max-w-full`, `max-h-full` |

The width shifts inherited from `005` (header stacking on
`*-compact`, manager columns stacking on `*-compact`, login form
full-width on `*-compact`/`*-narrow`) continue to apply on top of
the height shifts above.

### What the operator MUST be able to do in any size

In `/` (the public tournament view):

- Read the current participant name and crate count for each team.
- See the Top 3.
- See the last 10 participants.
- Click the "Focus para jugar" button (always visible; not hidden
  on small sizes).
- Press the keyboard shortcuts (`a/z/s/x/q/w`).
- See the celebration overlay without text overflow.

In `/admin` (operator only, separate route):

- Read and edit the event title and subtitle; the inputs must
  remain usable at every layout bucket.
- Manage embed tokens (list / create / revoke) with the same
  controls the modal used to have.
- Log out.

The Tokens modal and the Salir button are no longer rendered by
`MainViewComponent`; both moved to `/admin`.

### Manual test

```html
<!-- Wide x Short (landscape widget) — layout-wide-short -->
<iframe src="https://app.example.com/?embed_token=..." width="800" height="200"></iframe>
<!-- Compact x Tall (phone-portrait) — layout-compact-tall -->
<iframe src="https://app.example.com/?embed_token=..." width="320" height="640"></iframe>
<!-- Compact x Short (tiny sidebar) — layout-compact-short -->
<iframe src="https://app.example.com/?embed_token=..." width="300" height="200"></iframe>
<!-- Narrow x Tall (tablet-portrait) — layout-narrow-tall -->
<iframe src="https://app.example.com/?embed_token=..." width="600" height="900"></iframe>
<!-- Narrow x Medium (small embed) — layout-narrow-medium -->
<iframe src="https://app.example.com/?embed_token=..." width="600" height="450"></iframe>
<!-- Wide x Tall (default full-screen) — layout-wide-tall -->
<iframe src="https://app.example.com/?embed_token=..." width="1920" height="1080"></iframe>
<!-- Wide x Medium (landscape small) — layout-wide-medium -->
<iframe src="https://app.example.com/?embed_token=..." width="1024" height="500"></iframe>
<!-- Narrow x Short (rare, narrow landscape) — layout-narrow-short -->
<iframe src="https://app.example.com/?embed_token=..." width="700" height="200"></iframe>
<!-- Compact x Medium (rare, cramped square) — layout-compact-medium -->
<iframe src="https://app.example.com/?embed_token=..." width="420" height="420"></iframe>
```

Each iframe must render the operator's actions without overflow
or unreadable text, and `document.documentElement.dataset.layout`
must equal the expected bucket from the table above.

## Validation

- **No frontend unit tests.** `003` does not add Karma specs;
  end-to-end behavior is verified manually against the running
  backend.
- **`tsc --noEmit` is now green.** `esModuleInterop: true` is added
  to `tsconfig.json`'s `compilerOptions` so the standalone `tsc`
  typecheck accepts the `js-confetti` default import. The
  previously-documented `TS1259` should no longer appear.
- **Angular build succeeds.** Both `ng build --configuration
  development` and `--configuration production` produce a bundle
  through the `@angular/build:application` builder. The hardcoded
  WSL `outputPath` is still in `angular.json`; use
  `--output-path /tmp/...` to override.
- **End-to-end smoke.** With the backend running (SQLite is fine for
  a quick check) and `npm start` on the frontend, the operator can:
  1. Type "Ana" in the red input, press Enter. The slot shows "Ana"
     and "0 cajas!" and the history list shows "Ana" as the most
     recent.
  2. Click "Focus para jugar", press `a` three times. The slot shows
     "3 cajas!" and the Top 3 list contains "Ana" in first place.
  3. Press `q`. The red slot resets to `- - -` but "Ana" remains in
     the history and Top 3.
  4. Type "Bea" in the blue input, press Enter, click "Focus para
     jugar", press `s` once. The blue slot shows "1 caja!". The
     celebration does **not** fire because "1 < 3".