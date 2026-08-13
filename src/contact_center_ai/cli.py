"""Command-line interface for batch analysis and evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .evaluation import evaluate_topics
from .pipeline import analyze_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Privacy-first contact center analytics")
    commands = parser.add_subparsers(dest="command", required=True)
    analyze = commands.add_parser("analyze")
    analyze.add_argument("input", type=Path)
    analyze.add_argument("--output-dir", type=Path, default=Path("output"))
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("input", type=Path)
    args = parser.parse_args()

    if args.command == "analyze":
        output, summary = analyze_file(args.input, args.output_dir)
        print(json.dumps({"output": str(output), **summary}, indent=2))
    else:
        print(json.dumps(evaluate_topics(args.input), indent=2))


if __name__ == "__main__":
    main()

