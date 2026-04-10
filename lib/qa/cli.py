"""
CLI entrypoint for QA.

Usage:
  python -m lib.qa.cli <project-dir>
  python -m lib.qa.cli <project-dir> --json
"""

import argparse
import json
import sys
from pathlib import Path

from .runner import run_qa_on_project


def main():
    parser = argparse.ArgumentParser(
        description="Run QA gates on a reel project",
        prog="python -m lib.qa.cli",
    )
    parser.add_argument("project_dir", type=Path, help="Project directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    report = run_qa_on_project(args.project_dir)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(report.summary())

    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
