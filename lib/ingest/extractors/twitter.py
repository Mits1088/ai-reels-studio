"""Twitter/X URL extractor.

Delegates to capture-x-video.js (Node.js) to download the video,
then registers it in the project catalog and returns an IngestionResult.

The downloaded video is raw source footage. To get a transcript from it,
pass it through the voice ingest pipeline:
  python -m lib.ingest.cli full assets/sourced/x-video-<id>.mp4 projects/<slug>/

Requirements:
  node on PATH
  AUTH_TOKEN and CT0 set in .env (grab from browser DevTools → Application → Cookies → x.com)
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .base import BaseExtractor
from ..url_router import IngestionResult


class TwitterExtractor(BaseExtractor):
    """Download a Twitter/X video using capture-x-video.js."""

    def extract(
        self,
        url: str,
        project_dir: Path,
        *,
        frames_every: float = 5.0,  # reserved for future frame extraction
        **kwargs,
    ) -> IngestionResult:
        root = Path(__file__).resolve().parents[3]  # D:/Reel generation/
        script = root / "lib" / "capture" / "capture-x-video.js"

        if not script.exists():
            return _error_result(url, f"capture-x-video.js not found at {script}")

        # Derive a stable output filename from the tweet ID
        tweet_id = _extract_tweet_id(url)
        assets_dir = project_dir / "assets" / "sourced"
        assets_dir.mkdir(parents=True, exist_ok=True)
        out_file = assets_dir / f"x-video-{tweet_id}.mp4"

        print(f"  → Downloading X/Twitter video (tweet {tweet_id}) …")
        print(f"    Requires AUTH_TOKEN + CT0 in .env")

        cmd = ["node", str(script), "--url", url, "--out", str(out_file)]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(root),
            timeout=180,
        )

        if proc.stdout:
            for line in proc.stdout.splitlines():
                print(f"    {line}")

        if proc.returncode != 0:
            print(f"  ⚠  capture-x-video.js exited {proc.returncode}")
            if proc.stderr:
                for line in proc.stderr.splitlines()[-10:]:
                    print(f"    {line}")
            if "AUTH_TOKEN" in (proc.stderr or ""):
                print("    → Set AUTH_TOKEN and CT0 in .env")
                print("      Get them from: browser DevTools > Application > Cookies > x.com")

        # Register in catalog whether download succeeded or not (partial state is useful)
        video_downloaded = out_file.exists() and out_file.stat().st_size > 1024
        if video_downloaded:
            _register_in_catalog(project_dir, url, tweet_id, out_file)
            print(f"  ✓ Downloaded: {out_file.name} ({out_file.stat().st_size // 1024}KB)")

        try:
            rel_path = str(out_file.relative_to(project_dir))
        except ValueError:
            rel_path = str(out_file)

        assets = [rel_path] if video_downloaded else []

        return IngestionResult(
            source_url=url,
            source_type="twitter",
            title=f"X post {tweet_id}",
            text_content="",   # No transcript until audio extraction runs
            key_claims=[],
            frames=[],
            assets=assets,
            metadata={
                "tweet_id": tweet_id,
                "video_downloaded": video_downloaded,
                "video_path": rel_path if video_downloaded else "",
                "note": (
                    "Video downloaded. To get transcript: "
                    "python -m lib.ingest.cli full "
                    + rel_path
                    + " projects/<slug>/"
                ) if video_downloaded else "Download failed — check AUTH_TOKEN/CT0 in .env",
            },
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_tweet_id(url: str) -> str:
    """Extract numeric tweet ID from a Twitter/X URL."""
    # https://x.com/user/status/1234567890
    parts = url.rstrip("/").split("/")
    for i, part in enumerate(parts):
        if part == "status" and i + 1 < len(parts):
            return parts[i + 1].split("?")[0]
    # Fallback: last numeric segment
    for part in reversed(parts):
        clean = part.split("?")[0]
        if clean.isdigit():
            return clean
    return "unknown"


def _register_in_catalog(
    project_dir: Path,
    url: str,
    tweet_id: str,
    video_path: Path,
) -> None:
    try:
        from ...assets import catalog as cat
        try:
            rel_path = str(video_path.relative_to(project_dir))
        except ValueError:
            rel_path = str(video_path)

        cat.register(
            project_dir,
            cat.SourcedAsset(
                source="twitter",
                asset_type="video",
                local_path=rel_path,
                query=url,
                license="Source-dependent (Twitter/X)",
                attribution_required=True,
                attribution_text=f"via X: {url}",
                metadata={"tweet_id": tweet_id, "url": url},
            ),
        )
    except Exception as e:
        print(f"  ⚠  Catalog registration failed: {e}")


def _error_result(url: str, message: str) -> IngestionResult:
    print(f"  ✗ {message}")
    return IngestionResult(
        source_url=url,
        source_type="twitter",
        title="(download failed)",
        text_content="",
        key_claims=[],
        frames=[],
        assets=[],
        metadata={"error": message},
    )
