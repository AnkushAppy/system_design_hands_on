"""
Write-heavy lab: explicit routes for Postgres (B-tree + heap) vs Cassandra (LSM).
"""
import json
import os
import uuid
from contextlib import contextmanager
from typing import Any

import psycopg2
from cassandra.cluster import Cluster
from fastapi import Body, FastAPI, HTTPException

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/lab",
)
CASSANDRA_HOSTS = os.environ.get("CASSANDRA_HOSTS", "cassandra").split(",")
CASSANDRA_KEYSPACE = os.environ.get("CASSANDRA_KEYSPACE", "lab")

app = FastAPI(title="pg-vs-cassandra-writes", version="0.1.0")

_pg_conn = None
_cassandra_session = None


def _pg():
    global _pg_conn
    if _pg_conn is None or _pg_conn.closed:
        _pg_conn = psycopg2.connect(DATABASE_URL)
    return _pg_conn


def _cass():
    global _cassandra_session
    if _cassandra_session is None:
        cluster = Cluster(contact_points=[h.strip() for h in CASSANDRA_HOSTS if h.strip()], port=9042)
        _cassandra_session = cluster.connect(CASSANDRA_KEYSPACE)
    return _cassandra_session


@contextmanager
def _pg_cursor():
    conn = _pg()
    conn.autocommit = True
    cur = conn.cursor()
    try:
        yield cur
    finally:
        cur.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/pg/events")
def write_pg_event(body: dict[str, Any] = Body(...)):
    bucket = body.get("bucket")
    if not bucket or not isinstance(bucket, str):
        raise HTTPException(status_code=400, detail="bucket (string) is required")
    payload = body.get("payload", {})
    eid = uuid.uuid4()
    try:
        with _pg_cursor() as cur:
            cur.execute(
                "INSERT INTO events (id, bucket, payload) VALUES (%s, %s, %s::jsonb)",
                (str(eid), bucket, json.dumps(payload)),
            )
    except psycopg2.Error as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return {"backend": "postgres", "id": str(eid), "bucket": bucket}


@app.post("/cassandra/events")
def write_cassandra_event(body: dict[str, Any] = Body(...)):
    bucket = body.get("bucket")
    if not bucket or not isinstance(bucket, str):
        raise HTTPException(status_code=400, detail="bucket (string) is required")
    payload = body.get("payload", {})
    # timeuuid for clustering column (write-ordered)
    from uuid import uuid1

    tid = uuid1()
    session = _cass()
    try:
        session.execute(
            "INSERT INTO events (bucket, id, payload) VALUES (%s, %s, %s)",
            (bucket, tid, json.dumps(payload)),
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=str(e)) from e
    return {"backend": "cassandra", "id": str(tid), "bucket": bucket}


@app.get("/pg/stats")
def pg_stats():
    try:
        with _pg_cursor() as cur:
            cur.execute("SELECT count(*)::bigint FROM events")
            (n,) = cur.fetchone()
    except psycopg2.Error as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return {"backend": "postgres", "rows": int(n)}


@app.get("/cassandra/stats")
def cassandra_stats():
    session = _cass()
    try:
        rows = session.execute("SELECT count(*) FROM events")
        n = rows.one()[0]
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=str(e)) from e
    return {"backend": "cassandra", "rows": int(n)}
