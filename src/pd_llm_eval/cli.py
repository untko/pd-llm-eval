from __future__ import annotations

import argparse
import json

from .io import load_jsonl
from .yellow import run_yellow_batch


def main() -> None:
    parser = argparse.ArgumentParser(prog="pd-eval")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate a canonical JSONL dataset")
    validate.add_argument("path")

    run_yellow = subparsers.add_parser(
        "run-yellow",
        help="Run a canonical dataset against a Yellow.ai bot endpoint",
    )
    run_yellow.add_argument("dataset", help="JSONL file or directory of JSONL files")
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
        cases = load_jsonl(args.path)
        print(f"valid: {len(cases)} cases")
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
