"""
lib/orchestrator/results.py — Structured execution result types.

Every phase execution produces an ExecResult. For code phases this contains
output/error/duration. For Claude phases it contains a WorkOrder that Claude
reads in conversation. For human phases it contains a HumanAction checklist.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


# ── Execution status ───────────────────────────────────────────────────────

class ExecStatus(str, Enum):
    SUCCESS            = "success"
    PAUSED_FOR_CLAUDE  = "paused_for_claude"
    PAUSED_FOR_HUMAN   = "paused_for_human"
    FAILED             = "failed"
    BLOCKED            = "blocked"
    SKIPPED            = "skipped"


# ── Work order (emitted for Claude phases) ─────────────────────────────────

@dataclass
class WorkOrder:
    """
    Structured brief emitted when the orchestrator pauses for a Claude phase.
    Claude reads this at the start of the conversation turn.
    """
    phase_key: str
    phase_name: str
    purpose: str
    project_slug: str

    # Pre-work requirements
    creative_intent_required: bool
    memory_to_read: list[str]      # file paths to read before starting
    rules_to_apply: list[str]      # rule/skill files to load

    # Project context
    context: dict[str, Any]        # style, theme, beat_count, duration, etc.

    # Inputs and expected output
    input_files: list[str]
    output_files: list[str]

    # What to do after
    approval_command: str          # command to run after human reviews output
    sets_gate: str | None          # gate that gets set on approval

    def render(self) -> str:
        """Format the work order as a human-readable block."""
        lines: list[str] = []
        w = 56
        lines.append("═" * w)
        lines.append(f" WORK ORDER — {self.phase_name}")
        lines.append("═" * w)
        lines.append(f" Project  : {self.project_slug}")
        lines.append(f" Purpose  : {self.purpose}")
        lines.append("")

        if self.creative_intent_required:
            lines.append(" ★ Creative Intent Summary REQUIRED before beginning.")
            lines.append("   Produce the 6-field summary and wait for confirmation.")
            lines.append("")

        if self.context:
            lines.append(" Context:")
            for k, v in self.context.items():
                lines.append(f"   {k:<22}: {v}")
            lines.append("")

        if self.memory_to_read:
            lines.append(" Read before starting:")
            for f in self.memory_to_read:
                lines.append(f"   - {f}")
            lines.append("")

        if self.rules_to_apply:
            lines.append(" Apply rules / skills:")
            for r in self.rules_to_apply:
                lines.append(f"   - {r}")
            lines.append("")

        if self.input_files:
            lines.append(" Input files:")
            for f in self.input_files:
                lines.append(f"   - {f}")
            lines.append("")

        lines.append(" Output to produce:")
        for f in self.output_files:
            lines.append(f"   - {f}")
        lines.append("")

        if self.sets_gate:
            lines.append(f" After output is reviewed and approved:")
            lines.append(f"   {self.approval_command}")
        lines.append("═" * w)
        return "\n".join(lines)


# ── Human action (emitted for human phases) ────────────────────────────────

@dataclass
class HumanAction:
    """
    Structured checklist emitted when the orchestrator pauses for a human phase.
    """
    phase_key: str
    phase_name: str
    project_slug: str
    description: str
    steps: list[str]               # numbered action steps
    approval_command: str          # command to run when done
    rejection_command: str         # command to run if rejected

    def render(self) -> str:
        lines: list[str] = []
        w = 56
        lines.append("═" * w)
        lines.append(f" ACTION REQUIRED — {self.phase_name}")
        lines.append("═" * w)
        lines.append(f" Project : {self.project_slug}")
        lines.append(f" {self.description}")
        lines.append("")
        for i, step in enumerate(self.steps, 1):
            lines.append(f" {i}. {step}")
        lines.append("")
        lines.append(f" When approved:")
        lines.append(f"   {self.approval_command}")
        lines.append(f" When rejected:")
        lines.append(f"   {self.rejection_command}")
        lines.append("═" * w)
        return "\n".join(lines)


# ── Execution result ───────────────────────────────────────────────────────

@dataclass
class ExecResult:
    """Result of executing one pipeline phase."""
    phase_key: str
    phase_name: str
    actor: str
    status: ExecStatus
    duration_s: float = 0.0
    exit_code: int = 0
    output: str = ""
    error: str | None = None
    gate_set: str | None = None      # gate that was set (code phases)
    work_order: WorkOrder | None = None
    human_action: HumanAction | None = None
    qa_passed: bool | None = None    # for qa-reel phase
    qa_blockers: list[str] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return self.status == ExecStatus.SUCCESS

    @property
    def paused(self) -> bool:
        return self.status in (
            ExecStatus.PAUSED_FOR_CLAUDE,
            ExecStatus.PAUSED_FOR_HUMAN,
        )

    def summary_line(self) -> str:
        icon = {
            ExecStatus.SUCCESS:           "✓",
            ExecStatus.PAUSED_FOR_CLAUDE: "⏸",
            ExecStatus.PAUSED_FOR_HUMAN:  "⏸",
            ExecStatus.FAILED:            "✗",
            ExecStatus.BLOCKED:           "◻",
            ExecStatus.SKIPPED:           "–",
        }.get(self.status, "?")
        dur = f" ({self.duration_s:.1f}s)" if self.duration_s >= 0.1 else ""
        return f"{icon}  {self.phase_name} [{self.status.value}]{dur}"


# ── Run report (returned by runner.run) ────────────────────────────────────

@dataclass
class RunReport:
    """
    Aggregate result of a runner.run() call — may span multiple phases.
    """
    project_slug: str
    results: list[ExecResult]
    final_status: ExecStatus
    phases_run: int
    phases_succeeded: int
    terminal_work_order: WorkOrder | None = None
    terminal_human_action: HumanAction | None = None
    error_message: str | None = None

    def summary(self) -> str:
        lines = [f"Run report: {self.project_slug}  [{self.final_status.value}]"]
        for r in self.results:
            lines.append(f"  {r.summary_line()}")
        if self.error_message:
            lines.append(f"  Error: {self.error_message}")
        return "\n".join(lines)
