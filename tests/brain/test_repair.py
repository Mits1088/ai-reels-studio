"""
Tests for lib.brain.repair — structured repair plan generation.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from lib.brain.repair import (
    RepairPlan,
    RepairStep,
    generate_repair_plan,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_diag(
    slug: str = "test-proj",
    healthy: bool = True,
    human_required: bool = False,
    human_required_reason: str = "",
    next_action: str = "all good",
    next_required_gate: str | None = None,
    validation_errors: list[str] | None = None,
    gate_artifact_mismatches: list[str] | None = None,
    qa_available: bool = False,
    qa_verdict: str = "not_run",
    qa_blockers: int = 0,
    qa_top_blockers: list[str] | None = None,
    critic_available: bool = False,
    critic_status: str = "critic_passed",
    critic_findings_count: int = 0,
    critic_top_findings: list[str] | None = None,
    critic_highest_severity: str = "none",
    staleness_results: list | None = None,
) -> MagicMock:
    d = MagicMock()
    d.slug = slug
    d.healthy = healthy

    d.validation_errors = validation_errors or []

    d.artifacts.gate_artifact_mismatches = gate_artifact_mismatches or []
    d.artifacts.staleness_results = staleness_results or []

    d.qa.available = qa_available
    d.qa.verdict = qa_verdict
    d.qa.blockers = qa_blockers
    d.qa.top_blockers = qa_top_blockers or []

    d.critic.available = critic_available
    d.critic.status = critic_status
    d.critic.findings_count = critic_findings_count
    d.critic.top_findings = critic_top_findings or []
    d.critic.highest_severity = critic_highest_severity

    d.autonomy.human_required = human_required
    d.autonomy.human_required_reason = human_required_reason
    d.autonomy.next_action = next_action
    d.gates.next_required = next_required_gate

    return d


def _make_staleness(
    upstream: str = "script.md",
    downstream: str = "timeline.json",
    confidence: str = "high",
    age_delta_seconds: float = 300.0,
    reason: str = "script.md changed.",
    recommended_action: str = "Re-run assembly.",
) -> MagicMock:
    r = MagicMock()
    r.upstream = upstream
    r.downstream = downstream
    r.confidence = confidence
    r.age_delta_seconds = age_delta_seconds
    r.reason = reason
    r.recommended_action = recommended_action
    return r


# ── Required spec tests ────────────────────────────────────────────────────────

class TestSpecRequired:
    """Spec-mandated test names verified here."""

    def test_repair_empty_or_low_action_when_healthy(self):
        """Healthy project → status 'healthy', no steps."""
        diag = _make_diag(healthy=True)
        plan = generate_repair_plan(diag)
        assert plan.status == "healthy"
        assert len(plan.steps) == 0

    def test_repair_steps_for_validation_errors(self):
        """Validation errors produce at least one human-actor repair step."""
        diag = _make_diag(
            healthy=False,
            validation_errors=["Field 'slug' is required"],
        )
        plan = generate_repair_plan(diag)
        assert plan.status == "blocked"
        assert len(plan.steps) >= 1
        assert plan.steps[0].actor == "human"

    def test_repair_steps_for_missing_artifacts(self):
        """Gate-artifact mismatch → repair step targeting that gate."""
        mismatch = "Gate 'assets_validated' is set but 'output/asset-report.json' is missing"
        diag = _make_diag(healthy=False, gate_artifact_mismatches=[mismatch])
        plan = generate_repair_plan(diag)
        assert plan.status == "blocked"
        assert any(s.gate_target == "assets_validated" for s in plan.steps)

    def test_repair_steps_for_stale_artifacts(self):
        """High-confidence staleness → repair step describing the stale file."""
        stale = _make_staleness(
            upstream="script.md",
            downstream="timeline.json",
            confidence="high",
        )
        diag = _make_diag(healthy=False, staleness_results=[stale])
        plan = generate_repair_plan(diag)
        assert any(
            "timeline.json" in s.description or "Regenerate" in s.description
            for s in plan.steps
        )

    def test_repair_steps_for_qa_fail(self):
        """QA FAIL → step targeting qa_passed gate."""
        diag = _make_diag(
            healthy=False,
            qa_available=True,
            qa_verdict="FAIL",
            qa_blockers=2,
        )
        plan = generate_repair_plan(diag)
        assert plan.status == "blocked"
        assert any(s.gate_target == "qa_passed" for s in plan.steps)

    def test_repair_estimates_human_touchpoints(self):
        """Human-actor steps are counted in estimated_human_touchpoints."""
        diag = _make_diag(
            healthy=False,
            validation_errors=["missing slug", "bad phase"],
        )
        plan = generate_repair_plan(diag)
        assert plan.estimated_human_touchpoints >= 1


# ── T1: Validation errors ─────────────────────────────────────────────────────

class TestValidationErrors:
    def test_single_error_produces_steps(self):
        diag = _make_diag(
            healthy=False,
            validation_errors=["Field 'slug' is required"],
        )
        plan = generate_repair_plan(diag)
        assert plan.project_slug == "test-proj"
        assert len(plan.steps) >= 1
        assert plan.steps[0].actor == "human"
        assert "project.json" in plan.steps[0].files_to_inspect

    def test_three_errors_shown_inline(self):
        errs = ["err1", "err2", "err3"]
        diag = _make_diag(healthy=False, validation_errors=errs)
        plan = generate_repair_plan(diag)
        descriptions = [s.description for s in plan.steps]
        assert any("err1" in d for d in descriptions)
        assert any("err2" in d for d in descriptions)
        assert any("err3" in d for d in descriptions)

    def test_more_than_three_truncated(self):
        errs = ["e1", "e2", "e3", "e4", "e5"]
        diag = _make_diag(healthy=False, validation_errors=errs)
        plan = generate_repair_plan(diag)
        descriptions = [s.description for s in plan.steps]
        assert any("more" in d for d in descriptions)

    def test_blocked_reason_mentions_validation(self):
        diag = _make_diag(healthy=False, validation_errors=["bad field"])
        plan = generate_repair_plan(diag)
        assert "validation" in plan.blocked_reason.lower()

    def test_human_touchpoints_at_least_one(self):
        diag = _make_diag(healthy=False, validation_errors=["bad field"])
        plan = generate_repair_plan(diag)
        assert plan.estimated_human_touchpoints >= 1

    def test_validation_error_status_is_blocked(self):
        diag = _make_diag(healthy=False, validation_errors=["missing field"])
        plan = generate_repair_plan(diag)
        assert plan.status == "blocked"
        assert plan.confidence == "high"


# ── T2: Gate–artifact mismatches ──────────────────────────────────────────────

class TestGateArtifactMismatches:
    def test_assets_validated_mismatch_adds_asset_auditor(self):
        mismatch = "Gate 'assets_validated' is set but 'output/asset-report.json' is missing"
        diag = _make_diag(healthy=False, gate_artifact_mismatches=[mismatch])
        plan = generate_repair_plan(diag)
        assert "asset-auditor" in plan.specialist_agents

    def test_preview_passed_mismatch_adds_timeline_critic(self):
        mismatch = "Gate 'preview_passed' is set but 'output/timeline.json' is missing"
        diag = _make_diag(healthy=False, gate_artifact_mismatches=[mismatch])
        plan = generate_repair_plan(diag)
        assert "timeline-critic" in plan.specialist_agents

    def test_mismatch_step_is_claude_actor(self):
        mismatch = "Gate 'script_approved' is set but 'script.md' is missing"
        diag = _make_diag(healthy=False, gate_artifact_mismatches=[mismatch])
        plan = generate_repair_plan(diag)
        mismatch_steps = [s for s in plan.steps if s.gate_target is not None]
        assert mismatch_steps
        assert all(s.actor == "claude" for s in mismatch_steps)

    def test_files_to_inspect_contains_project_json(self):
        mismatch = "Gate 'qa_passed' is set but 'output/qa-report.md' is missing"
        diag = _make_diag(healthy=False, gate_artifact_mismatches=[mismatch])
        plan = generate_repair_plan(diag)
        all_files = [f for s in plan.steps for f in s.files_to_inspect]
        assert "project.json" in all_files

    def test_blocked_reason_mentions_mismatch(self):
        mismatch = "Gate 'brief_approved' is set but 'brief.md' is missing"
        diag = _make_diag(healthy=False, gate_artifact_mismatches=[mismatch])
        plan = generate_repair_plan(diag)
        assert "mismatch" in plan.blocked_reason.lower()

    def test_mismatch_specialist_agent_on_step(self):
        mismatch = "Gate 'assets_validated' is set but 'output/asset-report.json' is missing"
        diag = _make_diag(healthy=False, gate_artifact_mismatches=[mismatch])
        plan = generate_repair_plan(diag)
        step = next(s for s in plan.steps if s.gate_target == "assets_validated")
        assert step.specialist_agent == "asset-auditor"


# ── T3: QA failures ───────────────────────────────────────────────────────────

class TestQAFailures:
    def test_qa_fail_adds_qa_runner_agent(self):
        diag = _make_diag(
            healthy=False,
            qa_available=True,
            qa_verdict="FAIL",
            qa_blockers=2,
            qa_top_blockers=["text-emphasis-domination", "missing-sfx"],
        )
        plan = generate_repair_plan(diag)
        assert "qa-runner" in plan.specialist_agents

    def test_qa_fail_step_targets_qa_passed_gate(self):
        diag = _make_diag(
            healthy=False,
            qa_available=True,
            qa_verdict="FAIL",
            qa_blockers=1,
        )
        plan = generate_repair_plan(diag)
        qa_step = next((s for s in plan.steps if s.gate_target == "qa_passed"), None)
        assert qa_step is not None

    def test_qa_blocker_lines_appended(self):
        diag = _make_diag(
            healthy=False,
            qa_available=True,
            qa_verdict="FAIL",
            qa_blockers=2,
            qa_top_blockers=["blocker-alpha"],
        )
        plan = generate_repair_plan(diag)
        descriptions = [s.description for s in plan.steps]
        assert any("blocker-alpha" in d for d in descriptions)

    def test_qa_files_to_inspect(self):
        diag = _make_diag(
            healthy=False,
            qa_available=True,
            qa_verdict="FAIL",
            qa_blockers=1,
        )
        plan = generate_repair_plan(diag)
        qa_step = next(s for s in plan.steps if s.gate_target == "qa_passed")
        assert "output/qa_report.json" in qa_step.files_to_inspect

    def test_qa_pass_does_not_produce_qa_step(self):
        diag = _make_diag(
            healthy=True,
            qa_available=True,
            qa_verdict="PASS",
        )
        plan = generate_repair_plan(diag)
        assert not any(s.gate_target == "qa_passed" for s in plan.steps)

    def test_qa_fail_specialist_agent_on_step(self):
        diag = _make_diag(
            healthy=False,
            qa_available=True,
            qa_verdict="FAIL",
            qa_blockers=1,
        )
        plan = generate_repair_plan(diag)
        qa_step = next(s for s in plan.steps if s.gate_target == "qa_passed")
        assert qa_step.specialist_agent == "qa-runner"


# ── T4: Critic blocked ────────────────────────────────────────────────────────

class TestCriticBlocked:
    def test_critic_blocked_step_added(self):
        diag = _make_diag(
            healthy=False,
            critic_available=True,
            critic_status="critic_blocked",
            critic_findings_count=3,
            critic_highest_severity="high",
        )
        plan = generate_repair_plan(diag)
        assert any("critic" in s.description.lower() for s in plan.steps)

    def test_critic_step_files_to_inspect(self):
        diag = _make_diag(
            healthy=False,
            critic_available=True,
            critic_status="critic_blocked",
            critic_findings_count=1,
        )
        plan = generate_repair_plan(diag)
        critic_step = next(
            s for s in plan.steps if "critic" in s.description.lower()
            and not s.description.startswith(" ")
        )
        assert "output/critic-report.json" in critic_step.files_to_inspect

    def test_critic_passed_does_not_produce_critic_step(self):
        diag = _make_diag(
            healthy=True,
            critic_available=True,
            critic_status="critic_passed",
            critic_findings_count=0,
        )
        plan = generate_repair_plan(diag)
        assert not any(
            "critic" in s.description.lower() and not s.description.startswith(" ")
            for s in plan.steps
        )

    def test_critic_step_has_specialist_agent(self):
        diag = _make_diag(
            healthy=False,
            critic_available=True,
            critic_status="critic_blocked",
            critic_findings_count=2,
        )
        plan = generate_repair_plan(diag)
        critic_step = next(
            s for s in plan.steps if "critic" in s.description.lower()
            and not s.description.startswith(" ")
        )
        assert critic_step.specialist_agent == "creative-critic"


# ── T5: High-confidence staleness ─────────────────────────────────────────────

class TestStaleness:
    def test_high_staleness_produces_step(self):
        stale = _make_staleness(confidence="high")
        diag = _make_diag(healthy=False, staleness_results=[stale])
        plan = generate_repair_plan(diag)
        assert any(
            "stale" in s.description.lower() or "Regenerate" in s.description
            for s in plan.steps
        )

    def test_timeline_staleness_adds_timeline_critic(self):
        stale = _make_staleness(downstream="timeline.json", confidence="high")
        diag = _make_diag(healthy=False, staleness_results=[stale])
        plan = generate_repair_plan(diag)
        assert "timeline-critic" in plan.specialist_agents

    def test_low_staleness_not_in_steps(self):
        stale = _make_staleness(confidence="low")
        diag = _make_diag(healthy=False, staleness_results=[stale])
        plan = generate_repair_plan(diag)
        assert all(
            "stale" not in s.description.lower() and "Regenerate" not in s.description
            for s in plan.steps
        )

    def test_staleness_files_to_inspect(self):
        stale = _make_staleness(upstream="script.md", downstream="timeline.json")
        diag = _make_diag(healthy=False, staleness_results=[stale])
        plan = generate_repair_plan(diag)
        all_files = [f for s in plan.steps for f in s.files_to_inspect]
        assert "script.md" in all_files
        assert "timeline.json" in all_files


# ── T6: Status and new fields ─────────────────────────────────────────────────

class TestStatusAndFields:
    def test_healthy_project_status(self):
        diag = _make_diag(healthy=True)
        plan = generate_repair_plan(diag)
        assert plan.status == "healthy"
        assert plan.confidence == "high"

    def test_human_required_status(self):
        diag = _make_diag(
            healthy=False,
            human_required=True,
            human_required_reason="Approval needed after Phase 4b-i",
        )
        plan = generate_repair_plan(diag)
        assert plan.status == "human_required"

    def test_blocked_status_from_validation_errors(self):
        diag = _make_diag(healthy=False, validation_errors=["bad"])
        plan = generate_repair_plan(diag)
        assert plan.status == "blocked"

    def test_blocked_status_from_qa_fail(self):
        diag = _make_diag(
            healthy=False,
            qa_available=True,
            qa_verdict="FAIL",
            qa_blockers=1,
        )
        plan = generate_repair_plan(diag)
        assert plan.status == "blocked"

    def test_project_slug_field(self):
        diag = _make_diag(slug="my-reel")
        plan = generate_repair_plan(diag)
        assert plan.project_slug == "my-reel"

    def test_slug_property_alias(self):
        diag = _make_diag(slug="my-reel")
        plan = generate_repair_plan(diag)
        assert plan.slug == "my-reel"

    def test_notes_populated_for_healthy(self):
        diag = _make_diag(healthy=True)
        plan = generate_repair_plan(diag)
        assert len(plan.notes) > 0

    def test_confidence_medium_for_staleness(self):
        stale = _make_staleness(confidence="high")
        diag = _make_diag(healthy=False, staleness_results=[stale])
        plan = generate_repair_plan(diag)
        assert plan.confidence == "medium"

    def test_confidence_low_for_fallback(self):
        diag = _make_diag(healthy=False)  # unhealthy but no specific cause
        plan = generate_repair_plan(diag)
        assert plan.confidence == "low"


# ── T7: Fallback ──────────────────────────────────────────────────────────────

class TestFallback:
    def test_fallback_step_when_nothing_found(self):
        """Unhealthy project with no identified cause → 1 fallback step."""
        diag = _make_diag(healthy=False)
        plan = generate_repair_plan(diag)
        assert len(plan.steps) == 1
        assert plan.steps[0].order == 1

    def test_fallback_step_is_human_actor(self):
        diag = _make_diag(healthy=False)
        plan = generate_repair_plan(diag)
        assert plan.steps[0].actor == "human"

    def test_fallback_no_specialist_agents(self):
        diag = _make_diag(healthy=False)
        plan = generate_repair_plan(diag)
        assert plan.specialist_agents == []

    def test_fallback_status_is_unknown(self):
        diag = _make_diag(healthy=False)
        plan = generate_repair_plan(diag)
        assert plan.status == "unknown"


# ── T8: Serialization ─────────────────────────────────────────────────────────

class TestSerialization:
    def test_repair_step_to_dict_keys(self):
        step = RepairStep(
            order=1,
            actor="human",
            description="Fix something",
            command="python -m lib.validate",
            gate_target=None,
            why="required",
            files_to_inspect=["project.json"],
            specialist_agent="asset-auditor",
        )
        d = step.to_dict()
        assert set(d.keys()) == {
            "order", "actor", "description", "command", "gate_target", "why",
            "files_to_inspect", "specialist_agent",
            "critic_id", "severity",
        }

    def test_repair_plan_to_dict_is_json_serializable(self):
        diag = _make_diag(healthy=False, validation_errors=["missing field"])
        plan = generate_repair_plan(diag)
        d = plan.to_dict()
        raw = json.dumps(d)
        parsed = json.loads(raw)
        assert parsed["project_slug"] == "test-proj"
        assert isinstance(parsed["steps"], list)
        assert isinstance(parsed["specialist_agents"], list)

    def test_plan_dict_has_all_top_level_keys(self):
        diag = _make_diag(healthy=False)
        plan = generate_repair_plan(diag)
        d = plan.to_dict()
        assert set(d.keys()) == {
            "project_slug", "status", "blocked_reason", "steps",
            "estimated_human_touchpoints", "confidence", "notes",
            "specialist_agents", "critic_mode",
        }

    def test_specialist_agents_preserved_in_dict(self):
        stale = _make_staleness(downstream="timeline.json", confidence="high")
        diag = _make_diag(healthy=False, staleness_results=[stale])
        plan = generate_repair_plan(diag)
        d = plan.to_dict()
        assert "timeline-critic" in d["specialist_agents"]
