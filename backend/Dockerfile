# syntax=docker/dockerfile:1.6
#
# Multi-stage build for the escalabirras FastAPI backend.
#   - Builder: build the wheel from pyproject.toml.
#   - Runtime: slim image with the wheel installed, a non-root user,
#     and uvicorn as CMD. Exposes 8000 and HEALTHCHECK against /healthz.
#     Migrations (alembic upgrade head) are run out-of-band in K8s
#     (a separate Job), not by the image entrypoint.

ARG PYTHON_VERSION=3.12-slim

FROM python:${PYTHON_VERSION} AS builder
WORKDIR /build

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app ./app

RUN pip install --upgrade pip build \
    && python -m build --wheel --outdir /wheels

FROM python:${PYTHON_VERSION} AS runtime
WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --home /app --shell /sbin/nologin app

COPY --from=builder /wheels /wheels
COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

RUN pip install --no-index --find-links=/wheels escalabirras-backend \
    && pip install alembic \
    && chown -R app:app /app

USER app
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=3 \
    CMD curl --fail --silent http://127.0.0.1:8000/healthz || exit 1

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${API_WORKERS:-2} --log-level ${API_LOG_LEVEL:-info} --proxy-headers --forwarded-allow-ips='*'"]