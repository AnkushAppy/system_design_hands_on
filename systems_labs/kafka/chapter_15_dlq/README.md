# Chapter 15: Poison Messages and the DLQ Pattern

When consumers meet invalid input (bad JSON, missing fields, schema mismatch), you generally choose one:

- **skip** bad records and continue processing
- **DLQ** bad records to another topic (`orders_dlq`) for triage/replay

This chapter demonstrates both modes.

## Prerequisites

- Docker
- Python 3 + `kafka-python`

## Quick start

```bash
cd chapter_15_dlq
docker compose up -d
pip install -r requirements.txt
```

Initialize topics:

```bash
python dlq_demo.py --action setup
python dlq_demo.py --action produce
```

### Mode 1: skip invalid

```bash
python dlq_demo.py --action consume --mode skip
```

### Mode 2: route invalid to DLQ

```bash
python dlq_demo.py --action consume --mode dlq
python read_dlq.py
```

## What to observe

- valid orders are processed normally
- malformed/missing fields are flagged
- in DLQ mode, failed messages appear in `orders_dlq` with metadata:
  - original topic, partition, offset
  - key, raw payload
  - error string and timestamp

## Files

| File | Role |
|------|------|
| `docker-compose.yml` | Single-broker Kafka |
| `dlq_demo.py` | setup + produce + consume(skip/dlq) |
| `read_dlq.py` | reads DLQ records for debugging |

## Cleanup

```bash
docker compose down -v
```
