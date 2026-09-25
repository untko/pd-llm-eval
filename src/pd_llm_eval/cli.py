from __future__ import annotations

import argparse

from .io import load_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(prog="pd-eval")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate a canonical JSONL dataset")
    validate.add_argument("path")

    args = parser.parse_args()

    if args.command == "validate":
        cases = load_jsonl(args.path)
        print(f"valid: {len(cases)} cases")
