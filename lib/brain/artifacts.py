"""
lib.brain.artifacts — Artifact registry and directed dependency map.

Pure data module. No I/O, no mutations.

Every known pipeline artifact has an ArtifactSpec (path, role, description).
Every upstream→downstream dependency has an ArtifactDep carrying the reason
a change to the upstream can make the downstream stale, and the recommended
remediation step.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactSpec:
    """Metadata for a known pipeline artifact."""
    path: str         # relative path from project root
    role: str         # short semantic ID used by tooling
    description: str  # one-line human description
    optional: bool    # True → only present in some projects


@dataclass(frozen=True)
class ArtifactDep:
    """
    A directed dependency: changes to upstream may make downstream stale.

    All fields are plain strings so the map can be treated as pure data
    and serialised without any special handling.
    """
    upstream: str            # relative path of the upstream artifact
    downstream: str          # relative path of the downstream artifact
    reason: str              # why downstream depends on upstream
    recommended_action: str  # what to do when downstream is stale
    base_confidence: str     # "high" | "medium" | "low" — before mtime scaling


# ── Artifact registry ─────────────────────────────────────────────────────────

ARTIFACT_REGISTRY: dict[str, ArtifactSpec] = {a.path: a for a in [
    ArtifactSpec(
        "brief.md",
        "brief",
        "Creative brief — topic, hook, and creative direction",
        optional=False,
    ),
    ArtifactSpec(
        "script.md",
        "script",
        "ElevenLabs-ready narration script",
        optional=False,
    ),
    ArtifactSpec(
        "audio/source.wav",
        "source-audio",
        "Processed narration audio extracted from HeyGen or raw recording",
        optional=False,
    ),
    ArtifactSpec(
        "audio/beat-map.json",
        "beat-map",
        "Beat-level timing map derived from actual audio",
        optional=False,
    ),
    ArtifactSpec(
        "audio/captions.json",
        "captions",
        "Polished caption chunks with phrase-boundary timing",
        optional=False,
    ),
    ArtifactSpec(
        "audio/reconciliation.md",
        "reconciliation",
        "Script-vs-transcript reconciliation report",
        optional=False,
    ),
    ArtifactSpec(
        "shot-list.md",
        "shot-list",
        "Visual assignment, component mapping, and technical planning",
        optional=False,
    ),
    ArtifactSpec(
        "lib/capture/demo-config.json",
        "demo-config",
        "Demo capture specification per beat (what to record)",
        optional=True,
    ),
    ArtifactSpec(
        "assets/sourced/catalog.json",
        "asset-catalog",
        "Catalog of all sourced assets with provenance and license",
        optional=True,
    ),
    ArtifactSpec(
        "output/motion-intent.md",
        "motion-intent",
        "Per-beat motion direction: mode, entry/exit presets, gap ownership",
        optional=False,
    ),
    ArtifactSpec(
        "output/edit-plan.json",
        "edit-plan",
        "Structured edit plan compiled from the shot list",
        optional=True,
    ),
    ArtifactSpec(
        "output/timeline.json",
        "timeline",
        "Remotion timeline — primary input to the composition engine",
        optional=False,
    ),
    ArtifactSpec(
        "output/qa_report.json",
        "qa-report",
        "Structured QA report (machine-readable JSON)",
        optional=True,
    ),
    ArtifactSpec(
        "output/qa-report.md",
        "qa-report-md",
        "Human-readable QA report",
        optional=True,
    ),
    ArtifactSpec(
        "output/critic-report.json",
        "critic-report",
        "Critic analysis report",
        optional=True,
    ),
    ArtifactSpec(
        "output/review-feedback.md",
        "review-feedback",
        "Human review feedback captured after a QA or preview session",
        optional=True,
    ),
]}


# ── Dependency map ────────────────────────────────────────────────────────────
#
# Directed edges: upstream → downstream.
#
# If upstream.mtime > downstream.mtime + STALE_TOLERANCE_SECONDS, the
# downstream is considered potentially stale and a StalenessResult is emitted.
#
# base_confidence reflects how directly the upstream affects the downstream:
#   "high"   → any change to upstream almost certainly invalidates downstream
#   "medium" → change likely invalidates downstream but judgment may be needed
#   "low"    → change may or may not affect downstream (loose coupling)

DEPENDENCY_MAP: list[ArtifactDep] = [

    # ── Script lineage ─────────────────────────────────────────────────────

    ArtifactDep(
        upstream="brief.md",
        downstream="script.md",
        reason=(
            "Script is written from the brief. If the brief was revised after "
            "the script was written, the script may not reflect the current "
            "creative direction."
        ),
        recommended_action="Re-run reel-script or reconcile brief changes manually.",
        base_confidence="medium",
    ),
    ArtifactDep(
        upstream="script.md",
        downstream="audio/reconciliation.md",
        reason=(
            "Reconciliation compares the approved script against actual audio. "
            "If the script was updated after reconciliation was written, the "
            "comparison is no longer valid."
        ),
        recommended_action="Re-run script-reconcile (/script-reconcile).",
        base_confidence="high",
    ),
    ArtifactDep(
        upstream="script.md",
        downstream="audio/beat-map.json",
        reason=(
            "If the script was changed after the beat map was built, the "
            "recorded audio may no longer match the current script text. "
            "A re-record or re-ingest may be required."
        ),
        recommended_action=(
            "Verify the audio still matches the current script. "
            "If not, re-ingest voice and rebuild the beat map."
        ),
        base_confidence="medium",
    ),

    # ── Audio lineage ──────────────────────────────────────────────────────

    ArtifactDep(
        upstream="audio/source.wav",
        downstream="audio/beat-map.json",
        reason=(
            "The beat map is derived from the source audio. A new audio file "
            "makes the existing beat map stale."
        ),
        recommended_action="Rebuild the beat map from the new audio.",
        base_confidence="high",
    ),
    ArtifactDep(
        upstream="audio/beat-map.json",
        downstream="audio/captions.json",
        reason=(
            "Captions are polished from the raw beat map. A newer beat map "
            "means beat timing has changed and captions may be out of sync."
        ),
        recommended_action="Re-run caption-polish (/caption-polish).",
        base_confidence="high",
    ),
    ArtifactDep(
        upstream="audio/beat-map.json",
        downstream="shot-list.md",
        reason=(
            "The shot list assigns visuals to beats from the beat map. A newer "
            "beat map changes beat boundaries and may invalidate visual "
            "assignments that reference those boundaries."
        ),
        recommended_action=(
            "Review the shot list against the updated beat map. "
            "Revise sections tied to changed beats."
        ),
        base_confidence="medium",
    ),

    # ── Shot-list lineage ──────────────────────────────────────────────────

    ArtifactDep(
        upstream="shot-list.md",
        downstream="output/motion-intent.md",
        reason=(
            "Motion intent is derived from the approved shot list. If the "
            "shot list was revised, motion direction may reference beats or "
            "components that no longer exist."
        ),
        recommended_action=(
            "Re-run motion-intent (/motion-intent) against the updated shot list."
        ),
        base_confidence="high",
    ),

    # ── Assembly lineage ───────────────────────────────────────────────────

    ArtifactDep(
        upstream="output/motion-intent.md",
        downstream="output/timeline.json",
        reason=(
            "Timeline assembly is based on motion intent. If motion intent "
            "was revised after the timeline was assembled, the timeline may "
            "not reflect the intended motion design."
        ),
        recommended_action=(
            "Re-assemble the timeline from the updated motion intent."
        ),
        base_confidence="high",
    ),
    ArtifactDep(
        upstream="output/edit-plan.json",
        downstream="output/timeline.json",
        reason=(
            "If the edit plan was updated but the timeline was not recompiled, "
            "they are out of sync."
        ),
        recommended_action=(
            "Recompile: PYTHONPATH=. python -m lib.edit_plan compile "
            "projects/<slug>"
        ),
        base_confidence="high",
    ),
    ArtifactDep(
        upstream="audio/captions.json",
        downstream="output/timeline.json",
        reason=(
            "The timeline embeds caption timing. Updated captions require a "
            "timeline rebuild."
        ),
        recommended_action=(
            "Re-assemble the timeline with the updated captions."
        ),
        base_confidence="medium",
    ),
    ArtifactDep(
        upstream="assets/sourced/catalog.json",
        downstream="output/timeline.json",
        reason=(
            "New assets added to the catalog after the timeline was assembled "
            "may not be referenced in the timeline."
        ),
        recommended_action=(
            "Review the timeline against the updated asset catalog and add "
            "missing asset references where needed."
        ),
        base_confidence="low",
    ),

    # ── QA lineage ─────────────────────────────────────────────────────────

    ArtifactDep(
        upstream="output/timeline.json",
        downstream="output/qa_report.json",
        reason=(
            "QA runs against the timeline. If the timeline was changed after "
            "QA ran, the report no longer reflects the current state."
        ),
        recommended_action=(
            "Re-run QA: PYTHONPATH=. python -m lib.qa.cli projects/<slug>"
        ),
        base_confidence="high",
    ),

    # ── Review-feedback signal ─────────────────────────────────────────────

    ArtifactDep(
        upstream="output/review-feedback.md",
        downstream="output/qa_report.json",
        reason=(
            "Review feedback was captured after the last QA run. The feedback "
            "may identify issues that automated QA does not cover. A manual "
            "re-review or QA re-run is recommended."
        ),
        recommended_action=(
            "Address the review feedback, then re-run QA: "
            "PYTHONPATH=. python -m lib.qa.cli projects/<slug>"
        ),
        base_confidence="medium",
    ),
]
