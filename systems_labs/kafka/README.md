# Build Your Own Kafka

A hands-on, step-by-step journey to understand how Apache Kafka works by building simplified versions from the ground up. Each chapter adds one or two key concepts, progressing from a single file to a distributed, fault-tolerant system.

## Overview

This repository walks through the core ideas behind Kafka by implementing progressively more sophisticated versions of a message broker. By the end, you'll understand partitions, replication, indexing, fault tolerance — plus **consumer groups**, **compacted topics**, **Schema Registry payloads**, and **consumer lag operations** — and you'll see how the real Kafka stores data on disk.

## Prerequisites

- Python 3.8+
- Docker and Docker Compose (for Chapter 6 onward in the `"real Kafka"` labs)

## Quick Start

```bash
# Install dependencies for Python-based chapters
cd chapter_1_producer
pip install -r ../requirements.txt  # if you create one, or install kafka-python as needed
```

## Chapter Guide

### Chapter 1: Simple Producer — Writing to a Log
**Location:** `chapter_1_producer/producer.py`

A single function that appends messages to a file. This is the most basic "queue" possible.

- Opens `my_topic.log` in append mode
- Writes a message + newline
- Closes the file

**Key Concept:** A log is just an ordered, immutable sequence of messages. Appending is fast and simple.

```python
def produce(topic_name, message):
    with open(f"{topic_name}.log", "a") as f:
        f.write(message + "\n")
```

**Run it:**
```bash
cd chapter_1_producer
python producer.py
```

---

### Chapter 2: Simple Consumer — Reading with an Offset
**Location:** `chapter_2_consumer/consumer.py`

Consumers don't delete messages. They remember their **offset** (line number) and read the next line.

- Reads the entire log file
- Tracks `current_offset` as state
- Prints new messages as they appear
- Sleeps and polls when no data is available

**Key Concept:** The offset is just an integer — the position in the ordered log. Consumers control their own position.

```python
def consume(topic_name, start_offset):
    current_offset = start_offset
    while True:
        with open(f"{topic_name}.log", "r") as f:
            lines = f.readlines()
            if len(lines) > current_offset:
                print(lines[current_offset])
                current_offset += 1
```

**Run it:**
```bash
cd chapter_2_consumer
python consumer.py
```

---

### Chapter 3: Integrated Producer & Consumer
**Location:** `chapter_3_integrated/producer_consumer.py`

Both producer and consumer in one file, running concurrently with threads. Demonstrates how they work together in real time.

- Producer thread writes messages
- Consumer thread reads them as they arrive
- Offsets track progress

**Key Concept:** Producers and consumers are independent. They scale separately. Consumers can lag, catch up, or restart without affecting producers.

**Run it:**
```bash
cd chapter_3_integrated
python producer_consumer.py
```

---

### Chapter 4: Partitions (Parallelism)
**Location:** `chapter_4_partitions/producer_consumer_partitions.py`

To scale beyond one file, we create multiple **partitions** (folders with separate log files). Messages are assigned to partitions by hashing a key.

- `orders_topic/partition_0.log`
- `orders_topic/partition_1.log`
- Each partition gets its own consumer thread

**Key Concepts:**
- **Parallelism:** Multiple consumers can read different partitions simultaneously
- **Ordering:** Messages with the same key go to the same partition, preserving order per key
- **Scalability:** Add more partitions to handle more throughput

**Run it:**
```bash
cd chapter_4_partitions
python producer_consumer_partitions.py
```

---

### Chapter 5: The Index (The "Pro" Move)
**Location:** `chapter_5_index/producer_consumer_index.py`

For a 10 GB log file, finding "line 5,000,000" by scanning is slow. The solution: an **index file** that maps offsets to byte positions.

- `partition_0.log` — the data
- `partition_0.index` — offset → byte position mapping (binary, 16 bytes per entry)
- Sparse indexing (every N messages)
- Binary search to find the closest indexed offset

**Key Concept:** Kafka is fast not because of magic — it uses simple files plus smart indexing. Seeking by byte offset avoids reading the entire log.

**Run it:**
```bash
cd chapter_5_index
python producer_consumer_index.py
```

---

### Chapter 6: Real Kafka with Docker Compose
**Location:** `chapter_6_docker/`

Run the **real Apache Kafka** in Docker using KRaft mode (no ZooKeeper). Then inspect the actual `.log` and `.index` files inside the container.

