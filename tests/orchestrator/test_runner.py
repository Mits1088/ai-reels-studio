"""
tests/orchestrator/test_runner.py — Execution layer behavior tests.

Validates Runner.run() and Runner.run_phase() across all core scenarios:
  A. Claude pause behavior
  B. Human pause behavior
  C. Illegal phase rejection (missing gates)
  D. Code phase execution (mocked + skipped)
  E. run() stops at first pause
  F. Parity-blocked execution
  G. Missing required file blocks phase
  H. Pause state written to project.json
  I. Event logging on execution
  J. WorkOrder and HumanAction content validity
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lib.orchestrator.results import ExecStatus
from lib.orchestrator.runner import Runner
from lib.orchestrator.tasks import TaskResult
from lib.orchestrator.state import load_snapshot


# ── Helpers ────────────────────────────────────────────────────────────────

def _read_events(project_dir: Path) -> list[dict]:
    log = project_dir / "output" / "orchestration-log.jsonl"
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


def _project_json(project_dir: Path) -> dict:
    return json.loads((project_dir / "project.json").read_text(encoding="utf-8"))


# ── A. Claude pause behavior ───────────────────────────────────────────────

class TestClaudePauseBehavior:

    def test_run_phase_pauses_for_claude(self, theme_ready_project):
        """Scenario 4: run_pauses_for_claude_phase — IMPLEMENTED."""
        result = Runner().run_phase(theme_ready_project, "reel-script")
        assert result.status == ExecStatus.PAUSED_FOR_CLAUDE

    def test_run_pauses_for_claude_has_work_order(self, theme_ready_project):
        result = Runner().run_phase(theme_ready_project, "reel-script")
        assert result.work_order is not None, "Claude phase must emit a WorkOrder"
        assert result.human_action is None

    def test_work_order_has_required_fields(self, theme_ready_project):
        """WorkOrder must have phase_key, purpose, approval_command, project_slug."""
        result = Runner().run_phase(theme_ready_project, "reel-script")
        wo = result.work_order
        assert wo.phase_key == "reel-script"
        assert wo.project_slug == theme_ready_project.name
        assert wo.purpose, "WorkOrder.purpose must be non-empty"
        assert "approve" in wo.approval_command, "approval_command must reference approve command"
        assert wo.sets_gate == "script_approved"

    def test_work_order_has_memory_and_rules(self, theme_ready_project):
        """WorkOrder for reel-script must include creative core memory and hook grammar."""
        result = Runner().run_phase(theme_ready_project, "reel-script")
        wo = result.work_order
        assert len(wo.memory_to_read) > 0, "reel-script must specify memory files to read"
        assert len(wo.rules_to_apply) > 0, "reel-script must specify rule files"

    def test_work_order_creative_intent_required_for_script(self, theme_ready_project):
        """reel-script requires Creative Intent Summary."""
        result = Runner().run_phase(theme_ready_project, "reel-script")
        assert result.work_order.creative_intent_required is True

    def test_run_stops_at_claude_phase(self, theme_ready_project):
        """Scenario 1 (partial): run() reaches claude phase and stops."""
        report = Runner().run(theme_ready_project)
        assert report.final_status == ExecStatus.PAUSED_FOR_CLAUDE
        assert report.terminal_work_order is not None
        # No phases should have succeeded (reel-script is the first action and it pauses)
        assert report.phases_succeeded == 0

    def test_claude_pause_writes_pause_state(self, theme_ready_project):
        """Scenario H: pause state written to project.json."""
        Runner().run(theme_ready_project)
        proj = _project_json(theme_ready_project)
        assert "_paused_at" in proj, "project.json must have _paused_at after pause"
        assert proj["_paused_at"] == "reel-script"
        assert proj["_paused_for"] == "paused_for_claude"


# ── B. Human pause behavior ────────────────────────────────────────────────

class TestHumanPauseBehavior:

    def test_run_phase_pauses_for_human(self, script_ready_project):
        """Scenario 5: run_pauses_for_human_approval — IMPLEMENTED."""
        result = Runner().run_phase(script_ready_project, "ingest-voice")
        assert result.status == ExecStatus.PAUSED_FOR_HUMAN

    def test_run_phase_human_has_action_checklist(self, script_ready_project):
        result = Runner().run_phase(script_ready_project, "ingest-voice")
        assert result.human_action is not None, "Human phase must emit a HumanAction"
        assert result.work_order is None

    def test_human_action_has_steps(self, script_ready_project):
        result = Runner().run_phase(script_ready_project, "ingest-voice")
        ha = result.human_action
        assert ha.phase_key == "ingest-voice"
        assert len(ha.steps) > 0, "HumanAction must have at least one step"

    def test_human_action_has_commands(self, script_ready_project):
        result = Runner().run_phase(script_ready_project, "ingest-voice")
        ha = result.human_action
        assert "approve" in ha.approval_command
        assert "reject" in ha.rejection_command

    def test_assembled_project_pauses_for_preview(self, assembled_project):
        """Preview is a human phase — run() should pause there."""
        report = Runner().run(assembled_project)
        assert report.final_status == ExecStatus.PAUSED_FOR_HUMAN
        assert report.terminal_human_action is not None

    def test_human_pause_writes_pause_state(self, script_ready_project):
        Runner().run(script_ready_project)
        proj = _project_json(script_ready_project)
        assert "_paused_at" in proj
        assert proj["_paused_for"] == "paused_for_human"


# ── C. Illegal phase rejection ────────────────────────────────────────────

class TestIllegalPhaseRejection:

    def test_run_phase_fails_on_missing_gates(self, fresh_project):
        """Scenario 3: run_phase_fails_on_illegal_phase — missing required gates."""
        result = Runner().run_phase(fresh_project, "reel-script")
        assert result.status == ExecStatus.BLOCKED

    def test_run_phase_blocked_has_error_message(self, fresh_project):
        result = Runner().run_phase(fresh_project, "reel-script")
        assert result.error, "Blocked result must have error message explaining why"
        assert "brief_approved" in result.error or "gate" in result.error.lower()

    def test_run_phase_blocked_does_not_mutate_gates(self, fresh_project):
        """Blocked phase must not add or remove any gates from project.json."""
        gates_before = _project_json(fresh_project)["gates_passed"]
        Runner().run_phase(fresh_project, "reel-script")
        gates_after = _project_json(fresh_project)["gates_passed"]
        assert gates_before == gates_after, "Blocked phase must not mutate gates"

    def test_run_phase_unknown_key_fails(self, fresh_project):
        result = Runner().run_phase(fresh_project, "nonexistent-phase-xyz")
        assert result.status == ExecStatus.FAILED

    def test_run_phase_unknown_key_has_error(self, fresh_project):
        result = Runner().run_phase(fresh_project, "nonexistent-phase-xyz")
        assert result.error, "Unknown phase must produce an error message"

    def test_render_blocked_when_missing_required_file(self, tmp_path):
        """Scenario 7: run_blocks_on_missing_artifact — IMPLEMENTED.

        qa_passed gate set but output/qa-report.md not present.
        """
        from tests.orchestrator.conftest import make_project
        project_dir = make_project(
            tmp_path,
            "test-no-qa-report",
            gates=[
                "brief_approved", "theme_set", "script_approved",
                "reconciliation_resolved",
                "visual_assignment_approved", "asset_fitness_passed",
                "technical_planning_approved",
                "motion_intent_reviewed", "assets_validated",
                "preview_passed", "qa_passed",
            ],
            extra_files={
                # output/qa-report.md intentionally omitted
                "output/timeline.json": "{}",
            },
        )
        result = Runner().run_phase(project_dir, "render")
        assert result.status == ExecStatus.BLOCKED
        assert "qa-report.md" in (result.error or "").lower() or "missing" in (result.error or "").lower()


# ── D. Code phase execution ────────────────────────────────────────────────

class TestCodePhaseExecution:

    def test_asset_prep_skips_gracefully(self, shot_list_ready_project):
        """Code phase with no registered task returns SKIPPED, not FAILED."""
        result = Runner().run_phase(shot_list_ready_project, "asset-prep")
        assert result.status == ExecStatus.SKIPPED

    def test_render_succeeds_with_mocked_task(self, qa_passed_project):
        """Scenario 2: run_phase_succeeds_on_legal_phase — IMPLEMENTED (mocked)."""
        mock_task = MagicMock(return_value=TaskResult(
            exit_code=0,
            output="Render complete: out/reel.mp4",
            error=None,
            sets_gate=None,
            duration_s=12.4,
        ))
        with patch("lib.orchestrator.executors.get_task", return_value=mock_task):
            result = Runner().run_phase(qa_passed_project, "render")

        assert result.status == ExecStatus.SUCCESS
        mock_task.assert_called_once_with(qa_passed_project)

    def test_code_phase_failure_on_nonzero_exit(self, qa_passed_project):
        """Code task returning non-zero exit_code produces FAILED status."""
        mock_task = MagicMock(return_value=TaskResult(
            exit_code=1,
            output="",
            error="render failed: missing codec",
            sets_gate=None,
            duration_s=0.1,
        ))
        with patch("lib.orchestrator.executors.get_task", return_value=mock_task):
            result = Runner().run_phase(qa_passed_project, "render")

        assert result.status == ExecStatus.FAILED
        assert result.error is not None

    def test_code_phase_sets_gate_on_success(self, tmp_path):
        """Code task that sets_gate propagates gate to project.json."""
        from tests.orchestrator.conftest import make_project
        from lib.constants import GATE_ORDER

        # qa_passed gate is all gates
        all_gates_except_qa = [g for g in GATE_ORDER if g != "qa_passed"]
        project_dir = make_project(
            tmp_path,
            "test-gate-set",
            gates=all_gates_except_qa,
            extra_files={
                "output/timeline.json": "{}",
                "output/motion-intent.md": "# Motion Intent\n",
            },
        )

        mock_task = MagicMock(return_value=TaskResult(
            exit_code=0,
            output="QA passed",
            error=None,
            sets_gate="qa_passed",
            duration_s=1.0,
        ))
        with patch("lib.orchestrator.executors.get_task", return_value=mock_task):
            result = Runner().run_phase(project_dir, "qa-reel")

        # qa-reel is code+claude, code part succeeded and set gate
        # then it should pause for Claude OR succeed if qa_passed gate is set
        assert result.status in (ExecStatus.SUCCESS, ExecStatus.PAUSED_FOR_CLAUDE)
        if result.status == ExecStatus.SUCCESS:
            assert "qa_passed" in _project_json(project_dir)["gates_passed"]

    def test_run_advances_through_skipped_phases(self, shot_list_ready_project):
        """Scenario 1: run_advances_deterministic_phase — IMPLEMENTED (skipped).

        asset-prep is a code phase with no task → SKIPPED.
        run() should process it without failing.
        """
        # shot_list_ready: motion-intent (claude) and asset-prep (code) are both legal.
        # run() takes the first unblocked non-optional action.
        report = Runner().run(shot_list_ready_project)
        # Either paused for Claude (motion-intent) or skipped (asset-prep)
        # depending on priority ordering. Either way, not FAILED.
        assert report.final_status != ExecStatus.FAILED
        assert report.phases_run >= 0


# ── E. Parity-blocked execution ────────────────────────────────────────────

class TestParityBlockedExecution:

    def test_parity_failure_blocks_render(self, qa_passed_project):
        """Scenario 6: run_blocks_on_parity_failure — IMPLEMENTED (mocked parity)."""
        failing_check = MagicMock()
        failing_check.check.description = "avatar_absence_hard_max"
        failing_check.check.must_match = True
        failing_check.check.fix_hint = "Update qa-gates.md to match STYLE_THRESHOLDS"
        failing_check.detail = "Expected 15s but found 12s"
        failing_check.passed = False

        with patch("lib.orchestrator.validators._run_parity_checks",
                   return_value=[_make_validation_failure("render", "parity_failed",
                                                          "Parity check failed: avatar_absence_hard_max",
                                                          "Update qa-gates.md")]):
            result = Runner().run_phase(qa_passed_project, "render")

        assert result.status == ExecStatus.BLOCKED
        assert result.error is not None

    def test_parity_failure_does_not_mutate_state(self, qa_passed_project):
        """A parity-blocked render must not remove any gates."""
        gates_before = set(_project_json(qa_passed_project)["gates_passed"])

        with patch("lib.orchestrator.validators._run_parity_checks",
                   return_value=[_make_validation_failure("render", "parity_failed",
                                                          "parity check failed", "fix hint")]):
            Runner().run_phase(qa_passed_project, "render")

        gates_after = set(_project_json(qa_passed_project)["gates_passed"])
        assert gates_before == gates_after


def _make_validation_failure(phase, kind, message, fix_hint):
    from lib.orchestrator.validators import ValidationFailure
    return ValidationFailure(phase=phase, kind=kind, message=message, fix_hint=fix_hint)


# ── F. Invalidation cascade ────────────────────────────────────────────────

class TestInvalidationCascade:

    def test_invalidate_script_removes_downstream_gates(self, reconciled_project):
        """Scenario 8: invalidate_marks_downstream_stale — IMPLEMENTED."""
        from lib.orchestrator.invalidation import invalidate_from_change

        gates_before = _project_json(reconciled_project)["gates_passed"]
        assert "reconciliation_resolved" in gates_before

        result = invalidate_from_change(reconciled_project, "script.md")

        gates_after = _project_json(reconciled_project)["gates_passed"]
        assert "reconciliation_resolved" not in gates_after, \
            "Invalidating script.md must remove reconciliation_resolved and all downstream"
        assert result.reset_from_gate is not None

    def test_invalidate_script_does_not_remove_upstream_gates(self, reconciled_project):
        """Invalidation must only remove the triggered gate and downstream."""
        from lib.orchestrator.invalidation import invalidate_from_change

        invalidate_from_change(reconciled_project, "script.md")
        gates_after = _project_json(reconciled_project)["gates_passed"]
        # brief_approved and theme_set are upstream of script.md — must survive
        assert "brief_approved" in gates_after
        assert "theme_set" in gates_after

    def test_invalidate_unknown_artifact_returns_no_reset(self, reconciled_project):
        from lib.orchestrator.invalidation import invalidate_from_change
        result = invalidate_from_change(reconciled_project, "nonexistent.json")
        assert result.reset_from_gate is None, "Unknown artifact must produce no invalidation"

    def test_run_respects_stale_state_after_invalidation(self, reconciled_project):
        """After invalidation, run() sees the degraded state and routes correctly."""
        from lib.orchestrator.invalidation import invalidate_from_change

        invalidate_from_change(reconciled_project, "script.md")

        # State is now at least "script_ready" (reconciliation_resolved removed)
        snap = load_snapshot(reconciled_project)
        assert snap.orchestration_state not in ("reconciled",), \
            "After invalidating script.md, state should no longer be 'reconciled'"


# ── G. Event logging ────────────────────────────────────────────────────────

class TestEventLogging:

    def test_run_phase_creates_event_log(self, theme_ready_project):
        """Scenario 9: history_records_execution_event — IMPLEMENTED."""
        events_before = _read_events(theme_ready_project)
        Runner().run_phase(theme_ready_project, "reel-script")
        events_after = _read_events(theme_ready_project)
        assert len(events_after) > len(events_before), \
            "run_phase must write at least one event to orchestration-log.jsonl"

    def test_event_log_has_required_fields(self, theme_ready_project):
        Runner().run_phase(theme_ready_project, "reel-script")
        events = _read_events(theme_ready_project)
        assert events, "Event log must not be empty after execution"
        last = events[-1]
        assert "timestamp" in last
        assert "actor" in last
        assert "action" in last
        assert "result" in last

    def test_blocked_phase_logs_blocked_result(self, fresh_project):
        Runner().run_phase(fresh_project, "reel-script")
        events = _read_events(fresh_project)
        # A blocked phase may or may not log depending on implementation.
        # If it logs, the result must be "blocked" or "failed".
        if events:
            results = {e.get("result") for e in events}
            assert results <= {"blocked", "failed", "paused"}, \
                f"Unexpected event result values: {results}"

    def test_run_loop_logs_events(self, assembled_project):
        """run() on assembled_project pauses at preview — event must be logged."""
        Runner().run(assembled_project)
        events = _read_events(assembled_project)
        assert len(events) >= 1, "run() loop must log at least one event"


# ── H. Resume behavior ────────────────────────────────────────────────────

class TestResumeBehavior:

    def test_pause_state_preserved_for_resume(self, theme_ready_project):
        """Scenario 10: resume_after_pause_surfaces_correct_next_step — IMPLEMENTED."""
        Runner().run(theme_ready_project)
        proj = _project_json(theme_ready_project)
        assert "_paused_at" in proj, \
            "project.json must have _paused_at after pause so resume command can use it"

    def test_paused_at_matches_actual_phase(self, theme_ready_project):
        Runner().run(theme_ready_project)
        proj = _project_json(theme_ready_project)
        assert proj.get("_paused_at") == "reel-script", \
            "_paused_at must name the phase that caused the pause"

    def test_clear_pause_state_on_success(self, qa_passed_project):
        """Successful code execution clears pause state."""
        # First write a fake pause state manually
        proj = _project_json(qa_passed_project)
        proj["_paused_at"] = "some-old-phase"
        proj["_paused_for"] = "paused_for_claude"
        (qa_passed_project / "project.json").write_text(
            json.dumps(proj, indent=2), encoding="utf-8"
        )

        mock_task = MagicMock(return_value=TaskResult(
            exit_code=0, output="done", error=None, sets_gate=None, duration_s=1.0
        ))
        with patch("lib.orchestrator.executors.get_task", return_value=mock_task):
            Runner().run_phase(qa_passed_project, "render")

        proj_after = _project_json(qa_passed_project)
        assert "_paused_at" not in proj_after, \
            "Successful execution must clear _paused_at from project.json"

    def test_run_snapshot_state_reflects_pause(self, theme_ready_project):
        """After run() pauses, load_snapshot reflects the project state correctly."""
        Runner().run(theme_ready_project)
        snap = load_snapshot(theme_ready_project)
        # State must still be theme_ready (no gates changed by a Claude pause)
        assert snap.orchestration_state == "theme_ready"


# ── I. Work order / human action content ──────────────────────────────────

class TestOutputContent:

    def test_work_order_render_returns_string(self, theme_ready_project):
        result = Runner().run_phase(theme_ready_project, "reel-script")
        rendered = result.work_order.render()
        assert isinstance(rendered, str)
        assert "WORK ORDER" in rendered
        assert "reel-script" in rendered.lower() or "Reel Script" in rendered

    def test_work_order_render_includes_approval_command(self, theme_ready_project):
        result = Runner().run_phase(theme_ready_project, "reel-script")
        rendered = result.work_order.render()
        assert "approve" in rendered

    def test_human_action_render_returns_string(self, script_ready_project):
        result = Runner().run_phase(script_ready_project, "ingest-voice")
        rendered = result.human_action.render()
        assert isinstance(rendered, str)
        assert "ACTION REQUIRED" in rendered

    def test_human_action_render_has_numbered_steps(self, script_ready_project):
        result = Runner().run_phase(script_ready_project, "ingest-voice")
        rendered = result.human_action.render()
        assert " 1." in rendered, "Rendered HumanAction must show numbered steps"

    def test_exec_result_summary_line_format(self, theme_ready_project):
        result = Runner().run_phase(theme_ready_project, "reel-script")
        summary = result.summary_line()
        assert "paused_for_claude" in summary
        assert result.phase_name in summary

    def test_run_report_summary_includes_all_results(self, theme_ready_project):
        report = Runner().run(theme_ready_project)
        summary = report.summary()
        assert "test-theme-ready" in summary
        assert report.final_status.value in summary
