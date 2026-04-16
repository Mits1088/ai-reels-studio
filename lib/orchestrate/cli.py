"""
lib/orchestrate CLI.

Subcommands:
  match  <project-dir>  — write output/asset-matches.json
  motion <project-dir>  — write output/motion-plan.json
  plan   <project-dir>  — run match + motion + gap-owner, write all 3 artifacts

All commands are advisory: they write planning artifacts but never
modify edit-plan.json or timeline.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .match_assets import match_assets_for_project
from .motion_plan import plan_motion_for_project
from .gap_owner import assign_gaps_for_project


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _print_match_summary(result: dict) -> None:
    if result.get("skipped"):
        print(f"SKIP: {result['project']} — {result.get('reason')}")
        return
    t = result["totals"]
    print(f"Project: {result['project']}")
    print(f"Matcher: {result['matcher_version']}")
    print(f"Enrichment: {result['config']['enrichment_status_overall']}")
    print(
        f"Beats: {t['beats']}  selected={t['with_selection']}  "
        f"high_conf={t['high_confidence']}  med_conf={t['medium_confidence']}  "
        f"low_conf={t['low_confidence']}  review_required={t['human_review_required']}"
    )


def _print_motion_summary(result: dict) -> None:
    if result.get("skipped"):
        print(f"SKIP: {result['project']} — {result.get('reason')}")
        return
    t = result["totals"]
    print(f"Project: {result['project']}")
    print(f"Planner: {result['planner_version']}")
    by_cat = ", ".join(f"{k}={v}" for k, v in sorted(t["by_category"].items()))
    print(
        f"Beats: {t['beats']}  high_conf={t['high_confidence']}  "
        f"low_conf={t['low_confidence']}  violations={t['violations_total']}"
    )
    print(f"By category: {by_cat}")


def _print_gap_summary(result: dict) -> None:
    if result.get("skipped"):
        print(f"SKIP: {result['project']} — {result.get('reason')}")
        return
    t = result["totals"]
    by_type = ", ".join(f"{k}={v}" for k, v in sorted(t["by_type"].items()))
    print(f"Gaps: {t['gaps_total']}  ({by_type})")


def cmd_match(project_dir: Path) -> int:
    result = match_assets_for_project(project_dir)
    out_path = project_dir / "output" / "asset-matches.json"
    _save_json(out_path, result)
    _print_match_summary(result)
    print(f"WROTE: {out_path}")
    return 0


def cmd_motion(project_dir: Path) -> int:
    result = plan_motion_for_project(project_dir)
    out_path = project_dir / "output" / "motion-plan.json"
    _save_json(out_path, result)
    _print_motion_summary(result)
    print(f"WROTE: {out_path}")
    return 0


def cmd_gap(project_dir: Path) -> int:
    result = assign_gaps_for_project(project_dir)
    out_path = project_dir / "output" / "gap-ownership.json"
    _save_json(out_path, result)
    _print_gap_summary(result)
    print(f"WROTE: {out_path}")
    return 0


def cmd_plan(project_dir: Path) -> int:
    """Run all three planning helpers and write each artifact."""
    print("=== match ===")
    rc1 = cmd_match(project_dir)
    print()
    print("=== motion ===")
    rc2 = cmd_motion(project_dir)
    print()
    print("=== gap-ownership ===")
    rc3 = cmd_gap(project_dir)
    return max(rc1, rc2, rc3)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="lib.orchestrate",
        description="Editorial planning helpers (Phase D)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_match = sub.add_parser("match", help="Score and rank assets per beat")
    p_match.add_argument("project_dir", type=Path)

    p_motion = sub.add_parser("motion", help="Assign motion budget per beat")
    p_motion.add_argument("project_dir", type=Path)

    p_gap = sub.add_parser("gap", help="Classify and assign gap ownership")
    p_gap.add_argument("project_dir", type=Path)

    p_plan = sub.add_parser("plan", help="Run match + motion + gap together")
    p_plan.add_argument("project_dir", type=Path)

    args = parser.parse_args()

    if not args.project_dir.exists():
        print(f"ERROR: project_dir not found: {args.project_dir}")
        sys.exit(1)

    if args.cmd == "match":
        sys.exit(cmd_match(args.project_dir))
    elif args.cmd == "motion":
        sys.exit(cmd_motion(args.project_dir))
    elif args.cmd == "gap":
        sys.exit(cmd_gap(args.project_dir))
    elif args.cmd == "plan":
        sys.exit(cmd_plan(args.project_dir))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
