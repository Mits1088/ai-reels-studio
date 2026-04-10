"""
Component existence guard — validates that referenced Remotion components exist.

Scans remotion/src/components/ for .tsx files and builds an inventory.
Used during shot-list validation to catch references to unbuilt components
before they reach assembly.

CLI:
    python -m lib.components list                    # Show all available components
    python -m lib.components check <name> [<name>]   # Check if components exist
"""

import sys
from pathlib import Path


# ── Component discovery ────────────────────────────────────────────────────

REMOTION_COMPONENTS_DIR = Path(__file__).resolve().parent.parent / "remotion" / "src" / "components"

# Components documented as planned but not yet built
NOT_BUILT = {
    "StackedImageReveal": "Use multiple FramedImage entries in rapid sequence (3-5 frames each)",
    "ImageMontage": "Use multiple FramedImage entries in rapid sequence (3-5 frames each)",
}


def discover_components(components_dir: Path | None = None) -> set[str]:
    """Scan remotion/src/components/ recursively for .tsx files.
    Returns set of component names (filename without extension).
    """
    root = components_dir or REMOTION_COMPONENTS_DIR
    if not root.exists():
        return set()

    components = set()
    for f in root.rglob("*.tsx"):
        name = f.stem
        # Skip index files and test files
        if name in ("index", "presets") or name.startswith("test"):
            continue
        components.add(name)
    return components


def check_components(names: list[str],
                     components_dir: Path | None = None) -> list[dict]:
    """Check if component names exist. Returns list of issues (empty = all good).

    Each issue is a dict with: name, status (NOT_FOUND | NOT_BUILT), hint
    """
    available = discover_components(components_dir)
    issues = []

    for name in names:
        if name in NOT_BUILT:
            issues.append({
                "name": name,
                "status": "NOT_BUILT",
                "hint": NOT_BUILT[name],
            })
        elif name not in available:
            issues.append({
                "name": name,
                "status": "NOT_FOUND",
                "hint": f"No {name}.tsx found in remotion/src/components/",
            })

    return issues


# ── CLI ────────────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage:")
        print("  python -m lib.components list")
        print("  python -m lib.components check <ComponentName> [<ComponentName> ...]")
        sys.exit(1)

    cmd = args[0]

    if cmd == "list":
        components = sorted(discover_components())
        print(f"Available Remotion components ({len(components)}):")
        for c in components:
            print(f"  {c}")
        print(f"\nNot yet built ({len(NOT_BUILT)}):")
        for name, hint in sorted(NOT_BUILT.items()):
            print(f"  {name} — {hint}")

    elif cmd == "check":
        names = args[1:]
        if not names:
            print("Usage: python -m lib.components check <ComponentName> [...]")
            sys.exit(1)

        issues = check_components(names)
        if not issues:
            print(f"OK: all {len(names)} component(s) exist.")
            sys.exit(0)
        else:
            for issue in issues:
                status = issue["status"]
                name = issue["name"]
                hint = issue["hint"]
                if status == "NOT_BUILT":
                    print(f"NOT_BUILT: {name} — planned but not implemented. Workaround: {hint}")
                else:
                    print(f"NOT_FOUND: {name} — {hint}")
            sys.exit(1)

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
