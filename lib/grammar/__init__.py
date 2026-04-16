"""
Grammar module — vocabulary and validation for editorial planning.

This package is the single source of truth for:
  - The 7 proof classes and their escalation order (proof_classes.py)
  - The layout template registry, loaded from
    training/derived/template-registry.json (templates.py)
  - The motion preset vocabulary — both renderer-accepted and editorially
    curated — with motion budget validation (motion_presets.py)

Phase A scope: vocabulary and validation only. Nothing in this package
mutates project state, reads timelines, or runs in the render path. The
deterministic compiler in Phase C (lib/edit_plan/) will consume these
vocabularies to compile edit-plan.json into timeline.json.

Drift detection: lib/test_contracts.py asserts the Python enums here stay
aligned with lib/schemas/timeline.schema.json and lib/schemas/edit_plan.schema.json.
"""

from .proof_classes import (
    PROOF_CLASSES,
    PROOF_ORDER,
    is_valid_proof_class,
    validate_proof_arc,
)
from .templates import (
    Template,
    TemplateRegistry,
    load_template_registry,
    VALID_TEMPLATE_CLASSES,
    VALID_CAPTION_MODES,
    DEFAULT_REGISTRY_PATH,
    DEFAULT_CAPTION_MODES_PATH,
)
from .motion_presets import (
    RENDERER_ENTER_PRESETS,
    RENDERER_EXIT_PRESETS,
    EDITORIAL_ENTER_PRESETS,
    EDITORIAL_EXIT_PRESETS,
    ENTER_DUR_BOUNDS,
    EXIT_DUR_BOUNDS,
    BEAT_CATEGORIES,
    MotionEvent,
    MotionBudget,
    validate_motion_budget,
    preferred_presets_for,
    is_editorial_enter,
    is_editorial_exit,
    is_renderer_enter,
    is_renderer_exit,
)

__all__ = [
    # proof_classes
    "PROOF_CLASSES",
    "PROOF_ORDER",
    "is_valid_proof_class",
    "validate_proof_arc",
    # templates
    "Template",
    "TemplateRegistry",
    "load_template_registry",
    "VALID_TEMPLATE_CLASSES",
    "VALID_CAPTION_MODES",
    "DEFAULT_REGISTRY_PATH",
    "DEFAULT_CAPTION_MODES_PATH",
    # motion_presets
    "RENDERER_ENTER_PRESETS",
    "RENDERER_EXIT_PRESETS",
    "EDITORIAL_ENTER_PRESETS",
    "EDITORIAL_EXIT_PRESETS",
    "ENTER_DUR_BOUNDS",
    "EXIT_DUR_BOUNDS",
    "BEAT_CATEGORIES",
    "MotionEvent",
    "MotionBudget",
    "validate_motion_budget",
    "preferred_presets_for",
    "is_editorial_enter",
    "is_editorial_exit",
    "is_renderer_enter",
    "is_renderer_exit",
]
