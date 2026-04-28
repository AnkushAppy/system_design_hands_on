#!/usr/bin/env python3
"""Read records from orders_dlq."""

import json
import sys

try:
    from kafka import KafkaConsumer
except ImportError:
    print("pip install kafka-python")
    sys.exit(1)


def main() -> None:
    consumer = KafkaConsumer(
        "orders_dlq",
        bootstrap_servers=["localhost:9092"],
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        consumer_timeout_ms=5000,
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")) if v else {},
    )

    count = 0
    for msg in consumer:
        count += 1
        print(
            f"dlq#{count} key={msg.key} p={msg.partition} off={msg.offset} "
            f"error={msg.value.get('error')} raw={msg.value.get('raw_value')}"
        )
    consumer.close()
    print(f"Total DLQ messages: {count}")


if __name__ == "__main__":
    main()
