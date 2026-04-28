# Chapter 14: Ordering Guarantees (Keys, Partitions, Producers)

Kafka guarantees ordering **within a partition**. Because a key maps to one partition, you get:

- same key -> same partition (usually, for a fixed partition count)
- same partition -> append order
- therefore, per-key order is preserved

What breaks assumptions:

- increasing partition count can remap keys
- multiple producers writing the same key can interleave globally
- cross-key global ordering is not guaranteed

## Prerequisites

- Docker
- Python 3 + `kafka-python`

## Quick start

```bash
cd chapter_14_ordering
docker compose up -d
pip install -r requirements.txt
```

### Experiment 1: single producer, one key

```bash
python ordering_demo.py --mode single --key account_42 --count 30
```

Expected: `global seq monotonic=True` for that key.

### Experiment 2: two producers, same key

```bash
python ordering_demo.py --mode dual --key account_42 --count 30
```

Expected:

- per-source sequence remains monotonic
- global sequence for the key may become non-monotonic due to interleaving

### Experiment 3: change partition count (fresh cluster)

```bash
docker compose down -v
docker compose up -d
python ordering_demo.py --partitions 5 --mode single --key account_42 --count 30
```

This demonstrates that partition topology is part of ordering behavior.

## Files

| File | Role |
|------|------|
| `docker-compose.yml` | Single-broker Kafka |
| `ordering_demo.py` | Topic setup + producer mode + ordering report |

## Cleanup

```bash
docker compose down -v
```
