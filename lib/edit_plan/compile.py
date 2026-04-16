"""
Edit-plan compiler — deterministic transformation EditPlan → timeline.json dict.

Two compilation modes coexist:

  1. Verbatim mode (per-lane): when EditPlan.verbatim_lanes contains a lane,
     the compiler emits that lane unchanged. Used by reverse-engineering and
     parity tests to round-trip legacy timelines whose shape does not fit a
     clean per-beat model.

  2. Generative mode (default for absent lanes): the compiler walks the
     BeatPlans and emits per-beat avatar / content / caption entries based
     on the template's split_ratio and the BeatPlan's selected asset.

Both modes coexist on a single compile call — each lane is verbatim or
generated independently.

The compiler is pure: no I/O, no global state, no side effects. It accepts
a beat_map dict for timing and an optional Catalog for asset lookup.
Asset lookup is only attempted when a BeatPlan has selected_asset_id but
NO selected_asset_filename — the catalog-free path is preferred.

Errors are raised as CompileError with stable error codes:
  E001 unknown_template       — template_id not in registry
  E002 missing_asset          — selected_asset_id not in catalog and no filename
  E003 invalid_proof_class    — proof_class not one of the 7 known classes
  E004 unsupported_motion     — motion preset not in renderer enum
  E005 invalid_caption_mode   — caption_mode not in known set
  E006 invalid_split_ratio    — split_ratio does not parse / does not sum to 100
  E007 invalid_avatar_mode    — avatar_mode is empty
  E008 missing_beat           — beat_plan.beat_id not in beat_map
  E009 unknown_role           — asset role doesn't map to a known lane
"""

from __future__ import annotations

from typing import Any

from lib.grammar import (
    PROOF_CLASSES,
    VALID_CAPTION_MODES,
    RENDERER_ENTER_PRESETS,
    RENDERER_EXIT_PRESETS,
    TemplateRegistry,
)
from .model import EditPlan, BeatPlan, COMPILER_VERSION


# ── Errors ────────────────────────────────────────────────────────────────


class CompileError(Exception):
    """Structured compile-time error with a stable code and beat context."""

    def __init__(self, code: str, beat_id: str | None, message: str):
        self.code = code
        self.beat_id = beat_id
        self.detail = message
        super().__init__(f"[{code}] beat={beat_id or '?'}: {message}")


# ── Constants ─────────────────────────────────────────────────────────────


# Lanes the validator + renderer always expect (even if empty).
ALWAYS_EMIT_LANES = ("avatar", "demo", "support", "captions", "sfx", "music")
# Lanes that are emitted only when the source had them or when generation
# produced entries. Keeps round-trip parity with timelines that omit them.
OPTIONAL_EMIT_LANES = ("broll", "overlays")
REQUIRED_LANES = ALWAYS_EMIT_LANES + OPTIONAL_EMIT_LANES

# Image extensions decide demo→support fallback in generative mode
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".gif"}
VIDEO_EXTS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}


# ── Public API ────────────────────────────────────────────────────────────


def compile_edit_plan(
    plan: EditPlan,
    beat_map: dict,
    *,
    catalog: Any = None,
    template_registry: TemplateRegistry | None = None,
    attach_planning_fields: bool = False,
) -> dict:
    """Deterministic compilation of an EditPlan into a timeline.json dict.

    Args:
        plan: the EditPlan to compile.
        beat_map: parsed beat-map.json (must contain 'beats' and 'total_duration').
        catalog: optional Catalog object. Only consulted when a BeatPlan has
            selected_asset_id but no selected_asset_filename. Catalog-free
            compile is preferred — Phase C parity uses inline filenames.
        template_registry: optional TemplateRegistry. When provided, the
            compiler validates template_id existence and raises E001 on
            unknown templates.
        attach_planning_fields: when True, the compiler attaches editorial
            metadata (template_id, proof_class, caption_mode, split_ratio,
            avatar_mode, proof_protected) onto the emitted lane entries.
            Default False so verbatim parity round-trip is byte-clean.

    Returns:
        a timeline dict ready to be written to output/timeline.json.

    Raises:
        CompileError on any structural problem with stable error codes.
    """
    # Pre-validate beat plans against the registry / proof classes / etc.
    _pre_validate(plan, beat_map, catalog, template_registry)

    timeline: dict[str, Any] = {}

    # Top-level scaffolding
    if plan.total_duration is not None:
        timeline["total_duration"] = plan.total_duration
    else:
        timeline["total_duration"] = float(beat_map.get("total_duration", 0))

    if plan.audio is not None:
        timeline["audio"] = plan.audio
    if plan.avatar_file is not None:
        timeline["avatar_file"] = plan.avatar_file
    if plan.project is not None:
        timeline["project"] = plan.project
    # Style is optional in EditPlan — emit only when explicitly set so
    # legacy timelines without a top-level style field round-trip cleanly.
    if plan.style is not None:
        timeline["style"] = plan.style

    # Lanes — verbatim per-lane, generated for absent lanes.
    # Required lanes are always emitted (even if empty). Optional lanes
    # (broll, overlays) are emitted only when the source had them OR when
    # generation produced entries — this preserves round-trip parity with
    # legacy timelines that omit those keys entirely.
    timeline["lanes"] = {}
    verbatim = plan.verbatim_lanes or {}

    for lane_name in ALWAYS_EMIT_LANES:
        if lane_name in verbatim:
            timeline["lanes"][lane_name] = [dict(e) for e in verbatim[lane_name]]
        else:
            timeline["lanes"][lane_name] = _generate_lane(plan, beat_map, lane_name, catalog)

    for lane_name in OPTIONAL_EMIT_LANES:
        if lane_name in verbatim:
            timeline["lanes"][lane_name] = [dict(e) for e in verbatim[lane_name]]
        else:
            generated = _generate_lane(plan, beat_map, lane_name, catalog)
            if generated:
                timeline["lanes"][lane_name] = generated

    # Optionally attach editorial planning fields onto matching entries
    if attach_planning_fields:
        _attach_planning_fields(timeline, plan)

    return timeline


