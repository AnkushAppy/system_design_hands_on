#!/bin/bash
# Script to demonstrate fault tolerance with acks=all
# This kills a broker mid-stream while messages are being produced
#
# Run from anywhere: script cds to its directory.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

bootstrap_inside_broker() {
  case "$1" in
    1) echo "localhost:9092" ;;
    2) echo "localhost:9093" ;;
    3) echo "localhost:9094" ;;
    *) echo "localhost:9092" ;;
  esac
}

echo "============================================"
echo "Kafka Fault Tolerance Test"
echo "============================================"
echo ""
echo "Scenario:"
echo "  3 brokers, replication factor = 3"
echo "  acks = all (wait for all in-sync replicas)"
echo "  min.insync.replicas = 2"
echo ""
echo "What happens when we kill a broker?"
echo "============================================"
echo ""

# Wait for cluster to be ready
echo "Waiting for Kafka cluster to be ready..."
sleep 5

for i in 1 2 3; do
  echo -n "  Broker $i: "
  bs="$(bootstrap_inside_broker "$i")"
  if docker exec "broker-$i" kafka-broker-api-versions --bootstrap-server "$bs" > /dev/null 2>&1; then
    echo "✓ UP"
  else
    echo "✗ DOWN or not ready"
  fi
done

echo ""
echo "Starting producer in background with acks=all..."
echo ""

# Start producer in background
python3 producer_experiment.py all 30 &
PRODUCER_PID=$!

# Let it run for a few seconds before killing a broker
sleep 5

echo ""
echo "============================================"
echo "KILLING BROKER-2 MID-STREAM..."
echo "============================================"
echo ""

docker kill broker-2

echo "Broker-2 killed! Waiting 5 seconds..."
sleep 5

echo ""
echo "Current broker status:"
for i in 1 2 3; do
  echo -n "  Broker $i: "
  bs="$(bootstrap_inside_broker "$i")"
  if docker exec "broker-$i" kafka-broker-api-versions --bootstrap-server "$bs" > /dev/null 2>&1; then
    echo "✓ UP"
  else
    echo "✗ DOWN (expected for broker-2)"
  fi
done

echo ""
echo "Waiting for producer to finish sending all messages..."
wait $PRODUCER_PID 2>/dev/null || true

echo ""
echo "============================================"
echo "RESULTS"
echo "============================================"
echo ""
echo "With acks=all and min.insync.replicas=2:"
echo "  ✓ Messages are ONLY acknowledged after"
echo "    reaching ALL in-sync replicas"
echo "  ✓ Cluster can lose 1 broker and still"
echo "    accept writes without data loss"
echo "  ✓ The producer automatically retries"
echo "    and finds the remaining brokers"
echo ""

echo "============================================"
echo "Cleaning up - restarting broker-2..."
echo "============================================"
docker start broker-2
echo "Broker-2 restarted."
echo ""
