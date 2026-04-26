# Setup — Postgres vs Cassandra writes

Run from **`databases/pg-vs-cassandra-writes`**.

## Start

```bash
docker compose build
docker compose up -d
```

**Cassandra** can take **1–2 minutes** before the healthcheck passes the first time.

Check API:

```bash
curl -sS http://127.0.0.1:8280/health
curl -sS http://127.0.0.1:8280/pg/stats
curl -sS http://127.0.0.1:8280/cassandra/stats
```

Example write:

```bash
curl -sS -X POST http://127.0.0.1:8280/pg/events \
  -H 'Content-Type: application/json' \
  -d '{"bucket":"demo","payload":{"x":1}}'

curl -sS -X POST http://127.0.0.1:8280/cassandra/events \
  -H 'Content-Type: application/json' \
  -d '{"bucket":"demo","payload":{"x":1}}'
```

## Locust

Open **http://localhost:8289** — host for workers in Compose is already **`http://api:8000`**.

From your laptop (Locust installed locally):

```bash
export TARGET_HOST=http://127.0.0.1:8280
locust -f locust/locustfile.py
```

## Reset data

```bash
docker compose down -v
docker compose up -d
```

## Troubleshooting

- **`cassandra-init` failed**: `docker compose logs cassandra-init` — usually Cassandra not ready; `docker compose up -d` again after Cassandra is healthy.
- **Cassandra OOM on small laptops**: lower heap in `docker-compose.yml` (`MAX_HEAP_SIZE` / `JVM_OPTS`) or reduce Locust users.
- **`/cassandra/stats` slow**: expected after many rows — `COUNT(*)` is a full scan in Cassandra.
