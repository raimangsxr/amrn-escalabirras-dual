# Plan: 002-backend-foundation

## Approach

Add a `backend/` Python project at the repo root, parallel to
`src/`. Use the standard FastAPI + SQLAlchemy 2.0 + Alembic + psycopg3
stack. The dev DB is `postgres:16` via `docker-compose`, but the
test suite uses SQLite in-memory so `pytest` runs without Docker.
The `app-core` contract and the Angular frontend stay untouched in
this change; only `003-migrate-storage` will rewire the frontend.

The implementation is structured so each layer is independently
testable:

1. **Domain layer** (`models.py`, `schemas.py`): SQLAlchemy ORM and
   Pydantic DTOs. Pure data shapes.
2. **Data-access layer** (`crud.py`, `services/records.py`): atomic
   crate adjustments with `SELECT ... FOR UPDATE` and `MAX(crates)`
   on Postgres.
3. **Transport layer** (`routers/*.py`, `main.py`): FastAPI routes,
   CORS, error handlers.
4. **Migrations** (`alembic/`): `0001_create_participants.py`
   produced by autogenerate and reviewed.
5. **Dev infra** (`docker-compose.yml`, `.env.example`).
6. **Tests** (`tests/`): httpx.AsyncClient against the FastAPI app
   bound to a SQLite engine, with a `get_db` override.

## Steps

1. **Update `specs/manifest.yml`** to add the two new contracts and
   the new change, marking `app-core` as historical.
2. **Write `specs/contracts/api-rest/contract.md`** (R1–R9 mapping).
3. **Write `specs/contracts/persistence-postgres/contract.md`** with
   the schema, indexes, and migration workflow.
4. **Scaffold `backend/`**:
   - `backend/pyproject.toml` (deps pinned).
   - `backend/app/__init__.py`.
   - `backend/app/config.py` (pydantic-settings `Settings`).
   - `backend/app/database.py` (engine, `SessionLocal`, `Base`,
     `get_db` dependency).
   - `backend/app/models.py` (`Participant`).
   - `backend/app/schemas.py` (Pydantic `ParticipantRead`,
     `ParticipantCreate`, `CratesAdjustResponse`, `ErrorBody`,
     `HealthResponse`).
   - `backend/app/crud.py` (`create_participant`,
     `get_participant`, `adjust_crates`, `list_top`, `list_history`).
   - `backend/app/services/records.py`
     (`compute_is_new_record(participant, previous_max)`).
   - `backend/app/deps.py` (`get_db`).
   - `backend/app/routers/__init__.py`,
     `backend/app/routers/participants.py`,
     `backend/app/routers/leaderboard.py`.
   - `backend/app/main.py` (FastAPI app, CORS, routers, error
     handlers, `/docs`).
5. **Alembic**:
   - `backend/alembic.ini`.
   - `backend/alembic/env.py` reading `DATABASE_URL` from settings,
     `target_metadata = Base.metadata`.
   - `backend/alembic/script.py.mako` (Alembic default).
   - `backend/alembic/versions/0001_create_participants.py` produced
     by `alembic revision --autogenerate` against the SQLite dev DB
     and then edited to include the Postgres-only `CHECK` and
     indexes.
6. **Dev infra**:
   - `docker-compose.yml` with `db` (`postgres:16`,
     `POSTGRES_USER=escalabirras`, `POSTGRES_PASSWORD=escalabirras`,
     `POSTGRES_DB=escalabirras`, port `5432:5432`, named volume for
     data) and optional `adminer` on `8080:8080`.
   - `.env.example` with `DATABASE_URL=postgresql+psycopg://escalabirras:escalabirras@localhost:5432/escalabirras`
     and `CORS_ORIGINS=http://localhost:4200`.
7. **Tests** (`backend/tests/`):
   - `conftest.py`: per-test SQLite in-memory engine, `get_db`
     override, `httpx.AsyncClient` against the app.
   - `test_participants.py`: create, get, validation, 404.
   - `test_crates.py`: increment (including first-run new record,
     subsequent non-record, second participant overtakes), decrement
     including `crates_underflow` at zero.
   - `test_leaderboard.py`: ordering, tie-break by `created_at`,
     clamping of `limit`.
   - `test_history.py`: reverse-chronological order, pagination.
   - `test_health.py`: `/healthz`.
8. **Validation commands**:
   - `python3 -m venv .venv && source .venv/bin/activate && pip
     install -e backend[dev]` (or `pip install -r backend/requirements-dev.txt`).
   - `pytest backend -v`.
   - `cd backend && DATABASE_URL=sqlite:///./dev.db alembic upgrade
     head && DATABASE_URL=sqlite:///./dev.db uvicorn app.main:app
     --reload &` then `curl http://localhost:8000/healthz` and a
     handful of `/v1/*` calls.
   - `docker-compose config` to validate the compose file (does not
     require Docker running).
9. **Docs**: `backend/README.md` with quickstart for both Docker and
   bare-metal flows, and an explanation of the test-vs-prod DB
   divergence (SQLite vs Postgres).
10. **Final consistency sweep**:
    - `grep -nR "TODO" specs/contracts/api-rest specs/contracts/persistence-postgres specs/changes/002-backend-foundation` returns nothing.
    - `git status src/` is empty.
    - `specs/manifest.yml` still points to all the right paths.

## Risks

- **SQLite vs Postgres divergence.** Tests run on SQLite, prod on
  Postgres. `SELECT ... FOR UPDATE` is a Postgres-only construct.
  Mitigation: `crud.adjust_crates` uses SQLAlchemy's
  `with_for_update()` which is a no-op on SQLite; the prod path is
  covered by the contract and the Postgres schema. A future change
  could add a Testcontainers-based integration test if needed.
- **Alembic autogenerate noise.** SQLAlchemy's autogenerate can
  miss `CHECK` constraints and produce a migration that lacks them.
  Mitigation: the `0001` migration is hand-reviewed to include
  `op.create_check_constraint` and the two indexes.
- **CORS misconfiguration in dev.** If a developer runs the Angular
  app on a different port (e.g. `4201`), CORS will block it.
  Mitigation: `CORS_ORIGINS` env var is documented in `.env.example`
  and `backend/README.md`.
- **Connection pool exhaustion under load.** Not relevant for v1
  (single operator). Documented in `api-rest` non-goals.
- **Time zone drift.** `created_at` is stored as `TIMESTAMPTZ` and
  served as ISO 8601 with `Z`. Python side must use `datetime.now(tz=
  timezone.utc)` when comparing; the SQLAlchemy `server_default=
  func.now()` produces UTC by convention.
- **Backend boots before the DB is reachable.** In `docker-compose`
  the API service is not added in this change (only `db` and
  optionally `adminer`); developers start uvicorn manually after
  Postgres is up. Documented in `backend/README.md`.