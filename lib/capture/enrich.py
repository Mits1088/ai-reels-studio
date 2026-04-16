"""
lib/capture/enrich.py — non-destructive asset enrichment.

Reads assets/catalog.json (v2), runs a battery of fast checks against
each asset file, and writes back enrichment metadata under each asset's
'enrichment' block. Idempotent: re-running on already-enriched assets
is a no-op unless --force is passed.

Optional dependencies degrade gracefully:
  - Pillow:      hard requirement for any visual analysis. Skipped if missing.
  - cv2:         used for face detection. Skipped cleanly when unavailable.
  - pytesseract: used for accurate text density. Falls back to an
                 edge-density heuristic when missing.
  - ffprobe:     used for video metadata. Skipped cleanly when missing.
  - ffmpeg:      used for sampling video frames. Skipped cleanly when missing.

Per-measurement provenance:
  Every measurement returns a dict with at minimum:
    - method:         what produced the value (e.g. 'ffprobe', 'pillow', 'opencv-haarcascade')
    - skipped_reason: None when the measurement ran, otherwise a short reason string
    - derived_at:     ISO-8601 timestamp
    - confidence:     optional 0–1 score where applicable

Status semantics (the user-requested enrichment_status):
  - not_enriched: no enrichment block at all (or status='not_enriched')
  - full:         all applicable measurements ran successfully
  - partial:      some applicable measurements were skipped due to missing
                  optional dependencies, or hit recoverable errors
  - failed:       no measurement ran successfully (file unreadable, etc.)

Measurements that are not applicable for an asset type (e.g. motion on an
image) are skipped with a 'not_*' reason and do NOT lower the status —
the asset is still considered 'full' if every applicable check ran.

CLI:
    python -m lib.capture.enrich projects/<slug>
    python -m lib.capture.enrich projects/<slug> --dry-run
    python -m lib.capture.enrich projects/<slug> --force
    python -m lib.capture.enrich projects/<slug> --no-report
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── Optional dependency probes (module load time) ─────────────────────────

try:
    from PIL import Image, ImageStat, ImageChops, ImageFilter
    HAVE_PIL = True
except ImportError:
    Image = None  # type: ignore
    ImageStat = None  # type: ignore
    ImageChops = None  # type: ignore
    ImageFilter = None  # type: ignore
    HAVE_PIL = False

try:
    import cv2  # type: ignore
    HAVE_CV2 = True
except ImportError:
    cv2 = None  # type: ignore
    HAVE_CV2 = False

try:
    import pytesseract  # type: ignore
    HAVE_TESSERACT = True
except ImportError:
    pytesseract = None  # type: ignore
    HAVE_TESSERACT = False


def _have_ffprobe() -> bool:
    return shutil.which("ffprobe") is not None


def _have_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


# ── Constants ─────────────────────────────────────────────────────────────

ENRICHMENT_SCHEMA_VERSION = 1
ENRICHER_VERSION = "lib.capture.enrich@1.0.0"

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".gif"}
VIDEO_EXTS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".ogg", ".flac"}

# Skip-reason classification — used by status determination.
_NOT_APPLICABLE_REASONS = frozenset({
    "not_a_video",
    "not_visual_asset",
    "unsupported_extension",
})

# Substrings that mark a skip as "missing optional dep" (counts toward partial).
_DEP_MISSING_HINTS = (
    "_unavailable",
    "haarcascade_load_failed",  # cv2 present but cascade asset missing
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── ffprobe helpers ───────────────────────────────────────────────────────

def _ffprobe_streams(asset_path: Path) -> dict:
    """Return ffprobe JSON output for the asset. Raises on failure."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt",
        "-show_entries", "format=duration",
        "-of", "json",
        str(asset_path),
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if out.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {out.stderr.strip()[:200]}")
    return json.loads(out.stdout)


