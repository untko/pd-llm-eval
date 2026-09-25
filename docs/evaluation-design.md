# Evaluation design

## Unit of evaluation

A case represents one user request plus any prior conversational context and the behavior that should be true of the system response.

The canonical dataset is vendor-neutral. Platform-specific representations are generated from it rather than becoming the source of truth.

## Three independent taxonomies

The source evaluation workbook shows that one `case_type` is too lossy. Keep three axes separate.

### 1. Behavior label

What kind of request is this?

- `answerable`
- `underspecified`
- `out_of_kb`
- `near_miss`
- `social`
- `escalate`

### 2. Expected action

What should the assistant do?

- `answerable` -> `answer`
- `underspecified` -> `clarify`
- `out_of_kb` -> `abstain`
- `near_miss` -> `abstain`
- `social` -> `no_retrieval`
- `escalate` -> `escalate`

These pairs are validated by the canonical schema.

### 3. Evaluation focus

What capability or failure mode are we probing?

Examples:

- `retrieval`
- `generation`
- `multi_turn`
- `ambiguity`
- `routing`
- `tool_use`
- `robustness`
- `safety`
- `domain_reasoning`
- `numeric_handling`
- `keyword_conflict`
- `near_miss`

A case may have multiple evaluation-focus values.

## Domain taxonomy

Agriculture metadata is also independent of behavior. Preserve the existing hierarchy where available:

`category -> crop_group -> topic_code/topic_title -> level -> subtopic`

This lets us answer questions such as:

- Does the system fail more on crop protection than farm extension?
- Are failures concentrated in one crop?
- Does subtopic retrieval degrade as similar crop FAQs are added?

## Scoring

The default rubric is in `config/rubric.yaml`.

Use three layers:

1. Deterministic assertions where possible, such as expected action, expected tool name, required fields, forbidden strings, source IDs, latency, or schema validity.
2. LLM-as-judge for semantic criteria such as correctness, groundedness, completeness, and clarity.
3. Human review for calibration, disputed cases, and high-risk failures.

A single reference answer is evidence, not the only valid wording.

## Hard failures

Hard failures are reported separately from the numerical score. A fluent answer with a critical hallucination should not be hidden by a high average score.

For this agriculture assistant, also treat these as important failure classes:

- wrong crop
- wrong topic/disease
- wrong dosage or numeric value
- relevant-sounding but unsupported answer
- failure to clarify an ambiguous crop/input request
- retrieval of a generic practice article when the user is asking for diagnosis

## Dataset quality tiers

Do not treat every existing reference answer as equally authoritative.

Recommended roles:

- **gold**: human/expert-verified response or expected behavior
- **silver**: model-generated/reference response that passed automated review but has not been human-verified
- **behavior-only**: cases such as social, clarify, abstain, or escalate where the action matters more than a reference answer
- **regression**: a known production failure retained permanently after the expected behavior is verified

Use metadata/dataset membership to record these roles.

## Dataset construction

The existing workbook is large enough to seed the benchmark, but the first runnable suite should remain small and interpretable.

Start with 20-30 cases covering:

- every behavior label
- common/golden answerable paths
- several crops and domain categories
- symptom-based disease retrieval
- ambiguity requiring clarification
- near-miss and out-of-KB abstention
- social messages that should bypass retrieval
- escalation requests
- numeric/dosage questions
- typo/encoding/noisy Burmese
- keyword-conflict cases

Then create a larger regression/coverage suite from the remaining curated data.

Every meaningful production failure should become a regression case.

## Comparison protocol

When comparing Yellow.ai, ChatbotX, or a custom stack:

- use the same canonical cases
- pin knowledge-base version where possible
- record model/provider and configuration
- repeat stochastic cases multiple times
- report quality, hard-fail rate, latency, and cost separately
- report results by behavior label, evaluation focus, crop, category, and provenance
- do not collapse everything into one leaderboard number
