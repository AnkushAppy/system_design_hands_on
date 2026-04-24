#!/usr/bin/env python3
"""
Fetch range/instant results from the Prometheus HTTP API and write JSON dumps
to metrics/exports/ for offline review and charting.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Prometheus reachable from the host (compose maps 9090:9090)
PROM = os.environ.get("PROMETHEUS_URL", "http://127.0.0.1:9090").rstrip("/")
BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / "metrics" / "exports"
HISTORY = OUT_DIR / "history"
RANGE_END = int(time.time())
# Last 30 minutes, 15s step (Prometheus 11000 point limit is fine)
RANGE_START = RANGE_END - 30 * 60
STEP = 15

# Named PromQL for demos — adjust in Grafana to explore more.
RANGE_QUERIES: list[tuple[str, str]] = [
    ("redis_memory_bytes", "redis_memory_used_bytes"),
    ("redis_keyspace_hits", "rate(redis_keyspace_hits_total[5m])"),
    ("redis_keyspace_misses", "rate(redis_keyspace_misses_total[5m])"),
    ("app_http_req_rate", 'sum by (path) (rate(http_requests_total[5m]))'),
    (
        "app_redis_ops_rate",
        'sum by (op) (rate(redis_ops_total[5m]))',
    ),
    (
        "nginx_active_connections",
        "nginx_connections_active",
    ),
    (
        "nginx_requests_per_sec",
        "rate(nginx_http_requests_total[5m])",
    ),
    (
        "prom_scrape_samples",
        "scrape_samples_scraped",
    ),
]

# Instant snapshot (single value per target)
INSTANT_QUERIES: list[tuple[str, str]] = [
    ("redis_uptime", "redis_uptime_in_seconds"),
    ("redis_db_keys_total", "sum(redis_db_keys)"),
    ("up_redis_exporter", "up{job=\"redis-exporter\"}"),
    ("up_nginx_exporter", "up{job=\"nginx-exporter\"}"),
    ("up_app", "up{job=\"app\"}"),
]


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        return json.load(resp)


def _range_query(q: str) -> dict:
    params = urllib.parse.urlencode(
        {
            "query": q,
            "start": str(RANGE_START),
            "end": str(RANGE_END),
            "step": str(STEP),
        }
    )
    return _get(f"{PROM}/api/v1/query_range?{params}")


def _instant_query(q: str) -> dict:
    params = urllib.parse.urlencode({"query": q})
    return _get(f"{PROM}/api/v1/query?{params}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload: dict = {
        "meta": {
            "prometheus_url": PROM,
            "exported_at_utc": datetime.now(timezone.utc).isoformat(),
            "range": {
                "start_unix": RANGE_START,
                "end_unix": RANGE_END,
                "step_sec": STEP,
            },
        },
        "range": {},
        "instant": {},
    }

    for name, ql in RANGE_QUERIES:
        try:
            payload["range"][name] = _range_query(ql)
        except Exception as e:  # noqa: BLE001
            payload["range"][name] = {"error": str(e)}

    for name, ql in INSTANT_QUERIES:
        try:
            payload["instant"][name] = _instant_query(ql)
        except Exception as e:  # noqa: BLE001
            payload["instant"][name] = {"error": str(e)}

    latest = OUT_DIR / "latest.json"
    hist = HISTORY / f"metrics-{stamp}.json"
    for path in (latest, hist):
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
