"""HTTP ingest API; publishes accepted payloads to Redpanda (Kafka API)."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import socket
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from kafka import KafkaProducer
from kafka.errors import KafkaError
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.environ.get("REDPANDA_BROKERS", "localhost:19092")
TOPIC = os.environ.get("ANALYTICS_TOPIC", "analytics.events")
STARTUP_RETRIES = int(os.environ.get("KAFKA_STARTUP_RETRIES", "40"))
STARTUP_DELAY_SEC = float(os.environ.get("KAFKA_STARTUP_DELAY_SEC", "1.0"))

producer: KafkaProducer | None = None


class TrackBody(BaseModel):
    event_type: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    data: dict[str, Any] = Field(default_factory=dict)


def _build_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=[s.strip() for s in KAFKA_BOOTSTRAP.split(",") if s.strip()],
        value_serializer=lambda v: json.dumps(v, separators=(",", ":")).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k is not None else None,
        linger_ms=5,
        acks="all",
        retries=5,
    )


def _parse_host_port(addr: str) -> tuple[str, int]:
    a = addr.strip()
    if ":" in a:
        host, port_s = a.rsplit(":", 1)
        return host, int(port_s)
    return a, 9092


def _tcp_reachable(bootstrap: str, timeout_sec: float = 5.0) -> None:
    last: OSError | None = None
    for raw in bootstrap.split(","):
        host, port = _parse_host_port(raw)
        try:
            with socket.create_connection((host, port), timeout=timeout_sec):
                return
        except OSError as e:
            last = e
    if last:
        raise last


@asynccontextmanager
async def lifespan(_: FastAPI):
    global producer

    last_err: Exception | None = None
    for attempt in range(1, STARTUP_RETRIES + 1):
        try:
            _tcp_reachable(KAFKA_BOOTSTRAP, timeout_sec=5.0)
            producer = _build_producer()
            log.info("Producer ready bootstrap=%s topic=%s", KAFKA_BOOTSTRAP, TOPIC)
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
            log.warning("Kafka not ready (%s/%s): %s", attempt, STARTUP_RETRIES, e)
            producer = None
            await asyncio.sleep(STARTUP_DELAY_SEC)

    if producer is None:
        raise RuntimeError(f"Could not connect to Kafka at {KAFKA_BOOTSTRAP}") from last_err

    yield

    if producer is not None:
        producer.flush(timeout=10)
        producer.close()
        producer = None


app = FastAPI(title="Analytics Producer API", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/track")
def track(body: TrackBody) -> dict[str, Any]:
    if producer is None:
        raise HTTPException(status_code=503, detail="Kafka producer not initialized")

    envelope = {
        "event_type": body.event_type,
        "user_id": body.user_id,
        "data": body.data,
        "ingested_at_ms": int(time.time() * 1000),
    }

    try:
        future = producer.send(TOPIC, key=body.user_id, value=envelope)
        future.get(timeout=10)
    except KafkaError as e:
        log.exception("Kafka send failed")
        raise HTTPException(status_code=502, detail=f"Kafka error: {e}") from e

    return {"status": "accepted", "topic": TOPIC}

