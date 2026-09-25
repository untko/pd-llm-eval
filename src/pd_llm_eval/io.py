from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from .models import EvalCase


def load_jsonl(path: str | Path) -> list[EvalCase]:
    """Load and validate a JSONL evaluation dataset."""
    path = Path(path)
    cases: list[EvalCase] = []
    seen: set[str] = set()

    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        try:
            case = EvalCase.model_validate_json(line)
        except ValidationError as exc:
            raise ValueError(f"{path}:{line_number}: invalid evaluation case\n{exc}") from exc

        if case.case_id in seen:
            raise ValueError(f"{path}:{line_number}: duplicate case_id {case.case_id!r}")

        seen.add(case.case_id)
        cases.append(case)

    return cases
