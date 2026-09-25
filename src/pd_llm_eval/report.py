import json
from pathlib import Path
from typing import Any


def _load_rows(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        if raw.strip():
            rows.append(json.loads(raw))
    return rows


def _cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def render_markdown_report(path: str | Path, output: str | Path) -> dict[str, Any]:
    rows = _load_rows(path)
    ok = [row for row in rows if row.get("status") == "ok"]
    errors = [row for row in rows if row.get("status") != "ok"]
    judged = [row for row in rows if row.get("judge_status") == "ok"]

    lines = [
        "# Evaluation report",
        "",
        f"- Rows: {len(rows)}",
        f"- Successful responses: {len(ok)}",
        f"- Errors: {len(errors)}",
    ]

    if judged:
        passed = sum(bool(row.get("pass")) for row in judged)
        mean = sum(float(row.get("score_10", 0)) for row in judged) / len(judged)
        lines.extend([
            f"- Judged: {len(judged)}",
            f"- Pass rate: {passed}/{len(judged)} ({passed / len(judged):.0%})",
            f"- Mean score: {mean:.2f}/10",
        ])

    lines.extend(["", "## Cases", ""])
    lines.append("| Case | Status | Score | Pass | Response / Error |")
    lines.append("|---|---|---:|---|---|")

    for row in rows:
        response = row.get("assistant_text") or row.get("error") or row.get("judge_error") or ""
        score = row.get("score_10", "")
        passed = row.get("pass", "")
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(row.get("case_id")),
                    _cell(row.get("status")),
                    _cell(score),
                    _cell(passed),
                    _cell(response),
                ]
            )
            + " |"
        )

    if errors:
        lines.extend(["", "## Errors", ""])
        for row in errors:
            lines.extend([
                f"### {_cell(row.get('case_id'))}",
                "",
                "```text",
                str(row.get("error") or row.get("judge_error") or "Unknown error"),
                "```",
                "",
            ])

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    return {
        "rows": len(rows),
        "ok": len(ok),
        "errors": len(errors),
        "judged": len(judged),
        "output": str(output),
    }
