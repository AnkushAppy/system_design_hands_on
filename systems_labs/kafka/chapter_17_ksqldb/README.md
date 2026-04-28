# Chapter 17: ksqlDB (Stream Processing with SQL)

This chapter adds stream processing on top of Kafka using **ksqlDB**.

Goal:

- produce click events to `clicks_raw`
- define a stream (`clicks_stream`)
- materialize per-user counts (`clicks_per_user`)

## Prerequisites

- Docker
- Python 3 + `kafka-python`
- `curl`

## Quick start

```bash
cd chapter_17_ksqldb
docker compose up -d
pip install -r requirements.txt
```

Wait until ksqlDB is live:

```bash
curl -s http://localhost:8088/info
```

Create stream + table:

```bash
bash create_pipeline.sh
```

Produce sample events:

```bash
python produce_clicks.py 300
```

Read output changelog topic from broker:

```bash
docker exec kafka-ch17 kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic CLICKS_PER_USER \
  --from-beginning \
  --property print.key=true \
  --max-messages 20
```

## Files

| File | Role |
|------|------|
| `docker-compose.yml` | Kafka + ksqlDB server |
| `create_pipeline.sh` | Creates stream/table pipeline via REST |
| `produce_clicks.py` | Emits JSON click events |

## Cleanup

```bash
docker compose down -v
```
