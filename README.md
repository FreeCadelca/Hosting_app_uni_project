# Hosting Service

A local teaching demo: five FastAPI services, PostgreSQL 16 with a standby,
Redis 7, a two-node RabbitMQ 3.13 cluster, and a static frontend behind nginx.
Virtual servers and payments are simulated.

## Start

Docker Desktop must be running with integration enabled for this WSL distro.

```sh
docker compose up --build -d
```

Open **http://localhost**. Register with an email and an 8–72-byte password,
choose a plan, pay, and wait for provisioning. The Servers page supports
stop, start, reboot and password reset.

The gateway uses port 80; service debug ports are 8001–8005. Data services have
no host port mappings. Inspect them with `docker compose exec`.
Credentials in Compose are for this local demo only. Do not delete volumes
to troubleshoot a startup failure.

## Checks

```sh
sh scripts/check-stage1.sh
python3 scripts/smoke.py
node scripts/check-frontend.cjs
python3 scripts/check-network.py
docker compose exec -T redis redis-cli TTL plans:all
docker compose exec -T pg-master psql -U postgres -d hosting -c 'SELECT state, sync_state FROM pg_stat_replication;'
docker compose exec -T rabbitmq-1 rabbitmqctl list_queues name synchronised_slave_pids
```

Smoke checks create unique demo users, orders and servers. The frontend check
executes the shipped JavaScript against the real API with a minimal DOM; it
does not replace a visual browser check.

Verified in this workspace:
- All containers start; public health endpoints and static HTML respond.
- Registration, login, caching, ordering, payment, provisioning and server actions.
- Frontend JavaScript registration → catalog → payment → active server.
- nginx cannot connect to PostgreSQL's data-network IP; backend services can.
- Disconnecting auth from backend-net blocks access (HTTP 504 in the tested
  timeout case); the network check reconnects it automatically.
- A synchronized RabbitMQ queue replica exists; ordering and provisioning work
  while rabbitmq-1 is stopped.
- PostgreSQL standby promotion and the full API workflow on the promoted node.
- Backup, restore, deletion and re-restore in an isolated test database.

## Message delivery

Payment commits the paid order to PostgreSQL. A background delivery worker
retries paid orders whose server is still pending, using either broker.
This also recovers payments made while brokers are unavailable. It declares
the durable exchange, queue and binding before publishing persistent messages
with confirms. Provisioning acknowledges after committing server details;
duplicate deliveries retain existing server credentials.

The queue has two classic mirrored replicas with automatic synchronization,
as supported by [RabbitMQ 3.13](https://www.rabbitmq.com/docs/3.13/ha).
This is a teaching configuration: classic mirroring is removed in RabbitMQ 4.
The application account has no administrator role and can access only the
orders exchange and provisioning queue.

## Failure demonstrations

Broker outage (restart it afterward):

```sh
docker compose stop rabbitmq-1
python3 scripts/smoke.py
docker compose start rabbitmq-1
```

Database failover:

```sh
sh scripts/failover.sh
python3 scripts/smoke.py
sh scripts/restore-replication.sh
```

Failover stops the original primary before promotion, changes application
connections, and persists DB_HOST in the ignored .env file. Replication is
asynchronous, so unreplicated transactions can be lost on an abrupt failure.
Promotion is manual, not automatic.

The recovery script briefly stops the application, backs up the promoted
database, restores it onto the original primary, and clones a fresh standby.
It keeps the previous standby files and the SQL backup. Do not run ordinary
startup commands midway through this demonstration.

Backup and restore:

```sh
sh scripts/backup.sh
sh scripts/restore.sh backups/backup_TIMESTAMP.sql
```

Restore replaces the target database contents; stop application writes first.
Use DB_HOST=pg-standby after promotion. RESTORE_DB can select a separate
database for a safe rehearsal. Backups include demo passwords and are ignored
by Git.

## Network layout

nginx belongs to frontend-net and backend-net. Application services belong to
backend-net and data-net. PostgreSQL, Redis and RabbitMQ belong only to the
internal data-net. Infrastructure ports are not published: publishing them
would allow access that defeats the isolation demonstration.

Requirements and original architecture are in agent-prompt.md and tech-stack.md.
