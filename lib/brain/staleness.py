"""
lib.brain.staleness — Artifact staleness detection.

Walks the dependency map in lib.brain.artifacts and compares file
modification times. Returns StalenessResult objects for every
upstream→downstream pair where the upstream is detectably newer.

Read-only. No mutations. No gate changes.
"""

from __future__ import annotations

from pathlib import Path

from .artifacts import DEPENDENCY_MAP
from .models import StalenessResult

# Minimum mtime delta (seconds) required to flag a pair as stale.
# Artifacts written during the same pipeline run often land within 1–2s of
# each other. This threshold filters those same-run writes.
STALE_TOLERANCE_SECONDS: float = 2.0


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _adjust_confidence(base: str, delta_seconds: float) -> str:
    """
    Scale base_confidence by the size of the mtime gap.

    Very small deltas (< 30s) suggest the files were written in the same
    session even if they are technically above STALE_TOLERANCE_SECONDS.
    Larger deltas strongly imply the upstream was intentionally changed later.
    """
    if delta_seconds < 30:
        # Barely over tolerance — very likely same session
        return "medium" if base == "high" else "low"
    if delta_seconds < 300:
        # Under 5 minutes — possibly the same session
        return base if base == "high" else "medium"
    # Over 5 minutes — almost certainly a different pipeline session
    return base


def detect_staleness(project_dir: Path) -> list[StalenessResult]:
    """
    Return all detected staleness signals for the given project directory.

    Only reports on artifact pairs where BOTH files exist on disk.  Missing
    artifacts are handled by gate-artifact mismatch logic in diagnose.py.

    Results are sorted: high confidence first, then by age delta descending
    (largest divergence shown first within each confidence tier).
    """
    project_dir = Path(project_dir).resolve()
    results: list[StalenessResult] = []

    for dep in DEPENDENCY_MAP:
        up_path = project_dir / dep.upstream
        down_path = project_dir / dep.downstream

        if not up_path.exists() or not down_path.exists():
            continue

        up_mt = _mtime(up_path)
        down_mt = _mtime(down_path)
        delta = up_mt - down_mt

        if delta > STALE_TOLERANCE_SECONDS:
            confidence = _adjust_confidence(dep.base_confidence, delta)
            results.append(StalenessResult(
                downstream=dep.downstream,
                upstream=dep.upstream,
                confidence=confidence,
                reason=dep.reason,
                recommended_action=dep.recommended_action,
                age_delta_seconds=round(delta, 1),
            ))

    _RANK = {"high": 0, "medium": 1, "low": 2}
    results.sort(key=lambda r: (_RANK.get(r.confidence, 3), -r.age_delta_seconds))
    return results
