#!/usr/bin/env bash
set -euo pipefail

: "${YELLOW_API_URL:?Set YELLOW_API_URL to Yellow.ai's synchronous send-message endpoint}"
: "${YELLOW_BOT_ID:?Set YELLOW_BOT_ID to the bot ID}"

ITERATIONS="${ITERATIONS:-1}"
CONCURRENCY="${CONCURRENCY:-1}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${OUT:-results/yellow-smoke-v1-${STAMP}.jsonl}"

python -m pd_llm_eval.cli run-yellow datasets/smoke_v1 \
  --out "$OUT" \
  --iterations "$ITERATIONS" \
  --concurrency "$CONCURRENCY" \
  "$@"

echo "Saved: $OUT"
