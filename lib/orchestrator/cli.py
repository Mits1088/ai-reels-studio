"""
lib/orchestrator/cli.py — Orchestrator CLI commands.

Commands:
  status     projects/<slug>              — quick state summary
  next       projects/<slug>              — legal next actions (compact)
  diagnose   projects/<slug>              — full diagnostic with gates, artifacts, parity
  approve    projects/<slug> <gate-id>    — record human approval; set gate
  reject     projects/<slug> <phase-key>  — record rejection; move to revision
  resume     projects/<slug>              — show what's needed to resume
  invalidate projects/<slug> <artifact>   — cascade-invalidate from changed artifact
  history    projects/<slug>              — show orchestration event log
  run        projects/<slug>              — advance through legal phases; pause at claude/human
  run-phase  projects/<slug> <phase-key>  — run one specific phase

Usage:
  python -m lib.orchestrator <command> projects/<slug> [args]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .state import load_snapshot, state_label
from .transitions import compute_next_actions
from .validators import validate_phase_preconditions, check_required_artifacts
from .invalidation import invalidate_from_change
from .events import log_event, read_events
from .results import ExecResult, ExecStatus
from .spec import PHASES, PARITY_REQUIRED_BEFORE


# ── Colour helpers (graceful degradation on non-ANSI terminals) ────────────

def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"

GREEN  = lambda t: _c(t, "32")
RED    = lambda t: _c(t, "31")
YELLOW = lambda t: _c(t, "33")
CYAN   = lambda t: _c(t, "36")
BOLD   = lambda t: _c(t, "1")
DIM    = lambda t: _c(t, "2")


# ── status ─────────────────────────────────────────────────────────────────

def cmd_status(project_dir: Path) -> int:
    snap = load_snapshot(project_dir)
    g = snap.gates_passed
    total_gates = 11  # reel pipeline

    print(f"{BOLD(f'Project: {snap.slug}')}")
    print(f"  State  : {CYAN(state_label(snap.orchestration_state))}")
    print(f"  Phase  : {snap.phase} ({snap.status})")
    print(f"  Style  : {snap.style}")
    print(f"  Theme  : {snap.theme} ({snap.theme_primary})")
    print(f"  Gates  : {GREEN(str(len(g)))}/{total_gates} passed")

    actions = compute_next_actions(snap)
    unblocked = [a for a in actions if not a.blocked]
    if unblocked:
        print(f"\n  Next:")
        for a in unblocked[:3]:
            opt = DIM(" [optional]") if a.optional else ""
            cis = YELLOW(" ★ Creative Intent Summary required") if a.creative_intent_required else ""
            print(f"    → {a.name} ({a.actor}){opt}{cis}")
    else:
        print(f"\n  {GREEN('No blockers — project may be complete.')}")

    return 0


# ── next ───────────────────────────────────────────────────────────────────

def cmd_next(project_dir: Path) -> int:
    snap = load_snapshot(project_dir)
    actions = compute_next_actions(snap)

    if not actions:
        print(f"{GREEN('Project is complete or no actions available.')}")
        return 0

    print(f"{BOLD('Legal next actions')} for {snap.slug} [{state_label(snap.orchestration_state)}]\n")

    for a in actions:
        if a.blocked:
            icon = RED("✗")
            blocked_note = f"  {RED(f'BLOCKED: {a.blocked_reason}')}"
        else:
            icon = GREEN("→")
            blocked_note = ""

        opt = DIM(" [optional]") if a.optional else ""
        cis = YELLOW(" [CIS required]") if a.creative_intent_required else ""
        par = DIM(f" [{a.parallel_label}]") if a.parallel_label else ""
        print(f"  {icon}  {BOLD(a.name)}{opt}{cis}{par}")
        print(f"       Actor  : {a.actor}")
        print(f"       Run    : {DIM(a.command_hint)}")
        if a.notes:
            print(f"       Notes  : {DIM(a.notes)}")
        if blocked_note:
            print(blocked_note)
        print()

    return 0


# ── diagnose ───────────────────────────────────────────────────────────────

def cmd_diagnose(project_dir: Path) -> int:
    snap = load_snapshot(project_dir)
    g = set(snap.gates_passed)

    from lib.constants import GATE_ORDER

    # Header
    width = 56
    print("╔" + "═" * width + "╗")
    title = f"  Project: {snap.slug}"
    print(f"║{title:<{width}}║")
    print("╚" + "═" * width + "╝")
    print()

    # State block
    print(f"  {BOLD('State')}      : {CYAN(state_label(snap.orchestration_state))}")
    print(f"  {BOLD('Phase')}      : {snap.phase} ({snap.status})")
    print(f"  {BOLD('Style')}      : {snap.style}")
    print(f"  {BOLD('Theme')}      : {snap.theme} ({snap.theme_primary})")
    if snap.render_artifact:
        print(f"  {BOLD('Render')}     : {GREEN(str(snap.render_artifact.relative_to(project_dir)))}")
    print()

    # Gate checklist
    print(BOLD("Gates:"))
    for gate in GATE_ORDER:
        if gate in g:
            print(f"  {GREEN('✓')} {gate}")
        else:
            is_next = _is_next_gate(gate, g, GATE_ORDER)
            marker = YELLOW("← NEXT REQUIRED") if is_next else ""
            print(f"  {RED('✗')} {gate}  {marker}")
    print()

    # Required artifact check
    missing_artifacts = check_required_artifacts(snap)
    print(BOLD("Required Artifacts:"))
    _print_artifact_row("brief.md", project_dir)
    _print_artifact_row("script.md", project_dir)
    _print_artifact_row("audio/beat-map.json", project_dir)
    _print_artifact_row("shot-list.md", project_dir)
    _print_artifact_row("output/motion-intent.md", project_dir)
    _print_artifact_row("output/timeline.json", project_dir)
    _print_artifact_row("output/qa-report.md", project_dir)
    if missing_artifacts:
        print()
        print(f"  {YELLOW('WARNING:')} {len(missing_artifacts)} expected artifact(s) missing despite gate being set:")
        for m in missing_artifacts:
            print(f"    {RED('✗')} {m}")
    print()

    # Parity check (always run in diagnose)
    print(BOLD("Parity:"))
    parity_ok, parity_count, parity_failures = _run_parity()
    if parity_ok:
        print(f"  {GREEN(f'✓  All {parity_count} parity checks passed')}")
    else:
        for f in parity_failures:
            print(f"  {RED(f'✗  {f}')}")
    print()

    # Legal next actions
    actions = compute_next_actions(snap)
    print(BOLD("Next Actions:"))
    if not actions:
        print(f"  {GREEN('No pending actions — project may be complete.')}")
    else:
        for a in actions:
            if a.blocked:
                icon = RED("✗  [BLOCKED]")
            elif a.optional:
                icon = DIM("○  [optional]")
            else:
                icon = GREEN("→")

            cis = YELLOW(" ★ Creative Intent Summary required") if a.creative_intent_required else ""
            par = DIM(f" [{a.parallel_label}]") if a.parallel_label else ""
            print(f"  {icon}  {BOLD(a.name)} ({a.actor}){cis}{par}")
            print(f"         {DIM(a.command_hint)}")
            if a.notes:
                print(f"         {DIM(a.notes)}")
            if a.blocked_reason:
                print(f"         {RED(a.blocked_reason)}")

    print()

    # Feedback / benchmark triggers
    state = snap.orchestration_state
    if state in {"rendered", "qa_passed"}:
        print(BOLD("Recommended:"))
        if state == "rendered":
            print(f"  → {YELLOW('Benchmark')} — training/benchmark-scorecard.md")
        print(f"  → {YELLOW('Feedback capture')} — In conversation: /feedback-capture")
        print()

    # Revision hint
    if snap.status == "failed" or "revision" in snap.status.lower():
        print(f"  {YELLOW('Project is in revision state.')} Creative Intent Summary required before changes.")
        print()

    return 0


def _is_next_gate(gate: str, passed: set, gate_order: list) -> bool:
    """True if this gate is the lowest unpassed gate in the sequence."""
    for g in gate_order:
        if g not in passed:
            return g == gate
    return False


def _print_artifact_row(rel_path: str, project_dir: Path) -> None:
    full = project_dir / rel_path
    if full.exists():
        size = ""
        if full.is_file():
            kb = full.stat().st_size / 1024
            size = DIM(f" ({kb:.1f} KB)")
        print(f"  {GREEN('✓')} {rel_path}{size}")
    else:
        print(f"  {DIM('○')} {rel_path}  {DIM('(not yet produced)')}")


def _run_parity() -> tuple[bool, int, list[str]]:
    """Run parity checks; return (ok, total_count, failure_messages)."""
    try:
        from lib.parity import run_checks
        results = run_checks()
        failures = [f"{r.check.description}: {r.detail}" for r in results if not r.passed]
        return len(failures) == 0, len(results), failures
    except ImportError:
        return True, 0, []


# ── approve ────────────────────────────────────────────────────────────────

def cmd_approve(project_dir: Path, gate_id: str) -> int:
    snap = load_snapshot(project_dir)
    prior_state = snap.orchestration_state
    prior_gates = list(snap.gates_passed)

    from lib.gates import set_gate
    msg = set_gate(project_dir, gate_id)
    print(msg)

    if msg.startswith("ERROR"):
        return 1

    # Reload to get new state
    snap2 = load_snapshot(project_dir)
    new_state = snap2.orchestration_state

    log_event(
        project_dir,
        actor="human",
        action=f"approve {gate_id}",
        phase=gate_id,
        prior_state=prior_state,
        next_state=new_state,
        gates_before=prior_gates,
        gates_after=snap2.gates_passed,
        result="approved",
    )

    if prior_state != new_state:
        print(f"  State: {DIM(state_label(prior_state))} → {CYAN(state_label(new_state))}")

    # Show immediate next action
    actions = compute_next_actions(snap2)
    unblocked = [a for a in actions if not a.blocked]
    if unblocked:
        a = unblocked[0]
        cis = " [Creative Intent Summary required]" if a.creative_intent_required else ""
        print(f"\n  Next: {GREEN(a.name)} ({a.actor}){cis}")
        print(f"        {DIM(a.command_hint)}")

    return 0


# ── reject ─────────────────────────────────────────────────────────────────

def cmd_reject(project_dir: Path, phase_key: str, reason: str = "") -> int:
    snap = load_snapshot(project_dir)
    prior_state = snap.orchestration_state

    log_event(
        project_dir,
        actor="human",
        action=f"reject {phase_key}",
        phase=phase_key,
        prior_state=prior_state,
        next_state="revision_pending",
        gates_before=snap.gates_passed,
        gates_after=snap.gates_passed,
        result="rejected",
        notes=reason,
    )

    print(f"{RED('Rejected:')} {phase_key}")
    if reason:
        print(f"  Reason: {reason}")
    print(f"  {YELLOW('Creative Intent Summary required before any revision.')}")
    print(f"  In conversation: explain what needs to change — Claude will produce the summary first.")
    return 0


# ── resume ─────────────────────────────────────────────────────────────────

def cmd_resume(project_dir: Path) -> int:
    """Show exactly what is needed to resume the workflow."""
    snap = load_snapshot(project_dir)
    actions = compute_next_actions(snap)
    unblocked = [a for a in actions if not a.blocked]

    print(f"{BOLD('Resume:')} {snap.slug}")
    print(f"  Current state: {CYAN(state_label(snap.orchestration_state))}")
    print()

    if not unblocked:
        print(f"  {GREEN('Nothing blocking — project may be complete or waiting for review.')}")
        return 0

    print(f"  {BOLD('To resume, do the following:')}")
    for i, a in enumerate(unblocked, 1):
        cis = " [Creative Intent Summary first]" if a.creative_intent_required else ""
        par = f" [{a.parallel_label}]" if a.parallel_label else ""
        print(f"  {i}. {a.name} ({a.actor}){cis}{par}")
        print(f"     {DIM(a.command_hint)}")
        if a.notes:
            print(f"     {DIM(a.notes)}")
    return 0


# ── invalidate ─────────────────────────────────────────────────────────────

def cmd_invalidate(project_dir: Path, artifact: str) -> int:
    snap = load_snapshot(project_dir)
    prior_gates = list(snap.gates_passed)
    prior_state = snap.orchestration_state

    result = invalidate_from_change(project_dir, artifact)

    if result.reset_from_gate is None:
        print(f"{YELLOW('No invalidation rule for:')} {artifact}")
        print(f"  Known artifacts: {', '.join(sorted(['script.md', 'audio/beat-map.json', 'shot-list.md', 'output/motion-intent.md', 'output/timeline.json']))}")
        return 1

    snap2 = load_snapshot(project_dir)
    new_state = snap2.orchestration_state

    print(f"{YELLOW('Invalidated:')} {artifact}")
    print(f"  {result.description}")
    if result.gates_removed:
        print(f"\n  Gates removed ({len(result.gates_removed)}):")
        for g in result.gates_removed:
            print(f"    {RED('✗')} {g}")
    if result.stale_files_hint:
        print(f"\n  Stale artifacts:")
        for f in result.stale_files_hint:
            print(f"    {YELLOW('⚠')} {f}")

    if prior_state != new_state:
        print(f"\n  State: {DIM(state_label(prior_state))} → {CYAN(state_label(new_state))}")

    log_event(
        project_dir,
        actor="human",
        action=f"invalidate {artifact}",
        phase=result.reset_from_gate,
        prior_state=prior_state,
        next_state=new_state,
        gates_before=prior_gates,
        gates_after=snap2.gates_passed,
        result="invalidated",
        notes=result.description,
    )

    return 0


# ── history ────────────────────────────────────────────────────────────────

def cmd_history(project_dir: Path, tail: int = 10) -> int:
    events = read_events(project_dir)
    if not events:
        print(f"  {DIM('No orchestration events logged yet.')}")
        return 0

    shown = events[-tail:]
    print(f"{BOLD('Orchestration log:')} {project_dir.name} (last {len(shown)} of {len(events)})\n")
    for e in shown:
        ts = e.get("timestamp", "")[:19].replace("T", " ")
        actor = e.get("actor", "?")
        action = e.get("action", "?")
        result = e.get("result", "?")
        result_color = GREEN(result) if result in ("success", "approved") else (
            RED(result) if result in ("failed", "rejected") else YELLOW(result)
        )
        state_change = ""
        if e.get("prior_state") and e.get("next_state") and e["prior_state"] != e["next_state"]:
            state_change = f"  {DIM(e['prior_state'])} → {CYAN(e['next_state'])}"
        notes = f"  {DIM(e['notes'])}" if e.get("notes") else ""
        print(f"  {DIM(ts)}  [{actor}] {action}  {result_color}{state_change}{notes}")
    return 0


# ── run ───────────────────────────────────────────────────────────────────

def cmd_run(project_dir: Path, max_phases: int | None = None) -> int:
    """
    Advance the project from its current state.
    Runs code phases automatically; pauses at Claude or human phases.
    """
    from .runner import Runner

    snap = load_snapshot(project_dir)
    print(f"{BOLD('Run:')} {snap.slug}  [{state_label(snap.orchestration_state)}]")
    print()

    runner = Runner()
    report = runner.run(project_dir, max_phases=max_phases)

    # Print each phase result
    for result in report.results:
        _print_exec_result(result)

    print()
    print(f"  {BOLD('Phases run:')} {report.phases_run}  "
          f"{BOLD('Succeeded:')} {report.phases_succeeded}  "
          f"{BOLD('Status:')} {_status_color(report.final_status)(report.final_status.value)}")

    # Print work order or human action
    if report.terminal_work_order:
        print()
        print(report.terminal_work_order.render())
    elif report.terminal_human_action:
        print()
        print(report.terminal_human_action.render())

    if report.error_message:
        print(f"\n  {RED('Error:')} {report.error_message}")

    return 0 if report.final_status in (
        ExecStatus.SUCCESS,
        ExecStatus.PAUSED_FOR_CLAUDE,
        ExecStatus.PAUSED_FOR_HUMAN,
        ExecStatus.SKIPPED,
    ) else 1


# ── run-phase ──────────────────────────────────────────────────────────────

def cmd_run_phase(project_dir: Path, phase_key: str) -> int:
    """Run one specific phase. Validates preconditions first."""
    from .runner import Runner
    from .results import ExecStatus

    snap = load_snapshot(project_dir)
    spec = PHASES.get(phase_key)
    phase_name = spec.name if spec else phase_key

    print(f"{BOLD('Run phase:')} {phase_name} ({phase_key})")
    print(f"  Project: {snap.slug}  [{state_label(snap.orchestration_state)}]")
    print()

    runner = Runner()
    result = runner.run_phase(project_dir, phase_key)

    _print_exec_result(result)

    if result.work_order:
        print()
        print(result.work_order.render())
    elif result.human_action:
        print()
        print(result.human_action.render())

    if result.error:
        print(f"\n  {RED('Error:')} {result.error}")

    return 0 if result.status in (
        ExecStatus.SUCCESS,
        ExecStatus.PAUSED_FOR_CLAUDE,
        ExecStatus.PAUSED_FOR_HUMAN,
        ExecStatus.SKIPPED,
    ) else 1


# ── shared result printer ──────────────────────────────────────────────────

def _print_exec_result(result: "ExecResult") -> None:  # type: ignore[name-defined]
    from .results import ExecStatus
    icon_map = {
        ExecStatus.SUCCESS:           GREEN("✓"),
        ExecStatus.PAUSED_FOR_CLAUDE: YELLOW("⏸"),
        ExecStatus.PAUSED_FOR_HUMAN:  YELLOW("⏸"),
        ExecStatus.FAILED:            RED("✗"),
        ExecStatus.BLOCKED:           RED("◻"),
        ExecStatus.SKIPPED:           DIM("–"),
    }
    icon = icon_map.get(result.status, "?")
    dur = DIM(f" ({result.duration_s:.1f}s)") if result.duration_s >= 0.1 else ""
    print(f"  {icon}  {result.phase_name}  [{result.status.value}]{dur}")

    if result.gate_set:
        print(f"     {GREEN(f'Gate set: {result.gate_set}')}")

    if result.status == ExecStatus.PAUSED_FOR_CLAUDE:
        print(f"     {YELLOW('Paused for Claude — work order below.')}")
    elif result.status == ExecStatus.PAUSED_FOR_HUMAN:
        print(f"     {YELLOW('Paused for human — action checklist below.')}")
    elif result.status == ExecStatus.FAILED and result.error:
        print(f"     {RED(result.error[:120])}")
    elif result.status == ExecStatus.BLOCKED and result.error:
        first_line = result.error.split("\n")[0]
        print(f"     {RED(first_line)}")


def _status_color(status: "ExecStatus"):  # type: ignore[name-defined]
    from .results import ExecStatus
    if status == ExecStatus.SUCCESS:
        return GREEN
    if status in (ExecStatus.PAUSED_FOR_CLAUDE, ExecStatus.PAUSED_FOR_HUMAN):
        return YELLOW
    if status in (ExecStatus.FAILED, ExecStatus.BLOCKED):
        return RED
    return DIM


# ── main entrypoint ────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lib.orchestrator",
        description="Workflow orchestration for AI Reels Studio.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    def _add_project(p: argparse.ArgumentParser) -> None:
        p.add_argument("project_dir", type=Path, help="Path to project directory")

    # status
    p = sub.add_parser("status", help="Quick state summary")
    _add_project(p)

    # next
    p = sub.add_parser("next", help="Legal next actions (detailed)")
    _add_project(p)

    # diagnose
    p = sub.add_parser("diagnose", help="Full diagnostic: gates, artifacts, parity, next actions")
    _add_project(p)

    # approve
    p = sub.add_parser("approve", help="Record human approval and set gate")
    _add_project(p)
    p.add_argument("gate_id", help="Gate to approve (e.g. visual_assignment_approved)")

    # reject
    p = sub.add_parser("reject", help="Record rejection; flag for revision")
    _add_project(p)
    p.add_argument("phase_key", help="Phase that was rejected (e.g. assemble-reel)")
    p.add_argument("--reason", default="", help="Rejection reason")

    # resume
    p = sub.add_parser("resume", help="Show what is needed to resume the workflow")
    _add_project(p)

    # invalidate
    p = sub.add_parser("invalidate", help="Cascade-invalidate from a changed artifact")
    _add_project(p)
    p.add_argument("artifact", help="Changed artifact path (e.g. script.md, output/timeline.json)")

    # history
    p = sub.add_parser("history", help="Show orchestration event log")
    _add_project(p)
    p.add_argument("--tail", type=int, default=10, help="Number of events to show")

    # run
    p = sub.add_parser("run", help="Advance through legal phases; pause at Claude/human")
    _add_project(p)
    p.add_argument("--max-phases", type=int, default=None,
                   help="Max phases to advance in one call")

    # run-phase
    p = sub.add_parser("run-phase", help="Run one specific phase by key")
    _add_project(p)
    p.add_argument("phase_key", help="Phase key (e.g. qa-reel, render, assemble-reel)")

    args = parser.parse_args(argv)

    project_dir = args.project_dir
    if not project_dir.exists():
        print(f"ERROR: project_dir not found: {project_dir}")
        return 1

    try:
        if args.cmd == "status":
            return cmd_status(project_dir)
        elif args.cmd == "next":
            return cmd_next(project_dir)
        elif args.cmd == "diagnose":
            return cmd_diagnose(project_dir)
        elif args.cmd == "approve":
            return cmd_approve(project_dir, args.gate_id)
        elif args.cmd == "reject":
            return cmd_reject(project_dir, args.phase_key, getattr(args, "reason", ""))
        elif args.cmd == "resume":
            return cmd_resume(project_dir)
        elif args.cmd == "invalidate":
            return cmd_invalidate(project_dir, args.artifact)
        elif args.cmd == "history":
            return cmd_history(project_dir, tail=args.tail)
        elif args.cmd == "run":
            return cmd_run(project_dir, max_phases=getattr(args, "max_phases", None))
        elif args.cmd == "run-phase":
            return cmd_run_phase(project_dir, args.phase_key)
        else:
            parser.print_help()
            return 1
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
