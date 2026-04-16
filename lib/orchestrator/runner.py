"""
lib/orchestrator/runner.py — Execution engine for the orchestration layer.

Runner advances a project through legal pipeline phases:
  - Code phases run automatically (render, QA, parity)
  - Claude phases pause and emit a WorkOrder
  - Human phases pause and emit a HumanAction checklist

Usage (via CLI):
  python -m lib.orchestrator run        projects/<slug>
  python -m lib.orchestrator run-phase  projects/<slug> <phase-key>
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .executors import route_executor
from .events import log_event
from .results import ExecResult, ExecStatus, RunReport
from .state import load_snapshot, ProjectSnapshot
from .transitions import compute_next_actions
from .validators import validate_phase_preconditions
from .spec import PHASES


# ── Runner ─────────────────────────────────────────────────────────────────

class Runner:
    """
    Execution engine that advances a project through legal pipeline phases.

    run()        — advance from current state; stop at Claude/human pause
    run_phase()  — execute one specific phase by key if preconditions pass
    """

    def run(
        self,
        project_dir: Path,
        max_phases: int | None = None,
    ) -> RunReport:
        """
        Advance the project from its current state.

        Runs consecutive code-only phases automatically. Stops at the first
        Claude or human phase, emitting a WorkOrder or HumanAction.

        Stops early on:
          - Any phase failure
          - Any paused phase (claude / human)
          - max_phases limit reached
        """
        results: list[ExecResult] = []
        phases_run = 0
        phases_succeeded = 0
        snap = load_snapshot(project_dir)

        while True:
            if max_phases is not None and phases_run >= max_phases:
                break

            actions = compute_next_actions(snap)
            runnable = [a for a in actions if not a.blocked and not a.optional]

            if not runnable:
                break

            # Take the highest-priority unblocked action
            action = runnable[0]
            phase_key = action.phase_key

            if phase_key is None:
                # Action has no executable phase key (informational action)
                break

            # Validate preconditions
            failures = validate_phase_preconditions(phase_key, snap)
            if failures:
                error_msg = "; ".join(f.message for f in failures)
                result = ExecResult(
                    phase_key=phase_key,
                    phase_name=action.name,
                    actor=action.actor,
                    status=ExecStatus.BLOCKED,
                    error=error_msg,
                )
                results.append(result)
                break

            # Execute the phase
            result = route_executor(phase_key, snap)
            results.append(result)
            phases_run += 1

            if result.succeeded:
                phases_succeeded += 1
                snap = load_snapshot(project_dir)  # reload to pick up gate changes
                continue

            if result.paused:
                # Save pause state so resume/status can show where we stopped
                _save_pause_state(project_dir, phase_key, result.status.value)
                break

            if result.status == ExecStatus.FAILED:
                break

            # Skipped phases: continue
            snap = load_snapshot(project_dir)

        # Determine final status
        final_status = _aggregate_status(results)

        # Extract terminal work order / human action
        terminal_work_order = None
        terminal_human_action = None
        for r in reversed(results):
            if r.work_order and terminal_work_order is None:
                terminal_work_order = r.work_order
            if r.human_action and terminal_human_action is None:
                terminal_human_action = r.human_action

        return RunReport(
            project_slug=snap.slug,
            results=results,
            final_status=final_status,
            phases_run=phases_run,
            phases_succeeded=phases_succeeded,
            terminal_work_order=terminal_work_order,
            terminal_human_action=terminal_human_action,
        )

    def run_phase(
        self,
        project_dir: Path,
        phase_key: str,
    ) -> ExecResult:
        """
        Run a single named phase. Validates preconditions before executing.

        Returns an ExecResult. Does NOT advance to subsequent phases.
        """
        snap = load_snapshot(project_dir)
        spec = PHASES.get(phase_key)

        if spec is None:
            return ExecResult(
                phase_key=phase_key,
                phase_name=phase_key,
                actor="unknown",
                status=ExecStatus.FAILED,
                error=f"Unknown phase key: '{phase_key}'. Check lib/orchestrator/spec.py.",
            )

        # Validate preconditions
        failures = validate_phase_preconditions(phase_key, snap)
        if failures:
            error_lines = [f"  - {f.message}" for f in failures]
            hint_lines = [f"    Fix: {f.fix_hint}" for f in failures if f.fix_hint]
            error_msg = "Precondition failures:\n" + "\n".join(error_lines + hint_lines)
            log_event(
                project_dir,
                actor="code",
                action=f"run-phase {phase_key}",
                phase=phase_key,
                result="blocked",
                notes=error_msg,
            )
            return ExecResult(
                phase_key=phase_key,
                phase_name=spec.name,
                actor=spec.actor,
                status=ExecStatus.BLOCKED,
                error=error_msg,
            )

        result = route_executor(phase_key, snap)

        if result.paused:
            _save_pause_state(project_dir, phase_key, result.status.value)
        elif result.succeeded:
            _clear_pause_state(project_dir)

        return result


# ── Pause state persistence ────────────────────────────────────────────────

def _save_pause_state(
    project_dir: Path,
    phase_key: str,
    paused_for: str,
) -> None:
    """Write pause metadata to project.json so CLI commands can show it."""
    pf = project_dir / "project.json"
    try:
        data: dict[str, Any] = json.loads(pf.read_text(encoding="utf-8"))
        data["_paused_at"] = phase_key
        data["_paused_for"] = paused_for
        pf.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _clear_pause_state(project_dir: Path) -> None:
    """Remove pause metadata from project.json after successful completion."""
    pf = project_dir / "project.json"
    try:
        data: dict[str, Any] = json.loads(pf.read_text(encoding="utf-8"))
        data.pop("_paused_at", None)
        data.pop("_paused_for", None)
        pf.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


# ── Helpers ────────────────────────────────────────────────────────────────

def _aggregate_status(results: list[ExecResult]) -> ExecStatus:
    """Determine overall run status from individual phase results."""
    if not results:
        return ExecStatus.SKIPPED

    for r in reversed(results):
        if r.status == ExecStatus.FAILED:
            return ExecStatus.FAILED
        if r.status == ExecStatus.BLOCKED:
            return ExecStatus.BLOCKED
        if r.status == ExecStatus.PAUSED_FOR_CLAUDE:
            return ExecStatus.PAUSED_FOR_CLAUDE
        if r.status == ExecStatus.PAUSED_FOR_HUMAN:
            return ExecStatus.PAUSED_FOR_HUMAN

    if all(r.status == ExecStatus.SKIPPED for r in results):
        return ExecStatus.SKIPPED

    return ExecStatus.SUCCESS
