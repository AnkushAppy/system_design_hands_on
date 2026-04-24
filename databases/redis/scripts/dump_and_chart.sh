#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PROMETHEUS_URL="${PROMETHEUS_URL:-http://127.0.0.1:9090}"
python3 "$ROOT/scripts/export_metrics.py"
python3 "$ROOT/scripts/display_charts.py"
echo "Exports: $ROOT/metrics/exports/latest.json"
echo "Charts:  $ROOT/metrics/charts/*.svg"
