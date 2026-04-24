"""
Tests for lib.brain.memory_apply — safe, human-approved memory promotion.

All tests use tmp_path fixtures. Production memory/creative-feedback.json
is NEVER touched by this test suite.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lib.brain.memory_apply import (
    KNOWN_TARGETS,
    VALID_PROPOSAL_TYPES,
    ApplyResult,
    apply_proposal,
    validate_proposal,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

MINIMAL_MEMORY: dict = {
    "_meta": {"version": "1.0"},
    "hard_rules": ["No OverlayKeyword more than 3 times per reel."],
    "soft_preferences": ["Prefer image-dominant beats for proof sections."],
    "likes": [],
    "dislikes": [],
    "motion_notes": [],
    "hook_notes": [],
    "caption_notes": [],
    "components_to_use_more": [],
    "components_to_use_less": [],
    "reference_reels": [],
    "feedback_log": [],
}


def _write_memory(tmp_path: Path, content: dict | None = None) -> Path:
    p = tmp_path / "creative-feedback.json"
    p.write_text(json.dumps(content or MINIMAL_MEMORY, indent=2, ensure_ascii=False), encoding="utf-8")
    return p


def _write_proposal(tmp_path: Path, proposal: dict) -> Path:
    p = tmp_path / "proposal.json"
    p.write_text(json.dumps(proposal, ensure_ascii=False), encoding="utf-8")
    return p


def _valid_add_rule_proposal(**overrides) -> dict:
    base = {
        "proposal_id": "test-001",
        "created_at": "2026-04-24T00:00:00Z",
        "source_project": "test-project",
        "proposal_type": "add_rule",
        "target_path": "hard_rules",
        "change_summary": "Add rule about AnnotationCircle usage.",
        "evidence_refs": ["projects/test-project/output/review-feedback.md"],
        "confidence": "high",
        "proposed_change": {"value": "Use AnnotationCircle when narrator names a specific element."},
        "requires_human_approval": True,
    }
    base.update(overrides)
    return base


def _valid_feedback_log_proposal(**overrides) -> dict:
    base = {
        "proposal_id": "test-002",
        "created_at": "2026-04-24T00:00:00Z",
        "source_project": "test-project",
        "proposal_type": "append_feedback_log",
        "target_path": "feedback_log",
        "change_summary": "Log a review round observation.",
        "evidence_refs": [],
        "confidence": "medium",
        "proposed_change": {
            "entry": {
                "date": "2026-04-24",
                "note": "AnnotationCircle worked well on benchmark screenshot.",
                "source_project": "test-project",
            }
        },
        "requires_human_approval": True,
    }
    base.update(overrides)
    return base


# ── Validation ─────────────────────────────────────────────────────────────────

class TestValidateProposal:
    def test_valid_add_rule_passes(self):
        errs = validate_proposal(_valid_add_rule_proposal())
        assert errs == []

    def test_valid_feedback_log_passes(self):
        errs = validate_proposal(_valid_feedback_log_proposal())
        assert errs == []

    def test_missing_required_field_reported(self):
        p = _valid_add_rule_proposal()
        del p["proposal_id"]
        errs = validate_proposal(p)
        assert any("proposal_id" in e for e in errs)

    def test_requires_human_approval_must_be_true(self):
        p = _valid_add_rule_proposal(requires_human_approval=False)
        errs = validate_proposal(p)
        assert any("requires_human_approval" in e for e in errs)

    def test_requires_human_approval_string_rejected(self):
        p = _valid_add_rule_proposal(requires_human_approval="true")
        errs = validate_proposal(p)
        assert any("requires_human_approval" in e for e in errs)

    def test_unknown_proposal_type_rejected(self):
        p = _valid_add_rule_proposal(proposal_type="invent_new_rule")
        errs = validate_proposal(p)
        assert any("proposal_type" in e or "Unknown" in e for e in errs)

    def test_unknown_target_path_rejected(self):
        p = _valid_add_rule_proposal(target_path="arbitrary_new_key")
        errs = validate_proposal(p)
        assert any("target_path" in e or "Unknown" in e or "arbitrary_new_key" in e for e in errs)

    def test_meta_target_rejected(self):
        """_meta must never be a valid target."""
        p = _valid_add_rule_proposal(target_path="_meta")
        errs = validate_proposal(p)
        assert errs  # any error — _meta is not in KNOWN_TARGETS

    def test_evidence_refs_required_for_add_rule(self):
        p = _valid_add_rule_proposal(evidence_refs=[])
        errs = validate_proposal(p)
        assert any("evidence" in e.lower() for e in errs)

    def test_evidence_refs_required_for_update_rule(self):
        p = _valid_add_rule_proposal(
            proposal_type="update_rule",
            proposed_change={
                "old_value": "No OverlayKeyword more than 3 times per reel.",
                "new_value": "No OverlayKeyword more than 4 times per reel.",
            },
            evidence_refs=[],
        )
        errs = validate_proposal(p)
        assert any("evidence" in e.lower() for e in errs)

    def test_evidence_refs_not_required_for_feedback_log(self):
        p = _valid_feedback_log_proposal(evidence_refs=[])
        errs = validate_proposal(p)
        assert errs == []

    def test_invalid_confidence_rejected(self):
        p = _valid_add_rule_proposal(confidence="very_high")
        errs = validate_proposal(p)
        assert any("confidence" in e for e in errs)

    def test_proposed_change_must_be_dict(self):
        p = _valid_add_rule_proposal(proposed_change="just a string")
        errs = validate_proposal(p)
        assert any("proposed_change" in e for e in errs)

    def test_add_rule_change_needs_value_key(self):
        p = _valid_add_rule_proposal(proposed_change={"wrong_key": "something"})
        errs = validate_proposal(p)
        assert any("value" in e for e in errs)

    def test_update_rule_needs_old_and_new_value(self):
        p = _valid_add_rule_proposal(
            proposal_type="update_rule",
            evidence_refs=["projects/test/review.md"],
            proposed_change={"new_value": "only new"},
        )
        errs = validate_proposal(p)
        assert any("old_value" in e for e in errs)

    def test_append_feedback_log_needs_entry_key(self):
        p = _valid_feedback_log_proposal(proposed_change={"wrong": "shape"})
        errs = validate_proposal(p)
        assert any("entry" in e for e in errs)

    def test_non_dict_proposal_rejected(self):
        errs = validate_proposal(["not", "a", "dict"])
        assert errs


# ── Dry-run ────────────────────────────────────────────────────────────────────

class TestDryRun:
    def test_dry_run_does_not_modify_memory(self, tmp_path):
        mem = _write_memory(tmp_path)
        prop = _write_proposal(tmp_path, _valid_add_rule_proposal())
        before = mem.read_bytes()

        result = apply_proposal(prop, mem, confirm=False)

        assert result.success
        assert result.dry_run
        assert mem.read_bytes() == before, "Memory file must not be modified in dry-run"

    def test_dry_run_returns_diff_lines(self, tmp_path):
        mem = _write_memory(tmp_path)
        prop = _write_proposal(tmp_path, _valid_add_rule_proposal())

        result = apply_proposal(prop, mem, confirm=False)

        assert result.success
        assert result.dry_run
        assert len(result.diff_lines) >= 1
        assert any("hard_rules" in line for line in result.diff_lines)

    def test_dry_run_no_backup_created(self, tmp_path):
        mem = _write_memory(tmp_path)
        prop = _write_proposal(tmp_path, _valid_add_rule_proposal())

        apply_proposal(prop, mem, confirm=False)

        bak_files = list(tmp_path.glob("*.bak.*"))
        assert bak_files == [], "Dry-run must not create backup files"

    def test_dry_run_render_mentions_no_changes_written(self, tmp_path):
        mem = _write_memory(tmp_path)
        prop = _write_proposal(tmp_path, _valid_add_rule_proposal())
        result = apply_proposal(prop, mem, confirm=False)
        rendered = result.render()
        assert "No changes were written" in rendered


# ── Confirm mode ───────────────────────────────────────────────────────────────

class TestConfirmMode:
    def test_confirm_writes_memory(self, tmp_path):
        mem = _write_memory(tmp_path)
        new_rule = "Use AnnotationCircle when narrator names a specific element."
        prop = _write_proposal(tmp_path, _valid_add_rule_proposal(
            proposed_change={"value": new_rule}
        ))

        result = apply_proposal(prop, mem, confirm=True)

        assert result.success
        assert not result.dry_run
        updated = json.loads(mem.read_text(encoding="utf-8"))
        assert new_rule in updated["hard_rules"]

    def test_confirm_creates_backup_before_write(self, tmp_path):
        mem = _write_memory(tmp_path)
        prop = _write_proposal(tmp_path, _valid_add_rule_proposal())

        result = apply_proposal(prop, mem, confirm=True)

        assert result.backup_path is not None
        assert result.backup_path.exists()

    def test_backup_contains_original_content(self, tmp_path):
        mem = _write_memory(tmp_path)
        original_bytes = mem.read_bytes()
        prop = _write_proposal(tmp_path, _valid_add_rule_proposal())

        result = apply_proposal(prop, mem, confirm=True)

        assert result.backup_path.read_bytes() == original_bytes

    def test_backup_path_is_adjacent_to_memory(self, tmp_path):
        mem = _write_memory(tmp_path)
        prop = _write_proposal(tmp_path, _valid_add_rule_proposal())
        result = apply_proposal(prop, mem, confirm=True)
        assert result.backup_path.parent == mem.parent

    def test_written_memory_is_valid_json(self, tmp_path):
        mem = _write_memory(tmp_path)
        prop = _write_proposal(tmp_path, _valid_add_rule_proposal())
        apply_proposal(prop, mem, confirm=True)
        content = mem.read_text(encoding="utf-8")
        parsed = json.loads(content)  # must not raise
        assert isinstance(parsed, dict)

    def test_written_memory_ends_with_newline(self, tmp_path):
        mem = _write_memory(tmp_path)
        prop = _write_proposal(tmp_path, _valid_add_rule_proposal())
        apply_proposal(prop, mem, confirm=True)
        raw = mem.read_bytes()
        assert raw.endswith(b"\n"), "Written memory file must end with a newline"

    def test_meta_key_preserved_after_write(self, tmp_path):
        mem = _write_memory(tmp_path)
        original_meta = MINIMAL_MEMORY["_meta"].copy()
        prop = _write_proposal(tmp_path, _valid_add_rule_proposal())
        apply_proposal(prop, mem, confirm=True)
        updated = json.loads(mem.read_text(encoding="utf-8"))
        assert updated["_meta"] == original_meta

    def test_confirm_returns_backup_path_in_result(self, tmp_path):
        mem = _write_memory(tmp_path)
        prop = _write_proposal(tmp_path, _valid_add_rule_proposal())
        result = apply_proposal(prop, mem, confirm=True)
        assert result.backup_path is not None

    def test_confirm_returns_diff_lines(self, tmp_path):
        mem = _write_memory(tmp_path)
        prop = _write_proposal(tmp_path, _valid_add_rule_proposal())
        result = apply_proposal(prop, mem, confirm=True)
        assert len(result.diff_lines) >= 1


# ── Proposal types ─────────────────────────────────────────────────────────────

class TestProposalTypes:
    def test_add_like(self, tmp_path):
        mem = _write_memory(tmp_path)
        prop = _write_proposal(tmp_path, {
            "proposal_id": "t-003",
            "created_at": "2026-04-24T00:00:00Z",
            "source_project": "test",
            "proposal_type": "add_like",
            "target_path": "likes",
            "change_summary": "Like: hook with bouncing logo.",
            "evidence_refs": [],
            "confidence": "medium",
            "proposed_change": {"value": "Hooks with bouncing product logo from frame 0."},
            "requires_human_approval": True,
        })
        result = apply_proposal(prop, mem, confirm=True)
        assert result.success
        updated = json.loads(mem.read_text())
        assert "Hooks with bouncing product logo from frame 0." in updated["likes"]

    def test_add_dislike(self, tmp_path):
        mem = _write_memory(tmp_path)
        prop = _write_proposal(tmp_path, {
            "proposal_id": "t-004",
            "created_at": "2026-04-24T00:00:00Z",
            "source_project": "test",
            "proposal_type": "add_dislike",
            "target_path": "dislikes",
            "change_summary": "Dislike: static hook with no motion.",
            "evidence_refs": [],
            "confidence": "medium",
            "proposed_change": {"value": "Static hook with no continuous motion element."},
            "requires_human_approval": True,
        })
        result = apply_proposal(prop, mem, confirm=True)
        assert result.success
        updated = json.loads(mem.read_text())
        assert "Static hook with no continuous motion element." in updated["dislikes"]

    def test_update_rule_replaces_existing(self, tmp_path):
        mem = _write_memory(tmp_path)
        old_rule = "No OverlayKeyword more than 3 times per reel."
        new_rule = "No OverlayKeyword more than 4 times per reel."
        prop = _write_proposal(tmp_path, {
            "proposal_id": "t-005",
            "created_at": "2026-04-24T00:00:00Z",
            "source_project": "test",
            "proposal_type": "update_rule",
            "target_path": "hard_rules",
            "change_summary": "Relax OverlayKeyword limit.",
            "evidence_refs": ["projects/test/review.md"],
            "confidence": "high",
            "proposed_change": {"old_value": old_rule, "new_value": new_rule},
            "requires_human_approval": True,
        })
        result = apply_proposal(prop, mem, confirm=True)
        assert result.success
        updated = json.loads(mem.read_text())
        assert new_rule in updated["hard_rules"]
        assert old_rule not in updated["hard_rules"]

    def test_update_rule_old_value_not_found_fails(self, tmp_path):
        mem = _write_memory(tmp_path)
        prop = _write_proposal(tmp_path, {
            "proposal_id": "t-006",
            "created_at": "2026-04-24T00:00:00Z",
            "source_project": "test",
            "proposal_type": "update_rule",
            "target_path": "hard_rules",
            "change_summary": "Update a rule that does not exist.",
            "evidence_refs": ["projects/test/review.md"],
            "confidence": "high",
            "proposed_change": {
                "old_value": "This rule does not exist in memory.",
                "new_value": "Replacement rule.",
            },
            "requires_human_approval": True,
        })
        result = apply_proposal(prop, mem, confirm=True)
        assert not result.success
        assert result.error is not None

    def test_append_feedback_log(self, tmp_path):
        mem = _write_memory(tmp_path)
        prop = _write_proposal(tmp_path, _valid_feedback_log_proposal())
        result = apply_proposal(prop, mem, confirm=True)
        assert result.success
        updated = json.loads(mem.read_text())
        assert len(updated["feedback_log"]) == 1
        assert updated["feedback_log"][0]["source_project"] == "test-project"

    def test_append_feedback_log_diff_contains_note(self, tmp_path):
        mem = _write_memory(tmp_path)
        prop = _write_proposal(tmp_path, _valid_feedback_log_proposal())
        result = apply_proposal(prop, mem, confirm=False)
        assert result.success
        assert any("feedback_log" in line for line in result.diff_lines)


# ── Error handling ─────────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_missing_proposal_file_fails(self, tmp_path):
        mem = _write_memory(tmp_path)
        nonexistent = tmp_path / "no-such-file.json"
        result = apply_proposal(nonexistent, mem, confirm=False)
        assert not result.success
        assert "not found" in (result.error or "").lower()

    def test_invalid_json_proposal_fails(self, tmp_path):
        mem = _write_memory(tmp_path)
        bad = tmp_path / "bad.json"
        bad.write_text("{ not valid json", encoding="utf-8")
        result = apply_proposal(bad, mem, confirm=False)
        assert not result.success
        assert result.error is not None

    def test_missing_memory_file_fails(self, tmp_path):
        nonexistent = tmp_path / "no-memory.json"
        prop = _write_proposal(tmp_path, _valid_add_rule_proposal())
        result = apply_proposal(prop, nonexistent, confirm=False)
        assert not result.success
        assert "not found" in (result.error or "").lower()

    def test_invalid_json_memory_fails(self, tmp_path):
        mem = tmp_path / "creative-feedback.json"
        mem.write_text("{ bad json", encoding="utf-8")
        prop = _write_proposal(tmp_path, _valid_add_rule_proposal())
        result = apply_proposal(prop, mem, confirm=False)
        assert not result.success

    def test_target_not_in_memory_fails(self, tmp_path):
        """target_path valid by spec but key absent from the actual file."""
        stripped = {k: v for k, v in MINIMAL_MEMORY.items() if k != "motion_notes"}
        mem = _write_memory(tmp_path, stripped)
        prop = _write_proposal(tmp_path, {
            "proposal_id": "t-err",
            "created_at": "2026-04-24T00:00:00Z",
            "source_project": "test",
            "proposal_type": "add_preference",
            "target_path": "motion_notes",
            "change_summary": "Add motion note.",
            "evidence_refs": ["projects/test/review.md"],
            "confidence": "medium",
            "proposed_change": {"value": "Prefer still holds in proof sections."},
            "requires_human_approval": True,
        })
        result = apply_proposal(prop, mem, confirm=False)
        assert not result.success
        assert result.error is not None

    def test_invalid_proposal_does_not_modify_memory_in_confirm_mode(self, tmp_path):
        """Even with --confirm, an invalid proposal must never touch the memory file."""
        mem = _write_memory(tmp_path)
        before = mem.read_bytes()
        prop = _write_proposal(tmp_path, _valid_add_rule_proposal(requires_human_approval=False))
        result = apply_proposal(prop, mem, confirm=True)
        assert not result.success
        assert mem.read_bytes() == before


# ── ApplyResult rendering ──────────────────────────────────────────────────────

class TestApplyResultRender:
    def test_error_result_renders_error_prefix(self):
        r = ApplyResult(
            success=False, dry_run=True,
            proposal_id="x", change_summary="",
            error="Something went wrong.",
        )
        assert r.render().startswith("ERROR:")

    def test_dry_run_render_contains_dry_run_label(self, tmp_path):
        mem = _write_memory(tmp_path)
        prop = _write_proposal(tmp_path, _valid_add_rule_proposal())
        result = apply_proposal(prop, mem, confirm=False)
        assert "[DRY-RUN]" in result.render()

    def test_confirm_render_contains_applied_label(self, tmp_path):
        mem = _write_memory(tmp_path)
        prop = _write_proposal(tmp_path, _valid_add_rule_proposal())
        result = apply_proposal(prop, mem, confirm=True)
        assert "[APPLIED]" in result.render()


# ── KNOWN_TARGETS coverage ─────────────────────────────────────────────────────

class TestKnownTargets:
    def test_meta_not_in_known_targets(self):
        assert "_meta" not in KNOWN_TARGETS

    def test_all_string_list_targets_are_known(self):
        from lib.brain.memory_apply import STRING_LIST_TARGETS
        assert STRING_LIST_TARGETS.issubset(KNOWN_TARGETS)

    def test_feedback_log_is_known(self):
        assert "feedback_log" in KNOWN_TARGETS

    def test_reference_reels_is_known(self):
        assert "reference_reels" in KNOWN_TARGETS
