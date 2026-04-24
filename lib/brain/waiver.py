"""
lib.brain.waiver — Waiver loading and matching for critic hard mode.

A waiver explicitly grants a named exception from hard-mode blocking for a
specific critic check in a specific project. Waivers must be written to a
named file — there are no silent or automatic waivers.

Design rules:
  - Waivers live in projects/<slug>/critic_waivers.json
  - Every waiver entry must carry all REQUIRED_WAIVER_FIELDS
  - Invalid entries are silently skipped (load_waivers never raises)
  - Matching is by critic_id == finding["check"] — simple equality
"""

from __future__ import annotations

import json
from pathlib import Path


# ── Schema ────────────────────────────────────────────────────────────────────

REQUIRED_WAIVER_FIELDS: frozenset[str] = frozenset({
    "waiver_id",
    "critic_id",       # critic check name being waived, e.g. "asset_overreuse"
    "project_slug",    # must match the project this file lives in
    "reason",          # why the finding is being waived for this render
    "reviewer",        # who approved the waiver
    "date",            # ISO date string
    "scope",           # "this_render" or "permanent"
})

VALID_SCOPES: frozenset[str] = frozenset({"this_render", "permanent"})


# ── Validation ────────────────────────────────────────────────────────────────

def validate_waiver(entry: object) -> list[str]:
    """Return a list of error strings (empty = valid). Never raises."""
    errors: list[str] = []
    if not isinstance(entry, dict):
        return ["Waiver entry must be a JSON object (dict)."]

    missing = REQUIRED_WAIVER_FIELDS - set(entry.keys())
    for m in sorted(missing):
        errors.append(f"Missing required field: '{m}'")

    scope = entry.get("scope", "")
    if scope and scope not in VALID_SCOPES:
        errors.append(
            f"Unknown scope '{scope}'. Valid: {sorted(VALID_SCOPES)}"
        )

    return errors


# ── Loading ───────────────────────────────────────────────────────────────────

def load_waivers(project_dir: Path) -> list[dict]:
    """
    Load waivers from <project_dir>/critic_waivers.json.

    Returns only entries that pass validate_waiver().
    Silently returns [] on missing file, unreadable JSON, or non-list root.
    Never raises.
    """
    waiver_path = Path(project_dir) / "critic_waivers.json"
    if not waiver_path.exists():
        return []
    try:
        raw = json.loads(waiver_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(raw, list):
        return []
    return [entry for entry in raw if validate_waiver(entry) == []]


# ── Matching ──────────────────────────────────────────────────────────────────

def is_waived(finding: dict, waivers: list[dict]) -> bool:
    """
    Return True if any waiver matches this finding.
    Matches on finding["check"] == waiver["critic_id"] (exact string equality).
    """
    check = finding.get("check", "")
    return any(w.get("critic_id") == check for w in waivers)
