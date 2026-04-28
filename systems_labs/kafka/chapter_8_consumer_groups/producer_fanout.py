#!/usr/bin/env python3
"""
Produce keyed messages so they spread across partitions.
Run after setup_topic.py and with Kafka up.
"""

import sys
import time

try:
    from kafka import KafkaProducer
except ImportError:
    print("pip install kafka-python")
    sys.exit(1)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    topic = "orders"
    producer = KafkaProducer(
        bootstrap_servers=["localhost:9092"],
        key_serializer=lambda k: k.encode("utf-8"),
        value_serializer=lambda v: v.encode("utf-8"),
    )

    print(f"Producing {n} messages to '{topic}' (keys user_0..user_7 for spread)...")
    for i in range(n):
        key = f"user_{i % 8}"
        value = f"order_{i}:item_{i % 100}"
        r = producer.send(topic, key=key, value=value).get(timeout=10)
        if i % 10 == 0 or i == n - 1:
            print(f"  [{i}] key={key} partition={r.partition} offset={r.offset}")
        time.sleep(0.03)

    producer.flush()
    producer.close()
    print("Done.")


if __name__ == "__main__":
    main()
