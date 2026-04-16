"""YouTube URL extractor.

Uses lib.assets.youtube (yt-dlp wrapper) to:
  1. Download the video + auto-captions
  2. Convert captions to plain text
  3. Extract one frame every N seconds
  4. Register everything in the project catalog
  5. Return a unified IngestionResult

Requirements:
  pip install -U yt-dlp
  ffmpeg on PATH
"""

from __future__ import annotations

import re
from pathlib import Path

from .base import BaseExtractor
from ..url_router import IngestionResult


class YouTubeExtractor(BaseExtractor):
    """Download a YouTube video, extract its transcript, and sample frames."""

    def extract(
        self,
        url: str,
        project_dir: Path,
        *,
        frames_every: float = 5.0,
        **kwargs,
    ) -> IngestionResult:
        from ...assets import youtube as yt  # lib.assets.youtube

        assets_dir = project_dir / "assets" / "sourced"
        frames_dir = project_dir / "assets" / "frames"
        assets_dir.mkdir(parents=True, exist_ok=True)
        frames_dir.mkdir(parents=True, exist_ok=True)

        print(f"  → Downloading YouTube video …")

        # ── Step 1: Download video + transcript ──────────────────────────────
        try:
            dl = yt.download(url, out_dir=assets_dir, project_dir=project_dir)
        except RuntimeError as e:
            print(f"  ✗ yt-dlp failed: {e}")
            print("    Install yt-dlp:  pip install -U yt-dlp")
            return IngestionResult(
                source_url=url,
                source_type="youtube",
                title="(download failed)",
                text_content="",
                key_claims=[],
                frames=[],
                assets=[],
                metadata={"error": str(e)},
            )

        video_path = Path(dl["video_path"])
        title = dl.get("title", "(unknown)")
        channel = dl.get("channel", "(unknown)")
        duration_s = dl.get("duration_s", 0)

        print(f"  ✓ Downloaded: {title} ({duration_s}s)")

        # ── Step 2: Extract transcript ────────────────────────────────────────
        text_content = ""
        subs_path = dl.get("subs_path")
        if subs_path:
            text_content = yt.vtt_to_text(Path(subs_path))
            word_count = len(text_content.split())
            print(f"  ✓ Transcript: {word_count} words")
        else:
            print("  ⚠  No subtitles found — transcript unavailable")
            print("     Tip: for private or caption-disabled videos, run:")
            print("       python -m lib.ingest.cli full <audio.mp3> projects/<slug>/")

        # ── Step 3: Extract key claims from transcript ────────────────────────
        key_claims = _claims_from_transcript(text_content)

        # ── Step 4: Extract frames ────────────────────────────────────────────
        print(f"  → Extracting frames every {frames_every}s …")
        try:
            frame_paths = yt.extract_frames(
                video_path=video_path,
                out_dir=frames_dir,
                every_seconds=frames_every,
                project_dir=project_dir,
                attribution_text=f"{channel} via YouTube",
            )
            frames = []
            for f in frame_paths:
                try:
                    frames.append(str(f.relative_to(project_dir)))
                except ValueError:
                    frames.append(str(f))
            print(f"  ✓ {len(frames)} frames extracted → assets/frames/")
        except RuntimeError as e:
            print(f"  ⚠  Frame extraction failed: {e}")
            frames = []

        # ── Build asset paths relative to project_dir ─────────────────────────
        assets = []
        for p in [video_path, Path(subs_path) if subs_path else None]:
            if p is None:
                continue
            try:
                assets.append(str(p.relative_to(project_dir)))
            except ValueError:
                assets.append(str(p))

        return IngestionResult(
            source_url=url,
            source_type="youtube",
            title=title,
            text_content=text_content,
            key_claims=key_claims,
            frames=frames,
            assets=assets,
            metadata={
                "channel": channel,
                "duration_s": duration_s,
                "video_path": assets[0] if assets else "",
                "has_transcript": bool(text_content),
                "frame_count": len(frames),
                "frames_every_s": frames_every,
            },
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _claims_from_transcript(text: str, max_claims: int = 20) -> list[str]:
    """
    Heuristically extract notable sentences from transcript text.

    Prefers sentences with numbers/percentages, power words, or product names.
    Falls back to first N sentences if no high-signal lines are found.
    """
    if not text:
        return []

    lines = [ln.strip() for ln in text.splitlines() if len(ln.strip()) > 20]

    scored: list[tuple[int, str]] = []
    for line in lines:
        score = 0
        # Numbers, percentages, multipliers
        if re.search(r"\d+[x%]|\d+\s*(times|percent|faster|better|less|more)", line, re.I):
            score += 3
        # Launch / announcement language
        if re.search(r"\b(new|first|only|best|free|launch|introduces|can now|never|just)\b", line, re.I):
            score += 2
        # Product / feature language
        if re.search(r"\b(feature|model|support|release|update|improvement|version)\b", line, re.I):
            score += 1
        scored.append((score, line))

    high_signal = [ln for score, ln in scored if score > 0]
    if high_signal:
        return high_signal[:max_claims]

    # Fallback: first N non-trivial lines
    return lines[:max_claims]
