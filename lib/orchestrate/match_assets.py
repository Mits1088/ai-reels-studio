"""
Asset matcher — deterministic, explainable per-beat asset scoring.

Given a beat-map and a catalog, produces a BeatMatch per beat with:
  - candidate_assets: ranked list with explicit ScoreBreakdown
  - selected_asset_id / selected_asset_filename: top candidate (catalog-free)
  - selection_confidence: top candidate's final_score
  - selection_reason: human-readable explanation
  - fallback_asset_ids: next 3 candidates
  - human_review_required: when confidence is low or no good match

Score factors (weights chosen so positive factors sum to 1.0):
  role_fit          0.25  — asset role matches beat intent
  proof_fit         0.20  — proof_class hint matches asset's editorial tags
  aspect_fit        0.15  — asset aspect ratio fits the beat's display intent
  duration_fit      0.10  — asset duration covers the beat duration
  legibility        0.10  — text density appropriateness for the beat intent
  focal_point       0.10  — focal point quality
  enrichment_bonus  0.10  — bonus for fully-enriched assets
                            ──────
                            1.00
quality_penalty   subtract  — quality_flags reduce the final score
                              file_missing eliminates (-1.0)

Confidence thresholds:
  HIGH    >= 0.70  — use top, no review needed
  MEDIUM  >= 0.50  — use top, optional review
  LOW     <  0.50  — use top, mandatory review
  NONE    no candidates above 0.30 — selected = None, mandatory review

Tie-break: alphabetical asset_id (stable, deterministic).

Graceful degradation: missing enrichment → factors that depend on enrichment
return 0.5 (neutral). The matcher never fails on missing data; it only
lowers confidence and surfaces a review reason.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lib.capture.catalog import AssetEntry, Catalog, load_catalog


MATCHER_VERSION = "lib.orchestrate.match_assets@1.0.0"

# Score weights — positive factors sum to 1.0
SCORE_WEIGHTS: dict[str, float] = {
    "role_fit":         0.25,
    "proof_fit":        0.20,
    "aspect_fit":       0.15,
    "duration_fit":     0.10,
    "legibility":       0.10,
    "focal_point":      0.10,
    "enrichment_bonus": 0.10,
}

# Confidence thresholds
CONFIDENCE_HIGH = 0.70
CONFIDENCE_MEDIUM = 0.50
CONFIDENCE_LOW = 0.30  # below this, no candidates are selected

# Quality flag penalties (subtracted from final_score)
QUALITY_PENALTIES: dict[str, float] = {
    "low_resolution":       0.10,
    "no_audio_track":       0.05,
    "non_standard_fps":     0.05,
    "non_standard_pix_fmt": 0.05,
    "browser_chrome_likely": 0.10,
    "wrong_orientation":    0.10,
    "private_data":         0.20,
    "file_missing":         1.00,  # eliminates
}

# Asset roles that are NEVER content candidates (avatar / sfx / music / background)
NON_CONTENT_ROLES = {"avatar", "sfx", "music", "background"}

# Mapping from beat intent → preferred content roles (in priority order)
INTENT_ROLE_PREFERENCE: dict[str, tuple[str, ...]] = {
    "hook":    ("broll", "demo", "support"),
    "setup":   ("support", "broll", "demo"),
    "demo":    ("demo", "broll", "support"),
    "proof":   ("demo", "support", "broll"),
    "context": ("support", "broll", "demo"),
    "trust":   ("support", "demo"),
    "recap":   ("support", "broll"),
    "cta":     ("support", "broll"),
    "mechanism": ("demo", "support"),
}

# Mapping from beat intent → expected display mode (drives aspect_fit)
INTENT_DISPLAY: dict[str, str] = {
    "hook":     "split-screen",
    "setup":    "split-screen",
    "demo":     "center-full",
    "proof":    "center-full",
    "context":  "split-screen",
    "trust":    "split-screen",
    "recap":    "center-full",
    "cta":      "split-screen",
    "mechanism": "center-full",
}


# ── Data classes ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ScoreBreakdown:
    """Explicit per-factor score breakdown for one (asset, beat) pairing."""
    role_fit:         float
    proof_fit:        float
    aspect_fit:       float
    duration_fit:     float
    legibility:       float
    focal_point:      float
    enrichment_bonus: float
    quality_penalty:  float
    final_score:      float

    def to_dict(self) -> dict:
        return {
            "role_fit":         round(self.role_fit, 4),
            "proof_fit":        round(self.proof_fit, 4),
            "aspect_fit":       round(self.aspect_fit, 4),
            "duration_fit":     round(self.duration_fit, 4),
            "legibility":       round(self.legibility, 4),
            "focal_point":      round(self.focal_point, 4),
            "enrichment_bonus": round(self.enrichment_bonus, 4),
            "quality_penalty":  round(self.quality_penalty, 4),
            "final_score":      round(self.final_score, 4),
        }


@dataclass(frozen=True)
class CandidateMatch:
    """One scored asset candidate for a beat."""
    asset_id: str
    asset_filename: str
    breakdown: ScoreBreakdown
    score: float
    reason: str

    def to_dict(self) -> dict:
        return {
            "asset_id":       self.asset_id,
            "asset_filename": self.asset_filename,
            "score":          round(self.score, 4),
            "score_breakdown": self.breakdown.to_dict(),
            "reason":         self.reason,
        }


@dataclass
class BeatMatch:
    """The matcher's decision for one beat — carries all 6 mandatory fields."""
    beat_id: str
    candidate_assets: list[CandidateMatch]
    selected_asset_id: str | None
    selected_asset_filename: str | None
    selection_confidence: float
    selection_reason: str
    fallback_asset_ids: list[str]
    human_review_required: bool
    review_reason: str | None
    enrichment_status: str  # 'full' | 'partial' | 'none' (across all candidates)

    def to_dict(self) -> dict:
        return {
            "beat_id":               self.beat_id,
            "candidate_assets":      [c.to_dict() for c in self.candidate_assets],
            "selected_asset_id":     self.selected_asset_id,
            "selected_asset_filename": self.selected_asset_filename,
            "selection_confidence":  round(self.selection_confidence, 4),
            "selection_reason":      self.selection_reason,
            "fallback_asset_ids":    list(self.fallback_asset_ids),
            "human_review_required": self.human_review_required,
            "review_reason":         self.review_reason,
            "enrichment_status":     self.enrichment_status,
        }


