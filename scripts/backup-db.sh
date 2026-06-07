#!/usr/bin/env bash
set -euo pipefail

if [ -z "${POSTGRES_DB:-}" ] || [ -z "${POSTGRES_USER:-}" ] || [ -z "${POSTGRES_PASSWORD:-}" ]; then
  echo "POSTGRES_DB, POSTGRES_USER, and POSTGRES_PASSWORD are required" >&2
  exit 1
fi

command -v pg_dump >/dev/null 2>&1 || { echo "pg_dump is not installed" >&2; exit 1; }
command -v gzip >/dev/null 2>&1 || { echo "gzip is not installed" >&2; exit 1; }

BACKUP_DIR=${BACKUP_DIR:-./backend/backups}
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="${BACKUP_DIR}/backup_${POSTGRES_DB}_${TIMESTAMP}.sql.gz"
KEEP_BACKUPS=${KEEP_BACKUPS:-7}

mkdir -p "${BACKUP_DIR}"

echo "Creating database backup: ${FILENAME}"
export PGPASSWORD="${POSTGRES_PASSWORD}"
pg_dump -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "${FILENAME}"
unset PGPASSWORD

if [ ! -s "${FILENAME}" ]; then
  echo "Backup file is empty or missing — pg_dump may have failed" >&2
  rm -f "${FILENAME}"
  exit 1
fi

BACKUP_COUNT=$(find "${BACKUP_DIR}" -name "backup_${POSTGRES_DB}_*.sql.gz" | wc -l)
if [ "${BACKUP_COUNT}" -gt "${KEEP_BACKUPS}" ]; then
  DELETE_COUNT=$((BACKUP_COUNT - KEEP_BACKUPS))
  echo "Rotating backups: removing ${DELETE_COUNT} old backup(s)"
  find "${BACKUP_DIR}" -name "backup_${POSTGRES_DB}_*.sql.gz" -print0 | sort -z | head -z -n "${DELETE_COUNT}" | xargs -0 rm -f
fi

echo "Backup completed: ${FILENAME}"
