"""
lib.brain.memory_apply — Safe, human-approved memory promotion.

Applies a structured proposal JSON to memory/creative-feedback.json ONLY
when --confirm is explicitly provided. Every other invocation is dry-run.

Design rules:
  - Memory is NEVER modified automatically. --confirm is a hard gate.
  - A timestamped .bak file is always created before any write.
  - Only known top-level keys may be targeted (no arbitrary key creation).
  - Proposals must carry requires_human_approval: true or are rejected.
  - Evidence refs are required for rule/preference promotions.
  - Invalid proposals are rejected with a clear error; never partially applied.
"""

from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── Constants ─────────────────────────────────────────────────────────────────

# Top-level keys in creative-feedback.json that may be targeted.
# "_meta" is deliberately excluded — it must never be programmatically changed.
KNOWN_TARGETS: frozenset[str] = frozenset({
    "hard_rules",
    "soft_preferences",
    "likes",
    "dislikes",
    "motion_notes",
    "hook_notes",
    "caption_notes",
    "components_to_use_more",
    "components_to_use_less",
    "reference_reels",
    "feedback_log",
})

# Keys whose items are plain strings (as opposed to dicts).
STRING_LIST_TARGETS: frozenset[str] = frozenset({
    "hard_rules", "soft_preferences", "likes", "dislikes",
    "motion_notes", "hook_notes", "caption_notes",
    "components_to_use_more", "components_to_use_less",
})

VALID_PROPOSAL_TYPES: frozenset[str] = frozenset({
    "add_rule",
    "update_rule",
    "add_preference",
    "update_preference",
    "add_like",
    "add_dislike",
    "add_component_weight",
    "append_feedback_log",
})

VALID_CONFIDENCES: frozenset[str] = frozenset({"low", "medium", "high"})

# Proposal types that must supply at least one evidence ref.
EVIDENCE_REQUIRED_TYPES: frozenset[str] = frozenset({
    "add_rule",
    "update_rule",
    "add_preference",
    "update_preference",
})

# Required top-level fields in every proposal.
REQUIRED_PROPOSAL_FIELDS: frozenset[str] = frozenset({
    "proposal_id",
    "created_at",
    "source_project",
    "proposal_type",
    "target_path",
    "change_summary",
    "evidence_refs",
    "confidence",
    "proposed_change",
    "requires_human_approval",
})


# ── Result model ──────────────────────────────────────────────────────────────

@dataclass
class ApplyResult:
    """Outcome of apply_proposal()."""
    success: bool
    dry_run: bool
    proposal_id: str
    change_summary: str
    diff_lines: list[str] = field(default_factory=list)
    backup_path: Path | None = None
    error: str | None = None

    def render(self) -> str:
        lines: list[str] = []
        if self.error:
            lines.append(f"ERROR: {self.error}")
            return "\n".join(lines)

        mode = "DRY-RUN" if self.dry_run else "APPLIED"
        lines.append(f"[{mode}] Proposal: {self.proposal_id}")
        lines.append(f"  Summary : {self.change_summary}")
        lines.append("")
        if self.diff_lines:
            lines.append("  What changed:")
            for dl in self.diff_lines:
                lines.append(f"    {dl}")
        if self.backup_path:
            lines.append("")
            lines.append(f"  Backup  : {self.backup_path}")
        if self.dry_run:
            lines.append("")
            lines.append(
                "  No changes were written. "
                "Re-run with --confirm to apply."
            )
        return "\n".join(lines)


# ── Validation ────────────────────────────────────────────────────────────────

def validate_proposal(proposal: Any) -> list[str]:
    """
    Validate a proposal dict. Returns a list of error strings (empty = valid).
    Never raises — caller decides what to do with errors.
    """
    errors: list[str] = []

    if not isinstance(proposal, dict):
        return ["Proposal must be a JSON object (dict)."]

    # Required fields
    missing = REQUIRED_PROPOSAL_FIELDS - set(proposal.keys())
    for m in sorted(missing):
        errors.append(f"Missing required field: '{m}'")
    if missing:
        return errors  # can't validate further without required fields

    # requires_human_approval must literally be True
    if proposal.get("requires_human_approval") is not True:
        errors.append(
            "'requires_human_approval' must be true. "
            "Proposals that do not require approval cannot be applied."
        )

    # proposal_type
    ptype = proposal.get("proposal_type", "")
    if ptype not in VALID_PROPOSAL_TYPES:
        errors.append(
            f"Unknown proposal_type '{ptype}'. "
            f"Valid: {sorted(VALID_PROPOSAL_TYPES)}"
        )

    # target_path
    target = proposal.get("target_path", "")
    if target not in KNOWN_TARGETS:
        errors.append(
            f"Unknown target_path '{target}'. "
            f"Valid: {sorted(KNOWN_TARGETS)}"
        )

    # confidence
    conf = proposal.get("confidence", "")
    if conf not in VALID_CONFIDENCES:
        errors.append(
            f"Unknown confidence '{conf}'. "
            f"Valid: {sorted(VALID_CONFIDENCES)}"
        )

    # evidence_refs must be a list
    evidence = proposal.get("evidence_refs", None)
    if not isinstance(evidence, list):
        errors.append("'evidence_refs' must be a list (can be empty for non-rule types).")
    elif ptype in EVIDENCE_REQUIRED_TYPES and len(evidence) == 0:
        errors.append(
            f"proposal_type '{ptype}' requires at least one evidence ref. "
            "Add the source project's review-feedback.md or performance.json to evidence_refs."
        )

    # proposed_change must be a dict
    change = proposal.get("proposed_change", None)
    if not isinstance(change, dict):
        errors.append("'proposed_change' must be a JSON object (dict).")
    else:
        # Validate proposed_change structure per proposal_type
        if ptype in VALID_PROPOSAL_TYPES and target in KNOWN_TARGETS:
            errors.extend(_validate_change_shape(ptype, target, change))

    return errors


