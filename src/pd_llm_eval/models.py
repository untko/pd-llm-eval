from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


CaseType = Literal[
    "factual_qa",
    "retrieval",
    "multi_turn",
    "clarification",
    "abstention",
    "tool_call",
    "routing",
    "safety",
    "robustness",
    "edge_case",
]

Role = Literal["system", "user", "assistant", "tool"]
Provenance = Literal["expert", "production", "synthetic", "regression"]


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Role
    content: str
    name: str | None = None


class SourceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    title: str | None = None
    uri: str | None = None
    locator: str | None = None


class ToolCallExpectation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: str
    arguments: dict[str, Any] | None = None
    turn_index: int | None = Field(default=None, ge=0)


class EvalCase(BaseModel):
    """Canonical, vendor-neutral evaluation case."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    name: str
    case_type: CaseType
    language: str = "en"

    # The final user message under evaluation. Prior turns live in conversation_context.
    user_input: str
    conversation_context: list[Message] = Field(default_factory=list)
    initial_state: dict[str, Any] = Field(default_factory=dict)

    intent: str | None = None
    expected_behavior: list[str] = Field(min_length=1)
    reference_answer: str | None = None

    required_facts: list[str] = Field(default_factory=list)
    forbidden_claims: list[str] = Field(default_factory=list)
    gold_sources: list[SourceRef] = Field(default_factory=list)
    expected_tool_calls: list[ToolCallExpectation] = Field(default_factory=list)
    evaluation_rules: list[str] = Field(default_factory=list)

    tags: list[str] = Field(default_factory=list)
    datasets: list[str] = Field(default_factory=list)
    provenance: Provenance = "expert"
    metadata: dict[str, Any] = Field(default_factory=dict)
