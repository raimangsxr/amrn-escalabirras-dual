# Context Pack: 002-backend-foundation

## Goal

Introduce a FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL backend
under `backend/`, exposing the REST contract in
`specs/contracts/api-rest/contract.md` and the schema in
`specs/contracts/persistence-postgres/contract.md`. The frontend
(`src/`) is untouched in this change.

## Relevant Contracts

- `specs/contracts/api-rest/contract.md`
- `specs/contracts/persistence-postgres/contract.md`

(Also referenced but **not modified**: `specs/contracts/app-core/contract.md`
stays active as the historical description of the pre-Postgres
frontend.)

## Current Understanding

- Repo is a monorepo with the Angular SPA under `src/` and SDD
  scaffolding under `specs/`. There is no existing Python code.
- The local environment has Python 3.12, Docker, `docker-compose`,
  and `psql` (Postgres 18 client).
- `app-core` describes a `localStorage`-backed frontend. This change
  is the first step toward replacing that: the backend lands now,
  and `003-migrate-storage` will rewire the frontend.
- The team decided to discard any existing `localStorage` data, keep
  only the `Participant` model, drop the seed of 10 placeholders,
  ship no auth, and use REST + JSON over HTTP.

## Files / Areas Likely Involved

### New: backend/ (created in this change)

- `backend/pyproject.toml` — FastAPI 0.115, SQLAlchemy 2.0,
  Alembic 1.13, `psycopg[binary]`, pydantic v2, pydantic-settings,
  pytest, pytest-asyncio, httpx. All deps pinned to known-good
  versions.
- `backend/app/config.py` — `Settings(BaseSettings)` reading
  `DATABASE_URL` and `CORS_ORIGINS`.
- `backend/app/database.py` — `engine = create_engine(...)`,
  `SessionLocal`, `Base`, `get_db` generator dependency.
- `backend/app/models.py` — `Participant` SQLAlchemy 2.0 model with
  `Mapped[...]` annotations.
- `backend/app/schemas.py` — Pydantic v2 DTOs:
  `ParticipantCreate`, `ParticipantRead`,
  `CratesAdjustResponse`, `ErrorBody`, `HealthResponse`.
- `backend/app/crud.py` — `create_participant(session, name)`,
  `get_participant(session, id)`,
  `adjust_crates(session, id, delta)`,
  `list_top(session, limit)`, `list_history(session, limit,
  offset)`.
- `backend/app/services/records.py` —
  `compute_is_new_record(participant, previous_max)`.
- `backend/app/deps.py` — re-export of `get_db`.
- `backend/app/main.py` — FastAPI app, CORS middleware,
  exception handlers, routers mounted at `/v1`, `/healthz`,
  `/docs`, `/redoc`.
- `backend/app/routers/participants.py` — `POST /v1/participants`,
  `GET /v1/participants/{id}`, increment, decrement.
- `backend/app/routers/leaderboard.py` — `GET /v1/leaderboard/top`,
  `GET /v1/history`.
- `backend/alembic.ini` and `backend/alembic/env.py` —
  `target_metadata = Base.metadata`, reads `DATABASE_URL` from
  settings.
- `backend/alembic/versions/0001_create_participants.py` —
  hand-reviewed initial migration (table + CHECK + two indexes).
- `backend/tests/conftest.py` — per-test SQLite in-memory engine,
  `get_db` override, `AsyncClient`.
- `backend/tests/test_participants.py`,
  `test_crates.py`, `test_leaderboard.py`, `test_history.py`,
  `test_health.py`.

### New: repo root infra

- `docker-compose.yml` — `db` (`postgres:16`,
  `POSTGRES_USER=escalabirras`, `POSTGRES_PASSWORD=escalabirras`,
  `POSTGRES_DB=escalabirras`, port `5432:5432`, named volume) and
  optional `adminer` on `8080:8080`.
- `.env.example` — `DATABASE_URL` and `CORS_ORIGINS` with safe
  defaults.

### Updated

- `specs/manifest.yml` — adds `api-rest`, `persistence-postgres`,
  and `002-backend-foundation`. Keeps `app-core` and
  `001-current-behavior-baseline` active.

### Untouched (must remain so)

- `src/**` — the Angular frontend. `003-migrate-storage` will
  rewire it; not in this change.
- `specs/contracts/app-core/contract.md`,
  `specs/changes/001-current-behavior-baseline/**` — historical,
  still accurate for the frontend.

## Constraints

