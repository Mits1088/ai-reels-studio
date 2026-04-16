"""
URL ingestion router — detects URL type, routes to the right extractor,
and returns a unified IngestionResult.

The three URL types handled:
  youtube  → yt-dlp download + transcript + frame extraction
  twitter  → capture-x-video.js download
  webpage  → source-brief.js scrape + screenshots

Usage:
    from lib.ingest.url_router import ingest_url
    result = ingest_url("https://youtube.com/watch?v=xxx", Path("projects/my-reel"))
    result = ingest_url("https://anthropic.com/claude",   Path("projects/my-reel"))
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class IngestionResult:
    """Unified output from any URL ingestion — text, frames, assets, metadata."""

    source_url: str
    source_type: str           # "youtube" | "webpage" | "twitter"
    title: str                 # page/video/tweet title
    text_content: str          # transcript or article body text
    key_claims: list[str]      # extracted bullet points, headings, stats
    frames: list[str]          # paths to frames (relative to project_dir)
    assets: list[str]          # paths to other downloaded files
    metadata: dict[str, Any]   # source-specific extras (duration, channel, …)
    project_dir: Optional[Path] = None
    ingested_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # ── Serialisation ────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "source_url": self.source_url,
            "source_type": self.source_type,
            "title": self.title,
            "text_content": self.text_content,
            "key_claims": self.key_claims,
            "frames": self.frames,
            "assets": self.assets,
            "metadata": self.metadata,
            "ingested_at": self.ingested_at,
        }

    def write(self, project_dir: Path) -> None:
        """Write ingestion.json and, if missing, source-research.md."""
        project_dir = Path(project_dir)
        project_dir.mkdir(parents=True, exist_ok=True)

        # Always write machine-readable ingestion record
        (project_dir / "ingestion.json").write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Write source-research.md only if not already present
        # (webpage extractor delegates to source-brief.js which writes its own)
        research_path = project_dir / "source-research.md"
        if not research_path.exists():
            research_path.write_text(self._to_markdown(project_dir), encoding="utf-8")

    def _to_markdown(self, project_dir: Path) -> str:
        slug = project_dir.name
        claims_md = "\n".join(f"- {c}" for c in self.key_claims) or "_none extracted_"
        frames_md = "\n".join(f"- `{f}`" for f in self.frames[:20]) or "_none_"
        assets_md = "\n".join(f"- `{a}`" for a in self.assets) or "_none_"

        meta_lines = ""
        if self.metadata.get("duration_s"):
            meta_lines += f"- **Duration**: {self.metadata['duration_s']}s\n"
        if self.metadata.get("channel"):
            meta_lines += f"- **Channel**: {self.metadata['channel']}\n"
        if self.metadata.get("description"):
            meta_lines += f"- **Description**: {self.metadata['description']}\n"

        text_preview = self.text_content[:3000]
        if len(self.text_content) > 3000:
            text_preview += "\n... [truncated — see ingestion.json for full text]"

        return f"""# Source Research — {slug}

**URL**: {self.source_url}
**Type**: {self.source_type}
**Captured**: {self.ingested_at[:10]}

---

## Overview

- **Title**: {self.title}
{meta_lines}
---

## Transcript / Text Content

```
{text_preview}
```

---

## Key Claims Extracted

{claims_md}

---

## Frames Available

{frames_md}

---

## Other Assets

{assets_md}

---

## Claude — Action Required

Review the content above and produce:

1. **Hook** — the single most surprising or valuable claim (1 sentence)
2. **3 support points** — the strongest features or proof moments
3. **CTA** — what should the viewer do after watching?
4. **Demo candidates** — which moments should be shown on screen?
5. **Script direction** — educational / hype / comparison
6. **Frames to use directly** — which extracted frames can go straight into the reel?
7. **Assets still needed** — what needs to be captured separately?

Do not proceed to reel-script until the user has confirmed the brief direction.
"""


# ── URL type detection ────────────────────────────────────────────────────────

def detect_url_type(url: str) -> str:
    """Detect the type of content at a URL."""
    parsed = urlparse(url.strip())
    hostname = (parsed.hostname or "").lower().lstrip("www.")

    if hostname in ("youtube.com", "youtu.be") or "youtube.com" in hostname:
        return "youtube"

    if hostname in ("x.com", "twitter.com"):
        return "twitter"

    if parsed.path.lower().endswith(".pdf"):
        return "pdf"

    return "webpage"


# ── Router ─────────────────────────────────────────────────────────────────────

def ingest_url(
    url: str,
    project_dir: Path,
    *,
    frames_every: float = 5.0,
    write_output: bool = True,
) -> IngestionResult:
    """
    Ingest any URL and return a unified IngestionResult.

    Args:
        url:          Any URL — YouTube, web page, Twitter/X, PDF
        project_dir:  Project directory (e.g. projects/my-reel/)
        frames_every: For video sources — seconds between extracted frames
        write_output: Whether to write ingestion.json and source-research.md
    """
    project_dir = Path(project_dir)
    url_type = detect_url_type(url)

    if url_type == "youtube":
        from .extractors.youtube import YouTubeExtractor
        extractor: Any = YouTubeExtractor()
    elif url_type == "twitter":
        from .extractors.twitter import TwitterExtractor
        extractor = TwitterExtractor()
    elif url_type == "pdf":
        from .extractors.pdf import PDFExtractor
        extractor = PDFExtractor()
    else:
        from .extractors.webpage import WebpageExtractor
        extractor = WebpageExtractor()

    result = extractor.extract(url, project_dir, frames_every=frames_every)
    result.project_dir = project_dir

    if write_output:
        result.write(project_dir)

    return result