def _sample_video_frame(asset_path: Path) -> Path | None:
    """Extract a single frame at the midpoint of a video. Returns a temp path or None."""
    if not _have_ffprobe() or not _have_ffmpeg():
        return None
    try:
        data = _ffprobe_streams(asset_path)
        dur = float(data.get("format", {}).get("duration", "0") or "0")
    except Exception:
        return None
    if dur <= 0:
        dur = 1.0
    seek = max(0.0, dur * 0.5)
    tmp = Path(tempfile.gettempdir()) / f"enrich_frame_{asset_path.stem}_{int(time.time()*1000)}.png"
    cmd = [
        "ffmpeg", "-v", "quiet", "-y",
        "-ss", f"{seek:.2f}",
        "-i", str(asset_path),
        "-frames:v", "1",
        "-vf", "scale=320:-1",
        str(tmp),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=15)
        if result.returncode == 0 and tmp.exists():
            return tmp
    except Exception:
        pass
    return None


def _safe_unlink(path: Path | None) -> None:
    if path is None:
        return
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        pass


# ── Per-measurement helpers ───────────────────────────────────────────────

def _measure_technical(asset_path: Path, asset_type: str) -> dict:
    """Hard technical metadata via ffprobe (videos/audio) or Pillow (images)."""
    result: dict[str, Any] = {
        "method": "ffprobe+pillow",
        "skipped_reason": None,
        "derived_at": _now(),
    }

    suffix = asset_path.suffix.lower()

    if suffix in IMAGE_EXTS:
        if not HAVE_PIL:
            result["skipped_reason"] = "pillow_unavailable"
            return result
        try:
            with Image.open(asset_path) as img:
                w, h = img.size
                result["width"] = w
                result["height"] = h
                result["mode"] = img.mode
        except Exception as e:
            result["skipped_reason"] = f"pillow_error: {type(e).__name__}"
        return result

    if suffix in VIDEO_EXTS or suffix in AUDIO_EXTS:
        if not _have_ffprobe():
            result["skipped_reason"] = "ffprobe_unavailable"
            return result
        try:
            data = _ffprobe_streams(asset_path)
            video_streams = [s for s in data.get("streams", []) if s.get("codec_type") == "video"]
            audio_streams = [s for s in data.get("streams", []) if s.get("codec_type") == "audio"]

            if video_streams:
                v = video_streams[0]
                result["codec"] = v.get("codec_name", "")
                result["pix_fmt"] = v.get("pix_fmt", "")
                result["width"] = int(v.get("width", 0) or 0)
                result["height"] = int(v.get("height", 0) or 0)
                fps_str = v.get("r_frame_rate", "30/1") or "30/1"
                try:
                    num, den = fps_str.split("/")
                    den_i = int(den)
                    result["fps"] = round(int(num) / den_i, 2) if den_i else None
                except (ValueError, ZeroDivisionError):
                    result["fps"] = None

            result["has_audio"] = len(audio_streams) > 0
            duration = data.get("format", {}).get("duration")
            if duration:
                try:
                    result["duration_s"] = round(float(duration), 3)
                except (ValueError, TypeError):
                    pass
        except Exception as e:
            result["skipped_reason"] = f"ffprobe_error: {type(e).__name__}"
        return result

    result["skipped_reason"] = "unsupported_extension"
    return result


def _measure_appearance(asset_path: Path) -> dict:
    """Pillow-based dominant colors and brightness."""
    result: dict[str, Any] = {
        "method": "pillow",
        "skipped_reason": None,
        "derived_at": _now(),
    }

    if not HAVE_PIL:
        result["skipped_reason"] = "pillow_unavailable"
        return result

    suffix = asset_path.suffix.lower()
    sample_path: Path | None = None
    cleanup = False

    if suffix in IMAGE_EXTS:
        sample_path = asset_path
    elif suffix in VIDEO_EXTS:
        sample_path = _sample_video_frame(asset_path)
        cleanup = True
        if sample_path is None:
            result["skipped_reason"] = "frame_extraction_failed"
            return result
    else:
        result["skipped_reason"] = "not_visual_asset"
        return result

    try:
        with Image.open(sample_path) as img:
            img_rgb = img.convert("RGB")
            small = img_rgb.copy()
            small.thumbnail((100, 100))

            stat = ImageStat.Stat(small)
            avg_rgb = stat.mean[:3]
            brightness = sum(avg_rgb) / 3.0 / 255.0
            result["brightness"] = round(brightness, 3)

            quantized = small.quantize(colors=5).convert("RGB")
            colors = quantized.getcolors(maxcolors=10) or []
            colors.sort(reverse=True)  # by count
            hex_colors = []
            for _count, rgb in colors[:3]:
                if isinstance(rgb, tuple):
                    hex_colors.append("#{:02X}{:02X}{:02X}".format(*rgb[:3]))
            result["dominant_colors"] = hex_colors
        result["confidence"] = 0.8
    except Exception as e:
        result["skipped_reason"] = f"pillow_error: {type(e).__name__}"
    finally:
        if cleanup:
            _safe_unlink(sample_path)

    return result


