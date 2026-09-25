#!/usr/bin/env bash
set -euo pipefail

: "${MODELS:?Set MODELS to comma-separated OpenCode model IDs, e.g. provider/model,provider/model2}"

DATASET="${DATASET:-datasets/smoke_v1/cases.json}"
MODE="${MODE:-oracle}"
ITERATIONS="${ITERATIONS:-1}"
CONCURRENCY="${CONCURRENCY:-1}"
LIMIT="${LIMIT:-}"
JUDGE_MODEL="${JUDGE_MODEL:-}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

IFS="," read -r -a MODEL_ARRAY <<< "$MODELS"

for model in "${MODEL_ARRAY[@]}"; do
  slug="${model//\//-}"
  slug="${slug//:/-}"
  out="results/opencode-${slug}-${MODE}-${STAMP}.jsonl"

  args=(pd-eval run-opencode "$DATASET" --model "$model" --mode "$MODE" --out "$out" --iterations "$ITERATIONS" --concurrency "$CONCURRENCY")
  if [[ -n "$LIMIT" ]]; then args+=(--limit "$LIMIT"); fi

  echo "Running $model -> $out"
  "${args[@]}"

  if [[ -n "$JUDGE_MODEL" ]]; then
    judged="results/opencode-${slug}-${MODE}-${STAMP}-judged.jsonl"
    judge_args=(pd-eval judge-opencode "$DATASET" "$out" --model "$JUDGE_MODEL" --out "$judged")
    if [[ -n "$LIMIT" ]]; then judge_args+=(--limit "$LIMIT"); fi
    echo "Judging with $JUDGE_MODEL -> $judged"
    "${judge_args[@]}"
  fi
done
