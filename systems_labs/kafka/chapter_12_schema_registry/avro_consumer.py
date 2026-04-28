#!/usr/bin/env python3
"""Read Avro-encoded messages using the Schema Registry (same schema subject as producer)."""

import sys

from confluent_kafka import DeserializingConsumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import StringDeserializer

SCHEMA_STR = """{
  "doc": "User profile demo",
  "name": "UserProfile",
  "namespace": "examples",
  "type": "record",
  "fields": [
    { "name": "name", "type": "string" },
    { "name": "department", "type": "string" }
  ]
}"""

BOOTSTRAP = "localhost:9092"
SR_URL = "http://localhost:8081"
TOPIC = "registered_users"


def main():
    registry = SchemaRegistryClient({"url": SR_URL})
    avro_deserializer = AvroDeserializer(registry, SCHEMA_STR)

    consumer = DeserializingConsumer(
        {
            "bootstrap.servers": BOOTSTRAP,
            "group.id": "registered-users-demo",
            "auto.offset.reset": "earliest",
            "key.deserializer": StringDeserializer("utf_8"),
            "value.deserializer": avro_deserializer,
        }
    )

    consumer.subscribe([TOPIC])

    print(f"Polling {TOPIC} — Ctrl+C to stop.\n")
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            err = msg.error()
            if err is not None:
                print(f"Consumer error: {err}")
                continue
            print(
                f"key={msg.key()} value={msg.value()} partition={msg.partition()} "
                f"offset={msg.offset()}"
            )
    except KeyboardInterrupt:
        sys.stdout.write("\nClosing consumer.\n")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
