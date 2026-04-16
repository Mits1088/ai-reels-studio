"""
Edit-plan validator. Hand-rolled, no jsonschema dep.

Returns a list of EditPlanValidationError objects (severity-tagged).

Cross-references when the relevant data is provided:
  - beat_ids:           every BeatPlan.beat_id must exist in beat_map
  - catalog_asset_ids:  every selected_asset_id must exist in catalog (when set)
  - template_registry:  every template_id must be in the registry
"""

from __future__ import annotations

from dataclasses import dataclass

from lib.constants import VALID_STYLES
from lib.grammar import (
    PROOF_CLASSES,
    VALID_CAPTION_MODES,
    EDITORIAL_ENTER_PRESETS,
    EDITORIAL_EXIT_PRESETS,
    RENDERER_ENTER_PRESETS,
    RENDERER_EXIT_PRESETS,
    ENTER_DUR_BOUNDS,
    EXIT_DUR_BOUNDS,
    TemplateRegistry,
)
from .model import EditPlan, BeatPlan


SEVERITY_BLOCK = "BLOCK"
SEVERITY_WARN = "WARN"
SEVERITY_INFO = "INFO"


@dataclass
class EditPlanValidationError:
    severity: str
    field: str
    message: str

    def __repr__(self) -> str:
        return f"[{self.severity}] {self.field}: {self.message}"


def validate_edit_plan_dict(
    data: dict,
    *,
    beat_ids: set[str] | None = None,
    catalog_asset_ids: set[str] | None = None,
    template_registry: TemplateRegistry | None = None,
) -> list[EditPlanValidationError]:
    """Validate a plain dict before constructing EditPlan."""
    errs: list[EditPlanValidationError] = []

    for required in ("schema_version", "project_slug", "beats"):
        if required not in data:
            errs.append(EditPlanValidationError(
                SEVERITY_BLOCK, required, "required field missing",
            ))

    # style is optional; if set it must be one of the known styles
    style = data.get("style")
    if style is not None and style not in VALID_STYLES:
        errs.append(EditPlanValidationError(
            SEVERITY_BLOCK, "style",
            f"invalid style: {style!r}, expected {sorted(VALID_STYLES)}",
        ))

    beats = data.get("beats")
    if not isinstance(beats, list) or not beats:
        errs.append(EditPlanValidationError(
            SEVERITY_BLOCK, "beats", "must be a non-empty list",
        ))
        return errs

    seen_beat_ids: set[str] = set()
    for i, raw_beat in enumerate(beats):
        prefix = f"beats[{i}]"
        if not isinstance(raw_beat, dict):
            errs.append(EditPlanValidationError(SEVERITY_BLOCK, prefix, "must be an object"))
            continue
        bid = raw_beat.get("beat_id", "")
        if bid in seen_beat_ids:
            errs.append(EditPlanValidationError(
                SEVERITY_BLOCK, f"{prefix}.beat_id", f"duplicate beat_id: {bid!r}",
            ))
        seen_beat_ids.add(bid)
        _validate_beat_dict(
            raw_beat, prefix, errs,
            beat_ids=beat_ids,
            catalog_asset_ids=catalog_asset_ids,
            template_registry=template_registry,
        )

    return errs


def validate_edit_plan(
    plan: EditPlan,
    *,
    beat_ids: set[str] | None = None,
    catalog_asset_ids: set[str] | None = None,
    template_registry: TemplateRegistry | None = None,
) -> list[EditPlanValidationError]:
    """Validate a constructed EditPlan."""
    return validate_edit_plan_dict(
        plan.to_dict(),
        beat_ids=beat_ids,
        catalog_asset_ids=catalog_asset_ids,
        template_registry=template_registry,
    )


# ── Per-beat validation ───────────────────────────────────────────────────


