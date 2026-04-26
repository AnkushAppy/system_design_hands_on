# Postgres vs Cassandra — write-heavy lab

One **HTTP API** with **two explicit write paths**:

- **`POST /pg/events`** → **PostgreSQL** (heap rows + **B-tree** secondary index on `bucket`)
- **`POST /cassandra/events`** → **Apache Cassandra** (partition key `bucket`, clustering `id` **timeuuid** — **LSM** / SSTables + compaction)

Same JSON body shape for both. Use **Locust** (or any client) to stress writes and compare latency, errors, and resource use.

**How to run:** [SETUP.md](SETUP.md)

---

## What you’re learning (B-tree vs LSM, simplified)

| Idea | Postgres (this schema) | Cassandra (this schema) |
|------|------------------------|---------------------------|
| **Write path** | Insert row + update **secondary index** (B-tree on `bucket`) | Append to **memtable**; later flush to **SSTables**; **compaction** merges SSTables |
| **Read model cost** | Index helps reads by `bucket`; **writes pay** index maintenance | Writes grouped by **partition** (`bucket`); **hot partition** if too many writes hit one `bucket` |
| **“Who wins”** | Depends on workload, disk, tuning — not universal | High append rate with **spread partitions** often favors Cassandra; **indexed churn** and transactional patterns often stress Postgres differently |

This repo does **not** tune production knobs; it gives you a **controlled** place to observe behavior under load.

---

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness |
| `POST` | `/pg/events` | Body: `{"bucket": "string", "payload": {}}` |
| `POST` | `/cassandra/events` | Same body |
| `GET` | `/pg/stats` | Row count (`SELECT count(*)`) |
| `GET` | `/cassandra/stats` | Row count — **full table scan** in Cassandra; slow on large tables |

---

## Ports (host)

- API: **8280**
- Postgres: **5433** → 5432 in container
- Cassandra CQL: **9043** → 9042
- Locust UI: **8289**

---

## Layout

- `docker-compose.yml` — Postgres, Cassandra, one-shot `cassandra-init`, `api`, `locust`
- `postgres/init.sql` — table + index
- `cassandra/schema.cql` — keyspace + table
- `app/` — FastAPI
- `locust/` — stress client
