"""
lib/orchestrator/spec.py — Static specification: phase definitions,
state model, legal transitions, and invalidation rules.

This is the single canonical source for workflow structure.
Nothing here does I/O — pure data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Actor = Literal["code", "claude", "human", "code+claude", "human+claude"]


# ── Phase spec ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PhaseSpec:
    """Static description of a single pipeline phase."""
    key: str
    name: str
    purpose: str
    actor: Actor
    skill_name: str | None          # skill invoked in conversation (e.g. "reel-script")
    required_gates: tuple[str, ...] # gates that must be passed before this phase
    required_files: tuple[str, ...] # files that must exist (relative to project_dir)
    output_files: tuple[str, ...]   # files this phase produces
    sets_gate: str | None           # gate that gets set after human approval
    human_approval_required: bool
    creative_intent_required: bool
    optional: bool                  # True = skippable (e.g. broll-pipeline)
    parallel_with: tuple[str, ...]  # phase keys that can run simultaneously
    command_hint: str               # what to tell the user


# ── Canonical phases ───────────────────────────────────────────────────────

PHASES: dict[str, PhaseSpec] = {

    "source-brief": PhaseSpec(
        key="source-brief",
        name="Source Brief (Phase 0)",
        purpose="Extract source research and create project brief from URL or topic",
        actor="code+claude",
        skill_name="source-brief",
        required_gates=(),
        required_files=(),
        output_files=("brief.md", "source-research.md"),
        sets_gate="brief_approved",
        human_approval_required=True,
        creative_intent_required=False,
        optional=False,
        parallel_with=(),
        command_hint="node lib/capture/source-brief.js --url <url> --project <slug>",
    ),

    "theme-factory": PhaseSpec(
        key="theme-factory",
        name="Theme Selection (Phase 0b)",
        purpose="Set theme and brand-aligned color defaults in project.json",
        actor="code+claude",
        skill_name="theme-factory",
        required_gates=(),
        required_files=("project.json",),
        output_files=(),
        sets_gate="theme_set",
        human_approval_required=False,
        creative_intent_required=False,
        optional=False,
        parallel_with=(),
        command_hint="In conversation: /theme-factory",
    ),

    "reel-script": PhaseSpec(
        key="reel-script",
        name="Reel Script (Phase 1)",
        purpose="Write ElevenLabs-ready voiceover script with hook and CTA",
        actor="claude",
        skill_name="reel-script",
        required_gates=("brief_approved", "theme_set"),
        required_files=("brief.md", "project.json"),
        output_files=("script.md",),
        sets_gate="script_approved",
        human_approval_required=True,
        creative_intent_required=True,
        optional=False,
        parallel_with=(),
        command_hint="In conversation: /reel-script",
    ),

    "broll-pipeline": PhaseSpec(
        key="broll-pipeline",
        name="B-Roll Pipeline (Phase 1b)",
        purpose="Generate and classify cinematic b-roll footage (optional)",
        actor="human+claude",
        skill_name="broll-pipeline",
        required_gates=("script_approved",),
        required_files=("script.md",),
        output_files=("broll_scenes/scene_list.json",),
        sets_gate=None,
        human_approval_required=False,
        creative_intent_required=False,
        optional=True,
        parallel_with=("ingest-voice",),
        command_hint="In conversation: /broll-pipeline (ask user first)",
    ),

    "ingest-voice": PhaseSpec(
        key="ingest-voice",
        name="Voice Ingest (Phase 2)",
        purpose="Generate or extract avatar video and audio; produce beat-map and captions",
        actor="human",
        skill_name="ingest-voice",
        required_gates=("script_approved",),
        required_files=("script.md",),
        output_files=("audio/beat-map.json", "audio/captions.json", "source.wav"),
        sets_gate=None,
        human_approval_required=False,
        creative_intent_required=False,
        optional=False,
        parallel_with=("broll-pipeline",),
        command_hint="Generate ElevenLabs audio + HeyGen avatar → place files in audio/ and project root",
    ),

    "script-reconcile": PhaseSpec(
        key="script-reconcile",
        name="Script Reconciliation (Phase 2b)",
        purpose="Align approved script text against actual spoken transcript word-by-word",
        actor="claude",
        skill_name="script-reconcile",
        required_gates=("script_approved",),
        required_files=("audio/beat-map.json", "script.md"),
        output_files=("audio/reconciliation.md",),
        sets_gate="reconciliation_resolved",
        human_approval_required=True,
        creative_intent_required=False,
        optional=False,
        parallel_with=(),
        command_hint="In conversation: /script-reconcile",
    ),

    "caption-polish": PhaseSpec(
        key="caption-polish",
        name="Caption Polish (Phase 3b)",
        purpose="Correct spelling, chunk length, emphasis tags in captions.json",
        actor="code+claude",
        skill_name="caption-polish",
        required_gates=("reconciliation_resolved",),
        required_files=("audio/captions.json", "audio/beat-map.json"),
        output_files=("audio/captions.json",),
        sets_gate=None,
        human_approval_required=False,
        creative_intent_required=False,
        optional=False,
        parallel_with=("capture-demo", "shot-list-4b-i"),
        command_hint="In conversation: /caption-polish",
    ),

    "capture-demo": PhaseSpec(
        key="capture-demo",
        name="Demo Capture (Phase 4)",
        purpose="Capture demo screenshots and videos; populate assets catalog",
        actor="code+claude",
        skill_name="capture-demo",
        required_gates=("reconciliation_resolved",),
        required_files=("audio/beat-map.json",),
        output_files=("assets/sourced/catalog.json",),
        sets_gate=None,
        human_approval_required=False,
        creative_intent_required=False,
        optional=False,
        parallel_with=("caption-polish", "shot-list-4b-i"),
        command_hint="node lib/capture/capture-demo.js  OR  python -m lib.assets ...",
    ),

    "shot-list-4b-i": PhaseSpec(
        key="shot-list-4b-i",
        name="Visual Assignment (Phase 4b-i)",
        purpose="Map every beat to a visual type and asset; editorial creative decisions",
        actor="claude",
        skill_name="shot-list",
        required_gates=("reconciliation_resolved",),
        required_files=("audio/beat-map.json",),
        output_files=("shot-list.md",),
        sets_gate="visual_assignment_approved",
        human_approval_required=True,
        creative_intent_required=True,
        optional=False,
        parallel_with=("caption-polish", "capture-demo"),
        command_hint="In conversation: /shot-list (Phase 4b-i)",
    ),

    "shot-list-4b-ii": PhaseSpec(
        key="shot-list-4b-ii",
        name="Component Mapping + Asset Fitness (Phase 4b-ii)",
        purpose="Select Remotion components per beat; audit asset fitness (MATCH/PARTIAL/MISMATCH/MISSING)",
        actor="claude",
        skill_name="shot-list",
        required_gates=("visual_assignment_approved",),
        required_files=("shot-list.md",),
        output_files=("shot-list.md",),
        sets_gate="asset_fitness_passed",
        human_approval_required=True,
        creative_intent_required=False,
        optional=False,
        parallel_with=(),
        command_hint="In conversation: /shot-list (Phase 4b-ii)",
    ),

    "shot-list-4b-iii": PhaseSpec(
        key="shot-list-4b-iii",
        name="Technical Planning (Phase 4b-iii)",
        purpose="Define zoom coordinates, SFX plan, backgrounds, playbackRate per beat",
        actor="claude",
        skill_name="shot-list",
        required_gates=("asset_fitness_passed",),
        required_files=("shot-list.md",),
        output_files=("shot-list.md",),
        sets_gate="technical_planning_approved",
        human_approval_required=True,
        creative_intent_required=False,
        optional=False,
        parallel_with=(),
        command_hint="In conversation: /shot-list (Phase 4b-iii)",
    ),

    "motion-intent": PhaseSpec(
        key="motion-intent",
        name="Motion Intent (Phase 4c)",
        purpose="Assign motion mode and behavior per beat; preset mapping for assembly",
        actor="claude",
        skill_name="motion-intent",
        required_gates=("technical_planning_approved",),
        required_files=("shot-list.md",),
        output_files=("output/motion-intent.md",),
        sets_gate="motion_intent_reviewed",
        human_approval_required=True,
        creative_intent_required=True,
        optional=False,
        parallel_with=("asset-prep",),
        command_hint="In conversation: /motion-intent",
    ),

    "asset-prep": PhaseSpec(
        key="asset-prep",
        name="Asset Prep (Phase 4d)",
        purpose="Re-encode videos, crop chrome, validate all assets for Remotion",
        actor="code",
        skill_name="asset-prep",
        required_gates=("technical_planning_approved",),
        required_files=(),
        output_files=(),
        sets_gate="assets_validated",
        human_approval_required=False,
        creative_intent_required=False,
        optional=False,
        parallel_with=("motion-intent",),
        command_hint="In conversation: /asset-prep  OR  python -m lib.phase post asset-prep projects/<slug>",
    ),

    "assemble-reel": PhaseSpec(
        key="assemble-reel",
        name="Assembly (Phase 5)",
        purpose="Build timeline.json from approved shot list, motion intent, and prepared assets",
        actor="claude",
        skill_name="assemble-reel",
        required_gates=("motion_intent_reviewed", "assets_validated"),
        required_files=("output/motion-intent.md",),
        output_files=("output/timeline.json",),
        sets_gate=None,
        human_approval_required=False,
        creative_intent_required=False,  # only when structure materially changes
        optional=False,
        parallel_with=(),
        command_hint="In conversation: /assemble-reel",
    ),

    "preview": PhaseSpec(
        key="preview",
        name="Quick Preview (Phase 5b)",
        purpose="Inspect key frames in Remotion studio; sanity-check before full QA",
        actor="human",
        skill_name=None,
        required_gates=(),
        required_files=("output/timeline.json",),
        output_files=(),
        sets_gate="preview_passed",
        human_approval_required=True,
        creative_intent_required=False,
        optional=False,
        parallel_with=(),
        command_hint="cd remotion && npx remotion studio  →  python -m lib.orchestrator approve <slug> preview_passed",
    ),

    "qa-reel": PhaseSpec(
        key="qa-reel",
        name="QA (Phase 6)",
        purpose="Full technical + creative freshness QA; must pass before render",
        actor="code+claude",
        skill_name="qa-reel",
        required_gates=("preview_passed",),
        required_files=("output/timeline.json",),
        output_files=("output/qa-report.md",),
        sets_gate="qa_passed",
        human_approval_required=True,
        creative_intent_required=False,
        optional=False,
        parallel_with=(),
        command_hint="python -m lib.qa.cli projects/<slug>  →  In conversation: /qa-reel",
    ),

    "render": PhaseSpec(
        key="render",
        name="Render (Phase 7)",
        purpose="Final export — only after QA passes",
        actor="code",
        skill_name="render",
        required_gates=("qa_passed",),
        required_files=("output/qa-report.md",),
        output_files=(),
        sets_gate=None,
        human_approval_required=False,
        creative_intent_required=False,
        optional=False,
        parallel_with=(),
        command_hint="cd remotion && npx remotion render ReelComposition --output out/reel.mp4",
    ),

    "benchmark": PhaseSpec(
        key="benchmark",
        name="Benchmark Review (Phase 10)",
        purpose="Score reel against 9 benchmark dimensions; compare to liked reference reels",
        actor="human",
        skill_name=None,
        required_gates=(),
        required_files=(),
        output_files=(),
        sets_gate=None,
        human_approval_required=False,
        creative_intent_required=False,
        optional=True,
        parallel_with=("feedback-capture",),
        command_hint="Use training/benchmark-scorecard.md + projects/_shared/benchmark-review-template.md",
    ),

    "feedback-capture": PhaseSpec(
        key="feedback-capture",
        name="Feedback Capture",
        purpose="Classify review signals; propose updates to creative-feedback.json",
        actor="claude",
        skill_name="feedback-capture",
        required_gates=(),
        required_files=(),
        output_files=("output/review-feedback.md",),
        sets_gate=None,
        human_approval_required=True,
        creative_intent_required=False,
        optional=True,
        parallel_with=("benchmark",),
        command_hint="In conversation: /feedback-capture",
    ),

    "revision": PhaseSpec(
        key="revision",
        name="Revision",
        purpose="Apply fixes based on QA findings, benchmark outcomes, or review feedback",
        actor="claude",
        skill_name=None,
        required_gates=(),
        required_files=(),
        output_files=(),
        sets_gate=None,
        human_approval_required=True,
        creative_intent_required=True,
        optional=False,
        parallel_with=(),
        command_hint="In conversation: explain what to change → Creative Intent Summary required",
    ),
}


# ── Orchestration states ───────────────────────────────────────────────────

# Ordered from lowest to highest pipeline progress.
# Used for display and comparison only — state is always derived from gates.
ORCHESTRATION_STATES = [
    "created",
    "brief_ready",
    "theme_ready",
    "script_ready",
    "voice_ingested",
    "reconciled",
    "shot_list_visual_done",
    "shot_list_fitness_done",
    "shot_list_ready",
    "motion_ready",
    "assets_ready",
    "assembled",
    "preview_approved",
    "qa_passed",
    "rendered",
    "complete",
]


# ── Artifact → gate invalidation map ──────────────────────────────────────
# Key: artifact path (relative to project_dir, or basename)
# Value: gate to reset FROM (cascades all downstream gates too)
# Uses lib.gates.reset_gate which removes the named gate + all downstream.

INVALIDATION_MAP: dict[str, str] = {
    # If script changes: everything from reconciliation onward is stale
    "script.md":                    "reconciliation_resolved",
    # If beat-map changes: visual assignments may no longer match beats
    "audio/beat-map.json":          "visual_assignment_approved",
    # If shot-list changes: motion intent and assembly are stale
    "shot-list.md":                 "technical_planning_approved",
    # If motion intent changes: assembly and preview are stale
    "output/motion-intent.md":      "assets_validated",
    # If timeline changes: preview and QA are stale
    "output/timeline.json":         "preview_passed",
}

# Human-readable descriptions for each invalidation
INVALIDATION_DESCRIPTIONS: dict[str, str] = {
    "script.md": "Script changed → reconciliation, shot list, motion intent, assembly, preview, QA all stale",
    "audio/beat-map.json": "Beat map changed → visual assignment, technical planning, motion intent, assembly, preview, QA all stale",
    "shot-list.md": "Shot list changed → technical planning, motion intent, assembly, preview, QA all stale",
    "output/motion-intent.md": "Motion intent changed → assembly, preview, QA all stale",
    "output/timeline.json": "Timeline changed → preview, QA stale",
}


# ── Parity-critical phases ──────────────────────────────────────────────────
# Parity checks must pass before these phases begin.

PARITY_REQUIRED_BEFORE: frozenset[str] = frozenset({
    "assemble-reel",
    "qa-reel",
    "render",
})


# ── Feedback-capture trigger points ────────────────────────────────────────
# Suggest feedback-capture after these phases complete.

FEEDBACK_TRIGGER_AFTER: frozenset[str] = frozenset({
    "preview",
    "qa-reel",
    "render",
    "revision",
})


# ── Benchmark trigger points ────────────────────────────────────────────────
# Suggest benchmark after render (and after major rule changes).

BENCHMARK_TRIGGER_AFTER: frozenset[str] = frozenset({
    "render",
})
