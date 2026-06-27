# Spec: 002-backend-foundation

## Problem

The frontend currently persists everything in `localStorage`. That
worked for a single-browser, single-operator prototype, but it makes
the data non-shareable, brittle (Safari private mode, malformed JSON),
and unable to scale beyond one device. The team needs a real backend
so multiple devices can see the same state, and so the data survives
browser refreshes, profile switches, or device swaps.

This change introduces the backend itself. It does not change the
frontend yet: `src/` continues to use `localStorage` exactly as
documented in `specs/contracts/app-core/contract.md`. A separate
change (`003-migrate-storage`) will rewire the frontend to the new
API; that change is out of scope here.

## Goals

- Introduce a FastAPI backend under `backend/` that exposes the
  REST contract in `specs/contracts/api-rest/contract.md`.
- Persist participants in PostgreSQL using the schema in
  `specs/contracts/persistence-postgres/contract.md`.
- Provide Alembic migrations, including the initial
  `0001_create_participants` migration.
- Provide a `docker-compose.yml` that boots a `postgres:16` service
  (and optionally Adminer) for local development.
- Provide a `backend/README.md` that explains how to bring the
  service up locally (Docker + uvicorn, or pure Postgres + uvicorn).
- Provide a `pytest` test suite that exercises the API end-to-end
  using `httpx.AsyncClient` against an in-memory SQLite database
  so tests are Docker-free.
- Keep `app-core` unchanged and still marked active until
  `003-migrate-storage` closes.

## Non-Goals

- **No changes under `src/`.** The frontend is untouched in this
  change.
- No authentication, no multi-user, no rate limiting.
- No multi-event / tournament abstraction. One flat
  `participants` table.
- No real-time push (no SSE / WebSocket).
- No production deployment configuration (no Dockerfile for the
  API itself in this change; only `docker-compose.yml` for the
  Postgres dev service).
- No migration of existing `localStorage` data. The decision to
  discard was taken in the planning pass.

## Requirements

### Functional

- **R1.** `POST /v1/participants` accepts `{name}` and returns
  `201` + `Participant` (with `crates: 0`). Names are trimmed and
  must be 1–20 characters after trimming.
- **R2.** `GET /v1/participants/{id}` returns `200` + `Participant`
  or `404` + `{code: "participant_not_found"}`.
- **R3.** `POST /v1/participants/{id}/crates/increment` atomically
  increments `crates` by 1 and returns
  `{participant, is_new_record}`. `is_new_record` is `true` iff the
  post-increment `crates` is strictly greater than every other
  participant's `crates` (or the participant is the first one and
  reaches `crates >= 1`).
- **R4.** `POST /v1/participants/{id}/crates/decrement` atomically
  decrements `crates` by 1, returning `{participant, is_new_record:
  false}`. If `crates == 0`, the response is `409` +
  `{code: "crates_underflow"}` and the row is unchanged.
- **R5.** `GET /v1/leaderboard/top?limit=3` returns up to `limit`
  participants ordered by `crates DESC, created_at ASC`. Limit is
  clamped to `[1, 100]`; default is `3`.
- **R6.** `GET /v1/history?limit=10&offset=0` returns up to `limit`
  participants ordered by `created_at DESC, id DESC`. Limit clamped
  to `[1, 100]`; offset is `>= 0`.
- **R7.** `GET /healthz` returns `200` + `{status: "ok"}`.
- **R8.** Every non-2xx response body matches
  `{detail: string, code: string}`.
- **R9.** CORS allows `http://localhost:4200` by default and any
  origin listed in the `CORS_ORIGINS` environment variable.

### Non-functional

- **R10.** `pytest` runs without Docker. The test suite uses SQLite
  in-memory, and the production schema is documented in the
  persistence contract. SQLAlchemy-level guards ensure the API
  behaves identically for the tests' purposes.
- **R11.** `docker-compose up db` boots a `postgres:16` service on
  `localhost:5432`. The repo includes a `.env.example` documenting
  the expected `DATABASE_URL`.
- **R12.** `alembic upgrade head` applies cleanly against a fresh
  Postgres database and creates the `participants` table and
  indexes.
- **R13.** All Python dependencies are pinned in
  `backend/pyproject.toml` so a clean install produces a working
  environment.
- **R14.** `backend/README.md` documents the two supported flows:
  Docker + uvicorn, and bare Postgres + uvicorn.

### Structural (SDD)

- **R15.** `specs/manifest.yml` lists `api-rest` and
  `persistence-postgres` as active contracts and `002-backend-foundation`
  as the active change.
- **R16.** `specs/contracts/api-rest/contract.md` and
  `specs/contracts/persistence-postgres/contract.md` are fully
  populated with no `TODO` markers in the populated sections.
- **R17.** `app-core` remains unchanged. Its manifest entry has a
  note that it is "historical" until `003` closes.
- **R18.** No files under `src/` are modified.

## Acceptance Criteria

- **AC1.** From a fresh checkout with `python3 -m venv .venv` and
  `pip install -e backend[dev]`, running `pytest backend` exits 0
  with the full test suite green.
- **AC2.** Tests cover at least: create participant, get one,
  increment (including first-run `is_new_record: true` and a
  subsequent non-record increment), decrement (including
  `crates_underflow` at zero), leaderboard ordering and tie-break,
  history pagination, validation errors, and 404s.
- **AC3.** `uvicorn app.main:app --reload` (from `backend/` with
  `DATABASE_URL=sqlite:///./dev.db` and a one-time
  `alembic upgrade head`) starts the service, and `curl
  http://localhost:8000/healthz` returns `{"status":"ok"}`. This
  proves the SQLAlchemy + Alembic wiring even without Docker.
- **AC4.** `docker-compose config` validates the compose file
  (does not require Docker to be running).
- **AC5.** The FastAPI service exposes `/docs` (Swagger UI) with the
  full `/v1` route set.
- **AC6.** `git status` shows no modifications under `src/`.