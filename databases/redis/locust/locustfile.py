"""
Stress profile for Redis: many unique keys, large values, minimal think time.
Tune PAYLOAD_{MIN,MAX}_KB via env. Requires stack: docker compose up -d
"""
import os
import random
import string

from locust import HttpUser, between, task

HOST = os.environ.get("TARGET_HOST", "http://load-balancer:80")

# Size of JSON "blob" per session write (keeps in Redis for TTL sec from API)
PAYLOAD_MIN_KB = int(os.environ.get("PAYLOAD_MIN_KB", "2"))
PAYLOAD_MAX_KB = int(os.environ.get("PAYLOAD_MAX_KB", "32"))


def _rand_id(n: int = 10) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def _blob_kb(kb: int) -> str:
    return "x" * (max(1, kb) * 1024)


class RedisApiUser(HttpUser):
    host = HOST
    # Almost no think time so we can hammer Redis
    wait_time = between(0, 0.02)

    @task(1)
    def get_health(self):
        self.client.get("/health", name="GET /health")

    @task(2)
    def get_counter(self):
        self.client.get("/api/counter?name=locust", name="GET /api/counter")

    @task(4)
    def post_counter(self):
        step = random.randint(1, 50)
        self.client.post(
            f"/api/counter?name=locust&step={step}",
            name="POST /api/counter",
        )

    @task(6)
    def session_flow(self):
        sid = _rand_id()
        kb = random.randint(PAYLOAD_MIN_KB, PAYLOAD_MAX_KB)
        self.client.put(
            f"/api/session/{sid}",
            json={
                "user": f"u-{sid}",
                "score": random.randint(0, 10_000),
                "blob": _blob_kb(kb),
            },
            name="PUT /api/session (medium)",
        )
        self.client.get(f"/api/session/{sid}", name="GET /api/session")

    @task(14)
    def session_flood_large(self):
        """New key every time + large value — fastest way to fill small maxmemory."""
        sid = _rand_id(16)
        kb = random.randint(PAYLOAD_MIN_KB, PAYLOAD_MAX_KB)
        self.client.put(
            f"/api/session/{sid}",
            json={
                "b": _blob_kb(kb),
                "i": _rand_id(8),
            },
            name="PUT /api/session (flood large)",
        )

    @task(10)
    def write_only_flood(self):
        """Writes only: maximizes new keys / second (skip GET to pressure SET path)."""
        sid = _rand_id(20)
        kb = random.randint(max(PAYLOAD_MIN_KB, 4), PAYLOAD_MAX_KB)
        self.client.put(
            f"/api/session/{sid}",
            json={"b": _blob_kb(kb)},
            name="PUT /api/session (write-only)",
        )
