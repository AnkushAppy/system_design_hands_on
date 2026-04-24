# Redis Cluster observability lab

Six **Redis Cluster** nodes (three primaries + three replicas) on a fixed Docker bridge subnet, plus the same **HTTP → Nginx → two FastAPI apps** pattern as [`databases/redis`](../redis/), with **Prometheus**, **Grafana**, optional **cAdvisor**, and **Locust**.

**How to run:** [SETUP.md](SETUP.md)

---

## What you learn (vs single-node `databases/redis`)

| Topic | This lab |
|-------|-----------|
| **Sharding** | Keys are distributed across **hash slots** (managed by the cluster); the client follows **MOVED** / **ASK** redirects. |
| **Topology** | Multiple primaries; each slot has a primary (replicas for HA in this 3+3 layout). |
| **Discovery** | The app uses **`RedisCluster`** with **startup nodes** (all six endpoints) so it can learn the full topology. |
| **Metrics** | One **redis_exporter** process; Prometheus scrapes **each node** via the multi-target **`/scrape?target=`** pattern. |
| **Ops** | A one-shot **`cluster-init`** job runs `redis-cli --cluster create` (idempotent if the cluster is already `ok`). |

---

## Components (what / why)

| Piece | Role |
|-------|------|
| **redis-1 … redis-6** | Cluster members with **`cluster-announce-ip`** set to static IPs so nodes can gossip on the bridge network. |
| **cluster-init** | Waits for PING on all nodes, then **`redis-cli --cluster create … --cluster-replicas 1`**. |
| **redis-exporter** | Started with **`--redis.addr=`** so it does not default to a single Redis; Prometheus supplies each `target`. |
| **app-1 / app-2** | Same API as the single-node lesson, but **`redis.cluster.RedisCluster`** and **`REDIS_CLUSTER_NODES`**. |
| **load-balancer, nginx-exporter, prometheus, grafana, cadvisor, locust** | Same observability story as the first lab; **host ports differ** so both stacks can run side by side (see SETUP). |

---

## Ports vs `databases/redis`

This project uses **8180** (HTTP), **9190** (Prometheus), **3100** (Grafana), **8189** (Locust), **8181** (cAdvisor), **9114** (nginx exporter) so it does not collide with the single-node stack on **8080 / 9090 / 3000 / …**.

---

## Layout

| Path | Purpose |
|------|---------|
| `docker-compose.yml` | 6 Redis services, init, apps, LB, observability |
| `scripts/cluster-init.sh` | Cluster bootstrap |
| `app/` | Cluster-aware FastAPI |
| `prometheus/prometheus.yml` | Multi-target Redis scrape + usual jobs |
| `grafana/provisioning/` | Datasource + **Redis Cluster + LB + App** dashboard |
| `nginx/`, `locust/` | Same pattern as `databases/redis` |

---

## Further reading

- Redis Cluster [tutorial](https://redis.io/docs/management/scaling/) (slots, failover, limits).  
- Multi-target pattern for redis_exporter: [Prometheus docs](https://prometheus.io/docs/guides/multi-target-exporter/).
