"""
Gap owner — classifies gaps between beats and assigns ownership.

From .claude/rules/visual-style.md "Gap Ownership Rule":

  - Gaps < 0.3s (< 9 frames): exiting beat holds through. No special treatment needed.
  - Gaps 0.3–0.8s (9–24 frames): designed seam. Define whether the exiting beat
    fades out, the entering beat pre-enters, or the gap is a background transition.
  - Gaps > 0.8s (> 24 frames): breathing space. Must contain intentional transition
    or anticipation.

Each gap gets ownership:
  - micro     → owned by the previous beat (just hold)
  - seam      → owned by the previous beat (extends through, designed)
  - breathing → split — first half owned by prev, second half by next (anticipation)

For Phase D simplicity, every gap is given ONE owner (the prev beat). The
ownership_type tells downstream tooling how the gap should be treated.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


# Bands (per visual-style.md). Epsilon protects against IEEE-754 noise like
# `5.3 - 5.0 = 0.2999999999999998` from being misclassified as micro when
# the editorial intent was a seam. 1e-6 = 1µs at 1MHz; well below any
# meaningful video timing precision.
MICRO_THRESHOLD = 0.3       # < 0.3s = micro
SEAM_THRESHOLD = 0.8        # 0.3–0.8s = seam
_EPSILON = 1e-6

OWNERSHIP_MICRO = "micro"
OWNERSHIP_SEAM = "seam"
OWNERSHIP_BREATHING = "breathing"

GAP_OWNER_VERSION = "lib.orchestrate.gap_owner@1.0.0"


@dataclass(frozen=True)
class GapAssignment:
    """One gap between two adjacent beats."""
    gap_id: str
    gap_start: float
    gap_end: float
    gap_duration: float
    ownership_type: str         # 'micro' | 'seam' | 'breathing'
    owner_beat_id: str | None
    next_beat_id: str | None
    reason: str

    def to_dict(self) -> dict:
        return {
            "gap_id":         self.gap_id,
            "gap_start":      round(self.gap_start, 3),
            "gap_end":        round(self.gap_end, 3),
            "gap_duration":   round(self.gap_duration, 3),
            "ownership_type": self.ownership_type,
            "owner_beat_id":  self.owner_beat_id,
            "next_beat_id":   self.next_beat_id,
            "reason":         self.reason,
        }


def _classify_gap(duration: float) -> tuple[str, str]:
    """Return (ownership_type, machine-readable reason).

    Boundary handling: when duration is within _EPSILON of a threshold, the
    higher band wins. This makes 0.3s land in 'seam' (not 'micro') even when
    the value comes from a subtraction that produces 0.29999... due to IEEE-754
    representation noise.
    """
    if duration < MICRO_THRESHOLD - _EPSILON:
        return (
            OWNERSHIP_MICRO,
            f"micro gap ({duration:.3f}s < {MICRO_THRESHOLD}s) — exiting beat holds through, no treatment needed",
        )
    if duration < SEAM_THRESHOLD - _EPSILON:
        return (
            OWNERSHIP_SEAM,
            f"seam gap ({MICRO_THRESHOLD}s ≤ {duration:.3f}s < {SEAM_THRESHOLD}s) — exiting beat owns the seam, choose fade/pre-enter/bg transition",
        )
    return (
        OWNERSHIP_BREATHING,
        f"breathing gap ({duration:.3f}s ≥ {SEAM_THRESHOLD}s) — must contain intentional transition or anticipation",
    )


def assign_gaps(beats: list[dict]) -> list[GapAssignment]:
    """Pure function. Identify gaps between adjacent beats and assign ownership.

    Beats must be sorted by start time. Gaps are computed between
    consecutive beat pairs. A leading gap (before the first beat) and a
    trailing gap (after the last beat) are NOT included — those are reel
    edge concerns, not beat gaps.
    """
    if len(beats) < 2:
        return []

    sorted_beats = sorted(beats, key=lambda b: float(b.get("start", 0)))
    gaps: list[GapAssignment] = []

    for i in range(len(sorted_beats) - 1):
        prev = sorted_beats[i]
        nxt = sorted_beats[i + 1]
        try:
            prev_end = float(prev.get("end", 0))
            next_start = float(nxt.get("start", 0))
        except (TypeError, ValueError):
            continue

        duration = next_start - prev_end
        # Negative duration = overlap; we still record it as a special case
        if duration <= 0:
            gaps.append(GapAssignment(
                gap_id=f"gap-{i+1:02d}",
                gap_start=next_start,
                gap_end=prev_end,
                gap_duration=duration,
                ownership_type="overlap",
                owner_beat_id=prev.get("id"),
                next_beat_id=nxt.get("id"),
                reason=f"overlap of {abs(duration):.3f}s — beats touch or interlock",
            ))
            continue

        ownership_type, reason = _classify_gap(duration)
        gaps.append(GapAssignment(
            gap_id=f"gap-{i+1:02d}",
            gap_start=prev_end,
            gap_end=next_start,
            gap_duration=duration,
            ownership_type=ownership_type,
            owner_beat_id=prev.get("id"),
            next_beat_id=nxt.get("id"),
            reason=reason,
        ))

    return gaps


def assign_gaps_for_project(project_dir: Path) -> dict:
    bm_path = project_dir / "audio" / "beat-map.json"
    if not bm_path.exists():
        return {
            "project": project_dir.name,
            "skipped": True,
            "reason": "no beat-map.json",
            "gaps": [],
        }
    with open(bm_path, "r", encoding="utf-8") as f:
        bm = json.load(f)

    beats = bm.get("beats", [])
    gaps = assign_gaps(beats)

    by_type: dict[str, int] = {}
    for g in gaps:
        by_type[g.ownership_type] = by_type.get(g.ownership_type, 0) + 1

    return {
        "schema_version": 1,
        "project": project_dir.name,
        "version": GAP_OWNER_VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "thresholds": {
            "micro_threshold_s": MICRO_THRESHOLD,
            "seam_threshold_s":  SEAM_THRESHOLD,
        },
        "totals": {
            "gaps_total": len(gaps),
            "by_type":    by_type,
        },
        "gaps": [g.to_dict() for g in gaps],
    }
