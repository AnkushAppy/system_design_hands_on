#!/usr/bin/env python3
"""
Slow consumer in a fixed group. Pair with burst_produce.py and check_lag.sh.

Process messages deliberately slowly so TOTAL-LAG grows (consumer throughput < producer throughput).
"""

import argparse
import sys
import time

try:
    from kafka import KafkaConsumer
except ImportError:
    print("pip install kafka-python")
    sys.exit(1)

BOOTSTRAP = ["localhost:9092"]
GROUP = "lag-demo-group"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sleep-ms", type=float, default=50.0, help="pause after each message")
    parser.add_argument("--max-messages", type=int, default=0, help="stop after N messages (0 = run forever)")
    args = parser.parse_args()

    consumer = KafkaConsumer(
        "lag_demo",
        bootstrap_servers=BOOTSTRAP,
        group_id=GROUP,
        enable_auto_commit=True,
        auto_offset_reset="earliest",
        value_deserializer=lambda v: v.decode("utf-8"),
    )

    seen = 0
    print(
        f"Consuming slowly from lag_demo group={GROUP}. "
        f"sleep_ms={args.sleep_ms}. Ctrl+C to stop.\n"
    )
    try:
        for msg in consumer:
            seen += 1
            if seen % 100 == 0:
                print(f"  consumed {seen} msgs (partition={msg.partition} offset={msg.offset})")
            time.sleep(args.sleep_ms / 1000.0)
            if args.max_messages and seen >= args.max_messages:
                break
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
