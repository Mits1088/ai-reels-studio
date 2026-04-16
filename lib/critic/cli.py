"""
lib/critic CLI.

Subcommand: critic <project-dir>
  Reads beat-map / asset-matches / motion-plan / gap-ownership / edit-plan / catalog
  Writes:
    output/critic-report.json   (full structured report)
    output/critic-report.md     (human-readable, high-signal first)
    output/critic-status.json   (slim informational status — Phase E2)

Always exits 0 (advisory only). Phase E3 may add gating later.

Phase E2 flag:
  --severity-floor LEVEL   Filter findings below LEVEL (SUGGEST | WARN | BLOCK).
                           Default: SUGGEST (no filtering). The verdict and
                           critic_status are always computed from the unfiltered
                           findings — only the rendered findings are filtered.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .runner import (
    run_critic_for_project,
    build_critic_status_dict,
    CriticReport,
    CRITIC_VERSION,
)
from .markdown import render_critic_markdown
from .finding import (
    CriticFinding,
    SEVERITY_BLOCK,
    SEVERITY_WARN,
    SEVERITY_SUGGEST,
)
from .gate import evaluate_gate, GateContext


VALID_FLOORS = (SEVERITY_SUGGEST, SEVERITY_WARN, SEVERITY_BLOCK)


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _save_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def cmd_critic(project_dir: Path, severity_floor: str = SEVERITY_SUGGEST) -> int:
    report_dict = run_critic_for_project(project_dir, severity_floor=severity_floor)

    out_json = project_dir / "output" / "critic-report.json"
    out_md = project_dir / "output" / "critic-report.md"
    out_status = project_dir / "output" / "critic-status.json"

    _save_json(out_json, report_dict)
    _save_json(out_status, build_critic_status_dict(report_dict))

    # Re-build a CriticReport object for markdown rendering
    findings: list[CriticFinding] = []
    for beat_block in report_dict.get("beats", []):
        for f in beat_block.get("findings", []):
            findings.append(_finding_from_dict(f))
    for f in report_dict.get("global_findings", []):
        findings.append(_finding_from_dict(f))

    report = CriticReport(
        project=report_dict["project"],
        findings=findings,
        inputs_present=report_dict.get("inputs_present", {}),
        enrichment_state=report_dict.get("enrichment_state", {}),
        severity_floor=report_dict.get("severity_floor", SEVERITY_SUGGEST),
        pre_filter_total=report_dict["totals"]["pre_filter"]["total"],
        pre_filter_blockers=report_dict["totals"]["pre_filter"]["blockers"],
        pre_filter_warnings=report_dict["totals"]["pre_filter"]["warnings"],
        pre_filter_suggestions=report_dict["totals"]["pre_filter"]["suggestions"],
    )
    _save_text(out_md, render_critic_markdown(report))

    # Phase E3: also compute + write the shadow-mode gate decision for visibility.
    # The critic CLI always runs the gate in shadow mode (hard_gate_enabled=False,
    # override_used=False). The compile CLI re-evaluates with its own flags, so
    # this file is an audit/visibility artifact, not a source of truth for enforcement.
    gate_decision = evaluate_gate(
        report_dict,
        hard_gate_enabled=False,
        override_used=False,
    )
    out_gate = project_dir / "output" / "critic-gate.json"
    _save_json(out_gate, gate_decision.to_dict(project=report_dict["project"]))

    print(f"Project: {report_dict['project']}")
    print(
        f"Verdict: {report_dict['verdict']}  Status: {report_dict['critic_status']}  "
        f"(advisory mode, severity_floor={severity_floor})"
    )
    pre = report_dict["totals"]["pre_filter"]
    print(
        f"Findings (pre-filter): {pre['total']}  "
        f"(blockers={pre['blockers']}, warnings={pre['warnings']}, suggestions={pre['suggestions']})"
    )
    print(
        f"Gate (shadow): {gate_decision.gate_status}  "
        f"would_refuse={gate_decision.would_refuse_compile}  "
        f"blocking={len(gate_decision.blocking_findings)}  "
        f"conditional={len(gate_decision.conditional_findings)}"
    )
    if severity_floor != SEVERITY_SUGGEST:
        print(f"Filtered output: {report_dict['totals']['total']} findings shown")
    inputs = report_dict.get("inputs_present", {})
    missing = [k for k, v in inputs.items() if not v]
    if missing:
        print(f"Missing inputs: {', '.join(missing)}")
    print(f"WROTE: {out_json}")
    print(f"WROTE: {out_md}")
    print(f"WROTE: {out_status}")
    print(f"WROTE: {out_gate}")
    return 0


def _finding_from_dict(d: dict) -> CriticFinding:
    return CriticFinding(
        check=d["check"],
        severity=d["severity"],
        confidence=float(d["confidence"]),
        reason=d["reason"],
        evidence=d.get("evidence", {}),
        suggested_fix=d.get("suggested_fix", ""),
        beat_id=d.get("beat_id"),
        finding_id=d.get("finding_id", ""),
        related_ids=tuple(d.get("related_ids", [])),
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="lib.critic", description="Editorial critic (Phase E2 advisory)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_critic = sub.add_parser("critic", help="Run critic and write critic-report.{json,md} + critic-status.json")
    p_critic.add_argument("project_dir", type=Path)
    p_critic.add_argument(
        "--severity-floor",
        choices=VALID_FLOORS,
        default=SEVERITY_SUGGEST,
        help="Filter findings below this severity (default: SUGGEST = no filtering)",
    )

    args = parser.parse_args()

    if not args.project_dir.exists():
        print(f"ERROR: project_dir not found: {args.project_dir}")
        sys.exit(1)

    if args.cmd == "critic":
        sys.exit(cmd_critic(args.project_dir, severity_floor=args.severity_floor))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
