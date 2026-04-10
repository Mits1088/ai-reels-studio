"""
Catalog validation — catches orphan assets, missing files, bad references.

Integrates with lib/validate.py by providing validate_catalog().
"""

from __future__ import annotations

import re
from pathlib import Path

from .catalog import (
    Catalog, load_catalog,
    ASSET_TYPES, ASSET_ROLES, ASSET_SOURCES, TYPE_EXTENSIONS,
)

# Reuse ValidationError from the main validator
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate import ValidationError


ASSET_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def validate_catalog(
    catalog: Catalog | dict,
    *,
    assets_dir: Path | None = None,
    beat_ids: set[str] | None = None,
) -> list[ValidationError]:
    """
    Validate catalog.json contents.

    Checks:
      - Required fields present
      - Valid type/role/source enums
      - No duplicate IDs or filenames
      - Every asset links to at least one beat
      - Linked beats exist in beat-map (if beat_ids provided)
      - Files exist on disk (if assets_dir provided)
      - File extension matches declared type
      - No orphan files in assets/ not in catalog
    """
    errs: list[ValidationError] = []
    f = "catalog.json"

    # Accept dict or Catalog
    if isinstance(catalog, dict):
        assets = catalog.get("assets", [])
    else:
        assets = [a.to_dict() for a in catalog.assets]

    if not assets:
        errs.append(ValidationError(f, "assets", "catalog is empty — no assets registered"))
        return errs

    seen_ids: set[str] = set()
    seen_filenames: set[str] = set()
    cataloged_filenames: set[str] = set()

    for i, asset in enumerate(assets):
        prefix = f"assets[{i}]"

        # ── Required fields ──────────────────────────────────────────────
        for field in ("id", "filename", "type", "role", "linked_beats", "description"):
            if field not in asset:
                errs.append(ValidationError(f, f"{prefix}.{field}", "required field missing"))

        # ── ID format ────────────────────────────────────────────────────
        aid = asset.get("id", "")
        if aid and not ASSET_ID_RE.match(aid):
            errs.append(ValidationError(f, f"{prefix}.id", f"invalid asset ID format: {aid!r}"))

        # ── Duplicate ID ─────────────────────────────────────────────────
        if aid in seen_ids:
            errs.append(ValidationError(f, f"{prefix}.id", f"duplicate asset ID: {aid!r}"))
        seen_ids.add(aid)

        # ── Duplicate filename ───────────────────────────────────────────
        fname = asset.get("filename", "")
        if fname in seen_filenames:
            errs.append(ValidationError(f, f"{prefix}.filename", f"duplicate filename: {fname!r}"))
        seen_filenames.add(fname)
        cataloged_filenames.add(fname)

        # ── Type/role/source enums ───────────────────────────────────────
        atype = asset.get("type", "")
        if atype and atype not in ASSET_TYPES:
            errs.append(ValidationError(f, f"{prefix}.type", f"invalid type: {atype!r}"))

        arole = asset.get("role", "")
        if arole and arole not in ASSET_ROLES:
            errs.append(ValidationError(f, f"{prefix}.role", f"invalid role: {arole!r}"))

        asource = asset.get("source", "")
        if asource and asource not in ASSET_SOURCES:
            errs.append(ValidationError(f, f"{prefix}.source", f"invalid source: {asource!r}"))

        # ── Extension matches type ───────────────────────────────────────
        if fname and atype and atype in TYPE_EXTENSIONS:
            ext = Path(fname).suffix.lower()
            if ext and ext not in TYPE_EXTENSIONS[atype]:
                errs.append(ValidationError(
                    f, f"{prefix}.filename",
                    f"extension '{ext}' doesn't match type '{atype}' (expected: {sorted(TYPE_EXTENSIONS[atype])})"
                ))

        # ── Linked beats ─────────────────────────────────────────────────
        beats = asset.get("linked_beats", [])
        if isinstance(beats, list) and len(beats) == 0:
            errs.append(ValidationError(
                f, f"{prefix}.linked_beats",
                f"asset '{aid}' has no linked beats — every asset must have a purpose"
            ))

        # Cross-reference beats
        if beat_ids is not None and isinstance(beats, list):
            for bid in beats:
                if bid not in beat_ids:
                    errs.append(ValidationError(
                        f, f"{prefix}.linked_beats",
                        f"references nonexistent beat: {bid!r}"
                    ))

        # ── File exists on disk ──────────────────────────────────────────
        if assets_dir and fname:
            if not (assets_dir / fname).exists():
                errs.append(ValidationError(
                    f, f"{prefix}.filename",
                    f"file not found on disk: {fname}"
                ))

        # ── Description not empty ────────────────────────────────────────
        desc = asset.get("description", "")
        if isinstance(desc, str) and not desc.strip():
            errs.append(ValidationError(
                f, f"{prefix}.description",
                "description must explain the asset's purpose"
            ))

    # ── Orphan files check ───────────────────────────────────────────────
    if assets_dir and assets_dir.exists():
        for file in assets_dir.iterdir():
            if file.name == "catalog.json":
                continue
            if file.is_file() and file.name not in cataloged_filenames:
                errs.append(ValidationError(
                    f, "orphan_file",
                    f"file '{file.name}' exists in assets/ but is not in the catalog"
                ))

    return errs
