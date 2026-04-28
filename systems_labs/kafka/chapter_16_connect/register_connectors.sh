#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8083}"

mkdir -p ./connect-data
cat > ./connect-data/source.txt <<'EOF'
alpha
beta
gamma
delta
EOF

echo "Registering FileStreamSource connector..."
curl -s -X POST "${BASE_URL}/connectors" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "file-source-demo",
    "config": {
      "connector.class": "org.apache.kafka.connect.file.FileStreamSourceConnector",
      "tasks.max": "1",
      "file": "/tmp/connect-data/source.txt",
      "topic": "connect_file_demo",
      "key.converter": "org.apache.kafka.connect.storage.StringConverter",
      "value.converter": "org.apache.kafka.connect.storage.StringConverter"
    }
  }' || true
echo

echo "Registering FileStreamSink connector..."
curl -s -X POST "${BASE_URL}/connectors" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "file-sink-demo",
    "config": {
      "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
      "tasks.max": "1",
      "topics": "connect_file_demo",
      "file": "/tmp/connect-data/sink.txt",
      "key.converter": "org.apache.kafka.connect.storage.StringConverter",
      "value.converter": "org.apache.kafka.connect.storage.StringConverter"
    }
  }' || true
echo

echo "Current connectors:"
curl -s "${BASE_URL}/connectors"
echo
echo "Done. Inspect sink file:"
echo "  cat ./connect-data/sink.txt"
