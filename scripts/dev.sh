#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://flare:flare_local_demo@127.0.0.1:5432/flare}"
cd backend
../work/venv/bin/alembic upgrade head
../work/venv/bin/python -m flare.seed
../work/venv/bin/python -m flare.worker &
worker_pid=$!
trap 'kill "$worker_pid" 2>/dev/null || true' EXIT INT TERM
../work/venv/bin/uvicorn flare.api:app --host 0.0.0.0 --port "${PORT:-8100}"
