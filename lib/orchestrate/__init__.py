"""
lib/orchestrate/ — deterministic editorial planning helpers.

Phase D scope: explainable, opt-in helpers that enrich edit-plan creation
without replacing human judgment. They produce structured, machine-readable
artifacts that humans or skills can review and use to drive Phase C's
edit-plan compiler.

Modules:
  - match_assets.py:  rank candidate assets per beat with explicit score breakdowns
  - motion_plan.py:   classify beat category and assign motion_budget per Phase A grammar
  - gap_owner.py:     classify gaps between beats and assign ownership
  - cli.py:           CLI subcommands (match, motion, plan)

Key design rules:
  - Pure functions wherever possible — no I/O in the scoring core
  - Every result carries the 6 mandatory editorial fields (candidate_assets,
    selected_asset_id, selection_confidence, selection_reason,
    fallback_asset_ids, human_review_required)
  - Score breakdowns are exposed per beat — no opaque "confidence" numbers
  - Stable tie-breaking (alphabetical asset_id)
  - Graceful degradation when enrichment is absent: missing data lowers
    confidence rather than failing the planner
  - Outputs are advisory: nothing in the existing render path consumes them
"""

from .match_assets import (
    ScoreBreakdown,
    CandidateMatch,
    BeatMatch,
    SCORE_WEIGHTS,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_LOW,
    score_asset_for_beat,
    match_assets,
    match_assets_for_project,
    MATCHER_VERSION,
)
from .motion_plan import (
    BeatMotionPlan,
    BEAT_CATEGORY_DEFAULTS,
    classify_beat_category,
    plan_motion,
    plan_motion_for_project,
    PLANNER_VERSION,
)
from .gap_owner import (
    GapAssignment,
    OWNERSHIP_MICRO,
    OWNERSHIP_SEAM,
    OWNERSHIP_BREATHING,
    assign_gaps,
    assign_gaps_for_project,
)

__all__ = [
    # match_assets
    "ScoreBreakdown",
    "CandidateMatch",
    "BeatMatch",
    "SCORE_WEIGHTS",
    "CONFIDENCE_HIGH",
    "CONFIDENCE_MEDIUM",
    "CONFIDENCE_LOW",
    "score_asset_for_beat",
    "match_assets",
    "match_assets_for_project",
    "MATCHER_VERSION",
    # motion_plan
    "BeatMotionPlan",
    "BEAT_CATEGORY_DEFAULTS",
    "classify_beat_category",
    "plan_motion",
    "plan_motion_for_project",
    "PLANNER_VERSION",
    # gap_owner
    "GapAssignment",
    "OWNERSHIP_MICRO",
    "OWNERSHIP_SEAM",
    "OWNERSHIP_BREATHING",
    "assign_gaps",
    "assign_gaps_for_project",
]
