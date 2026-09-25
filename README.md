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
  running-opencode.md         local model evaluation through OpenCode
  source-grounding.md         use the actual private KB as oracle evidence
examples/
  example_cases.jsonl         schema examples, not production benchmark cases
datasets/
  smoke_v1/                   30-case initial benchmark; cases.json is editable source
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
human-editable cases.json
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
3. Run local model baselines through OpenCode.
4. Run a Yellow.ai end-to-end baseline.
5. Add target adapters for alternative stacks.
6. Expand toward 100-200 representative cases from real conversations.

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

## Run local model baselines

The human-editable smoke suite is `datasets/smoke_v1/cases.json`.

```bash
opencode models
pd-eval run-opencode datasets/smoke_v1/cases.json --model PROVIDER/MODEL --limit 3 --out results/model-smoke-3.jsonl
```

Then judge with a different model when practical:

```bash
pd-eval judge-opencode datasets/smoke_v1/cases.json results/model-smoke-3.jsonl --model PROVIDER/JUDGE_MODEL --out results/model-smoke-3-judged.jsonl
```

See `docs/running-opencode.md` for oracle vs closed-book mode and multi-model batch runs.

## Read results

Raw runs are JSONL for machine processing. Generate a human-readable Markdown report with:

```bash
pd-eval report results/model-smoke-3.jsonl --out results/model-smoke-3.md
open results/model-smoke-3.md
```

The report includes a compact case table plus full error messages when a run fails.


## Actual KB grounding

Answerable cases can cite real KB sections through `gold_sources`. Point the runner at the private team's parsed KB:

```bash
export PD_KB_PATH=../llm-judge/data/kb_structure.json

pd-eval validate-sources datasets/private/core_v1/cases.json \
  --kb "$PD_KB_PATH"
```

In `--mode oracle`, cited KB text takes precedence over legacy `required_facts` or model-generated reference answers. See `docs/source-grounding.md`.

Production-derived benchmark files belong under `datasets/private/`, which is gitignored.
