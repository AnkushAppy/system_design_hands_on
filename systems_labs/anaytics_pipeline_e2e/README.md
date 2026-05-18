# Analytics Pipeline (E2E)

End-to-end analytics mini-pipeline with a write path and a read path:

- **FastAPI producer** ingests `/track` events and publishes to **Redpanda** (Kafka API)
- **Processor** consumes from Kafka and writes raw events into **ClickHouse** (`default.events`)
- **FastAPI consumer** queries ClickHouse for aggregates / recent events

## Ports

Host ports are **`8010` (producer)** and **`8011` (consumer)** to avoid conflicts with the non-E2E lab.

## Run

From this folder:

```bash
docker compose up -d --build
```

## Send sample events

```bash
./send_sample_events.sh
```

## Useful URLs

- Producer health: `http://localhost:8010/health`
- Producer ingest: `POST http://localhost:8010/track`
- Consumer health: `http://localhost:8011/health`
- Aggregates: `http://localhost:8011/counts`
- Recent events: `http://localhost:8011/events?limit=50`

## Load testing (Locust)

This repo includes a Locust script at `locustfile.py` that targets:

- **Writes**: `POST /track` on the producer (`AnalyticsWriteUser`)
- **Reads (optional)**: `/counts` and `/events` on the consumer (`AnalyticsReadUser`)

Install and run Locust:

```bash
pip install locust

# Opens Locust UI at http://localhost:8089
locust -f locustfile.py --host http://localhost:8010
```

Headless example:

```bash
USER_POOL_SIZE=50000 locust -f locustfile.py --host http://localhost:8010 -u 200 -r 20 -t 2m --headless
```

## Troubleshooting

If something looks stuck, these are the fastest checks:

```bash
docker compose ps
docker compose logs -f --tail 200
```

Reset the stack (deletes ClickHouse data volume):

```bash
docker compose down -v
docker compose up -d --build
```

