"""
Asset registration — import files into the project and add them to catalog.json.

Two workflows:
  1. register_demo()  — screen recordings, product walkthroughs, UI clips
  2. register_asset() — stills, screenshots, logos, charts, overlays, audio
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from datetime import datetime, timezone

from .catalog import (
    AssetEntry, Catalog, load_catalog, save_catalog,
    ASSET_TYPES, ASSET_ROLES, ASSET_SOURCES, TYPE_EXTENSIONS, ALL_VALID_EXTENSIONS,
)


class RegisterError(RuntimeError):
    pass


# ── Naming ───────────────────────────────────────────────────────────────────

ASSET_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def make_asset_id(role: str, description: str, beat_ids: list[str]) -> str:
    """
    Generate a descriptive, beat-linked asset ID.

    Examples:
      demo_deploy-click_beat-03
      support_success-anim_beat-04
      avatar_talking-head_beat-01-02
    """
    # Slugify description: lowercase, replace spaces/special with dashes, truncate
    slug = re.sub(r"[^a-z0-9]+", "-", description.lower()).strip("-")[:30]

    # Beat suffix
    if len(beat_ids) <= 2:
        beat_part = "-".join(b.replace("beat-", "") for b in sorted(beat_ids))
    else:
        nums = sorted(b.replace("beat-", "") for b in beat_ids)
        beat_part = f"{nums[0]}-to-{nums[-1]}"

    return f"{role}_{slug}_beat-{beat_part}"


# ── Probing ──────────────────────────────────────────────────────────────────

def probe_image_dimensions(path: Path) -> dict | None:
    """Get image dimensions using Pillow if available."""
    try:
        from PIL import Image
        with Image.open(path) as img:
            return {"w": img.width, "h": img.height}
    except Exception:
        return None


def probe_video_info(path: Path) -> tuple[float | None, dict | None]:
    """Get video duration and dimensions via ffprobe if available."""
    try:
        import subprocess
        ffprobe = shutil.which("ffprobe")
        if not ffprobe:
            return None, None

        # Duration
        dur_cmd = [
            ffprobe, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
        dur_result = subprocess.run(dur_cmd, capture_output=True, text=True)
        duration = round(float(dur_result.stdout.strip()), 3) if dur_result.returncode == 0 else None

        # Dimensions
        dim_cmd = [
            ffprobe, "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=s=x:p=0",
            str(path),
        ]
        dim_result = subprocess.run(dim_cmd, capture_output=True, text=True)
        dims = None
        if dim_result.returncode == 0 and "x" in dim_result.stdout:
            w, h = dim_result.stdout.strip().split("x")
            dims = {"w": int(w), "h": int(h)}

        return duration, dims
    except Exception:
        return None, None


def _infer_type_from_extension(path: Path) -> str | None:
    """Guess asset type from file extension."""
    ext = path.suffix.lower()
    for asset_type, exts in TYPE_EXTENSIONS.items():
        if ext in exts:
            # Ambiguous: .png could be image, logo, chart, icon, overlay
            # Default to most common
            if asset_type in ("image", "video", "sfx", "music"):
                return asset_type
    return None


# ── Registration ─────────────────────────────────────────────────────────────

def register_asset(
    source_path: Path,
    project_dir: Path,
    *,
    asset_type: str,
    role: str,
    linked_beats: list[str],
    description: str,
    scene: int | None = None,
    asset_id: str | None = None,
    source: str = "import",
) -> AssetEntry:
    """
    Register any asset (image, video, audio, overlay) into the project catalog.

    Copies the file into assets/, probes metadata, adds to catalog.json.
    """
    # ── Validate inputs ──────────────────────────────────────────────────
    if not source_path.exists():
        raise RegisterError(f"Source file not found: {source_path}")

    ext = source_path.suffix.lower()
    if ext not in ALL_VALID_EXTENSIONS:
        raise RegisterError(
            f"Unsupported extension '{ext}'. Valid: {sorted(ALL_VALID_EXTENSIONS)}"
        )

    if asset_type not in ASSET_TYPES:
        raise RegisterError(f"Invalid type '{asset_type}'. Valid: {sorted(ASSET_TYPES)}")

    if role not in ASSET_ROLES:
        raise RegisterError(f"Invalid role '{role}'. Valid: {sorted(ASSET_ROLES)}")

    if source not in ASSET_SOURCES:
        raise RegisterError(f"Invalid source '{source}'. Valid: {sorted(ASSET_SOURCES)}")

    if not linked_beats:
        raise RegisterError("Asset must link to at least one beat. No orphan assets allowed.")

    if not description.strip():
        raise RegisterError("Asset must have a description explaining its purpose.")

    # ── Generate ID ──────────────────────────────────────────────────────
    if asset_id is None:
        asset_id = make_asset_id(role, description, linked_beats)

    if not ASSET_ID_RE.match(asset_id):
        raise RegisterError(f"Invalid asset ID '{asset_id}'. Must match: {ASSET_ID_RE.pattern}")

    # ── Check for duplicates ─────────────────────────────────────────────
    assets_dir = project_dir / "assets"
    catalog_path = assets_dir / "catalog.json"
    catalog = load_catalog(catalog_path)

    if catalog.get(asset_id):
        raise RegisterError(f"Asset ID '{asset_id}' already exists in catalog")

    # ── Copy file ────────────────────────────────────────────────────────
    filename = f"{asset_id}{ext}"
    dest = assets_dir / filename
    assets_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, dest)

    # ── Probe metadata ───────────────────────────────────────────────────
    duration_s = None
    dimensions = None

    if asset_type == "video":
        duration_s, dimensions = probe_video_info(dest)
    elif asset_type in ("image", "logo", "chart", "icon", "overlay"):
        dimensions = probe_image_dimensions(dest)

    # ── Add to catalog ───────────────────────────────────────────────────
    entry = AssetEntry(
        id=asset_id,
        filename=filename,
        type=asset_type,
        role=role,
        linked_beats=linked_beats,
        description=description,
        scene=scene,
        duration_s=duration_s,
        dimensions=dimensions,
        source=source,
    )
    catalog.assets.append(entry)
    save_catalog(catalog, catalog_path)

    return entry


def register_demo(
    source_path: Path,
    project_dir: Path,
    *,
    linked_beats: list[str],
    description: str,
    scene: int | None = None,
    asset_id: str | None = None,
) -> AssetEntry:
    """
    Register a demo capture (screen recording, product walkthrough).

    Shorthand for register_asset with type=video, role=demo, source=capture.
    """
    return register_asset(
        source_path, project_dir,
        asset_type="video",
        role="demo",
        linked_beats=linked_beats,
        description=description,
        scene=scene,
        asset_id=asset_id,
        source="capture",
    )


# ── Project status update ────────────────────────────────────────────────────

def finalize_assets(project_dir: Path) -> None:
    """
    Update project.json to assets_ready after all assets are registered.
    Call this when the operator is done adding assets.
    """
    import json

    pj_path = project_dir / "project.json"
    if not pj_path.exists():
        return

    with open(pj_path, "r", encoding="utf-8") as f:
        project = json.load(f)

    project["phase"] = "asset-prep"
    project["status"] = "completed"
    project["updated"] = datetime.now(timezone.utc).isoformat()

    with open(pj_path, "w", encoding="utf-8") as f:
        json.dump(project, f, indent=2, ensure_ascii=False)
