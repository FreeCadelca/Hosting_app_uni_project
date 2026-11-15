#!/bin/sh
set -eu
if [ "$#" -ne 1 ]; then echo "Usage: $0 backup.sql" >&2; exit 1; fi
# Restore targets an explicitly named database, allowing a safe rehearsal.
file=$(realpath "$1")
cd "$(dirname "$0")/.."
docker compose exec -T "${DB_HOST:-pg-master}" psql -v ON_ERROR_STOP=1 --single-transaction -U postgres -d "${RESTORE_DB:-hosting}" < "$file"