def _measure_motion(asset_path: Path) -> dict:
    """Sample 5 evenly spaced frames, compute mean pairwise pixel diff as a motion proxy."""
    result: dict[str, Any] = {
        "method": "ffmpeg-frame-diff",
        "skipped_reason": None,
        "derived_at": _now(),
    }

    suffix = asset_path.suffix.lower()
    if suffix not in VIDEO_EXTS:
        result["skipped_reason"] = "not_a_video"
        return result

    if not _have_ffprobe() or not _have_ffmpeg():
        result["skipped_reason"] = "ffmpeg_unavailable"
        return result

    if not HAVE_PIL:
        result["skipped_reason"] = "pillow_unavailable"
        return result

    try:
        data = _ffprobe_streams(asset_path)
        dur = float(data.get("format", {}).get("duration", "0") or "0")
    except Exception as e:
        result["skipped_reason"] = f"ffprobe_error: {type(e).__name__}"
        return result

    if dur <= 0:
        result["skipped_reason"] = "zero_duration"
        return result

    timestamps = [dur * i / 6 for i in range(1, 6)]
    frames: list[Path] = []
    tmpdir = Path(tempfile.gettempdir())

    try:
        for i, t in enumerate(timestamps):
            tmp = tmpdir / f"motion_{asset_path.stem}_{int(time.time()*1000)}_{i}.png"
            cmd = [
                "ffmpeg", "-v", "quiet", "-y",
                "-ss", f"{t:.2f}",
                "-i", str(asset_path),
                "-frames:v", "1",
                "-vf", "scale=160:-1",
                str(tmp),
            ]
            r = subprocess.run(cmd, capture_output=True, timeout=10)
            if r.returncode == 0 and tmp.exists():
                frames.append(tmp)

        if len(frames) < 2:
            result["skipped_reason"] = "insufficient_frames"
            return result

        diffs: list[float] = []
        prev = None
        for f in frames:
            try:
                img = Image.open(f).convert("L")
                if prev is not None:
                    diff = ImageChops.difference(prev, img)
                    stat = ImageStat.Stat(diff)
                    diffs.append(stat.mean[0] / 255.0)
                prev = img
            except Exception:
                pass

        if not diffs:
            result["skipped_reason"] = "no_diffs_computed"
            return result

        score = sum(diffs) / len(diffs)
        result["score"] = round(score, 3)
        result["sample_count"] = len(frames)
        result["confidence"] = 0.6
    finally:
        for f in frames:
            _safe_unlink(f)

    return result


