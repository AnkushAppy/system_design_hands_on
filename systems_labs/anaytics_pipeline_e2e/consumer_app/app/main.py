"""Query API for ClickHouse-backed analytics data."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

import clickhouse_connect
from fastapi import FastAPI, HTTPException, Query

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

CH_HOST = os.environ.get("CLICKHOUSE_HOST", "localhost")
CH_PORT = int(os.environ.get("CLICKHOUSE_PORT", "8123"))
CH_USER = os.environ.get("CLICKHOUSE_USER", "user")
CH_PASSWORD = os.environ.get("CLICKHOUSE_PASSWORD", "password")
CH_DB = os.environ.get("CLICKHOUSE_DB", "default")
CH_TABLE = os.environ.get("CLICKHOUSE_TABLE", "events")

STARTUP_RETRIES = int(os.environ.get("CLICKHOUSE_STARTUP_RETRIES", "40"))
STARTUP_DELAY_SEC = float(os.environ.get("CLICKHOUSE_STARTUP_DELAY_SEC", "1.0"))

client: clickhouse_connect.driver.Client | None = None


def _ensure_schema(ch: clickhouse_connect.driver.Client) -> None:
    ch.command(
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


@asynccontextmanager
async def lifespan(_: FastAPI):
    global client
    last_err: Exception | None = None
    for attempt in range(1, STARTUP_RETRIES + 1):
        try:
            client = clickhouse_connect.get_client(
                host=CH_HOST,
                port=CH_PORT,
                username=CH_USER,
                password=CH_PASSWORD,
                database=CH_DB,
            )
            _ensure_schema(client)
            client.command("SELECT 1")
            log.info("ClickHouse client ready %s:%s db=%s table=%s", CH_HOST, CH_PORT, CH_DB, CH_TABLE)
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
            client = None
            log.warning("ClickHouse not ready (%s/%s): %s", attempt, STARTUP_RETRIES, e)
            await asyncio.sleep(STARTUP_DELAY_SEC)
    if client is None:
        raise RuntimeError("Could not connect to ClickHouse") from last_err

    yield

    if client is not None:
        client.close()
        client = None


app = FastAPI(title="Analytics Consumer API", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/counts")
def counts() -> dict[str, Any]:
    if client is None:
        raise HTTPException(status_code=503, detail="ClickHouse client not initialized")

    q = f"""
      SELECT event_type, count() AS cnt
      FROM {CH_DB}.{CH_TABLE}
      GROUP BY event_type
      ORDER BY cnt DESC
    """
    res = client.query(q)
    items = [{"event_type": r[0], "count": int(r[1])} for r in res.result_rows]
    return {"items": items}


@app.get("/events")
def events(limit: int = Query(default=50, ge=1, le=500)) -> dict[str, Any]:
    if client is None:
        raise HTTPException(status_code=503, detail="ClickHouse client not initialized")

    q = f"""
      SELECT ingested_at_ms, event_type, user_id, data_json
      FROM {CH_DB}.{CH_TABLE}
      ORDER BY ingested_at_ms DESC
      LIMIT %(limit)s
    """
    res = client.query(q, parameters={"limit": limit})
    out: list[dict[str, Any]] = []
    for ingested_at_ms, event_type, user_id, data_json in res.result_rows:
        try:
            data = json.loads(data_json) if isinstance(data_json, str) else data_json
        except Exception:
            data = {"_raw": data_json}
        out.append(
            {
                "ingested_at_ms": int(ingested_at_ms),
                "event_type": event_type,
                "user_id": user_id,
                "data": data,
            }
        )
    return {"items": out}