def _validate_change_shape(ptype: str, target: str, change: dict) -> list[str]:
    """Validate the proposed_change dict shape for a given proposal_type."""
    errs: list[str] = []

    if ptype in ("add_rule", "add_preference", "add_like", "add_dislike", "add_component_weight"):
        if "value" not in change:
            errs.append(
                f"proposed_change for '{ptype}' must have a 'value' key "
                "(the string to append)."
            )
        elif not isinstance(change["value"], str):
            errs.append("proposed_change.value must be a string.")

    elif ptype in ("update_rule", "update_preference"):
        for key in ("old_value", "new_value"):
            if key not in change:
                errs.append(f"proposed_change for '{ptype}' must have '{key}'.")
            elif not isinstance(change[key], str):
                errs.append(f"proposed_change.{key} must be a string.")

    elif ptype == "append_feedback_log":
        if "entry" not in change:
            errs.append(
                "proposed_change for 'append_feedback_log' must have an 'entry' key "
                "(the feedback_log dict to append)."
            )
        elif not isinstance(change["entry"], dict):
            errs.append("proposed_change.entry must be a dict.")

    return errs


# ── Change application ────────────────────────────────────────────────────────

def _compute_change(
    memory: dict, proposal: dict
) -> tuple[dict, list[str]]:
    """
    Compute the new memory state after applying the proposal.

    Returns (new_memory_dict, diff_lines).
    Never modifies the input dict — always works on a deep copy.
    Raises ValueError if the change cannot be applied (e.g. old_value not found).
    """
    new_memory = copy.deepcopy(memory)
    ptype = proposal["proposal_type"]
    target = proposal["target_path"]
    change = proposal["proposed_change"]
    diff: list[str] = []

    if ptype in ("add_rule", "add_preference", "add_like", "add_dislike", "add_component_weight"):
        value = change["value"]
        lst = new_memory[target]
        if not isinstance(lst, list):
            raise ValueError(f"target '{target}' is not a list in memory file.")
        lst.append(value)
        preview = value[:100] + ("…" if len(value) > 100 else "")
        diff.append(f"+ [{target}] append: {preview!r}")

    elif ptype in ("update_rule", "update_preference"):
        old_value = change["old_value"]
        new_value = change["new_value"]
        lst = new_memory[target]
        if not isinstance(lst, list):
            raise ValueError(f"target '{target}' is not a list in memory file.")
        try:
            idx = lst.index(old_value)
        except ValueError:
            raise ValueError(
                f"old_value not found in '{target}'. "
                f"The existing rule/preference to replace must match exactly."
            )
        lst[idx] = new_value
        old_p = old_value[:60] + ("…" if len(old_value) > 60 else "")
        new_p = new_value[:60] + ("…" if len(new_value) > 60 else "")
        diff.append(f"~ [{target}][{idx}] replace:")
        diff.append(f"  - {old_p!r}")
        diff.append(f"  + {new_p!r}")

    elif ptype == "append_feedback_log":
        entry = change["entry"]
        lst = new_memory.get("feedback_log", [])
        if not isinstance(lst, list):
            raise ValueError("'feedback_log' is not a list in memory file.")
        new_memory["feedback_log"].append(entry)
        note = entry.get("note", "")
        note_p = note[:80] + ("…" if len(note) > 80 else "")
        diff.append(f"+ [feedback_log] append entry: {note_p!r}")

    else:
        raise ValueError(f"Unsupported proposal_type: {ptype!r}")

    return new_memory, diff


# ── Backup ────────────────────────────────────────────────────────────────────

