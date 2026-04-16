"""
Motion preset vocabulary and motion budget validation.

Two layers of vocabulary:

1. RENDERER_*  — the full enum the Remotion renderer accepts. Mirrors
   timeline.schema.json $defs.transition_preset.{enter,exit} and the
   union types in remotion/src/types.ts. Drift between these and Python
   = bug. lib/test_contracts.py asserts they stay aligned.

2. EDITORIAL_* — the curated subset from .claude/rules/visual-style.md
   "Motion Preset Vocabulary". This is what motion-intent and edit-plan
   should pick from. The renderer accepts the wider enum, but we keep
   editorial choices in the smaller set for consistency across reels.

The motion budget rule (1 hero / 1 support / 1 accent, max 3 per beat)
from .claude/rules/visual-style.md "Motion Budget Rule" is enforced by
validate_motion_budget().
"""

from __future__ import annotations

from dataclasses import dataclass


# ── Renderer-level enums (must mirror timeline.schema.json + types.ts) ─────

RENDERER_ENTER_PRESETS: frozenset[str] = frozenset({
    "punch", "slide-up", "slide-left", "zoom-in", "scale-pop",
    "scale-pop-overshoot", "glitch", "fade", "wipe-up",
    "zoom-through", "blur-dissolve", "luminance-sweep", "iris-reveal",
    "whip-pan", "smooth-push", "hard-cut", "flash-reset", "slide-stack",
})

RENDERER_EXIT_PRESETS: frozenset[str] = frozenset({
    "punch-out", "slide-down", "slide-right", "scale-down",
    "fade", "wipe-down",
    "zoom-through-out", "blur-out", "whip-out", "iris-close", "hard-cut",
})


# ── Editorial subsets (from .claude/rules/visual-style.md) ─────────────────

EDITORIAL_ENTER_PRESETS: frozenset[str] = frozenset({
    "wipe-up", "fade", "zoom-in", "scale-pop", "slide-up", "smooth-push", "punch",
})

EDITORIAL_EXIT_PRESETS: frozenset[str] = frozenset({
    "fade", "scale-down", "slide-down", "wipe-down",
})

# Editorial duration bounds (frames at 30fps), per visual-style.md.
ENTER_DUR_BOUNDS: tuple[int, int] = (3, 10)
EXIT_DUR_BOUNDS: tuple[int, int] = (2, 4)


# ── Beat categories and per-category preferences ───────────────────────────

BEAT_CATEGORIES: frozenset[str] = frozenset({
    "avatar", "demo", "concept", "return", "hook", "cta",
})

# Per-category recommended preset choices, organized by motion role.
# Source: .claude/rules/visual-style.md "Four Beat Categories" + hook/CTA
# guidance from same file.
#
# These are recommendations, not hard constraints. The Phase D motion_plan
# helper uses them to suggest defaults — final picks remain editorial.
_PREFERRED_PRESETS: dict[str, dict[str, tuple[str, ...]]] = {
    "avatar": {
        "hero":    ("scale-pop", "smooth-push", "fade"),
        "support": ("fade",),
        "accent":  ("scale-pop",),
    },
    "demo": {
        "hero":    ("wipe-up", "zoom-in", "scale-pop"),
        "support": ("fade",),
        "accent":  ("scale-pop",),
    },
    "concept": {
        "hero":    ("wipe-up", "fade", "zoom-in"),
        "support": ("fade", "smooth-push"),
        "accent":  ("scale-pop",),
    },
    "return": {
        "hero":    ("scale-pop", "smooth-push"),
        "support": ("fade",),
        "accent":  ("scale-pop",),
    },
    "hook": {
        "hero":    ("punch", "scale-pop", "wipe-up"),
        "support": ("fade",),
        "accent":  ("punch",),
    },
    "cta": {
        "hero":    ("smooth-push", "scale-pop"),
        "support": ("fade",),
        "accent":  ("scale-pop",),
    },
}


# ── Motion budget data model ───────────────────────────────────────────────

