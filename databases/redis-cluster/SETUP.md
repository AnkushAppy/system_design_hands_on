# Redis Cluster stack — setup & operations

Companion to [README.md](README.md) (concepts). **Run all commands from `databases/redis-cluster`.**

---

## Prerequisites

- Docker / Docker Compose v2  
- **Do not** change the Compose **project name** arbitrarily: Grafana’s cAdvisor panels filter on `com.docker.compose.project=redis-cluster` (the default when this folder is named `redis-cluster`).

---

## Start

```bash
cd databases/redis-cluster
docker compose build
docker compose up -d
```

First start: **`cluster-init`** forms the cluster (can take ~30–60s). Apps start only after it exits **0**.

Verify:

- <http://localhost:8180/health> — should include `"redis": "cluster"`.
- <http://localhost:9190/targets> — `redis-cluster-nodes` should show 6 targets **UP**.
- <http://localhost:3100> — Grafana → dashboard **Redis Cluster + LB + App**.

---

## Host ports (collision-safe vs `databases/redis`)

| Service | Host port |
|---------|-----------|
| Load balancer | **8180** |
| Prometheus | **9190** |
| Grafana | **3100** (`admin` / `admin`) |
| Locust | **8189** |
| cAdvisor UI | **8181** |
| Nginx exporter | **9114** |

Redis **data** ports are **not** published to the host by default (cluster talks on the internal network).

---

## Locust

**In Docker** (same compose network): open <http://localhost:8189>, host **`http://load-balancer:80`**.

**On your laptop** (after `pip install -r requirements.txt`):

```bash
export TARGET_HOST=http://127.0.0.1:8180
locust -f locust/locustfile.py
```

---

## API (same as single-node lesson)

- `GET /health`
- `GET` / `POST /api/counter?name=…`
- `GET` / `PUT /api/session/{sid}`

---

## Reset cluster data

If `cluster-init` or cluster state is broken:

```bash
docker compose down -v
docker compose up -d --build
```

`-v` removes Redis **and** Prometheus/Grafana volumes for this compose project.

---

## Troubleshooting

1. **`cluster-init` exits non-zero**  
   Inspect logs: `docker compose logs cluster-init`. Often fixed by `docker compose down -v` and bringing the stack up again.

2. **`redis-cluster-nodes` targets down in Prometheus**  
   Confirm static IPs **172.29.0.11–16** are not used by another Docker network on your machine. If they clash, change the subnet in `docker-compose.yml`, **and** the IPs in `prometheus/prometheus.yml` and `scripts/cluster-init.sh` together.

3. **cAdvisor panels empty**  
   Same as `databases/redis`: Docker Desktop quirks; check `docker logs` for the cadvisor service. Process-level Redis panels still work from redis_exporter.

4. **Grafana cAdvisor “no data”**  
   If you used `docker compose -p othername`, update the dashboard variable or PromQL filter `container_label_com_docker_compose_project` to match your project name.

---

## Optional: Prometheus queries from the host

```bash
curl -sS 'http://127.0.0.1:9190/api/v1/query?query=redis_cluster_slots_assigned' | head
```

(Metric exists only when the node is in cluster mode.)
