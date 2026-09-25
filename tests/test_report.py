import json

from pd_llm_eval.report import render_markdown_report


def test_render_error_report(tmp_path):
    results = tmp_path / "results.jsonl"
    results.write_text(
        json.dumps(
            {
                "case_id": "qa.001",
                "status": "error",
                "error": "agent not found",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "report.md"

    summary = render_markdown_report(results, output)

    text = output.read_text(encoding="utf-8")
    assert "qa.001" in text
    assert "agent not found" in text
    assert summary["errors"] == 1
