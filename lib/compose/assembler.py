"""
Reel assembler — reads timeline.json + beat-map.json and produces rendered frames.

This is the orchestrator that:
  1. Loads timeline data
  2. Assigns scene types to beats via the scene grammar
  3. Resolves which assets are active at each moment
  4. Calls the renderer to produce frames
  5. Handles transitions between scenes
  6. Outputs key frames (preview stills) or full frame sequences
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from PIL import Image

from . import layout as L
from .scene_grammar import assign_scene_types
from .renderer import (
    compose_frame, apply_transition, render_caption, clear_asset_cache,
    COLORS, _get_font, load_asset,
)


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class ActiveLayers:
    """What's visible at a given time."""
    beat_id: str | None = None
    scene_type: str = "context"
    avatar_file: str | None = None
    demo_file: str | None = None
    support_file: str | None = None
    caption_text: str | None = None
    sfx_file: str | None = None
    transition: dict | None = None  # {"type": "fade", "duration": 0.3}

    def __repr__(self):
        parts = [f"scene={self.scene_type}"]
        if self.avatar_file:
            parts.append(f"avatar={self.avatar_file}")
        if self.demo_file:
            parts.append(f"demo={self.demo_file}")
        if self.support_file:
            parts.append(f"support={self.support_file}")
        if self.caption_text:
            parts.append(f"caption={self.caption_text!r}")
        return f"ActiveLayers({', '.join(parts)})"


@dataclass
class SfxEvent:
    """An SFX trigger point."""
    time: float
    file: str
    beat_id: str | None = None


# ── Timeline resolver ────────────────────────────────────────────────────────

def _find_active(entries: list[dict], t: float) -> dict | None:
    """Find the entry active at time t in a lane."""
    for entry in entries:
        if entry["start"] <= t < entry["end"]:
            return entry
    return None


def resolve_layers(timeline: dict, beat_map: dict, t: float) -> ActiveLayers:
    """
    Resolve which assets and captions are active at time t.

    Reads timeline lanes and beat-map to determine scene type.
    """
    lanes = timeline.get("lanes", {})

    # Find active entries in each lane
    avatar_entry = _find_active(lanes.get("avatar", []), t)
    demo_entry = _find_active(lanes.get("demo", []), t)
    support_entry = _find_active(lanes.get("support", []), t)
    caption_entry = _find_active(lanes.get("captions", []), t)

    # Determine which beat we're in
    beat_id = None
    scene_type = "context"
    for entry in [avatar_entry, demo_entry, support_entry, caption_entry]:
        if entry and "beat_id" in entry:
            beat_id = entry["beat_id"]
            break

    # Look up scene type from beat map
    if beat_id:
        for beat in beat_map.get("beats", []):
            if beat["id"] == beat_id:
                scene_type = beat.get("scene_type", "context")
                break

    # Get transition from the primary visual entry
    transition = None
    for entry in [demo_entry, avatar_entry, support_entry]:
        if entry and "transition" in entry:
            transition = entry["transition"]
            break

    return ActiveLayers(
        beat_id=beat_id,
        scene_type=scene_type,
        avatar_file=avatar_entry["asset"] if avatar_entry else None,
        demo_file=demo_entry["asset"] if demo_entry else None,
        support_file=support_entry["asset"] if support_entry else None,
        caption_text=caption_entry["text"] if caption_entry else None,
        transition=transition,
    )


def collect_sfx_events(timeline: dict) -> list[SfxEvent]:
    """Extract all SFX trigger points from the timeline."""
    events = []
    for entry in timeline.get("lanes", {}).get("sfx", []):
        events.append(SfxEvent(
            time=entry["start"],
            file=entry["asset"],
            beat_id=entry.get("beat_id"),
        ))
    return sorted(events, key=lambda e: e.time)


# ── Key frame generator ─────────────────────────────────────────────────────

