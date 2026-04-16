"""Webpage URL extractor.

Delegates to the existing source-brief.js script (which already handles
cookie dismissal, section screenshots, image downloads, and source-research.md).

After source-brief.js writes its JSON output, this extractor reads it and
returns a unified IngestionResult that the rest of the ingestion layer
can work with.

Requirements:
  node on PATH
  npm install (run once in D:/Reel generation/ — installs playwright + dotenv)
  npx playwright install chromium (run once)
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .base import BaseExtractor
from ..url_router import IngestionResult


class WebpageExtractor(BaseExtractor):
    """Scrape a web page using the existing source-brief.js Playwright script."""

    def extract(
        self,
        url: str,
        project_dir: Path,
        *,
        frames_every: float = 5.0,  # not used for pages, kept for API compatibility
        **kwargs,
    ) -> IngestionResult:
        root = Path(__file__).resolve().parents[3]  # D:/Reel generation/
        script = root / "lib" / "capture" / "source-brief.js"
        slug = project_dir.name

        if not script.exists():
            return _error_result(url, f"source-brief.js not found at {script}")

        print(f"  → Scraping page with Playwright …")

        cmd = ["node", str(script), "--url", url, "--project", slug]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(root),
            timeout=120,
        )

        if proc.stdout:
            # Pass through the script's own progress output
            for line in proc.stdout.splitlines():
                print(f"    {line}")

        if proc.returncode != 0:
            print(f"  ⚠  source-brief.js exited {proc.returncode}")
            if proc.stderr:
                for line in proc.stderr.splitlines()[-10:]:
                    print(f"    {line}")
            # Partial output is still useful — fall through to read what was written

        # ── Read source-brief.js JSON output ─────────────────────────────────
        json_path = project_dir / "source-research.json"
        data: dict = {}
        if json_path.exists():
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass

        page = data.get("page", {})
        title = page.get("title", "(unknown)")
        description = page.get("description", "")

        # Build text content from extracted sections
        sections = data.get("sections", [])
        text_parts = []
        for s in sections:
            heading = s.get("heading", "")
            body = s.get("body", "")
            if heading:
                text_parts.append(f"{heading}\n{body}" if body else heading)
        text_content = "\n\n".join(text_parts)

        # Key claims = feature list bullets from the page
        feature_items: list[str] = data.get("features", [])
        heading_claims = [s["heading"] for s in sections if s.get("heading")]

        # Prefer feature bullets; supplement with headings if thin
        if len(feature_items) >= 5:
            key_claims = feature_items[:20]
        else:
            key_claims = (heading_claims + feature_items)[:20]

        # Frames = section screenshots captured by source-brief.js
        assets_info = data.get("assets", {})
        screenshot_names: list[str] = assets_info.get("screenshots", [])
        frames = [f"assets/source/screenshots/{s}" for s in screenshot_names]

        # Other assets = downloaded images
        raw_images = assets_info.get("images", [])
        assets: list[str] = []
        for img in raw_images:
            fname = img.get("filename") if isinstance(img, dict) else None
            if fname:
                assets.append(f"assets/source/{fname}")

        return IngestionResult(
            source_url=url,
            source_type="webpage",
            title=title,
            text_content=text_content,
            key_claims=key_claims,
            frames=frames,
            assets=assets,
            metadata={
                "description": description,
                "section_count": len(sections),
                "screenshot_count": len(screenshot_names),
                "image_count": len(raw_images),
                "code_block_count": len(data.get("codeBlocks", [])),
                "source_brief_exit_code": proc.returncode,
            },
        )


def _error_result(url: str, message: str) -> IngestionResult:
    print(f"  ✗ {message}")
    return IngestionResult(
        source_url=url,
        source_type="webpage",
        title="(scrape failed)",
        text_content="",
        key_claims=[],
        frames=[],
        assets=[],
        metadata={"error": message},
    )
