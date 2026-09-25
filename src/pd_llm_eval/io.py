from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from .models import EvalCase


def _validate_objects(objects: list[object], source: Path) -> list[EvalCase]:
    cases: list[EvalCase] = []
    seen: set[str] = set()

    for index, obj in enumerate(objects, start=1):
        try:
            case = EvalCase.model_validate(obj)
        except ValidationError as exc:
            raise ValueError(f"{source}: item {index}: invalid evaluation case\n{exc}") from exc

        if case.case_id in seen:
            raise ValueError(f"{source}: duplicate case_id {case.case_id!r}")

        seen.add(case.case_id)
        cases.append(case)

    return cases


def load_json(path: str | Path) -> list[EvalCase]:
    """Load a readable JSON array of evaluation cases."""
    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise TypeError(f"{path}: expected a JSON array")
    return _validate_objects(payload, path)


def load_jsonl(path: str | Path) -> list[EvalCase]:
    """Load and validate a JSONL evaluation dataset."""
    path = Path(path)
    objects: list[object] = []

    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            objects.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON\n{exc}") from exc

    return _validate_objects(objects, path)


def load_dataset(path: str | Path) -> list[EvalCase]:
    """Load a canonical dataset.

    For a directory, prefer cases.json as the human-editable source of truth.
    Otherwise load JSON/JSONL files in lexical order.
    """
    path = Path(path)

    if path.is_file():
        if path.suffix == ".json":
            return load_json(path)
        if path.suffix == ".jsonl":
            return load_jsonl(path)
        raise ValueError(f"Unsupported dataset format: {path}")

    readable = path / "cases.json"
    if readable.exists():
        return load_json(readable)

    files = sorted([*path.glob("*.json"), *path.glob("*.jsonl")])
    if not files:
        raise ValueError(f"No JSON/JSONL dataset files found at {path}")

    cases: list[EvalCase] = []
    seen: set[str] = set()
    for file in files:
        for case in load_dataset(file):
            if case.case_id in seen:
                raise ValueError(f"duplicate case_id across dataset: {case.case_id!r}")
            seen.add(case.case_id)
            cases.append(case)
    return cases
