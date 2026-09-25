from __future__ import annotations

from typing import Any

from pd_llm_eval.models import EvalCase


def to_yellow_concept(case: EvalCase) -> dict[str, Any]:
    """Map a canonical case to Yellow.ai's documented conceptual fields.

    This intentionally does not serialize Yellow.ai CSV. Yellow.ai documents bulk CSV
    import, but its public Testing Lab docs do not currently publish a stable CSV column
    contract. Keep the canonical dataset stable and add the final serializer once an
    exported template or platform-provided schema is available.
    """
    user_inputs = [
        message.content for message in case.conversation_context if message.role == "user"
    ]
    user_inputs.append(case.user_input)

    expected_outcome = list(case.expected_behavior)
    expected_outcome.extend(f"Must include fact: {fact}" for fact in case.required_facts)
    expected_outcome.extend(
        f"Must not claim: {claim}" for claim in case.forbidden_claims
    )
    expected_outcome.extend(
        f"Must call tool: {tool.tool_name}" for tool in case.expected_tool_calls
    )

    return {
        "name": case.name,
        "user_inputs": user_inputs,
        "initial_state": case.initial_state,
        "expected_outcome": expected_outcome,
        "source_reference": case.case_id,
    }
