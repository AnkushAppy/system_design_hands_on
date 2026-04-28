# Chapter 9: Lag and Operations (“Is the Consumer Keeping Up?”)

For streaming systems the health signal is often **consumer lag**: how far behind the consumer group is versus the newest messages on each partition.

- **TOTAL-LAG** (from `kafka-consumer-groups`) is the backlog you need to drain.
- **Causes**: slow processing, insufficient consumers, hotspots on one partition, or bursts from producers.

## Prerequisites

Docker, Python 3, `kafka-python`.

## Quick start

```bash
cd chapter_9_lag_ops
docker compose up -d
- - -
CONTAINER ID   IMAGE                         COMMAND                  CREATED         STATUS         PORTS                              NAMES
f7f4ab0cb284   confluentinc/cp-kafka:7.5.0   "/etc/confluent/dock…"   4 seconds ago   Up 3 seconds   0.0.0.0:9092->9092/tcp             kafka-ch9

pip install -r requirements.txt

python setup_lag_topic.py
- - -
Created topic lag_demo (4 partitions).
```

Terminal 1 — **slow consumer** (sleeps modestly between messages):

```bash
python slow_consume.py
- - -
Consuming slowly from lag_demo group=lag-demo-group. sleep_ms=50.0. Ctrl+C to stop.
```

Terminal 2 — **burst producer**:

```bash
python burst_produce.py 20000
```

Terminal 3 — **observe lag**:

```bash
chmod +x check_lag.sh   # once
./check_lag.sh
- - -
GROUP           TOPIC           PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG             CONSUMER-ID                                             HOST            CLIENT-ID
lag-demo-group  lag_demo        0          0               3750            3750            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
lag-demo-group  lag_demo        1          0               2500            2500            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
lag-demo-group  lag_demo        2          0               7500            7500            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
lag-demo-group  lag_demo        3          0               6250            6250            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
- - -
GROUP           TOPIC           PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG             CONSUMER-ID                                             HOST            CLIENT-ID
lag-demo-group  lag_demo        0          751             3750            2999            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
lag-demo-group  lag_demo        1          249             2500            2251            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
lag-demo-group  lag_demo        2          0               7500            7500            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
lag-demo-group  lag_demo        3          0               6250            6250            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
- - -
GROUP           TOPIC           PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG             CONSUMER-ID                                             HOST            CLIENT-ID
lag-demo-group  lag_demo        0          751             3750            2999            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
lag-demo-group  lag_demo        1          500             2500            2000            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
lag-demo-group  lag_demo        2          0               7500            7500            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
lag-demo-group  lag_demo        3          249             6250            6001            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
- - -
GROUP           TOPIC           PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG             CONSUMER-ID                                             HOST            CLIENT-ID
lag-demo-group  lag_demo        0          751             3750            2999            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
lag-demo-group  lag_demo        1          500             2500            2000            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
lag-demo-group  lag_demo        2          0               7500            7500            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
lag-demo-group  lag_demo        3          749             6250            5501            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
- - -
GROUP           TOPIC           PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG             CONSUMER-ID                                             HOST            CLIENT-ID
lag-demo-group  lag_demo        0          751             3750            2999            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
lag-demo-group  lag_demo        1          500             2500            2000            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
lag-demo-group  lag_demo        2          498             7500            7002            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
lag-demo-group  lag_demo        3          1751            6250            4499            kafka-python-2.0.2-e2d260ed-1b6f-4f6d-a6f8-da224c9898eb /172.24.0.1     kafka-python-2.0.2
```

You should see **non-zero LAG** on `lag_demo` partitions while the slow consumer drains the backlog.

## Files


| File                 | Role                                         |
| -------------------- | -------------------------------------------- |
| `docker-compose.yml` | Single broker Kafka                          |
| `setup_lag_topic.py` | Creates `lag_demo` (4 partitions)            |
| `burst_produce.py`   | High throughput producer                     |
| `slow_consume.py`    | Throttled consumer in group `lag-demo-group` |
| `check_lag.sh`       | Wraps `kafka-consumer-groups --describe`     |


Environment overrides:

- `KAFKA_CONTAINER` (default `kafka-ch9`) if you rename the container.
- `GROUP_ID` (default `lag-demo-group`).

## Cleanup

```bash
docker compose down -v
```

