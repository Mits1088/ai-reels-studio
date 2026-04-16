"""
beat_registry.py — Deterministic beat-to-component lookup.

Equivalent to the Remotion skills system's exampleIdMap:
instead of asking Claude to reason about component selection
each time, this provides a zero-reasoning table lookup.

Usage in Phase 4b-ii (component mapping):
    from lib.beat_registry import lookup, get_background, get_sfx

    decision = lookup(style="editorial-authority", classification="number_proof_with_asset")
    # → {
    #     "primary": ["FramedImage", "OverlayKeyword"],
    #     "avatar_layout": "split-screen",
    #     "default_transition": { "enter": "zoom-in", ... },
    #     "notes": "FramedImage shows the proof. OverlayKeyword echoes the number."
    #   }

    bg = get_background(style="cinematic-presenter", classification="direct_address")
    # → "GradientMesh + SmokeWisp"

    sfx = get_sfx(classification="hook_opening")
    # → ["@sfx/whoosh on entry", "@sfx/ding per brand logo reveal"]

CLI (for use in shot-list skill):
    python -m lib.beat_registry lookup editorial-authority number_proof_with_asset
    python -m lib.beat_registry list-classifications
    python -m lib.beat_registry list-sfx
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_REGISTRY_PATH = Path(__file__).parent / "beat_registry.json"
_registry: dict | None = None


def _load() -> dict:
    global _registry
    if _registry is None:
        _registry = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    return _registry


def lookup(style: str, classification: str) -> dict[str, Any]:
    """
    Return the component decision for a beat.

    Args:
        style: "editorial-authority" or "cinematic-presenter"
        classification: beat classification key (see list_classifications())

    Returns:
        dict with keys: primary, secondary, avatar_layout, content_zone,
        default_transition, mandatory_extras, notes.
        Returns {} if no match found.
    """
    reg = _load()
    style_map = reg.get("component_map", {}).get(style, {})
    return style_map.get(classification, {})


def get_background(style: str, classification: str) -> str:
    """Return the recommended background component for a beat."""
    reg = _load()
    bg_map = reg.get("background_map", {}).get(style, {})
    return bg_map.get(classification, bg_map.get("_default", ""))


def get_sfx(classification: str) -> list[str]:
    """Return recommended SFX entries for a beat classification."""
    reg = _load()
    return reg.get("sfx_map", {}).get(classification, [])


def list_classifications() -> list[str]:
    """List all valid beat classification keys."""
    reg = _load()
    return list(reg.get("classifications", {}).keys())


def get_classification_info(classification: str) -> dict:
    """Return pattern description + examples for a classification."""
    reg = _load()
    return reg.get("classifications", {}).get(classification, {})


def get_mandatory_brand_rule() -> str:
    return _load().get("mandatory_brand_rule", "")


def format_decision(style: str, classification: str) -> str:
    """Format a human-readable component decision for shot-list output."""
    decision = lookup(style, classification)
    if not decision:
        return f"[No registry entry for {style}/{classification}]"

    lines = [
        f"**Components:** {', '.join(decision.get('primary', []))}",
        f"**Avatar layout:** {decision.get('avatar_layout', '—')}",
        f"**Content zone:** {decision.get('content_zone', '—')}",
    ]

    transition = decision.get("default_transition", {})
    if transition:
        t_str = f"enter:{transition.get('enter','')} ({transition.get('enterDur',0)}f) / exit:{transition.get('exit','')} ({transition.get('exitDur',0)}f)"
        if transition.get("kenBurns"):
            t_str += " / kenBurns:true"
        lines.append(f"**Default transition:** {t_str}")

    extras = decision.get("mandatory_extras", [])
    if extras:
        lines.append(f"**Mandatory extras:** {'; '.join(extras)}")

    notes = decision.get("notes", "")
    if notes:
        lines.append(f"**Notes:** {notes}")

    bg = get_background(style, classification)
    if bg:
        lines.append(f"**Background:** {bg}")

    sfx = get_sfx(classification)
    if sfx:
        lines.append(f"**SFX:** {'; '.join(sfx)}")

    return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────────────

def _cli():
    args = sys.argv[1:]
    if not args:
        print("Usage:")
        print("  python -m lib.beat_registry lookup <style> <classification>")
        print("  python -m lib.beat_registry list-classifications")
        print("  python -m lib.beat_registry list-sfx")
        print("  python -m lib.beat_registry brand-rule")
        return

    cmd = args[0]

    if cmd == "lookup" and len(args) == 3:
        style, classification = args[1], args[2]
        print(format_decision(style, classification))

    elif cmd == "list-classifications":
        for c in list_classifications():
            info = get_classification_info(c)
            print(f"{c:35s}  {info.get('pattern', '')}")

    elif cmd == "list-sfx":
        reg = _load()
        for classification, sfx_list in reg.get("sfx_map", {}).items():
            print(f"{classification:35s}  {', '.join(sfx_list)}")

    elif cmd == "brand-rule":
        print(get_mandatory_brand_rule())

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    _cli()
