"""Per-project asset catalog with provenance tracking.

Every asset fetched by lib.assets is recorded in
`projects/<slug>/assets/sourced/catalog.json` with:
- source library (lobehub, simpleicons, pexels, ...)
- query / brand / URL used to fetch
- license + attribution requirements
- local file path
- timestamp

This is separate from the existing `assets/catalog.json` (which tracks
ALL project assets including manually added ones). The sourced catalog
is the audit log of what came from external libraries.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class SourcedAsset:
    """One fetched asset entry."""

    source: str  # "lobehub" | "simpleicons" | "pexels" | "pixabay" | "coverr" | "youtube"
    asset_type: str  # "logo" | "video" | "image" | "transcript" | "frame"
    local_path: str  # relative to project root
    query: str = ""  # search term, brand slug, or URL used to fetch
    license: str = ""  # "MIT", "CC0", "Pexels License", "Pixabay License", "Coverr Free", etc.
    attribution_required: bool = False
    attribution_text: str = ""  # if attribution_required, what to credit
    fetched_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)


def catalog_path(project_dir: Path) -> Path:
    """Return the path to the sourced catalog for a project."""
    return Path(project_dir) / "assets" / "sourced" / "catalog.json"


def load(project_dir: Path) -> list[SourcedAsset]:
    """Load the sourced catalog for a project. Empty list if missing."""
    path = catalog_path(project_dir)
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [SourcedAsset(**entry) for entry in raw.get("assets", [])]


def save(project_dir: Path, assets: list[SourcedAsset]) -> None:
    """Persist the sourced catalog."""
    path = catalog_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "project": Path(project_dir).name,
        "updated": datetime.now(timezone.utc).isoformat(),
        "assets": [asdict(a) for a in assets],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def register(project_dir: Path, asset: SourcedAsset) -> None:
    """Append an asset to the project's sourced catalog (idempotent on local_path)."""
    project_dir = Path(project_dir)
    assets = load(project_dir)
    # Replace any prior entry with the same local_path
    assets = [a for a in assets if a.local_path != asset.local_path]
    assets.append(asset)
    save(project_dir, assets)


def list_attribution(project_dir: Path) -> list[SourcedAsset]:
    """Return all assets in the catalog that require attribution."""
    return [a for a in load(project_dir) if a.attribution_required]


def summarize(project_dir: Path) -> dict[str, Any]:
    """Return a summary count of assets per source."""
    assets = load(project_dir)
    by_source: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for a in assets:
        by_source[a.source] = by_source.get(a.source, 0) + 1
        by_type[a.asset_type] = by_type.get(a.asset_type, 0) + 1
    return {
        "total": len(assets),
        "by_source": by_source,
        "by_type": by_type,
        "attribution_required_count": len(list_attribution(project_dir)),
    }