def _measure_text(asset_path: Path) -> dict:
    """Tesseract OCR if available, else edge-density heuristic."""
    result: dict[str, Any] = {
        "method": "edge-density-heuristic",
        "skipped_reason": None,
        "derived_at": _now(),
    }

    if not HAVE_PIL:
        result["skipped_reason"] = "pillow_unavailable"
        return result

    suffix = asset_path.suffix.lower()
    sample_path: Path | None = None
    cleanup = False

    if suffix in IMAGE_EXTS:
        sample_path = asset_path
    elif suffix in VIDEO_EXTS:
        sample_path = _sample_video_frame(asset_path)
        cleanup = True
        if sample_path is None:
            result["skipped_reason"] = "frame_extraction_failed"
            return result
    else:
        result["skipped_reason"] = "not_visual_asset"
        return result

    try:
        if HAVE_TESSERACT:
            result["method"] = "tesseract-ocr"
            with Image.open(sample_path) as img:
                text = pytesseract.image_to_string(img)
            words = len(text.split())
            score = min(words / 50.0, 1.0)
            result["score"] = round(score, 3)
            result["word_count"] = words
            result["confidence"] = 0.85
        else:
            with Image.open(sample_path) as img:
                gray = img.convert("L")
                gray.thumbnail((300, 300))
                edges = gray.filter(ImageFilter.FIND_EDGES)
                stat = ImageStat.Stat(edges)
                edge_score = min(stat.mean[0] / 50.0, 1.0)
                result["score"] = round(edge_score, 3)
                result["confidence"] = 0.4  # heuristic, low confidence
    except Exception as e:
        result["skipped_reason"] = f"text_error: {type(e).__name__}"
    finally:
        if cleanup:
            _safe_unlink(sample_path)

    return result


def _measure_faces(asset_path: Path) -> dict:
    """OpenCV haarcascade face detection. Skipped cleanly if cv2 unavailable."""
    result: dict[str, Any] = {
        "method": "opencv-haarcascade",
        "skipped_reason": None,
        "derived_at": _now(),
        "detected": False,
        "boxes": [],
    }

    if not HAVE_CV2:
        result["skipped_reason"] = "cv2_unavailable"
        return result

    suffix = asset_path.suffix.lower()
    sample_path: Path | None = None
    cleanup = False

    if suffix in IMAGE_EXTS:
        sample_path = asset_path
    elif suffix in VIDEO_EXTS:
        sample_path = _sample_video_frame(asset_path)
        cleanup = True
        if sample_path is None:
            result["skipped_reason"] = "frame_extraction_failed"
            return result
    else:
        result["skipped_reason"] = "not_visual_asset"
        return result

    try:
        img = cv2.imread(str(sample_path))
        if img is None:
            result["skipped_reason"] = "imread_failed"
            return result

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        haar_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        cascade = cv2.CascadeClassifier(haar_path)
        if cascade.empty():
            result["skipped_reason"] = "haarcascade_load_failed"
            return result

        faces = cascade.detectMultiScale(gray, 1.1, 5)
        h, w = img.shape[:2]
        boxes = []
        for (x, y, fw, fh) in faces:
            boxes.append({
                "x": round(float(x) / w * 100, 2),
                "y": round(float(y) / h * 100, 2),
                "w": round(float(fw) / w * 100, 2),
                "h": round(float(fh) / h * 100, 2),
            })
        result["detected"] = len(boxes) > 0
        result["boxes"] = boxes
        result["confidence"] = 0.7
    except Exception as e:
        result["skipped_reason"] = f"cv2_error: {type(e).__name__}"
    finally:
        if cleanup:
            _safe_unlink(sample_path)

    return result


# ── Composite derivations ─────────────────────────────────────────────────

def _normalize_aspect(width: int | None, height: int | None) -> tuple[str | None, float | None]:
    """Return (label, decimal). E.g. (1920, 1080) → ('16:9', 1.7778)."""
    if not width or not height:
        return None, None
    decimal = width / height

    common = {
        "16:9": 16 / 9,
        "9:16": 9 / 16,
        "4:3":  4 / 3,
        "3:4":  3 / 4,
        "1:1":  1.0,
        "21:9": 21 / 9,
        "5:4":  5 / 4,
        "2:1":  2.0,
    }
    for label, ratio in common.items():
        if abs(decimal - ratio) < 0.02:
            return label, round(decimal, 4)

    from math import gcd
    g = gcd(width, height)
    return f"{width // g}:{height // g}", round(decimal, 4)


