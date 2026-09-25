import json
import re
import typing
from pathlib import Path

from .io import load_dataset
from .opencode_runner import run_opencode


def _extract_json_object(text: str) -> dict[str, typing.Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\\s*", "", stripped)
        stripped = re.sub(r"\\s*```$", "", stripped)

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Judge did not return JSON: {text[:1000]}")

    payload = json.loads(stripped[start : end + 1])
    if not isinstance(payload, dict):
        raise TypeError("Judge output is not a JSON object")
    return payload


def _judge_prompt(case: typing.Any, assistant_text: str) -> str:
    payload = {
        "case_id": case.case_id,
        "behavior_label": case.behavior_label,
        "expected_action": case.expected_action,
        "expected_behavior": case.expected_behavior,
        "reference_answer": case.reference_answer,
        "required_facts": case.required_facts,
        "forbidden_claims": case.forbidden_claims,
        "evaluation_rules": case.evaluation_rules,
        "user_input": case.user_input,
        "assistant_text": assistant_text,
    }
    return (
        "Grade this assistant response against the evaluation case below.\n\n"
        f"Case:\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "Return exactly one JSON object with this schema:\n"
        "{\n"
        '  "meets_expected_behavior": true,\n'
        '  "scores": {\n'
        '    "correctness": 0,\n'
        '    "groundedness": 0,\n'
        '    "completeness": 0,\n'
        '    "instruction_adherence": 0,\n'
        '    "clarity": 0\n'
        "  },\n"
        '  "hard_fail": [],\n'
        '  "rationale": "brief explanation"\n'
        "}\n\n"
        "Scales: correctness, groundedness, completeness, instruction_adherence are 0-2; "
        "clarity is 0-1. hard_fail may contain only: critical_hallucination, "
        "unsafe_advice, materially_wrong_tool_or_action, contradicts_authoritative_source, "
        "fails_required_abstention, privacy_or_security_violation. "
        "Judge the expected action as well as factual content. Do not reward fluent but unsupported answers."
    )


def judge_opencode_results(
    dataset: str | Path,
    results_path: str | Path,
    output: str | Path,
    *,
    model: str,
    timeout: float = 180.0,
    limit: int | None = None,
) -> dict[str, typing.Any]:
    cases = {case.case_id: case for case in load_dataset(dataset)}
    rows = [
        json.loads(line)
        for line in Path(results_path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if limit is not None:
        rows = rows[:limit]

    judged: list[dict[str, typing.Any]] = []
    for row in rows:
        if row.get("status") != "ok":
            judged.append({**row, "judge_status": "skipped"})
            continue

        case = cases[row["case_id"]]
        try:
            judge_text, judge_latency_ms = run_opencode(
                _judge_prompt(case, row.get("assistant_text", "")),
                model=model,
                agent="pd-eval-judge",
                timeout=timeout,
            )
            verdict = _extract_json_object(judge_text)
            scores = verdict.get("scores", {})
            raw_score = sum(
                float(scores.get(key, 0))
                for key in (
                    "correctness",
                    "groundedness",
                    "completeness",
                    "instruction_adherence",
                    "clarity",
                )
            )
            hard_fail = verdict.get("hard_fail") or []
            judged.append(
                {
                    **row,
                    "judge_status": "ok",
                    "judge_model": model,
                    "judge": verdict,
                    "score_10": round(raw_score * 10 / 9, 2),
                    "pass": bool(verdict.get("meets_expected_behavior")) and not hard_fail,
                    "judge_latency_ms": round(judge_latency_ms, 2),
                }
            )
        except Exception as exc:  # noqa: BLE001
            judged.append(
                {
                    **row,
                    "judge_status": "error",
                    "judge_model": model,
                    "judge_error": str(exc),
                }
            )

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in judged:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    graded = [row for row in judged if row.get("judge_status") == "ok"]
    passed = sum(bool(row.get("pass")) for row in graded)
    mean_score = (
        round(sum(float(row["score_10"]) for row in graded) / len(graded), 2)
        if graded
        else None
    )
    return {
        "judge_model": model,
        "rows": len(judged),
        "graded": len(graded),
        "passed": passed,
        "pass_rate": round(passed / len(graded), 4) if graded else None,
        "mean_score_10": mean_score,
        "output": str(output),
    }
