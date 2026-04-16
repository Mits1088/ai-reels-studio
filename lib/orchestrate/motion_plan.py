"""
Motion planner — assigns beat category and motion budget per beat.

For each beat:
  - Classifies beat_category (hook/setup/demo/proof/concept/return/avatar/cta)
    using either the legacy 'intent' field or the schema 'visual_intent' field.
  - Picks preferred presets from lib.grammar.preferred_presets_for(category).
  - Builds a MotionBudget (hero/support/accent) per the editorial rule.
  - Validates the budget with lib.grammar.validate_motion_budget.
  - Surfaces violations clearly.
  - Returns confidence based on category certainty + validation result.

Pure functions throughout — no I/O in the planning core.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from lib.grammar import (
    BEAT_CATEGORIES,
    MotionBudget,
    MotionEvent,
    preferred_presets_for,
    validate_motion_budget,
)


PLANNER_VERSION = "lib.orchestrate.motion_plan@1.0.0"


# Per-category default motion budget recipe.
# Each entry: (hero_kind, support_kind, accent_kind, hero_dur, support_dur, accent_dur)
# kinds are editorial language; presets come from preferred_presets_for(category)[role][0]
BEAT_CATEGORY_DEFAULTS: dict[str, dict] = {
    "hook": {
        "hero":    {"kind": "punch-in", "duration_frames": 5},
        "support": {"kind": "fade",     "duration_frames": 4},
        "accent":  {"kind": "punch",    "duration_frames": 4},
    },
    "setup": {
        "hero":    {"kind": "scale-settle", "duration_frames": 6},
        "support": {"kind": "fade",         "duration_frames": 4},
        "accent":  None,
    },
    "demo": {
        "hero":    {"kind": "wipe-reveal",  "duration_frames": 5},
        "support": {"kind": "fade",         "duration_frames": 4},
        "accent":  {"kind": "scale-pulse",  "duration_frames": 4},
    },
    "proof": {
        "hero":    {"kind": "zoom-focus",   "duration_frames": 5},
        "support": {"kind": "fade",         "duration_frames": 4},
        "accent":  {"kind": "scale-pulse",  "duration_frames": 4},
    },
    "concept": {
        "hero":    {"kind": "wipe-reveal",  "duration_frames": 5},
        "support": {"kind": "fade",         "duration_frames": 4},
        "accent":  None,
    },
    "return": {
        "hero":    {"kind": "scale-settle", "duration_frames": 6},
        "support": {"kind": "fade",         "duration_frames": 4},
        "accent":  None,
    },
    "avatar": {
        "hero":    {"kind": "scale-settle", "duration_frames": 5},
        "support": {"kind": "fade",         "duration_frames": 4},
        "accent":  None,
    },
    "cta": {
        "hero":    {"kind": "smooth-push",  "duration_frames": 6},
        "support": {"kind": "fade",         "duration_frames": 4},
        "accent":  {"kind": "scale-pulse",  "duration_frames": 4},
    },
    "trust": {
        "hero":    {"kind": "scale-settle", "duration_frames": 5},
        "support": {"kind": "fade",         "duration_frames": 4},
        "accent":  None,
    },
    "recap": {
        "hero":    {"kind": "wipe-reveal",  "duration_frames": 5},
        "support": {"kind": "fade",         "duration_frames": 4},
        "accent":  None,
    },
}


# ── Data classes ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BeatMotionPlan:
    beat_id: str
    beat_category: str
    motion_budget: dict             # serialized MotionBudget
    confidence: float
    rationale: str
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "beat_id":       self.beat_id,
            "beat_category": self.beat_category,
            "motion_budget": self.motion_budget,
            "confidence":    round(self.confidence, 4),
            "rationale":     self.rationale,
            "violations":    list(self.violations),
        }


# ── Beat category classification ──────────────────────────────────────────


_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "hook":    ("hook", "intro", "open"),
    "demo":    ("demo", "interaction", "interactive", "show"),
    "proof":   ("proof", "stat", "result", "number", "benchmark"),
    "trust":   ("trust", "credibility", "authority", "validation"),
    "cta":     ("cta", "follow", "subscribe", "comment", "outro"),
    "recap":   ("recap", "reframe", "summary", "wrap"),
    "setup":   ("setup", "context", "background"),
    "concept": ("concept", "explain", "mechanism"),
    "return":  ("return",),
    "avatar":  ("avatar", "presenter", "direct"),
}


def classify_beat_category(beat: dict, position: int, total_beats: int) -> tuple[str, float]:
    """Return (category, confidence). Confidence reflects how unambiguous the classification is.

    Uses, in order:
      1. Explicit 'intent' field (legacy beat-map format)
      2. Explicit 'visual_intent' field (schema beat-map format)
      3. Position heuristic (first → hook, last → cta)
      4. Default → context

    Confidence:
      1.0 — explicit field exact match
      0.8 — explicit field keyword match
      0.6 — position heuristic
      0.4 — default fallback
    """
    raw = beat.get("intent") or beat.get("visual_intent") or ""
    raw = raw.strip().lower()

    if raw:
        # Exact match against known categories
        if raw in BEAT_CATEGORIES or raw in _CATEGORY_KEYWORDS:
            # Map "context" to "concept" to fit the grammar
            mapped = "concept" if raw == "context" else raw
            if mapped in BEAT_CATEGORIES:
                return (mapped, 1.0)

        # Keyword match
        for cat, keywords in _CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in raw:
                    if cat in BEAT_CATEGORIES:
                        return (cat, 0.8)

    # Position heuristic
    if position == 0:
        return ("hook", 0.6)
    if position == total_beats - 1:
        return ("cta", 0.6)
    return ("concept", 0.4)


# ── Motion budget assembly ────────────────────────────────────────────────


def _build_motion_budget(category: str) -> MotionBudget:
    """Build a MotionBudget for a beat category using preferred_presets_for."""
    prefs = preferred_presets_for(category)
    defaults = BEAT_CATEGORY_DEFAULTS.get(category, BEAT_CATEGORY_DEFAULTS["concept"])

    def _make(role: str) -> MotionEvent | None:
        cfg = defaults.get(role)
        if cfg is None:
            return None
        preset_options = prefs.get(role, ())
        preset = preset_options[0] if preset_options else None
        return MotionEvent(
            kind=cfg["kind"],
            preset=preset,
            duration_frames=cfg.get("duration_frames"),
        )

    hero = _make("hero")
    if hero is None:
        # Fallback — every budget needs a hero
        hero = MotionEvent(kind="settle")
    return MotionBudget(
        hero=hero,
        support=_make("support"),
        accent=_make("accent"),
    )


def plan_beat_motion(beat: dict, position: int, total_beats: int) -> BeatMotionPlan:
    """Pure function. Plan motion for one beat."""
    category, cat_confidence = classify_beat_category(beat, position, total_beats)
    budget = _build_motion_budget(category)
    violations = validate_motion_budget(budget)

    # Confidence is the product of category certainty and validation result
    if violations:
        # Some violations = lower confidence; only block if hero is missing
        hard_block = any("hero" in v for v in violations)
        confidence = 0.0 if hard_block else max(0.2, cat_confidence * 0.5)
    else:
        confidence = cat_confidence

    rationale_parts = [
        f"category={category!r} (confidence {cat_confidence:.2f})",
        f"hero={budget.hero.kind!r}",
    ]
    if budget.support:
        rationale_parts.append(f"support={budget.support.kind!r}")
    if budget.accent:
        rationale_parts.append(f"accent={budget.accent.kind!r}")
    rationale = "; ".join(rationale_parts)

    return BeatMotionPlan(
        beat_id=beat.get("id", ""),
        beat_category=category,
        motion_budget=_serialize_budget(budget),
        confidence=confidence,
        rationale=rationale,
        violations=list(violations),
    )


def _serialize_budget(budget: MotionBudget) -> dict:
    out: dict = {"hero": _serialize_event(budget.hero)}
    if budget.support is not None:
        out["support"] = _serialize_event(budget.support)
    if budget.accent is not None:
        out["accent"] = _serialize_event(budget.accent)
    return out


def _serialize_event(event: MotionEvent) -> dict:
    d: dict = {"kind": event.kind}
    if event.preset is not None:
        d["preset"] = event.preset
    if event.duration_frames is not None:
        d["duration_frames"] = event.duration_frames
    return d


def plan_motion(beats: list[dict]) -> list[BeatMotionPlan]:
    """Pure function. Plan motion for every beat in a beat-map."""
    total = len(beats)
    return [plan_beat_motion(beat, i, total) for i, beat in enumerate(beats)]


# ── Project-level entry ───────────────────────────────────────────────────


def plan_motion_for_project(project_dir: Path) -> dict:
    bm_path = project_dir / "audio" / "beat-map.json"
    if not bm_path.exists():
        return {
            "project": project_dir.name,
            "skipped": True,
            "reason": "no beat-map.json",
            "beats": [],
        }
    with open(bm_path, "r", encoding="utf-8") as f:
        bm = json.load(f)

    beats = bm.get("beats", [])
    plans = plan_motion(beats)

    by_category: dict[str, int] = {}
    violations_total = 0
    for p in plans:
        by_category[p.beat_category] = by_category.get(p.beat_category, 0) + 1
        violations_total += len(p.violations)

    return {
        "schema_version": 1,
        "project": project_dir.name,
        "planner_version": PLANNER_VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "totals": {
            "beats":            len(plans),
            "by_category":      by_category,
            "violations_total": violations_total,
            "high_confidence":  sum(1 for p in plans if p.confidence >= 0.8),
            "low_confidence":   sum(1 for p in plans if p.confidence < 0.5),
        },
        "beats": [p.to_dict() for p in plans],
    }
