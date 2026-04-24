"""
Tests for Phase 5 — critic hard-mode gate enforcement.

Validates the full diagnose_project() path end-to-end using real
critic-report.json fixtures on tmp_path. Never touches production files.

Seven required tests:
  1. test_default_advisory_mode_does_not_block
  2. test_hard_mode_blocks_allowlisted_check
  3. test_hard_mode_does_not_block_non_allowlisted_check
  4. test_waived_check_does_not_block
  5. test_repair_includes_hard_critic_steps
  6. test_critic_hard_blocked_property_in_to_dict
  7. test_existing_advance_behavior_unchanged
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lib.brain.diagnose import diagnose_project, CRITIC_HARD_ALLOWLIST
from lib.brain.repair import generate_repair_plan, repair_project


# ── Fixture helpers ────────────────────────────────────────────────────────────

def _minimal_project_json(tmp_path: Path, slug: str = "test-proj") -> Path:
    """Write a minimal valid project.json with gates that have no artifact requirements.

    Uses only theme_set + assets_validated so _build_artifact_inventory never
    produces gate_artifact_mismatches regardless of what files are on disk.
    This keeps the healthy/unhealthy signal driven entirely by critic state.
    """
    from lib.constants import CURRENT_SCHEMA_VERSION
    pj = {
        "slug": slug,
        "title": "Test Project",
        "schema_version": CURRENT_SCHEMA_VERSION,
        "phase": "render",
        "status": "approved",
        "project_type": "reel",
        "style": "cinematic-presenter",
        "theme": "Tech Neutral",
        "theme_primary": "#000000",
        "theme_secondary": "#FFFFFF",
        "gates_passed": ["theme_set", "assets_validated"],  # no artifact requirements
        "created": "2026-01-01T00:00:00Z",
        "updated": "2026-01-01T00:00:00Z",
    }
    path = tmp_path / "project.json"
    path.write_text(json.dumps(pj), encoding="utf-8")
    return path


def _write_critic_report(
    project_dir: Path,
    findings_by_beat: list[dict] | None = None,
    global_findings: list[dict] | None = None,
    critic_status: str = "critic_blocked",
) -> Path:
    """Write output/critic-report.json with given findings."""
    output_dir = project_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    beats = []
    if findings_by_beat:
        beats = [{"beat_id": "beat-01", "findings": findings_by_beat}]

    report = {
        "critic_status": critic_status,
        "advisory": True,
        "critic_version": "lib.critic@1.1.0-advisory",
        "beats": beats,
        "global_findings": global_findings or [],
    }
    path = output_dir / "critic-report.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


def _block_finding(check: str, reason: str = "test finding") -> dict:
    return {
        "finding_id": f"{check}:beat-01",
        "check": check,
        "severity": "BLOCK",
        "reason": reason,
        "suggested_fix": f"Fix {check}",
    }


def _write_waiver(project_dir: Path, critic_id: str, slug: str = "test-proj") -> Path:
    """Write critic_waivers.json with a single valid waiver for the given check."""
    waivers = [
        {
            "waiver_id": f"w-{critic_id}-001",
            "critic_id": critic_id,
            "project_slug": slug,
            "reason": "Accepted for this render — documented edge case.",
            "reviewer": "Mits",
            "date": "2026-01-01",
            "scope": "this_render",
        }
    ]
    path = project_dir / "critic_waivers.json"
    path.write_text(json.dumps(waivers), encoding="utf-8")
    return path


# ── Test 1 ─────────────────────────────────────────────────────────────────────

class TestDefaultAdvisoryModeDoesNotBlock:
    """Advisory mode (default) never hard-blocks regardless of critic findings."""

    def test_default_advisory_mode_does_not_block(self, tmp_path):
        """critic_hard_mode=False: allowlisted BLOCK finding → healthy=True, hard_blocked=False."""
        _minimal_project_json(tmp_path)
        _write_critic_report(
            tmp_path,
            findings_by_beat=[_block_finding("asset_overreuse")],
        )

        diag = diagnose_project(tmp_path, critic_hard_mode=False)

        assert diag.critic.available is True
        assert diag.critic.status == "critic_blocked"
        # CriticStatus.hard_blocked reflects the report content (allowlisted BLOCK found).
        # The mode gate lives in Diagnosis.critic_hard_blocked.
        assert diag.critic.hard_blocked is True, (
            "CriticStatus.hard_blocked reports finding presence regardless of mode"
        )
        assert diag.critic_hard_blocked is False, (
            "Diagnosis.critic_hard_blocked must be False when critic_hard_mode=False"
        )
        assert diag.healthy is True, "Advisory mode must not affect healthy"
        assert diag.brain_critic_status == "advisory_fail"


# ── Test 2 ─────────────────────────────────────────────────────────────────────

class TestHardModeBlocksAllowlistedCheck:
    """Hard mode + allowlisted BLOCK finding → hard_blocked, healthy=False."""

    def test_hard_mode_blocks_allowlisted_check(self, tmp_path):
        """asset_overreuse BLOCK in hard mode triggers hard_blocked state."""
        _minimal_project_json(tmp_path)
        _write_critic_report(
            tmp_path,
            findings_by_beat=[_block_finding("asset_overreuse")],
        )

        diag = diagnose_project(tmp_path, critic_hard_mode=True)

        assert diag.critic.hard_blocked is True
        assert diag.critic_hard_blocked is True
        assert diag.healthy is False
        assert diag.brain_critic_status == "hard_blocked"
        assert len(diag.critic.hard_blocked_findings) == 1
        assert diag.critic.hard_blocked_findings[0]["check"] == "asset_overreuse"

    def test_visual_novelty_also_blocks_in_hard_mode(self, tmp_path):
        """visual_novelty is also in the allowlist — should trigger hard_blocked."""
        _minimal_project_json(tmp_path)
        _write_critic_report(
            tmp_path,
            findings_by_beat=[_block_finding("visual_novelty")],
        )

        diag = diagnose_project(tmp_path, critic_hard_mode=True)

        assert diag.critic.hard_blocked is True
        assert diag.brain_critic_status == "hard_blocked"


# ── Test 3 ─────────────────────────────────────────────────────────────────────

class TestHardModeDoesNotBlockNonAllowlistedCheck:
    """Hard mode with BLOCK findings outside the allowlist → healthy stays True."""

    def test_hard_mode_does_not_block_non_allowlisted_check(self, tmp_path):
        """dead_holds is not in CRITIC_HARD_ALLOWLIST — must not hard-block."""
        assert "dead_holds" not in CRITIC_HARD_ALLOWLIST, (
            "Test precondition: dead_holds must not be in the allowlist"
        )
        _minimal_project_json(tmp_path)
        _write_critic_report(
            tmp_path,
            findings_by_beat=[_block_finding("dead_holds")],
        )

        diag = diagnose_project(tmp_path, critic_hard_mode=True)

        assert diag.critic.hard_blocked is False
        assert diag.healthy is True
        assert diag.brain_critic_status == "advisory_fail"
        assert diag.critic_hard_blocked is False


# ── Test 4 ─────────────────────────────────────────────────────────────────────

class TestWaivedCheckDoesNotBlock:
    """A waiver matching an allowlisted BLOCK finding removes the hard-block."""

    def test_waived_check_does_not_block(self, tmp_path):
        """asset_overreuse BLOCK + matching waiver → hard_blocked=False."""
        _minimal_project_json(tmp_path, slug="test-proj")
        _write_critic_report(
            tmp_path,
            findings_by_beat=[_block_finding("asset_overreuse")],
        )
        _write_waiver(tmp_path, critic_id="asset_overreuse", slug="test-proj")

        diag = diagnose_project(tmp_path, critic_hard_mode=True)

        assert diag.critic.hard_blocked is False, (
            "Waiver should remove the allowlisted finding from the block set"
        )
        assert diag.healthy is True
        assert diag.brain_critic_status == "advisory_fail"
        assert len(diag.critic.applied_waivers) == 1
        assert diag.critic.applied_waivers[0]["critic_id"] == "asset_overreuse"

    def test_waiver_for_other_check_does_not_remove_block(self, tmp_path):
        """Waiver for visual_novelty does not waive asset_overreuse."""
        _minimal_project_json(tmp_path)
        _write_critic_report(
            tmp_path,
            findings_by_beat=[_block_finding("asset_overreuse")],
        )
        _write_waiver(tmp_path, critic_id="visual_novelty")  # wrong check

        diag = diagnose_project(tmp_path, critic_hard_mode=True)

        assert diag.critic.hard_blocked is True, (
            "Waiver for visual_novelty must not waive asset_overreuse"
        )


# ── Test 5 ─────────────────────────────────────────────────────────────────────

class TestRepairIncludesHardCriticSteps:
    """Repair plan labels hard-blocked steps as [BLOCKER], advisory as [advisory]."""

    def test_repair_includes_hard_critic_steps(self, tmp_path):
        """Hard mode + allowlisted BLOCK → repair step carries [BLOCKER] label."""
        _minimal_project_json(tmp_path)
        _write_critic_report(
            tmp_path,
            findings_by_beat=[_block_finding("asset_overreuse")],
        )

        plan = repair_project(tmp_path, critic_hard_mode=True)

        blocker_steps = [s for s in plan.steps if "blocker" in s.description.lower()]
        assert blocker_steps, "Expected at least one [BLOCKER] critic repair step"
        assert plan.critic_mode == "hard"

    def test_repair_advisory_label_when_non_allowlisted_in_hard_mode(self, tmp_path):
        """Non-allowlisted BLOCK in hard mode → repair step is [advisory], not [BLOCKER]."""
        _minimal_project_json(tmp_path)
        _write_critic_report(
            tmp_path,
            findings_by_beat=[_block_finding("dead_holds")],
        )

        plan = repair_project(tmp_path, critic_hard_mode=True)

        blocker_steps = [s for s in plan.steps if "blocker" in s.description.lower()]
        assert not blocker_steps, (
            "Non-allowlisted check must not produce [BLOCKER] label even in hard mode"
        )
        advisory_steps = [s for s in plan.steps if "advisory" in s.description.lower()]
        assert advisory_steps, "Expected [advisory] label for non-allowlisted check"


# ── Test 6 ─────────────────────────────────────────────────────────────────────

class TestCriticHardBlockedPropertyInToDict:
    """to_dict() exposes hard_blocked and applied_waivers in the critic section."""

    def test_critic_hard_blocked_property_in_to_dict(self, tmp_path):
        """hard_blocked and applied_waivers appear in to_dict() output."""
        _minimal_project_json(tmp_path)
        _write_critic_report(
            tmp_path,
            findings_by_beat=[_block_finding("asset_overreuse")],
        )

        diag = diagnose_project(tmp_path, critic_hard_mode=True)
        d = diag.to_dict()

        assert "hard_blocked" in d["critic"], "to_dict() must include hard_blocked"
        assert d["critic"]["hard_blocked"] is True
        assert "applied_waivers" in d["critic"], "to_dict() must include applied_waivers"
        assert isinstance(d["critic"]["applied_waivers"], list)
        assert "critic_hard_blocked" in d
        assert d["critic_hard_blocked"] is True

    def test_to_dict_hard_blocked_false_in_advisory_mode(self, tmp_path):
        """Advisory mode: critic_hard_blocked is False at the top level.
        critic['hard_blocked'] still reflects the finding (True) — the mode gate
        lives in the top-level 'critic_hard_blocked' key."""
        _minimal_project_json(tmp_path)
        _write_critic_report(
            tmp_path,
            findings_by_beat=[_block_finding("asset_overreuse")],
        )

        diag = diagnose_project(tmp_path, critic_hard_mode=False)
        d = diag.to_dict()

        # critic["hard_blocked"] = True (finding is present, mode-agnostic)
        assert d["critic"]["hard_blocked"] is True
        # critic_hard_blocked = False (mode gate is off)
        assert d["critic_hard_blocked"] is False


# ── Test 7 ─────────────────────────────────────────────────────────────────────

class TestExistingAdvanceBehaviorUnchanged:
    """Default behavior: non-allowlisted checks in hard mode must not newly block."""

    def test_existing_advance_behavior_unchanged(self, tmp_path):
        """Projects with only non-allowlisted BLOCK findings are unaffected by hard mode."""
        _minimal_project_json(tmp_path)
        _write_critic_report(
            tmp_path,
            findings_by_beat=[
                _block_finding("dead_holds"),
                _block_finding("claim_to_proof_latency"),
            ],
        )

        # Advisory mode (default) — must not block
        diag_advisory = diagnose_project(tmp_path, critic_hard_mode=False)
        assert diag_advisory.healthy is True
        assert diag_advisory.critic.hard_blocked is False

        # Hard mode — still must not block (non-allowlisted checks)
        diag_hard = diagnose_project(tmp_path, critic_hard_mode=True)
        assert diag_hard.healthy is True, (
            "Non-allowlisted BLOCK findings must never trigger hard-mode blocking"
        )
        assert diag_hard.critic.hard_blocked is False

    def test_allowlist_contains_only_evidence_backed_checks(self):
        """The allowlist only contains checks with real evidence."""
        assert "asset_overreuse" in CRITIC_HARD_ALLOWLIST
        assert "visual_novelty" in CRITIC_HARD_ALLOWLIST
        # Checks that were explicitly excluded for insufficient evidence
        assert "dead_holds" not in CRITIC_HARD_ALLOWLIST
        assert "claim_to_proof_latency" not in CRITIC_HARD_ALLOWLIST
