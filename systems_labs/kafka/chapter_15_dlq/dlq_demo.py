#!/usr/bin/env python3
"""
Poison message + DLQ demo.

Modes:
- produce: publish a mix of valid and invalid payloads
- consume: process input topic, either skip invalid messages or route to DLQ
"""

import argparse
import json
import sys
from datetime import datetime, timezone

try:
    from kafka import KafkaConsumer, KafkaProducer
    from kafka.admin import KafkaAdminClient, NewTopic
    from kafka.errors import TopicAlreadyExistsError
except ImportError:
    print("pip install kafka-python")
    sys.exit(1)

BOOTSTRAP = ["localhost:9092"]
INPUT_TOPIC = "orders_in"
DLQ_TOPIC = "orders_dlq"


def ensure_topics() -> None:
    admin = KafkaAdminClient(bootstrap_servers=BOOTSTRAP)
    topics = [
        NewTopic(name=INPUT_TOPIC, num_partitions=3, replication_factor=1),
        NewTopic(name=DLQ_TOPIC, num_partitions=3, replication_factor=1),
    ]
    try:
        admin.create_topics(topics)
        print("Created topics orders_in and orders_dlq.")
    except TopicAlreadyExistsError:
        print("Topics already exist (ok).")
    finally:
        admin.close()


def produce_test_data() -> None:
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        value_serializer=lambda v: v.encode("utf-8"),
    )

    payloads = [
        ("ord-100", '{"order_id":"ord-100","amount":19.5,"currency":"USD"}'),
        ("ord-101", '{"order_id":"ord-101","amount":200.0,"currency":"USD"}'),
        ("ord-bad-json", '{"order_id":"ord-bad-json","amount":7.0'),  # malformed JSON
        ("ord-missing-amount", '{"order_id":"ord-missing-amount","currency":"USD"}'),
        ("ord-102", '{"order_id":"ord-102","amount":88.0,"currency":"USD"}'),
    ]

    for key, value in payloads:
        producer.send(INPUT_TOPIC, key=key, value=value)
        print(f"produced key={key} value={value}")
    producer.flush()
    producer.close()
    print("Produced sample input records.")


def validate_order(raw_value: str) -> dict:
    record = json.loads(raw_value)
    if "order_id" not in record:
        raise ValueError("missing required field: order_id")
    if "amount" not in record:
        raise ValueError("missing required field: amount")
    if not isinstance(record["amount"], (int, float)):
        raise ValueError("amount must be numeric")
    return record


def consume_and_handle(mode: str, max_messages: int) -> None:
    if mode not in {"skip", "dlq"}:
        raise ValueError("mode must be skip or dlq")

    consumer = KafkaConsumer(
        INPUT_TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id="orders-processor",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        value_deserializer=lambda v: v.decode("utf-8") if v else "",
    )
    dlq_producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    ok = 0
    failed = 0

    try:
        for msg in consumer:
            try:
                parsed = validate_order(msg.value)
                ok += 1
                print(f"ok key={msg.key} order_id={parsed['order_id']} amount={parsed['amount']}")
            except Exception as exc:
                failed += 1
                print(f"bad key={msg.key} reason={exc}")
                if mode == "dlq":
                    dlq_payload = {
                        "source_topic": msg.topic,
                        "source_partition": msg.partition,
                        "source_offset": msg.offset,
                        "source_key": msg.key,
                        "raw_value": msg.value,
                        "error": str(exc),
                        "failed_at_utc": datetime.now(timezone.utc).isoformat(),
                    }
                    dlq_producer.send(DLQ_TOPIC, key=msg.key, value=dlq_payload)
                    dlq_producer.flush()
                    print(f"  -> sent to DLQ topic={DLQ_TOPIC}")
                else:
                    print("  -> skipped (no DLQ)")

            if max_messages > 0 and (ok + failed) >= max_messages:
                break
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        consumer.close()
        dlq_producer.close()
        print(f"\nSummary: ok={ok}, failed={failed}, mode={mode}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["setup", "produce", "consume"], required=True)
    parser.add_argument("--mode", choices=["skip", "dlq"], default="dlq")
    parser.add_argument("--max-messages", type=int, default=0)
    args = parser.parse_args()

    if args.action == "setup":
        ensure_topics()
    elif args.action == "produce":
        produce_test_data()
    else:
        consume_and_handle(args.mode, args.max_messages)


if __name__ == "__main__":
    main()
