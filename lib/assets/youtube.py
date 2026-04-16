"""YouTube source video fetcher via yt-dlp.

Wraps yt-dlp for the reel pipeline's needs:
- Download a YouTube video at the best quality available
- Extract subtitles / auto-captions as a transcript
- Extract frames at regular intervals via ffmpeg
- Register everything in the project's sourced catalog

Used in Phase 0 (source-brief) and Phase 4 (capture-demo) when a
YouTube URL is the source of truth for a demo or proof clip.

Requirements:
  - yt-dlp installed:  python -m pip install -U yt-dlp
  - ffmpeg on PATH (already required by the rest of the pipeline)

LICENSE NOTE: yt-dlp downloads content for personal use; the user is
responsible for verifying that the source video's license permits the
intended reel use. For OFFICIAL Anthropic / OpenAI / Google / etc.
brand channels, fair use for editorial commentary on a product launch
is the typical justification — but the user should always confirm.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import catalog as cat


LICENSE = "Source-dependent (yt-dlp download)"
ATTRIBUTION_REQUIRED = True  # Always credit the source channel


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a subprocess and capture output."""
    return subprocess.run(
        cmd, capture_output=True, text=True, check=check, encoding="utf-8"
    )


def video_id(url: str) -> str:
    """Extract the YouTube video ID from a URL."""
    parsed = urlparse(url)
    if parsed.hostname in ("youtu.be",):
        return parsed.path.lstrip("/")
    if parsed.hostname and "youtube.com" in parsed.hostname:
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [""])[0]
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/")[2]
        if parsed.path.startswith("/embed/"):
            return parsed.path.split("/")[2]
    raise ValueError(f"Could not extract video ID from {url}")


def info(url: str) -> dict:
    """Return yt-dlp's full metadata dict for a URL."""
    result = _run(
        ["python", "-m", "yt_dlp", "-J", "--no-playlist", url],
        check=True,
    )
    return json.loads(result.stdout)


