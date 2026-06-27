# Tasks: 002-backend-foundation

## Tasks

- [x] Update `specs/manifest.yml` to add `api-rest` and
      `persistence-postgres` contracts and the
      `002-backend-foundation` change.
- [x] Write `specs/contracts/api-rest/contract.md`.
- [x] Write `specs/contracts/persistence-postgres/contract.md`.
- [x] Write `specs/changes/002-backend-foundation/spec.md`.
- [x] Write `specs/changes/002-backend-foundation/plan.md`.
- [x] Write this task list and the context pack.
- [x] Scaffold `backend/` directory tree.
- [x] Write `backend/pyproject.toml` with pinned deps.
- [x] Write `backend/app/config.py` (pydantic-settings).
- [x] Write `backend/app/database.py` (engine, SessionLocal, Base,
      `get_db`).
- [x] Write `backend/app/models.py` (`Participant` SQLAlchemy model).
- [x] Write `backend/app/schemas.py` (Pydantic DTOs).
- [x] Write `backend/app/crud.py` (atomic crate adjustments,
      leaderboard, history queries).
- [x] Write `backend/app/services/records.py`
      (`compute_is_new_record`).
- [x] Write `backend/app/deps.py` (`get_db`).
- [x] Write `backend/app/routers/participants.py` and
      `backend/app/routers/leaderboard.py`.
- [x] Write `backend/app/main.py` (FastAPI app, CORS, error
      handlers, `/healthz`, `/docs`).
- [x] Initialize Alembic and write
      `backend/alembic/versions/0001_create_participants.py`
      (hand-reviewed to include `CHECK (crates >= 0)` and both
      indexes).
- [x] Write `docker-compose.yml` with `db` and optional `adminer`.
- [x] Write `.env.example` at repo root.
- [x] Write `backend/tests/conftest.py` (per-test SQLite in-memory
      engine, `get_db` override, `httpx.AsyncClient`).
- [x] Write `backend/tests/test_participants.py`.
- [x] Write `backend/tests/test_crates.py` (including
      `crates_underflow` and first-run record).
- [x] Write `backend/tests/test_leaderboard.py` (ordering, tie-break,
      limit clamping).
- [x] Write `backend/tests/test_history.py` (ordering, pagination).
- [x] Write `backend/tests/test_health.py`.
- [x] Write `backend/README.md` with Docker and bare-metal flows.
- [x] Install backend deps in a local venv and run `pytest backend
      -v` until green.
- [x] Validate `docker-compose config` syntactically.
- [x] Validate the FastAPI app boots against SQLite and the
      documented `curl` calls succeed.
- [x] Final sweep: no `TODO` in the new SDD files; no `src/`
      changes; `specs/manifest.yml` consistent.

## Out of scope (recorded for future changes)

- Rewire the frontend to call this API (lives in
  `003-migrate-storage`).
- Move `app-core` to `specs/archive/` (happens at the end of
  `003`).
- Add auth, rate limiting, multi-event scoping, server-push, or
  production Dockerfile for the API.
- Add Testcontainers-based integration tests against real Postgres.
- Pinning Python version via `.python-version` or `runtime.txt`.
- Pre-commit hooks for Python (ruff / black / mypy).