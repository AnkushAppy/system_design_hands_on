#!/usr/bin/env python3
"""Produce JSON click events for ksqlDB stream processing."""

import json
import random
import sys
import time

try:
    from kafka import KafkaProducer
except ImportError:
    print("pip install kafka-python")
    sys.exit(1)


def main() -> None:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    users = ["alice", "bob", "charlie", "diana"]
    pages = ["/home", "/pricing", "/docs", "/blog"]

    producer = KafkaProducer(
        bootstrap_servers=["localhost:9092"],
        key_serializer=lambda k: k.encode("utf-8"),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print(f"Producing {count} click events to topic clicks_raw ...")
    for i in range(count):
        event = {
            "user_id": random.choice(users),
            "page": random.choice(pages),
            "ts": int(time.time() * 1000),
            "event_id": i,
        }
        producer.send("clicks_raw", key=event["user_id"], value=event)
        if i > 0 and i % 50 == 0:
            print(f"  ... {i} events sent")
        time.sleep(0.01)
    producer.flush()
    producer.close()
    print("Done.")


if __name__ == "__main__":
    main()
