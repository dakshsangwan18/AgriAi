#!/bin/sh
set -e

if [ -z "${POSTGRES_DB}" ] || [ -z "${POSTGRES_USER}" ] || [ -z "${POSTGRES_PASSWORD}" ]; then
  echo "POSTGRES_DB, POSTGRES_USER, and POSTGRES_PASSWORD are required" >&2
  exit 1
fi

BACKUP_DIR=${BACKUP_DIR:-./backend/backups}
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="${BACKUP_DIR}/backup_${POSTGRES_DB}_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

echo "Creating database backup: ${FILENAME}"
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump -h "${POSTGRES_HOST:-localhost}" -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "${FILENAME}"

echo "Backup completed"
