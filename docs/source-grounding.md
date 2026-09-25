# Actual-KB grounding

The canonical evaluation cases can now point to the team's actual knowledge-base sections through `gold_sources`.

The KB content itself is **not committed to this public repository**. The current authoritative parsed KB already exists in the private `llm-judge` project as:

```text
data/kb_structure.json
```

## Source IDs

For a section-level case:

```json
"gold_sources": [
  {"source_id": "BFSC/1-Ingredients"}
]
```

For a topic-level case:

```json
"gold_sources": [
  {"source_id": "BFSC/topic-general"}
]
```

`topic-general` is a virtual source ID. The resolver expands it to the article intro plus all real sections.

## Configure locally

If the repositories are siblings:

```text
Projects/
  pd-llm-eval/
  llm-judge/
```

set:

```bash
export PD_KB_PATH=../llm-judge/data/kb_structure.json
```

Or pass the path explicitly with `--kb`.

## Validate a dataset against the real KB

```bash
pd-eval validate-sources datasets/private/core_v1/cases.json \
  --kb ../llm-judge/data/kb_structure.json
```

This checks that every `gold_sources[].source_id` resolves.

## Model-only oracle evaluation

```bash
pd-eval run-opencode datasets/private/core_v1/cases.json \
  --model PROVIDER/MODEL \
  --mode oracle \
  --kb ../llm-judge/data/kb_structure.json \
  --limit 5 \
  --out results/model-core-v1.jsonl
```

For answerable cases, the model now receives the **actual Burmese KB source text** for the cited section. It no longer needs to rely on the workbook's model-generated reference answer.

For clarify, abstain, near-miss, social, and escalation cases, no KB answer is supplied. Those cases test the behavior policy.

## Why the core dataset stays private

The reviewed workbook contains real farmer utterances and internal curation metadata. `datasets/private/` is gitignored so a large production-derived benchmark cannot be accidentally pushed into this public repository.

A public regression/smoke set can still contain deliberately reviewed, non-sensitive examples.
