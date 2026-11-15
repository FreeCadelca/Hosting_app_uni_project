#!/bin/sh
set -eu
if [ ! -s "$PGDATA/PG_VERSION" ]; then
    mkdir -p "$PGDATA"
    chown postgres:postgres "$PGDATA"
    chmod 700 "$PGDATA"
    export PGPASSWORD=repl_pass
    gosu postgres pg_basebackup -h pg-master -U replicator -D "$PGDATA" -Fp -Xs -P -R
    unset PGPASSWORD
fi
exec docker-entrypoint.sh postgres
