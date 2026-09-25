# Local model evaluation with OpenCode

This path evaluates models before testing Yellow.ai end to end.

## What it measures

The default `oracle` mode isolates **model response quality** from retrieval quality:

- answerable cases receive the case's approved required facts as context
- non-answerable cases receive no approved knowledge context
- the model must still decide whether to answer, clarify, abstain, reply socially, or route/escalate
- OpenCode tools are disabled through the `pd-eval-respondent` agent

This is intentionally different from the later Yellow.ai baseline, which evaluates retrieval + orchestration + model together.

`closed-book` mode supplies no approved facts. It is useful for curiosity/robustness checks, but should not be treated as the primary agriculture benchmark because it rewards model prior knowledge.

## Human-editable tests

`datasets/smoke_v1/cases.json` is now the source of truth for the smoke suite.

It is ordinary pretty-printed JSON, so you can edit questions, reference answers, required facts, tags, and expected behavior directly in an editor. The older split JSONL files remain as compatibility snapshots; do not edit them unless regenerating them deliberately.

Validate after editing:

```bash
pd-eval validate datasets/smoke_v1/cases.json
```

## List your OpenCode models

```bash
opencode models
```

Use the exact `provider/model` IDs printed there. OpenCode supports non-interactive `opencode run --model ...`, which is what the harness calls.

## Start with three cases

```bash
pd-eval run-opencode datasets/smoke_v1/cases.json \
  --model YOUR_PROVIDER/YOUR_MODEL \
  --mode oracle \
  --limit 3 \
  --out results/model-smoke-3.jsonl
```

Inspect:

```bash
cat results/model-smoke-3.jsonl | jq
```

## Judge the responses

Prefer a **different model family** as judge when practical to reduce self-preference bias.

```bash
pd-eval judge-opencode datasets/smoke_v1/cases.json \
  results/model-smoke-3.jsonl \
  --model YOUR_JUDGE_PROVIDER/YOUR_JUDGE_MODEL \
  --out results/model-smoke-3-judged.jsonl
```

The judge records:

- whether expected behavior was met
- correctness 0-2
- groundedness 0-2
- completeness 0-2
- instruction adherence 0-2
- clarity 0-1
- normalized score out of 10
- hard-fail labels

`pass` means the judge says expected behavior was met and no hard-fail label was triggered.

## Run several models

```bash
MODELS='provider/model-a,provider/model-b' \
JUDGE_MODEL='provider/judge-model' \
LIMIT=5 \
bash scripts/run_opencode_smoke.sh
```

Remove `LIMIT=5` when the setup looks correct.

For reliability testing:

```bash
MODELS='provider/model-a' \
JUDGE_MODEL='provider/judge-model' \
ITERATIONS=3 \
bash scripts/run_opencode_smoke.sh
```

OpenCode's current CLI documents `opencode run` for non-interactive automation and `--model provider/model` for selecting the model.
