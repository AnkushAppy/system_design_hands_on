#!/usr/bin/env bash
# Describe consumer group offsets and compute lag (TOTAL-LAG columns from broker).
set -euo pipefail

CONTAINER="${KAFKA_CONTAINER:-kafka-ch9}"
GROUP="${GROUP_ID:-lag-demo-group}"

docker exec "${CONTAINER}" kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group "${GROUP}"
