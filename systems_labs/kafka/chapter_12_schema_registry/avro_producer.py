#!/usr/bin/env python3
"""Produce Avro payloads with Schema Registry (subject auto-registered per topic/value)."""

from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import SerializationContext, StringSerializer

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


def user_as_record(user: dict, ctx: SerializationContext) -> dict:
    """Avro serializer hook: passthrough dict shaped like the schema."""
    return user


def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed: {err}")


def main():
    registry = SchemaRegistryClient({"url": SR_URL})
    avro_serializer = AvroSerializer(registry, SCHEMA_STR, user_as_record)

    producer = SerializingProducer(
        {
            "bootstrap.servers": BOOTSTRAP,
            "key.serializer": StringSerializer("utf_8"),
            "value.serializer": avro_serializer,
        }
    )

    payloads = [
        {"name": "Ada", "department": "Engineering"},
        {"name": "Linus", "department": "Kernel"},
        {"name": "Edsger", "department": "Theory"},
    ]

    print(f"Publishing {len(payloads)} Avro records to {TOPIC} ...")
    for body in payloads:
        producer.poll(0)
        producer.produce(
            topic=TOPIC,
            key=str(body["name"]).lower(),
            value=body,
            on_delivery=delivery_report,
        )
    producer.flush()
    print("Done. Inspect subjects: curl http://localhost:8081/subjects")


if __name__ == "__main__":
    main()
