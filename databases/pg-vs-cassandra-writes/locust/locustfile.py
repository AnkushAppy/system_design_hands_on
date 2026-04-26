"""
Write stress: alternate explicit paths /pg/events vs /cassandra/events.
From host: TARGET_HOST=http://127.0.0.1:8280
"""
import json
import os
import random
import string

from locust import HttpUser, between, task

HOST = os.environ.get("TARGET_HOST", "http://api:8000")


def _rand_bucket() -> str:
    return "b-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))


def _payload() -> dict:
    return {
        "k": random.randint(0, 1_000_000),
        "s": "".join(random.choices(string.ascii_letters, k=64)),
    }


class WriteHeavyUser(HttpUser):
    host = HOST
    wait_time = between(0, 0.02)

    @task(1)
    def health(self):
        self.client.get("/health", name="GET /health")

    @task(5)
    def write_pg(self):
        self.client.post(
            "/pg/events",
            json={"bucket": _rand_bucket(), "payload": _payload()},
            name="POST /pg/events",
        )

    @task(5)
    def write_cassandra(self):
        self.client.post(
            "/cassandra/events",
            json={"bucket": _rand_bucket(), "payload": _payload()},
            name="POST /cassandra/events",
        )
