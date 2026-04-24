"""
Tests for Phase 2 — critic integration (advisory vs hard mode).

Covers:
  - Advisory mode (default): critic_blocked never blocks can_continue_autonomously
  - Advisory mode: Diagnosis.healthy unaffected by critic_blocked
  - Advisory mode: repair plan labels critic steps as [advisory]
  - Advisory mode: critic_advisory_signal property
  - Hard mode: critic_blocked blocks can_continue_autonomously when all gates passed
  - Hard mode: Diagnosis.healthy returns False when critic_blocked
  - Hard mode: repair plan labels critic steps as [BLOCKER]
  - Hard mode: clear fix path always present in critic repair steps
  - Backward compat: default critic_hard_mode=False, no existing project newly blocks
  - CriticStatus not available: no effect in either mode
  - critic_warnings: never a blocker in either mode (only critic_blocked is)
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from lib.brain.models import (
    AutonomyVerdict,
    CriticStatus,
    Diagnosis,
    GateInventory,
    QAStatus,
    ArtifactInventory,
)
from lib.brain.diagnose import _build_autonomy_verdict
from lib.brain.repair import generate_repair_plan


# ── Helpers ────────────────────────────────────────────────────────────────────

def _all_gates_passed() -> GateInventory:
    from lib.constants import GATE_ORDER
    return GateInventory(
        passed=list(GATE_ORDER),
        missing=[],
        next_required=None,
        unknown_gates=[],
        total=len(GATE_ORDER),
    )


def _mid_pipeline_gates() -> GateInventory:
    """Gates up to script_approved only."""
    from lib.constants import GATE_ORDER
    passed = GATE_ORDER[:3]
    missing = list(GATE_ORDER[3:])
    return GateInventory(
        passed=list(passed),
        missing=missing,
        next_required=missing[0] if missing else None,
        unknown_gates=[],
        total=len(GATE_ORDER),
    )


def _qa_pass() -> QAStatus:
    return QAStatus(
        available=True, verdict="PASS", blockers=0, warnings=0,
        top_blockers=[], report_timestamp="",
    )


def _qa_not_run() -> QAStatus:
    return QAStatus(
        available=False, verdict="not_run", blockers=0, warnings=0,
        top_blockers=[], report_timestamp="",
    )


def _critic_blocked(count: int = 3, severity: str = "block") -> CriticStatus:
    # hard_blocked=True so that tests exercising hard-mode blocking still work
    # after Phase 5 changed the check from `status == "critic_blocked"` to `hard_blocked`.
    return CriticStatus(
        available=True,
        status="critic_blocked",
        findings_count=count,
        highest_severity=severity,
        top_findings=["text-emphasis-domination: 6 consecutive text-emphasis beats"],
        hard_blocked=True,
    )


def _critic_warnings() -> CriticStatus:
    return CriticStatus(
        available=True,
        status="critic_warnings",
        findings_count=2,
        highest_severity="warn",
        top_findings=["pacing-density: slight warning"],
    )


def _critic_not_run() -> CriticStatus:
    return CriticStatus(
        available=False, status="not_run",
        findings_count=0, highest_severity="none", top_findings=[],
    )


def _make_diag_mock(
    slug: str = "test-proj",
    critic_status_obj: CriticStatus | None = None,
    critic_hard_mode: bool = False,
    validation_errors: list[str] | None = None,
    gate_artifact_mismatches: list[str] | None = None,
    qa_available: bool = False,
    qa_verdict: str = "not_run",
    all_gates: bool = False,
) -> MagicMock:
    d = MagicMock()
    d.slug = slug
    d.validation_errors = validation_errors or []
    d.artifacts.gate_artifact_mismatches = gate_artifact_mismatches or []
    d.artifacts.staleness_results = []
    d.qa.available = qa_available
    d.qa.verdict = qa_verdict
    d.qa.blockers = 0
    d.qa.top_blockers = []
    cs = critic_status_obj or _critic_not_run()
    d.critic.available = cs.available
    d.critic.status = cs.status
    d.critic.findings_count = cs.findings_count
    d.critic.highest_severity = cs.highest_severity
    d.critic.top_findings = cs.top_findings
    d.critic.hard_blocked = cs.hard_blocked
    d.critic.hard_blocked_findings = cs.hard_blocked_findings
    d.autonomy.next_action = "next step"
    d.autonomy.human_required = False
    d.autonomy.human_required_reason = ""
    d.healthy = False
    d.gates.next_required = None
    return d


# ── T1: Advisory mode (default) — autonomy not affected ───────────────────────

class TestAdvisoryModeAutonomy:
    def test_critic_blocked_does_not_block_when_all_gates_passed(self):
        """Default mode: critic_blocked → can_continue stays True (advisory)."""
        verdict = _build_autonomy_verdict(
            _all_gates_passed(),
            _qa_pass(),
            [],
            critic=_critic_blocked(),
            critic_hard_mode=False,
        )
        assert verdict.can_continue_autonomously is True
        assert verdict.human_required is False

    def test_critic_blocked_advisory_next_action_still_render(self):
        verdict = _build_autonomy_verdict(
            _all_gates_passed(),
            _qa_pass(),
            [],
            critic=_critic_blocked(),
            critic_hard_mode=False,
        )
        assert "render" in verdict.next_action.lower()

    def test_critic_not_run_advisory_still_continues(self):
        verdict = _build_autonomy_verdict(
            _all_gates_passed(),
            _qa_pass(),
            [],
            critic=_critic_not_run(),
            critic_hard_mode=False,
        )
        assert verdict.can_continue_autonomously is True

    def test_critic_warnings_advisory_still_continues(self):
        verdict = _build_autonomy_verdict(
            _all_gates_passed(),
            _qa_pass(),
            [],
            critic=_critic_warnings(),
            critic_hard_mode=False,
        )
        assert verdict.can_continue_autonomously is True

    def test_mid_pipeline_critic_blocked_advisory_does_not_block(self):
        """Even mid-pipeline, critic_blocked advisory never changes routing."""
        verdict = _build_autonomy_verdict(
            _mid_pipeline_gates(),
            _qa_not_run(),
            [],
            critic=_critic_blocked(),
            critic_hard_mode=False,
        )
        # GATE_ORDER[3] = reconciliation_resolved (claude gate) → not a human block
        # Key: critic_blocked in advisory mode does NOT change gate-driven routing
        assert verdict.human_required is False
        assert verdict.can_continue_autonomously is True
        assert "critic" not in verdict.next_action.lower()


# ── T2: Advisory mode — Diagnosis.healthy unaffected ──────────────────────────

class TestAdvisoryModeHealthy:
    def _minimal_diagnosis(self, critic_hard_mode: bool = False) -> Diagnosis:
        from lib.constants import GATE_ORDER
        gates = _all_gates_passed()
        artifacts = MagicMock()
        artifacts.gate_artifact_mismatches = []
        return Diagnosis(
            slug="proj",
            title="",
            project_dir="/tmp/proj",
            project_json_found=True,
            schema_version=2,
            schema_ok=True,
            phase="render",
            status="approved",
            style="cinematic-presenter",
            theme="Tech Neutral",
            theme_primary="#000000",
            validation_errors=[],
            gates=gates,
            artifacts=artifacts,
            qa=_qa_pass(),
            critic=_critic_blocked(),
            autonomy=_build_autonomy_verdict(
                gates, _qa_pass(), [],
                critic=_critic_blocked(),
                critic_hard_mode=critic_hard_mode,
            ),
            critic_hard_mode=critic_hard_mode,
            diagnosis_timestamp="2026-01-01T00:00:00Z",
        )

    def test_advisory_mode_healthy_ignores_critic_blocked(self):
        diag = self._minimal_diagnosis(critic_hard_mode=False)
        assert diag.healthy is True

    def test_advisory_mode_critic_advisory_signal_true(self):
        diag = self._minimal_diagnosis(critic_hard_mode=False)
        assert diag.critic_advisory_signal is True

    def test_hard_mode_healthy_false_when_critic_blocked(self):
        diag = self._minimal_diagnosis(critic_hard_mode=True)
        assert diag.healthy is False

    def test_hard_mode_critic_advisory_signal_false(self):
        diag = self._minimal_diagnosis(critic_hard_mode=True)
        assert diag.critic_advisory_signal is False

    def test_no_critic_report_advisory_signal_false(self):
        """critic_advisory_signal is False when no critic report exists."""
        gates = _all_gates_passed()
        artifacts = MagicMock()
        artifacts.gate_artifact_mismatches = []
        diag = Diagnosis(
            slug="proj", title="", project_dir="/tmp",
            project_json_found=True, schema_version=2, schema_ok=True,
            phase="render", status="approved",
            style="cinematic-presenter", theme="", theme_primary="",
            validation_errors=[],
            gates=gates, artifacts=artifacts,
            qa=_qa_pass(), critic=_critic_not_run(),
            autonomy=_build_autonomy_verdict(gates, _qa_pass(), []),
            critic_hard_mode=False,
            diagnosis_timestamp="2026-01-01T00:00:00Z",
        )
        assert diag.critic_advisory_signal is False


# ── T3: Hard mode — blocks when all gates passed ───────────────────────────────

class TestHardModeAutonomy:
    def test_hard_mode_blocks_when_critic_blocked_and_all_gates_passed(self):
        verdict = _build_autonomy_verdict(
            _all_gates_passed(),
            _qa_pass(),
            [],
            critic=_critic_blocked(),
            critic_hard_mode=True,
        )
        assert verdict.can_continue_autonomously is False
        assert verdict.human_required is False

    def test_hard_mode_next_action_mentions_critic_hard_mode(self):
        verdict = _build_autonomy_verdict(
            _all_gates_passed(),
            _qa_pass(),
            [],
            critic=_critic_blocked(),
            critic_hard_mode=True,
        )
        assert "--critic-hard-mode" in verdict.next_action

    def test_hard_mode_actor_is_claude(self):
        verdict = _build_autonomy_verdict(
            _all_gates_passed(),
            _qa_pass(),
            [],
            critic=_critic_blocked(),
            critic_hard_mode=True,
        )
        assert verdict.next_action_actor == "claude"

    def test_hard_mode_confidence_is_high(self):
        verdict = _build_autonomy_verdict(
            _all_gates_passed(),
            _qa_pass(),
            [],
            critic=_critic_blocked(),
            critic_hard_mode=True,
        )
        assert verdict.confidence == "high"

    def test_hard_mode_critic_warnings_does_not_block(self):
        """critic_warnings should never block even in hard mode."""
        verdict = _build_autonomy_verdict(
            _all_gates_passed(),
            _qa_pass(),
            [],
            critic=_critic_warnings(),
            critic_hard_mode=True,
        )
        assert verdict.can_continue_autonomously is True

    def test_hard_mode_no_critic_report_does_not_block(self):
        verdict = _build_autonomy_verdict(
            _all_gates_passed(),
            _qa_pass(),
            [],
            critic=_critic_not_run(),
            critic_hard_mode=True,
        )
        assert verdict.can_continue_autonomously is True

    def test_hard_mode_qa_fail_takes_priority_over_critic(self):
        """QA fail is checked before critic — QA fail reason is returned."""
        qa_fail = QAStatus(
            available=True, verdict="FAIL", blockers=2, warnings=0,
            top_blockers=["encoding"], report_timestamp="",
        )
        verdict = _build_autonomy_verdict(
            _all_gates_passed(),
            qa_fail,
            [],
            critic=_critic_blocked(),
            critic_hard_mode=True,
        )
        assert verdict.can_continue_autonomously is False
        assert "QA" in verdict.next_action or "blocker" in verdict.next_action.lower()

    def test_hard_mode_mid_pipeline_critic_still_routed_by_gates(self):
        """Mid-pipeline: critic hard-mode check only fires when all gates passed."""
        verdict = _build_autonomy_verdict(
            _mid_pipeline_gates(),
            _qa_not_run(),
            [],
            critic=_critic_blocked(),
            critic_hard_mode=True,
        )
        # GATE_ORDER[3] = reconciliation_resolved (claude gate) → gates control routing
        # Hard-mode critic check only fires when gates.next_required is None
        assert verdict.human_required is False
        assert verdict.can_continue_autonomously is True
        assert "critic" not in verdict.next_action.lower()


# ── T4: Repair plan — advisory vs hard labeling ───────────────────────────────

class TestRepairPlanCriticMode:
    def _critic_diag(self) -> MagicMock:
        return _make_diag_mock(critic_status_obj=_critic_blocked(count=2))

    def test_advisory_label_in_step_description(self):
        diag = self._critic_diag()
        plan = generate_repair_plan(diag, critic_hard_mode=False)
        critic_steps = [s for s in plan.steps if "advisory" in s.description.lower()]
        assert critic_steps, "Expected at least one [advisory] critic step"

    def test_hard_label_in_step_description(self):
        diag = self._critic_diag()
        plan = generate_repair_plan(diag, critic_hard_mode=True)
        blocker_steps = [s for s in plan.steps if "blocker" in s.description.lower()]
        assert blocker_steps, "Expected at least one [BLOCKER] critic step"

    def test_advisory_plan_critic_mode_field(self):
        diag = self._critic_diag()
        plan = generate_repair_plan(diag, critic_hard_mode=False)
        assert plan.critic_mode == "advisory"

    def test_hard_plan_critic_mode_field(self):
        diag = self._critic_diag()
        plan = generate_repair_plan(diag, critic_hard_mode=True)
        assert plan.critic_mode == "hard"

    def test_critic_step_always_has_fix_path(self):
        """Every critic step must have files_to_inspect with the report path."""
        for hard_mode in (False, True):
            diag = self._critic_diag()
            plan = generate_repair_plan(diag, critic_hard_mode=hard_mode)
            critic_main_steps = [
                s for s in plan.steps
                if "critic" in s.description.lower() and not s.description.startswith(" ")
                and not s.description.startswith("  ")
            ]
            for step in critic_main_steps:
                assert "output/critic-report.json" in step.files_to_inspect, (
                    f"Missing fix path in hard_mode={hard_mode}: {step.description}"
                )
                assert step.command, f"Missing command in hard_mode={hard_mode}"

    def test_advisory_why_mentions_advancement_not_blocked(self):
        diag = self._critic_diag()
        plan = generate_repair_plan(diag, critic_hard_mode=False)
        critic_step = next(
            s for s in plan.steps
            if "advisory" in s.description.lower()
        )
        assert "not block" in critic_step.why or "advisory" in critic_step.why.lower()

    def test_hard_why_mentions_fix_path(self):
        diag = self._critic_diag()
        plan = generate_repair_plan(diag, critic_hard_mode=True)
        critic_step = next(
            s for s in plan.steps
            if "blocker" in s.description.lower()
        )
        assert "fix path" in critic_step.why.lower() or "critic-report" in critic_step.why.lower()

    def test_plan_to_dict_includes_critic_mode(self):
        diag = self._critic_diag()
        for hard_mode, expected in ((False, "advisory"), (True, "hard")):
            plan = generate_repair_plan(diag, critic_hard_mode=hard_mode)
            d = plan.to_dict()
            assert d["critic_mode"] == expected

    def test_plan_to_dict_json_serializable(self):
        diag = self._critic_diag()
        plan = generate_repair_plan(diag, critic_hard_mode=True)
        raw = json.dumps(plan.to_dict())
        parsed = json.loads(raw)
        assert parsed["critic_mode"] == "hard"


# ── T5: Backward compatibility — no existing project newly blocks ──────────────

class TestBackwardCompatibility:
    def test_default_critic_hard_mode_is_false(self):
        """generate_repair_plan and repair_project default to advisory."""
        import inspect
        from lib.brain.repair import generate_repair_plan, repair_project
        from lib.brain.diagnose import diagnose_project
        from lib.brain.sweep import sweep_projects
        from lib.brain.advance import advance_project

        for fn, param in [
            (generate_repair_plan, "critic_hard_mode"),
            (repair_project, "critic_hard_mode"),
            (diagnose_project, "critic_hard_mode"),
            (sweep_projects, "critic_hard_mode"),
            (advance_project, "critic_hard_mode"),
        ]:
            sig = inspect.signature(fn)
            assert param in sig.parameters, f"{fn.__name__} missing {param}"
            default = sig.parameters[param].default
            assert default is False, (
                f"{fn.__name__}.{param} default is {default!r}, expected False"
            )

    def test_advisory_mode_does_not_affect_healthy_without_critic_report(self):
        """No critic report + advisory mode = healthy unaffected."""
        gates = _all_gates_passed()
        artifacts = MagicMock()
        artifacts.gate_artifact_mismatches = []
        diag = Diagnosis(
            slug="proj", title="", project_dir="/tmp",
            project_json_found=True, schema_version=2, schema_ok=True,
            phase="render", status="approved",
            style="cinematic-presenter", theme="", theme_primary="",
            validation_errors=[],
            gates=gates, artifacts=artifacts,
            qa=_qa_pass(), critic=_critic_not_run(),
            autonomy=_build_autonomy_verdict(gates, _qa_pass(), []),
            critic_hard_mode=False,
            diagnosis_timestamp="2026-01-01T00:00:00Z",
        )
        assert diag.healthy is True
        assert diag.critic_advisory_signal is False

    def test_fallback_plan_no_critic_findings_unaffected_by_hard_mode(self):
        """If no critic findings, hard mode has no repair plan effect."""
        diag = _make_diag_mock()  # critic_not_run
        plan_advisory = generate_repair_plan(diag, critic_hard_mode=False)
        plan_hard = generate_repair_plan(diag, critic_hard_mode=True)
        # Both should be fallback plans with same step count
        assert len(plan_advisory.steps) == len(plan_hard.steps)


# ── T6: brain_critic_status vocabulary ───────────────────────────────────────

class TestBrainCriticStatus:
    """Diagnosis.brain_critic_status returns the 5-state vocabulary."""

    def _diag(self, critic: CriticStatus, hard_mode: bool = False) -> Diagnosis:
        gates = _all_gates_passed()
        artifacts = MagicMock()
        artifacts.gate_artifact_mismatches = []
        return Diagnosis(
            slug="proj", title="", project_dir="/tmp/proj",
            project_json_found=True, schema_version=2, schema_ok=True,
            phase="render", status="approved",
            style="cinematic-presenter", theme="", theme_primary="",
            validation_errors=[],
            gates=gates, artifacts=artifacts,
            qa=_qa_pass(), critic=critic,
            autonomy=_build_autonomy_verdict(
                gates, _qa_pass(), [], critic=critic, critic_hard_mode=hard_mode,
            ),
            critic_hard_mode=hard_mode,
            diagnosis_timestamp="2026-01-01T00:00:00Z",
        )

    def test_brain_status_not_run_when_no_report(self):
        diag = self._diag(_critic_not_run())
        assert diag.brain_critic_status == "not_run"

    def test_brain_status_advisory_pass_when_critic_passed(self):
        critic = CriticStatus(
            available=True, status="critic_passed",
            findings_count=0, highest_severity="none", top_findings=[],
        )
        diag = self._diag(critic)
        assert diag.brain_critic_status == "advisory_pass"

    def test_brain_status_advisory_warn_when_critic_warnings(self):
        diag = self._diag(_critic_warnings())
        assert diag.brain_critic_status == "advisory_warn"

    def test_brain_status_advisory_fail_when_critic_blocked_advisory(self):
        diag = self._diag(_critic_blocked(), hard_mode=False)
        assert diag.brain_critic_status == "advisory_fail"

    def test_brain_status_hard_blocked_when_critic_blocked_hard_mode(self):
        diag = self._diag(_critic_blocked(), hard_mode=True)
        assert diag.brain_critic_status == "hard_blocked"

    def test_brain_status_in_to_dict(self):
        diag = self._diag(_critic_blocked(), hard_mode=False)
        d = diag.to_dict()
        assert d["critic"]["brain_status"] == "advisory_fail"

    def test_brain_status_hard_blocked_in_to_dict(self):
        diag = self._diag(_critic_blocked(), hard_mode=True)
        d = diag.to_dict()
        assert d["critic"]["brain_status"] == "hard_blocked"

    def test_findings_in_to_dict(self):
        """to_dict includes the findings list from CriticStatus."""
        diag = self._diag(_critic_not_run())
        d = diag.to_dict()
        assert "findings" in d["critic"]
        assert isinstance(d["critic"]["findings"], list)


# ── T7: include_critic flag — per-finding repair steps ───────────────────────

class TestIncludeCriticRepairSteps:
    """include_critic=True adds structured per-finding steps with critic_id/severity."""

    def _critic_with_findings(self) -> CriticStatus:
        return CriticStatus(
            available=True,
            status="critic_blocked",
            findings_count=2,
            highest_severity="block",
            top_findings=["asset_overreuse: repeated asset"],
            findings=[
                {
                    "finding_id": "asset_overreuse:beat-03",
                    "check": "asset_overreuse",
                    "severity": "BLOCK",
                    "reason": "Same asset used 4 times",
                    "suggested_fix": "Replace 2 uses with different assets",
                },
                {
                    "finding_id": "dead_holds:beat-07",
                    "check": "dead_holds",
                    "severity": "WARN",
                    "reason": "3.2s static hold with no motion",
                    "suggested_fix": "Add zoom_moment or cut",
                },
            ],
        )

    def _diag_with_findings(self) -> MagicMock:
        d = _make_diag_mock(critic_status_obj=self._critic_with_findings())
        cs = self._critic_with_findings()
        d.critic.findings = cs.findings
        return d

    def test_include_critic_false_is_default(self):
        """include_critic defaults to False — no per-finding steps without the flag."""
        import inspect
        from lib.brain.repair import generate_repair_plan, repair_project
        for fn, param in [
            (generate_repair_plan, "include_critic"),
            (repair_project, "include_critic"),
        ]:
            sig = inspect.signature(fn)
            assert param in sig.parameters, f"{fn.__name__} missing {param}"
            assert sig.parameters[param].default is False

    def test_without_include_critic_no_per_finding_steps(self):
        """Default mode: no steps have critic_id set."""
        diag = self._diag_with_findings()
        plan = generate_repair_plan(diag, include_critic=False)
        steps_with_id = [s for s in plan.steps if s.critic_id is not None]
        assert steps_with_id == []

    def test_include_critic_adds_per_finding_steps(self):
        """include_critic=True: structured steps appear for each finding."""
        diag = self._diag_with_findings()
        plan = generate_repair_plan(diag, include_critic=True)
        steps_with_id = [s for s in plan.steps if s.critic_id is not None]
        assert len(steps_with_id) == 2

    def test_critic_id_populated_in_per_finding_steps(self):
        diag = self._diag_with_findings()
        plan = generate_repair_plan(diag, include_critic=True)
        ids = {s.critic_id for s in plan.steps if s.critic_id is not None}
        assert "asset_overreuse:beat-03" in ids
        assert "dead_holds:beat-07" in ids

    def test_severity_populated_in_per_finding_steps(self):
        diag = self._diag_with_findings()
        plan = generate_repair_plan(diag, include_critic=True)
        severities = {s.severity for s in plan.steps if s.severity is not None}
        assert "BLOCK" in severities
        assert "WARN" in severities

    def test_specialist_agent_per_finding(self):
        diag = self._diag_with_findings()
        plan = generate_repair_plan(diag, include_critic=True)
        agents = {s.specialist_agent for s in plan.steps if s.critic_id is not None}
        assert "asset-auditor" in agents   # asset_overreuse → asset-auditor
        assert "timeline-critic" in agents  # dead_holds → timeline-critic

    def test_per_finding_steps_in_to_dict(self):
        diag = self._diag_with_findings()
        plan = generate_repair_plan(diag, include_critic=True)
        raw = plan.to_dict()
        finding_steps = [s for s in raw["steps"] if s["critic_id"] is not None]
        assert len(finding_steps) == 2
        assert finding_steps[0]["critic_id"] == "asset_overreuse:beat-03"
        assert finding_steps[0]["severity"] == "BLOCK"

    def test_non_finding_steps_have_null_critic_id(self):
        """Steps not related to critic findings have critic_id=None."""
        diag = self._diag_with_findings()
        plan = generate_repair_plan(diag, include_critic=True)
        summary_step = next(
            s for s in plan.steps if "advisory" in s.description.lower()
        )
        assert summary_step.critic_id is None
        assert summary_step.severity is None
