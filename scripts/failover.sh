#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
# Fence the old writer before promotion. Do not restart it as a writer afterward.
docker compose stop pg-master
docker compose exec -T -u postgres pg-standby sh -c 'pg_ctl promote -w -D "$PGDATA"' 
# Persist routing so later Compose commands keep using the promoted database.
touch .env
awk '!/^DB_HOST=/' .env > .env.failover
echo 'DB_HOST=pg-standby' >> .env.failover
mv .env.failover .env
DB_HOST=pg-standby docker compose up -d --no-deps --force-recreate auth-service product-service payment-service provisioning-service management-service
docker compose exec -T nginx nginx -s reload
echo "Standby is now primary. Use DB_HOST=pg-standby for subsequent Compose and backup commands."
