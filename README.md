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
examples/
  example_cases.jsonl         schema examples, not production benchmark cases
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

1. Define the canonical case schema and scoring rubric.
2. Curate a small 10-30 case smoke/regression set.
3. Run a Yellow.ai baseline.
4. Add target adapters for alternative stacks.
5. Expand toward 100-200 representative cases from real conversations.

The next substantive step is dataset curation, not adding more framework code.
