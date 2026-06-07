#!/usr/bin/env bash
set -euo pipefail

if [ -z "${POSTGRES_DB:-}" ] || [ -z "${POSTGRES_USER:-}" ] || [ -z "${POSTGRES_PASSWORD:-}" ]; then
  echo "POSTGRES_DB, POSTGRES_USER, and POSTGRES_PASSWORD are required" >&2
  exit 1
fi

if [ -z "${1:-}" ]; then
  echo "Usage: scripts/restore-db.sh <backup_file.sql.gz>" >&2
  exit 1
fi

command -v psql >/dev/null 2>&1 || { echo "psql is not installed" >&2; exit 1; }
command -v gunzip >/dev/null 2>&1 || { echo "gunzip is not installed" >&2; exit 1; }

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
  echo "Backup file not found: ${BACKUP_FILE}" >&2
  exit 1
fi

if [ ! -s "${BACKUP_FILE}" ]; then
  echo "Backup file is empty: ${BACKUP_FILE}" >&2
  exit 1
fi

echo "WARNING: This will overwrite the current database '${POSTGRES_DB}'!"
echo "Backup file: ${BACKUP_FILE}"
read -r -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "${CONFIRM}" != "yes" ]; then
  echo "Restore cancelled"
  exit 0
fi

echo "Restoring database from ${BACKUP_FILE}"
export PGPASSWORD="${POSTGRES_PASSWORD}"
gunzip -c "${BACKUP_FILE}" | psql -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER}" --single-transaction "${POSTGRES_DB}"
unset PGPASSWORD

echo "Restore completed"
