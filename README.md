# pd-llm-eval

Platform-neutral evaluation harness and regression dataset for the PD agriculture assistant.

The repository is designed around one canonical test-set format, with adapters for platform-specific evaluation systems such as Yellow.ai and for direct model/RAG endpoints.

## Goals

- Keep evaluation cases independent of any vendor.
- Evaluate the full response pipeline: routing, retrieval, tool use, generation, and final answer.
- Compare Yellow.ai, replacement platforms, and custom models on the same cases.
- Promote real production failures into permanent regression cases.
- Track quality, hard failures, latency, and cost separately.

## Repository layout

```text
config/
  rubric.yaml                 scoring dimensions and hard-fail rules
docs/
  evaluation-design.md        methodology and dataset construction
  yellow-ai.md                Yellow.ai compatibility boundary
  running-yellow.md           batch execution against Yellow.ai
examples/
  example_cases.jsonl         schema examples, not production benchmark cases
datasets/
  smoke_v1/                   30-case initial benchmark
src/pd_llm_eval/
  models.py                   canonical case schema
  io.py                       JSONL validation/loading
  cli.py                      command-line utilities
  adapters/yellow.py          Yellow.ai conceptual mapping
tests/
  test_io.py                  schema/loader regression tests
```

## Canonical data flow

```text
canonical JSONL
    |
    +--> Yellow.ai adapter
    +--> alternative platform adapter
    +--> direct model/RAG runner
             |
             v
      deterministic checks
      + semantic judge
      + human calibration
             |
             v
      comparable run report
```

Yellow.ai remains a target, not the source of truth.

## Local setup

Python 3.11+ is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"

ruff check .
pytest -q
pd-eval validate examples/example_cases.jsonl
```

Using `uv` is also fine:

```bash
uv sync --extra dev
uv run ruff check .
uv run pytest -q
uv run pd-eval validate examples/example_cases.jsonl
```

## Initial plan

1. Define the canonical case schema and scoring rubric. ✓
2. Curate a 30-case smoke/regression set. ✓
3. Run a Yellow.ai baseline.
4. Add target adapters for alternative stacks.
5. Expand toward 100-200 representative cases from real conversations.

The smoke suite currently contains 16 answerable, 4 clarification, 3 out-of-KB, 3 near-miss, 2 social, and 2 escalation cases. See `datasets/smoke_v1/README.md`.

## Run the Yellow.ai baseline

Dry-run the 30-case suite:

```bash
pd-eval run-yellow datasets/smoke_v1 --dry-run
```

Then configure `YELLOW_API_URL`, `YELLOW_BOT_ID`, and (when required) `YELLOW_API_TOKEN`, and run:

```bash
bash scripts/run_yellow_smoke.sh
```

See `docs/running-yellow.md` for one-case testing, response-path configuration, concurrency, and repeated runs.
