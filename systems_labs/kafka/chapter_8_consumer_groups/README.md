# Chapter 8: Consumer Groups (Scale-out Consumption)

A **consumer group** is how Kafka distributes partitions across multiple worker processes.

- Every partition is consumed by **at most one consumer in the group at a time**.
- When you **add or remove consumers**, Kafka **rebalances** so partitions are reassigned.
- More partitions than consumers means some consumers read multiple partitions; **more consumers than partitions leaves some idle**.

## Prerequisites

- Docker
- Python 3 + `kafka-python` (`pip install -r requirements.txt`)

## Quick start

```bash
cd chapter_8_consumer_groups
docker compose up -d
```

Wait ~15–30 seconds, then:

```bash
pip install -r requirements.txt

python setup_topic.py
python producer_fanout.py 120
```

In **two terminals**, run consumers that share `**--group-id`**:

```bash
python consumer_in_group.py --group-id demo-workers --member A --from earliest

[A] group=demo-workers topic=orders — polling (Ctrl+C to stop)

[A] assigned partitions: 2, 3
```

```bash
python consumer_in_group.py --group-id demo-workers --member B --from earliest

[A] group=demo-workers topic=orders — polling (Ctrl+C to stop)

[A] assigned partitions: 0, 1
```



Watch each terminal print `**assigned partitions**`: together they hold all partitions of `orders` (four partitions).

Stop one consumer (Ctrl+C) and restart it — Kafka may **revoke/reassign** partitions (rebalancing).

Use `kafka-consumer-groups` inside the broker for the official lag view:

```bash
docker exec kafka-ch8 kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group demo-workers

Consumer group 'demo-workers' has no active members.

GROUP           TOPIC           PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG             CONSUMER-ID     HOST            CLIENT-ID
demo-workers    orders          0          0               0               0               -               -               -
demo-workers    orders          1          45              45              0               -               -               -
demo-workers    orders          2          60              60              0               -               -               -
demo-workers    orders          3          15              15              0               -               -               -

```

## Files


| File                   | Role                                               |
| ---------------------- | -------------------------------------------------- |
| `docker-compose.yml`   | Single-broker Kafka (KRaft), host port `9092`      |
| `setup_topic.py`       | Creates `orders` with 4 partitions                 |
| `producer_fanout.py`   | Produces keyed messages (spread across partitions) |
| `consumer_in_group.py` | Subscribe + print assigns + consume loop           |


## Cleanup

```bash
docker compose down -v
```

