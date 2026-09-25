import json

import pytest

from pd_llm_eval.io import load_jsonl
from pd_llm_eval.models import EvalCase


def minimal_case(case_id: str) -> dict:
    return {
        "case_id": case_id,
        "name": "Example",
        "case_type": "factual_qa",
        "user_input": "Question",
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
