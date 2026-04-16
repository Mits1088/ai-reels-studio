"""Tests for lib/critic/gate.py (Phase E3 shadow gate).

Fixture-based coverage of:
  - gate_passed / gate_blocked / gate_unavailable / gate_skipped statuses
  - asset_overreuse and visual_novelty trigger shadow refusal
  - dead_holds only gates when edit_plan is present
  - caption_competition only gates when full enrichment is present
  - claim_to_proof_latency and proof_relevance stay advisory
  - override + hard_mode interaction
  - critic_unavailable yields gate_unavailable
  - rule_summary shape and rationale content
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lib.critic.gate import (
    evaluate_gate,
    GateContext,
    GateDecision,
    GATE_PASSED,
    GATE_BLOCKED,
    GATE_UNAVAILABLE,
    GATE_SKIPPED,
    RULE_ALWAYS,
    RULE_REQUIRES_EDIT_PLAN,
    RULE_REQUIRES_ENRICHMENT,
    RULE_ADVISORY,
    CHECK_RULES,
)
from lib.critic.runner import STATUS_UNAVAILABLE, STATUS_WARNINGS, STATUS_BLOCKED


# ── Fixture builders ──────────────────────────────────────────────────────


def _finding(check: str, severity: str = "BLOCK", beat_id: str | None = "beat-01",
             confidence: float = 1.0, reason: str = "test reason") -> dict:
    return {
        "check":       check,
        "severity":    severity,
        "confidence":  confidence,
        "beat_id":     beat_id,
        "finding_id":  f"{check}:{'beat' if beat_id else 'global'}:{beat_id or 'key'}",
        "reason":      reason,
        "evidence":    {},
        "suggested_fix": "",
    }


def _report(
    findings: list[dict] | None = None,
    global_findings: list[dict] | None = None,
    critic_status: str = "critic_blocked",
    edit_plan_present: bool = False,
    enrichment_full: bool = False,
) -> dict:
    per_beat: dict[str, list[dict]] = {}
    for f in findings or []:
        bid = f.get("beat_id")
        if bid:
            per_beat.setdefault(bid, []).append(f)
    return {
        "project":       "test",
        "critic_status": critic_status,
        "verdict":       "advisory_blocked",
        "inputs_present": {
            "beat_map":      True,
            "asset_matches": True,
            "motion_plan":   True,
            "gap_ownership": True,
            "edit_plan":     edit_plan_present,
            "catalog":       True,
        },
        "enrichment_state": (
            {"full": 10, "partial": 0, "none": 0, "total": 10}
            if enrichment_full
            else {"full": 0, "partial": 0, "none": 10, "total": 10}
        ),
        "totals":         {"pre_filter": {"blockers": len([f for f in (findings or []) + (global_findings or []) if f["severity"] == "BLOCK"])}},
        "beats":          [{"beat_id": bid, "findings": fs} for bid, fs in per_beat.items()],
        "global_findings": list(global_findings or []),
    }


# ── Basic statuses ────────────────────────────────────────────────────────


class TestGateStatuses(unittest.TestCase):
    def test_gate_skipped_when_report_is_none(self):
        d = evaluate_gate(None)
        self.assertEqual(d.gate_status, GATE_SKIPPED)
        self.assertFalse(d.would_refuse_compile)
        self.assertFalse(d.actual_refuse_compile)

    def test_gate_skipped_when_report_is_empty_dict(self):
        d = evaluate_gate({})
        self.assertEqual(d.gate_status, GATE_SKIPPED)

    def test_gate_unavailable_when_critic_unavailable(self):
        d = evaluate_gate(_report(critic_status=STATUS_UNAVAILABLE))
        self.assertEqual(d.gate_status, GATE_UNAVAILABLE)
        self.assertFalse(d.would_refuse_compile)

    def test_gate_passed_when_no_blockers(self):
        d = evaluate_gate(_report(findings=[]))
        self.assertEqual(d.gate_status, GATE_PASSED)
        self.assertFalse(d.would_refuse_compile)


# ── Always-enabled checks (asset_overreuse, visual_novelty) ──────────────


class TestAlwaysEnabledChecks(unittest.TestCase):
    def test_overreuse_blocker_triggers_gate(self):
        f = _finding("asset_overreuse", beat_id=None)
        d = evaluate_gate(_report(global_findings=[f]))
        self.assertEqual(d.gate_status, GATE_BLOCKED)
        self.assertEqual(len(d.blocking_findings), 1)
        self.assertEqual(d.blocking_findings[0]["check"], "asset_overreuse")
        self.assertTrue(d.would_refuse_compile)

    def test_visual_novelty_blocker_triggers_gate(self):
        f = _finding("visual_novelty")
        d = evaluate_gate(_report(findings=[f]))
        self.assertEqual(d.gate_status, GATE_BLOCKED)
        self.assertEqual(d.blocking_findings[0]["check"], "visual_novelty")

    def test_both_always_checks_contribute_to_gate(self):
        f1 = _finding("asset_overreuse", beat_id=None)
        f2 = _finding("visual_novelty", beat_id="beat-02")
        d = evaluate_gate(_report(findings=[f2], global_findings=[f1]))
        self.assertEqual(d.gate_status, GATE_BLOCKED)
        self.assertEqual(len(d.blocking_findings), 2)

    def test_warn_severity_does_not_gate(self):
        # Only BLOCK severity contributes. WARN is noted but doesn't gate.
        f = _finding("asset_overreuse", severity="WARN")
        d = evaluate_gate(_report(findings=[f]))
        self.assertEqual(d.gate_status, GATE_PASSED)
        self.assertFalse(d.would_refuse_compile)


# ── Conditional: dead_holds requires edit_plan ────────────────────────────


class TestDeadHoldsConditional(unittest.TestCase):
    def test_dead_holds_does_not_gate_without_edit_plan(self):
        f = _finding("dead_holds")
        d = evaluate_gate(_report(findings=[f], edit_plan_present=False))
        self.assertEqual(d.gate_status, GATE_PASSED)
        self.assertEqual(len(d.blocking_findings), 0)
        self.assertEqual(len(d.conditional_findings), 1)
        self.assertEqual(d.conditional_findings[0]["check"], "dead_holds")
        self.assertFalse(d.conditional_findings[0]["precondition_met"])

    def test_dead_holds_gates_when_edit_plan_present(self):
        f = _finding("dead_holds")
        d = evaluate_gate(_report(findings=[f], edit_plan_present=True))
        self.assertEqual(d.gate_status, GATE_BLOCKED)
        self.assertEqual(len(d.blocking_findings), 1)
        self.assertEqual(d.blocking_findings[0]["check"], "dead_holds")
        self.assertTrue(d.blocking_findings[0]["precondition_met"])

    def test_dead_holds_does_not_block_when_other_always_checks_clear(self):
        # Only dead_holds (conditional, no edit_plan) → gate passes
        f = _finding("dead_holds")
        d = evaluate_gate(_report(findings=[f], edit_plan_present=False))
        self.assertFalse(d.would_refuse_compile)


# ── Conditional: caption_competition requires enrichment ─────────────────


class TestCaptionCompetitionConditional(unittest.TestCase):
    def test_caption_does_not_gate_without_full_enrichment(self):
        f = _finding("caption_competition")
        d = evaluate_gate(_report(findings=[f], enrichment_full=False))
        self.assertEqual(d.gate_status, GATE_PASSED)
        self.assertEqual(len(d.conditional_findings), 1)
        self.assertFalse(d.conditional_findings[0]["precondition_met"])

    def test_caption_gates_with_full_enrichment(self):
        f = _finding("caption_competition")
        d = evaluate_gate(_report(findings=[f], enrichment_full=True))
        self.assertEqual(d.gate_status, GATE_BLOCKED)
        self.assertEqual(len(d.blocking_findings), 1)
        self.assertEqual(d.blocking_findings[0]["check"], "caption_competition")


# ── Advisory checks never gate ───────────────────────────────────────────


class TestAdvisoryChecks(unittest.TestCase):
    def test_claim_to_proof_latency_never_gates(self):
        f = _finding("claim_to_proof_latency")
        d = evaluate_gate(_report(findings=[f], edit_plan_present=True, enrichment_full=True))
        self.assertEqual(d.gate_status, GATE_PASSED)
        self.assertEqual(len(d.blocking_findings), 0)
        self.assertEqual(len(d.advisory_findings), 1)
        self.assertEqual(d.advisory_findings[0]["check"], "claim_to_proof_latency")

    def test_proof_relevance_never_gates(self):
        f = _finding("proof_relevance")
        d = evaluate_gate(_report(findings=[f], edit_plan_present=True, enrichment_full=True))
        self.assertEqual(d.gate_status, GATE_PASSED)
        self.assertEqual(len(d.advisory_findings), 1)
        self.assertEqual(d.advisory_findings[0]["check"], "proof_relevance")

    def test_advisory_alongside_blocker_does_not_double_count(self):
        blocker = _finding("asset_overreuse", beat_id=None)
        advisory = _finding("claim_to_proof_latency")
        d = evaluate_gate(_report(findings=[advisory], global_findings=[blocker]))
        self.assertEqual(d.gate_status, GATE_BLOCKED)
        self.assertEqual(len(d.blocking_findings), 1)  # only the overreuse blocker
        self.assertEqual(len(d.advisory_findings), 1)  # the advisory is noted separately


# ── Shadow mode vs hard mode ─────────────────────────────────────────────


class TestShadowVsHardMode(unittest.TestCase):
    def test_shadow_mode_never_actually_refuses(self):
        f = _finding("asset_overreuse", beat_id=None)
        d = evaluate_gate(_report(global_findings=[f]), hard_gate_enabled=False)
        self.assertTrue(d.would_refuse_compile)  # gate WOULD block
        self.assertFalse(d.actual_refuse_compile)  # but shadow mode doesn't refuse
        self.assertFalse(d.hard_gate_enabled)

    def test_hard_mode_refuses_on_blockers(self):
        f = _finding("asset_overreuse", beat_id=None)
        d = evaluate_gate(_report(global_findings=[f]), hard_gate_enabled=True)
        self.assertTrue(d.would_refuse_compile)
        self.assertTrue(d.actual_refuse_compile)

    def test_hard_mode_with_override_does_not_refuse(self):
        f = _finding("asset_overreuse", beat_id=None)
        d = evaluate_gate(
            _report(global_findings=[f]),
            hard_gate_enabled=True,
            override_used=True,
        )
        self.assertTrue(d.would_refuse_compile)
        self.assertFalse(d.actual_refuse_compile)
        self.assertTrue(d.override_used)

    def test_override_in_shadow_mode_is_noop(self):
        f = _finding("asset_overreuse", beat_id=None)
        d = evaluate_gate(
            _report(global_findings=[f]),
            hard_gate_enabled=False,
            override_used=True,
        )
        # Shadow mode already doesn't refuse; override makes no difference
        self.assertFalse(d.actual_refuse_compile)

    def test_hard_mode_on_gate_passed_does_not_refuse(self):
        d = evaluate_gate(_report(findings=[]), hard_gate_enabled=True)
        self.assertEqual(d.gate_status, GATE_PASSED)
        self.assertFalse(d.actual_refuse_compile)


# ── Context derivation from report ───────────────────────────────────────


class TestContextDerivation(unittest.TestCase):
    def test_edit_plan_present_derived_from_inputs(self):
        f = _finding("dead_holds")
        r = _report(findings=[f], edit_plan_present=True)
        d = evaluate_gate(r)  # no explicit context
        self.assertEqual(d.gate_status, GATE_BLOCKED)

    def test_enrichment_full_derived_from_state(self):
        f = _finding("caption_competition")
        r = _report(findings=[f], enrichment_full=True)
        d = evaluate_gate(r)
        self.assertEqual(d.gate_status, GATE_BLOCKED)

    def test_explicit_context_overrides_derivation(self):
        f = _finding("dead_holds")
        r = _report(findings=[f], edit_plan_present=False)  # report says no edit_plan
        ctx = GateContext(edit_plan_present=True)  # but explicit context overrides
        d = evaluate_gate(r, context=ctx)
        self.assertEqual(d.gate_status, GATE_BLOCKED)


# ── Rule summary + rationale ─────────────────────────────────────────────


class TestRuleSummaryAndRationale(unittest.TestCase):
    def test_rule_summary_lists_all_fired_checks(self):
        f1 = _finding("asset_overreuse", beat_id=None)
        f2 = _finding("dead_holds")
        d = evaluate_gate(_report(findings=[f2], global_findings=[f1]))
        self.assertIn("asset_overreuse", d.rule_summary)
        self.assertIn("dead_holds", d.rule_summary)
        self.assertEqual(d.rule_summary["asset_overreuse"]["rule"], RULE_ALWAYS)
        self.assertEqual(d.rule_summary["dead_holds"]["rule"], RULE_REQUIRES_EDIT_PLAN)
        self.assertEqual(d.rule_summary["asset_overreuse"]["blockers"], 1)
        self.assertTrue(d.rule_summary["asset_overreuse"]["triggered"])
        self.assertFalse(d.rule_summary["dead_holds"]["triggered"])  # no edit_plan

    def test_rationale_mentions_shadow_mode(self):
        f = _finding("asset_overreuse", beat_id=None)
        d = evaluate_gate(_report(global_findings=[f]), hard_gate_enabled=False)
        self.assertIn("SHADOW", d.rationale.upper())

    def test_rationale_mentions_hard_mode_on_refuse(self):
        f = _finding("asset_overreuse", beat_id=None)
        d = evaluate_gate(_report(global_findings=[f]), hard_gate_enabled=True)
        self.assertIn("REFUSE", d.rationale.upper())

    def test_rationale_mentions_override(self):
        f = _finding("asset_overreuse", beat_id=None)
        d = evaluate_gate(
            _report(global_findings=[f]),
            hard_gate_enabled=True,
            override_used=True,
        )
        self.assertIn("override", d.rationale.lower())


# ── Serialization ────────────────────────────────────────────────────────


class TestGateDecisionSerialization(unittest.TestCase):
    def test_to_dict_has_required_keys(self):
        f = _finding("asset_overreuse", beat_id=None)
        d = evaluate_gate(_report(global_findings=[f]))
        out = d.to_dict(project="test")
        for key in (
            "schema_version", "gate_version", "mode", "gate_status",
            "would_refuse_compile", "hard_gate_enabled", "override_used",
            "actual_refuse_compile", "blocking_findings", "conditional_findings",
            "advisory_findings", "rule_summary", "rationale", "project",
        ):
            self.assertIn(key, out)

    def test_to_dict_mode_reflects_hard_gate(self):
        out = evaluate_gate({}, hard_gate_enabled=True).to_dict()
        self.assertEqual(out["mode"], "hard")
        out = evaluate_gate({}, hard_gate_enabled=False).to_dict()
        self.assertEqual(out["mode"], "shadow")

    def test_check_rules_covers_all_6_checks(self):
        # Drift detector: every known check must have a rule assigned
        known = {
            "asset_overreuse", "visual_novelty", "dead_holds",
            "caption_competition", "claim_to_proof_latency", "proof_relevance",
        }
        self.assertEqual(set(CHECK_RULES.keys()), known)


if __name__ == "__main__":
    unittest.main(verbosity=2)
