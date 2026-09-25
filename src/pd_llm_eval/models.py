from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field
from pydantic.functional_validators import model_validator


BehaviorLabel = Literal[
    "answerable",
    "underspecified",
    "out_of_kb",
    "near_miss",
    "social",
    "escalate",
]

ExpectedAction = Literal[
    "answer",
    "clarify",
    "abstain",
    "no_retrieval",
    "escalate",
]

EvalFocus = Literal[
    "retrieval",
    "generation",
    "multi_turn",
    "ambiguity",
    "routing",
    "tool_use",
    "robustness",
    "safety",
    "domain_reasoning",
    "numeric_handling",
    "keyword_conflict",
    "near_miss",
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


class DomainMetadata(BaseModel):
    """Agriculture/knowledge-base taxonomy associated with a case."""

    model_config = ConfigDict(extra="forbid")

    level: Literal["topic", "subtopic"] | None = None
    topic_code: str | None = None
    topic_title_my: str | None = None
    crop_group: str | None = None
    category: str | None = None
    subtopic: str | None = None


class CurationMetadata(BaseModel):
    """How the case was sourced, selected, and reviewed."""

    model_config = ConfigDict(extra="forbid")

    source_type: Literal["real", "generated"] | None = None
    selection: Literal["census", "real-census", "representative", "spanning"] | None = None
    kb_overlap: float | None = None
    kb_longest_span: float | None = None
    origin_uuid: str | None = None
    origin_intent: str | None = None
    judge_verdict: str | None = None
    judge_reason: str | None = None
    near_topic: str | None = None
    notes: str | None = None
    ground_truth_status: str | None = None
    ground_truth_model: str | None = None


class EvalCase(BaseModel):
    """Canonical, vendor-neutral evaluation case."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    name: str
    language: str = "my"

    # The final user message under evaluation. Prior turns live in conversation_context.
    user_input: str
    conversation_context: list[Message] = Field(default_factory=list)
    initial_state: dict[str, Any] = Field(default_factory=dict)

    # What the user request represents and what the system should do.
    behavior_label: BehaviorLabel
    expected_action: ExpectedAction

    # What capability or failure mode this case is intended to probe.
    evaluation_focus: list[EvalFocus] = Field(default_factory=list)

    intent: str | None = None
    expected_behavior: list[str] = Field(min_length=1)
    reference_answer: str | None = None

    required_facts: list[str] = Field(default_factory=list)
    forbidden_claims: list[str] = Field(default_factory=list)
    gold_sources: list[SourceRef] = Field(default_factory=list)
    expected_tool_calls: list[ToolCallExpectation] = Field(default_factory=list)
    evaluation_rules: list[str] = Field(default_factory=list)

    domain: DomainMetadata = Field(default_factory=DomainMetadata)
    curation: CurationMetadata = Field(default_factory=CurationMetadata)

    tags: list[str] = Field(default_factory=list)
    datasets: list[str] = Field(default_factory=list)
    provenance: Provenance = "expert"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_behavior_action(self) -> Self:
        expected_by_label: dict[str, str] = {
            "answerable": "answer",
            "underspecified": "clarify",
            "out_of_kb": "abstain",
            "near_miss": "abstain",
            "social": "no_retrieval",
            "escalate": "escalate",
        }
        required = expected_by_label[self.behavior_label]
        if self.expected_action != required:
            raise ValueError(
                f"behavior_label={self.behavior_label!r} requires "
                f"expected_action={required!r}, got {self.expected_action!r}"
            )
        return self
