# Running the smoke suite against Yellow.ai

The repository now has two distinct evaluation paths:

1. **Independent runtime baseline** — run the canonical cases directly against the Yellow.ai bot endpoint with this repository.
2. **Yellow.ai Testing Lab** — import/capture the same cases inside Yellow.ai and use its native evaluators, assertions, traces, and reports.

The runtime runner is automated here. It does not replace Yellow.ai Testing Lab.

## Why the runner uses the bot endpoint

Yellow.ai publicly documents a synchronous **Send message/event to bot** API. The public Testing Lab documentation describes running datasets from the UI, but does not currently publish a stable public automation API for creating/running those Testing Lab datasets.

So this runner sends the exact benchmark inputs to the deployed lower-tier bot endpoint and saves the raw output for our own evaluation pipeline.

## 1. Install

```bash
git checkout setup/eval-infra
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

After PR #1 is merged, use `main` instead of the setup branch.

## 2. Configure Yellow.ai

Keep credentials out of git.

```bash
export YELLOW_API_URL='YOUR_FULL_YELLOW_SEND_MESSAGE_ENDPOINT'
export YELLOW_BOT_ID='YOUR_BOT_ID'
export YELLOW_API_TOKEN='YOUR_TOKEN'
```

`YELLOW_API_TOKEN` is optional in the runner because authentication varies by endpoint/configuration, but use it when your Yellow endpoint requires bearer authentication.

The request body follows Yellow.ai's documented shape:

```json
{
  "botId": "...",
  "sender": "...",
  "data": {
    "message": "..."
  }
}
```

## 3. Validate without calling Yellow.ai

```bash
pd-eval run-yellow datasets/smoke_v1 --dry-run
```

Expected summary: 30 cases.

## 4. Test one case first

```bash
pd-eval run-yellow datasets/smoke_v1 \
  --limit 1 \
  --out results/yellow-one.jsonl
```

Inspect the saved raw response. The runner always preserves the complete response payload.

If `assistant_text` is empty or the wrong field was selected, pass the response field explicitly:

```bash
pd-eval run-yellow datasets/smoke_v1 \
  --limit 1 \
  --response-path 'data.reply.text' \
  --out results/yellow-one.jsonl
```

The exact response path depends on the Yellow endpoint/configuration you use.

## 5. Run all 30 cases

```bash
bash scripts/run_yellow_smoke.sh
```

By default it runs sequentially and writes a timestamped JSONL file under `results/`.

For two concurrent cases:

```bash
CONCURRENCY=2 bash scripts/run_yellow_smoke.sh
```

For stochastic reliability, run each case three times:

```bash
ITERATIONS=3 CONCURRENCY=2 bash scripts/run_yellow_smoke.sh
```

Each case and iteration receives a unique `sender` ID, so conversation state does not leak between tests.

## Multi-turn cases

For a multi-turn case, the runner replays the stored **user** turns in order and lets Yellow.ai generate its own intermediate assistant responses. It does not inject the stored assistant messages.

That is intentional: this is an end-to-end conversation test rather than a model-only test with a fabricated transcript.

## Output

Each JSONL row contains:

- case ID and expected action
- behavior/evaluation metadata
- final assistant text
- raw Yellow response for every turn
- per-turn and total latency
- execution error, if any

Raw run outputs live under `results/`, which is gitignored.

## Native Yellow.ai Testing Lab

Yellow.ai's current docs say a Testing Lab execution can run up to 200 cases and is available in lower-tier environments such as Sandbox/Development.

For native Yellow evaluator scores and execution traces, use Testing Lab as the second baseline. Once we have an actual CSV template exported/downloaded from your Yellow.ai workspace, we can add an exact canonical -> Yellow CSV exporter instead of guessing its private/import schema.
