# Evaluation design

## Unit of evaluation

A case represents one user request plus any prior conversational context and the behavior that should be true of the system response.

The canonical dataset is vendor-neutral. Platform-specific representations are generated from it rather than becoming the source of truth.

## Test taxonomy

- `factual_qa`: direct answer grounded in approved knowledge
- `retrieval`: correct evidence/chunk must be found
- `multi_turn`: prior conversational context matters
- `clarification`: information is insufficient and the bot should ask
- `abstention`: the bot should explicitly avoid unsupported claims
- `tool_call`: correct tool and arguments matter
- `routing`: correct intent, agent, or workflow must be selected
- `safety`: harmful or prohibited guidance must be avoided
- `robustness`: typos, code-switching, vague phrasing, prompt attacks
- `edge_case`: conflicting sources, stale data, unusual states

Use one primary `case_type` and additional `tags` for overlapping properties.

## Scoring

The default rubric is in `config/rubric.yaml`.

Use three layers:

1. Deterministic assertions where possible, such as expected tool name, required fields, forbidden strings, source IDs, latency, or schema validity.
2. LLM-as-judge for semantic criteria such as correctness, groundedness, completeness, and clarity.
3. Human review for calibration, disputed cases, and high-risk failures.

A single reference answer is evidence, not the only valid wording.

## Hard failures

Hard failures are reported separately from the numerical score. A fluent answer with a critical hallucination should not be hidden by a high average score.

## Dataset construction

Start with 10-30 cases:

- common/golden paths
- at least one case per route/workflow
- at least one case per tool
- clarification and abstention cases
- 2-3 adversarial/robustness cases

Grow toward 100-200 representative cases after the first baseline. Prefer real user conversations, then add expert-authored edge cases. Synthetic generation is useful for coverage expansion but should not define the entire benchmark.

Every meaningful production failure should become a regression case.

## Comparison protocol

When comparing Yellow.ai, ChatbotX, or a custom stack:

- use the same canonical cases
- pin knowledge-base version where possible
- record model/provider and configuration
- repeat stochastic cases multiple times
- report quality, hard-fail rate, latency, and cost separately
- do not collapse everything into one leaderboard number
