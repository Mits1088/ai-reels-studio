"""Coverr API — cinematic stock video fetcher.

API: https://api.coverr.co/docs
License: Coverr's API content is commercially licensed but VIDEOS REQUIRE
         attribution. The reel pipeline tracks attribution requirements
         in the sourced catalog so the user can include credits in the
         description / pinned comment when publishing.
Rate limit: 1000 calls/month on the free tier.

Get a free API key at https://coverr.co/developers — instant approval.
Add to .env as: COVERR_API_KEY=your_key_here
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from . import catalog as cat


API_BASE = "https://api.coverr.co"
LICENSE = "Coverr (commercial, attribution required)"


def _api_key() -> str:
    key = os.environ.get("COVERR_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "COVERR_API_KEY not set. Add it to your .env or shell environment. "
            "Get a free key at https://coverr.co/developers"
        )
    return key


def _request(path: str, params: dict | None = None) -> dict[str, Any]:
    base_params = {"api_key": _api_key()}
    if params:
        base_params.update(params)
    qs = urllib.parse.urlencode(base_params)
    url = f"{API_BASE}{path}?{qs}"
    req = urllib.request.Request(
        url, headers={"User-Agent": "lib.assets/1.0 (reel-pipeline)"}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def search_videos(query: str, per_page: int = 10) -> dict[str, Any]:
    """Search for videos on Coverr.

    The Coverr API does NOT include download URLs in search results by
    default — you must pass `urls=true` to get the `urls` object on each
    hit. Without it, downloads fail because there's no mp4 link.
    """
    return _request(
        "/videos",
        {"query": query, "page_size": per_page, "page": 1, "urls": "true"},
    )


def _best_video_url(video: dict[str, Any]) -> tuple[str, str]:
    """Pick the best download URL from a Coverr video result.

    Coverr's `urls` object contains:
      - mp4          — full resolution
      - mp4_preview  — low resolution
      - mp4_download — same as mp4 but with Content-Disposition header

    Prefer mp4 (full resolution) for the reel pipeline.
    """
    urls = video.get("urls", {})
    for key in ("mp4", "mp4_download", "mp4_preview"):
        if key in urls and urls[key]:
            return urls[key], key
    raise ValueError(
        f"No usable video URLs in Coverr result for {video.get('id')}. "
        f"Make sure search_videos was called with urls=true."
    )


def register_download(video_id: str) -> None:
    """PATCH /videos/:id/stats/downloads — register a download event.

    Per Coverr docs: 'this is a MUST and not optional since it really
    improves our feedback loop.'
    """
    import urllib.request
    url = f"{API_BASE}/videos/{video_id}/stats/downloads?api_key={_api_key()}"
    req = urllib.request.Request(url, method="PATCH",
                                 headers={"User-Agent": "lib.assets/1.0 (reel-pipeline)"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
    except Exception as e:
        # Non-fatal — log and continue
        print(f"  ! warning: failed to register Coverr download for {video_id}: {e}")


def download_video(
    video: dict[str, Any],
    out_dir: Path,
    project_dir: Path | None = None,
    query: str = "",
) -> Path:
    """Download a Coverr video given a result dict from search_videos."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    url, quality = _best_video_url(video)
    vid_id = video.get("id", "unknown")
    title = video.get("title", "untitled").replace("/", "-").replace(" ", "-")[:40]
    dest = out_dir / f"coverr-{vid_id}-{title}.mp4"

    print(f"  → downloading Coverr video {vid_id} ({quality}) ...")
    req = urllib.request.Request(
        url, headers={"User-Agent": "lib.assets/1.0 (reel-pipeline)"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        dest.write_bytes(resp.read())

    # Register download event per Coverr docs (mandatory for feedback loop)
    register_download(vid_id)

    creator = video.get("author") or video.get("creator", {}).get("name", "unknown")
    attribution = f"Video by {creator} via Coverr"

    if project_dir is not None:
        try:
            rel_path = str(dest.relative_to(Path(project_dir)))
        except ValueError:
            rel_path = str(dest)
        cat.register(
            project_dir,
            cat.SourcedAsset(
                source="coverr",
                asset_type="video",
                local_path=rel_path,
                query=query or f"id:{vid_id}",
                license=LICENSE,
                attribution_required=True,
                attribution_text=attribution,
                metadata={
                    "coverr_id": vid_id,
                    "title": video.get("title"),
                    "quality": quality,
                    "page_url": video.get("poster"),
                },
            ),
        )
    return dest


def search_and_download_videos(
    query: str,
    out_dir: Path,
    project_dir: Path | None = None,
    limit: int = 3,
) -> list[Path]:
    """Search Coverr and download the top N matches."""
    results = search_videos(query, per_page=limit)
    hits = results.get("hits", []) or results.get("videos", [])
    if not hits:
        print(f"  ! no Coverr videos found for query: {query!r}")
        return []
    paths: list[Path] = []
    for v in hits[:limit]:
        try:
            paths.append(
                download_video(v, out_dir, project_dir=project_dir, query=query)
            )
        except Exception as e:
            print(f"  ! failed to download Coverr {v.get('id')}: {e}")
    return paths
