"""
Canonicalization helpers for parity diffing.

A "canonical" timeline is one where:
  - Floats are rounded to 3 decimal places
  - Lane entries are sorted by (start, end, key-order)
  - Empty arrays are preserved (semantic difference from absent)
  - None values are dropped from optional fields
  - Dict keys are sorted in serialized output

Canonicalization is symmetric: canonicalize(x) == canonicalize(y) means
the two timelines are semantically equivalent.

The Phase C parity tests use this to compare a reverse-engineered →
recompiled timeline against the original.
"""

from __future__ import annotations

import json
from typing import Any


# Float precision for comparison. 3 decimals = 1ms at 1000fps, well below
# any meaningful audio/video sync threshold.
ROUND_PRECISION = 3


def _round_floats(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, ROUND_PRECISION)
    if isinstance(value, dict):
        return {k: _round_floats(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_round_floats(v) for v in value]
    return value


def _drop_none(value: Any) -> Any:
    """Strip dict keys whose value is None. Recurses into nested dicts and lists.

    Empty lists are preserved (they carry semantic meaning — "the lane exists").
    Empty dicts are preserved.
    """
    if isinstance(value, dict):
        return {k: _drop_none(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_drop_none(v) for v in value]
    return value


def _sort_lane_entries(entries: list[dict]) -> list[dict]:
    """Sort lane entries by (start, end, asset, beat_id) for stable comparison."""
    def key(e: dict) -> tuple:
        return (
            e.get("start") if e.get("start") is not None else 0.0,
            e.get("end") if e.get("end") is not None else 0.0,
            str(e.get("asset", "")),
            str(e.get("beat_id", "")),
            str(e.get("type", "")),  # for overlay entries
        )
    return sorted(entries, key=key)


def canonicalize_timeline(tl: dict) -> dict:
    """Return a canonical form of a timeline dict suitable for parity diffing."""
    # Round floats first, then drop Nones, then sort lanes
    out = _round_floats(tl)
    out = _drop_none(out)

    if isinstance(out.get("lanes"), dict):
        canonical_lanes: dict[str, Any] = {}
        for lane_name, entries in out["lanes"].items():
            if isinstance(entries, list):
                canonical_lanes[lane_name] = _sort_lane_entries(
                    [e for e in entries if isinstance(e, dict)]
                )
            else:
                canonical_lanes[lane_name] = entries
        out["lanes"] = canonical_lanes

    return out


def canonical_json(tl: dict) -> str:
    """Serialize a canonicalized timeline to JSON with sorted keys."""
    canonical = canonicalize_timeline(tl)
    return json.dumps(canonical, indent=2, sort_keys=True, ensure_ascii=False)


# ── Diff helpers ──────────────────────────────────────────────────────────


def diff_timelines(
    original: dict,
    compiled: dict,
    *,
    allowed_extra_keys: set[str] | None = None,
) -> list[str]:
    """Return a list of diff strings between two timelines after canonicalization.

    Empty list = round-trip exact (parity passes).

    `allowed_extra_keys` is a set of keys that are allowed to appear in the
    compiled output but not in the original (e.g. Phase C may attach
    template_id, proof_class, captionMode, etc. as optional planning fields
    that the original timelines do not carry). When checking, the diff
    ignores extra keys in the compiled output that are in this allowlist.
    """
    a = canonicalize_timeline(original)
    b = canonicalize_timeline(compiled)
    diffs: list[str] = []
    _walk_diff(a, b, "", diffs, allowed_extra_keys or set())
    return diffs


def _walk_diff(
    a: Any,
    b: Any,
    path: str,
    diffs: list[str],
    allowed_extras: set[str],
) -> None:
    if isinstance(a, dict) and isinstance(b, dict):
        a_keys = set(a.keys())
        b_keys = set(b.keys())
        only_in_a = a_keys - b_keys
        only_in_b = b_keys - a_keys
        for k in sorted(only_in_a):
            diffs.append(f"{path}.{k}: only in original (value={a[k]!r})")
        for k in sorted(only_in_b):
            if k in allowed_extras:
                continue
            diffs.append(f"{path}.{k}: only in compiled (value={b[k]!r})")
        for k in sorted(a_keys & b_keys):
            _walk_diff(a[k], b[k], f"{path}.{k}", diffs, allowed_extras)
        return

    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append(
                f"{path}: list length {len(a)} → {len(b)}"
            )
            # Compare what we can
            for i, (ai, bi) in enumerate(zip(a, b)):
                _walk_diff(ai, bi, f"{path}[{i}]", diffs, allowed_extras)
            return
        for i, (ai, bi) in enumerate(zip(a, b)):
            _walk_diff(ai, bi, f"{path}[{i}]", diffs, allowed_extras)
        return

    if a != b:
        diffs.append(f"{path}: {a!r} → {b!r}")
