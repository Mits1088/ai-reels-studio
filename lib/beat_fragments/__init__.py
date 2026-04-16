"""
beat_fragments — Example skill library for the reel assembly pipeline.

Equivalent to the Remotion skills system's example skills:
complete, validated timeline.json fragments for proven beat patterns.

Usage:
    python -m lib.beat_fragments list
    python -m lib.beat_fragments show editorial-number-proof
    python -m lib.beat_fragments find editorial-authority number_proof_with_asset
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_FRAGMENTS_DIR = Path(__file__).parent


def list_fragments() -> list[dict]:
    """Return metadata for all available fragments."""
    fragments = []
    for f in sorted(_FRAGMENTS_DIR.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        fragments.append({
            "id": data.get("id", f.stem),
            "style": data.get("style", ""),
            "classification": data.get("classification", ""),
            "description": data.get("description", ""),
            "duration_range_s": data.get("duration_range_s", []),
        })
    return fragments


def get_fragment(fragment_id: str) -> dict | None:
    """Load a fragment by its ID."""
    path = _FRAGMENTS_DIR / f"{fragment_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    # Also try searching by id field
    for f in _FRAGMENTS_DIR.glob("*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        if data.get("id") == fragment_id:
            return data
    return None


def find_fragments(style: str, classification: str) -> list[dict]:
    """Find all fragments matching a style + classification."""
    results = []
    for f in _FRAGMENTS_DIR.glob("*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        if data.get("style") == style and data.get("classification") == classification:
            results.append(data)
    return results


def _cli():
    args = sys.argv[1:]
    if not args or args[0] == "list":
        frags = list_fragments()
        print(f"{'ID':<45} {'STYLE':<25} {'CLASSIFICATION'}")
        print("-" * 90)
        for f in frags:
            dur = f["duration_range_s"]
            dur_str = f"{dur[0]}-{dur[1]}s" if dur else ""
            print(f"{f['id']:<45} {f['style']:<25} {f['classification']}  {dur_str}")
            print(f"    {f['description']}")

    elif args[0] == "show" and len(args) == 2:
        frag = get_fragment(args[1])
        if frag:
            print(json.dumps(frag, indent=2))
        else:
            print(f"Fragment not found: {args[1]}")
            sys.exit(1)

    elif args[0] == "find" and len(args) == 3:
        results = find_fragments(args[1], args[2])
        if results:
            for r in results:
                print(f"\n{'='*60}")
                print(f"Fragment: {r['id']}")
                print(f"Description: {r['description']}")
                print(f"Notes: {r['notes']}")
                print(f"\nAdaptation notes:")
                for note in r.get("adaptation_notes", []):
                    print(f"  • {note}")
        else:
            print(f"No fragments found for {args[1]} / {args[2]}")

    else:
        print("Usage:")
        print("  python -m lib.beat_fragments list")
        print("  python -m lib.beat_fragments show <fragment-id>")
        print("  python -m lib.beat_fragments find <style> <classification>")


if __name__ == "__main__":
    _cli()
