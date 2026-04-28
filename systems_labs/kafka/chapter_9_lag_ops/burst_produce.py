#!/usr/bin/env python3
"""Push many messages quickly to build lag when consumers are slower than producers."""

import sys
import time

try:
    from kafka import KafkaProducer
except ImportError:
    print("pip install kafka-python")
    sys.exit(1)

TOPIC = "lag_demo"
BOOTSTRAP = ["localhost:9092"]


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        value_serializer=lambda v: v.encode("utf-8"),
        batch_size=16384,
        linger_ms=5,
    )
    print(f"Pushing {count} messages to {TOPIC} ...")
    t0 = time.time()
    for i in range(count):
        key = f"p{i % 16}"
        producer.send(TOPIC, key=key, value=f"payload_{i}")
        if i > 0 and i % 2000 == 0:
            print(f"  ... {i} sent")
    producer.flush()
    producer.close()
    dt = time.time() - t0
    print(f"Done in {dt:.2f}s (~{count / dt:.0f} msg/s).")


if __name__ == "__main__":
    main()