# ── Beat introspection (legacy + schema-conforming) ──────────────────────


def _beat_intent(beat: dict, position: int, total_beats: int) -> str:
    """Extract beat intent from either the legacy 'intent' field or schema 'visual_intent'.

    Falls back to position heuristics:
      - first beat → hook
      - last beat → cta
      - else → context
    """
    raw = beat.get("intent") or beat.get("visual_intent") or ""
    raw = raw.strip().lower()
    if raw:
        # Normalize a few common variants
        if raw in ("hook", "setup", "proof", "demo", "mechanism", "trust",
                   "recap", "context", "cta"):
            return raw
        if "hook" in raw:
            return "hook"
        if "demo" in raw or "interaction" in raw:
            return "demo"
        if "proof" in raw or "stat" in raw or "result" in raw:
            return "proof"
        if "trust" in raw or "credibility" in raw:
            return "trust"
        if "cta" in raw or "follow" in raw or "subscribe" in raw:
            return "cta"
        if "recap" in raw or "reframe" in raw:
            return "recap"
        if "setup" in raw:
            return "setup"

    # Position fallback
    if position == 0:
        return "hook"
    if position == total_beats - 1:
        return "cta"
    return "context"


def _beat_duration(beat: dict) -> float:
    try:
        return float(beat.get("end", 0)) - float(beat.get("start", 0))
    except (TypeError, ValueError):
        return 0.0


# ── Asset filtering ──────────────────────────────────────────────────────


def _is_content_candidate(asset: AssetEntry) -> bool:
    """Filter out assets that aren't content (avatar/sfx/music/background)."""
    if not asset.filename:
        return False
    if asset.role in NON_CONTENT_ROLES:
        return False
    return True


def _enrichment_status(asset: AssetEntry) -> str:
    e = asset.enrichment if isinstance(asset.enrichment, dict) else None
    if not e:
        return "none"
    s = e.get("status", "none")
    if s in ("full", "partial"):
        return s
    return "none"


# ── Score factors (each returns float in [0, 1]) ─────────────────────────


