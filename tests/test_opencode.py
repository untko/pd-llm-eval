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
