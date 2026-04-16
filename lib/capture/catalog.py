"""
Asset catalog — the manifest that tracks every asset in a project.

catalog.json lives at projects/<slug>/assets/catalog.json.
Every asset must link to at least one beat. No orphans allowed.
"""

from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass, field, asdict


# ── Valid types and roles ────────────────────────────────────────────────────

ASSET_TYPES = {"video", "image", "logo", "chart", "icon", "overlay", "sfx", "music"}
# v2: 'broll' added to match the timeline broll lane.
ASSET_ROLES = {"avatar", "demo", "support", "broll", "background", "sfx", "music"}
# v2: 'url-import' added — pairs with source_url field.
ASSET_SOURCES = {"capture", "import", "generate", "brand-kit", "url-import"}

# File extensions by type
TYPE_EXTENSIONS: dict[str, set[str]] = {
    "video":   {".mp4", ".webm", ".mov", ".avi", ".mkv"},
    "image":   {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"},
    "logo":    {".png", ".svg", ".webp"},
    "chart":   {".png", ".jpg", ".svg", ".webp"},
    "icon":    {".png", ".svg", ".webp"},
    "overlay": {".png", ".webp", ".mov"},  # .mov for alpha overlays
    "sfx":     {".wav", ".mp3", ".m4a", ".ogg"},
    "music":   {".wav", ".mp3", ".m4a", ".ogg"},
}

ALL_VALID_EXTENSIONS = set()
for exts in TYPE_EXTENSIONS.values():
    ALL_VALID_EXTENSIONS.update(exts)


# ── Data model ───────────────────────────────────────────────────────────────

@dataclass
class AssetEntry:
    id: str
    filename: str
    type: str
    role: str
    linked_beats: list[str]
    description: str
    scene: int | None = None
    duration_s: float | None = None
    dimensions: dict | None = None  # {"w": int, "h": int}
    source: str = "import"
    # v2 fields — additive, both optional
    source_url: str | None = None     # original URL when source == "url-import"
    enrichment: dict | None = None    # enrichment block written by lib.capture.enrich

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "filename": self.filename,
            "type": self.type,
            "role": self.role,
            "linked_beats": self.linked_beats,
            "description": self.description,
            "source": self.source,
        }
        if self.scene is not None:
            d["scene"] = self.scene
        if self.duration_s is not None:
            d["duration_s"] = self.duration_s
        if self.dimensions is not None:
            d["dimensions"] = self.dimensions
        if self.source_url is not None:
            d["source_url"] = self.source_url
        if self.enrichment is not None:
            d["enrichment"] = self.enrichment
        return d


# Default catalog schema version for newly created catalogs.
# Existing catalogs preserve whatever schema_version they were loaded with.
CATALOG_SCHEMA_VERSION = 2


@dataclass
class Catalog:
    assets: list[AssetEntry] = field(default_factory=list)
    schema_version: int = CATALOG_SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "assets": [a.to_dict() for a in self.assets],
        }

    def get(self, asset_id: str) -> AssetEntry | None:
        for a in self.assets:
            if a.id == asset_id:
                return a
        return None

    def ids(self) -> set[str]:
        return {a.id for a in self.assets}

    def filenames(self) -> set[str]:
        return {a.filename for a in self.assets}

    def by_role(self, role: str) -> list[AssetEntry]:
        return [a for a in self.assets if a.role == role]

    def by_beat(self, beat_id: str) -> list[AssetEntry]:
        return [a for a in self.assets if beat_id in a.linked_beats]


def load_catalog(path: Path) -> Catalog:
    """Load a catalog from disk. Tolerant of legacy and partial data.

    Tolerance rules (so the validator can run and report problems instead of
    crashing the whole pipeline on a malformed entry):
      - Missing required fields are loaded as empty strings / empty lists
      - vNext-style aliases are accepted: 'file' → filename,
        'beats' → linked_beats, 'note' → description
      - schema_version is preserved as-loaded (defaults to 1 if absent)

    The validator (validate_catalog) is the single source of truth for
    "is this catalog well-formed" — load_catalog just gets the data into
    memory without raising.
    """
    if not path.exists():
        return Catalog()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    schema_version = data.get("schema_version", 1)
    entries = []
    for a in data.get("assets", []):
        if not isinstance(a, dict):
            continue
        # Accept vNext-style aliases for the legacy projects in projects/
        filename = a.get("filename") or a.get("file") or ""
        linked_beats = a.get("linked_beats")
        if linked_beats is None:
            linked_beats = a.get("beats") or []
        description = a.get("description") or a.get("note") or ""
        entries.append(AssetEntry(
            id=a.get("id", ""),
            filename=filename,
            type=a.get("type", ""),
            role=a.get("role", ""),
            linked_beats=linked_beats,
            description=description,
            scene=a.get("scene"),
            duration_s=a.get("duration_s"),
            dimensions=a.get("dimensions"),
            source=a.get("source", "import"),
            source_url=a.get("source_url"),
            enrichment=a.get("enrichment"),
        ))
    return Catalog(assets=entries, schema_version=schema_version)


def save_catalog(catalog: Catalog, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(catalog.to_dict(), f, indent=2, ensure_ascii=False)
