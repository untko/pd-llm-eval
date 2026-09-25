import json

from pd_llm_eval.kb import KnowledgeBase
from pd_llm_eval.models import EvalCase
from pd_llm_eval.opencode_runner import build_prompt, run_opencode_batch


def _case() -> EvalCase:
    return EvalCase.model_validate(
        {
            "case_id": "qa.001",
            "name": "Example",
            "language": "en",
            "user_input": "How much?",
            "behavior_label": "answerable",
            "expected_action": "answer",
            "evaluation_focus": ["generation"],
            "expected_behavior": ["Use the approved fact"],
            "required_facts": ["Use 4 tablespoons."],
        }
    )


def test_oracle_prompt_contains_required_facts():
    prompt = build_prompt(_case(), "oracle")

    assert "Use 4 tablespoons." in prompt


def test_closed_book_prompt_hides_required_facts():
    prompt = build_prompt(_case(), "closed-book")

    assert "Use 4 tablespoons." not in prompt


def test_opencode_dry_run_does_not_call_binary(tmp_path):
    dataset = tmp_path / "cases.json"
    dataset.write_text(
        "[" + _case().model_dump_json() + "]",
        encoding="utf-8",
    )

    summary = run_opencode_batch(
        dataset,
        tmp_path / "out.jsonl",
        model="provider/model",
        dry_run=True,
    )

    assert summary["cases"] == 1
    assert summary["jobs"] == 1

def test_oracle_prompt_prefers_actual_kb_source(tmp_path):
    kb_path = tmp_path / "kb.json"
    kb_path.write_text(
        json.dumps(
            [
                {
                    "code": "ABC",
                    "title_en": "Example",
                    "subtopics": [
                        {
                            "id": "ABC/1-How_to",
                            "name": "How to",
                            "content": "Authoritative source says five tablespoons.",
                        }
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )
    data = _case().model_dump()
    data["gold_sources"] = [{"source_id": "ABC/1-How_to"}]
    data["required_facts"] = ["Legacy fact says four tablespoons."]
    case = EvalCase.model_validate(data)

    prompt = build_prompt(case, "oracle", KnowledgeBase(kb_path))

    assert "five tablespoons" in prompt
    assert "Legacy fact says four tablespoons." not in prompt
