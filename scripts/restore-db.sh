#!/bin/sh
set -e

if [ -z "${POSTGRES_DB}" ] || [ -z "${POSTGRES_USER}" ] || [ -z "${POSTGRES_PASSWORD}" ]; then
  echo "POSTGRES_DB, POSTGRES_USER, and POSTGRES_PASSWORD are required" >&2
  exit 1
fi

if [ -z "$1" ]; then
  echo "Usage: scripts/restore-db.sh <backup_file.sql.gz>" >&2
  exit 1
fi

BACKUP_FILE="$1"

echo "Restoring database from ${BACKUP_FILE}"
PGPASSWORD="${POSTGRES_PASSWORD}" gunzip -c "${BACKUP_FILE}" | psql -h "${POSTGRES_HOST:-localhost}" -U "${POSTGRES_USER}" "${POSTGRES_DB}"

echo "Restore completed"
