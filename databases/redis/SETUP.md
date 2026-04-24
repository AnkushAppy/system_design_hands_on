# Setup and operations — how to run the stack

This file is the **procedural** companion to [README.md](README.md) (what each part is and why). Everything below is **how**.

---

## Prerequisites

- **Docker** and **Docker Compose** (v2)
- Optional: **Python 3** on the host for Locust outside Docker, export scripts, and chart scripts (see each section)

---

## Quick start

```bash
cd databases/redis
docker compose build
docker compose up -d
```

Check:

| What | URL |
|------|-----|
| API (via load balancer) | <http://localhost:8080/health> |
| Prometheus | <http://localhost:9090> |
| Grafana | <http://localhost:3000> (default `admin` / `admin`) |
| Locust (if service is up) | <http://localhost:8089> |
| cAdvisor (optional UI) | <http://localhost:8081> — metrics are scraped by Prometheus |

Grafana: open **Dashboards** → **Redis, LB, App & cAdvisor** (provisioned on startup).

---

## Ports (host)

| Service | Port |
|---------|------|
| Load balancer (Nginx) | 8080 |
| Redis | 6379 |
| Redis exporter | 9121 |
| Nginx exporter | 9113 |
| App containers | *not* published — use the LB on **8080** |
| Prometheus | 9090 |
| Grafana | 3000 |
| Locust | 8089 |
| cAdvisor | 8081 (UI; Prom scrapes the service on the internal network) |

---

## API endpoints

- `GET /health` — liveness, includes `instance` id.
- `GET` / `POST /api/counter` — shared counter in Redis (`name` query param, optional `step` for POST).
- `GET` / `PUT /api/session/{sid}` — JSON session in Redis (TTL 1h on writes).

---

## Locust (load tests)

### Inside Docker (recommended with the compose service)

1. `docker compose up -d` (includes Locust if you start the full project).
2. Open <http://localhost:8089>.
3. **Host** for workers on the same compose network: **`http://load-balancer:80`** (often pre-set via `TARGET_HOST` in `docker-compose.yml`).

**Headless example:**

```bash
docker compose run --rm -e PAYLOAD_MAX_KB=64 -e TARGET_HOST=http://load-balancer:80 locust \
  -f /mnt/locust/locustfile.py --headless -u 200 -r 20 -t 2m --host http://load-balancer:80
```

The locust file path **inside the container** is `/mnt/locust/locustfile.py` (see volume in `docker-compose.yml`).

### On your machine (outside Docker)

```bash
cd databases/redis
pip install -r requirements.txt   # or use a venv
export TARGET_HOST=http://127.0.0.1:8080
locust -f locust/locustfile.py
```

Open <http://localhost:8089> and start the test, or add `--headless` / `-u` / `-r` / `-t` as needed.

`TARGET_HOST` must be **`http://127.0.0.1:8080`** (or your machine’s IP) so traffic hits the **published** Nginx port — not `http://load-balancer:80` (that hostname only resolves inside the compose network).

---

## Export metrics to JSON (offline)

`scripts/export_metrics.py` calls the Prometheus HTTP API and writes:

- `metrics/exports/latest.json`
- `metrics/exports/history/metrics-<UTC-timestamp>.json`

```bash
export PROMETHEUS_URL=http://127.0.0.1:9090   # default if omitted
python3 scripts/export_metrics.py
```

Edit `RANGE_QUERIES` and `INSTANT_QUERIES` at the top of the script to add or change series.

`rate(...[5m])` style queries can be empty for the first few minutes after startup until enough scrapes exist.

---

## Render charts (SVG) from an export

Stdlib-only (no extra `pip` packages):

```bash
python3 scripts/display_charts.py
python3 scripts/display_charts.py metrics/exports/history/metrics-20250101T120000Z.json
```

Output: one **`.svg` per series key** under `metrics/charts/`.

**One-liner** (export + charts):

```bash
export PROMETHEUS_URL=http://127.0.0.1:9090
./scripts/dump_and_chart.sh
```

---

## Shut down

```bash
docker compose down
```

Remove data volumes (Redis, Prometheus, Grafana on-disk TSDB, etc.):

```bash
docker compose down -v
```

---

## File map (operational)

- `docker-compose.yml` — services, volumes, env
- `nginx/nginx.conf` — upstream, proxy, `stub_status`
- `app/` — API + `/metrics`
- `prometheus/prometheus.yml` — scrape targets
- `grafana/provisioning/` — datasource UID `prom`, dashboard JSON
- `locust/locustfile.py` — load scenarios; host run uses `requirements.txt`
- `scripts/export_metrics.py`, `scripts/display_charts.py`, `scripts/dump_and_chart.sh`

---

## Troubleshooting

- **Nginx / Prometheus names:** v1.1 exporter uses `nginx_connections_*` and `nginx_http_requests_total`. If a dashboard query is empty, check **Explore** in Grafana or <http://localhost:9090/graph>.
- **cAdvisor:** On some **Docker Desktop** hosts, cAdvisor may show no containers. Check `docker logs cadvisor` and that **Status → Targets** in Prometheus has the `cadvisor` job **UP**. **Redis** charts from `redis-exporter` do not depend on cAdvisor.
- **Locust “file not found” in container:** the host path `./locust` must contain `locustfile.py` (see [README](README.md#repository-layout-high-level)); recreate with `docker compose up -d --force-recreate locust` after adding files.
- **Redis at `maxmemory`:** with **`noeviction`**, writes can fail; with **`allkeys-lru`**, evictions happen — align expectations with your policy in `docker-compose.yml`.

For architecture and motivation, see [README.md](README.md).
