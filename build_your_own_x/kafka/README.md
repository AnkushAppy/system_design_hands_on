# Build Your Own Kafka

A hands-on, step-by-step journey to understand how Apache Kafka works by building simplified versions from the ground up. Each chapter adds one or two key concepts, progressing from a single file to a distributed, fault-tolerant system.

## Overview

This repository walks through the core ideas behind Kafka by implementing progressively more sophisticated versions of a message broker. By the end, you'll understand partitions, replication, indexing, and fault tolerance — and you'll see how the real Kafka stores data on disk.

## Prerequisites

- Python 3.8+
- Docker and Docker Compose (for Chapters 6 and 7)

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

## Cleanup

```bash
# Python chapters: no cleanup needed (local files only)

# Docker chapters:
cd chapter_6_docker
docker compose down -v

cd chapter_7_reliability
docker compose down -v
```

## Further Learning

- **Kafka: The Definitive Guide** (O'Reilly) — comprehensive reference
- **Kafka Internals** (Apache docs) — deep dive into replication, ISR, controller
- **Designing Data-Intensive Applications** (Martin Kleppmann) — broader context on log-based systems

---

## Roadmap: Next Concepts to Explore

Here are 5 advanced topics to continue your journey beyond the basics:

### 2. Idempotence (No More Duplicates)
**The Problem:** In distributed systems, "I sent the message, the server received it, but the network crashed before the server could tell me 'Success'. So I sent it again." Now you have two orders for the same pizza.

**The Concept:** Kafka has a "Producer ID" and "Sequence Number." If the producer sends the same message twice, the broker sees the sequence number is the same and silently drops the duplicate.

**The Learning:** Turn on `enable.idempotence=true`. This is what makes Kafka "Exactly Once" (almost) possible.

**Experiment:** Create a producer with idempotence enabled. Simulate a network retry and observe that duplicate messages are not written to the log.

---

### 3. Log Compaction (The "Latest Truth" Database)
**The Concept:** Most people think Kafka deletes data after 7 days. But there is a second mode called **Compaction**. If you send `User_1: "Lives in NY"` and then `User_1: "Lives in CA"`, Kafka will eventually delete the "NY" message and only keep the latest "CA" message for that key.

**Why It Matters:** This turns Kafka from a "stream of events" into a **Database**. You can store the current state of 1 million customers in a topic, and it will never grow too large because it only keeps the "latest truth" for each customer ID.

**The Experiment:** Create a topic with `cleanup.policy=compact`. Send 10 updates for the same key. Wait for the log cleaner to run (or force it) and see only the last message remains. Observe the `.log` file shrink as old keys are removed.

---

### 4. ksqlDB (SQL for Streams)
**The Aha! Moment:** If you know SQL, this will be your "Aha!" moment. Usually, to process data, you write a Java/Python app. With ksqlDB, you write SQL queries that run forever as data flows in.

**Standard SQL:** "Tell me the average price of orders right now (in the table)."

**ksqlDB:** "Tell me the average price of orders for every 5-minute window from now on."

**The Experiment:**
1. Add `ksqldb-server` and `ksqldb-cli` containers to your Docker Compose
2. Create a stream of "clicks"
3. Write a SQL query: `CREATE TABLE user_clicks AS SELECT user_id, COUNT(*) AS cnt FROM clicks WINDOW TUMBLING (SIZE 5 MINUTES) GROUP BY user_id;`
4. As you produce messages into Kafka, watch the SQL results update instantly on your screen

---

### 5. Consumer Lag (The "Health" Metric)
**The Concept:** In a traditional app, you monitor CPU and RAM. In Kafka, the most important metric is **Lag**. Lag is the distance between the last message produced and the last message read by your consumer.

- **Lag = 0:** You are real-time.
- **Lag = 1,000,000:** Your consumer is failing or too slow, and your system is "falling behind."

**The Learning:** Use a tool like Kafka UI, Cerebro, or `kafka-consumer-groups.sh` to visualize the lag. Understanding lag is how you know when to scale your consumer group. It's the heartbeat of a healthy streaming system.

**The Experiment:** Start a slow consumer (add `time.sleep(2)` between messages), produce messages rapidly, and watch the lag graph climb. Then add more consumers to the same group and see the lag drop as work is distributed.

---

## License

Educational — use freely to learn and teach.
