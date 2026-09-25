import json

from pd_llm_eval.yellow import extract_response_text, load_dataset, run_yellow_batch


def _case(case_id: str) -> dict:
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


def test_extract_response_text_with_path():
    payload = {"data": {"reply": {"text": "hello"}}}

    assert extract_response_text(payload, "data.reply.text") == "hello"


def test_extract_response_text_heuristic():
    payload = {"data": [{"type": "text", "message": "hello"}]}

    assert extract_response_text(payload) == "hello"


def test_load_dataset_directory(tmp_path):
    first = tmp_path / "a.jsonl"
    second = tmp_path / "b.jsonl"
    first.write_text(json.dumps(_case("qa.001")) + "\n", encoding="utf-8")
    second.write_text(json.dumps(_case("qa.002")) + "\n", encoding="utf-8")

    cases = load_dataset(tmp_path)

    assert [case.case_id for case in cases] == ["qa.001", "qa.002"]


def test_dry_run_needs_no_credentials(tmp_path):
    dataset = tmp_path / "cases.jsonl"
    dataset.write_text(json.dumps(_case("qa.001")) + "\n", encoding="utf-8")

    summary = run_yellow_batch(dataset, tmp_path / "out.jsonl", dry_run=True)

    assert summary["cases"] == 1
    assert summary["jobs"] == 1
    assert summary["behavior_counts"] == {"answerable": 1}
