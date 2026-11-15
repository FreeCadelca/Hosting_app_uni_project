#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p backups
file="backups/backup_$(date +%Y%m%d_%H%M%S).sql"
umask 077
docker compose exec -T "${DB_HOST:-pg-master}" pg_dump -U postgres --clean --if-exists hosting > "$file.tmp"
mv "$file.tmp" "$file"
echo "$file"
