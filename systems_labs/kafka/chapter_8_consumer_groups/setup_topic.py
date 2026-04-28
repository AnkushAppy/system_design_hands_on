#!/usr/bin/env python3
"""Create the demo topic with multiple partitions (consumer groups divide partitions across members)."""

import sys

try:
    from kafka.admin import KafkaAdminClient, NewTopic
    from kafka.errors import TopicAlreadyExistsError
except ImportError:
    print("Install kafka-python: pip install kafka-python")
    sys.exit(1)


def main():
    bootstrap = ["localhost:9092"]
    topic_name = "orders"
    partitions = 4
    rf = 1

    admin = KafkaAdminClient(bootstrap_servers=bootstrap)
    topic = NewTopic(
        name=topic_name,
        num_partitions=partitions,
        replication_factor=rf,
    )
    try:
        admin.create_topics([topic])
        print(f"Created topic '{topic_name}' ({partitions} partitions, rf={rf}).")
    except TopicAlreadyExistsError:
        print(f"Topic '{topic_name}' already exists (ok).")
    admin.close()


if __name__ == "__main__":
    main()
