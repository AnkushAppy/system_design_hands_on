#!/usr/bin/env python3
"""
Ordering guarantees demo:

1) Same key + one producer -> per-key order is stable.
2) Same key + two producers -> records can interleave globally.
3) Different keys -> each key remains ordered, but no global order across keys.
"""

import argparse
import json
import sys
import threading
import time

try:
    from kafka import KafkaConsumer, KafkaProducer
    from kafka.admin import KafkaAdminClient, NewTopic
    from kafka.errors import TopicAlreadyExistsError
except ImportError:
    print("pip install kafka-python")
    sys.exit(1)

TOPIC = "ordering_demo"
BOOTSTRAP = ["localhost:9092"]


def ensure_topic(partitions: int) -> None:
    admin = KafkaAdminClient(bootstrap_servers=BOOTSTRAP)
    topic = NewTopic(name=TOPIC, num_partitions=partitions, replication_factor=1)
    try:
        admin.create_topics([topic])
        print(f"Created topic '{TOPIC}' with {partitions} partitions.")
    except TopicAlreadyExistsError:
        print(f"Topic '{TOPIC}' already exists.")
    finally:
        admin.close()


def build_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        key_serializer=lambda k: k.encode("utf-8"),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )


def produce_single(count: int, key: str) -> None:
    producer = build_producer()
    for seq in range(count):
        producer.send(TOPIC, key=key, value={"source": "single", "seq": seq, "key": key})
    producer.flush()
    producer.close()
    print(f"Produced {count} events with one producer and key='{key}'.")


def produce_dual(count_each: int, key: str) -> None:
    def worker(source: str) -> None:
        producer = build_producer()
        for seq in range(count_each):
            producer.send(TOPIC, key=key, value={"source": source, "seq": seq, "key": key})
            time.sleep(0.002)
        producer.flush()
        producer.close()

    a = threading.Thread(target=worker, args=("A",), daemon=True)
    b = threading.Thread(target=worker, args=("B",), daemon=True)
    a.start()
    b.start()
    a.join()
    b.join()
    print(f"Produced {count_each * 2} events from two producers for key='{key}'.")


def consume_and_report(timeout_ms: int) -> None:
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        consumer_timeout_ms=timeout_ms,
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")) if v else None,
    )

    by_key = {}
    by_source = {}

    for msg in consumer:
        key = msg.key
        data = msg.value or {}
        by_key.setdefault(key, []).append(data.get("seq"))
        src = data.get("source")
        by_source.setdefault((key, src), []).append(data.get("seq"))
        print(f"p={msg.partition} off={msg.offset} key={key} value={data}")

    consumer.close()

    print("\n--- ORDER REPORT ---")
    for key, seqs in by_key.items():
        global_monotonic = all(seqs[i] <= seqs[i + 1] for i in range(len(seqs) - 1))
        print(f"key={key}: {len(seqs)} records, global seq monotonic={global_monotonic}")
    for (key, src), seqs in by_source.items():
        source_monotonic = all(seqs[i] <= seqs[i + 1] for i in range(len(seqs) - 1))
        print(f"key={key}, source={src}: per-source monotonic={source_monotonic}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--partitions", type=int, default=3)
    parser.add_argument("--mode", choices=["single", "dual"], default="single")
    parser.add_argument("--key", default="account_42")
    parser.add_argument("--count", type=int, default=40, help="count per producer")
    parser.add_argument("--consume-timeout-ms", type=int, default=5000)
    args = parser.parse_args()

    ensure_topic(args.partitions)
    if args.mode == "single":
        produce_single(args.count, args.key)
    else:
        produce_dual(args.count, args.key)
    consume_and_report(args.consume_timeout_ms)


if __name__ == "__main__":
    main()
