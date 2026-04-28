#!/usr/bin/env python3
"""
Run one consumer in a shared consumer group.

Open TWO terminals with the SAME --group-id. Each member gets a disjoint subset
of partitions (rebalancing happens when members join / leave).

Example:
  Terminal A: python consumer_in_group.py --group-id demo-workers --member A
  Terminal B: python consumer_in_group.py --group-id demo-workers --member B
"""

import argparse
import sys

try:
    from kafka import KafkaConsumer
except ImportError:
    print("pip install kafka-python")
    sys.exit(1)

try:
    from kafka import ConsumerRebalanceListener
except ImportError:
    from kafka.consumer.subscription_state import ConsumerRebalanceListener


class Listener(ConsumerRebalanceListener):
    """Print partition assignments on rebalance."""

    def __init__(self, member_name: str):
        self.member = member_name

    def on_partitions_revoked(self, revoked):
        if revoked:
            print(f"[{self.member}] revoked: {[p.partition for p in revoked]}")

    def on_partitions_assigned(self, assigned):
        if assigned:
            parts = [f"{p.partition}" for p in assigned]
            print(f"[{self.member}] assigned partitions: {', '.join(parts)}")
        else:
            print(f"[{self.member}] assigned partitions: (none)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--group-id", default="demo-workers")
    parser.add_argument("--member", default="worker1")
    parser.add_argument("--topic", default="orders")
    parser.add_argument(
        "--from",
        dest="reset",
        choices=["earliest", "latest"],
        default="earliest",
        help="auto.offset.reset when no committed offset exists",
    )
    args = parser.parse_args()

    listener = Listener(args.member)
    consumer = KafkaConsumer(
        args.topic,
        bootstrap_servers=["localhost:9092"],
        group_id=args.group_id,
        enable_auto_commit=True,
        auto_offset_reset=args.reset,
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        value_deserializer=lambda v: v.decode("utf-8") if v else None,
    )
    consumer.subscribe([args.topic], listener=listener)

    member = args.member
    print(f"[{member}] group={args.group_id} topic={args.topic} — polling (Ctrl+C to stop)\n")

    try:
        for msg in consumer:
            val = msg.value or ""
            snippet = val if len(val) <= 72 else val[:72] + "..."
            print(f"[{member}] p={msg.partition} off={msg.offset} key={msg.key} value={snippet}")
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
