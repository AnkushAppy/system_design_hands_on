# Chapter 16: Kafka Connect (Integration Hub)

Kafka Connect moves data between Kafka and external systems without writing custom producer/consumer apps for every integration.

This chapter uses built-in **FileStreamSource** and **FileStreamSink** connectors to show the pattern end-to-end:

`file -> Kafka topic -> file`

## Prerequisites

- Docker + Docker Compose
- `curl`

## Quick start

```bash
cd chapter_16_connect
docker compose up -d
```

Wait for Connect to become healthy:

```bash
curl -s http://localhost:8083/connectors
```

Register demo connectors:

```bash
bash register_connectors.sh
```

Inspect output:

```bash
cat ./connect-data/sink.txt
```

If you append new lines to `connect-data/source.txt`, source connector continues reading them and sink file updates.

## Useful APIs

```bash
curl -s http://localhost:8083/connectors
curl -s http://localhost:8083/connectors/file-source-demo/status
curl -s http://localhost:8083/connectors/file-sink-demo/status
```

Delete connectors:

```bash
curl -s -X DELETE http://localhost:8083/connectors/file-source-demo
curl -s -X DELETE http://localhost:8083/connectors/file-sink-demo
```

## Files

| File | Role |
|------|------|
| `docker-compose.yml` | Kafka broker + Connect worker |
| `register_connectors.sh` | seeds source file and registers source/sink connectors |

## Cleanup

```bash
docker compose down -v
```
