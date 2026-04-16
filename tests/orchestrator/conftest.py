"""
tests/orchestrator/conftest.py — Shared fixtures for orchestrator tests.

All fixtures produce isolated tmp_path directories containing minimal
project.json + required stub files for the target orchestration state.

Fixture naming convention: <state>_project → project at that orchestration state.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


# ── Base project.json template ─────────────────────────────────────────────

_BASE_PROJECT = {
    "phase": "planning",
    "status": "in_progress",
    "style": "cinematic-presenter",
    "theme": "Tech Neutral",
    "theme_primary": "#6366F1",
    "theme_secondary": "#818CF8",
    "topic": "AI test reel",
    "audience": "developers",
    "target_duration_seconds": 40,
    "hook_direction": "result-first",
    "cta_direction": "follow",
    "input_quality": "good",
}


# ── Factory helper ─────────────────────────────────────────────────────────

def make_project(
    tmp_path: Path,
    slug: str,
    gates: list[str],
    extra_files: dict[str, str] | None = None,
    extra_json: dict | None = None,
) -> Path:
    """
    Create a minimal project directory at tmp_path/<slug>/ with project.json
    and any required stub files.

    extra_files: {relative_path: content} — stub files to create
    extra_json: additional fields merged into project.json
    """
    project_dir = tmp_path / slug
    project_dir.mkdir(parents=True, exist_ok=True)

    proj = {**_BASE_PROJECT, "slug": slug, "gates_passed": gates}
    if extra_json:
        proj.update(extra_json)

    (project_dir / "project.json").write_text(
        json.dumps(proj, indent=2), encoding="utf-8"
    )

    if extra_files:
        for rel_path, content in extra_files.items():
            full = project_dir / rel_path
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content, encoding="utf-8")

    return project_dir


# ── Named pytest fixtures ──────────────────────────────────────────────────

@pytest.fixture
def fresh_project(tmp_path: Path) -> Path:
    """State: created — no gates, no files. Entry point."""
    return make_project(tmp_path, "test-fresh", gates=[])


@pytest.fixture
def brief_ready_project(tmp_path: Path) -> Path:
    """State: brief_ready — brief approved, theme not yet set."""
    return make_project(
        tmp_path,
        "test-brief-ready",
        gates=["brief_approved"],
        extra_files={"brief.md": "# Brief\n\nTest topic: AI reel\n"},
    )


@pytest.fixture
def theme_ready_project(tmp_path: Path) -> Path:
    """
    State: theme_ready — brief + theme approved.
    Next: reel-script (claude) — will pause for Claude.
    """
    return make_project(
        tmp_path,
        "test-theme-ready",
        gates=["brief_approved", "theme_set"],
        extra_files={"brief.md": "# Brief\n\nTest topic: AI reel\n"},
    )


@pytest.fixture
def script_ready_project(tmp_path: Path) -> Path:
    """
    State: script_ready — script approved, no audio yet.
    Next: ingest-voice (human) — will pause for human.
    """
    return make_project(
        tmp_path,
        "test-script-ready",
        gates=["brief_approved", "theme_set", "script_approved"],
        extra_files={
            "brief.md": "# Brief\n\nTest topic: AI reel\n",
            "script.md": "# Script\n\n## ElevenLabs Script\n\nHello world.\n",
        },
    )


@pytest.fixture
def reconciled_project(tmp_path: Path) -> Path:
    """
    State: reconciled — voice ingested and reconciled.
    Next: shot-list-4b-i (claude) — will pause for Claude.
    """
    return make_project(
        tmp_path,
        "test-reconciled",
        gates=[
            "brief_approved", "theme_set", "script_approved",
            "reconciliation_resolved",
        ],
        extra_files={
            "brief.md": "# Brief\n",
            "script.md": "# Script\n\n## ElevenLabs Script\n\nHello.\n",
            "audio/beat-map.json": json.dumps({
                "beats": [
                    {"id": "beat-01", "start": 0.0, "end": 2.5, "text": "Hello"},
                    {"id": "beat-02", "start": 2.5, "end": 5.0, "text": "World"},
                ],
                "total_duration": 5.0,
                "editorial_grain": "medium",
            }),
            "audio/reconciliation.md": "# Reconciliation\n\nNo issues found.\n",
            "audio/captions.json": json.dumps([]),
        },
    )


@pytest.fixture
def shot_list_ready_project(tmp_path: Path) -> Path:
    """
    State: shot_list_ready — all 3 shot-list sub-phases approved.
    Next: motion-intent (claude) + asset-prep (code) in parallel.
    """
    return make_project(
        tmp_path,
        "test-shot-list-ready",
        gates=[
            "brief_approved", "theme_set", "script_approved",
            "reconciliation_resolved",
            "visual_assignment_approved", "asset_fitness_passed",
            "technical_planning_approved",
        ],
        extra_files={
            "brief.md": "# Brief\n",
            "script.md": "# Script\n\n## ElevenLabs Script\n\nHello.\n",
            "audio/beat-map.json": json.dumps({
                "beats": [{"id": "beat-01", "start": 0.0, "end": 2.5, "text": "Hello"}],
                "total_duration": 2.5,
            }),
            "shot-list.md": "# Shot List\n\n## Phase 4b-iii\n\nTechnical planning approved.\n",
        },
    )


@pytest.fixture
def assembled_project(tmp_path: Path) -> Path:
    """
    State: assembled — motion + assets done, timeline.json exists.
    Next: preview (human) — will pause for human.
    """
    return make_project(
        tmp_path,
        "test-assembled",
        gates=[
            "brief_approved", "theme_set", "script_approved",
            "reconciliation_resolved",
            "visual_assignment_approved", "asset_fitness_passed",
            "technical_planning_approved",
            "motion_intent_reviewed", "assets_validated",
        ],
        extra_files={
            "brief.md": "# Brief\n",
            "script.md": "# Script\n\n## ElevenLabs Script\n\nHello.\n",
            "audio/beat-map.json": json.dumps({"beats": [], "total_duration": 5.0}),
            "shot-list.md": "# Shot List\n",
            "output/motion-intent.md": "# Motion Intent\n\nAll beats assigned.\n",
            "output/timeline.json": json.dumps({"beats": [], "version": "2"}),
        },
    )


@pytest.fixture
def preview_passed_project(tmp_path: Path) -> Path:
    """
    State: preview_approved — preview passed, ready for QA.
    Next: qa-reel (code+claude).
    """
    return make_project(
        tmp_path,
        "test-preview-passed",
        gates=[
            "brief_approved", "theme_set", "script_approved",
            "reconciliation_resolved",
            "visual_assignment_approved", "asset_fitness_passed",
            "technical_planning_approved",
            "motion_intent_reviewed", "assets_validated",
            "preview_passed",
        ],
        extra_files={
            "brief.md": "# Brief\n",
            "script.md": "# Script\n\n## ElevenLabs Script\n\nHello.\n",
            "audio/beat-map.json": json.dumps({"beats": [], "total_duration": 5.0}),
            "shot-list.md": "# Shot List\n",
            "output/motion-intent.md": "# Motion Intent\n",
            "output/timeline.json": json.dumps({"beats": [], "version": "2"}),
        },
    )


@pytest.fixture
def qa_passed_project(tmp_path: Path) -> Path:
    """
    State: qa_passed — all 11 gates passed, ready to render.
    Next: render (code).
    Includes output/qa-report.md so required_files check passes.
    """
    return make_project(
        tmp_path,
        "test-qa-passed",
        gates=[
            "brief_approved", "theme_set", "script_approved",
            "reconciliation_resolved",
            "visual_assignment_approved", "asset_fitness_passed",
            "technical_planning_approved",
            "motion_intent_reviewed", "assets_validated",
            "preview_passed", "qa_passed",
        ],
        extra_files={
            "brief.md": "# Brief\n",
            "script.md": "# Script\n\n## ElevenLabs Script\n\nHello.\n",
            "audio/beat-map.json": json.dumps({"beats": [], "total_duration": 5.0}),
            "shot-list.md": "# Shot List\n",
            "output/motion-intent.md": "# Motion Intent\n",
            "output/timeline.json": json.dumps({"beats": [], "version": "2"}),
            "output/qa-report.md": "# QA Report\n\nAll checks passed.\n",
        },
    )
