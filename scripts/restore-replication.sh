#!/bin/sh
# Return from the failover demonstration without losing writes on the promoted node.
set -eu
cd "$(dirname "$0")/.."
services="auth-service product-service payment-service provisioning-service management-service"
docker compose stop $services
backup=$(DB_HOST=pg-standby sh scripts/backup.sh)
echo "Promoted database backed up to $backup"
docker compose start pg-master
until docker compose exec -T pg-master pg_isready -U postgres >/dev/null; do sleep 1; done
DB_HOST=pg-master sh scripts/restore.sh "$backup"
docker compose stop pg-standby
# Preserve the old promoted data directory; clone into a fresh subdirectory.
touch .env
awk '!/^(DB_HOST|STANDBY_PGDATA)=/' .env > .env.recovery
echo 'DB_HOST=pg-master' >> .env.recovery
echo "STANDBY_PGDATA=/var/lib/postgresql/data/replica_$(date +%s)" >> .env.recovery
mv .env.recovery .env
docker compose up -d --no-deps --force-recreate pg-standby
docker compose up -d --no-deps --force-recreate $services
docker compose exec -T nginx nginx -s reload
echo "Master restored with promoted-node data; standby reinitializing. Previous replica files retained."