def _compute_focal_point(faces: dict, asset_type: str) -> dict | None:
    """Derive focal point from face boxes if any, else center."""
    if asset_type not in ("video", "image"):
        return None
    if faces.get("detected") and faces.get("boxes"):
        boxes = faces["boxes"]
        largest = max(boxes, key=lambda b: b["w"] * b["h"])
        return {
            "x": round(largest["x"] + largest["w"] / 2, 2),
            "y": round(largest["y"] + largest["h"] / 2, 2),
            "source": "face",
            "confidence": 0.8,
        }
    return {
        "x": 50.0,
        "y": 50.0,
        "source": "center",
        "confidence": 0.5,
    }


def _derive_quality_flags(asset: dict, technical: dict) -> list[str]:
    flags: list[str] = []
    w = technical.get("width") or 0
    h = technical.get("height") or 0
    if w and h and (w * h) < (640 * 360):
        flags.append("low_resolution")

    asset_type = asset.get("type", "")
    if asset_type == "video":
        if technical.get("has_audio") is False:
            flags.append("no_audio_track")
        fps = technical.get("fps")
        if fps and abs(fps - 30) > 1.0:
            flags.append("non_standard_fps")
        pix_fmt = technical.get("pix_fmt")
        if pix_fmt and pix_fmt != "yuv420p":
            flags.append("non_standard_pix_fmt")

    return flags


def _derive_usable_display_modes(technical: dict, asset_type: str) -> list[str]:
    """Suggest which display modes the asset is suitable for."""
    if asset_type not in ("video", "image"):
        return []

    w = technical.get("width") or 0
    h = technical.get("height") or 0
    if not w or not h:
        return []

    decimal = w / h
    modes: list[str] = []

    if 0.75 <= decimal <= 1.5:
        modes.append("split-screen")
    if decimal > 1.5:
        modes.append("center-full")
        modes.append("responsive")
    if asset_type == "video":
        modes.append("hook-reveal")

    return modes or ["center-full"]


# ── Status classification ─────────────────────────────────────────────────

def _classify_skip(reason: str | None) -> str:
    """Classify a skipped_reason as one of: ran, not_applicable, dep_missing, error."""
    if reason is None:
        return "ran"
    if reason in _NOT_APPLICABLE_REASONS:
        return "not_applicable"
    for hint in _DEP_MISSING_HINTS:
        if hint in reason:
            return "dep_missing"
    return "error"


def _determine_status(measurements: list[dict]) -> str:
    """full / partial / failed based on classified measurement outcomes."""
    classes = [_classify_skip(m.get("skipped_reason")) for m in measurements]
    ran = sum(1 for c in classes if c == "ran")
    dep_missing = sum(1 for c in classes if c == "dep_missing")
    errors = sum(1 for c in classes if c == "error")
    applicable = ran + dep_missing + errors

    if applicable == 0:
        return "full"  # nothing to do (e.g. SFX with only technical applicable, which ran)
    if errors > 0 and ran == 0:
        return "failed"
    if dep_missing > 0 or errors > 0:
        return "partial"
    return "full"


# ── Public API ─────────────────────────────────────────────────────────────

def is_enriched(asset: dict) -> bool:
    """An asset is considered enriched if its enrichment block has status full or partial."""
    enrichment = asset.get("enrichment")
    if not isinstance(enrichment, dict):
        return False
    return enrichment.get("status") in ("full", "partial")