**What you'll see:**
- Real `.log` files with your messages in plain text (mixed with binary headers)
- Real `.index` files for fast offset-to-byte lookups
- The moment it "clicks": Kafka is just very high-performance file management

**Key Commands:**
```bash
cd chapter_6_docker
docker compose up -d
python produce_messages.py
./inspect_files.sh

# Inside the container:
docker exec -it kafka bash
cd /tmp/kraft-combined-logs
strings 00000000000000000000.log
```

**Key Concept:** The real Kafka uses the same fundamental ideas — logs, offsets, indexes — but with extreme optimization, replication, and clustering built on top.

---

### Chapter 7: Acks and Reliability (Durability)
**Location:** `chapter_7_reliability/`

A 3-broker Kafka cluster configured for maximum durability. Experiment with the `acks` setting and see what happens when you kill a broker mid-stream.

**Acks settings:**
- `acks=0` — Fire and forget (fast, can lose data)
- `acks=1` — Leader confirms (medium, can lose data if leader crashes)
- `acks=all` — All in-sync replicas confirm (safe, zero data loss)

**The Experiment:**
1. Start 3 brokers with replication factor 3
2. Produce with `acks=all`
3. Kill a broker while producing
4. Watch messages keep flowing — **zero loss**

**Key Concepts:**
- **Durability:** You choose how much "insurance" you want
- **Replication:** Messages live on multiple brokers
- **min.insync.replicas:** Enforces a minimum number of replicas for writes
- With 3 brokers and `acks=all`, you can lose 1–2 brokers and still not lose data

**Run the demo:**
```bash
cd chapter_7_reliability
docker compose up -d
python producer_experiment.py all 50

# In another terminal, while it's running:
docker kill broker-2

# It keeps working! No messages lost.

# Verify:
python consumer_verify.py
```

**The Automated Test:**
```bash
./kill_broker_test.sh
```

**Key Concept:** Kafka's durability guarantees come from replication and careful acknowledgment policies. You trade performance for safety.

---

### Chapter 8: Consumer Groups (`chapter_8_consumer_groups/`)

**Recommended after Chapter 7.** Run multiple consumers with the **same `group.id`**: Kafka assigns **partitions**, not duplicates, inside the group — that is horizontal scale-out for consuming.

See:

```bash
cd chapter_8_consumer_groups
docker compose up -d
pip install -r requirements.txt
python setup_topic.py
python producer_fanout.py
# Two terminals — same group:
python consumer_in_group.py --group-id demo-workers --member A --from earliest
python consumer_in_group.py --group-id demo-workers --member B --from earliest
```

---

### Chapter 10: Log Compaction (`chapter_10_compaction/`)

**Recommended after Chapter 8.** Topics with **`cleanup.policy=compact`** keep the **latest value per key** (subject to cleaner timing), turning a changelog into a keyed “latest truth” store.

```bash
cd chapter_10_compaction
docker compose up -d
pip install -r requirements.txt
python compaction_demo.py
```

---

### Chapter 12: Schema Registry + Avro (`chapter_12_schema_registry/`)

**Recommended after Chapter 10.** Registers Avro schemas in **Schema Registry**, then produces/consumes with the **`confluent-kafka`** client (wired serializers).

```bash
cd chapter_12_schema_registry
docker compose up -d
pip install -r requirements.txt   # installs confluent-kafka + certifi
python avro_producer.py
python avro_consumer.py
curl http://localhost:8081/subjects
```

---

### Chapter 9: Lag & Operations (`chapter_9_lag_ops/`)

**Recommended last in this arc.** Burst-produce vs slow-consume and read **`TOTAL-LAG`** from `kafka-consumer-groups` — the main operational KPI for pipelines.

```bash
cd chapter_9_lag_ops
docker compose up -d
pip install -r requirements.txt
python setup_lag_topic.py
# Terminal A: python slow_consume.py
# Terminal B: python burst_produce.py 20000
# Terminal C: ./check_lag.sh
```

---

### Chapter 14: Ordering Guarantees (`chapter_14_ordering/`)

Demonstrates Kafka's real ordering scope:

- ordering is guaranteed **within a partition**
- same key typically maps to one partition -> per-key ordering
- multiple producers can interleave writes for the same key

