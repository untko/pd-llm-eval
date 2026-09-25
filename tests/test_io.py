import json

import pytest

from pd_llm_eval.io import load_dataset, load_jsonl
from pd_llm_eval.models import EvalCase


def minimal_case(case_id: str) -> dict:
    return {
        "case_id": case_id,
        "name": "Example",
        "language": "en",
        "user_input": "Question",
        "behavior_label": "answerable",
        "expected_action": "answer",
        "evaluation_focus": ["generation"],
        "expected_behavior": ["Answer correctly"],
    }


def test_load_jsonl(tmp_path):
    path = tmp_path / "cases.jsonl"
    path.write_text(json.dumps(minimal_case("qa.001")) + "\n", encoding="utf-8")

    cases = load_jsonl(path)

    assert len(cases) == 1
    assert cases[0].case_id == "qa.001"


def test_duplicate_ids_fail(tmp_path):
    path = tmp_path / "cases.jsonl"
    line = json.dumps(minimal_case("qa.001"))
    path.write_text(f"{line}\n{line}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate case_id"):
        load_jsonl(path)


def test_expected_behavior_is_required():
    data = minimal_case("qa.002")
    data["expected_behavior"] = []

    with pytest.raises(ValueError):
        EvalCase.model_validate(data)


def test_behavior_and_expected_action_must_agree():
    data = minimal_case("qa.003")
    data["behavior_label"] = "underspecified"
    data["expected_action"] = "answer"

    with pytest.raises(ValueError, match="requires expected_action"):
        EvalCase.model_validate(data)

def test_readable_cases_json_is_preferred(tmp_path):
    readable = tmp_path / "cases.json"
    readable.write_text(
        json.dumps([minimal_case("qa.readable")], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    legacy = tmp_path / "legacy.jsonl"
    legacy.write_text(json.dumps(minimal_case("qa.legacy")) + "\n", encoding="utf-8")

    cases = load_dataset(tmp_path)

    assert [case.case_id for case in cases] == ["qa.readable"]
