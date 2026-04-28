#!/usr/bin/env bash
set -euo pipefail

KSQL_URL="${KSQL_URL:-http://localhost:8088}"

STATEMENTS=$(cat <<'EOF'
CREATE STREAM IF NOT EXISTS clicks_stream (
  user_id VARCHAR,
  page VARCHAR,
  ts BIGINT,
  event_id BIGINT
) WITH (
  KAFKA_TOPIC='clicks_raw',
  VALUE_FORMAT='JSON',
  PARTITIONS=3
);

CREATE TABLE IF NOT EXISTS clicks_per_user AS
SELECT user_id, COUNT(*) AS cnt
FROM clicks_stream
GROUP BY user_id
EMIT CHANGES;
EOF
)

curl -s -X POST "${KSQL_URL}/ksql" \
  -H "Content-Type: application/vnd.ksql.v1+json; charset=utf-8" \
  -d "{\"ksql\":\"${STATEMENTS//$'\n'/ }\",\"streamsProperties\":{}}"
echo
echo "Pipeline created. Output table changelog topic: CLICKS_PER_USER."
