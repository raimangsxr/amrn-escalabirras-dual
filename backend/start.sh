#!/usr/bin/env bash
# Container entrypoint for the escalabirras backend.
#
# 1. Applies any pending Alembic migrations.
# 2. Execs uvicorn with N workers (default 2) and proxy-header trust
#    so the security middleware can detect the original scheme behind
#    a TLS-terminating proxy.

set -euo pipefail

echo "[entrypoint] running alembic upgrade head..."
alembic upgrade head

API_WORKERS="${API_WORKERS:-2}"
API_LOG_LEVEL="${API_LOG_LEVEL:-info}"

echo "[entrypoint] starting uvicorn with ${API_WORKERS} workers..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${API_WORKERS}" \
    --proxy-headers \
    --forwarded-allow-ips="*" \
    --log-level "${API_LOG_LEVEL}"