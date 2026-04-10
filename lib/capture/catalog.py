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
ASSET_ROLES = {"avatar", "demo", "support", "background", "sfx", "music"}
ASSET_SOURCES = {"capture", "import", "generate", "brand-kit"}

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
        return d


@dataclass
class Catalog:
    assets: list[AssetEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"assets": [a.to_dict() for a in self.assets]}

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
    if not path.exists():
        return Catalog()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    entries = []
    for a in data.get("assets", []):
        entries.append(AssetEntry(
            id=a["id"],
            filename=a["filename"],
            type=a["type"],
            role=a["role"],
            linked_beats=a["linked_beats"],
            description=a["description"],
            scene=a.get("scene"),
            duration_s=a.get("duration_s"),
            dimensions=a.get("dimensions"),
            source=a.get("source", "import"),
        ))
    return Catalog(assets=entries)


def save_catalog(catalog: Catalog, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(catalog.to_dict(), f, indent=2, ensure_ascii=False)
