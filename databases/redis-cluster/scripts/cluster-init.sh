#!/bin/sh
# Form a 3-master / 3-replica Redis Cluster once all nodes answer PING.
# Idempotent: if cluster_state is already ok, exit 0.
set -eu

INSTANCES="172.29.0.11:6379 172.29.0.12:6379 172.29.0.13:6379 172.29.0.14:6379 172.29.0.15:6379 172.29.0.16:6379"

echo "Waiting for Redis nodes..."
i=0
while [ "$i" -lt 60 ]; do
  ok=1
  for h in $INSTANCES; do
    host="${h%:*}"
    port="${h#*:}"
    if ! redis-cli -h "$host" -p "$port" ping | grep -q PONG; then
      ok=0
      break
    fi
  done
  if [ "$ok" -eq 1 ]; then
    break
  fi
  i=$((i + 1))
  sleep 1
done

if ! redis-cli -h 172.29.0.11 -p 6379 ping | grep -q PONG; then
  echo "Redis nodes did not become reachable in time" >&2
  exit 1
fi

if redis-cli -h 172.29.0.11 -p 6379 cluster info 2>/dev/null | grep -q "cluster_state:ok"; then
  echo "Cluster already initialized (cluster_state:ok)."
  exit 0
fi

echo "Creating cluster (3 masters, 1 replica each)..."
redis-cli --cluster create $INSTANCES --cluster-replicas 1 --cluster-yes

redis-cli -h 172.29.0.11 -p 6379 cluster info
