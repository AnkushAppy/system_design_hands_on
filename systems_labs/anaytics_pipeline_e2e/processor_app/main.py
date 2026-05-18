"""Kafka -> ClickHouse processor (raw event loader)."""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
import time
from typing import Any

import clickhouse_connect
from kafka import KafkaConsumer
from kafka.errors import KafkaError

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.environ.get("REDPANDA_BROKERS", "localhost:19092")
TOPIC = os.environ.get("ANALYTICS_TOPIC", "analytics.events")
GROUP = os.environ.get("ANALYTICS_GROUP_ID", "analytics-pipeline-e2e")

CH_HOST = os.environ.get("CLICKHOUSE_HOST", "localhost")
CH_PORT = int(os.environ.get("CLICKHOUSE_PORT", "8123"))
CH_USER = os.environ.get("CLICKHOUSE_USER", "user")
CH_PASSWORD = os.environ.get("CLICKHOUSE_PASSWORD", "password")
CH_DB = os.environ.get("CLICKHOUSE_DB", "default")
CH_TABLE = os.environ.get("CLICKHOUSE_TABLE", "events")

BATCH_MAX = int(os.environ.get("INSERT_BATCH_MAX", "250"))
BATCH_FLUSH_SEC = float(os.environ.get("INSERT_BATCH_FLUSH_SEC", "1.5"))
CH_STARTUP_RETRIES = int(os.environ.get("CLICKHOUSE_STARTUP_RETRIES", "60"))
CH_STARTUP_DELAY_SEC = float(os.environ.get("CLICKHOUSE_STARTUP_DELAY_SEC", "1.0"))

running = True


def _stop(*_: object) -> None:
    global running
    running = False


def _ensure_schema(client: clickhouse_connect.driver.Client) -> None:
    client.command(
        f"""
        CREATE TABLE IF NOT EXISTS {CH_DB}.{CH_TABLE} (
          ingested_at_ms UInt64,
          event_type LowCardinality(String),
          user_id String,
          data_json String
        )
        ENGINE = MergeTree
        ORDER BY (event_type, user_id, ingested_at_ms)
        """
    )


def _as_row(payload: dict[str, Any]) -> list[Any]:
    ingested_at_ms = int(payload.get("ingested_at_ms") or 0)
    event_type = str(payload.get("event_type") or "")
    user_id = str(payload.get("user_id") or "")
    data = payload.get("data") or {}
    if not isinstance(data, dict):
        data = {"_raw": data}
    return [ingested_at_ms, event_type, user_id, json.dumps(data, separators=(",", ":"))]

def _connect_clickhouse_with_retries() -> clickhouse_connect.driver.Client:
    last_err: Exception | None = None
    for attempt in range(1, CH_STARTUP_RETRIES + 1):
        try:
            ch = clickhouse_connect.get_client(
                host=CH_HOST,
                port=CH_PORT,
                username=CH_USER,
                password=CH_PASSWORD,
                database=CH_DB,
            )
            _ensure_schema(ch)
            ch.command("SELECT 1")
            return ch
        except Exception as e:  # noqa: BLE001
            last_err = e
            log.warning("ClickHouse not ready (%s/%s): %s", attempt, CH_STARTUP_RETRIES, e)
            time.sleep(CH_STARTUP_DELAY_SEC)
    raise RuntimeError("Could not connect to ClickHouse") from last_err


def main() -> None:
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    log.info(
        "Processor starting bootstrap=%s topic=%s group=%s clickhouse=%s:%s %s.%s",
        KAFKA_BOOTSTRAP,
        TOPIC,
        GROUP,
        CH_HOST,
        CH_PORT,
        CH_DB,
        CH_TABLE,
    )

    ch = _connect_clickhouse_with_retries()

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=[s.strip() for s in KAFKA_BOOTSTRAP.split(",") if s.strip()],
        group_id=GROUP,
        enable_auto_commit=True,
        auto_offset_reset="earliest",
        key_deserializer=lambda b: b.decode("utf-8") if b is not None else None,
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
        consumer_timeout_ms=1000,
    )

    batch: list[list[Any]] = []
    last_flush = time.monotonic()
    total = 0

    try:
        while running:
            try:
                for msg in consumer:
                    if not running:
                        break
                    payload = msg.value
                    if not isinstance(payload, dict):
                        log.warning("skip non-dict payload: %s", payload)
                        continue
                    batch.append(_as_row(payload))
                    if len(batch) >= BATCH_MAX:
                        ch.insert(
                            f"{CH_DB}.{CH_TABLE}",
                            batch,
                            column_names=["ingested_at_ms", "event_type", "user_id", "data_json"],
                        )
                        total += len(batch)
                        log.info("inserted rows=%s (total=%s)", len(batch), total)
                        batch.clear()
                        last_flush = time.monotonic()
                # consumer timed out; fall through to flush checks
            except KafkaError as e:
                log.error("kafka error: %s", e)
                time.sleep(1.0)

            now = time.monotonic()
            if batch and (now - last_flush) >= BATCH_FLUSH_SEC:
                ch.insert(
                    f"{CH_DB}.{CH_TABLE}",
                    batch,
                    column_names=["ingested_at_ms", "event_type", "user_id", "data_json"],
                )
                total += len(batch)
                log.info("inserted rows=%s (total=%s)", len(batch), total)
                batch.clear()
                last_flush = now
    except Exception as e:  # noqa: BLE001
        log.error("processor crashed: %s", e)
        raise
    finally:
        try:
            if batch:
                ch.insert(
                    f"{CH_DB}.{CH_TABLE}",
                    batch,
                    column_names=["ingested_at_ms", "event_type", "user_id", "data_json"],
                )
                total += len(batch)
                log.info("final flush rows=%s (total=%s)", len(batch), total)
        except Exception:
            log.exception("final flush failed")
        consumer.close()
        ch.close()
        log.info("Processor stopped.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