def _score_role_fit(asset: AssetEntry, intent: str) -> float:
    pref = INTENT_ROLE_PREFERENCE.get(intent, ("demo", "support", "broll"))
    if asset.role in pref:
        # 1.0 for first-choice, 0.7 for second, 0.4 for third+
        idx = pref.index(asset.role)
        return [1.0, 0.7, 0.4][min(idx, 2)]
    return 0.2  # not a preferred role for this intent, but still usable


def _score_proof_fit(asset: AssetEntry, intent: str) -> float:
    """Use enrichment.editorial_tags to match asset's proof intent. Neutral on missing data."""
    e = asset.enrichment if isinstance(asset.enrichment, dict) else None
    if not e:
        return 0.5  # neutral when no enrichment

    tags = e.get("editorial_tags", []) or []
    if not isinstance(tags, list) or not tags:
        return 0.5

    # Heuristic: tags that contain the intent string score 1.0
    intent_lower = intent.lower()
    for tag in tags:
        if isinstance(tag, str) and intent_lower in tag.lower():
            return 1.0

    # Tags exist but no intent match → 0.4 (slightly below neutral)
    return 0.4


def _score_aspect_fit(asset: AssetEntry, intent: str) -> float:
    """Aspect ratio fit against the expected display mode for this intent."""
    e = asset.enrichment if isinstance(asset.enrichment, dict) else None
    if not e:
        return 0.5

    decimal = e.get("aspect_ratio_decimal")
    if decimal is None:
        # Try dimensions fallback
        dims = asset.dimensions if isinstance(asset.dimensions, dict) else None
        if dims and dims.get("w") and dims.get("h"):
            decimal = dims["w"] / dims["h"]
        else:
            return 0.5

    expected_display = INTENT_DISPLAY.get(intent, "split-screen")
    # split-screen → favors square-ish (0.75–1.5)
    # center-full → favors landscape (>1.5)
    if expected_display == "split-screen":
        if 0.75 <= decimal <= 1.5:
            return 1.0
        if 0.5 <= decimal <= 2.0:
            return 0.7
        return 0.4
    elif expected_display == "center-full":
        if decimal >= 1.5:
            return 1.0
        if decimal >= 1.0:
            return 0.6
        return 0.3
    return 0.5


def _score_duration_fit(asset: AssetEntry, beat_duration: float) -> float:
    """For videos: must cover beat duration. For images: always 1.0 (can hold)."""
    if asset.type == "image":
        return 1.0
    if asset.duration_s is None or asset.duration_s <= 0:
        return 0.5  # unknown — neutral
    if asset.duration_s >= beat_duration:
        return 1.0
    # Linear penalty: 0.5x duration → 0.0
    ratio = asset.duration_s / beat_duration if beat_duration > 0 else 0
    return max(0.0, ratio)


def _score_legibility(asset: AssetEntry, intent: str) -> float:
    """Text density appropriateness for the beat intent."""
    e = asset.enrichment if isinstance(asset.enrichment, dict) else None
    if not e:
        return 0.5

    text_block = e.get("text", {}) or {}
    if not isinstance(text_block, dict):
        return 0.5
    score = text_block.get("score")
    if score is None:
        return 0.5

    try:
        text_density = float(score)
    except (TypeError, ValueError):
        return 0.5

    # Demo / proof / mechanism → text-heavy is GOOD (UI screenshots)
    # Hook / setup / cta → text-heavy is BAD (competes with overlays)
    text_loving = {"demo", "proof", "mechanism", "trust"}
    text_avoiding = {"hook", "setup", "cta"}

    if intent in text_loving:
        return min(1.0, 0.5 + text_density * 0.5)  # high density rewarded
    if intent in text_avoiding:
        return max(0.0, 1.0 - text_density * 0.6)  # high density punished
    return 0.5


def _score_focal_point(asset: AssetEntry) -> float:
    e = asset.enrichment if isinstance(asset.enrichment, dict) else None
    if not e:
        return 0.5
    fp = e.get("focal_point")
    if not isinstance(fp, dict):
        return 0.5
    source = fp.get("source", "center")
    return {
        "manual":     1.0,
        "face":       0.85,
        "text-block": 0.75,
        "center":     0.5,
    }.get(source, 0.5)


def _score_enrichment_bonus(asset: AssetEntry) -> float:
    status = _enrichment_status(asset)
    return {"full": 1.0, "partial": 0.5, "none": 0.0}[status]


