"""
lib.brain CLI — project diagnosis, advance, repair, and portfolio sweep.

Usage:
    python -m lib.brain diagnose projects/<slug>
    python -m lib.brain diagnose projects/<slug> --json
    python -m lib.brain diagnose projects/<slug> --json --out diagnosis.json

    python -m lib.brain advance  projects/<slug>
    python -m lib.brain advance  projects/<slug> --dry-run

    python -m lib.brain repair   projects/<slug>

    python -m lib.brain sweep    projects/
    python -m lib.brain sweep    projects/ --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# ── ANSI helpers (degrade gracefully on non-ANSI terminals) ──────────────────

def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"

GREEN  = lambda t: _c(t, "32")
RED    = lambda t: _c(t, "31")
YELLOW = lambda t: _c(t, "33")
CYAN   = lambda t: _c(t, "36")
BOLD   = lambda t: _c(t, "1")
DIM    = lambda t: _c(t, "2")


def _fmt_delta(seconds: float) -> str:
    """Human-readable age delta: '2h 14m', '45s', etc."""
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m {s % 60}s"
    h = s // 3600
    m = (s % 3600) // 60
    return f"{h}h {m}m" if m else f"{h}h"


# ── Human-readable renderer ───────────────────────────────────────────────────

def _render_human(diag) -> str:
    from .models import Diagnosis
    d: Diagnosis = diag
    lines: list[str] = []

    W = 60
    lines.append("╔" + "═" * W + "╗")
    title = f"  Brain Diagnosis: {d.slug}"
    lines.append(f"║{title:<{W}}║")
    lines.append("╚" + "═" * W + "╝")
    lines.append("")

    # ── Project health ────────────────────────────────────────────────────────
    if not d.project_json_found:
        lines.append(f"  {RED('✗')} project.json not found — cannot diagnose further")
        lines.append("")
        return "\n".join(lines)

    sv_display = str(d.schema_version) if d.schema_version is not None else "missing"
    schema_color = GREEN if d.schema_ok else RED
    lines.append(f"  {BOLD('Project')}    : {d.title or d.slug}")
    lines.append(f"  {BOLD('Phase')}      : {CYAN(d.phase)}  ({d.status})")
    lines.append(f"  {BOLD('Style')}      : {d.style}")
    lines.append(f"  {BOLD('Theme')}      : {d.theme}  {DIM(d.theme_primary)}")
    lines.append(f"  {BOLD('Schema')}     : {schema_color(sv_display)}")
    if d.validation_errors:
        for err in d.validation_errors:
            lines.append(f"    {RED('!')} {err}")
    lines.append("")

    # ── Gate inventory ────────────────────────────────────────────────────────
    g = d.gates
    lines.append(BOLD(f"Gates  {len(g.passed)}/{g.total}"))
    for gate in g.passed:
        lines.append(f"  {GREEN('✓')} {gate}")
    for i, gate in enumerate(g.missing):
        if i == 0:
            lines.append(f"  {YELLOW('←')} {gate}  {YELLOW('← NEXT')}")
        else:
            lines.append(f"  {DIM('○')} {gate}")
    if g.unknown_gates:
        for ug in g.unknown_gates:
            lines.append(f"  {RED('?')} {ug}  {RED('(unknown gate — suspicious)')}")
    lines.append("")

    # ── Artifact inventory ────────────────────────────────────────────────────
    lines.append(BOLD("Key Artifacts"))
    for entry in d.artifacts.entries:
        if entry.present:
            kb = entry.size_bytes / 1024
            lines.append(f"  {GREEN('✓')} {entry.path}  {DIM(f'({kb:.1f} KB)')}")
        else:
            lines.append(f"  {DIM('○')} {entry.path}")

    if d.artifacts.gate_artifact_mismatches:
        lines.append("")
        lines.append(f"  {RED('Gate–Artifact Mismatches (suspicious):')}")
        for m in d.artifacts.gate_artifact_mismatches:
            lines.append(f"    {RED('!')} {m}")

    if d.artifacts.staleness_results:
        lines.append("")
        lines.append(BOLD("Staleness"))
        _CONF_COLOR = {"high": RED, "medium": YELLOW, "low": DIM}
        for r in d.artifacts.staleness_results:
            color = _CONF_COLOR.get(r.confidence, DIM)
            delta_str = _fmt_delta(r.age_delta_seconds)
            lines.append(
                f"  {color('⚠')} [{r.confidence}] "
                f"'{r.upstream}' → '{r.downstream}' ({delta_str} newer)"
            )
            # First sentence of the reason is enough for the console
            short_reason = r.reason.split(".")[0] + "."
            lines.append(f"    {DIM(short_reason)}")
            lines.append(f"    {DIM('→ ' + r.recommended_action)}")
    lines.append("")

    # ── QA status ─────────────────────────────────────────────────────────────
    q = d.qa
    if not q.available:
        qa_label = DIM("not run")
    elif q.verdict == "PASS":
        qa_label = GREEN("PASS")
    elif q.verdict == "PASS_WITH_WARNINGS":
        qa_label = YELLOW("PASS_WITH_WARNINGS")
    elif q.verdict == "FAIL":
        qa_label = RED("FAIL")
    else:
        qa_label = YELLOW(q.verdict)

    lines.append(BOLD("QA Status") + f"  {qa_label}")
    if q.available:
        lines.append(f"  Blockers: {q.blockers}  Warnings: {q.warnings}")
        if q.report_timestamp:
            lines.append(f"  Timestamp: {DIM(q.report_timestamp[:19].replace('T',' '))}")
        if q.top_blockers:
            for b in q.top_blockers:
                lines.append(f"  {RED('!')} {b}")
    lines.append("")

    # ── Critic status ─────────────────────────────────────────────────────────
    c = d.critic
    if not c.available:
        critic_label = DIM("not run")
    elif c.status == "critic_passed":
        critic_label = GREEN("passed")
    elif c.status == "critic_warnings":
        critic_label = YELLOW("warnings")
    elif c.status == "critic_blocked":
        critic_label = RED("blocked")
    else:
        critic_label = DIM(c.status)

    lines.append(BOLD("Critic") + f"  {critic_label}")
    if c.available:
        lines.append(f"  Findings: {c.findings_count}  Highest: {c.highest_severity}")
        for f in c.top_findings:
            lines.append(f"  {DIM('·')} {f}")
        if d.critic_advisory_signal:
            lines.append(
                f"  {YELLOW('⚠')} critic_blocked is advisory — "
                f"add --critic-hard-mode to make it a render blocker"
            )
    lines.append("")

    # ── Autonomy verdict ──────────────────────────────────────────────────────
    av = d.autonomy
    lines.append(BOLD("Verdict"))

    if av.can_continue_autonomously:
        lines.append(f"  {GREEN('→ Claude can continue autonomously')}  {DIM(f'[confidence: {av.confidence}]')}")
    elif av.human_required:
        lines.append(f"  {YELLOW('⏸ Human approval required')}  {DIM(f'[confidence: {av.confidence}]')}")
        if av.human_required_reason:
            lines.append(f"  {DIM(av.human_required_reason)}")
    else:
        lines.append(f"  {RED('✗ Blocked')}  {DIM(f'[confidence: {av.confidence}]')}")

    lines.append("")
    lines.append(f"  {BOLD('Next action')} : {av.next_action}")
    lines.append(f"  {BOLD('Actor')}       : {av.next_action_actor}")
    if av.next_action_command:
        lines.append(f"  {BOLD('Command')}     : {DIM(av.next_action_command)}")
    lines.append("")

    # ── Health summary ────────────────────────────────────────────────────────
    if d.healthy:
        lines.append(GREEN("  ✓ Project is healthy."))
    else:
        issues = d.validation_errors + d.artifacts.gate_artifact_mismatches
        if d.qa.available and d.qa.verdict == "FAIL":
            issues.append(f"QA FAIL — {d.qa.blockers} blocker(s)")
        lines.append(RED(f"  ✗ Project has {len(issues)} issue(s)."))
    lines.append("")

    return "\n".join(lines)


# ── diagnose command ──────────────────────────────────────────────────────────

def cmd_diagnose(
    project_dir: Path,
    json_mode: bool,
    out_path: Path | None,
    critic_hard_mode: bool = False,
) -> int:
    from .diagnose import diagnose_project

    if not project_dir.exists():
        print(f"ERROR: project directory not found: {project_dir}", file=sys.stderr)
        return 1

    diag = diagnose_project(project_dir, critic_hard_mode=critic_hard_mode)

    if json_mode:
        output = json.dumps(diag.to_dict(), indent=2, ensure_ascii=False)
    else:
        output = _render_human(diag)

    if out_path:
        out_path.write_text(output, encoding="utf-8")
        print(f"Written to {out_path}", file=sys.stderr)
    else:
        print(output)

    # Exit 1 if project is blocked or unhealthy (useful in CI / hooks)
    return 0 if diag.healthy else 1


# ── advance command ───────────────────────────────────────────────────────────

def cmd_advance(
    project_dir: Path,
    execute: bool,
    json_mode: bool,
    critic_hard_mode: bool = False,
) -> int:
    from .advance import advance_project

    if not project_dir.exists():
        print(f"ERROR: project directory not found: {project_dir}", file=sys.stderr)
        return 1

    result = advance_project(project_dir, execute=execute, critic_hard_mode=critic_hard_mode)

    if json_mode:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return 0 if result.status in ("succeeded", "skipped", "dry_run") else 1

    # ── Human-readable output ─────────────────────────────────────────────
    status_label = {
        "succeeded": GREEN("succeeded"),
        "skipped":   YELLOW("skipped"),
        "failed":    RED("failed"),
        "dry_run":   CYAN("dry-run"),
    }.get(result.status, result.status)

    print(f"\n{BOLD('Brain Advance')}  [{status_label}]")
    print(f"  Project : {result.project_slug}")
    if result.phase_key:
        print(f"  Phase   : {result.phase_key}")
    print(f"  Actor   : {result.actor}")
    if result.gate_target:
        if result.executed:
            print(f"  Gate    : {GREEN(result.gate_target)} ← set")
        else:
            print(f"  Gate    : {DIM(result.gate_target)} (would set)")
    print()

    # Reason
    print(f"  {DIM(result.reason)}")
    print()

    # Would-execute hint
    if not result.executed:
        print(f"  {BOLD('Would run:')} {DIM(result.would_execute)}")
        print()

    # Output (trimmed)
    if result.output:
        for line in result.output.strip().splitlines()[:10]:
            print(f"  {line}")
        print()

    if result.error:
        print(f"  {RED('Error:')} {result.error}")
        print()

    # Post-advance state snapshot from re_diagnosis_summary
    if result.re_diagnosis_summary:
        s = result.re_diagnosis_summary
        gates_str = f"{s['gates_passed']}/{s['gates_total']}"
        healthy = GREEN("healthy") if s["healthy"] else RED("unhealthy")
        print(f"  State  : {healthy}  |  Gates: {gates_str}  |  Phase: {s['phase']}")
        if s["human_required"]:
            print(f"  {YELLOW('⏸')} Waiting for human input")
        elif s["can_continue"]:
            print(f"  {GREEN('▶')} Next: {s['next_action']}")
        else:
            print(f"  {RED('✗')} Blocked: {s['next_action']}")
        print()

    return 0 if result.status in ("succeeded", "skipped", "dry_run") else 1


# ── repair command ────────────────────────────────────────────────────────────

def cmd_repair(
    project_dir: Path,
    json_mode: bool = False,
    critic_hard_mode: bool = False,
    include_critic: bool = False,
) -> int:
    from .repair import repair_project

    if not project_dir.exists():
        print(f"ERROR: project directory not found: {project_dir}", file=sys.stderr)
        return 1

    plan = repair_project(
        project_dir, critic_hard_mode=critic_hard_mode, include_critic=include_critic
    )

    if json_mode:
        print(json.dumps(plan.to_dict(), indent=2, ensure_ascii=False))
    else:
        print()
        print(plan.render())
        print()
    return 0


# ── sweep command ─────────────────────────────────────────────────────────────

def cmd_sweep(
    projects_dir: Path,
    json_mode: bool,
    critic_hard_mode: bool = False,
) -> int:
    from .sweep import sweep_projects, format_sweep_table, format_sweep_json

    if not projects_dir.exists():
        print(f"ERROR: projects directory not found: {projects_dir}", file=sys.stderr)
        return 1

    summaries = sweep_projects(projects_dir, critic_hard_mode=critic_hard_mode)

    if json_mode:
        print(format_sweep_json(summaries))
    else:
        print()
        print(format_sweep_table(summaries))
        print()

    # Exit 1 if any project is unhealthy (useful for CI / hooks)
    return 0 if all(s.healthy for s in summaries) else 1


# ── main ──────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lib.brain",
        description="AI Reels production brain — diagnose, advance, repair, sweep.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    def _add_critic_flag(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--critic-hard-mode",
            dest="critic_hard_mode",
            action="store_true",
            default=False,
            help=(
                "Treat critic_blocked as a render blocker. "
                "Default: advisory (critic findings never block advancement)."
            ),
        )

    # diagnose
    p_diag = sub.add_parser("diagnose", help="Diagnose a project directory")
    p_diag.add_argument("project_dir", type=Path, help="Path to project directory")
    p_diag.add_argument("--json", dest="json_mode", action="store_true",
                        help="Output machine-readable JSON")
    p_diag.add_argument("--out", dest="out_path", type=Path, default=None,
                        help="Write output to file instead of stdout")
    _add_critic_flag(p_diag)

    # advance
    p_adv = sub.add_parser(
        "advance",
        help="Show (or execute) the next code-safe pipeline step",
    )
    p_adv.add_argument("project_dir", type=Path, help="Path to project directory")
    p_adv.add_argument("--execute", dest="execute", action="store_true",
                       help="Execute the phase (default is dry-run)")
    p_adv.add_argument("--json", dest="json_mode", action="store_true",
                       help="Output machine-readable JSON")
    _add_critic_flag(p_adv)

    # repair
    p_rep = sub.add_parser(
        "repair",
        help="Generate a structured repair plan for a blocked project",
    )
    p_rep.add_argument("project_dir", type=Path, help="Path to project directory")
    p_rep.add_argument("--json", dest="json_mode", action="store_true",
                       help="Output machine-readable JSON")
    p_rep.add_argument(
        "--include-critic",
        dest="include_critic",
        action="store_true",
        default=False,
        help=(
            "Include structured per-finding critic repair steps with critic_id and severity. "
            "Default: summary step only."
        ),
    )
    _add_critic_flag(p_rep)

    # sweep
    p_sw = sub.add_parser(
        "sweep",
        help="Portfolio health scan — diagnose all projects",
    )
    p_sw.add_argument(
        "projects_dir",
        type=Path,
        nargs="?",
        default=Path("projects"),
        help="Directory containing project directories (default: projects/)",
    )
    p_sw.add_argument("--json", dest="json_mode", action="store_true",
                      help="Output machine-readable JSON array")
    _add_critic_flag(p_sw)

    args = parser.parse_args(argv)

    if args.cmd == "diagnose":
        return cmd_diagnose(
            project_dir=args.project_dir,
            json_mode=args.json_mode,
            out_path=args.out_path,
            critic_hard_mode=args.critic_hard_mode,
        )
    if args.cmd == "advance":
        return cmd_advance(
            project_dir=args.project_dir,
            execute=args.execute,
            json_mode=args.json_mode,
            critic_hard_mode=args.critic_hard_mode,
        )
    if args.cmd == "repair":
        return cmd_repair(
            project_dir=args.project_dir,
            json_mode=args.json_mode,
            critic_hard_mode=args.critic_hard_mode,
            include_critic=args.include_critic,
        )
    if args.cmd == "sweep":
        return cmd_sweep(
            projects_dir=args.projects_dir,
            json_mode=args.json_mode,
            critic_hard_mode=args.critic_hard_mode,
        )

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
