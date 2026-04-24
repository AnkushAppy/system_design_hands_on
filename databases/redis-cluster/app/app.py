import json
import os
import time

import redis
from redis.cluster import ClusterNode, RedisCluster
from fastapi import Body, FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

INSTANCE = os.environ.get("APP_INSTANCE", "unknown")

# Comma-separated host:port for initial discovery (all 6 nodes recommended).
_NODES_ENV = os.environ.get(
    "REDIS_CLUSTER_NODES",
    "redis-1:6379,redis-2:6379,redis-3:6379,redis-4:6379,redis-5:6379,redis-6:6379",
)


def _cluster_client() -> RedisCluster:
    startup: list[ClusterNode] = []
    for part in _NODES_ENV.split(","):
        part = part.strip()
        if not part:
            continue
        host, _, port = part.partition(":")
        startup.append(ClusterNode(host, int(port or "6379")))
    if not startup:
        raise RuntimeError("REDIS_CLUSTER_NODES is empty")
    return RedisCluster(
        startup_nodes=startup,
        decode_responses=True,
        read_from_replicas=False,
    )


r = _cluster_client()

app = FastAPI(title="redis-cluster-lb-demo")

http_requests = Counter(
    "http_requests_total",
    "HTTP requests by path and method",
    ["method", "path", "status"],
)
http_latency = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)
redis_ops = Counter("redis_ops_total", "Redis operations", ["op", "result"])


def _metric_path(p: str) -> str:
    if p.startswith("/api/session/"):
        return "/api/session/{sid}"
    return p


@app.middleware("http")
async def metrics_middleware(request, call_next):
    path = _metric_path(request.url.path)
    if request.url.path == "/metrics":
        return await call_next(request)
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        http_requests.labels(request.method, path, "500").inc()
        raise
    dur = time.perf_counter() - start
    http_requests.labels(request.method, path, str(response.status_code)).inc()
    http_latency.labels(request.method, path).observe(dur)
    return response


@app.get("/health")
def health():
    return {"status": "ok", "instance": INSTANCE, "redis": "cluster"}


@app.get("/api/counter")
def get_counter(name: str = "demo"):
    try:
        val = r.get(name)
        redis_ops.labels("get", "ok").inc()
    except redis.RedisError as e:
        redis_ops.labels("get", "error").inc()
        raise HTTPException(status_code=503, detail=str(e)) from e
    return {"name": name, "value": int(val) if val is not None else 0, "instance": INSTANCE}


@app.post("/api/counter")
def incr_counter(name: str = "demo", step: int = 1):
    if step < 1 or step > 1000:
        raise HTTPException(status_code=400, detail="step must be 1..1000")
    try:
        n = r.incrby(name, step)
        redis_ops.labels("incr", "ok").inc()
    except redis.RedisError as e:
        redis_ops.labels("incr", "error").inc()
        raise HTTPException(status_code=503, detail=str(e)) from e
    return {"name": name, "value": n, "instance": INSTANCE}


@app.get("/api/session/{sid}")
def session_lookup(sid: str):
    key = f"session:{sid}"
    try:
        val = r.get(key)
        redis_ops.labels("get", "ok").inc()
    except redis.RedisError as e:
        redis_ops.labels("get", "error").inc()
        raise HTTPException(status_code=503, detail=str(e)) from e
    return {"sid": sid, "data": val, "instance": INSTANCE}


@app.put("/api/session/{sid}")
def session_store(sid: str, body: dict = Body(...)):
    key = f"session:{sid}"
    try:
        r.setex(key, 3600, json.dumps(body))
        redis_ops.labels("setex", "ok").inc()
    except redis.RedisError as e:
        redis_ops.labels("setex", "error").inc()
        raise HTTPException(status_code=503, detail=str(e)) from e
    return {"sid": sid, "ttl_sec": 3600, "instance": INSTANCE}


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