def _quality_penalty(asset: AssetEntry) -> float:
    e = asset.enrichment if isinstance(asset.enrichment, dict) else None
    if not e:
        return 0.0
    flags = e.get("quality_flags", []) or []
    if not isinstance(flags, list):
        return 0.0
    total = 0.0
    for flag in flags:
        total += QUALITY_PENALTIES.get(flag, 0.0)
    return min(total, 1.0)


# ── Public scoring API ────────────────────────────────────────────────────


def score_asset_for_beat(asset: AssetEntry, beat: dict, position: int, total_beats: int) -> ScoreBreakdown:
    """Score one asset against one beat. Pure function — no I/O.

    Returns a ScoreBreakdown with all 8 factors plus the final clamped score.
    """
    intent = _beat_intent(beat, position, total_beats)
    duration = _beat_duration(beat)

    role_fit         = _score_role_fit(asset, intent)
    proof_fit        = _score_proof_fit(asset, intent)
    aspect_fit       = _score_aspect_fit(asset, intent)
    duration_fit     = _score_duration_fit(asset, duration)
    legibility       = _score_legibility(asset, intent)
    focal_point      = _score_focal_point(asset)
    enrichment_bonus = _score_enrichment_bonus(asset)
    quality_penalty  = _quality_penalty(asset)

    weighted = (
        role_fit         * SCORE_WEIGHTS["role_fit"] +
        proof_fit        * SCORE_WEIGHTS["proof_fit"] +
        aspect_fit       * SCORE_WEIGHTS["aspect_fit"] +
        duration_fit     * SCORE_WEIGHTS["duration_fit"] +
        legibility       * SCORE_WEIGHTS["legibility"] +
        focal_point      * SCORE_WEIGHTS["focal_point"] +
        enrichment_bonus * SCORE_WEIGHTS["enrichment_bonus"]
    )
    final = max(0.0, min(1.0, weighted - quality_penalty))

    return ScoreBreakdown(
        role_fit=role_fit,
        proof_fit=proof_fit,
        aspect_fit=aspect_fit,
        duration_fit=duration_fit,
        legibility=legibility,
        focal_point=focal_point,
        enrichment_bonus=enrichment_bonus,
        quality_penalty=quality_penalty,
        final_score=final,
    )


def _explain_breakdown(breakdown: ScoreBreakdown, asset: AssetEntry, intent: str) -> str:
    """Compact human-readable reason for a candidate."""
    parts = []
    if breakdown.role_fit >= 0.9:
        parts.append(f"role={asset.role!r} fits intent={intent!r}")
    elif breakdown.role_fit < 0.5:
        parts.append(f"role={asset.role!r} weak for intent={intent!r}")
    if breakdown.aspect_fit >= 0.9:
        parts.append("aspect-ratio matches display mode")
    elif breakdown.aspect_fit < 0.5:
        parts.append("aspect-ratio mismatch")
    if breakdown.duration_fit < 0.5:
        parts.append("duration too short")
    if breakdown.quality_penalty > 0:
        parts.append(f"quality_penalty={breakdown.quality_penalty:.2f}")
    if breakdown.enrichment_bonus == 0:
        parts.append("no enrichment data")
    return "; ".join(parts) if parts else "neutral defaults across factors"


# ── Top-level matching ────────────────────────────────────────────────────


