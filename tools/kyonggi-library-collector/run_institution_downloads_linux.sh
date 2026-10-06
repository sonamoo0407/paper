#!/usr/bin/env bash
# Ubuntu launcher: enter credentials only in this visible terminal when prompted.
# Usage: ./run_institution_downloads_linux.sh "ransomware detection" 20
set -euo pipefail

QUERY="${1:-ransomware detection}"
LIMIT="${2:-20}"
OUT_ROOT="${3:-outputs}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

case "$LIMIT" in
  ''|*[!0-9]*) echo "LIMIT must be a positive whole number." >&2; exit 2 ;;
esac
if [ "$LIMIT" -lt 1 ]; then
  echo "LIMIT must be a positive whole number." >&2
  exit 2
fi

"$PYTHON_BIN" kyonggi_collector.py collect \
  --mode browser \
  --auto-login \
  --query "$QUERY" \
  --max-records "$LIMIT" \
  --max-pages "$(( (LIMIT + 9) / 10 ))" \
  --output-dir "$OUT_ROOT"

RUN_DIR="$OUT_ROOT/$(find "$OUT_ROOT" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort | tail -n 1)"
RECORDS="$RUN_DIR/records.jsonl"
if [ ! -f "$RECORDS" ]; then
  echo "Could not locate the records ledger after collection." >&2
  exit 1
fi

"$PYTHON_BIN" kyonggi_collector.py auto-downloads \
  --records "$RECORDS" \
  --output-dir "$RUN_DIR/institution-auto-downloads" \
  --max-records "$LIMIT" \
  --priority top-tier
