from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from .io import load_dataset
from .models import EvalCase


_TEXT_KEYS = ("text", "message", "content", "response", "answer")


def load_dataset(path: str | Path) -> list[EvalCase]:
    """Load one JSONL file or every JSONL file in a directory."""
    path = Path(path)
    files = [path] if path.is_file() else sorted(path.glob("*.jsonl"))
    if not files:
        raise ValueError(f"No JSONL files found at {path}")

    cases: list[EvalCase] = []
    seen: set[str] = set()
    for file in files:
        for case in load_jsonl(file):
            if case.case_id in seen:
                raise ValueError(f"duplicate case_id across dataset: {case.case_id!r}")
            seen.add(case.case_id)
            cases.append(case)
    return cases


def _read_path(payload: Any, path: str) -> Any:
    current = payload
    for part in path.split("."):
        if isinstance(current, list):
            current = current[int(part)]
        elif isinstance(current, dict):
            current = current[part]
        else:
            raise KeyError(path)
    return current


def extract_response_text(payload: Any, response_path: str | None = None) -> str | None:
    """Extract assistant text while always retaining the raw response separately."""
    if response_path:
        try:
            value = _read_path(payload, response_path)
        except (KeyError, IndexError, ValueError, TypeError):
            return None
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)

    if isinstance(payload, str):
        return payload

    if isinstance(payload, list):
        texts = [
            text
            for item in payload
            if (text := extract_response_text(item, response_path=None))
        ]
        return "\n".join(texts) if texts else None

    if isinstance(payload, dict):
        for key in _TEXT_KEYS:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value
        for value in payload.values():
            text = extract_response_text(value, response_path=None)
            if text:
                return text

    return None


class YellowClient:
    """Minimal client for Yellow.ai's synchronous send-message-to-bot API."""

    def __init__(
        self,
        *,
        api_url: str,
        bot_id: str,
        token: str | None = None,
        timeout: float = 60.0,
        response_path: str | None = None,
    ) -> None:
        self.api_url = api_url
        self.bot_id = bot_id
        self.token = token
        self.timeout = timeout
        self.response_path = response_path

    def send(self, *, sender: str, message: str) -> tuple[Any, str | None, float]:
        payload = {
            "botId": self.bot_id,
            "sender": sender,
            "data": {"message": message},
        }
        request = urllib.request.Request(
            self.api_url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers={
                "Content-Type": "application/json",
                **(
                    {"Authorization": f"Bearer {self.token}"}
                    if self.token
                    else {}
                ),
            },
        )

        started = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Yellow.ai HTTP {exc.code}: {body[:1000]}"
            ) from exc
        elapsed_ms = (time.perf_counter() - started) * 1000

        try:
            decoded: Any = json.loads(raw)
        except json.JSONDecodeError:
            decoded = raw

        return decoded, extract_response_text(decoded, self.response_path), elapsed_ms


def _sender_id(run_id: str, case: EvalCase, iteration: int) -> str:
    safe_case = "".join(ch if ch.isalnum() else "-" for ch in case.case_id)
    return f"pd-eval-{run_id}-{safe_case}-{iteration}"[:120]


def run_case(
    client: YellowClient,
    case: EvalCase,
    *,
    run_id: str,
    iteration: int,
) -> dict[str, Any]:
    """Replay user turns for one case and capture the final response.

    Stored assistant turns in conversation_context are not injected. The target
    system generates its own intermediate assistant turns, preserving an end-to-end
    test of conversation state.
    """
    sender = _sender_id(run_id, case, iteration)
    inputs = [
        message.content
        for message in case.conversation_context
        if message.role == "user"
    ]
    inputs.append(case.user_input)

    turns: list[dict[str, Any]] = []
    total_latency_ms = 0.0

    try:
        for user_input in inputs:
            raw, text, latency_ms = client.send(sender=sender, message=user_input)
            total_latency_ms += latency_ms
            turns.append(
                {
                    "user_input": user_input,
                    "assistant_text": text,
                    "latency_ms": round(latency_ms, 2),
                    "raw_response": raw,
                }
            )

        return {
            "run_id": run_id,
            "target": "yellow",
            "case_id": case.case_id,
            "iteration": iteration,
            "status": "ok",
            "behavior_label": case.behavior_label,
            "expected_action": case.expected_action,
            "evaluation_focus": case.evaluation_focus,
            "domain": case.domain.model_dump(exclude_none=True),
            "assistant_text": turns[-1]["assistant_text"] if turns else None,
            "latency_ms": round(total_latency_ms, 2),
            "turns": turns,
        }
    except Exception as exc:
        return {
            "run_id": run_id,
            "target": "yellow",
            "case_id": case.case_id,
            "iteration": iteration,
            "status": "error",
            "behavior_label": case.behavior_label,
            "expected_action": case.expected_action,
            "error": str(exc),
            "turns": turns,
        }


def run_yellow_batch(
    dataset: str | Path,
    output: str | Path,
    *,
    api_url: str | None = None,
    bot_id: str | None = None,
    token: str | None = None,
    timeout: float = 60.0,
    response_path: str | None = None,
    iterations: int = 1,
    concurrency: int = 1,
    limit: int | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    cases = load_dataset(dataset)
    if limit is not None:
        cases = cases[:limit]

    jobs = [(case, iteration) for case in cases for iteration in range(1, iterations + 1)]
    if dry_run:
        return {
            "cases": len(cases),
            "jobs": len(jobs),
            "output": str(output),
            "behavior_counts": _count_behaviors(cases),
        }

    api_url = api_url or os.getenv("YELLOW_API_URL")
    bot_id = bot_id or os.getenv("YELLOW_BOT_ID")
    token = token or os.getenv("YELLOW_API_TOKEN")

    if not api_url:
        raise ValueError("Set YELLOW_API_URL or pass --api-url")
    if not bot_id:
        raise ValueError("Set YELLOW_BOT_ID or pass --bot-id")

    client = YellowClient(
        api_url=api_url,
        bot_id=bot_id,
        token=token,
        timeout=timeout,
        response_path=response_path,
    )
    run_id = uuid.uuid4().hex[:10]
    results: list[dict[str, Any]] = []

    if concurrency == 1:
        for case, iteration in jobs:
            results.append(
                run_case(client, case, run_id=run_id, iteration=iteration)
            )
    else:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = {
                pool.submit(
                    run_case,
                    client,
                    case,
                    run_id=run_id,
                    iteration=iteration,
                ): (case.case_id, iteration)
                for case, iteration in jobs
            }
            for future in as_completed(futures):
                results.append(future.result())

        order = {case.case_id: index for index, case in enumerate(cases)}
        results.sort(key=lambda row: (order[row["case_id"]], row["iteration"]))

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in results:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    ok = sum(row["status"] == "ok" for row in results)
    return {
        "run_id": run_id,
        "cases": len(cases),
        "jobs": len(results),
        "ok": ok,
        "errors": len(results) - ok,
        "output": str(output),
        "behavior_counts": _count_behaviors(cases),
    }


def _count_behaviors(cases: list[EvalCase]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for case in cases:
        counts[case.behavior_label] = counts.get(case.behavior_label, 0) + 1
    return counts