def match_assets(beats: list[dict], catalog: Catalog) -> list[BeatMatch]:
    """Pure function. Score every asset against every beat and return BeatMatches.

    Tie-break: alphabetical asset_id (stable).
    """
    candidates_pool = [a for a in catalog.assets if _is_content_candidate(a)]
    total_beats = len(beats)
    matches: list[BeatMatch] = []

    for i, beat in enumerate(beats):
        intent = _beat_intent(beat, i, total_beats)
        scored: list[CandidateMatch] = []
        for asset in candidates_pool:
            breakdown = score_asset_for_beat(asset, beat, i, total_beats)
            scored.append(CandidateMatch(
                asset_id=asset.id,
                asset_filename=asset.filename,
                breakdown=breakdown,
                score=breakdown.final_score,
                reason=_explain_breakdown(breakdown, asset, intent),
            ))

        # Sort by (score desc, asset_id asc) — stable tiebreak
        scored.sort(key=lambda c: (-c.score, c.asset_id))

        # Build the BeatMatch decision
        top = scored[0] if scored else None
        if top is None or top.score < CONFIDENCE_LOW:
            matches.append(BeatMatch(
                beat_id=beat.get("id", ""),
                candidate_assets=scored[:5],  # keep top 5 for inspection
                selected_asset_id=None,
                selected_asset_filename=None,
                selection_confidence=top.score if top else 0.0,
                selection_reason="no candidate above CONFIDENCE_LOW threshold (0.30)",
                fallback_asset_ids=[],
                human_review_required=True,
                review_reason="no_acceptable_candidate",
                enrichment_status=_aggregate_enrichment_status(candidates_pool),
            ))
            continue

        confidence = top.score
        review_required, review_reason = _review_decision(confidence, scored)
        fallback_ids = [c.asset_id for c in scored[1:4] if c.score >= CONFIDENCE_LOW]

        matches.append(BeatMatch(
            beat_id=beat.get("id", ""),
            candidate_assets=scored[:5],
            selected_asset_id=top.asset_id,
            selected_asset_filename=top.asset_filename,
            selection_confidence=confidence,
            selection_reason=top.reason,
            fallback_asset_ids=fallback_ids,
            human_review_required=review_required,
            review_reason=review_reason,
            enrichment_status=_aggregate_enrichment_status(candidates_pool),
        ))

    return matches


def _review_decision(confidence: float, scored: list[CandidateMatch]) -> tuple[bool, str | None]:
    """Decide if a beat requires human review and why."""
    if confidence < CONFIDENCE_MEDIUM:
        return True, "low_confidence"
    if confidence < CONFIDENCE_HIGH:
        return True, "medium_confidence"
    # High confidence — but check for narrow margin (top vs second is < 0.05)
    if len(scored) >= 2 and (scored[0].score - scored[1].score) < 0.05:
        return True, "narrow_margin"
    return False, None


def _aggregate_enrichment_status(assets: list[AssetEntry]) -> str:
    """Return overall enrichment status for the candidate pool."""
    if not assets:
        return "none"
    statuses = [_enrichment_status(a) for a in assets]
    if all(s == "full" for s in statuses):
        return "full"
    if all(s == "none" for s in statuses):
        return "none"
    return "partial"


# ── Project-level entry ───────────────────────────────────────────────────


def match_assets_for_project(project_dir: Path) -> dict:
    """Read project files and return a complete asset-matches summary dict."""
    bm_path = project_dir / "audio" / "beat-map.json"
    cat_path = project_dir / "assets" / "catalog.json"

    if not bm_path.exists():
        return {
            "project": project_dir.name,
            "skipped": True,
            "reason": "no beat-map.json",
            "totals": {},
            "beats": [],
        }
    with open(bm_path, "r", encoding="utf-8") as f:
        bm = json.load(f)

    catalog = load_catalog(cat_path) if cat_path.exists() else Catalog()
    beats = bm.get("beats", [])
    matches = match_assets(beats, catalog)

    totals = {
        "beats":                  len(matches),
        "with_selection":         sum(1 for m in matches if m.selected_asset_id),
        "human_review_required":  sum(1 for m in matches if m.human_review_required),
        "no_candidates":          sum(1 for m in matches if m.selected_asset_id is None),
        "high_confidence":        sum(1 for m in matches if m.selection_confidence >= CONFIDENCE_HIGH),
        "medium_confidence":      sum(1 for m in matches if CONFIDENCE_MEDIUM <= m.selection_confidence < CONFIDENCE_HIGH),
        "low_confidence":         sum(1 for m in matches if m.selection_confidence < CONFIDENCE_MEDIUM),
    }

    return {
        "schema_version": 1,
        "project": project_dir.name,
        "matcher_version": MATCHER_VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config": {
            "weights": SCORE_WEIGHTS,
            "confidence_thresholds": {
                "high":   CONFIDENCE_HIGH,
                "medium": CONFIDENCE_MEDIUM,
                "low":    CONFIDENCE_LOW,
            },
            "tie_break": "alphabetical asset_id",
            "enrichment_status_overall": _aggregate_enrichment_status(
                [a for a in catalog.assets if _is_content_candidate(a)]
            ),
        },
        "totals": totals,
        "beats": [m.to_dict() for m in matches],
    }