def enrich_asset(
    asset: dict,
    asset_path: Path,
    *,
    force: bool = False,
) -> dict:
    """Run enrichment for one asset. Returns a NEW asset dict (does not mutate input).

    Idempotent: returns the input unchanged if already enriched and not force=True.
    Non-destructive: existing editorial_tags are preserved across re-runs.
    On unrecoverable error, returns the asset with enrichment.status='failed'.
    Never raises.
    """
    if not force and is_enriched(asset):
        return asset

    new_asset = json.loads(json.dumps(asset))  # deep copy via JSON roundtrip

    if not asset_path.exists():
        new_asset["enrichment"] = {
            "status": "failed",
            "schema_version": ENRICHMENT_SCHEMA_VERSION,
            "derived_at": _now(),
            "derived_by": ENRICHER_VERSION,
            "failure_reason": f"file not found: {asset_path}",
            "aspect_ratio": None,
            "aspect_ratio_decimal": None,
            "quality_flags": ["file_missing"],
            "editorial_tags": (asset.get("enrichment") or {}).get("editorial_tags") or [],
            "usable_display_modes": [],
        }
        return new_asset

    asset_type = asset.get("type", "")

    technical  = _measure_technical(asset_path, asset_type)
    appearance = _measure_appearance(asset_path)
    motion     = _measure_motion(asset_path)
    text       = _measure_text(asset_path)
    faces      = _measure_faces(asset_path)

    measurements = [technical, appearance, motion, text, faces]

    aspect_str, aspect_decimal = _normalize_aspect(
        technical.get("width"), technical.get("height")
    )
    focal_point = _compute_focal_point(faces, asset_type)
    quality_flags = _derive_quality_flags(asset, technical)
    usable_modes = _derive_usable_display_modes(technical, asset_type)

    status = _determine_status(measurements)

    # Preserve any existing editorial tags across re-runs
    existing_tags = (asset.get("enrichment") or {}).get("editorial_tags") or []

    new_asset["enrichment"] = {
        "status": status,
        "schema_version": ENRICHMENT_SCHEMA_VERSION,
        "derived_at": _now(),
        "derived_by": ENRICHER_VERSION,
        "failure_reason": None,
        "aspect_ratio": aspect_str,
        "aspect_ratio_decimal": aspect_decimal,
        "technical":  technical,
        "appearance": appearance,
        "motion":     motion,
        "text":       text,
        "faces":      faces,
        "focal_point": focal_point,
        "quality_flags": quality_flags,
        "editorial_tags": list(existing_tags),
        "usable_display_modes": usable_modes,
    }

    return new_asset


