#!/usr/bin/env bash
set -euo pipefail

if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL is required" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PRJ_ROOT="$(dirname "$SCRIPT_DIR")"

if [ ! -f "${PRJ_ROOT}/backend/alembic.ini" ]; then
  echo "alembic.ini not found at ${PRJ_ROOT}/backend/alembic.ini" >&2
  exit 1
fi

echo "Running database migrations..."
cd "${PRJ_ROOT}/backend"
alembic upgrade head
echo "Migrations completed successfully"
