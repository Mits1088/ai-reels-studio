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


CATALOG_SCHEMA_VERSION = 2

VALID_ENRICHMENT_STATUS = {"not_enriched", "partial", "full", "failed"}
VALID_FOCAL_POINT_SOURCES = {"face", "text-block", "center", "manual"}
VALID_USABLE_DISPLAY_MODES = {"split-screen", "center-full", "responsive", "hook-reveal"}


def _validate_enrichment(asset: dict, prefix: str, errs: list[ValidationError]) -> None:
    """Validate the optional enrichment block on an asset (Phase B).

    Skipped when no enrichment block is present — enrichment is optional.
    """
    enrichment = asset.get("enrichment")
    if enrichment is None:
        return

    f = "catalog.json"

    if not isinstance(enrichment, dict):
        errs.append(ValidationError(f, f"{prefix}.enrichment", "must be an object"))
        return

    # Required fields
    for field_name in ("status", "schema_version", "derived_at", "derived_by"):
        if field_name not in enrichment:
            errs.append(ValidationError(
                f, f"{prefix}.enrichment.{field_name}", "required field missing",
            ))

    # Status enum
    status = enrichment.get("status")
    if status is not None and status not in VALID_ENRICHMENT_STATUS:
        errs.append(ValidationError(
            f, f"{prefix}.enrichment.status",
            f"invalid status: {status!r} (expected {sorted(VALID_ENRICHMENT_STATUS)})",
        ))

    # Schema version is a positive int
    sv = enrichment.get("schema_version")
    if sv is not None and (not isinstance(sv, int) or sv < 1):
        errs.append(ValidationError(
            f, f"{prefix}.enrichment.schema_version",
            f"must be a positive integer, got {sv!r}",
        ))

    # Focal point shape
    fp = enrichment.get("focal_point")
    if isinstance(fp, dict):
        for fp_field in ("x", "y", "source"):
            if fp_field not in fp:
                errs.append(ValidationError(
                    f, f"{prefix}.enrichment.focal_point.{fp_field}",
                    "required field missing",
                ))
        fp_source = fp.get("source")
        if fp_source is not None and fp_source not in VALID_FOCAL_POINT_SOURCES:
            errs.append(ValidationError(
                f, f"{prefix}.enrichment.focal_point.source",
                f"invalid source: {fp_source!r} (expected {sorted(VALID_FOCAL_POINT_SOURCES)})",
            ))
        for coord in ("x", "y"):
            v = fp.get(coord)
            if v is not None and isinstance(v, (int, float)) and not (0 <= v <= 100):
                errs.append(ValidationError(
                    f, f"{prefix}.enrichment.focal_point.{coord}",
                    f"out of range [0, 100]: {v}",
                ))

    # Usable display modes
    modes = enrichment.get("usable_display_modes", [])
    if isinstance(modes, list):
        for i, mode in enumerate(modes):
            if mode not in VALID_USABLE_DISPLAY_MODES:
                errs.append(ValidationError(
                    f, f"{prefix}.enrichment.usable_display_modes[{i}]",
                    f"invalid display mode: {mode!r}",
                ))


def validate_catalog(
    catalog: Catalog | dict,
    *,
    assets_dir: Path | None = None,
    beat_ids: set[str] | None = None,
) -> list[ValidationError]:
    """
    Validate catalog.json contents (v2).

    Checks:
      - schema_version present and equals 2 (v1 catalogs return a single
        "needs migration" error and short-circuit further validation)
      - Required fields present per asset
      - Valid type/role/source enums (v2 includes 'broll' role + 'url-import' source)
      - No duplicate IDs or filenames
      - Every asset links to at least one beat
      - Linked beats exist in beat-map (if beat_ids provided)
      - Files exist on disk (if assets_dir provided)
      - File extension matches declared type
      - No orphan files in assets/ not in catalog
      - Optional enrichment block (when present) has correct shape
    """
    errs: list[ValidationError] = []
    f = "catalog.json"

    # Accept dict or Catalog
    if isinstance(catalog, dict):
        schema_version = catalog.get("schema_version")
        assets = catalog.get("assets", [])
    else:
        schema_version = getattr(catalog, "schema_version", None)
        assets = [a.to_dict() for a in catalog.assets]

    # ── v2 schema version gate ───────────────────────────────────────────
    if schema_version is None:
        errs.append(ValidationError(
            f, "schema_version",
            "missing — needs migration to v2 — run: "
            "python -m lib.migrate --target catalog --project <slug>",
        ))
        return errs  # short-circuit; further checks are meaningless without migration
    if schema_version != CATALOG_SCHEMA_VERSION:
        errs.append(ValidationError(
            f, "schema_version",
            f"unsupported catalog schema_version: {schema_version!r} "
            f"(expected {CATALOG_SCHEMA_VERSION})",
        ))
        return errs

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

        # ── source_url required when source == 'url-import' ──────────────
        if asset.get("source") == "url-import" and not asset.get("source_url"):
            errs.append(ValidationError(
                f, f"{prefix}.source_url",
                "source_url is required when source='url-import'",
            ))

        # ── Optional enrichment block (v2) ───────────────────────────────
        _validate_enrichment(asset, prefix, errs)

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
