"""
lib.brain.advance — Safe, dry-run-by-default project advancement.

Determines the next code-safe pipeline step and optionally executes it via
lib.orchestrator.Runner.  Dry-run is the default; pass execute=True to act.

Safe actors (execute): "code"
Skipped actors:        "claude", "human", "code+claude", "human+claude"
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .diagnose import diagnose_project
from .models import Diagnosis
from ..orchestrator.state import load_snapshot
from ..orchestrator.transitions import compute_next_actions
from ..orchestrator.spec import PHASES
from ..orchestrator.runner import Runner
from ..orchestrator.results import ExecStatus


# ── Result type ────────────────────────────────────────────────────────────

@dataclass
class AdvanceResult:
    """Outcome of one advance_project() call."""
    project_slug: str
    phase_key: str | None
    status: Literal["dry_run", "succeeded", "skipped", "failed"]
    actor: str
    gate_target: str | None       # gate that would/did get set
    would_execute: str            # command description — always populated
    executed: bool                # True only when execution actually happened
    reason: str                   # plain-English explanation for all outcomes
    output: str
    error: str | None
    re_diagnosis_summary: dict | None  # compact snapshot after execution

    def to_dict(self) -> dict:
        return {
            "project_slug": self.project_slug,
            "phase_key": self.phase_key,
            "status": self.status,
            "actor": self.actor,
            "gate_target": self.gate_target,
            "would_execute": self.would_execute,
            "executed": self.executed,
            "reason": self.reason,
            "output": self.output,
            "error": self.error,
            "re_diagnosis_summary": self.re_diagnosis_summary,
        }


# ── Code-safe check ────────────────────────────────────────────────────────

def _is_code_safe(actor: str) -> bool:
    """Only pure code-actor phases are safe to execute autonomously."""
    return actor == "code"


# ── Compact diagnosis summary ──────────────────────────────────────────────

def _compact_summary(d: Diagnosis) -> dict:
    """Subset of Diagnosis fields — JSON-safe, no circular refs."""
    return {
        "slug": d.slug,
        "phase": d.phase,
        "healthy": d.healthy,
        "gates_passed": len(d.gates.passed),
        "gates_total": d.gates.total,
        "next_required": d.gates.next_required,
        "can_continue": d.autonomy.can_continue_autonomously,
        "human_required": d.autonomy.human_required,
        "next_action": d.autonomy.next_action,
        "qa_verdict": d.qa.verdict if d.qa.available else "not_run",
    }


# ── Main entry point ───────────────────────────────────────────────────────

def advance_project(
    project_dir: Path,
    execute: bool = False,
    critic_hard_mode: bool = False,
) -> AdvanceResult:
    """
    Determine (and optionally execute) the next code-safe pipeline step.

    Parameters
    ----------
    project_dir:
        Path to the project directory.
    execute:
        If False (default), returns a dry_run result describing what would
        happen without touching any files.  If True, calls Runner.run_phase()
        and returns the real result with re_diagnosis_summary populated.

    Returns
    -------
    AdvanceResult.status is one of:
        "dry_run"   — execute=False; describes what would run
        "succeeded" — phase executed and completed
        "skipped"   — nothing to run (human gate, non-code actor, or blocked)
        "failed"    — execution attempted but phase errored
    """
    project_dir = Path(project_dir).resolve()

    # ── Step 1: Diagnose current state ────────────────────────────────────
    diag = diagnose_project(project_dir, critic_hard_mode=critic_hard_mode)
    slug = diag.slug

    # ── Step 2: Validation errors block everything ────────────────────────
    if diag.validation_errors:
        return AdvanceResult(
            project_slug=slug,
            phase_key=None,
            status="skipped",
            actor="none",
            gate_target=None,
            would_execute="(none — fix validation errors first)",
            executed=False,
            reason=(
                f"Project has {len(diag.validation_errors)} validation error(s). "
                "Resolve project.json errors before advancing."
            ),
            output="",
            error=None,
            re_diagnosis_summary=None,
        )

    av = diag.autonomy

    # ── Step 3: Human approval gate ───────────────────────────────────────
    if av.human_required:
        return AdvanceResult(
            project_slug=slug,
            phase_key=None,
            status="skipped",
            actor="human",
            gate_target=diag.gates.next_required,
            would_execute=av.next_action_command or "(human action required)",
            executed=False,
            reason=(
                f"Human approval required: "
                f"{av.human_required_reason or av.next_action}"
            ),
            output="",
            error=None,
            re_diagnosis_summary=None,
        )

    # ── Step 4: General blocked / unknown state ───────────────────────────
    if not av.can_continue_autonomously:
        return AdvanceResult(
            project_slug=slug,
            phase_key=None,
            status="skipped",
            actor=av.next_action_actor or "unknown",
            gate_target=diag.gates.next_required,
            would_execute=av.next_action_command or "(no executable action)",
            executed=False,
            reason=(
                f"Cannot continue autonomously: "
                f"{av.next_action or 'no next action identified'}"
            ),
            output="",
            error=None,
            re_diagnosis_summary=None,
        )

    # ── Step 5: Resolve next action via orchestrator transitions ─────────
    snap = load_snapshot(project_dir)
    actions = compute_next_actions(snap)
    runnable = [a for a in actions if not a.blocked and not a.optional]

    if not runnable:
        return AdvanceResult(
            project_slug=slug,
            phase_key=None,
            status="skipped",
            actor="none",
            gate_target=None,
            would_execute="(no runnable action)",
            executed=False,
            reason=(
                "No unblocked, non-optional action found in current pipeline state. "
                "Pipeline may be complete or fully blocked."
            ),
            output="",
            error=None,
            re_diagnosis_summary=None,
        )

    action = runnable[0]
    phase_key = action.phase_key
    spec = PHASES.get(phase_key)
    actor = spec.actor if spec else action.actor
    gate_target = spec.sets_gate if spec else None
    command_hint = action.command_hint or f"Run phase: {phase_key}"

    # ── Step 6: Actor gate — only "code" is safe ──────────────────────────
    if not _is_code_safe(actor):
        return AdvanceResult(
            project_slug=slug,
            phase_key=phase_key,
            status="skipped",
            actor=actor,
            gate_target=gate_target,
            would_execute=command_hint,
            executed=False,
            reason=(
                f"Phase '{phase_key}' requires actor '{actor}'. "
                "advance only executes 'code' actor phases. "
                f"Invoke this phase via: {command_hint}"
            ),
            output="",
            error=None,
            re_diagnosis_summary=None,
        )

    # ── Step 7: Dry-run (default) ─────────────────────────────────────────
    if not execute:
        return AdvanceResult(
            project_slug=slug,
            phase_key=phase_key,
            status="dry_run",
            actor=actor,
            gate_target=gate_target,
            would_execute=command_hint,
            executed=False,
            reason=(
                f"Dry-run: would execute '{phase_key}' (actor: {actor}). "
                "Pass --execute to run for real."
            ),
            output="",
            error=None,
            re_diagnosis_summary=None,
        )

    # ── Step 8: Execute via Runner ─────────────────────────────────────────
    exec_result = Runner().run_phase(project_dir, phase_key)

    # Always re-diagnose after execution — captures gate changes
    post_diag = diagnose_project(project_dir, critic_hard_mode=critic_hard_mode)
    summary = _compact_summary(post_diag)

    if exec_result.status == ExecStatus.SUCCESS:
        return AdvanceResult(
            project_slug=slug,
            phase_key=phase_key,
            status="succeeded",
            actor=actor,
            gate_target=exec_result.gate_set or gate_target,
            would_execute=command_hint,
            executed=True,
            reason=f"Phase '{phase_key}' completed successfully.",
            output=exec_result.output or "",
            error=None,
            re_diagnosis_summary=summary,
        )

    # Failure / paused — both map to "failed" from advance's perspective
    return AdvanceResult(
        project_slug=slug,
        phase_key=phase_key,
        status="failed",
        actor=actor,
        gate_target=gate_target,
        would_execute=command_hint,
        executed=True,
        reason=(
            f"Phase '{phase_key}' ended with status "
            f"'{exec_result.status.value}': "
            f"{exec_result.error or 'no error detail'}"
        ),
        output=exec_result.output or "",
        error=exec_result.error,
        re_diagnosis_summary=summary,
    )
