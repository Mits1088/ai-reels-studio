"""
Reverse-engineer an EditPlan from an existing timeline.json.

Phase C uses this strictly for parity testing. The reverse-engineer captures
all timeline lanes verbatim into EditPlan.verbatim_lanes so the round-trip
is byte-clean. It also emits one synthetic BeatPlan per beat in the
beat_map so the resulting EditPlan structurally validates.

Template inference is intentionally minimal: every beat gets a default
"placeholder" template_id and a synthetic motion_budget. This is fine
because parity tests use the verbatim path — the BeatPlans are metadata
that the compiler does not consult when verbatim_lanes is set.

This module is not exported from lib/edit_plan/__init__.py — it lives
purely as a parity helper. Phase D's orchestrator will produce real
BeatPlans driven by editorial decisions, not by reverse-engineering.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .model import (
    EditPlan,
    BeatPlan,
    MotionBudget,
    MotionEvent,
    CandidateAsset,
    EDIT_PLAN_SCHEMA_VERSION,
    COMPILER_VERSION,
)


# Placeholder template — does not need to exist in the registry because
# parity validation runs without a registry.
_PLACEHOLDER_TEMPLATE_ID = "legacy-verbatim"
_PLACEHOLDER_AVATAR_MODE = "legacy"
_PLACEHOLDER_CAPTION_MODE = "standard"
_PLACEHOLDER_SPLIT_RATIO = "40/60"


def reverse_engineer(
    timeline: dict,
    beat_map: dict,
    project_slug: str,
    *,
    style: str | None = None,
) -> EditPlan:
    """Build an EditPlan from an existing timeline.json + beat_map.

    Strategy:
      - All timeline lanes are captured verbatim into EditPlan.verbatim_lanes
      - One synthetic BeatPlan is emitted per beat in beat_map
      - BeatPlans carry placeholder template/avatar/caption metadata
      - Top-level fields (audio, avatar_file, project, style) are captured
        from the timeline if present. style is preserved exactly as found —
        absent in source ⇒ absent in EditPlan.
    """
    beats_in_map = beat_map.get("beats", [])
    # Pass through the source style verbatim. If the timeline has no style
    # field, EditPlan.style stays None and compile() will not emit one.
    captured_style = timeline.get("style", style)

    # Capture verbatim lanes
    verbatim_lanes: dict[str, list[dict]] = {}
    raw_lanes = timeline.get("lanes", {})
    for lane_name in (
        "avatar", "demo", "broll", "support",
        "captions", "sfx", "music", "overlays",
    ):
        if lane_name in raw_lanes and isinstance(raw_lanes[lane_name], list):
            verbatim_lanes[lane_name] = [dict(e) for e in raw_lanes[lane_name]]

    # Build a synthetic BeatPlan per beat
    beat_plans: list[BeatPlan] = []
    for beat in beats_in_map:
        bid = beat.get("id")
        if not bid:
            continue
        # Try to find a content asset for this beat across content lanes
        selected_filename = _find_first_asset_for_beat(raw_lanes, bid)
        beat_plans.append(_make_synthetic_beat_plan(bid, selected_filename))

    return EditPlan(
        schema_version=EDIT_PLAN_SCHEMA_VERSION,
        project_slug=project_slug,
        style=captured_style,
        beats=tuple(beat_plans),
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        compiler_version=COMPILER_VERSION,
        audio=timeline.get("audio"),
        avatar_file=timeline.get("avatar_file"),
        project=timeline.get("project"),
        total_duration=timeline.get("total_duration"),
        meta={"reversed_from": "existing timeline.json", "phase": "C-parity"},
        verbatim_lanes=verbatim_lanes,
    )


def _find_first_asset_for_beat(raw_lanes: dict, beat_id: str) -> str | None:
    """Look across content lanes for an entry whose beat_id matches.

    Returns the asset filename of the first match, or None if no content
    asset is associated with this beat (e.g. avatar-only beat).
    """
    for lane_name in ("demo", "broll", "support"):
        for entry in raw_lanes.get(lane_name, []) or []:
            if entry.get("beat_id") == beat_id and entry.get("asset"):
                return entry["asset"]
    return None


def _make_synthetic_beat_plan(
    beat_id: str, selected_filename: str | None
) -> BeatPlan:
    """Generate a placeholder BeatPlan that satisfies the schema.

    All Phase D mandatory fields (candidate_assets, selected_asset_id,
    selection_confidence, selection_reason, fallback_asset_ids,
    human_review_required) are populated with synthetic values that
    indicate the plan was reverse-engineered, not authored editorially.
    """
    candidate: tuple[CandidateAsset, ...] = ()
    selected_id: str | None = None
    if selected_filename:
        # Use the filename as a stand-in asset_id (no catalog lookup)
        selected_id = "reversed-" + beat_id
        candidate = (
            CandidateAsset(
                asset_id=selected_id,
                score=1.0,
                reason="reversed from existing timeline.json",
            ),
        )

    return BeatPlan(
        beat_id=beat_id,
        template_id=_PLACEHOLDER_TEMPLATE_ID,
        avatar_mode=_PLACEHOLDER_AVATAR_MODE,
        caption_mode=_PLACEHOLDER_CAPTION_MODE,
        split_ratio=_PLACEHOLDER_SPLIT_RATIO,
        candidate_assets=candidate,
        selected_asset_id=selected_id,
        selection_confidence=1.0,
        selection_reason="reverse-engineered from finalized timeline",
        fallback_asset_ids=(),
        human_review_required=False,
        motion_budget=MotionBudget(
            hero=MotionEvent(kind="reversed", preset=None, duration_frames=None),
        ),
        rationale="placeholder — generated by lib.edit_plan.reverse for parity testing",
        selected_asset_filename=selected_filename,
    )
