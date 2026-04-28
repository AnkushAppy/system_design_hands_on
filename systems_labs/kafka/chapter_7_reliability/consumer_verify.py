#!/usr/bin/env python3
"""
Kafka Consumer - Verify Messages Were Not Lost

After running the producer_experiment.py, use this to read back
all messages from the topic and verify nothing was lost.

Usage:
  python consumer_verify.py              # print count only
  python consumer_verify.py 50           # exit 0 iff topic has exactly 50 messages

Use a fresh cluster (or new topic) before comparing counts; this reads from
earliest and includes every message ever written to the topic.
"""

import sys
from typing import Optional

from kafka import KafkaConsumer

def consume_and_verify(expected: Optional[int] = None):
    """Consume all messages and count them."""
    
    print("\n" + "="*60)
    print("VERIFYING MESSAGES - Consumer")
    print("="*60 + "\n")
    
    consumer = KafkaConsumer(
        'orders',
        bootstrap_servers=['localhost:9092', 'localhost:9093', 'localhost:9094'],
        auto_offset_reset='earliest',  # Read from the beginning
        enable_auto_commit=True,
        consumer_timeout_ms=5000,  # Stop after 5 seconds of no messages
        key_deserializer=lambda k: k.decode('utf-8') if k else None,
        value_deserializer=lambda v: v.decode('utf-8') if v else None,
    )
    
    print("Reading messages from topic 'orders'...\n")
    
    messages = []
    try:
        for message in consumer:
            messages.append(message)
            print(f"  Partition {message.partition:2d} | Offset {message.offset:4d} | "
                  f"{message.key:12s} | {message.value}")
    except Exception:
        # Timeout reached - no more messages
        pass
    
    consumer.close()
    
    print(f"\n{'─'*60}")
    print(f"Total messages consumed: {len(messages)}")
    print(f"{'─'*60}")
    
    # Show per-partition counts
    partitions = {}
    for msg in messages:
        p = msg.partition
        partitions[p] = partitions.get(p, 0) + 1
    
    print(f"\nMessages per partition:")
    for p in sorted(partitions.keys()):
        print(f"  Partition {p}: {partitions[p]} messages")
    
    n = len(messages)
    if expected is not None:
        print(f"\nExpected (from producer run): {expected}")
        if n == expected:
            print("Match: no discrepancy for this check.")
        else:
            print(f"MISMATCH: topic has {n} messages, expected {expected}.")
            sys.exit(1)
    else:
        print("\nTip: pass expected count to assert, e.g. python consumer_verify.py 50")
        print(f"Actual messages in topic (from earliest): {n}\n")

    return n

if __name__ == "__main__":
    expected_count = int(sys.argv[1]) if len(sys.argv) > 1 else None
    consume_and_verify(expected=expected_count)
