"""
tests/orchestrator/test_cli.py — CLI surface behavior tests.

Tests the orchestrator CLI commands by calling main() directly and
capturing stdout via capsys. Validates exit codes, key output signals,
and side effects on project state.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lib.orchestrator.cli import main
from lib.orchestrator.tasks import TaskResult


# ── Helpers ────────────────────────────────────────────────────────────────

def _run(args: list[str], capsys) -> tuple[int, str, str]:
    """Call main() with args, return (exit_code, stdout, stderr)."""
    exit_code = main(args)
    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err


def _project_json(project_dir: Path) -> dict:
    return json.loads((project_dir / "project.json").read_text(encoding="utf-8"))


def _read_events(project_dir: Path) -> list[dict]:
    log = project_dir / "output" / "orchestration-log.jsonl"
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


# ── status command ─────────────────────────────────────────────────────────

class TestStatusCommand:

    def test_status_exits_zero(self, fresh_project, capsys):
        code, _, _ = _run(["status", str(fresh_project)], capsys)
        assert code == 0

    def test_status_shows_project_slug(self, fresh_project, capsys):
        _, out, _ = _run(["status", str(fresh_project)], capsys)
        assert "test-fresh" in out

    def test_status_shows_state(self, theme_ready_project, capsys):
        _, out, _ = _run(["status", str(theme_ready_project)], capsys)
        # State is displayed as human label ("Theme set — ready for scripting")
        assert "theme" in out.lower()

    def test_status_nonexistent_dir_exits_nonzero(self, tmp_path, capsys):
        fake = tmp_path / "does-not-exist"
        code, _, _ = _run(["status", str(fake)], capsys)
        assert code != 0


# ── next command ───────────────────────────────────────────────────────────

class TestNextCommand:

    def test_next_exits_zero(self, theme_ready_project, capsys):
        code, _, _ = _run(["next", str(theme_ready_project)], capsys)
        assert code == 0

    def test_next_shows_reel_script_for_theme_ready(self, theme_ready_project, capsys):
        _, out, _ = _run(["next", str(theme_ready_project)], capsys)
        assert "reel-script" in out.lower() or "Reel Script" in out


# ── run command ────────────────────────────────────────────────────────────

class TestRunCommand:

    def test_run_exits_zero_on_claude_pause(self, theme_ready_project, capsys):
        """run pausing at a Claude phase is expected — exit 0, not error."""
        code, _, _ = _run(["run", str(theme_ready_project)], capsys)
        assert code == 0

    def test_run_emits_work_order_in_output(self, theme_ready_project, capsys):
        """run() output must include the WORK ORDER block when Claude pauses."""
        _, out, _ = _run(["run", str(theme_ready_project)], capsys)
        assert "WORK ORDER" in out

    def test_run_shows_paused_status(self, theme_ready_project, capsys):
        _, out, _ = _run(["run", str(theme_ready_project)], capsys)
        assert "paused_for_claude" in out

    def test_run_exits_zero_on_human_pause(self, script_ready_project, capsys):
        """run pausing for a human is expected — exit 0, not error."""
        code, _, _ = _run(["run", str(script_ready_project)], capsys)
        assert code == 0

    def test_run_human_pause_emits_action_checklist(self, script_ready_project, capsys):
        _, out, _ = _run(["run", str(script_ready_project)], capsys)
        assert "ACTION REQUIRED" in out

    def test_run_succeeds_with_mocked_code_task(self, qa_passed_project, capsys):
        """run() with mocked render task exits 0 and shows success."""
        mock_task = MagicMock(return_value=TaskResult(
            exit_code=0, output="Render complete", error=None,
            sets_gate=None, duration_s=8.0,
        ))
        with patch("lib.orchestrator.executors.get_task", return_value=mock_task), \
             patch("lib.orchestrator.validators._run_parity_checks", return_value=[]):
            code, out, _ = _run(["run", str(qa_passed_project)], capsys)
        assert code == 0
        assert "success" in out.lower()

    def test_run_max_phases_limits_execution(self, theme_ready_project, capsys):
        code, _, _ = _run(["run", str(theme_ready_project), "--max-phases", "0"], capsys)
        assert code == 0  # No phases run is not an error


# ── run-phase command ──────────────────────────────────────────────────────

class TestRunPhaseCommand:

    def test_run_phase_claude_exits_zero(self, theme_ready_project, capsys):
        """Pausing for Claude is not an error — exit 0."""
        code, _, _ = _run(["run-phase", str(theme_ready_project), "reel-script"], capsys)
        assert code == 0

    def test_run_phase_claude_shows_work_order(self, theme_ready_project, capsys):
        _, out, _ = _run(["run-phase", str(theme_ready_project), "reel-script"], capsys)
        assert "WORK ORDER" in out

    def test_run_phase_illegal_exits_nonzero(self, fresh_project, capsys):
        """Missing gates → blocked → exit nonzero."""
        code, _, _ = _run(["run-phase", str(fresh_project), "reel-script"], capsys)
        assert code != 0

    def test_run_phase_unknown_key_exits_nonzero(self, fresh_project, capsys):
        """Unknown phase key → FAILED → exit nonzero."""
        code, _, _ = _run(["run-phase", str(fresh_project), "nonexistent-xyz"], capsys)
        assert code != 0

    def test_run_phase_mocked_success_exits_zero(self, qa_passed_project, capsys):
        mock_task = MagicMock(return_value=TaskResult(
            exit_code=0, output="done", error=None, sets_gate=None, duration_s=1.0
        ))
        with patch("lib.orchestrator.executors.get_task", return_value=mock_task):
            code, _, _ = _run(["run-phase", str(qa_passed_project), "render"], capsys)
        assert code == 0

    def test_run_phase_mocked_failure_exits_nonzero(self, qa_passed_project, capsys):
        mock_task = MagicMock(return_value=TaskResult(
            exit_code=1, output="", error="render failed", sets_gate=None, duration_s=0.1
        ))
        with patch("lib.orchestrator.executors.get_task", return_value=mock_task):
            code, _, _ = _run(["run-phase", str(qa_passed_project), "render"], capsys)
        assert code != 0


# ── approve command ────────────────────────────────────────────────────────

class TestApproveCommand:

    def test_approve_sets_gate_in_project_json(self, fresh_project, capsys):
        code, _, _ = _run(["approve", str(fresh_project), "brief_approved"], capsys)
        assert code == 0
        proj = _project_json(fresh_project)
        assert "brief_approved" in proj["gates_passed"]

    def test_approve_logs_event(self, fresh_project, capsys):
        _run(["approve", str(fresh_project), "brief_approved"], capsys)
        events = _read_events(fresh_project)
        assert any(e.get("action", "").startswith("approve") for e in events), \
            "approve command must write an event to orchestration-log.jsonl"

    def test_approve_shows_state_transition(self, fresh_project, capsys):
        _, out, _ = _run(["approve", str(fresh_project), "brief_approved"], capsys)
        # Output should contain some indication of state change
        assert out.strip(), "approve output must not be empty"


# ── reject command ─────────────────────────────────────────────────────────

class TestRejectCommand:

    def test_reject_exits_zero(self, theme_ready_project, capsys):
        code, _, _ = _run(["reject", str(theme_ready_project), "reel-script"], capsys)
        assert code == 0

    def test_reject_logs_event(self, theme_ready_project, capsys):
        _run(["reject", str(theme_ready_project), "reel-script"], capsys)
        events = _read_events(theme_ready_project)
        assert any(e.get("result") == "rejected" for e in events)

    def test_reject_does_not_remove_gates(self, theme_ready_project, capsys):
        gates_before = _project_json(theme_ready_project)["gates_passed"]
        _run(["reject", str(theme_ready_project), "reel-script"], capsys)
        gates_after = _project_json(theme_ready_project)["gates_passed"]
        assert set(gates_before) == set(gates_after), \
            "reject must not modify gates_passed"


# ── invalidate command ─────────────────────────────────────────────────────

class TestInvalidateCommand:

    def test_invalidate_removes_downstream_gates(self, reconciled_project, capsys):
        """Scenario 8 (CLI): invalidate command cascades correctly."""
        assert "reconciliation_resolved" in _project_json(reconciled_project)["gates_passed"]
        code, _, _ = _run(
            ["invalidate", str(reconciled_project), "script.md"], capsys
        )
        assert code == 0
        assert "reconciliation_resolved" not in _project_json(reconciled_project)["gates_passed"]

    def test_invalidate_shows_removed_gates(self, reconciled_project, capsys):
        _, out, _ = _run(["invalidate", str(reconciled_project), "script.md"], capsys)
        assert "reconciliation_resolved" in out

    def test_invalidate_unknown_artifact_exits_nonzero(self, fresh_project, capsys):
        code, _, _ = _run(["invalidate", str(fresh_project), "unknown-file.xyz"], capsys)
        assert code != 0


# ── history command ────────────────────────────────────────────────────────

class TestHistoryCommand:

    def test_history_exits_zero_with_no_events(self, fresh_project, capsys):
        code, _, _ = _run(["history", str(fresh_project)], capsys)
        assert code == 0

    def test_history_shows_event_after_run_phase(self, theme_ready_project, capsys):
        """Scenario 9 (CLI): history shows logged events — IMPLEMENTED."""
        # Execute a phase to create an event
        _run(["run-phase", str(theme_ready_project), "reel-script"], capsys)
        capsys.readouterr()  # clear previous output

        code, out, _ = _run(["history", str(theme_ready_project)], capsys)
        assert code == 0
        # Some record of the execution must appear
        assert "reel-script" in out or "claude" in out.lower() or "paused" in out.lower()

    def test_history_empty_shows_appropriate_message(self, fresh_project, capsys):
        _, out, _ = _run(["history", str(fresh_project)], capsys)
        assert out.strip(), "history must produce non-empty output"


# ── resume command ─────────────────────────────────────────────────────────

class TestResumeCommand:

    def test_resume_exits_zero(self, theme_ready_project, capsys):
        code, _, _ = _run(["resume", str(theme_ready_project)], capsys)
        assert code == 0

    def test_resume_after_pause_shows_correct_next(self, theme_ready_project, capsys):
        """Scenario 10 (CLI): resume after pause surfaces correct next step."""
        # First pause the project
        _run(["run", str(theme_ready_project)], capsys)
        capsys.readouterr()  # clear previous output

        # Now check resume
        _, out, _ = _run(["resume", str(theme_ready_project)], capsys)
        assert "reel-script" in out.lower() or "Reel Script" in out


# ── diagnose command ───────────────────────────────────────────────────────

class TestDiagnoseCommand:

    def test_diagnose_exits_zero(self, theme_ready_project, capsys):
        code, _, _ = _run(["diagnose", str(theme_ready_project)], capsys)
        assert code == 0

    def test_diagnose_shows_gates_section(self, theme_ready_project, capsys):
        _, out, _ = _run(["diagnose", str(theme_ready_project)], capsys)
        assert "Gates" in out or "gate" in out.lower()
        assert "brief_approved" in out

    def test_diagnose_shows_next_actions(self, theme_ready_project, capsys):
        _, out, _ = _run(["diagnose", str(theme_ready_project)], capsys)
        assert "Next" in out
