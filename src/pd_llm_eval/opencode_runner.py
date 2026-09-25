import json
import os
import subprocess
import time
import typing
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .io import load_dataset
from .models import EvalCase


def build_prompt(case: EvalCase, mode: str) -> str:
    history = "\n".join(
        f"{message.role.upper()}: {message.content}" for message in case.conversation_context
    ) or "(none)"

    context = "(none)"
    if mode == "oracle" and case.behavior_label == "answerable":
        if case.required_facts:
            context = "\n".join(f"- {fact}" for fact in case.required_facts)
        elif case.reference_answer:
            context = case.reference_answer

    return (
        f"Evaluation mode: {mode}\n\n"
        f"Conversation so far:\n{history}\n\n"
        f"Approved knowledge context:\n{context}\n\n"
        f"Current user message:\n{case.user_input}\n\n"
        "Reply as the farmer-support assistant. Return only the user-facing reply."
    )


def run_opencode(
    prompt: str,
    *,
    model: str,
    agent: str,
    timeout: float,
) -> tuple[str, float]:
    command = ["opencode", "run", "--model", model, "--agent", agent, prompt]
    env = dict(os.environ)
    env["NO_COLOR"] = "1"

    started = time.perf_counter()
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        check=False,
    )
    latency_ms = (time.perf_counter() - started) * 1000

    if result.returncode != 0:
        error = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"OpenCode exited {result.returncode}: {error[:2000]}")

    return result.stdout.strip(), latency_ms


def _run_case(
    case: EvalCase,
    *,
    model: str,
    mode: str,
    timeout: float,
    run_id: str,
    iteration: int,
) -> dict[str, typing.Any]:
    try:
        answer, latency_ms = run_opencode(
            build_prompt(case, mode),
            model=model,
            agent="pd-eval-respondent",
            timeout=timeout,
        )
        return {
            "run_id": run_id,
            "target": "opencode",
            "model": model,
            "mode": mode,
            "case_id": case.case_id,
            "iteration": iteration,
            "status": "ok",
            "behavior_label": case.behavior_label,
            "expected_action": case.expected_action,
            "assistant_text": answer,
            "latency_ms": round(latency_ms, 2),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "run_id": run_id,
            "target": "opencode",
            "model": model,
            "mode": mode,
            "case_id": case.case_id,
            "iteration": iteration,
            "status": "error",
            "behavior_label": case.behavior_label,
            "expected_action": case.expected_action,
            "error": str(exc),
        }


def run_opencode_batch(
    dataset: str | Path,
    output: str | Path,
    *,
    model: str,
    mode: str = "oracle",
    timeout: float = 180.0,
    iterations: int = 1,
    concurrency: int = 1,
    limit: int | None = None,
    dry_run: bool = False,
) -> dict[str, typing.Any]:
    if mode not in {"oracle", "closed-book"}:
        raise ValueError("mode must be 'oracle' or 'closed-book'")

    cases = load_dataset(dataset)
    if limit is not None:
        cases = cases[:limit]

    jobs = [(case, i) for case in cases for i in range(1, iterations + 1)]
    if dry_run:
        return {
            "model": model,
            "mode": mode,
            "cases": len(cases),
            "jobs": len(jobs),
            "output": str(output),
        }

    run_id = uuid.uuid4().hex[:10]
    results: list[dict[str, typing.Any]] = []

    if concurrency == 1:
        for case, iteration in jobs:
            results.append(
                _run_case(
                    case,
                    model=model,
                    mode=mode,
                    timeout=timeout,
                    run_id=run_id,
                    iteration=iteration,
                )
            )
    else:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [
                pool.submit(
                    _run_case,
                    case,
                    model=model,
                    mode=mode,
                    timeout=timeout,
                    run_id=run_id,
                    iteration=iteration,
                )
                for case, iteration in jobs
            ]
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
        "model": model,
        "mode": mode,
        "cases": len(cases),
        "jobs": len(results),
        "ok": ok,
        "errors": len(results) - ok,
        "output": str(output),
    }
