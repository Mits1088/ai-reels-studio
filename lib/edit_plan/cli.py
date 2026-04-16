"""
Edit-plan CLI.

Subcommands:
  validate <project-dir>   Validate output/edit-plan.json against the schema +
                           cross-references with beat-map.
  compile  <project-dir>   Compile output/edit-plan.json + audio/beat-map.json
                           into output/timeline.json (writes if not dry-run).
  summary  <project-dir>   Render output/edit-plan.md from output/edit-plan.json.
  parity   <project-dir>   Round-trip the existing output/timeline.json through
                           reverse-engineer + compile, diff against the original.
                           Used as the parity gate for Phase C.

The CLI is opt-in: nothing in the existing pipeline calls it. The
assemble-reel skill will start to invoke `compile` only when an
edit-plan.json exists in the project's output/ directory.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .model import EditPlan
from .validate import validate_edit_plan_dict, SEVERITY_BLOCK
from .compile import compile_edit_plan, CompileError
from .markdown import render_edit_plan_markdown
from .canonical import diff_timelines


# Allowed extra keys that the compiler may attach to lane entries when
# attach_planning_fields=True. Documented as Phase C "allowed diffs" for
# parity tests that exercise the enriched compile path.
_PHASE_C_ATTACHED_KEYS = {
    "template_id",
    "proof_class",
    "captionMode",
    "splitRatio",
    "avatar_mode",
    "proof_protected",
}


def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _save_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


# ── Subcommands ────────────────────────────────────────────────────────────


def cmd_validate(project_dir: Path) -> int:
    plan_path = project_dir / "output" / "edit-plan.json"
    if not plan_path.exists():
        print(f"ERROR: edit-plan.json not found: {plan_path}")
        return 1
    plan_dict = _load_json(plan_path)

    beat_ids: set[str] = set()
    bm_path = project_dir / "audio" / "beat-map.json"
    if bm_path.exists():
        bm = _load_json(bm_path)
        beat_ids = {b["id"] for b in bm.get("beats", []) if "id" in b}

    errs = validate_edit_plan_dict(plan_dict, beat_ids=beat_ids or None)
    blockers = [e for e in errs if e.severity == SEVERITY_BLOCK]

    if not errs:
        print(f"PASSED: {plan_path}")
        return 0

    print(f"{len(errs)} finding(s) ({len(blockers)} blocker(s)):")
    for e in errs:
        print(f"  {e}")
    return 1 if blockers else 0


def cmd_compile(
    project_dir: Path,
    dry_run: bool = False,
    *,
    hard_critic_gate: bool = False,
    allow_critic_blocked: bool = False,
) -> int:
    plan_path = project_dir / "output" / "edit-plan.json"
    if not plan_path.exists():
        print(f"ERROR: edit-plan.json not found: {plan_path}")
        return 1
    bm_path = project_dir / "audio" / "beat-map.json"
    if not bm_path.exists():
        print(f"ERROR: beat-map.json not found: {bm_path}")
        return 1

    plan_dict = _load_json(plan_path)
    bm = _load_json(bm_path)

    try:
        plan = EditPlan.from_dict(plan_dict)
    except (KeyError, ValueError) as e:
        print(f"ERROR: edit-plan.json is malformed: {e}")
        return 1

    # Phase E3: consult the critic gate before compiling.
    # - If no critic-report.json exists, gate is skipped (no-op).
    # - By default (shadow mode), the gate decision is computed and printed
    #   but does not prevent compile.
    # - With --hard-critic-gate, a blocking gate refuses compile unless
    #   --allow-critic-blocked is passed.
    gate_decision = None
    critic_report_path = project_dir / "output" / "critic-report.json"
    if critic_report_path.exists():
        from lib.critic.gate import evaluate_gate
        try:
            critic_report = _load_json(critic_report_path)
        except Exception as e:
            print(f"WARNING: critic-report.json malformed, skipping gate: {e}")
            critic_report = None
        if critic_report:
            gate_decision = evaluate_gate(
                critic_report,
                hard_gate_enabled=hard_critic_gate,
                override_used=allow_critic_blocked,
            )
            mode = "hard" if hard_critic_gate else "shadow"
            print(
                f"Critic gate ({mode}): {gate_decision.gate_status}  "
                f"would_refuse={gate_decision.would_refuse_compile}  "
                f"actual_refuse={gate_decision.actual_refuse_compile}"
            )
            if gate_decision.blocking_findings:
                for f in gate_decision.blocking_findings[:3]:
                    print(f"  - [{f['check']}] {f.get('beat_id') or 'global'}: "
                          f"{(f.get('reason') or '')[:80]}")
            if gate_decision.actual_refuse_compile:
                print("COMPILE REFUSED by critic gate. "
                      "Override with --allow-critic-blocked.")
                return 1

    try:
        timeline = compile_edit_plan(plan, bm, attach_planning_fields=True)
    except CompileError as e:
        print(f"COMPILE ERROR: {e}")
        return 1

    if dry_run:
        print(f"DRY RUN: would write {len(json.dumps(timeline))} bytes to output/timeline.json")
        return 0

    out_path = project_dir / "output" / "timeline.json"
    _save_json(out_path, timeline)
    print(f"COMPILED: {out_path}")
    return 0


def cmd_summary(project_dir: Path) -> int:
    plan_path = project_dir / "output" / "edit-plan.json"
    if not plan_path.exists():
        print(f"ERROR: edit-plan.json not found: {plan_path}")
        return 1
    plan_dict = _load_json(plan_path)
    try:
        plan = EditPlan.from_dict(plan_dict)
    except (KeyError, ValueError) as e:
        print(f"ERROR: edit-plan.json is malformed: {e}")
        return 1
    md = render_edit_plan_markdown(plan)
    out_path = project_dir / "output" / "edit-plan.md"
    _save_text(out_path, md)
    print(f"WROTE: {out_path}")
    return 0


def cmd_parity(project_dir: Path) -> int:
    """Round-trip the existing timeline through reverse-engineer + compile."""
    from .reverse import reverse_engineer

    tl_path = project_dir / "output" / "timeline.json"
    bm_path = project_dir / "audio" / "beat-map.json"
    if not tl_path.exists() or not bm_path.exists():
        print(f"ERROR: missing timeline.json or beat-map.json in {project_dir}")
        return 1

    timeline_orig = _load_json(tl_path)
    bm = _load_json(bm_path)

    plan = reverse_engineer(timeline_orig, bm, project_slug=project_dir.name)
    try:
        timeline_compiled = compile_edit_plan(plan, bm, attach_planning_fields=False)
    except CompileError as e:
        print(f"PARITY FAIL: compile error: {e}")
        return 1

    diffs = diff_timelines(
        timeline_orig, timeline_compiled,
        allowed_extra_keys=_PHASE_C_ATTACHED_KEYS,
    )
    if not diffs:
        print(f"PARITY PASS: {project_dir.name} round-trip exact")
        return 0

    print(f"PARITY DIFF: {project_dir.name} — {len(diffs)} difference(s):")
    for d in diffs[:50]:
        print(f"  {d}")
    if len(diffs) > 50:
        print(f"  ... and {len(diffs) - 50} more")
    return 1


# ── Main entry ─────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(prog="lib.edit_plan", description="Edit-plan compiler CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_validate = sub.add_parser("validate", help="Validate output/edit-plan.json")
    p_validate.add_argument("project_dir", type=Path)

    p_compile = sub.add_parser("compile", help="Compile edit-plan.json into timeline.json")
    p_compile.add_argument("project_dir", type=Path)
    p_compile.add_argument("--dry-run", action="store_true")
    p_compile.add_argument(
        "--hard-critic-gate",
        action="store_true",
        help="Phase E3 testing flag: enforce the critic gate (refuse compile when blocked)",
    )
    p_compile.add_argument(
        "--allow-critic-blocked",
        action="store_true",
        help="Override the critic gate even in hard mode (plumbed through for emergencies)",
    )

    p_summary = sub.add_parser("summary", help="Render edit-plan.md from edit-plan.json")
    p_summary.add_argument("project_dir", type=Path)

    p_parity = sub.add_parser("parity", help="Round-trip parity check on existing timeline.json")
    p_parity.add_argument("project_dir", type=Path)

    args = parser.parse_args()

    if not args.project_dir.exists():
        print(f"ERROR: project_dir not found: {args.project_dir}")
        sys.exit(1)

    if args.cmd == "validate":
        sys.exit(cmd_validate(args.project_dir))
    elif args.cmd == "compile":
        sys.exit(cmd_compile(
            args.project_dir,
            dry_run=args.dry_run,
            hard_critic_gate=args.hard_critic_gate,
            allow_critic_blocked=args.allow_critic_blocked,
        ))
    elif args.cmd == "summary":
        sys.exit(cmd_summary(args.project_dir))
    elif args.cmd == "parity":
        sys.exit(cmd_parity(args.project_dir))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
