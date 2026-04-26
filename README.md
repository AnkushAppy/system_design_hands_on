# System design — hands-on

Hands-on exercises and reference stacks for **system design** topics: runnable services, observability, load testing, and notes you can extend over time.

**This file** is the repo index. Update it whenever you add a new area (new top-level folder, module, or significant doc) so others can find things quickly.

---

## Contents

| Area | Description | Docs |
|------|-------------|------|
| [**`databases/redis`**](databases/redis/) | Docker Compose stack: Nginx LB, FastAPI apps, single Redis, Prometheus, Grafana, cAdvisor, Locust; metrics export & chart scripts | [What & why](databases/redis/README.md) · [How to run](databases/redis/SETUP.md) |
| [**`databases/redis-cluster`**](databases/redis-cluster/) | Same HTTP/LB/app/observability pattern with **6-node Redis Cluster** (3 primaries + 3 replicas), multi-target `redis_exporter`, cluster bootstrap job | [What & why](databases/redis-cluster/README.md) · [How to run](databases/redis-cluster/SETUP.md) |
| [**`databases/pg-vs-cassandra-writes`**](databases/pg-vs-cassandra-writes/) | Single API: **`POST /pg/events`** vs **`POST /cassandra/events`**, Locust write stress (B-tree vs LSM intuition) | [What & why](databases/pg-vs-cassandra-writes/README.md) · [How to run](databases/pg-vs-cassandra-writes/SETUP.md) |

---

## Conventions (suggested)

- One **topic** per major directory (e.g. `databases/redis`, future `messaging/kafka`, …).
- Prefer a short **README** (intent + components) and a **SETUP** or **HOWTO** (commands) inside that directory, with links from here.
- Keep **root** `README.md` and **root** `.gitignore` current as the catalog and ignore rules grow.

---

## Requirements

Varies by subproject. Start from the linked **SETUP** in each area (e.g. Docker for the Redis stack, optional host Python for Locust).

---

## License

Add a license file when you are ready (e.g. MIT), and note it here.
