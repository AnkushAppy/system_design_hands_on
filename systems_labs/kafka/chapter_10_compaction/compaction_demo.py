#!/usr/bin/env python3
"""
Create a compacted topic and produce multiple versions per key.

With cleanup.policy=compact, Kafka's log cleaner eventually retains only the
latest record per key (plus tombstones if you delete keys). Immediately after
producing you still usually see full history until segments roll/compaction runs.

Reads from the beginning print the story: many updates for the same key.
"""

import sys
import time

try:
    from kafka import KafkaConsumer, KafkaProducer
    from kafka.admin import KafkaAdminClient, NewTopic
    from kafka.errors import TopicAlreadyExistsError
except ImportError:
    print("pip install kafka-python")
    sys.exit(1)

BOOTSTRAP = ["localhost:9092"]
TOPIC = "user_state"


def ensure_topic():
    admin = KafkaAdminClient(bootstrap_servers=BOOTSTRAP)
    t = NewTopic(
        name=TOPIC,
        num_partitions=1,
        replication_factor=1,
        topic_configs={
            "cleanup.policy": "compact",
            # Speed up segmentation for demos (still may need time for cleaner)
            "segment.ms": "5000",
            "segment.bytes": "536870912",
            "delete.retention.ms": "86400000",
            "min.compaction.lag.ms": "0",
        },
    )
    try:
        admin.create_topics([t])
        print(f"Created compacted topic '{TOPIC}'.")
    except TopicAlreadyExistsError:
        print(f"Topic '{TOPIC}' already exists.")
    admin.close()


def produce_updates():
    p = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        key_serializer=lambda k: k.encode("utf-8"),
        value_serializer=lambda v: v.encode("utf-8"),
    )
    states = ["NY", "CA", "WA", "TX"]
    print("\nPublishing state updates for key 'user_acme' (same key → same partition)...")
    for i, region in enumerate(states):
        value = f"{{company: acme_legal_name, hq_region: {region}, version: {i}}}"
        r = p.send(TOPIC, key="user_acme", value=value).get(timeout=10)
        print(f"  sent v{i} region={region} -> offset={r.offset}")
        time.sleep(0.2)
    p.flush()
    p.close()

    print("\nPublishing one update for a different key on the same topic...")
    p2 = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        key_serializer=lambda k: k.encode("utf-8"),
        value_serializer=lambda v: v.encode("utf-8"),
    )
    r = p2.send(TOPIC, key="user_other", value=b"{company: other, hq_region: FL, version: 0}").get(
        timeout=10
    )
    print(f"  key=user_other offset={r.offset}")
    p2.flush()
    p2.close()


def read_all():
    c = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        consumer_timeout_ms=8000,
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        value_deserializer=lambda v: v.decode("utf-8") if v else None,
    )
    print("\nReading from earliest (what you see before/after compaction differs over time):")
    for msg in c:
        print(f"  key={msg.key} partition={msg.partition} offset={msg.offset} value={msg.value}")
    c.close()


def main():
    ensure_topic()
    produce_updates()
    read_all()
    print(
        "\nTip: In production, compaction runs in the background. Only the latest value per key\n"
        "remains in the compacted log (older versions for that key are dropped subject to config).\n"
        "Use this topic as a changelog / 'table of latest truth' pattern."
    )


if __name__ == "__main__":
    main()
