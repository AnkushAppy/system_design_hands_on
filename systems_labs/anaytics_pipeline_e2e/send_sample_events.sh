#!/usr/bin/env bash
set -euo pipefail

BASE="${PRODUCER_URL:-http://localhost:8010}"

curl -sS -X POST "${BASE}/track" -H "Content-Type: application/json" \
  -d '{"event_type": "click", "user_id": "user123", "data": {"page": "/home"}}'
echo
curl -sS -X POST "${BASE}/track" -H "Content-Type: application/json" \
  -d '{"event_type": "click", "user_id": "user456", "data": {"page": "/products"}}'
echo
curl -sS -X POST "${BASE}/track" -H "Content-Type: application/json" \
  -d '{"event_type": "view", "user_id": "user123", "data": {"page": "/about"}}'
echo
curl -sS -X POST "${BASE}/track" -H "Content-Type: application/json" \
  -d '{"event_type": "click", "user_id": "user789", "data": {"page": "/cart"}}'
echo
curl -sS -X POST "${BASE}/track" -H "Content-Type: application/json" \
  -d '{"event_type": "purchase", "user_id": "user123", "data": {"amount": 50.0}}'
echo

