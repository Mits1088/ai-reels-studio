"""
Reel project contract validation.

Zero external dependencies — pure stdlib.
Validates project.json, beat-map.json, and timeline.json against their contracts.
"""

import json
import re
from pathlib import Path
from typing import Any

from lib.constants import (
    CURRENT_SCHEMA_VERSION, VALID_PROJECT_TYPES,
    VALID_PHASES, REEL_PHASES, YOUTUBE_PHASES,
    VALID_STATUSES, VALID_STYLES,
    VALID_GATE_IDS, REEL_GATE_IDS, YOUTUBE_GATE_IDS,
    SLUG_RE, BEAT_ID_RE, COLOR_HEX_RE, MAX_TRANSITION_DURATION,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _ts3(val: float) -> bool:
    """Check timestamp has at most 3 decimal places."""
    return round(val, 3) == val


class ValidationError:
    def __init__(self, file: str, field: str, message: str):
        self.file = file
        self.field = field
        self.message = message

    def __repr__(self):
        return f"[{self.file}] {self.field}: {self.message}"


# ── project.json ─────────────────────────────────────────────────────────────


def validate_project(data: dict) -> list[ValidationError]:
    errs: list[ValidationError] = []
    f = "project.json"

    # Required fields (v2 contract)
    for fld in ("slug", "title", "phase", "status", "gates_passed", "created", "updated"):
        if fld not in data:
            errs.append(ValidationError(f, fld, "required field missing"))

    # Schema version
    sv = data.get("schema_version")
    if sv is None:
        errs.append(ValidationError(f, "schema_version",
                    f"missing — run 'python -m lib.migrate' to upgrade"))
    elif not isinstance(sv, int) or sv < 1:
        errs.append(ValidationError(f, "schema_version", f"must be a positive integer, got {sv!r}"))
    elif sv > CURRENT_SCHEMA_VERSION:
        errs.append(ValidationError(f, "schema_version",
                    f"version {sv} is newer than supported ({CURRENT_SCHEMA_VERSION})"))

    # Project type
    pt = data.get("project_type")
    if pt is None:
        errs.append(ValidationError(f, "project_type",
                    f"missing — run 'python -m lib.migrate' to upgrade"))
    elif pt not in VALID_PROJECT_TYPES:
        errs.append(ValidationError(f, "project_type", f"unknown type: {pt!r}"))

    if "slug" in data and not SLUG_RE.match(data["slug"]):
        errs.append(ValidationError(f, "slug", f"invalid slug: {data['slug']!r}"))

    # Phase validation (type-aware)
    if "phase" in data:
        phase = data["phase"]
        if pt == "youtube":
            if phase not in YOUTUBE_PHASES:
                errs.append(ValidationError(f, "phase", f"unknown youtube phase: {phase!r}"))
        elif pt == "reel":
            if phase not in REEL_PHASES:
                errs.append(ValidationError(f, "phase", f"unknown reel phase: {phase!r}"))
        elif phase not in VALID_PHASES:
            errs.append(ValidationError(f, "phase", f"unknown phase: {phase!r}"))

    if "status" in data and data["status"] not in VALID_STATUSES:
        errs.append(ValidationError(f, "status", f"unknown status: {data['status']!r}"))

    if data.get("duration_s") is not None and not isinstance(data["duration_s"], (int, float)):
        errs.append(ValidationError(f, "duration_s", "must be a number or null"))

    # Style
    style = data.get("style")
    if style is not None and style not in VALID_STYLES:
        errs.append(ValidationError(f, "style", f"unknown style: {style!r}"))

    # Gates passed (type-aware)
    gates = data.get("gates_passed")
    if gates is not None:
        if not isinstance(gates, list):
            errs.append(ValidationError(f, "gates_passed", "must be an array"))
        else:
            valid_for_type = (YOUTUBE_GATE_IDS if pt == "youtube"
                              else REEL_GATE_IDS if pt == "reel"
                              else VALID_GATE_IDS)
            for i, gid in enumerate(gates):
                if gid not in valid_for_type:
                    errs.append(ValidationError(f, f"gates_passed[{i}]", f"unknown gate ID: {gid!r}"))

    # Theme consistency — if theme_set gate is passed, theme fields must be populated
    gates_set = set(gates) if isinstance(gates, list) else set()
    if "theme_set" in gates_set:
        for tf in ("theme", "theme_primary", "theme_secondary"):
            if not data.get(tf):
                errs.append(ValidationError(f, tf, f"required when theme_set gate is passed"))

    # Color format
    for cf in ("theme_primary", "theme_secondary"):
        val = data.get(cf)
        if val is not None and not COLOR_HEX_RE.match(str(val)):
            errs.append(ValidationError(f, cf, f"invalid hex color: {val!r} (expected #RRGGBB)"))

    return errs


# ── beat-map.json ────────────────────────────────────────────────────────────

# BEAT_ID_RE imported from lib.constants (allows sub-beats like beat-01a)


def validate_beat_map(data: dict) -> list[ValidationError]:
    errs: list[ValidationError] = []
    f = "beat-map.json"

    if "total_duration" not in data:
        errs.append(ValidationError(f, "total_duration", "required field missing"))
        return errs

    if not isinstance(data["total_duration"], (int, float)) or data["total_duration"] <= 0:
        errs.append(ValidationError(f, "total_duration", "must be a positive number"))

    beats = data.get("beats")
    if not beats:
        errs.append(ValidationError(f, "beats", "must contain at least one beat"))
        return errs

    seen_ids: set[str] = set()
    prev_end = 0.0

    for i, beat in enumerate(beats):
        prefix = f"beats[{i}]"

        # Required fields
        for field in ("id", "scene", "phrase", "start", "end", "words", "visual_intent"):
            if field not in beat:
                errs.append(ValidationError(f, f"{prefix}.{field}", "required field missing"))

        bid = beat.get("id", "")
        if not BEAT_ID_RE.match(bid):
            errs.append(ValidationError(f, f"{prefix}.id", f"invalid beat ID format: {bid!r}"))
        if bid in seen_ids:
            errs.append(ValidationError(f, f"{prefix}.id", f"duplicate beat ID: {bid!r}"))
        seen_ids.add(bid)

        start = beat.get("start", 0)
        end = beat.get("end", 0)

        if end <= start:
            errs.append(ValidationError(f, f"{prefix}.end", "end must be > start"))

        if start < prev_end - 0.001:  # small tolerance for float
            errs.append(ValidationError(f, f"{prefix}.start", f"beat overlaps with previous (starts {start}, prev ended {prev_end})"))
        prev_end = end

        # Words
        words = beat.get("words", [])
        if isinstance(words, list):
            if len(words) == 0:
                errs.append(ValidationError(f, f"{prefix}.words", "must contain at least one word"))
            for j, w in enumerate(words):
                for wf in ("word", "start", "end"):
                    if wf not in w:
                        errs.append(ValidationError(f, f"{prefix}.words[{j}].{wf}", "required field missing"))
                if "start" in w and "end" in w and w["end"] <= w["start"]:
                    errs.append(ValidationError(f, f"{prefix}.words[{j}]", "word end must be > start"))

    # Check last beat doesn't exceed total_duration
    if beats and beats[-1].get("end", 0) > data["total_duration"] + 0.001:
        errs.append(ValidationError(f, "beats[-1].end", "last beat end exceeds total_duration"))

    return errs


# ── timeline.json ────────────────────────────────────────────────────────────

REQUIRED_LANES = {"avatar", "demo", "support", "captions", "sfx", "music"}
VISUAL_LANES = {"avatar", "demo", "support"}


def validate_timeline(data: dict, beat_ids: set[str] | None = None,
                       asset_files: set[str] | None = None) -> list[ValidationError]:
    errs: list[ValidationError] = []
    f = "timeline.json"

    if "total_duration" not in data:
        errs.append(ValidationError(f, "total_duration", "required field missing"))

    lanes = data.get("lanes")
    if not lanes:
        errs.append(ValidationError(f, "lanes", "required field missing"))
        return errs

    for lane_name in REQUIRED_LANES:
        if lane_name not in lanes:
            errs.append(ValidationError(f, f"lanes.{lane_name}", "required lane missing"))

    for lane_name, entries in lanes.items():
        if not isinstance(entries, list):
            errs.append(ValidationError(f, f"lanes.{lane_name}", "must be an array"))
            continue

        for i, entry in enumerate(entries):
            prefix = f"lanes.{lane_name}[{i}]"

            # Timing
            start = entry.get("start")
            end = entry.get("end")
            if start is None:
                errs.append(ValidationError(f, f"{prefix}.start", "required field missing"))
            if end is None:
                errs.append(ValidationError(f, f"{prefix}.end", "required field missing"))
            if start is not None and end is not None and end <= start:
                errs.append(ValidationError(f, f"{prefix}", "end must be > start"))

            # Captions must have text and beat_id
            if lane_name == "captions":
                if "text" not in entry:
                    errs.append(ValidationError(f, f"{prefix}.text", "captions require text"))
                if "beat_id" not in entry:
                    errs.append(ValidationError(f, f"{prefix}.beat_id", "captions require beat_id"))

            # Visual lanes must have asset and beat_id
            if lane_name in VISUAL_LANES:
                if "asset" not in entry:
                    errs.append(ValidationError(f, f"{prefix}.asset", "visual lane requires asset"))
                if "beat_id" not in entry:
                    errs.append(ValidationError(f, f"{prefix}.beat_id", "visual lane requires beat_id"))

            # Beat ID cross-reference
            bid = entry.get("beat_id")
            if bid and beat_ids is not None and bid not in beat_ids:
                errs.append(ValidationError(f, f"{prefix}.beat_id", f"references nonexistent beat: {bid!r}"))

            # Asset cross-reference
            asset = entry.get("asset")
            if asset and asset_files is not None and asset not in asset_files:
                errs.append(ValidationError(f, f"{prefix}.asset", f"references nonexistent asset: {asset!r}"))

            # Transition duration
            tr = entry.get("transition")
            if tr and tr.get("duration", 0) > MAX_TRANSITION_DURATION:
                errs.append(ValidationError(f, f"{prefix}.transition.duration",
                            f"exceeds max {MAX_TRANSITION_DURATION}s"))

    return errs


# ── Full project validation ──────────────────────────────────────────────────

def validate_project_dir(project_path: Path) -> list[ValidationError]:
    """Validate all JSON contracts in a project directory."""
    errs: list[ValidationError] = []

    # project.json
    pj = project_path / "project.json"
    if pj.exists():
        errs.extend(validate_project(_load_json(pj)))
    else:
        errs.append(ValidationError("project.json", "", "file not found"))

    # beat-map.json
    beat_ids: set[str] = set()
    bm = project_path / "audio" / "beat-map.json"
    if bm.exists():
        bm_data = _load_json(bm)
        errs.extend(validate_beat_map(bm_data))
        beat_ids = {b["id"] for b in bm_data.get("beats", []) if "id" in b}

    # catalog.json
    asset_files: set[str] = set()
    cat = project_path / "assets" / "catalog.json"
    if cat.exists():
        from lib.capture.validate_catalog import validate_catalog as _validate_catalog
        from lib.capture.catalog import load_catalog
        catalog = load_catalog(cat)
        errs.extend(_validate_catalog(
            catalog,
            assets_dir=project_path / "assets",
            beat_ids=beat_ids or None,
        ))
        asset_files = catalog.filenames()

    # timeline.json
    tl = project_path / "output" / "timeline.json"
    if tl.exists():
        errs.extend(validate_timeline(
            _load_json(tl),
            beat_ids=beat_ids or None,
            asset_files=asset_files or None,
        ))

    return errs


# ── CLI entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python validate.py <project-dir>")
        sys.exit(1)
    errors = validate_project_dir(Path(sys.argv[1]))
    if errors:
        print(f"FAILED — {len(errors)} error(s):")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("PASSED — all contracts valid.")
