"""
lib/edit_plan/ — the editorial intermediate layer between beat-map and timeline.

Phase C scope:
  - model.py:     dataclasses for EditPlan, BeatPlan, etc.
  - validate.py:  hand-rolled validator with structured error codes
  - compile.py:   deterministic transformation EditPlan → timeline.json dict
  - reverse.py:   reverse-engineer an EditPlan from an existing timeline.json
                  (test-facing, used by parity tests)
  - canonical.py: canonicalization helpers for round-trip diffing
  - markdown.py:  human-readable edit-plan.md summary generator
  - cli.py:       CLI subcommands (validate, compile, summary, parity)

The compiler is opt-in via presence of output/edit-plan.json. When absent,
the existing direct-write path in the assemble-reel skill remains the
source of truth for timeline.json.

The compiler does not depend on a fully-loaded catalog: BeatPlans carry
selected_asset_filename inline, so legacy projects with broken catalogs
can still round-trip. Enrichment is optional; missing enrichment lowers
confidence rather than failing the build.
"""

from .model import (
    EditPlan,
    BeatPlan,
    CandidateAsset,
    MotionEvent,
    MotionBudget,
    ZoomMoment,
    EDIT_PLAN_SCHEMA_VERSION,
    COMPILER_VERSION,
)
from .validate import (
    EditPlanValidationError,
    validate_edit_plan,
    validate_edit_plan_dict,
)
from .compile import (
    CompileError,
    compile_edit_plan,
)
from .canonical import (
    canonicalize_timeline,
    diff_timelines,
)

__all__ = [
    # model
    "EditPlan",
    "BeatPlan",
    "CandidateAsset",
    "MotionEvent",
    "MotionBudget",
    "ZoomMoment",
    "EDIT_PLAN_SCHEMA_VERSION",
    "COMPILER_VERSION",
    # validate
    "EditPlanValidationError",
    "validate_edit_plan",
    "validate_edit_plan_dict",
    # compile
    "CompileError",
    "compile_edit_plan",
    # canonical
    "canonicalize_timeline",
    "diff_timelines",
]
