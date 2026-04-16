"""
lib/orchestrator/state.py — Project state loading and orchestration state derivation.

Derives a rich orchestration state from project.json (gates_passed + artifacts).
Backward-compatible: existing projects need no migration.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


# ── Project state snapshot ─────────────────────────────────────────────────

@dataclass
class ProjectSnapshot:
    """All relevant project state in one place."""
    slug: str
    project_dir: Path
    project_json: dict                     # raw project.json contents
    gates_passed: list[str]
    style: str
    theme: str
    theme_primary: str
    phase: str
    status: str
    orchestration_state: str               # derived (see derive_state)
    awaiting_human_input: bool
    awaiting_claude_phase: bool
    blocking_reason: str | None
    stale_artifacts: list[str]             # artifacts that may be stale
    render_artifact: Path | None           # path to rendered video if it exists


def load_snapshot(project_dir: Path) -> ProjectSnapshot:
    """Load project.json and derive full orchestration state."""
    project_file = project_dir / "project.json"
    if not project_file.exists():
        raise FileNotFoundError(f"project.json not found in {project_dir}")

    with open(project_file, encoding="utf-8") as f:
        proj = json.load(f)

    gates_passed = proj.get("gates_passed", [])
    style = proj.get("style", "cinematic-presenter")
    theme = proj.get("theme", "unknown")
    theme_primary = proj.get("theme_primary", "#000000")
    phase = proj.get("phase", "unknown")
    status = proj.get("status", "unknown")
    slug = proj.get("slug", project_dir.name)

    # Derive orchestration state
    orch_state = _derive_state(gates_passed, project_dir)

    # Detect pending human input
    awaiting_human = _is_awaiting_human(orch_state, gates_passed, project_dir)
    awaiting_claude = _is_awaiting_claude(orch_state)

    # Find render artifact
    render_artifact = _find_render_artifact(project_dir)

    return ProjectSnapshot(
        slug=slug,
        project_dir=project_dir,
        project_json=proj,
        gates_passed=gates_passed,
        style=style,
        theme=theme,
        theme_primary=theme_primary,
        phase=phase,
        status=status,
        orchestration_state=orch_state,
        awaiting_human_input=awaiting_human,
        awaiting_claude_phase=awaiting_claude,
        blocking_reason=None,
        stale_artifacts=[],
        render_artifact=render_artifact,
    )


# ── State derivation ───────────────────────────────────────────────────────

def _derive_state(gates_passed: list[str], project_dir: Path) -> str:
    """
    Compute the current orchestration state from gates_passed and artifact existence.
    Returns a string from ORCHESTRATION_STATES (or a transition sub-state).
    """
    g = set(gates_passed)

    # Rendered — qa_passed + render file exists
    if "qa_passed" in g and _find_render_artifact(project_dir) is not None:
        return "rendered"

    # QA passed — ready to render
    if "qa_passed" in g:
        return "qa_passed"

    # Preview approved — ready for QA
    if "preview_passed" in g:
        return "preview_approved"

    # Assembled — timeline exists (even without preview gate)
    timeline = project_dir / "output" / "timeline.json"
    if timeline.exists() and "assets_validated" in g and "motion_intent_reviewed" in g:
        return "assembled"

    # Both parallel phases done — ready to assemble
    if "assets_validated" in g and "motion_intent_reviewed" in g:
        return "assets_ready"

    # One parallel phase done, other still pending
    if "motion_intent_reviewed" in g and "assets_validated" not in g:
        return "motion_done_awaiting_assets"

    if "assets_validated" in g and "motion_intent_reviewed" not in g:
        return "assets_done_awaiting_motion"

    # Full shot list approved (all 3 sub-phases)
    if "technical_planning_approved" in g:
        return "shot_list_ready"

    # Shot list Phase 4b-ii done
    if "asset_fitness_passed" in g:
        return "shot_list_fitness_done"

    # Shot list Phase 4b-i done
    if "visual_assignment_approved" in g:
        return "shot_list_visual_done"

    # Voice reconciled — ready for shot list + demo capture
    if "reconciliation_resolved" in g:
        return "reconciled"

    # Script approved — need voice ingest
    if "script_approved" in g:
        # Check if audio files exist even without gate
        beat_map = project_dir / "audio" / "beat-map.json"
        if beat_map.exists():
            return "voice_ingested"
        return "script_ready"

    # Theme + brief ready for scripting
    if "brief_approved" in g and "theme_set" in g:
        return "theme_ready"

    # Brief only — need theme
    if "brief_approved" in g:
        return "brief_ready"

    return "created"


def _is_awaiting_human(state: str, gates_passed: list[str], project_dir: Path) -> bool:
    """Returns True when the project is waiting for explicit human action."""
    g = set(gates_passed)
    # Waiting for approval at various checkpoints
    if state == "created":
        return False
    if state == "brief_ready" and "theme_set" not in g:
        return False  # code can run theme-factory
    if state == "theme_ready":
        return False  # Claude can proceed to scripting
    if state == "script_ready":
        # Waiting for user to generate audio (can't be automated)
        return True
    if state == "assembled":
        # Waiting for preview review
        return True
    if state == "preview_approved":
        # QA can run automatically
        return False
    if state == "qa_passed":
        # Render can run automatically
        return False
    return False


def _is_awaiting_claude(state: str) -> bool:
    """Returns True when the next action requires Claude in conversation."""
    return state in {
        "theme_ready",           # reel-script
        "reconciled",            # shot-list-4b-i
        "shot_list_visual_done", # shot-list-4b-ii
        "shot_list_fitness_done",# shot-list-4b-iii
        "shot_list_ready",       # motion-intent
        "assets_ready",          # assemble-reel
        "motion_done_awaiting_assets",  # motion-intent done, waiting for asset-prep
        "assets_done_awaiting_motion",  # asset-prep done, waiting for motion-intent
    }


def _find_render_artifact(project_dir: Path) -> Path | None:
    """Find any rendered video in the project directory."""
    # Check common render output locations
    for pattern in ["out/reel.mp4", "out/*.mp4", "*.mp4"]:
        matches = list(project_dir.glob(pattern))
        if matches:
            return matches[0]
    return None


# ── State display helpers ──────────────────────────────────────────────────

STATE_LABELS: dict[str, str] = {
    "created":                    "Created — no work started",
    "brief_ready":                "Brief approved — theme selection needed",
    "theme_ready":                "Theme set — ready for scripting",
    "script_ready":               "Script approved — awaiting voice generation",
    "voice_ingested":             "Voice files present — awaiting reconciliation",
    "reconciled":                 "Reconciled — ready for shot list + demo capture",
    "shot_list_visual_done":      "Visual assignment approved — Phase 4b-ii next",
    "shot_list_fitness_done":     "Asset fitness passed — Phase 4b-iii next",
    "shot_list_ready":            "Shot list complete — motion intent + asset prep (parallel)",
    "motion_done_awaiting_assets":"Motion intent done — waiting for asset prep",
    "assets_done_awaiting_motion":"Asset prep done — waiting for motion intent",
    "assets_ready":               "Both parallel phases done — ready to assemble",
    "assembled":                  "Timeline assembled — awaiting preview review",
    "preview_approved":           "Preview approved — ready for QA",
    "qa_passed":                  "QA passed — ready to render",
    "rendered":                   "Rendered — ready for benchmark + feedback",
    "complete":                   "Complete",
}


def state_label(state: str) -> str:
    return STATE_LABELS.get(state, state)
