#!/bin/sh
set -e

if [ -z "${DATABASE_URL}" ]; then
  echo "DATABASE_URL is required" >&2
  exit 1
fi

echo "Running database migrations..."
alembic upgrade head