- **No changes under `src/`.** AGENTS.md rule 7 (update affected
  contract before implementation) does not apply yet because the
  frontend's contract is not changing in this change. The frontend
  contract changes in `003`.
- **No auth in v1.** The backend exposes open endpoints; the venue
  network is the trust boundary.
- **No multi-event / tournament scoping.** Participants are flat;
  one global leaderboard.
- **No real-time push.** The frontend polls (in `003`) if it needs
  live updates.
- **PostgreSQL 16+ only in production.** Tests use SQLite; the
  production-only constructs (`SELECT ... FOR UPDATE`,
  `TIMESTAMPTZ`, `CHECK`) are documented and reviewed by hand.
- **Single-event scope.** Each `app-core` event has no more than
  ~hundreds of participants; indexes and pagination are sized
  for that.
- **Dependencies are pinned.** No `^` ranges in `pyproject.toml`;
  exact versions or tight `~=` ranges only.

## Validation Plan

Run narrow checks first, then broader ones.

1. **Static + unit tests (narrow, no Docker).**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e backend[dev]
   pytest backend -v
   ```

   Expectation: full suite green, including the SQLite-vs-Postgres
   divergences documented in `persistence-postgres`.

2. **Compose file syntax (narrow, no Docker needed).**

   ```bash
   docker-compose config
   ```

   Expectation: exit 0 with the resolved YAML printed.

3. **Boot the FastAPI app against SQLite (narrow, end-to-end of the
   wiring).**

   ```bash
   cd backend
   DATABASE_URL=sqlite:///./dev.db alembic upgrade head
   DATABASE_URL=sqlite:///./dev.db uvicorn app.main:app --reload &
   curl http://localhost:8000/healthz
   curl -X POST http://localhost:8000/v1/participants \
       -H 'Content-Type: application/json' -d '{"name":"Ana"}'
   curl http://localhost:8000/v1/leaderboard/top?limit=3
   ```

   Expectation: `200 OK` from `/healthz`; `201` on create; `200` on
   leaderboard with one entry.

4. **Boot Postgres via Docker (broader).**

   ```bash
   docker compose up db -d
   DATABASE_URL=postgresql+psycopg://escalabirras:escalabirras@localhost:5432/escalabirras \
       alembic -c backend/alembic.ini upgrade head
   DATABASE_URL=postgresql+psycopg://escalabirras:escalabirras@localhost:5432/escalabirras \
       uvicorn app.main:app --reload --app-dir backend
   ```

   Expectation: Postgres is reachable, migration applies, API
   serves requests.

5. **CORS smoke (broader, manual).**

   ```bash
   curl -i -X OPTIONS http://localhost:8000/v1/participants \
       -H 'Origin: http://localhost:4200' \
       -H 'Access-Control-Request-Method: POST'
   ```

   Expectation: `Access-Control-Allow-Origin: http://localhost:4200`
   in the response.

6. **Final consistency sweep (broad).**

   ```bash
   git status src/
   # -> empty
   grep -nR "TODO" specs/contracts/api-rest specs/contracts/persistence-postgres specs/changes/002-backend-foundation
   # -> no matches
   ```

## Risks

- **SQLite vs Postgres divergence.** `crud.adjust_crates` uses
  `with_for_update()`, which is a no-op on SQLite but enforced on
  Postgres. The race-condition guarantee is therefore only
  exercised in production. Mitigation: documented; a future change
  can add Testcontainers integration tests.
- **Alembic autogenerate misses `CHECK` constraints.** Mitigation:
  the `0001` migration is hand-reviewed; the contract explicitly
  lists the CHECK.
- **Alembic and SQLAlchemy versions drifting apart.** Mitigation:
  both pinned in `pyproject.toml`.
- **CORS misconfiguration.** Mitigation: default to
  `http://localhost:4200`, document `CORS_ORIGINS` in
  `.env.example` and `backend/README.md`.
- **Local Postgres already running on 5432.** Mitigation:
  `docker-compose.yml` maps host 5432 to container 5432 only when
  the user explicitly runs `up`. Documentation warns about the
  conflict.
- **Time-zone drift in `created_at`.** Mitigation: SQLAlchemy
  stores as `TIMESTAMPTZ`, serialized as ISO 8601 UTC with `Z`.
  Documented in `persistence-postgres`.
- **`app-core` will be wrong after `003` lands.** Mitigation:
  `app-core`'s manifest entry is already labelled "historical —
  pre-Postgres"; `003` will move it to `archive/`.