def enrich_project(
    project_dir: Path,
    *,
    force: bool = False,
    dry_run: bool = False,
    write_report: bool = True,
) -> dict:
    """Enrich every asset in a project's catalog.

    Args:
        project_dir:  Path to the project directory.
        force:        If True, re-enrich already-enriched assets.
        dry_run:      If True, compute the enrichment but do not write changes.
        write_report: If True, write output/enrichment-report.json.

    Returns a dict with totals and per-asset results. Never raises.
    """
    cat_path = project_dir / "assets" / "catalog.json"
    if not cat_path.exists():
        return {
            "project": project_dir.name,
            "skipped": True,
            "reason": "no catalog.json",
            "totals": {},
            "assets": [],
        }

    try:
        with open(cat_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return {
            "project": project_dir.name,
            "skipped": True,
            "reason": f"invalid catalog.json: {e}",
            "totals": {},
            "assets": [],
        }

    assets_dir = project_dir / "assets"
    asset_results: list[dict] = []
    new_assets: list[dict] = []

    for asset in data.get("assets", []):
        # Phase E2.5 fix: tolerate vNext catalog 'file' alias AND its two
        # different conventions for the path:
        #   - claude-interactive-ui-pt1: 'file: "audio/x.mp4"'  (project-relative)
        #   - google-turboquant:         'file: "source/x.png"' (assets-relative)
        # We try both; whichever exists wins. If neither exists, we keep the
        # assets-relative path so enrich_asset can mark it failed cleanly.
        fname = asset.get("filename") or asset.get("file") or ""
        if not fname:
            asset_path = assets_dir
        else:
            candidate_assets_rel = assets_dir / fname
            candidate_project_rel = project_dir / fname
            if candidate_assets_rel.exists():
                asset_path = candidate_assets_rel
            elif candidate_project_rel.exists():
                asset_path = candidate_project_rel
            else:
                asset_path = candidate_assets_rel  # default; enrich_asset will mark file_missing
        before_status = (asset.get("enrichment") or {}).get("status", "not_enriched")

        if not force and is_enriched(asset):
            new_assets.append(asset)
            asset_results.append({
                "id": asset.get("id"),
                "filename": fname,
                "before": before_status,
                "after": before_status,
                "skipped": True,
                "reason": "already_enriched",
                "skipped_checks": [],
            })
            continue

        new_asset = enrich_asset(asset, asset_path, force=force)
        new_assets.append(new_asset)
        after_status = new_asset.get("enrichment", {}).get("status", "not_enriched")
        skipped_checks = []
        for k in ("technical", "appearance", "motion", "text", "faces"):
            block = new_asset.get("enrichment", {}).get(k) or {}
            reason = block.get("skipped_reason")
            if reason and _classify_skip(reason) != "not_applicable":
                skipped_checks.append({"check": k, "reason": reason})

        asset_results.append({
            "id": asset.get("id"),
            "filename": fname,
            "before": before_status,
            "after": after_status,
            "skipped": False,
            "skipped_checks": skipped_checks,
        })

    totals = {
        "total":           len(asset_results),
        "full":            sum(1 for r in asset_results if r["after"] == "full"),
        "partial":         sum(1 for r in asset_results if r["after"] == "partial"),
        "failed":          sum(1 for r in asset_results if r["after"] == "failed"),
        "not_enriched":    sum(1 for r in asset_results if r["after"] == "not_enriched"),
        "skipped_already": sum(1 for r in asset_results if r.get("reason") == "already_enriched"),
    }

    summary = {
        "project": project_dir.name,
        "dry_run": dry_run,
        "force": force,
        "enricher_version": ENRICHER_VERSION,
        "enrichment_schema_version": ENRICHMENT_SCHEMA_VERSION,
        "optional_deps": {
            "pillow":    HAVE_PIL,
            "cv2":       HAVE_CV2,
            "tesseract": HAVE_TESSERACT,
            "ffprobe":   _have_ffprobe(),
            "ffmpeg":    _have_ffmpeg(),
        },
        "derived_at": _now(),
        "totals": totals,
        "assets": asset_results,
    }

    if not dry_run:
        data["assets"] = new_assets
        with open(cat_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

        if write_report:
            report_path = project_dir / "output" / "enrichment-report.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
                f.write("\n")

    return summary


# ── CLI ────────────────────────────────────────────────────────────────────

def _print_summary(summary: dict, dry_run: bool) -> None:
    if summary.get("skipped"):
        print(f"SKIP: {summary.get('project')} — {summary.get('reason')}")
        return

    deps = summary["optional_deps"]
    print(f"Project: {summary.get('project')}")
    print(
        f"Optional deps: pillow={deps['pillow']}, cv2={deps['cv2']}, "
        f"tesseract={deps['tesseract']}, ffprobe={deps['ffprobe']}, ffmpeg={deps['ffmpeg']}"
    )
    print(f"Mode: {'dry-run' if dry_run else 'apply'}{', force' if summary['force'] else ''}")
    print()
    totals = summary["totals"]
    print(f"Totals: {totals.get('total', 0)} assets")
    print(f"  full:           {totals.get('full', 0)}")
    print(f"  partial:        {totals.get('partial', 0)}")
    print(f"  failed:         {totals.get('failed', 0)}")
    print(f"  already (skip): {totals.get('skipped_already', 0)}")
    if dry_run:
        print()
        print("(Dry run — no files modified. Remove --dry-run to apply.)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enrich asset catalog with technical and editorial metadata"
    )
    parser.add_argument("project_dir", type=Path, help="Project directory")
    parser.add_argument("--force", action="store_true", help="Re-enrich already-enriched assets")
    parser.add_argument("--dry-run", action="store_true", help="Compute enrichment but do not write changes")
    parser.add_argument("--no-report", action="store_true", help="Do not write output/enrichment-report.json")
    args = parser.parse_args()

    if not args.project_dir.exists():
        print(f"ERROR: project_dir not found: {args.project_dir}")
        sys.exit(1)

    summary = enrich_project(
        args.project_dir,
        force=args.force,
        dry_run=args.dry_run,
        write_report=not args.no_report,
    )
    _print_summary(summary, args.dry_run)


if __name__ == "__main__":
    main()
