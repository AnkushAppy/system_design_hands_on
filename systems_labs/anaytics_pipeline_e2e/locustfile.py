from __future__ import annotations

import os
import random
import time
import uuid
from typing import Any

from locust import FastHttpUser, between, task


def _now_ms() -> int:
    return int(time.time() * 1000)


def _rand_user_id() -> str:
    # A stable-ish distribution of user ids helps exercise partitioning keys.
    # Tune USER_POOL_SIZE to simulate more unique users.
    pool = int(os.environ.get("USER_POOL_SIZE", "5000"))
    return f"user{random.randint(1, pool)}"


PAGES = ["/", "/home", "/products", "/pricing", "/docs", "/cart", "/checkout", "/about"]
DEVICE_TYPES = ["mobile", "desktop", "tablet"]
EVENT_TYPES = ["click", "view", "purchase", "signup", "search"]


def _build_event(event_type: str, user_id: str) -> dict[str, Any]:
    base: dict[str, Any] = {
        "event_type": event_type,
        "user_id": user_id,
        "data": {
            "event_id": str(uuid.uuid4()),
            "ts_ms": _now_ms(),
            "page": random.choice(PAGES),
            "device": random.choice(DEVICE_TYPES),
        },
    }
    if event_type == "purchase":
        base["data"].update(
            {
                "amount": round(random.uniform(5, 250), 2),
                "currency": "USD",
                "items": random.randint(1, 6),
            }
        )
    if event_type == "search":
        base["data"].update({"q": random.choice(["shoes", "laptop", "book", "headphones", "chair"])})
    return base


class AnalyticsWriteUser(FastHttpUser):
    """
    Load test the producer API (`/track`).

    Run example:
      locust -f locustfile.py --host http://localhost:8010 -u 200 -r 20 -t 2m
    """

    wait_time = between(0.01, 0.2)

    @task(70)
    def track_click(self) -> None:
        self._track("click")

    @task(25)
    def track_view(self) -> None:
        self._track("view")

    @task(5)
    def track_purchase(self) -> None:
        self._track("purchase")

    def _track(self, event_type: str) -> None:
        payload = _build_event(event_type, _rand_user_id())
        with self.client.post("/track", json=payload, name="POST /track", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"unexpected status={resp.status_code} body={resp.text[:300]}")
                return
            try:
                body = resp.json()
            except Exception:
                resp.failure("non-json response")
                return
            if body.get("status") != "accepted":
                resp.failure(f"unexpected response: {body}")


class AnalyticsReadUser(FastHttpUser):
    """
    Optional: a smaller read workload against the consumer API.

    Run example:
      locust -f locustfile.py --host http://localhost:8011 -u 20 -r 2 -t 2m AnalyticsReadUser
    """

    wait_time = between(0.2, 1.2)

    @task(3)
    def counts(self) -> None:
        self.client.get("/counts", name="GET /counts")

    @task(1)
    def recent_events(self) -> None:
        limit = random.choice([10, 25, 50, 100])
        self.client.get(f"/events?limit={limit}", name="GET /events")

