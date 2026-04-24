# Redis observability stack

A **Docker Compose** learning lab: a small HTTP API behind a **load balancer**, backed by **Redis**, with **Prometheus** metrics, **Grafana** dashboards, optional **cAdvisor** for container resource stats, and **Locust** for load testing.

**How to run it** (ports, commands, Locust, exports) → **[SETUP.md](SETUP.md)**

---

## What this stack is for

- See **HTTP → app → Redis** in a real-looking topology (LB + two app containers).
- **Stress Redis** (memory policy, evictions) and still observe the system in **Grafana** and **Prometheus**.
- Practice the usual **“metrics → PromQL → dashboards”** path without a large production config.

---

## Components — what and why

| Component | What it does | Why it is here |
|-----------|----------------|----------------|
| **load-balancer** (Nginx) | Proxies HTTP to `app-1` and `app-2` (least-conn), exposes **`stub_status`** for scraping | Models a real edge/LB; gives Nginx request and connection metrics |
| **app-1**, **app-2** | Same **FastAPI** app: health, counter, session endpoints; talks to Redis; **`/metrics`** for Prometheus | Two instances so the LB and app metrics (per instance) are meaningful |
| **redis** | **Redis 7** with AOF, configurable **`maxmemory`** and **`maxmemory-policy`** | Single place for shared state; you can compare behaviors (e.g. `noeviction` vs `allkeys-lru`) under load |
| **redis-exporter** | Exposes **Redis `INFO` / keyspace** as Prometheus metrics | **Prometheus speaks HTTP**, not the Redis protocol — the exporter is the standard bridge |
| **nginx-exporter** | Polls Nginx `stub_status` and exposes **Prometheus** metrics | Same idea: scrape-friendly metrics for the LB without parsing logs |
| **prometheus** | **Pull** scrapes on an interval, stores time series | Central place to query and alert; exporters are designed to be scraped |
| **grafana** | **Dashboards** on top of the Prometheus datasource | Faster interpretation than raw PromQL for demos and on-call style views |
| **cadvisor** | **Per-container** CPU and memory (Linux cgroups) for Docker | **Complements** `redis-exporter`: process-level Redis stats vs **host/container** resource usage for the `redis` container |
| **locust** | **HTTP load generator** with a **web UI** (or headless) | Drives the LB so Redis, Nginx, and app metrics move under real concurrent traffic |

**Observability split:** *redis_exporter* answers “what is Redis doing?” (keys, evictions, memory, commands). *cAdvisor* answers “how much CPU/RAM is this **container** using on the host?” — different questions; both are useful.

---

## API surface (conceptual)

The demo app is intentionally small:

- **Liveness** and an **instance** label so you can see which backend handled a request.
- A **shared counter** and **JSON sessions** in Redis to generate read/write and key growth patterns under Locust.

Details of paths and query parameters are in [SETUP.md](SETUP.md#api-endpoints).

---

## Repository layout (high level)

| Path | Role |
|------|------|
| `docker-compose.yml` | All services, networks, volumes |
| `app/` | API Dockerfile + `prometheus_client` metrics |
| `nginx/` | LB config, `stub_status` location |
| `prometheus/` | Scrape config |
| `grafana/provisioning/` | Datasource and dashboard JSON |
| `locust/` | Locust scenarios |
| `scripts/` | Export Prometheus data to JSON, render SVG charts |
| `metrics/exports/`, `metrics/charts/` | Generated artifacts (see `.gitignore`) |
| `requirements.txt` | **Host-side** `pip` deps (Locust) only |

---

## Design notes (not step-by-step)

- **Nginx** stub_status metrics in **nginx-prometheus-exporter** v1.1 use names like `nginx_connections_*` and `nginx_http_requests_total` (not older `nginx_http_connections_*` names in some blog posts).
- **cAdvisor** on **Docker Desktop** can be finicky; Redis panels from `redis-exporter` are still valid if cAdvisor is empty. See [SETUP.md](SETUP.md#troubleshooting) for checks.
- Redis **`maxmemory`** and **`maxmemory-policy`** in Compose are for **demos** (OOM vs eviction), not production tuning.

For commands, ports, and troubleshooting → **[SETUP.md](SETUP.md)**.

**Related:** a **6-node Redis Cluster** variant (same HTTP/LB/metrics idea, different ports) lives in [`../redis-cluster/`](../redis-cluster/).
