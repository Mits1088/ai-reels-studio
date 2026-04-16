"""
lib/orchestrator/invalidation.py — Downstream artifact invalidation.

When an upstream artifact changes, removes the corresponding gate
(and all downstream gates) from project.json via lib.gates.reset_gate.
Produces a clear report of what was invalidated and why.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .spec import INVALIDATION_MAP, INVALIDATION_DESCRIPTIONS


@dataclass
class InvalidationResult:
    changed_artifact: str
    reset_from_gate: str | None
    gates_removed: list[str]
    description: str
    stale_files_hint: list[str]


def invalidate_from_change(
    project_dir: Path,
    artifact: str,   # relative path OR basename
) -> InvalidationResult:
    """
    Given a changed artifact path, determine which gate to reset from,
    remove it (and all downstream) from project.json, and return a report.

    artifact can be:
      - relative path like "shot-list.md" or "output/motion-intent.md"
      - just the filename like "script.md"
    """
    # Normalize: try exact match first, then basename match
    reset_from = INVALIDATION_MAP.get(artifact)
    if reset_from is None:
        # Try basename
        basename = Path(artifact).name
        for key, gate in INVALIDATION_MAP.items():
            if Path(key).name == basename:
                reset_from = gate
                artifact = key
                break

    if reset_from is None:
        return InvalidationResult(
            changed_artifact=artifact,
            reset_from_gate=None,
            gates_removed=[],
            description=f"No invalidation rule for '{artifact}'. No gates changed.",
            stale_files_hint=[],
        )

    description = INVALIDATION_DESCRIPTIONS.get(artifact, f"{artifact} changed")

    # Use lib.gates to do the actual cascade reset
    from lib.gates import reset_gate, _load_project
    import json

    project_file = project_dir / "project.json"
    before = set(_load_project(project_dir).get("gates_passed", []))
    msg = reset_gate(project_dir, reset_from)
    after = set(_load_project(project_dir).get("gates_passed", []))
    removed = sorted(before - after)

    # Build hint about which downstream files are now stale
    stale_hints = _stale_file_hints(removed)

    return InvalidationResult(
        changed_artifact=artifact,
        reset_from_gate=reset_from,
        gates_removed=removed,
        description=description,
        stale_files_hint=stale_hints,
    )


def _stale_file_hints(removed_gates: list[str]) -> list[str]:
    """Given removed gates, list files that are now effectively stale."""
    gate_file_hints: dict[str, str] = {
        "reconciliation_resolved": "audio/reconciliation.md",
        "visual_assignment_approved": "shot-list.md (Phase 4b-i section)",
        "asset_fitness_passed": "shot-list.md (Phase 4b-ii section)",
        "technical_planning_approved": "shot-list.md (Phase 4b-iii section)",
        "motion_intent_reviewed": "output/motion-intent.md",
        "assets_validated": "remotion/public/ assets",
        "preview_passed": "output/timeline.json",
        "qa_passed": "output/qa-report.md",
    }
    return [gate_file_hints[g] for g in removed_gates if g in gate_file_hints]
