# Chapter 7: Acks and Reliability (Durability)

This chapter connects **producer `acks`**, **replication**, and **`min.insync.replicas`** to what actually happens when a broker dies mid-flight.

## The core idea: how much confirmation you wait for

In a naive queue you send and hope. In Kafka the producer chooses how many replicas must acknowledge before the client considers a batch committed. That is the **`acks`** setting.

### `acks` settings

| Setting | Producer waits for | Durability | Latency |
|---------|-------------------|------------|---------|
| **`acks=0`** | Nothing (fire-and-forget) | Lowest; broker or network issues drop data silently | Lowest |
| **`acks=1`** | Leader persisted the record | Medium; if the leader fails before followers replicate, recent data can be lost | Low |
| **`acks=all`** (same as **`acks=-1`**) | Leader **and** enough in-sync replicas (ISR) per broker config | Highest when combined with `min.insync.replicas` and retries | Higher |

Important nuance: **`acks=all` does not mean “every broker in the cluster.”** It means “all replicas that are currently **in the ISR** for that partition,” capped by replication factor and broker health. That is why **`min.insync.replicas`** matters: the broker rejects writes if the ISR is too small, so you do not quietly commit at `acks=all` when only one replica is live.

With **`replication.factor=3`**, **`min.insync.replicas=2`**, and **`acks=all`**, losing **one** broker usually leaves at least two ISR members, so producing can continue after metadata and leader election settle. If **two** brokers are down, you often have fewer than two in-sync replicas for a partition; produces with `acks=all` can **fail or block** until the cluster recovers, which is preferable to acknowledging data that cannot survive another failure.

## Prerequisites

- Docker and Docker Compose
- Python 3 with **`kafka-python`** (same stack as earlier chapters):

  ```bash
  pip install kafka-python
  ```

## Cluster layout

From this directory:

```bash
docker compose up -d
```

Give the brokers **~15–30 seconds** on first start (ZooKeeper election, controller, internal topics).

This compose file defines:

| Service | Host ports | Role |
|---------|------------|------|
| `zookeeper` | `2181` | Coordination (Confluent 7.5 ZK mode) |
| `broker-1` | `9092` | Kafka |
| `broker-2` | `9093` | Kafka |
| `broker-3` | `9094` | Kafka |

Topic defaults (for auto-created topics such as `orders`):

- **`default.replication.factor`** / internal topics: **3**
- **`min.insync.replicas`**: **2** (so `acks=all` requires two live ISR members)

## Manual experiment: kill a broker while producing

**Terminal 1** — start the cluster, then produce with the safest setting:

```bash
cd chapter_7_reliability
docker compose up -d
# wait until brokers answer, then:
python producer_experiment.py all 50
```

**Terminal 2** — while the producer is still running:

```bash
docker kill broker-2
```

What you typically see with **`acks=all`** and **`min.insync.replicas=2`**:

- A short period of errors or pauses while leadership and ISR update (depends on timing).
- After the cluster stabilizes with two brokers, sends that satisfy the ISR rule **complete**; committed data that was already replicated is not “un-written.”
- The client library **retries** (this repo’s producer sets `retries=3` and `max_in_flight_requests_per_connection=1` to avoid reordering surprises while experimenting).

Try **`acks=1`** or **`acks=0`** with the same kill: you are more likely to see **failures or ambiguity** (and with `acks=0`, the client cannot even know what was lost).

## Automated demo

From `chapter_7_reliability` after `docker compose up -d`:

```bash
chmod +x kill_broker_test.sh   # once
./kill_broker_test.sh
```

The script waits for the cluster, runs the producer in the background, kills `broker-2` mid-run, waits for the producer to finish, then restarts `broker-2`.

## Verify message counts

The consumer reads **`orders`** from **`earliest`**, so the count is **cumulative for everything ever written** to that topic on the cluster. For a clean check, use a fresh volume:

```bash
docker compose down -v
docker compose up -d
# after brokers are ready:
python producer_experiment.py all 50
python consumer_verify.py 50    # exits 0 only if exactly 50 messages are visible
```

Without an argument, `consumer_verify.py` only prints totals and partition breakdowns:

```bash
python consumer_verify.py
```

The producer also prints a suggested verify command after each run.

## Files in this chapter

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Three brokers, ZK, RF=3, `min.insync.replicas=2` |
| `producer_experiment.py` | Configurable `acks` and message count; `compare` mode for back-to-back runs |
| `kill_broker_test.sh` | Scripted broker failure during `acks=all` produce |
| `consumer_verify.py` | Read-all + optional expected count assertion |

## Producer usage

```bash
python producer_experiment.py all 100
python producer_experiment.py 1 100
python producer_experiment.py 0 100
python producer_experiment.py compare   # interactive acks=0 / 1 / all
```

## Practical guidance (not legal advice)

| Pattern | Common choice | Why |
|---------|----------------|-----|
| High-volume telemetry where gaps are OK | `acks=1` or even `0` | Throughput and cost |
| Money, inventory, or anything requiring a durable audit trail | `acks=all` + `min.insync.replicas` ≥ 2 on critical topics | Commit only after redundant persistence |
| Idempotent “exactly-once-ish” semantics with retries | Enable **idempotent producer** (Kafka Java client; `kafka-python` exposes different knobs—know your client) | Avoid duplicates under retry |

## Cleanup

```bash
docker compose down -v    # remove containers and volumes (clean slate)
docker compose down       # stop containers; keep volumes for faster iteration
```

## Takeaways

1. **`acks=0`** — fastest; no delivery guarantee from the broker’s point of view.
2. **`acks=1`** — a good default for many workloads; still vulnerable to leader failure before replication.
3. **`acks=all`** — waits for the ISR; pair with **`min.insync.replicas`** so “all” means “enough replicas,” not “hope.”
4. **Fault tolerance is not magic:** with **`min.insync.replicas=2`**, you need **at least two healthy ISR members** to accept `acks=all` writes; killing too many brokers at once stops safe progress until replicas catch up.