# ── Pre-validation ────────────────────────────────────────────────────────


def _pre_validate(
    plan: EditPlan,
    beat_map: dict,
    catalog: Any,
    template_registry: TemplateRegistry | None,
) -> None:
    beat_ids = {b["id"] for b in beat_map.get("beats", []) if "id" in b}
    catalog_ids: set[str] = set()
    if catalog is not None:
        try:
            catalog_ids = catalog.ids() if hasattr(catalog, "ids") else set()
        except Exception:
            catalog_ids = set()

    for bp in plan.beats:
        # Beat existence
        if beat_ids and bp.beat_id not in beat_ids:
            raise CompileError("E008", bp.beat_id, "beat not found in beat_map")

        # Template
        if template_registry is not None and not template_registry.has(bp.template_id):
            raise CompileError("E001", bp.beat_id, f"unknown template_id: {bp.template_id!r}")

        # Proof class
        if bp.proof_class is not None and bp.proof_class not in PROOF_CLASSES:
            raise CompileError("E003", bp.beat_id, f"invalid proof_class: {bp.proof_class!r}")

        # Caption mode
        if bp.caption_mode not in VALID_CAPTION_MODES:
            raise CompileError("E005", bp.beat_id, f"invalid caption_mode: {bp.caption_mode!r}")

        # Split ratio
        if not _parse_split_ratio(bp.split_ratio):
            raise CompileError("E006", bp.beat_id, f"invalid split_ratio: {bp.split_ratio!r}")

        # Avatar mode
        if not bp.avatar_mode or not bp.avatar_mode.strip():
            raise CompileError("E007", bp.beat_id, "avatar_mode must be a non-empty string")

        # Motion presets
        for role, event in (
            ("hero", bp.motion_budget.hero),
            ("support", bp.motion_budget.support),
            ("accent", bp.motion_budget.accent),
        ):
            if event is None or event.preset is None:
                continue
            if event.preset not in RENDERER_ENTER_PRESETS and event.preset not in RENDERER_EXIT_PRESETS:
                raise CompileError(
                    "E004", bp.beat_id,
                    f"unsupported motion preset for {role}: {event.preset!r}",
                )

        # Asset reference (only error in generative mode — verbatim mode passes through)
        verbatim = plan.verbatim_lanes or {}
        any_verbatim_for_content = any(
            lane in verbatim for lane in ("demo", "broll", "support")
        )
        if (
            bp.selected_asset_id
            and not bp.selected_asset_filename
            and not any_verbatim_for_content
            and catalog is not None
            and catalog_ids
            and bp.selected_asset_id not in catalog_ids
        ):
            raise CompileError(
                "E002", bp.beat_id,
                f"asset {bp.selected_asset_id!r} not in catalog and no selected_asset_filename hint",
            )


def _parse_split_ratio(value: str) -> bool:
    try:
        a, b = value.split("/")
        return int(a) + int(b) == 100
    except (ValueError, AttributeError):
        return False


# ── Generative lane emission (per-beat) ───────────────────────────────────


def _generate_lane(
    plan: EditPlan, beat_map: dict, lane_name: str, catalog: Any
) -> list[dict]:
    """Generate a lane from BeatPlans when no verbatim data is present.

    Phase C minimum: handles avatar, demo/broll/support (mutually exclusive
    based on filename heuristics or render_overrides.lane_hint), and captions
    (from beat_map). sfx/music/overlays default to empty arrays.
    """
    if lane_name == "avatar":
        return _generate_avatar_lane(plan, beat_map)
    if lane_name in ("demo", "broll", "support"):
        return _generate_content_lane(plan, beat_map, lane_name, catalog)
    if lane_name == "captions":
        return _generate_caption_lane(plan, beat_map)
    return []


