#!/usr/bin/env python3
"""
Kafka Producer Script
Produces messages to a Kafka topic and then helps inspect
where the .log and .index files live inside the container.
"""

import sys

# Try importing kafka-python - install via: pip install kafka-python
try:
    from kafka import KafkaProducer
except ImportError:
    print("kafka-python not installed. Install with: pip install kafka-python")
    sys.exit(1)

def produce_messages():
    print("Connecting to Kafka at localhost:9092...")
    producer = KafkaProducer(
        bootstrap_servers=['localhost:9092'],
        key_serializer=lambda k: k.encode('utf-8') if k else None,
        value_serializer=lambda v: v.encode('utf-8') if v else None
    )

    topic = "orders"
    messages = [
        ("user_1", "order_101:apple"),
        ("user_2", "order_102:banana"),
        ("user_1", "order_103:cherry"),
        ("user_3", "order_104:date"),
        ("user_2", "order_105:elderberry"),
    ]

    print(f"Producing {len(messages)} messages to topic '{topic}'...")
    for key, value in messages:
        future = producer.send(topic, key=key, value=value)
        result = future.get(timeout=10)
        print(f"  Produced: key={key}, value={value} -> partition={result.partition}, offset={result.offset}")

    producer.flush()
    producer.close()
    print("\nAll messages produced successfully!")
    print("\nNow run inside the container to inspect files:")
    print("  docker exec -it kafka bash")
    print("  cd /tmp/kraft-combined-logs")
    print("  ls -la")
    print("  strings 00000000000000000000.log | head -20")

if __name__ == "__main__":
    produce_messages()