def download(
    url: str,
    out_dir: Path,
    project_dir: Path | None = None,
    filename: str | None = None,
    write_subs: bool = True,
    write_auto_subs: bool = True,
) -> dict:
    """Download a YouTube video, transcript, and metadata.

    Args:
      url: YouTube URL
      out_dir: Directory to save the video and assets
      project_dir: If provided, register everything in the catalog
      filename: Output stem (without extension); default: video ID
      write_subs: Try to download manual subtitles
      write_auto_subs: Fall back to auto-generated captions if no manual subs

    Returns:
      Dict with keys: video_path, info_path, subs_path (or None), title, duration_s
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    vid = video_id(url)
    stem = filename or vid
    output_template = str(out_dir / f"{stem}.%(ext)s")

    cmd = [
        "python", "-m", "yt_dlp",
        "--no-playlist",
        "-S", "ext:mp4:m4a,res:1080,fps:30",
        "--merge-output-format", "mp4",
        "--write-info-json",
        "-o", output_template,
        url,
    ]
    if write_subs:
        cmd += ["--write-sub", "--sub-langs", "en.*,en"]
    if write_auto_subs:
        cmd += ["--write-auto-sub"]

    print(f"  → downloading {url} ...")
    proc = _run(cmd, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"yt-dlp failed (exit {proc.returncode}):\n"
            f"STDOUT: {proc.stdout[-500:]}\n"
            f"STDERR: {proc.stderr[-500:]}"
        )

    # Locate the downloaded files
    video_path = next(out_dir.glob(f"{stem}.mp4"), None) or next(
        out_dir.glob(f"{stem}.webm"), None
    )
    if video_path is None:
        produced = list(out_dir.glob(f"{stem}.*"))
        raise RuntimeError(
            f"yt-dlp completed but no video file found. Produced: {produced}"
        )

    info_path = out_dir / f"{stem}.info.json"
    info_data = (
        json.loads(info_path.read_text(encoding="utf-8"))
        if info_path.exists()
        else {}
    )
    title = info_data.get("title", "(unknown)")
    channel = info_data.get("channel", info_data.get("uploader", "(unknown)"))
    duration_s = info_data.get("duration", 0)

    # Locate subtitle file (manual first, then auto)
    subs_path = None
    for ext in (".en.vtt", ".en-US.vtt", ".en-GB.vtt", ".vtt"):
        candidate = out_dir / f"{stem}{ext}"
        if candidate.exists():
            subs_path = candidate
            break

    # Register
    if project_dir is not None:
        try:
            rel_video = str(video_path.relative_to(Path(project_dir)))
        except ValueError:
            rel_video = str(video_path)
        cat.register(
            project_dir,
            cat.SourcedAsset(
                source="youtube",
                asset_type="video",
                local_path=rel_video,
                query=url,
                license=LICENSE,
                attribution_required=True,
                attribution_text=f"{channel} via YouTube",
                metadata={
                    "video_id": vid,
                    "title": title,
                    "channel": channel,
                    "duration_s": duration_s,
                    "url": url,
                },
            ),
        )
        if subs_path is not None:
            try:
                rel_subs = str(subs_path.relative_to(Path(project_dir)))
            except ValueError:
                rel_subs = str(subs_path)
            cat.register(
                project_dir,
                cat.SourcedAsset(
                    source="youtube",
                    asset_type="transcript",
                    local_path=rel_subs,
                    query=url,
                    license=LICENSE,
                    attribution_required=True,
                    attribution_text=f"{channel} via YouTube",
                    metadata={"video_id": vid, "url": url},
                ),
            )

    return {
        "video_path": str(video_path),
        "info_path": str(info_path) if info_path.exists() else None,
        "subs_path": str(subs_path) if subs_path else None,
        "title": title,
        "channel": channel,
        "duration_s": duration_s,
    }


def extract_frames(
    video_path: Path,
    out_dir: Path,
    every_seconds: float = 5.0,
    project_dir: Path | None = None,
    prefix: str | None = None,
    attribution_text: str = "",
) -> list[Path]:
    """Extract frames from a video at regular intervals using ffmpeg.

    Args:
      video_path: Source video
      out_dir: Directory for the extracted frames
      every_seconds: Frame interval in seconds (e.g. 5.0 = one frame per 5s)
      project_dir: If provided, register frames in the catalog
      prefix: Filename prefix (default: video stem)

    Returns:
      List of paths to extracted frame files.
    """
    video_path = Path(video_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = prefix or video_path.stem
    pattern = out_dir / f"{stem}-frame-%03d.png"
    fps = 1.0 / every_seconds

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vf", f"fps={fps}",
        "-vsync", "0",
        str(pattern),
    ]
    proc = _run(cmd, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"ffmpeg frame extraction failed (exit {proc.returncode}):\n"
            f"STDERR: {proc.stderr[-500:]}"
        )

    frames = sorted(out_dir.glob(f"{stem}-frame-*.png"))
    if project_dir is not None:
        for i, frame in enumerate(frames):
            try:
                rel_path = str(frame.relative_to(Path(project_dir)))
            except ValueError:
                rel_path = str(frame)
            cat.register(
                project_dir,
                cat.SourcedAsset(
                    source="youtube",
                    asset_type="frame",
                    local_path=rel_path,
                    query=str(video_path),
                    license=LICENSE,
                    attribution_required=True,
                    attribution_text=attribution_text,
                    metadata={
                        "frame_index": i + 1,
                        "approx_t_seconds": (i + 1) * every_seconds - every_seconds / 2,
                    },
                ),
            )
    return frames


def vtt_to_text(vtt_path: Path) -> str:
    """Convert a WebVTT subtitle file to plain text (for LLM context).

    Strips timestamps, cue identifiers, and HTML tags. Deduplicates
    consecutive identical lines (yt auto-captions repeat heavily).
    """
    vtt = Path(vtt_path).read_text(encoding="utf-8")
    lines: list[str] = []
    for raw in vtt.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.upper().startswith(("WEBVTT", "NOTE", "STYLE")):
            continue
        if "-->" in line:
            continue
        if re.match(r"^\d+$", line):
            continue
        # Strip <00:00:00.000> inline timestamps and <c> tags
        line = re.sub(r"<[^>]+>", "", line).strip()
        if not line:
            continue
        if lines and lines[-1] == line:
            continue
        lines.append(line)
    return "\n".join(lines)
