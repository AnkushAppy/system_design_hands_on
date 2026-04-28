#!/usr/bin/env python3
import sys

try:
    from kafka.admin import KafkaAdminClient, NewTopic
    from kafka.errors import TopicAlreadyExistsError
except ImportError:
    print("pip install kafka-python")
    sys.exit(1)


def main():
    admin = KafkaAdminClient(bootstrap_servers=["localhost:9092"])
    t = NewTopic(name="lag_demo", num_partitions=4, replication_factor=1)
    try:
        admin.create_topics([t])
        print("Created topic lag_demo (4 partitions).")
    except TopicAlreadyExistsError:
        print("Topic lag_demo already exists.")
    admin.close()


if __name__ == "__main__":
    main()
