"""
Layout templates — the named configurations that bundle:
  - avatar mode
  - split ratio
  - background type
  - caption behavior
  - template class (ANCHOR or PROOF)
  - which proof classes the template can serve

Loaded from training/derived/template-registry.json (produced by
training/derive_style_pack.py from annotated reference reels).

This module is read-only. Adding a new template means annotating a new
training example and re-running derive_style_pack.py — not editing code.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


# Canonical class enum. Templates are either face-led (ANCHOR) or content-led (PROOF).
VALID_TEMPLATE_CLASSES: frozenset[str] = frozenset({"ANCHOR", "PROOF"})

# The 5 caption modes derived from caption-modes.json. The compiler maps
# template_id → caption_mode via the registry's template_to_caption_mode lookup.
VALID_CAPTION_MODES: frozenset[str] = frozenset({
    "standard",
    "headline",
    "suppressed",
    "section-label",
    "badge-overlay",
})

# Default location of the derived registry. Override via load_template_registry(...)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_REGISTRY_PATH = _REPO_ROOT / "training" / "derived" / "template-registry.json"
DEFAULT_CAPTION_MODES_PATH = _REPO_ROOT / "training" / "derived" / "caption-modes.json"


@dataclass(frozen=True)
class Template:
    """A single layout template definition.

    Fields mirror training/derived/template-registry.json. Frozen so the
    registry is read-only at runtime — adding templates means re-running
    training/derive_style_pack.py, not mutating in place.
    """
    id: str
    description: str
    avatar_mode: str
    split_ratio: str               # "40/60", "65/35", "100/0", "0/100", "50/50"
    background: str
    caption_behavior: str          # raw value from registry
    proof_classes_served: tuple[str, ...]
    template_class: str            # "ANCHOR" or "PROOF"
    seen_in: tuple[str, ...]
    occurrences: int


@dataclass(frozen=True)
class TemplateRegistry:
    """Loaded template registry. Read-only after construction."""
    templates: dict[str, Template]
    template_to_caption_mode: dict[str, str]   # template_id → caption_mode
    derived_from: tuple[str, ...]

    def get(self, template_id: str) -> Template | None:
        return self.templates.get(template_id)

    def has(self, template_id: str) -> bool:
        return template_id in self.templates

    def by_class(self, template_class: str) -> list[Template]:
        if template_class not in VALID_TEMPLATE_CLASSES:
            return []
        return [t for t in self.templates.values() if t.template_class == template_class]

    def by_proof_class(self, proof_class: str) -> list[Template]:
        return [
            t for t in self.templates.values()
            if proof_class in t.proof_classes_served
        ]

    def caption_mode_for(self, template_id: str) -> str | None:
        """Return the caption mode for a template, or None if unknown.

        Prefers the explicit template_to_caption_mode lookup from
        caption-modes.json. Falls back to the template's own caption_behavior
        field when it is itself a known caption mode. Returns None when the
        template is unknown OR its caption_behavior is not a known mode.
        """
        if template_id in self.template_to_caption_mode:
            return self.template_to_caption_mode[template_id]
        tmpl = self.get(template_id)
        if tmpl and tmpl.caption_behavior in VALID_CAPTION_MODES:
            return tmpl.caption_behavior
        return None

    def ids(self) -> list[str]:
        return sorted(self.templates.keys())


def load_template_registry(
    registry_path: Path | None = None,
    caption_modes_path: Path | None = None,
) -> TemplateRegistry:
    """Load the derived template registry plus caption mode lookup.

    Returns an empty registry (templates={}, template_to_caption_mode={})
    if the files do not exist — callers should handle the empty case
    rather than crashing, since training/derived/ may not be populated yet.
    """
    rp = registry_path or DEFAULT_REGISTRY_PATH
    cp = caption_modes_path or DEFAULT_CAPTION_MODES_PATH

    templates: dict[str, Template] = {}
    derived_from: tuple[str, ...] = ()

    if rp.exists():
        with open(rp, "r", encoding="utf-8") as f:
            data = json.load(f)
        derived_from = tuple(data.get("_derived_from", []))
        for tid, raw in data.get("templates", {}).items():
            templates[tid] = Template(
                id=raw["id"],
                description=raw.get("description", ""),
                avatar_mode=raw.get("avatar_mode", ""),
                split_ratio=raw.get("split_ratio") or "",
                background=raw.get("background", ""),
                caption_behavior=raw.get("caption_behavior", "standard"),
                proof_classes_served=tuple(raw.get("proof_classes_served", [])),
                template_class=raw.get("template_class", "PROOF"),
                seen_in=tuple(raw.get("seen_in", [])),
                occurrences=int(raw.get("occurrences", 0)),
            )

    template_to_caption_mode: dict[str, str] = {}
    if cp.exists():
        with open(cp, "r", encoding="utf-8") as f:
            data = json.load(f)
        template_to_caption_mode = dict(data.get("template_to_caption_mode", {}))

    return TemplateRegistry(
        templates=templates,
        template_to_caption_mode=template_to_caption_mode,
        derived_from=derived_from,
    )
