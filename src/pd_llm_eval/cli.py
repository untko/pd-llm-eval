from __future__ import annotations

import argparse
import json

from .io import load_dataset
from .kb import KnowledgeBase, validate_case_sources
from .opencode_judge import judge_opencode_results
from .opencode_runner import run_opencode_batch
from .report import render_markdown_report
from .yellow import run_yellow_batch


def main() -> None:
    parser = argparse.ArgumentParser(prog="pd-eval")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate a canonical dataset")
    validate.add_argument("path")

    run_local = subparsers.add_parser(
        "run-opencode",
        help="Run cases against a model configured in OpenCode",
    )
    run_local.add_argument("dataset", help="cases.json, JSONL file, or dataset directory")
    run_local.add_argument("--model", required=True, help="OpenCode provider/model ID")
    run_local.add_argument("--mode", choices=["oracle", "closed-book"], default="oracle")
    run_local.add_argument("--out", default="results/opencode.jsonl")
    run_local.add_argument("--timeout", type=float, default=180.0)
    run_local.add_argument("--iterations", type=int, default=1)
    run_local.add_argument("--concurrency", type=int, default=1)
    run_local.add_argument("--limit", type=int)
    run_local.add_argument("--dry-run", action="store_true")
    run_local.add_argument(
        "--kb",
        help="Path to kb_structure.json. Defaults to PD_KB_PATH when set.",
    )

    judge_local = subparsers.add_parser(
        "judge-opencode",
        help="Judge saved model responses with another OpenCode model",
    )
    judge_local.add_argument("dataset")
    judge_local.add_argument("results")
    judge_local.add_argument("--model", required=True, help="Judge provider/model ID")
    judge_local.add_argument("--out", default="results/opencode-judged.jsonl")
    judge_local.add_argument("--timeout", type=float, default=180.0)
    judge_local.add_argument("--limit", type=int)

    validate_sources = subparsers.add_parser(
        "validate-sources",
        help="Validate every gold_source against an actual kb_structure.json",
    )
    validate_sources.add_argument("dataset")
    validate_sources.add_argument("--kb", required=True)

    report = subparsers.add_parser("report", help="Render JSONL results as readable Markdown")
    report.add_argument("results")
    report.add_argument("--out", default="results/report.md")

    run_yellow = subparsers.add_parser(
        "run-yellow",
        help="Run a canonical dataset against a Yellow.ai bot endpoint",
    )
    run_yellow.add_argument("dataset", help="cases.json, JSONL file, or dataset directory")
    run_yellow.add_argument("--out", default="results/yellow.jsonl")
    run_yellow.add_argument("--api-url")
    run_yellow.add_argument("--bot-id")
    run_yellow.add_argument("--response-path")
    run_yellow.add_argument("--timeout", type=float, default=60.0)
    run_yellow.add_argument("--iterations", type=int, default=1)
    run_yellow.add_argument("--concurrency", type=int, default=1)
    run_yellow.add_argument("--limit", type=int)
    run_yellow.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if args.command == "validate":
        cases = load_dataset(args.path)
        print(f"valid: {len(cases)} cases")
        return

    if args.command == "run-opencode":
        summary = run_opencode_batch(
            args.dataset,
            args.out,
            model=args.model,
            mode=args.mode,
            timeout=args.timeout,
            iterations=args.iterations,
            concurrency=args.concurrency,
            limit=args.limit,
            dry_run=args.dry_run,
            kb_path=args.kb,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    if args.command == "validate-sources":
        cases = load_dataset(args.dataset)
        missing = validate_case_sources(cases, KnowledgeBase(args.kb))
        summary = {
            "cases": len(cases),
            "source_refs": sum(len(case.gold_sources) for case in cases),
            "missing": missing,
            "valid": not missing,
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if missing:
            raise SystemExit(1)
        return

    if args.command == "judge-opencode":
        summary = judge_opencode_results(
            args.dataset,
            args.results,
            args.out,
            model=args.model,
            timeout=args.timeout,
            limit=args.limit,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    if args.command == "report":
        summary = render_markdown_report(args.results, args.out)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    if args.command == "run-yellow":
        summary = run_yellow_batch(
            args.dataset,
            args.out,
            api_url=args.api_url,
            bot_id=args.bot_id,
            timeout=args.timeout,
            response_path=args.response_path,
            iterations=args.iterations,
            concurrency=args.concurrency,
            limit=args.limit,
            dry_run=args.dry_run,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
