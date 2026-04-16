"""lib.feature_mockups — pre-built FeatureMockup overlay configs.

Reusable visual mockups for common product features (sandboxing, credentials,
checkpointing, tracing, monitoring, scaling, integration, performance, etc.).
Each preset is a dict with: label, iconPath (24x24 viewBox SVG path),
optional iconPath2, default details bullets, category, description.

Usage from a build_timeline.py script:

    from lib.feature_mockups import preset

    overlays = [
        # Pull a preset and use as-is
        {"beat_id": "beat-03", "type": "FeatureMockup",
         "start": 14.12, "end": 16.12,
         "props": {**preset("sandboxing"), "accentColor": "#D97757"}},

        # Pull a preset and override fields
        {"beat_id": "beat-03", "type": "FeatureMockup",
         "start": 17.04, "end": 18.08,
         "props": {**preset("tracing"),
                   "details": ["Custom bullet 1", "Custom bullet 2"],
                   "accentColor": "#D97757"}},
    ]

Adding new presets:
- Edit lib/feature_mockups/presets.json
- Add a key with: label, iconPath, optional iconPath2, details (list),
  category, description
- The iconPath uses a 24x24 viewBox SVG path. Lucide icons
  (https://lucide.dev) are a good source — open the icon and copy the
  `<path d="...">` value.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

PRESETS_FILE = Path(__file__).parent / "presets.json"


@lru_cache(maxsize=1)
def _load() -> dict[str, dict]:
    raw = json.loads(PRESETS_FILE.read_text(encoding="utf-8"))
    # Strip schema/metadata keys
    return {k: v for k, v in raw.items() if not k.startswith("$")}


def list_presets() -> list[str]:
    """Return all available preset names."""
    return sorted(_load().keys())


def preset(name: str) -> dict:
    """Return the props dict for a preset.

    Strips internal metadata fields (category, description) so the result
    can be passed straight as `props` to a FeatureMockup overlay entry.
    """
    presets = _load()
    if name not in presets:
        raise KeyError(
            f"Unknown feature mockup preset: {name!r}. "
            f"Available: {', '.join(list_presets())}"
        )
    p = presets[name].copy()
    p.pop("category", None)
    p.pop("description", None)
    return p


def by_category(category: str) -> list[str]:
    """Return all preset names in a category (security, observability, etc.)."""
    return sorted(
        name
        for name, p in _load().items()
        if p.get("category") == category
    )


def describe(name: str) -> str:
    """Return the human description for a preset."""
    presets = _load()
    if name not in presets:
        raise KeyError(f"Unknown preset: {name!r}")
    return presets[name].get("description", "")
