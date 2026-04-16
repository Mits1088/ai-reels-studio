"""
lib/orchestrator/transitions.py — Compute legal next actions from current state.

Returns a list of NextAction objects describing what can run, what's blocked,
and who needs to act.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .spec import PHASES, PhaseSpec, PARITY_REQUIRED_BEFORE
from .state import ProjectSnapshot


@dataclass
class NextAction:
    """A candidate next action for the project."""
    phase_key: str
    name: str
    actor: str
    command_hint: str
    blocked: bool
    blocked_reason: str | None
    creative_intent_required: bool
    optional: bool
    parallel_label: str | None  # e.g. "parallel with asset-prep"
    priority: int               # lower = more urgent; used for display ordering
    notes: str                  # additional context


def compute_next_actions(snap: ProjectSnapshot) -> list[NextAction]:
    """
    Given the current project snapshot, return all legal next actions
    sorted by priority (most urgent first).
    """
    state = snap.orchestration_state
    g = set(snap.gates_passed)
    project_dir = snap.project_dir
    actions: list[NextAction] = []

    # ── CREATED ─────────────────────────────────────────────────────────────
    if state == "created":
        if not (project_dir / "brief.md").exists():
            actions.append(_action("source-brief", priority=0))
        else:
            # brief.md exists but gate not set
            actions.append(NextAction(
                phase_key="source-brief",
                name="Approve Brief",
                actor="human",
                command_hint=f"python -m lib.orchestrator approve {project_dir.name} brief_approved",
                blocked=False,
                blocked_reason=None,
                creative_intent_required=False,
                optional=False,
                parallel_label=None,
                priority=0,
                notes="brief.md exists — approve it to unlock scripting",
            ))
        actions.append(_action("theme-factory", priority=1))

    # ── BRIEF_READY ─────────────────────────────────────────────────────────
    elif state == "brief_ready":
        actions.append(_action("theme-factory", priority=0,
            notes="Required before scripting — sets theme colors in project.json"))

    # ── THEME_READY ─────────────────────────────────────────────────────────
    elif state == "theme_ready":
        actions.append(_action("reel-script", priority=0))

    # ── SCRIPT_READY ────────────────────────────────────────────────────────
    elif state == "script_ready":
        actions.append(NextAction(
            phase_key="ingest-voice",
            name="Generate Audio + Avatar (Phase 2)",
            actor="human",
            command_hint="Generate ElevenLabs audio → HeyGen avatar → place source.wav + avatar.mp4 in project",
            blocked=False,
            blocked_reason=None,
            creative_intent_required=False,
            optional=False,
            parallel_label=None,
            priority=0,
            notes="Manual step: ElevenLabs for audio, HeyGen for avatar video",
        ))
        actions.append(_action("broll-pipeline", priority=1,
            notes="Optional — ask user first before running"))

    # ── VOICE_INGESTED ──────────────────────────────────────────────────────
    elif state == "voice_ingested":
        actions.append(_action("script-reconcile", priority=0))

    # ── RECONCILED ──────────────────────────────────────────────────────────
    elif state == "reconciled":
        actions.append(_action("shot-list-4b-i", priority=0))
        actions.append(_action("caption-polish", priority=1,
            parallel_label="parallel with shot-list-4b-i"))
        actions.append(_action("capture-demo", priority=1,
            parallel_label="parallel with shot-list-4b-i",
            notes="Stage 0→3 fallback chain — start with X/Twitter official demos"))

    # ── SHOT_LIST_VISUAL_DONE ───────────────────────────────────────────────
    elif state == "shot_list_visual_done":
        actions.append(_action("shot-list-4b-ii", priority=0))

    # ── SHOT_LIST_FITNESS_DONE ──────────────────────────────────────────────
    elif state == "shot_list_fitness_done":
        actions.append(_action("shot-list-4b-iii", priority=0))

    # ── SHOT_LIST_READY ─────────────────────────────────────────────────────
    elif state == "shot_list_ready":
        actions.append(_action("motion-intent", priority=0,
            parallel_label="parallel with asset-prep"))
        actions.append(_action("asset-prep", priority=0,
            parallel_label="parallel with motion-intent"))

    # ── PARALLEL STATES ─────────────────────────────────────────────────────
    elif state == "motion_done_awaiting_assets":
        actions.append(_action("asset-prep", priority=0,
            notes="Motion intent is done — asset prep is the last parallel task"))

    elif state == "assets_done_awaiting_motion":
        actions.append(_action("motion-intent", priority=0,
            notes="Asset prep is done — motion intent is the last parallel task"))

    # ── ASSETS_READY ────────────────────────────────────────────────────────
    elif state == "assets_ready":
        # Parity check note
        parity_note = "Parity checks will run before assembly begins"
        actions.append(_action("assemble-reel", priority=0, notes=parity_note))

    # ── ASSEMBLED ───────────────────────────────────────────────────────────
    elif state == "assembled":
        actions.append(NextAction(
            phase_key="preview",
            name="Preview Review (Phase 5b)",
            actor="human",
            command_hint="cd remotion && npx remotion studio",
            blocked=False,
            blocked_reason=None,
            creative_intent_required=False,
            optional=False,
            parallel_label=None,
            priority=0,
            notes=f"Scrub to 5 key frames. Approve: python -m lib.orchestrator approve {snap.slug} preview_passed",
        ))

    # ── PREVIEW_APPROVED ────────────────────────────────────────────────────
    elif state == "preview_approved":
        actions.append(_action("qa-reel", priority=0,
            notes="Parity checks run before QA begins"))

    # ── QA_PASSED ───────────────────────────────────────────────────────────
    elif state == "qa_passed":
        actions.append(_action("render", priority=0))

    # ── RENDERED ────────────────────────────────────────────────────────────
    elif state == "rendered":
        actions.append(_action("benchmark", priority=0,
            notes="Use training/benchmark-scorecard.md + projects/_shared/benchmark-review-template.md"))
        actions.append(_action("feedback-capture", priority=1,
            parallel_label="parallel with benchmark"))

    # ── Add feedback-capture suggestion after certain states ────────────────
    # (separate from the primary next actions)

    return sorted(actions, key=lambda a: (a.blocked, a.priority))


def _action(
    phase_key: str,
    priority: int = 0,
    notes: str = "",
    parallel_label: str | None = None,
    extra_blocked_reason: str | None = None,
) -> NextAction:
    """Create a NextAction from a PhaseSpec."""
    spec = PHASES.get(phase_key)
    if spec is None:
        return NextAction(
            phase_key=phase_key,
            name=phase_key,
            actor="unknown",
            command_hint="",
            blocked=True,
            blocked_reason=f"Unknown phase: {phase_key}",
            creative_intent_required=False,
            optional=False,
            parallel_label=parallel_label,
            priority=priority,
            notes=notes,
        )
    return NextAction(
        phase_key=phase_key,
        name=spec.name,
        actor=spec.actor,
        command_hint=spec.command_hint,
        blocked=extra_blocked_reason is not None,
        blocked_reason=extra_blocked_reason,
        creative_intent_required=spec.creative_intent_required,
        optional=spec.optional,
        parallel_label=parallel_label,
        priority=priority,
        notes=notes,
    )
