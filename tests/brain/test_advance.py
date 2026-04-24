"""
tests/brain/test_advance.py — Phase 1A: advance_project() behaviour tests.

  T1. dry-run (default) never calls Runner.run_phase
  T2. human actor → skipped
  T3. claude actor → skipped
  T4. blocked diagnosis (human_required) → skipped
  T5. successful execution re-diagnoses and populates re_diagnosis_summary
  T6. brain next_action agrees with orchestrator compute_next_actions for
      the same project state (render phase — both say actor="code")
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from lib.brain.advance import advance_project, AdvanceResult, _compact_summary
from lib.orchestrator.results import ExecStatus


# ── Minimal fixture helpers ────────────────────────────────────────────────

def _make_fake_diag(
    *,
    slug: str = "test-project",
    can_continue: bool = True,
    human_required: bool = False,
    human_reason: str = "",
    next_actor: str = "code",
    next_action: str = "Run render",
    next_command: str = "npx remotion render",
    validation_errors: list[str] | None = None,
    gates_passed: list[str] | None = None,
    next_required: str | None = None,
    healthy: bool = True,
    phase: str = "qa",
    qa_available: bool = False,
):
    """Build a fake Diagnosis-like object for patching diagnose_project."""
    d = MagicMock()
    d.slug = slug
    d.phase = phase
    d.healthy = healthy
    d.project_json_found = True
    d.validation_errors = validation_errors or []

    # gates
    d.gates.passed = gates_passed or []
    d.gates.total = 11
    d.gates.next_required = next_required
    d.gates.missing = []

    # autonomy
    d.autonomy.can_continue_autonomously = can_continue
    d.autonomy.human_required = human_required
    d.autonomy.human_required_reason = human_reason
    d.autonomy.next_action = next_action
    d.autonomy.next_action_actor = next_actor
    d.autonomy.next_action_command = next_command
    d.autonomy.confidence = "high"

    # qa
    d.qa.available = qa_available
    d.qa.verdict = "not_run"

    # critic / artifacts (keep them minimal)
    d.critic.available = False
    d.artifacts.gate_artifact_mismatches = []
    d.artifacts.staleness_results = []

    return d


def _make_next_action(
    phase_key: str = "render",
    actor: str = "code",
    command_hint: str = "npx remotion render",
    blocked: bool = False,
    optional: bool = False,
):
    a = MagicMock()
    a.phase_key = phase_key
    a.actor = actor
    a.command_hint = command_hint
    a.blocked = blocked
    a.optional = optional
    return a


def _make_exec_result(status: ExecStatus = ExecStatus.SUCCESS, gate_set: str | None = None):
    r = MagicMock()
    r.status = status
    r.gate_set = gate_set
    r.output = "phase completed"
    r.error = None
    r.succeeded = (status == ExecStatus.SUCCESS)
    r.paused = status in (ExecStatus.PAUSED_FOR_CLAUDE, ExecStatus.PAUSED_FOR_HUMAN)
    return r


# ── T1 — dry-run never executes ───────────────────────────────────────────

class TestDryRunDefault:

    def test_dry_run_returns_dry_run_status(self, tmp_path):
        """Default call (no --execute) must return status='dry_run'."""
        fake_diag = _make_fake_diag()
        fake_action = _make_next_action(phase_key="render", actor="code")

        with patch("lib.brain.advance.diagnose_project", return_value=fake_diag), \
             patch("lib.brain.advance.load_snapshot"), \
             patch("lib.brain.advance.compute_next_actions", return_value=[fake_action]), \
             patch("lib.brain.advance.PHASES", {"render": MagicMock(actor="code", sets_gate=None)}), \
             patch("lib.brain.advance.Runner") as MockRunner:

            result = advance_project(tmp_path)  # execute=False is default

        assert result.status == "dry_run"
        assert result.executed is False
        MockRunner.return_value.run_phase.assert_not_called()

    def test_dry_run_populates_would_execute(self, tmp_path):
        fake_diag = _make_fake_diag()
        fake_action = _make_next_action(
            phase_key="render",
            actor="code",
            command_hint="cd remotion && npx remotion render",
        )

        with patch("lib.brain.advance.diagnose_project", return_value=fake_diag), \
             patch("lib.brain.advance.load_snapshot"), \
             patch("lib.brain.advance.compute_next_actions", return_value=[fake_action]), \
             patch("lib.brain.advance.PHASES", {"render": MagicMock(actor="code", sets_gate=None)}):

            result = advance_project(tmp_path)

        assert "render" in result.would_execute or "remotion" in result.would_execute
        assert result.re_diagnosis_summary is None  # not populated for dry_run

    def test_explicit_execute_false_is_same_as_default(self, tmp_path):
        fake_diag = _make_fake_diag()
        fake_action = _make_next_action()

        with patch("lib.brain.advance.diagnose_project", return_value=fake_diag), \
             patch("lib.brain.advance.load_snapshot"), \
             patch("lib.brain.advance.compute_next_actions", return_value=[fake_action]), \
             patch("lib.brain.advance.PHASES", {"render": MagicMock(actor="code", sets_gate=None)}), \
             patch("lib.brain.advance.Runner"):

            r_default = advance_project(tmp_path)
            r_explicit = advance_project(tmp_path, execute=False)

        assert r_default.status == r_explicit.status == "dry_run"
        assert r_default.executed == r_explicit.executed is False


# ── T2 — human actor is rejected ─────────────────────────────────────────

class TestHumanActorRejected:

    def test_human_actor_phase_returns_skipped(self, tmp_path):
        """When next phase has actor='human', advance must skip it."""
        fake_diag = _make_fake_diag(
            can_continue=True,
            human_required=False,   # autonomy says ok, but actor check catches it
        )
        fake_action = _make_next_action(phase_key="ingest-voice", actor="human")

        with patch("lib.brain.advance.diagnose_project", return_value=fake_diag), \
             patch("lib.brain.advance.load_snapshot"), \
             patch("lib.brain.advance.compute_next_actions", return_value=[fake_action]), \
             patch("lib.brain.advance.PHASES",
                   {"ingest-voice": MagicMock(actor="human", sets_gate=None)}):

            result = advance_project(tmp_path, execute=True)

        assert result.status == "skipped"
        assert result.actor == "human"
        assert result.executed is False
        assert "human" in result.reason

    def test_human_required_flag_also_skips(self, tmp_path):
        """Autonomy verdict human_required=True skips before actor check."""
        fake_diag = _make_fake_diag(
            human_required=True,
            human_reason="Gate 'script_approved' requires human review",
            next_required="script_approved",
        )

        with patch("lib.brain.advance.diagnose_project", return_value=fake_diag):
            result = advance_project(tmp_path, execute=True)

        assert result.status == "skipped"
        assert result.actor == "human"
        assert result.executed is False


# ── T3 — claude actor is rejected ────────────────────────────────────────

class TestClaudeActorRejected:

    def test_claude_actor_phase_returns_skipped(self, tmp_path):
        """When next phase has actor='claude', advance must skip it."""
        fake_diag = _make_fake_diag(can_continue=True, human_required=False)
        fake_action = _make_next_action(phase_key="reel-script", actor="claude")

        with patch("lib.brain.advance.diagnose_project", return_value=fake_diag), \
             patch("lib.brain.advance.load_snapshot"), \
             patch("lib.brain.advance.compute_next_actions", return_value=[fake_action]), \
             patch("lib.brain.advance.PHASES",
                   {"reel-script": MagicMock(actor="claude", sets_gate="script_approved")}):

            result = advance_project(tmp_path, execute=True)

        assert result.status == "skipped"
        assert result.actor == "claude"
        assert result.executed is False
        assert "claude" in result.reason

    def test_code_plus_claude_actor_rejected(self, tmp_path):
        """actor='code+claude' is not code-safe — must be skipped."""
        fake_diag = _make_fake_diag(can_continue=True)
        fake_action = _make_next_action(phase_key="qa-reel", actor="code+claude")

        with patch("lib.brain.advance.diagnose_project", return_value=fake_diag), \
             patch("lib.brain.advance.load_snapshot"), \
             patch("lib.brain.advance.compute_next_actions", return_value=[fake_action]), \
             patch("lib.brain.advance.PHASES",
                   {"qa-reel": MagicMock(actor="code+claude", sets_gate="qa_passed")}):

            result = advance_project(tmp_path, execute=True)

        assert result.status == "skipped"
        assert result.actor == "code+claude"
        assert result.executed is False


# ── T4 — blocked diagnosis skips ─────────────────────────────────────────

class TestBlockedDiagnosisSkips:

    def test_validation_errors_block_advance(self, tmp_path):
        """Validation errors must prevent any execution."""
        fake_diag = _make_fake_diag(
            validation_errors=["'slug' is required", "'style' must be one of ..."],
        )

        with patch("lib.brain.advance.diagnose_project", return_value=fake_diag):
            result = advance_project(tmp_path, execute=True)

        assert result.status == "skipped"
        assert result.executed is False
        assert "validation" in result.reason.lower()

    def test_blocked_autonomy_skips(self, tmp_path):
        """When can_continue_autonomously=False and human_required=False, skip."""
        fake_diag = _make_fake_diag(
            can_continue=False,
            human_required=False,
            next_actor="claude",
            next_action="Fix QA blockers",
        )

        with patch("lib.brain.advance.diagnose_project", return_value=fake_diag):
            result = advance_project(tmp_path, execute=True)

        assert result.status == "skipped"
        assert result.executed is False


# ── T5 — successful execution re-diagnoses ───────────────────────────────

class TestSuccessfulExecutionReDiagnoses:

    def test_succeeded_status_on_success(self, tmp_path):
        fake_diag = _make_fake_diag(can_continue=True)
        fake_action = _make_next_action(phase_key="render", actor="code")
        fake_exec = _make_exec_result(ExecStatus.SUCCESS, gate_set=None)

        # Post-execution diagnosis (more gates passed)
        post_diag = _make_fake_diag(
            can_continue=False,
            human_required=False,
            gates_passed=["brief_approved", "theme_set", "script_approved",
                          "reconciliation_resolved", "visual_assignment_approved",
                          "asset_fitness_passed", "technical_planning_approved",
                          "motion_intent_reviewed", "assets_validated",
                          "preview_passed", "qa_passed"],
            healthy=True,
            phase="render",
        )

        with patch("lib.brain.advance.diagnose_project",
                   side_effect=[fake_diag, post_diag]) as mock_diag, \
             patch("lib.brain.advance.load_snapshot"), \
             patch("lib.brain.advance.compute_next_actions", return_value=[fake_action]), \
             patch("lib.brain.advance.PHASES",
                   {"render": MagicMock(actor="code", sets_gate=None)}), \
             patch("lib.brain.advance.Runner") as MockRunner, \
             patch("lib.brain.advance.ExecStatus", ExecStatus):

            MockRunner.return_value.run_phase.return_value = fake_exec
            result = advance_project(tmp_path, execute=True)

        assert result.status == "succeeded"
        assert result.executed is True
        assert result.re_diagnosis_summary is not None
        # Runner.run_phase was called exactly once
        MockRunner.return_value.run_phase.assert_called_once()
        # diagnose_project was called twice: once before, once after
        assert mock_diag.call_count == 2

    def test_re_diagnosis_summary_has_required_keys(self, tmp_path):
        fake_diag = _make_fake_diag(can_continue=True)
        fake_action = _make_next_action(phase_key="render", actor="code")
        fake_exec = _make_exec_result(ExecStatus.SUCCESS)
        post_diag = _make_fake_diag(phase="render", healthy=True)

        with patch("lib.brain.advance.diagnose_project", side_effect=[fake_diag, post_diag]), \
             patch("lib.brain.advance.load_snapshot"), \
             patch("lib.brain.advance.compute_next_actions", return_value=[fake_action]), \
             patch("lib.brain.advance.PHASES",
                   {"render": MagicMock(actor="code", sets_gate=None)}), \
             patch("lib.brain.advance.Runner") as MockRunner, \
             patch("lib.brain.advance.ExecStatus", ExecStatus):

            MockRunner.return_value.run_phase.return_value = fake_exec
            result = advance_project(tmp_path, execute=True)

        s = result.re_diagnosis_summary
        assert s is not None
        for key in ("slug", "phase", "healthy", "gates_passed", "gates_total",
                    "next_required", "can_continue", "human_required",
                    "next_action", "qa_verdict"):
            assert key in s, f"re_diagnosis_summary missing key: {key}"

    def test_result_is_json_serializable(self, tmp_path):
        """AdvanceResult.to_dict() must round-trip through json.dumps."""
        fake_diag = _make_fake_diag(can_continue=True)
        fake_action = _make_next_action()
        fake_exec = _make_exec_result(ExecStatus.SUCCESS)
        post_diag = _make_fake_diag()

        with patch("lib.brain.advance.diagnose_project", side_effect=[fake_diag, post_diag]), \
             patch("lib.brain.advance.load_snapshot"), \
             patch("lib.brain.advance.compute_next_actions", return_value=[fake_action]), \
             patch("lib.brain.advance.PHASES",
                   {"render": MagicMock(actor="code", sets_gate=None)}), \
             patch("lib.brain.advance.Runner") as MockRunner, \
             patch("lib.brain.advance.ExecStatus", ExecStatus):

            MockRunner.return_value.run_phase.return_value = fake_exec
            result = advance_project(tmp_path, execute=True)

        # Should not raise
        serialized = json.dumps(result.to_dict())
        roundtripped = json.loads(serialized)
        assert roundtripped["status"] == "succeeded"
        assert roundtripped["executed"] is True


# ── T6 — brain and orchestrator agree on next code action ────────────────

class TestBrainOrchestratorAgreement:

    def test_both_identify_render_as_next_code_action(self, tmp_path):
        """
        For a project where all 11 gates are passed (state='qa_passed'):
          - brain.diagnose says: can_continue=True, actor='code', action→render
          - orchestrator.compute_next_actions says: render, actor='code'
        Both must agree the next runnable code action is 'render'.
        """
        all_gates = [
            "brief_approved", "theme_set", "script_approved",
            "reconciliation_resolved", "visual_assignment_approved",
            "asset_fitness_passed", "technical_planning_approved",
            "motion_intent_reviewed", "assets_validated",
            "preview_passed", "qa_passed",
        ]

        # Build a valid project directory with a properly-named slug subfolder
        # so the slug matches the directory name and passes validation.
        proj_dir = tmp_path / "test-advance"
        proj_dir.mkdir()

        proj = {
            "schema_version": 2,
            "project_type": "reel",
            "slug": "test-advance",
            "title": "Test advance project",
            "topic": "test",
            "audience": "developers",
            "content_type": "product-launch",
            "target_duration_seconds": 30,
            "source_url": "https://example.com",
            "style": "cinematic-presenter",
            "theme": "tech-neutral",
            "theme_primary": "#000000",
            "theme_secondary": "#333333",
            "phase": "qa",
            "status": "completed",
            "gates_passed": all_gates,
            "created": "2026-01-01T00:00:00Z",
            "updated": "2026-01-01T00:00:00Z",
        }
        (proj_dir / "project.json").write_text(
            json.dumps(proj, indent=2), encoding="utf-8"
        )

        # ── Brain path ─────────────────────────────────────────────────────
        from lib.brain.diagnose import diagnose_project
        diag = diagnose_project(proj_dir)

        assert not diag.validation_errors, (
            f"Project fixture must be valid; got errors: {diag.validation_errors}"
        )
        assert diag.autonomy.can_continue_autonomously, (
            "Brain should say can_continue=True when all gates passed"
        )
        assert diag.autonomy.next_action_actor == "code", (
            f"Brain should identify actor='code' for render, got {diag.autonomy.next_action_actor!r}"
        )

        # ── Orchestrator path ──────────────────────────────────────────────
        from lib.orchestrator.state import load_snapshot
        from lib.orchestrator.transitions import compute_next_actions

        snap = load_snapshot(proj_dir)
        assert snap.orchestration_state == "qa_passed", (
            f"Expected orchestration state 'qa_passed', got {snap.orchestration_state!r}"
        )

        actions = compute_next_actions(snap)
        runnable = [a for a in actions if not a.blocked and not a.optional]

        assert runnable, "Orchestrator should return at least one runnable action"
        top_action = runnable[0]

        assert top_action.phase_key == "render", (
            f"Orchestrator should identify 'render' next, got {top_action.phase_key!r}"
        )
        assert top_action.actor == "code", (
            f"Orchestrator should say actor='code' for render, got {top_action.actor!r}"
        )

        # ── Agreement check ────────────────────────────────────────────────
        # Both must agree that the next code action is "render"
        assert diag.autonomy.next_action_actor == top_action.actor == "code"
