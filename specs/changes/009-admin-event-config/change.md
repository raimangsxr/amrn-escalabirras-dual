# 009 — Admin route and event configuration

## Status

Active. The single source of truth lives in
`specs/manifest.yml`.

## What this change delivers

- A new `event` table on the backend (singleton row, id=1) with
  `title`, `subtitle`, and `updated_at` columns.
- `GET /v1/event` and `PUT /v1/event` endpoints behind the
  existing Bearer auth.
- A new Angular `AdminComponent` hosted at `/admin`, behind the
  same `authGuard` as `/`. It contains three sections:
  event info editor, embed tokens management, and a logout
  button.
- A new Angular `EventService` that holds the event info as a
  stream and is fetched once on app startup.
- Removal of the Tokens and Salir buttons from the main
  tournament view; the page no longer contains any navigation
  to `/admin`.

## What this change does NOT do

- No new role / multi-operator model.
- No audit log of event edits.
- No real-time push (clients pick up the new event info on
  their next page load).
- No multi-event support (the table is a singleton).
