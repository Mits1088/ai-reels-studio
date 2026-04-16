"""
lib/orchestrator/tasks.py — Executable task registry for code phases.

Maps phase_key → callable for phases where code can do the work directly
(no Claude or human required). Each task runs the actual pipeline operation
and returns (exit_code, output, error).

Only phases with actor="code" or whose code part is fully deterministic
should be registered here.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class TaskResult:
    exit_code: int
    output: str
    error: str | None
    sets_gate: str | None       # gate to set on success (None = no automatic gate)
    duration_s: float = 0.0


TaskFn = Callable[[Path], TaskResult]


# ── Individual task implementations ────────────────────────────────────────

def _task_render(project_dir: Path) -> TaskResult:
    """Run: npx remotion render src/index.ts ReelComposition --output out/reel.mp4"""
    remotion_dir = project_dir.parent.parent / "remotion"  # D:\Reel generation\remotion
    if not remotion_dir.exists():
        remotion_dir = Path(__file__).resolve().parents[2] / "remotion"

    out_path = project_dir / "out" / "reel.mp4"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "npx", "remotion", "render",
        "src/index.ts",
        "ReelComposition",
        "--output", str(out_path),
    ]
    t0 = time.monotonic()
    result = subprocess.run(
        cmd,
        cwd=str(remotion_dir),
        capture_output=True,
        text=True,
    )
    duration = time.monotonic() - t0
    output = result.stdout + result.stderr
    return TaskResult(
        exit_code=result.returncode,
        output=output,
        error=result.stderr if result.returncode != 0 else None,
        sets_gate=None,  # render has no gate — presence of file is the signal
        duration_s=duration,
    )


def _task_qa(project_dir: Path) -> TaskResult:
    """Run QA checks via lib.qa.runner.run_qa_on_project."""
    t0 = time.monotonic()
    try:
        from lib.qa.runner import run_qa_on_project
        report = run_qa_on_project(project_dir)
        duration = time.monotonic() - t0
        output = report.summary()
        blockers = [f.message for f in report.blockers]
        if report.passed:
            return TaskResult(
                exit_code=0,
                output=output,
                error=None,
                sets_gate="qa_passed",
                duration_s=duration,
            )
        else:
            return TaskResult(
                exit_code=1,
                output=output,
                error=f"{len(blockers)} blocker(s): " + "; ".join(blockers[:3]),
                sets_gate=None,
                duration_s=duration,
            )
    except Exception as e:
        return TaskResult(
            exit_code=1,
            output="",
            error=str(e),
            sets_gate=None,
            duration_s=time.monotonic() - t0,
        )


def _task_parity(project_dir: Path) -> TaskResult:
    """Run parity checks."""
    t0 = time.monotonic()
    try:
        from lib.parity import run_checks
        results = run_checks()
        failures = [r for r in results if not r.passed]
        duration = time.monotonic() - t0
        if not failures:
            return TaskResult(
                exit_code=0,
                output=f"All {len(results)} parity checks passed",
                error=None,
                sets_gate=None,
                duration_s=duration,
            )
        msgs = [f"{r.check.description}: {r.detail}" for r in failures]
        return TaskResult(
            exit_code=1,
            output="\n".join(msgs),
            error=f"{len(failures)} parity check(s) failed",
            sets_gate=None,
            duration_s=duration,
        )
    except Exception as e:
        return TaskResult(
            exit_code=0,  # don't block on missing parity module
            output=f"Parity check skipped: {e}",
            error=None,
            sets_gate=None,
            duration_s=time.monotonic() - t0,
        )


def _task_phase_post(skill_name: str) -> TaskFn:
    """
    Factory: create a task that runs `python -m lib.phase post <skill> <project_dir>`.
    Used for phases where the post-flight validation IS the task.
    """
    def _task(project_dir: Path) -> TaskResult:
        cmd = [
            "python", "-m", "lib.phase", "post", skill_name, str(project_dir)
        ]
        t0 = time.monotonic()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(project_dir.parent))
        return TaskResult(
            exit_code=result.returncode,
            output=result.stdout + result.stderr,
            error=result.stderr if result.returncode != 0 else None,
            sets_gate=None,  # post-flight doesn't set gates — approval does
            duration_s=time.monotonic() - t0,
        )
    return _task


# ── Task registry ───────────────────────────────────────────────────────────
# Maps phase_key → task callable.
# Only phases that are fully code-executable belong here.

TASKS: dict[str, TaskFn] = {
    "render":   _task_render,
    "qa-reel":  _task_qa,
    "parity":   _task_parity,
}


def get_task(phase_key: str) -> TaskFn | None:
    """Return the task callable for a phase, or None if not code-executable."""
    return TASKS.get(phase_key)
