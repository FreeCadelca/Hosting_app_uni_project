#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
docker compose up --build -d
for route in auth products payment servers; do
    curl --fail --retry 30 --retry-all-errors --retry-delay 2 "http://localhost/api/$route/health"
done
curl --fail http://localhost/ >/dev/null
