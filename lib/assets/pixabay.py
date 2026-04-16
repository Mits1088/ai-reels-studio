"""Pixabay API — stock video and image fetcher.

API: https://pixabay.com/api/docs/
License: Pixabay License (commercial OK, no attribution required, no
         standalone resale).
Rate limit: 100 req/min on the free tier.

Get a free API key at https://pixabay.com/api/docs/ — instant approval
after creating a Pixabay account.
Add to .env as: PIXABAY_API_KEY=your_key_here
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from . import catalog as cat


API_VIDEO_BASE = "https://pixabay.com/api/videos/"
API_IMAGE_BASE = "https://pixabay.com/api/"
LICENSE = "Pixabay License"


def _api_key() -> str:
    key = os.environ.get("PIXABAY_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "PIXABAY_API_KEY not set. Add it to your .env or shell environment. "
            "Get a free key at https://pixabay.com/api/docs/"
        )
    return key


def _request(url: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url, headers={"User-Agent": "lib.assets/1.0 (reel-pipeline)"}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def search_videos(
    query: str,
    per_page: int = 10,
    video_type: str = "all",
    min_width: int = 1080,
    min_height: int = 1920,
) -> dict[str, Any]:
    """Search for videos on Pixabay.

    Args:
      query: Search term
      per_page: Results per page (3-200)
      video_type: "all" | "film" | "animation"
      min_width: Minimum video width in pixels
      min_height: Minimum video height in pixels
    """
    params = {
        "key": _api_key(),
        "q": query,
        "per_page": max(3, per_page),  # Pixabay requires per_page >= 3
        "video_type": video_type,
        "min_width": min_width,
        "min_height": min_height,
    }
    qs = urllib.parse.urlencode(params)
    return _request(f"{API_VIDEO_BASE}?{qs}")


def search_images(
    query: str,
    per_page: int = 10,
    image_type: str = "all",
    orientation: str = "all",
) -> dict[str, Any]:
    """Search for images on Pixabay.

    Args:
      image_type: "all" | "photo" | "illustration" | "vector"
      orientation: "all" | "horizontal" | "vertical"
    """
    params = {
        "key": _api_key(),
        "q": query,
        "per_page": max(3, per_page),
        "image_type": image_type,
        "orientation": orientation,
    }
    qs = urllib.parse.urlencode(params)
    return _request(f"{API_IMAGE_BASE}?{qs}")


def _best_video_url(video: dict[str, Any]) -> tuple[str, int, int]:
    """Pick the best video URL from a Pixabay video result.

    Pixabay returns 'videos' dict with keys: large, medium, small, tiny.
    Each has url, width, height. We prefer the largest available.
    """
    videos_dict = video.get("videos", {})
    if not videos_dict:
        raise ValueError("No video URLs in Pixabay result")
    candidates = []
    for size_key in ("large", "medium", "small", "tiny"):
        if size_key in videos_dict and videos_dict[size_key].get("url"):
            v = videos_dict[size_key]
            candidates.append((v["url"], v.get("width", 0), v.get("height", 0)))
    if not candidates:
        raise ValueError("No usable video URLs in Pixabay result")
    # Return the highest resolution
    candidates.sort(key=lambda c: c[1] * c[2], reverse=True)
    return candidates[0]


def download_video(
    video: dict[str, Any],
    out_dir: Path,
    project_dir: Path | None = None,
    query: str = "",
) -> Path:
    """Download a Pixabay video given a result dict from search_videos."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    url, width, height = _best_video_url(video)
    vid_id = video.get("id", "unknown")
    dest = out_dir / f"pixabay-{vid_id}-{height}p.mp4"

    print(f"  → downloading Pixabay video {vid_id} ({width}x{height}) ...")
    req = urllib.request.Request(
        url, headers={"User-Agent": "lib.assets/1.0 (reel-pipeline)"}
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
                source="pixabay",
                asset_type="video",
                local_path=rel_path,
                query=query or f"id:{vid_id}",
                license=LICENSE,
                attribution_required=False,
                metadata={
                    "pixabay_id": vid_id,
                    "width": width,
                    "height": height,
                    "page_url": video.get("pageURL"),
                    "user": video.get("user"),
                    "tags": video.get("tags"),
                },
            ),
        )
    return dest


def _is_portrait(video: dict[str, Any]) -> bool:
    """True if the video's largest variant is taller than wide."""
    sizes = video.get("videos", {})
    for key in ("large", "medium", "small", "tiny"):
        v = sizes.get(key, {})
        w, h = v.get("width", 0), v.get("height", 0)
        if w and h:
            return h > w
    return False


def search_and_download_videos(
    query: str,
    out_dir: Path,
    project_dir: Path | None = None,
    limit: int = 3,
    min_width: int = 1080,
    min_height: int = 1920,
    portrait_only: bool = True,
) -> list[Path]:
    """Search Pixabay and download the top N matches.

    Pixabay's video API does not support an orientation filter — when
    portrait_only=True, results are filtered client-side after the search
    by checking that height > width on the largest variant. We over-fetch
    (3x) so that filtering still leaves enough candidates.
    """
    fetch_count = max(3, limit * 3 if portrait_only else limit)
    results = search_videos(
        query, per_page=fetch_count, min_width=min_width, min_height=min_height
    )
    hits = results.get("hits", [])
    if portrait_only:
        hits = [v for v in hits if _is_portrait(v)]
    if not hits:
        suffix = " (after portrait filter)" if portrait_only else ""
        print(f"  ! no Pixabay videos found for query: {query!r}{suffix}")
        return []
    paths: list[Path] = []
    for v in hits[:limit]:
        try:
            paths.append(
                download_video(v, out_dir, project_dir=project_dir, query=query)
            )
        except Exception as e:
            print(f"  ! failed to download Pixabay {v.get('id')}: {e}")
    return paths
