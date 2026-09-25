# Yellow.ai compatibility

The canonical schema is intentionally richer than Yellow.ai's UI model.

Current Yellow.ai Nexus Testing Lab documentation describes these case fields:

- Name
- User inputs, one or many turns
- Initial state
- Expected outcome
- Source reference
- Baseline trace
- Run status

Yellow.ai also supports bulk CSV import, but the public Testing Lab documentation reviewed for this project does not specify a stable CSV column contract. We therefore do not invent one.

The conceptual mapping is implemented in `src/pd_llm_eval/adapters/yellow.py`:

| Canonical | Yellow.ai |
|---|---|
| `name` | Name |
| prior user turns + `user_input` | User inputs |
| `initial_state` | Initial state |
| `expected_action` + `expected_behavior` + assertions | Expected outcome |
| `case_id` | Source reference |

Behavior labels, evaluation-focus tags, domain taxonomy, curation provenance, required facts, forbidden claims, expected tool calls, and gold sources remain in the canonical dataset even when Yellow.ai cannot represent them directly.

## Why this boundary matters

The repository, not Yellow.ai, is the benchmark source of truth. This allows the same cases to be run against another orchestration platform or directly against a custom RAG/model endpoint.

## Yellow.ai references

- Testing Lab: https://docs.yellow.ai/docs/nexus/test-debug/trust-centre/testing-lab
- Create test cases: https://docs.yellow.ai/docs/nexus/test-debug/trust-centre/testing-lab/create-test-cases
- Run tests: https://docs.yellow.ai/docs/nexus/test-debug/trust-centre/testing-lab/run-tests
