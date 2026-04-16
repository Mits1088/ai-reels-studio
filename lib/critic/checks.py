"""
The six editorial critic checks. Each is a pure function that takes the
inputs it needs and returns a list of CriticFinding objects.

Phase E2 changes:
  - All findings are constructed via `make_finding(...)` so they get a stable,
    deterministic finding_id.
  - proof_relevance and caption_competition collapse to ONE global SUGGEST
    when enrichment is globally absent (controlled by the runner via the
    `enrichment_globally_absent` parameter).
  - dead_holds severity is downshifted by one step (BLOCK→WARN, WARN→SUGGEST)
    when no edit_plan is present, because the matcher's image selection is
    provisional and zoom intent cannot be confirmed.
  - dead_holds evidence now includes asset_id (in addition to filename) so
    the runner's related-finding linker can cross-reference it with
    asset_overreuse and visual_novelty findings.

Checks gracefully degrade when optional inputs are missing — they emit
SUGGEST-level findings noting the data gap rather than crashing.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from .finding import (
    CriticFinding,
    SEVERITY_BLOCK,
    SEVERITY_WARN,
    SEVERITY_SUGGEST,
    make_finding,
)


# ── Tunable thresholds (Phase E2 starting values) ──────────────────────────


# Claim-to-proof
CLAIM_LATENCY_WARN_S = 1.5
CLAIM_LATENCY_BLOCK_S = 3.0

# Dead holds
DEAD_HOLD_WARN_S = 2.5
DEAD_HOLD_BLOCK_S = 5.0

# Asset overreuse
OVERREUSE_SUGGEST_AT = 3
OVERREUSE_WARN_AT = 4
OVERREUSE_BLOCK_AT = 6

# Caption competition
HIGH_TEXT_DENSITY = 0.6

# Visual novelty
NOVELTY_REPEAT_WARN = 2
NOVELTY_REPEAT_BLOCK = 4


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".gif"}
VIDEO_EXTS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}


# Stat keywords that indicate a beat is making a measurable claim
_STAT_KEYWORDS = re.compile(
    r"\b("
    r"\d+\s*[xX]"
    r"|\d+\s*%"
    r"|\d+\s*(billion|million|thousand|trillion|k|m|b)\b"
    r"|\d+\s*(times|hours|minutes|seconds|days|weeks|months|years)\b"
    r"|(zero|none|nothing)\s+(loss|impact|cost)"
    r"|(faster|slower|cheaper|larger|smaller|bigger|better)\b"
    r"|(doubled|halved|tripled)"
    r")",
    re.IGNORECASE,
)


def _beat_text(beat: dict) -> str:
    return (beat.get("text") or beat.get("phrase") or "").strip()


def _beat_intent(beat: dict) -> str:
    return (beat.get("intent") or beat.get("visual_intent") or "").strip().lower()


def _beat_duration(beat: dict) -> float:
    try:
        return float(beat.get("end", 0)) - float(beat.get("start", 0))
    except (TypeError, ValueError):
        return 0.0


def _is_image_filename(filename: str | None) -> bool:
    if not filename:
        return False
    suffix = "." + filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    return suffix in IMAGE_EXTS


def _selected_for_beat(matches: list[dict], beat_id: str) -> dict | None:
    for m in matches:
        if m.get("beat_id") == beat_id:
            return m
    return None


def _selected_filename_for_beat(matches: list[dict], beat_id: str) -> str | None:
    m = _selected_for_beat(matches, beat_id)
    return m.get("selected_asset_filename") if m else None


def _selected_id_for_beat(matches: list[dict], beat_id: str) -> str | None:
    m = _selected_for_beat(matches, beat_id)
    return m.get("selected_asset_id") if m else None


# ── 1. Claim-to-proof latency ──────────────────────────────────────────────


def check_claim_to_proof_latency(
    beats: list[dict],
    matches: list[dict] | None,
    motion_plans: list[dict] | None = None,
) -> list[CriticFinding]:
    findings: list[CriticFinding] = []
    if not beats:
        return findings

    matches_list = matches or []

    for i, beat in enumerate(beats):
        text = _beat_text(beat)
        if not text or not _STAT_KEYWORDS.search(text):
            continue

        beat_id = beat.get("id", "")
        try:
            claim_start = float(beat.get("start", 0))
        except (TypeError, ValueError):
            continue

        proof_beat: dict | None = None
        proof_filename: str | None = None
        for j in range(i, len(beats)):
            candidate = beats[j]
            cand_id = candidate.get("id", "")
            filename = _selected_filename_for_beat(matches_list, cand_id)
            if filename:
                proof_beat = candidate
                proof_filename = filename
                break

        if proof_beat is None:
            findings.append(make_finding(
                check="claim_to_proof_latency",
                severity=SEVERITY_BLOCK if matches is not None else SEVERITY_SUGGEST,
                confidence=0.9 if matches is not None else 0.4,
                beat_id=beat_id,
                reason=(
                    f"Claim in {beat_id!r} has no visual proof anywhere in the reel"
                    if matches is not None else
                    f"Claim in {beat_id!r} — no asset-matches data to verify proof"
                ),
                evidence={
                    "claim_text": text[:140],
                    "claim_keywords": _STAT_KEYWORDS.findall(text)[:5],
                    "matches_available": matches is not None,
                },
                suggested_fix=(
                    "Capture or select a proof asset (chart, screenshot, demo) for this beat "
                    "or the next beat"
                ),
            ))
            continue

        try:
            proof_start = float(proof_beat.get("start", 0))
        except (TypeError, ValueError):
            proof_start = claim_start
        latency = max(0.0, proof_start - claim_start)

        if latency <= CLAIM_LATENCY_WARN_S:
            continue

        if latency > CLAIM_LATENCY_BLOCK_S:
            severity = SEVERITY_BLOCK
            confidence = 0.85
        else:
            severity = SEVERITY_WARN
            confidence = 0.75

        findings.append(make_finding(
            check="claim_to_proof_latency",
            severity=severity,
            confidence=confidence,
            beat_id=beat_id,
            reason=(
                f"Claim in {beat_id!r} ({text[:60]!r}) waits {latency:.2f}s "
                f"for proof in {proof_beat.get('id')!r} (threshold {CLAIM_LATENCY_WARN_S}s)"
            ),
            evidence={
                "claim_beat_id":  beat_id,
                "proof_beat_id":  proof_beat.get("id"),
                "proof_filename": proof_filename,
                "latency_s":      round(latency, 3),
                "warn_threshold_s":  CLAIM_LATENCY_WARN_S,
                "block_threshold_s": CLAIM_LATENCY_BLOCK_S,
            },
            suggested_fix=(
                f"Move a proof asset earlier — into {beat_id!r} itself or extend the claim beat "
                f"to span the proof beat"
            ),
        ))

    return findings


# ── 2. Dead holds ──────────────────────────────────────────────────────────


def check_dead_holds(
    beats: list[dict],
    matches: list[dict] | None,
    edit_plan: dict | None = None,
) -> list[CriticFinding]:
    """Flag image beats held longer than DEAD_HOLD_WARN_S without an explicit zoom plan.

    Phase E2: when edit_plan is None, severity is downshifted by one step
    (BLOCK→WARN, WARN→SUGGEST) because the matcher's image selection is
    provisional and zoom intent cannot be confirmed. Confidence stays at 0.5.
    Dead-hold evidence now also includes asset_id for cross-linking with
    asset_overreuse and visual_novelty findings.
    """
    findings: list[CriticFinding] = []
    matches_list = matches or []
    plans_by_beat: dict[str, dict] = {}
    if isinstance(edit_plan, dict):
        for bp in edit_plan.get("beats", []):
            if isinstance(bp, dict) and "beat_id" in bp:
                plans_by_beat[bp["beat_id"]] = bp

    edit_plan_present = edit_plan is not None

    for beat in beats:
        beat_id = beat.get("id", "")
        duration = _beat_duration(beat)
        if duration <= DEAD_HOLD_WARN_S:
            continue

        match = _selected_for_beat(matches_list, beat_id)
        filename = match.get("selected_asset_filename") if match else None
        asset_id = match.get("selected_asset_id") if match else None
        if not _is_image_filename(filename):
            continue

        bp = plans_by_beat.get(beat_id)
        zoom_count = 0
        if bp:
            zooms = bp.get("zoom_moments") or []
            zoom_count = len(zooms) if isinstance(zooms, list) else 0
            if zoom_count > 0:
                continue

        # Phase E2: severity downshift when no edit_plan
        if duration > DEAD_HOLD_BLOCK_S:
            if edit_plan_present:
                severity = SEVERITY_BLOCK
                confidence = 0.8
            else:
                severity = SEVERITY_WARN  # downshifted from BLOCK
                confidence = 0.5
        else:
            if edit_plan_present:
                severity = SEVERITY_WARN
                confidence = 0.7
            else:
                severity = SEVERITY_SUGGEST  # downshifted from WARN
                confidence = 0.5

        findings.append(make_finding(
            check="dead_holds",
            severity=severity,
            confidence=confidence,
            beat_id=beat_id,
            reason=(
                f"Image asset {filename!r} held for {duration:.2f}s without zoom "
                f"(threshold {DEAD_HOLD_WARN_S}s)"
                + ("" if edit_plan_present else
                   " — no edit-plan to confirm zoom intent (severity downshifted)")
            ),
            evidence={
                "filename":     filename,
                "asset_id":     asset_id,           # Phase E2: enables cross-linking
                "duration_s":   round(duration, 3),
                "warn_threshold_s":  DEAD_HOLD_WARN_S,
                "block_threshold_s": DEAD_HOLD_BLOCK_S,
                "zoom_moments_count": zoom_count,
                "edit_plan_present":  edit_plan_present,
            },
            suggested_fix=(
                "Split into sub-beats with different screenshots, OR add zoom_moments "
                "to the BeatPlan in edit-plan.json"
            ),
        ))

    return findings


# ── 3. Asset overreuse ─────────────────────────────────────────────────────


def check_asset_overreuse(matches: list[dict] | None) -> list[CriticFinding]:
    findings: list[CriticFinding] = []
    if not matches:
        return findings

    counter: Counter[str] = Counter()
    beat_ids_by_asset: dict[str, list[str]] = {}
    for m in matches:
        sel = m.get("selected_asset_id")
        if not sel:
            continue
        counter[sel] += 1
        beat_ids_by_asset.setdefault(sel, []).append(m.get("beat_id", ""))

    for asset_id, count in counter.most_common():
        if count < OVERREUSE_SUGGEST_AT:
            continue

        if count >= OVERREUSE_BLOCK_AT:
            severity = SEVERITY_BLOCK
        elif count >= OVERREUSE_WARN_AT:
            severity = SEVERITY_WARN
        else:
            severity = SEVERITY_SUGGEST

        findings.append(make_finding(
            check="asset_overreuse",
            severity=severity,
            confidence=1.0,
            beat_id=None,
            id_key=asset_id,
            reason=(
                f"Asset {asset_id!r} selected for {count} beats — exceeds variety guidance"
            ),
            evidence={
                "asset_id":  asset_id,
                "use_count": count,
                "beat_ids":  beat_ids_by_asset[asset_id],
                "thresholds": {
                    "suggest_at": OVERREUSE_SUGGEST_AT,
                    "warn_at":    OVERREUSE_WARN_AT,
                    "block_at":   OVERREUSE_BLOCK_AT,
                },
            },
            suggested_fix=(
                "Diversify selections — capture more screenshots, broaden the candidate "
                "pool, or rotate fallbacks for less-anchored beats"
            ),
        ))

    return findings


# ── 4. Proof relevance ─────────────────────────────────────────────────────


def check_proof_relevance(
    beats: list[dict],
    matches: list[dict] | None,
    catalog: Any = None,
    *,
    enrichment_globally_absent: bool = False,
) -> list[CriticFinding]:
    """Phase E2: when enrichment is globally absent (no asset has tags), emit
    ONE global SUGGEST instead of N per-beat suggestions. Otherwise per-beat
    findings as before.
    """
    findings: list[CriticFinding] = []
    if not matches or catalog is None:
        return findings

    # Build a quick lookup: asset_id → editorial_tags
    tags_by_id: dict[str, list[str]] = {}
    any_with_tags = False
    for asset in getattr(catalog, "assets", []):
        e = getattr(asset, "enrichment", None)
        if isinstance(e, dict):
            tags = e.get("editorial_tags", []) or []
            if isinstance(tags, list):
                tags_by_id[asset.id] = [str(t) for t in tags]
                if tags:
                    any_with_tags = True

    # Phase E2 dedup: if enrichment is globally absent (no asset has tags AND
    # the runner confirmed enrichment is globally absent), emit one global SUGGEST
    if enrichment_globally_absent and not any_with_tags:
        affected_beats = []
        for beat in beats:
            beat_id = beat.get("id", "")
            sel = _selected_id_for_beat(matches, beat_id)
            if sel and _beat_intent(beat):
                affected_beats.append(beat_id)
        if affected_beats:
            findings.append(make_finding(
                check="proof_relevance",
                severity=SEVERITY_SUGGEST,
                confidence=0.4,
                beat_id=None,
                id_key="no_enrichment",
                reason=(
                    f"Catalog has no enrichment data — proof_relevance check cannot be "
                    f"evaluated for {len(affected_beats)} beats with selected assets"
                ),
                evidence={
                    "affected_beat_count": len(affected_beats),
                    "affected_beat_ids":   affected_beats,
                    "catalog_enrichment_status": "absent",
                },
                suggested_fix=(
                    "Run `python -m lib.capture.enrich projects/<slug>` to populate "
                    "editorial_tags and enable a real proof-relevance check"
                ),
            ))
        return findings

    # Per-beat path (when at least some assets have enrichment)
    for beat in beats:
        beat_id = beat.get("id", "")
        sel = _selected_id_for_beat(matches, beat_id)
        if not sel:
            continue
        intent = _beat_intent(beat)
        if not intent:
            continue

        tags = tags_by_id.get(sel)
        if tags is None:
            findings.append(make_finding(
                check="proof_relevance",
                severity=SEVERITY_SUGGEST,
                confidence=0.4,
                beat_id=beat_id,
                reason=(
                    f"Asset {sel!r} has no enrichment data — proof relevance unverified "
                    f"for intent {intent!r}"
                ),
                evidence={
                    "asset_id": sel,
                    "intent":   intent,
                    "enrichment_status": "absent",
                },
                suggested_fix=(
                    "Run enrichment to populate editorial_tags for this asset"
                ),
            ))
            continue

        if not tags:
            continue

        intent_lower = intent.lower()
        match = any(intent_lower in t.lower() or t.lower() in intent_lower for t in tags)
        if match:
            continue

        findings.append(make_finding(
            check="proof_relevance",
            severity=SEVERITY_WARN,
            confidence=0.5,
            beat_id=beat_id,
            reason=(
                f"Asset {sel!r} editorial_tags={tags} do not contain intent {intent!r}"
            ),
            evidence={
                "asset_id":        sel,
                "intent":          intent,
                "editorial_tags":  tags,
                "match_method":    "substring",
            },
            suggested_fix=(
                "Either select a different asset whose tags match this beat's intent, "
                "or update the asset's editorial_tags via enrichment"
            ),
        ))

    return findings


# ── 5. Caption competition ─────────────────────────────────────────────────


def check_caption_competition(
    beats: list[dict],
    matches: list[dict] | None,
    catalog: Any = None,
    edit_plan: dict | None = None,
    *,
    enrichment_globally_absent: bool = False,
) -> list[CriticFinding]:
    """Phase E2: when text-density data is globally absent, emit ONE global
    SUGGEST instead of per-beat suggestions.
    """
    findings: list[CriticFinding] = []
    if not matches:
        return findings

    text_density: dict[str, float | None] = {}
    any_with_density = False
    if catalog is not None:
        for asset in getattr(catalog, "assets", []):
            e = getattr(asset, "enrichment", None)
            if not isinstance(e, dict):
                text_density[asset.id] = None
                continue
            text_block = e.get("text", {}) or {}
            score = text_block.get("score") if isinstance(text_block, dict) else None
            try:
                density = float(score) if score is not None else None
            except (TypeError, ValueError):
                density = None
            text_density[asset.id] = density
            if density is not None:
                any_with_density = True

    caption_modes_by_beat: dict[str, str] = {}
    if isinstance(edit_plan, dict):
        for bp in edit_plan.get("beats", []):
            if isinstance(bp, dict) and bp.get("beat_id"):
                caption_modes_by_beat[bp["beat_id"]] = bp.get("caption_mode", "standard")

    # Phase E2 dedup: globally absent text-density → one global SUGGEST
    if (enrichment_globally_absent or not any_with_density) and catalog is not None:
        affected = [b.get("id", "") for b in beats if _selected_id_for_beat(matches or [], b.get("id", ""))]
        if affected:
            findings.append(make_finding(
                check="caption_competition",
                severity=SEVERITY_SUGGEST,
                confidence=0.3,
                beat_id=None,
                id_key="no_text_density",
                reason=(
                    f"No text_density data anywhere in the catalog — caption competition "
                    f"cannot be evaluated for {len(affected)} beats with selected assets"
                ),
                evidence={
                    "affected_beat_count": len(affected),
                    "affected_beat_ids":   affected,
                    "catalog_enrichment_status": "absent",
                },
                suggested_fix=(
                    "Run enrichment to populate text density, then re-run the critic"
                ),
            ))
        return findings

    # Per-beat path (when at least some assets have density data)
    for beat in beats:
        beat_id = beat.get("id", "")
        sel = _selected_id_for_beat(matches or [], beat_id)
        if not sel:
            continue

        density = text_density.get(sel) if catalog is not None else None
        caption_mode = caption_modes_by_beat.get(beat_id, "standard")

        if density is None:
            # Per-beat SUGGEST only when SOME density data exists in the catalog
            # but THIS asset is missing it (otherwise we'd have hit the global path)
            findings.append(make_finding(
                check="caption_competition",
                severity=SEVERITY_SUGGEST,
                confidence=0.3,
                beat_id=beat_id,
                reason=(
                    f"No text_density data for asset {sel!r} — caption competition unverified"
                ),
                evidence={
                    "asset_id":     sel,
                    "caption_mode": caption_mode,
                    "text_density": None,
                },
                suggested_fix=(
                    "Re-run enrichment to populate text density for this asset"
                ),
            ))
            continue

        if density <= HIGH_TEXT_DENSITY:
            continue

        if caption_mode == "suppressed":
            continue

        findings.append(make_finding(
            check="caption_competition",
            severity=SEVERITY_WARN,
            confidence=0.8,
            beat_id=beat_id,
            reason=(
                f"Asset {sel!r} has text_density={density:.2f} (>{HIGH_TEXT_DENSITY}) "
                f"but caption_mode={caption_mode!r} (not suppressed) — "
                f"on-screen text and captions will compete"
            ),
            evidence={
                "asset_id":      sel,
                "text_density":  round(density, 3),
                "caption_mode":  caption_mode,
                "threshold":     HIGH_TEXT_DENSITY,
            },
            suggested_fix=(
                "Set caption_mode to 'suppressed' for this beat in edit-plan.json, OR "
                "switch to an asset with lower text density"
            ),
        ))

    return findings


# ── 6. Visual novelty ─────────────────────────────────────────────────────


def check_visual_novelty(matches: list[dict] | None) -> list[CriticFinding]:
    findings: list[CriticFinding] = []
    if not matches:
        return findings

    streak_asset: str | None = None
    streak_beats: list[str] = []

    def _flush_streak() -> None:
        nonlocal streak_beats
        if streak_asset and len(streak_beats) >= NOVELTY_REPEAT_WARN:
            count = len(streak_beats)
            if count >= NOVELTY_REPEAT_BLOCK:
                severity = SEVERITY_BLOCK
                confidence = 0.9
            else:
                severity = SEVERITY_WARN
                confidence = 0.8
            findings.append(make_finding(
                check="visual_novelty",
                severity=severity,
                confidence=confidence,
                beat_id=streak_beats[0],
                reason=(
                    f"Asset {streak_asset!r} held across {count} consecutive beats — "
                    f"viewers see the same content for too long"
                ),
                evidence={
                    "asset_id":    streak_asset,
                    "streak_size": count,
                    "beat_ids":    list(streak_beats),
                    "warn_at":     NOVELTY_REPEAT_WARN,
                    "block_at":    NOVELTY_REPEAT_BLOCK,
                },
                suggested_fix=(
                    "Vary the selected asset between beats — extract more screenshots, "
                    "or split the beat into sub-beats with different focal points"
                ),
            ))
        streak_beats = []

    for m in matches:
        sel = m.get("selected_asset_id")
        beat_id = m.get("beat_id", "")
        if sel == streak_asset and sel is not None:
            streak_beats.append(beat_id)
        else:
            _flush_streak()
            streak_asset = sel
            streak_beats = [beat_id] if sel else []
    _flush_streak()

    return findings


# ── Registry ──────────────────────────────────────────────────────────────


CHECK_REGISTRY: dict[str, str] = {
    "claim_to_proof_latency": "Claims must have visual proof within 1.5s",
    "dead_holds":              "Static images > 2.5s should have a zoom plan",
    "asset_overreuse":         "No single asset selected for too many beats",
    "proof_relevance":         "Asset editorial_tags should overlap beat intent",
    "caption_competition":     "Text-heavy assets should suppress captions",
    "visual_novelty":          "Adjacent beats should not show identical content",
}