@dataclass(frozen=True)
class MotionEvent:
    """A single motion element on a beat.

    `kind` is editorial language ("focus-crop", "scale-entrance", "ken-burns").
    `preset` is the optional renderer preset name (e.g. "wipe-up") if this
    motion maps to a transition_preset on a timeline entry.
    `duration_frames` is the optional enter/exit duration in frames at 30fps.
    """
    kind: str
    preset: str | None = None
    duration_frames: int | None = None


@dataclass
class MotionBudget:
    """The 1 hero / 1 support / 1 accent rule, encoded as data.

    Hero is required for any beat with motion. Support and accent are optional.
    Total filled slot count must not exceed 3 (the rule from visual-style.md).
    """
    hero: MotionEvent | None = None
    support: MotionEvent | None = None
    accent: MotionEvent | None = None

    def used_slots(self) -> int:
        return sum(1 for slot in (self.hero, self.support, self.accent) if slot is not None)

    def events(self) -> list[MotionEvent]:
        return [e for e in (self.hero, self.support, self.accent) if e is not None]


# ── Validation functions ───────────────────────────────────────────────────

def is_editorial_enter(preset: str) -> bool:
    return preset in EDITORIAL_ENTER_PRESETS


def is_editorial_exit(preset: str) -> bool:
    return preset in EDITORIAL_EXIT_PRESETS


def is_renderer_enter(preset: str) -> bool:
    return preset in RENDERER_ENTER_PRESETS


def is_renderer_exit(preset: str) -> bool:
    return preset in RENDERER_EXIT_PRESETS


def validate_motion_budget(
    budget: MotionBudget,
    *,
    enforce_editorial: bool = True,
) -> list[str]:
    """Validate a motion budget against the rules in visual-style.md.

    Returns a list of error strings. Empty list = valid budget.

    Checks:
      - hero slot must be set (every beat needs at least one hero motion)
      - total filled slots <= 3
      - if a slot has a preset name, it must be in either the editorial enter
        set or the editorial exit set (when enforce_editorial=True), or
        in either renderer set otherwise
      - duration_frames, when set alongside a preset, must be within
        ENTER_DUR_BOUNDS or EXIT_DUR_BOUNDS depending on which set the
        preset belongs to
    """
    errors: list[str] = []

    if budget.hero is None:
        errors.append(
            "motion_budget.hero is required (every beat needs at least one hero motion)"
        )

    if budget.used_slots() > 3:
        errors.append(
            f"motion_budget has {budget.used_slots()} slots filled — max 3 "
            f"(1 hero + 1 support + 1 accent)"
        )

    enter_set = EDITORIAL_ENTER_PRESETS if enforce_editorial else RENDERER_ENTER_PRESETS
    exit_set = EDITORIAL_EXIT_PRESETS if enforce_editorial else RENDERER_EXIT_PRESETS
    label = "editorial" if enforce_editorial else "renderer"

    for role, event in (
        ("hero", budget.hero),
        ("support", budget.support),
        ("accent", budget.accent),
    ):
        if event is None or event.preset is None:
            continue
        in_enter = event.preset in enter_set
        in_exit = event.preset in exit_set
        if not (in_enter or in_exit):
            errors.append(
                f"motion_budget.{role}.preset {event.preset!r} is not in the "
                f"{label} preset set"
            )
            continue
        if event.duration_frames is not None:
            lo, hi = ENTER_DUR_BOUNDS if in_enter else EXIT_DUR_BOUNDS
            if not (lo <= event.duration_frames <= hi):
                errors.append(
                    f"motion_budget.{role}.duration_frames={event.duration_frames} "
                    f"outside bounds [{lo}, {hi}] for {label} preset {event.preset!r}"
                )

    return errors


def preferred_presets_for(beat_category: str) -> dict[str, tuple[str, ...]]:
    """Return recommended presets per role for a beat category.

    Returns an empty dict if the category is unknown. Used by the Phase D
    motion_plan helper to suggest defaults — not enforcement.
    """
    return dict(_PREFERRED_PRESETS.get(beat_category, {}))
