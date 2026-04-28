# System design — hands-on

Hands-on exercises and reference stacks for **system design** topics: runnable services, observability, load testing, and notes you can extend over time.

**This file** is the repo index. Update it whenever you add a new area (new top-level folder, module, or significant doc) so others can find things quickly.

---

## Contents

| Area | Description | Docs |
|------|-------------|------|
| [**`agentic_ai/metrices`**](agentic_ai/metrices/) | Hands-on IR/search metric implementations with runnable demos: **MRR@K, NDCG@K, Precision@K, Recall@K, MAP/AP** | [Overview & run commands](agentic_ai/metrices/README.md) |
| [**`systems_labs/kafka`**](systems_labs/kafka/) | Hands-on Kafka from toy logs → real broker; includes **consumer groups**, **compaction**, **Schema Registry**, **lag ops** | [Kafka track](systems_labs/kafka/README.md) *(links every chapter README)* |
| [**`databases/redis`**](databases/redis/) | Docker Compose stack: Nginx LB, FastAPI apps, single Redis, Prometheus, Grafana, cAdvisor, Locust; metrics export & chart scripts | [What & why](databases/redis/README.md) · [How to run](databases/redis/SETUP.md) |
| [**`databases/redis-cluster`**](databases/redis-cluster/) | Same HTTP/LB/app/observability pattern with **6-node Redis Cluster** (3 primaries + 3 replicas), multi-target `redis_exporter`, cluster bootstrap job | [What & why](databases/redis-cluster/README.md) · [How to run](databases/redis-cluster/SETUP.md) |
| [**`databases/pg-vs-cassandra-writes`**](databases/pg-vs-cassandra-writes/) | Single API: **`POST /pg/events`** vs **`POST /cassandra/events`**, Locust write stress (B-tree vs LSM intuition) | [What & why](databases/pg-vs-cassandra-writes/README.md) · [How to run](databases/pg-vs-cassandra-writes/SETUP.md) |

Suggested Kafka learning path:

`chapter_1_producer` → `chapter_2_consumer` → `chapter_3_integrated` → `chapter_4_partitions` → `chapter_5_index` → `chapter_6_docker` → `chapter_7_reliability` → `chapter_8_consumer_groups` → `chapter_10_compaction` → `chapter_12_schema_registry` → `chapter_9_lag_ops` → `chapter_14_ordering` → `chapter_15_dlq` → `chapter_16_connect` → `chapter_17_ksqldb`.

---

## Latest Additions

- Added **search evaluation metrics** module at `agentic_ai/metrices` with runnable Python examples:
  - `mean_reciprocal_rank/mmr.py`
  - `ndcg/ndcg.py`
  - `precision_and_recall/pr_.py`
  - `map/map.py`
- Includes metric-specific docs and formula walkthroughs in subfolder READMEs.
- Expanded **Kafka** track at `systems_labs/kafka`: Chapters **8 / 10 / 12 / 9 / 14 / 15 / 16 / 17** — groups, compaction, schemas, lag operations, ordering guarantees, DLQ, Connect, and ksqlDB (see [Kafka README](systems_labs/kafka/README.md)).

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