def _generate_avatar_lane(plan: EditPlan, beat_map: dict) -> list[dict]:
    entries = []
    beats_by_id = {b["id"]: b for b in beat_map.get("beats", [])}
    for bp in plan.beats:
        ratio = _parse_split_ratio_tuple(bp.split_ratio)
        if ratio is None:
            continue
        content_pct, avatar_pct = ratio
        if avatar_pct == 0:
            continue  # template hides the avatar
        beat = beats_by_id.get(bp.beat_id)
        if not beat:
            continue
        layout = "full-screen" if content_pct == 0 else "split-screen"
        entry: dict[str, Any] = {
            "beat_id": bp.beat_id,
            "start": float(beat["start"]),
            "end": float(beat["end"]),
            "asset": plan.avatar_file or "avatar.mp4",
            "layout": layout,
        }
        entries.append(entry)
    return entries


def _generate_content_lane(
    plan: EditPlan, beat_map: dict, lane_name: str, catalog: Any
) -> list[dict]:
    entries = []
    beats_by_id = {b["id"]: b for b in beat_map.get("beats", [])}
    for bp in plan.beats:
        # Resolve filename: prefer inline, fall back to catalog
        filename = bp.selected_asset_filename
        if filename is None and bp.selected_asset_id and catalog is not None:
            asset = catalog.get(bp.selected_asset_id) if hasattr(catalog, "get") else None
            if asset is not None:
                filename = getattr(asset, "filename", None)
        if not filename:
            continue

        target_lane = _classify_content_lane(filename, bp)
        if target_lane != lane_name:
            continue

        beat = beats_by_id.get(bp.beat_id)
        if not beat:
            continue

        entry: dict[str, Any] = {
            "beat_id": bp.beat_id,
            "start": float(beat["start"]),
            "end": float(beat["end"]),
            "asset": filename,
        }

        # Render hints from BeatPlan
        if bp.zoom_moments:
            entry["zoom_moments"] = [z.to_dict() for z in bp.zoom_moments]
        if bp.playback_rate is not None:
            entry["playbackRate"] = bp.playback_rate
        if bp.render_overrides:
            for k, v in bp.render_overrides.items():
                if k not in entry:
                    entry[k] = v
        entries.append(entry)
    return entries


def _classify_content_lane(filename: str, beat_plan: BeatPlan) -> str:
    """Decide which content lane an asset belongs in.

    Order of preference:
      1. render_overrides.lane_hint (explicit)
      2. filename starts with 'broll' / 'broll_' → broll
      3. video extension → demo
      4. image extension → support
      5. default → demo
    """
    if beat_plan.render_overrides and "lane_hint" in beat_plan.render_overrides:
        return str(beat_plan.render_overrides["lane_hint"])
    name = filename.lower()
    if name.startswith("broll") or name.startswith("broll_"):
        return "broll"
    suffix = "." + name.rsplit(".", 1)[-1] if "." in name else ""
    if suffix in VIDEO_EXTS:
        return "demo"
    if suffix in IMAGE_EXTS:
        return "support"
    return "demo"


def _generate_caption_lane(plan: EditPlan, beat_map: dict) -> list[dict]:
    """Derive captions from beat_map. Suppressed templates emit nothing."""
    entries = []
    beats_by_id = {b["id"]: b for b in beat_map.get("beats", [])}
    for bp in plan.beats:
        if bp.caption_mode == "suppressed":
            continue
        beat = beats_by_id.get(bp.beat_id)
        if not beat:
            continue
        text = beat.get("phrase", "").strip()
        if not text:
            continue
        entries.append({
            "beat_id": bp.beat_id,
            "start": float(beat["start"]),
            "end": float(beat["end"]),
            "text": text,
        })
    return entries


def _parse_split_ratio_tuple(value: str) -> tuple[int, int] | None:
    try:
        a, b = value.split("/")
        ai, bi = int(a), int(b)
        if ai + bi != 100:
            return None
        return (ai, bi)
    except (ValueError, AttributeError):
        return None


# ── Editorial field attachment ────────────────────────────────────────────


def _attach_planning_fields(timeline: dict, plan: EditPlan) -> None:
    """Attach editorial metadata onto matching avatar/content lane entries.

    Adds template_id, proof_class, caption_mode (as captionMode),
    split_ratio (as splitRatio), avatar_mode, and proof_protected to the
    avatar entry for each beat. These are optional planning fields per the
    Phase A render contract — the renderer ignores them, but downstream
    tooling (critic, learning, retrieval) reads them.
    """
    plans_by_beat = {bp.beat_id: bp for bp in plan.beats}

    for lane_name in ("avatar", "demo", "broll", "support"):
        for entry in timeline["lanes"].get(lane_name, []):
            bid = entry.get("beat_id")
            bp = plans_by_beat.get(bid) if bid else None
            if bp is None:
                continue
            entry.setdefault("template_id", bp.template_id)
            if bp.proof_class is not None:
                entry.setdefault("proof_class", bp.proof_class)
            entry.setdefault("captionMode", bp.caption_mode)
            entry.setdefault("splitRatio", bp.split_ratio)
            entry.setdefault("avatar_mode", bp.avatar_mode)
            if bp.proof_protected:
                entry.setdefault("proof_protected", True)
