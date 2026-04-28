# Chapter 12: Schema Registry + Avro (Contracted payloads)

Kafka stores **bytes**. In real pipelines you attach a contract so producers and consumers agree on layout: **topics + schemas** via **Schema Registry**.

- Schemas evolve with **compatibility rules** (BACKWARD/FORWARD/FULL…) so clusters do not silently break clients.
- This chapter wires **Confluent Schema Registry** next to Kafka and uses **Apache Avro** with the **`confluent-kafka`** Python client (not `kafka-python`).

## Prerequisites

Docker, Python 3, `pip`:

```bash
pip install -r requirements.txt
```

(`certifi` is listed because some environments need it explicitly for HTTPS calls made by Schema Registry internals.)

## Quick start

```bash
cd chapter_12_schema_registry
docker compose up -d
```

Wait until **Kafka** listens on `:9092` and **Schema Registry** answers on `:8081` (first boot can take 30–60 seconds).

Smoke-test Schema Registry:

```bash
curl -s http://localhost:8081/subjects | head
```

Produce then consume Avro payloads:

```bash
python avro_producer.py
python avro_consumer.py
```

Subjects auto-register (`registered_users-value` pattern by default for Avro serializers). Inspect schemas:

```bash
curl http://localhost:8081/subjects
```

## Containers

| Service | Ports |
|---------|-------|
| `kafka-ch12` | `9092` |
| `schema-registry-ch12` | `8081` |

## Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Broker + Schema Registry |
| `avro_producer.py` | `SerializingProducer` + Avro schema |
| `avro_consumer.py` | `DeserializingConsumer` + matching schema |

## Cleanup

```bash
docker compose down -v
```
