"""Pexels API — stock video and image fetcher.

API: https://www.pexels.com/api/documentation/
License: Pexels License (commercial OK, no attribution required, no
         standalone resale).
Rate limit: 200 req/hr, 20,000 req/mo on the free tier.

Get a free API key at https://www.pexels.com/api/ — instant approval.
Add to .env as: PEXELS_API_KEY=your_key_here
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from . import catalog as cat


API_BASE = "https://api.pexels.com/v1"
VIDEO_API_BASE = "https://api.pexels.com/videos"
LICENSE = "Pexels License"


def _api_key() -> str:
    key = os.environ.get("PEXELS_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "PEXELS_API_KEY not set. Add it to your .env or shell environment. "
            "Get a free key at https://www.pexels.com/api/"
        )
    return key


def _request(url: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": _api_key(),
            "User-Agent": "lib.assets/1.0 (reel-pipeline)",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def search_videos(
    query: str,
    per_page: int = 10,
    orientation: str | None = None,
    size: str | None = None,
) -> dict[str, Any]:
    """Search for videos on Pexels.

    Args:
      query: Search term
      per_page: Results per page (max 80)
      orientation: "landscape" | "portrait" | "square"
      size: "large" (4K) | "medium" (Full HD) | "small" (HD)
    """
    params = {"query": query, "per_page": per_page}
    if orientation:
        params["orientation"] = orientation
    if size:
        params["size"] = size
    qs = urllib.parse.urlencode(params)
    return _request(f"{VIDEO_API_BASE}/search?{qs}")


def search_photos(
    query: str,
    per_page: int = 10,
    orientation: str | None = None,
) -> dict[str, Any]:
    """Search for photos on Pexels."""
    params = {"query": query, "per_page": per_page}
    if orientation:
        params["orientation"] = orientation
    qs = urllib.parse.urlencode(params)
    return _request(f"{API_BASE}/search?{qs}")


def _best_video_file(video: dict[str, Any], prefer_height: int = 1920) -> dict | None:
    """Pick the best video file from a Pexels video result.

    Prefers a file at or above prefer_height, falls back to the highest
    resolution available. Returns the file dict (with link, width, height).
    """
    files = video.get("video_files", [])
    if not files:
        return None
    # Sort by height descending
    sorted_files = sorted(files, key=lambda f: f.get("height", 0), reverse=True)
    # Prefer the smallest file >= prefer_height; fall back to the largest
    above = [f for f in sorted_files if f.get("height", 0) >= prefer_height]
    return above[-1] if above else sorted_files[0]


def download_video(
    video_id: int | str,
    out_dir: Path,
    project_dir: Path | None = None,
    query: str = "",
    prefer_height: int = 1920,
) -> Path:
    """Download a single Pexels video by ID."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    meta = _request(f"{VIDEO_API_BASE}/videos/{video_id}")
    file_info = _best_video_file(meta, prefer_height=prefer_height)
    if file_info is None:
        raise RuntimeError(f"No video files found for Pexels video {video_id}")

    file_url = file_info["link"]
    ext = ".mp4"
    dest = out_dir / f"pexels-{video_id}-{file_info.get('height', 0)}p{ext}"

    print(f"  → downloading Pexels video {video_id} ({file_info.get('width')}x{file_info.get('height')}) ...")
    req = urllib.request.Request(
        file_url, headers={"User-Agent": "lib.assets/1.0 (reel-pipeline)"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        dest.write_bytes(resp.read())

    if project_dir is not None:
        try:
            rel_path = str(dest.relative_to(Path(project_dir)))
        except ValueError:
            rel_path = str(dest)
        cat.register(
            project_dir,
            cat.SourcedAsset(
                source="pexels",
                asset_type="video",
                local_path=rel_path,
                query=query or f"id:{video_id}",
                license=LICENSE,
                attribution_required=False,
                metadata={
                    "pexels_id": video_id,
                    "width": file_info.get("width"),
                    "height": file_info.get("height"),
                    "page_url": meta.get("url"),
                    "user": meta.get("user", {}).get("name"),
                },
            ),
        )
    return dest


def search_and_download_videos(
    query: str,
    out_dir: Path,
    project_dir: Path | None = None,
    limit: int = 3,
    orientation: str = "portrait",
    prefer_height: int = 1920,
) -> list[Path]:
    """Search Pexels and download the top N matches in one call."""
    results = search_videos(query, per_page=limit, orientation=orientation)
    videos = results.get("videos", [])
    if not videos:
        print(f"  ! no Pexels videos found for query: {query!r}")
        return []
    paths: list[Path] = []
    for v in videos[:limit]:
        try:
            paths.append(
                download_video(
                    v["id"],
                    out_dir,
                    project_dir=project_dir,
                    query=query,
                    prefer_height=prefer_height,
                )
            )
        except Exception as e:
            print(f"  ! failed to download Pexels {v['id']}: {e}")
    return paths
