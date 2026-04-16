"""Simple Icons CDN — SaaS brand SVG/PNG fetcher.

Fetches brand icons from https://cdn.simpleicons.org which serves CC0
public-domain SVGs for ~3,400 popular brands. No API key, no attribution.

URL pattern:
  https://cdn.simpleicons.org/{slug}                   - default brand color
  https://cdn.simpleicons.org/{slug}/{hex}             - explicit color
  https://cdn.simpleicons.org/{slug}/{light}/{dark}    - light + dark mode

Slug rules: lowercase, no spaces, ampersands → "and", dots removed.
See https://simpleicons.org/ for the full slug list.

This module is the right choice for SaaS / non-AI brands like Notion,
Asana, Slack, Rakuten, Atlassian. For AI/LLM brands prefer lobehub.py
which has cleaner colored variants.
"""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

from . import catalog as cat


CDN_BASE = "https://cdn.simpleicons.org"
LICENSE = "CC0"


def slugify(brand: str) -> str:
    """Convert a brand name to a Simple Icons slug.

    Examples:
      "Notion"        -> "notion"
      "Google Cloud"  -> "googlecloud"
      "Tom & Jerry"   -> "tomandjerry"
      "X.com"         -> "xcom"
    """
    s = brand.lower()
    s = s.replace("&", "and")
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "", s)
    return s


def url(brand: str, color: str | None = None, dark_color: str | None = None) -> str:
    """Build a CDN URL for a brand."""
    slug = slugify(brand)
    parts = [CDN_BASE, slug]
    if color is not None:
        parts.append(color.lstrip("#"))
        if dark_color is not None:
            parts.append(dark_color.lstrip("#"))
    return "/".join(parts)


def fetch(
    brand: str,
    out_dir: Path,
    color: str | None = None,
    project_dir: Path | None = None,
    filename: str | None = None,
) -> Path:
    """Download a brand icon SVG to out_dir.

    Args:
      brand: Brand name (e.g. "Notion", "Asana")
      out_dir: Directory to save the SVG
      color: Optional hex color (e.g. "000000" or "#000000"). Default: brand color.
      project_dir: If provided, register in the project's sourced catalog.
      filename: Optional output filename (default: <slug>.svg)

    Returns:
      Path to the saved SVG file.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    target_url = url(brand, color=color)
    slug = slugify(brand)
    name = filename or f"{slug}.svg"
    dest = out_dir / name

    req = urllib.request.Request(
        target_url, headers={"User-Agent": "lib.assets/1.0 (reel-pipeline)"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        if resp.status != 200:
            raise RuntimeError(
                f"Simple Icons returned {resp.status} for brand '{brand}' (slug='{slug}'). "
                f"Check the slug at https://simpleicons.org/?q={slug}"
            )
        dest.write_bytes(resp.read())

    if project_dir is not None:
        try:
            rel_path = str(dest.relative_to(Path(project_dir)))
        except ValueError:
            rel_path = str(dest)
        cat.register(
            project_dir,
            cat.SourcedAsset(
                source="simpleicons",
                asset_type="logo",
                local_path=rel_path,
                query=brand,
                license=LICENSE,
                attribution_required=False,
                metadata={"slug": slug, "color": color, "url": target_url},
            ),
        )

    return dest


def fetch_many(
    brands: list[str],
    out_dir: Path,
    color: str | None = None,
    project_dir: Path | None = None,
) -> list[Path]:
    """Download a batch of brands. Logs failures, returns successful paths."""
    out_dir = Path(out_dir)
    results: list[Path] = []
    for brand in brands:
        try:
            results.append(
                fetch(brand, out_dir, color=color, project_dir=project_dir)
            )
        except Exception as e:
            print(f"  ! failed: {brand} ({e})")
    return results