```bash
cd chapter_14_ordering
docker compose up -d
pip install -r requirements.txt
python ordering_demo.py --mode single --key account_42 --count 30
python ordering_demo.py --mode dual --key account_42 --count 30
```

---

### Chapter 15: Poison Messages + DLQ (`chapter_15_dlq/`)

Covers bad-record handling patterns:

- `skip` mode: ignore invalid records and continue
- `dlq` mode: publish failed records + error metadata to `orders_dlq`

```bash
cd chapter_15_dlq
docker compose up -d
pip install -r requirements.txt
python dlq_demo.py --action setup
python dlq_demo.py --action produce
python dlq_demo.py --action consume --mode dlq
python read_dlq.py
```

---

### Chapter 16: Kafka Connect (`chapter_16_connect/`)

Uses built-in file source/sink connectors to show Kafka as an integration hub:

```bash
cd chapter_16_connect
docker compose up -d
bash register_connectors.sh
cat ./connect-data/sink.txt
```

---

### Chapter 17: ksqlDB (`chapter_17_ksqldb/`)

Adds stream processing with SQL semantics:

```bash
cd chapter_17_ksqldb
docker compose up -d
pip install -r requirements.txt
bash create_pipeline.sh
python produce_clicks.py 300
```

---

### Suggested arc (beyond Chapters 1–7)

`8 consumer groups → 10 compaction → 12 schema registry → 9 lag/ops → 14 ordering → 15 DLQ → 16 Connect → 17 ksqlDB`.

---

## How the Concepts Build on Each Other

| Chapter | Adds | Why It Matters |
|---------|------|----------------|
| 1 | Append-only log | Foundation: immutable, ordered sequence |
| 2 | Offset tracking | Consumers control their position independently |
| 3 | Concurrency | Producers and consumers scale separately |
| 4 | Partitions | Horizontal scaling via parallelism and key-based ordering |
| 5 | Index files | Fast random access into huge logs (O(log n) instead of O(n)) |
| 6 | Real Kafka | Same concepts, production-grade implementation |
| 7 | Replication + Acks | Fault tolerance and durability guarantees |
| 8 | Consumer groups | Cooperative partition assignment across processes |
| 10 | Compaction | Keyed changelog semantics (“latest truth” per key) |
| 12 | Schema Registry | Contracts + evolution for payloads |
| 9 | Consumer lag (`kafka-consumer-groups`) | Operations: backlog and throughput diagnosis |
| 14 | Ordering and key behavior | Clarifies per-partition ordering guarantees and failure modes |
| 15 | DLQ pattern | Operational handling of poison messages |
| 16 | Kafka Connect | Declarative data movement between Kafka and external systems |
| 17 | ksqlDB | Stream processing with SQL over Kafka topics |

## Common Patterns Across All Chapters

1. **The log is append-only:** Messages are never modified or deleted (compaction aside). This makes reads fast and writes simple.

2. **Offsets are just integers:** A lightweight way to track position. No complex cursors or IDs needed.

3. **Consumers control their offset:** A consumer can rewind, fast-forward, or reset independently. This enables replay, debugging, and recovery.

4. **Partitioning = parallelism + ordering:** More partitions = more throughput. Same key = same partition = ordered processing.

5. **Indexing trades space for speed:** Sparse indexes use little extra space but enable O(log n) seeks instead of O(n) scans.

6. **Replication trades performance for durability:** More replicas = safer, but slower writes.

## Real Kafka vs. Our Mini-Kafka

What the real Kafka adds on top of our simplified versions:

- **Network layer:** TCP protocol, client libraries, request routing
- **ZooKeeper/KRaft:** Cluster coordination, leader election, metadata
- **Replication protocol:** ISR tracking, leader/follower sync, log matching
- **Segmented logs:** Log files split into segments (`.log`, `.index`, `.timeindex`) for easier compaction and cleanup
- **Compression:** Batch compression for efficiency
- **Batching:** Group multiple messages into fewer network/disk operations
- **Security:** TLS, SASL authentication, ACLs
- **Quotas, throttling, metrics, monitoring**
- **Exactly-once semantics, transactions**
- **Connect API, Streams API, ksqlDB**

But the core idea remains: **Kafka is a distributed, replicated, partitioned commit log with fast indexing.**

## Testing Each Chapter

### Chapters 1–5 (Python-based)
```bash
# Run the script
python producer.py          # or consumer.py, etc.

# Check the log file
cat orders.log
```