def _create_backup(memory_path: Path) -> Path:
    """Copy memory_path to a timestamped .bak file. Returns the backup path."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    bak_path = memory_path.parent / f"{memory_path.name}.bak.{ts}"
    bak_path.write_bytes(memory_path.read_bytes())
    return bak_path


# ── Main entry point ──────────────────────────────────────────────────────────

def apply_proposal(
    proposal_path: Path,
    memory_path: Path,
    confirm: bool = False,
) -> ApplyResult:
    """
    Load a proposal file and apply it to memory_path.

    In dry-run mode (confirm=False): validates, computes the change, and returns
    a result describing what WOULD happen — without modifying any file.

    In confirm mode (confirm=True): validates, creates a backup, writes the new
    memory state, and returns a result with the backup path.

    Always returns an ApplyResult. Never raises except on unrecoverable I/O errors.
    """
    proposal_path = Path(proposal_path)
    memory_path = Path(memory_path)

    # ── Load proposal ─────────────────────────────────────────────────────────
    if not proposal_path.exists():
        return ApplyResult(
            success=False, dry_run=not confirm,
            proposal_id="unknown", change_summary="",
            error=f"Proposal file not found: {proposal_path}",
        )
    try:
        proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return ApplyResult(
            success=False, dry_run=not confirm,
            proposal_id="unknown", change_summary="",
            error=f"Proposal file is not valid JSON: {e}",
        )

    proposal_id = proposal.get("proposal_id", "unknown") if isinstance(proposal, dict) else "unknown"
    change_summary = proposal.get("change_summary", "") if isinstance(proposal, dict) else ""

    # ── Validate proposal structure ───────────────────────────────────────────
    errors = validate_proposal(proposal)
    if errors:
        joined = "; ".join(errors)
        return ApplyResult(
            success=False, dry_run=not confirm,
            proposal_id=proposal_id, change_summary=change_summary,
            error=f"Proposal validation failed: {joined}",
        )

    # ── Validate memory file ──────────────────────────────────────────────────
    if not memory_path.exists():
        return ApplyResult(
            success=False, dry_run=not confirm,
            proposal_id=proposal_id, change_summary=change_summary,
            error=f"Memory file not found: {memory_path}",
        )
    try:
        memory = json.loads(memory_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return ApplyResult(
            success=False, dry_run=not confirm,
            proposal_id=proposal_id, change_summary=change_summary,
            error=f"Memory file is not valid JSON: {e}",
        )
    if not isinstance(memory, dict):
        return ApplyResult(
            success=False, dry_run=not confirm,
            proposal_id=proposal_id, change_summary=change_summary,
            error="Memory file top level must be a JSON object.",
        )

    # Check that target_path exists in the actual memory file.
    target = proposal["target_path"]
    if target not in memory:
        return ApplyResult(
            success=False, dry_run=not confirm,
            proposal_id=proposal_id, change_summary=change_summary,
            error=(
                f"target_path '{target}' does not exist in memory file. "
                "Only existing keys may be targeted."
            ),
        )

    # ── Compute the change ────────────────────────────────────────────────────
    try:
        new_memory, diff_lines = _compute_change(memory, proposal)
    except ValueError as e:
        return ApplyResult(
            success=False, dry_run=not confirm,
            proposal_id=proposal_id, change_summary=change_summary,
            error=f"Cannot apply change: {e}",
        )

    # ── Dry-run: return without writing ──────────────────────────────────────
    if not confirm:
        return ApplyResult(
            success=True, dry_run=True,
            proposal_id=proposal_id, change_summary=change_summary,
            diff_lines=diff_lines,
        )

    # ── Confirm: backup then write ────────────────────────────────────────────
    bak_path = _create_backup(memory_path)
    memory_path.write_text(
        json.dumps(new_memory, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return ApplyResult(
        success=True, dry_run=False,
        proposal_id=proposal_id, change_summary=change_summary,
        diff_lines=diff_lines,
        backup_path=bak_path,
    )


# ── CLI ───────────────────────────────────────────────────────────────────────

_DEFAULT_MEMORY_PATH = Path("memory/creative-feedback.json")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="lib.brain.memory_apply",
        description=(
            "Apply a structured memory proposal to memory/creative-feedback.json. "
            "Default: dry-run only. Use --confirm to write."
        ),
    )
    parser.add_argument(
        "proposal",
        type=Path,
        help="Path to the proposal JSON file.",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        default=False,
        help=(
            "Actually write the change. Without this flag, only a dry-run is performed "
            "and memory is never modified."
        ),
    )
    parser.add_argument(
        "--memory",
        type=Path,
        default=_DEFAULT_MEMORY_PATH,
        help=f"Path to creative-feedback.json (default: {_DEFAULT_MEMORY_PATH})",
    )

    args = parser.parse_args(argv)

    result = apply_proposal(
        proposal_path=args.proposal,
        memory_path=args.memory,
        confirm=args.confirm,
    )

    print(result.render())

    if not result.success:
        return 2   # validation/IO error
    if result.dry_run:
        return 0   # dry-run always exits 0 (not an error — user should re-run with --confirm)
    return 0


if __name__ == "__main__":
    sys.exit(main())