def _validate_beat_dict(
    beat: dict,
    prefix: str,
    errs: list[EditPlanValidationError],
    *,
    beat_ids: set[str] | None,
    catalog_asset_ids: set[str] | None,
    template_registry: TemplateRegistry | None,
) -> None:
    # Required fields
    for field in (
        "beat_id", "template_id", "avatar_mode", "caption_mode", "split_ratio",
        "candidate_assets", "selected_asset_id", "selection_confidence",
        "selection_reason", "fallback_asset_ids", "human_review_required",
        "motion_budget", "rationale",
    ):
        if field not in beat:
            errs.append(EditPlanValidationError(
                SEVERITY_BLOCK, f"{prefix}.{field}", "required field missing",
            ))

    # Cross-reference beat_id with beat_map
    bid = beat.get("beat_id", "")
    if beat_ids is not None and bid and bid not in beat_ids:
        errs.append(EditPlanValidationError(
            SEVERITY_BLOCK, f"{prefix}.beat_id",
            f"E008: beat {bid!r} does not exist in beat_map",
        ))

    # Template id
    template_id = beat.get("template_id", "")
    if template_registry is not None and template_id and not template_registry.has(template_id):
        errs.append(EditPlanValidationError(
            SEVERITY_BLOCK, f"{prefix}.template_id",
            f"E001: unknown template_id: {template_id!r}",
        ))

    # Caption mode
    cm = beat.get("caption_mode")
    if cm and cm not in VALID_CAPTION_MODES:
        errs.append(EditPlanValidationError(
            SEVERITY_BLOCK, f"{prefix}.caption_mode",
            f"E005: invalid caption_mode: {cm!r}, expected {sorted(VALID_CAPTION_MODES)}",
        ))

    # Split ratio
    sr = beat.get("split_ratio")
    if sr and not _is_valid_split_ratio(sr):
        errs.append(EditPlanValidationError(
            SEVERITY_BLOCK, f"{prefix}.split_ratio",
            f"E006: invalid split_ratio: {sr!r} (expected 'N/M' summing to 100)",
        ))

    # Avatar mode (free-form, non-empty)
    am = beat.get("avatar_mode")
    if am is not None and (not isinstance(am, str) or not am.strip()):
        errs.append(EditPlanValidationError(
            SEVERITY_BLOCK, f"{prefix}.avatar_mode",
            f"E007: avatar_mode must be a non-empty string",
        ))

    # Proof class
    pc = beat.get("proof_class")
    if pc is not None and pc not in PROOF_CLASSES:
        errs.append(EditPlanValidationError(
            SEVERITY_BLOCK, f"{prefix}.proof_class",
            f"E003: invalid proof_class: {pc!r}, expected one of {sorted(PROOF_CLASSES)} or null",
        ))

    # Selected asset cross-reference
    sa_id = beat.get("selected_asset_id")
    sa_filename = beat.get("selected_asset_filename")
    if catalog_asset_ids is not None and sa_id and sa_id not in catalog_asset_ids and not sa_filename:
        errs.append(EditPlanValidationError(
            SEVERITY_BLOCK, f"{prefix}.selected_asset_id",
            f"E002: asset {sa_id!r} not found in catalog and no selected_asset_filename hint",
        ))

    # Selection confidence range
    sc = beat.get("selection_confidence")
    if sc is not None and not (0 <= sc <= 1):
        errs.append(EditPlanValidationError(
            SEVERITY_BLOCK, f"{prefix}.selection_confidence",
            f"out of range [0,1]: {sc}",
        ))

    # Motion budget shape
    mb = beat.get("motion_budget")
    if isinstance(mb, dict):
        _validate_motion_budget_dict(mb, f"{prefix}.motion_budget", errs)


def _validate_motion_budget_dict(
    mb: dict, prefix: str, errs: list[EditPlanValidationError]
) -> None:
    if "hero" not in mb:
        errs.append(EditPlanValidationError(
            SEVERITY_BLOCK, f"{prefix}.hero", "required (every beat needs at least one hero motion)",
        ))
        return

    for role in ("hero", "support", "accent"):
        event = mb.get(role)
        if event is None:
            continue
        if not isinstance(event, dict):
            errs.append(EditPlanValidationError(
                SEVERITY_BLOCK, f"{prefix}.{role}", "must be an object",
            ))
            continue
        preset = event.get("preset")
        if preset is not None:
            in_enter = preset in RENDERER_ENTER_PRESETS
            in_exit = preset in RENDERER_EXIT_PRESETS
            if not (in_enter or in_exit):
                errs.append(EditPlanValidationError(
                    SEVERITY_BLOCK, f"{prefix}.{role}.preset",
                    f"E004: unsupported motion preset: {preset!r}",
                ))
                continue
            df = event.get("duration_frames")
            if df is not None and isinstance(df, int):
                lo, hi = ENTER_DUR_BOUNDS if in_enter else EXIT_DUR_BOUNDS
                if not (lo <= df <= hi):
                    errs.append(EditPlanValidationError(
                        SEVERITY_WARN, f"{prefix}.{role}.duration_frames",
                        f"{df} outside editorial bounds [{lo},{hi}] for preset {preset!r}",
                    ))


def _is_valid_split_ratio(value: str) -> bool:
    """A split ratio like '40/60' must parse and sum to 100."""
    try:
        a, b = value.split("/")
        return int(a) + int(b) == 100
    except (ValueError, AttributeError):
        return False