### Chapter 6 (Docker)
```bash
cd chapter_6_docker
docker compose up -d
python produce_messages.py
./inspect_files.sh
```

### Chapter 7 (Docker, 3-broker cluster)
```bash
cd chapter_7_reliability
docker compose up -d

# Option 1: Run the automated kill test
./kill_broker_test.sh

# Option 2: Manual testing
python producer_experiment.py all 100
# In another terminal:
docker kill broker-2
python consumer_verify.py
```

### Chapters 8, 10, 12, 9, 14, 15, 16 & 17 (Docker + Python)

See each folder README for precise commands (`setup_*.py`, producers, consumers, `docker compose`). Shortcuts:

```bash
# 8 — consumer groups & rebalance demos
cd chapter_8_consumer_groups && docker compose up -d && pip install -r requirements.txt

# 10 — compaction
cd chapter_10_compaction && docker compose up -d && pip install -r requirements.txt

# 12 — Schema Registry + Avro (`confluent-kafka`)
cd chapter_12_schema_registry && docker compose up -d && pip install -r requirements.txt

# 9 — burst vs slow consume + lag describe
cd chapter_9_lag_ops && docker compose up -d && pip install -r requirements.txt

# 14 — ordering guarantees
cd chapter_14_ordering && docker compose up -d && pip install -r requirements.txt

# 15 — poison messages + DLQ
cd chapter_15_dlq && docker compose up -d && pip install -r requirements.txt

# 16 — Kafka Connect
cd chapter_16_connect && docker compose up -d

# 17 — ksqlDB stream processing
cd chapter_17_ksqldb && docker compose up -d && pip install -r requirements.txt
```

Tip: Stop any other Compose stack bound to `:9092` before starting the next chapter (each lab uses localhost `9092` by default).

## Cleanup

```bash
# Python chapters (1–5): no Docker cleanup needed (local files only)

# Docker-backed Kafka labs — stop each Compose project (from repo root):
KAFKA=systems_labs/kafka
for dir in chapter_6_docker chapter_7_reliability chapter_8_consumer_groups \
           chapter_9_lag_ops chapter_10_compaction chapter_12_schema_registry \
           chapter_14_ordering chapter_15_dlq chapter_16_connect chapter_17_ksqldb; do
  ( cd "$KAFKA/$dir" && docker compose down -v )
done
```

## Further Learning

- **Kafka: The Definitive Guide** (O'Reilly) — comprehensive reference
- **Kafka Internals** (Apache docs) — deep dive into replication, ISR, controller
- **Designing Data-Intensive Applications** (Martin Kleppmann) — broader context on log-based systems

---

## Roadmap: Next Concepts to Explore

Chapters **8**, **10**, **12**, **9**, **14**, **15**, **16**, and **17** now cover groups, compaction, schemas, lag, ordering, DLQ, Connect, and ksqlDB. Ideas to layer on next:

### 1. Idempotence & EOS
**Problem:** Retries after an ambiguous produce response can duplicate records on the broker.

**Idea:** Enable idempotent producers (`enable.idempotence=true`) and, when needed, transactions for read–process–write workflows.

**Experiment:** Enable idempotence in a Docker-backed producer and simulate retries.

### 2. ksqlDB (SQL for Streams)
**The Aha! Moment:** If you know SQL, this will be your "Aha!" moment. Usually, to process data, you write a Java/Python app. With ksqlDB, you write SQL queries that run forever as data flows in.

**Standard SQL:** "Tell me the average price of orders right now (in the table)."

**ksqlDB:** "Tell me the average price of orders for every 5-minute window from now on."

**The Experiment:**
1. Add `ksqldb-server` and `ksqldb-cli` containers to your Docker Compose
2. Create a stream of "clicks"
3. Write a SQL query: `CREATE TABLE user_clicks AS SELECT user_id, COUNT(*) AS cnt FROM clicks WINDOW TUMBLING (SIZE 5 MINUTES) GROUP BY user_id;`
4. As you produce messages into Kafka, watch the SQL results update instantly on your screen

### 3. Connect, Streams APIs, and Dashboards
Kafka **Connect**, **Kafka Streams**, and UIs (**Kafka UI**, Grafana lag panels) compose the pieces you exercised here — groups, compaction, schemas, lag — into long-running integrations.

---

## License

Educational — use freely to learn and teach.