def generate_keyframes(
    timeline: dict,
    beat_map: dict,
    assets_dir: Path,
) -> list[tuple[float, str, Image.Image]]:
    """
    Generate one key frame per beat — the midpoint of each beat.

    Returns list of (time, beat_id, frame_image).
    """
    clear_asset_cache()

    # Assign scene types
    beats = beat_map.get("beats", [])
    total = beat_map.get("total_duration", timeline.get("total_duration", 30))
    assign_scene_types(beats, total)

    keyframes = []
    for beat in beats:
        t = (beat["start"] + beat["end"]) / 2  # midpoint
        layers = resolve_layers(timeline, beat_map, t)

        frame = compose_frame(
            layers.scene_type,
            assets_dir,
            avatar_file=layers.avatar_file,
            demo_file=layers.demo_file,
            support_file=layers.support_file,
            caption_text=layers.caption_text,
        )

        keyframes.append((t, beat["id"], frame))

    return keyframes


# ── Frame sequence generator (for video encoding) ───────────────────────────

def generate_frame_at(
    timeline: dict,
    beat_map: dict,
    assets_dir: Path,
    t: float,
) -> Image.Image:
    """Render a single frame at time t."""
    layers = resolve_layers(timeline, beat_map, t)
    return compose_frame(
        layers.scene_type,
        assets_dir,
        avatar_file=layers.avatar_file,
        demo_file=layers.demo_file,
        support_file=layers.support_file,
        caption_text=layers.caption_text,
    )


# ── Preview sheet generator ─────────────────────────────────────────────────

def render_preview_sheet(
    keyframes: list[tuple[float, str, Image.Image]],
    cols: int = 3,
    thumb_width: int = 360,
) -> Image.Image:
    """
    Render all keyframes into a contact sheet for quick review.

    Shows beat ID, time, and scene type under each thumbnail.
    """
    if not keyframes:
        return Image.new("RGB", (100, 100), (30, 30, 30))

    thumb_height = int(thumb_width * L.HEIGHT / L.WIDTH)
    label_height = 60
    cell_height = thumb_height + label_height

    rows = math.ceil(len(keyframes) / cols)
    sheet_w = cols * thumb_width
    sheet_h = rows * cell_height

    sheet = Image.new("RGB", (sheet_w, sheet_h), (20, 20, 25))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(sheet)
    font = _get_font(18)

    for i, (t, beat_id, frame) in enumerate(keyframes):
        col = i % cols
        row = i // cols
        x = col * thumb_width
        y = row * cell_height

        # Thumbnail
        thumb = frame.convert("RGB").resize(
            (thumb_width, thumb_height), Image.Resampling.LANCZOS
        )
        sheet.paste(thumb, (x, y))

        # Label
        label = f"{beat_id} @ {t:.1f}s"
        draw.text((x + 8, y + thumb_height + 4), label,
                  fill=(200, 200, 200), font=font)

    return sheet


# ── Composition report ───────────────────────────────────────────────────────

def generate_composition_report(
    timeline: dict,
    beat_map: dict,
) -> list[dict]:
    """
    Generate a human-readable report showing how the reel is composed.

    Returns a list of dicts, one per beat, showing:
      - beat_id, scene_type, time range
      - which lanes are active and what assets they use
      - transitions and SFX
    """
    beats = beat_map.get("beats", [])
    total = beat_map.get("total_duration", 30)
    assign_scene_types(beats, total)

    sfx_events = collect_sfx_events(timeline)

    report = []
    for beat in beats:
        t = (beat["start"] + beat["end"]) / 2
        layers = resolve_layers(timeline, beat_map, t)

        # Find SFX in this beat's time range
        beat_sfx = [s for s in sfx_events if beat["start"] <= s.time < beat["end"]]

        entry = {
            "beat_id": beat["id"],
            "scene_type": beat.get("scene_type", "?"),
            "time": f"{beat['start']:.1f}s – {beat['end']:.1f}s",
            "phrase": beat.get("phrase", ""),
            "layers": {
                "avatar": layers.avatar_file or "—",
                "demo": layers.demo_file or "—",
                "support": layers.support_file or "—",
                "caption": layers.caption_text or "—",
            },
            "transition": layers.transition or {"type": "cut"},
            "sfx": [{"file": s.file, "at": f"{s.time:.1f}s"} for s in beat_sfx],
        }
        report.append(entry)

    return report
