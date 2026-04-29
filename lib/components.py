"""
Component existence guard — validates that referenced Remotion components exist.

Scans remotion/src/components/ for .tsx files and builds an inventory.
Used during shot-list validation to catch references to unbuilt components
before they reach assembly.

CLI:
    python -m lib.components list                               # Show all available components
    python -m lib.components check <name> [<name>]              # Check if components exist
    python -m lib.components audit-selection                    # Advisory: components vs OVERLAY_REGISTRY vs Step 2b
    python -m lib.components audit-selection --show-excluded    # Also list excluded components
"""

import re
import sys
from pathlib import Path


# ── Component discovery ────────────────────────────────────────────────────

REMOTION_COMPONENTS_DIR = Path(__file__).resolve().parent.parent / "remotion" / "src" / "components"
GENERIC_REEL_PATH = Path(__file__).resolve().parent.parent / "remotion" / "src" / "GenericReelComposition.tsx"
COMPONENT_MAPPING_PATH = Path(__file__).resolve().parent.parent / ".claude" / "rules" / "component-mapping.md"

# Components documented as planned but not yet built
NOT_BUILT = {
    "StackedImageReveal": "Use multiple FramedImage entries in rapid sequence (3-5 frames each)",
    "ImageMontage": "Use multiple FramedImage entries in rapid sequence (3-5 frames each)",
}

# Components that should never appear in Step 2b candidate sets
EXCLUDED_FROM_SELECTION: dict[str, str] = {
    # Internal/system-only
    "AuroraBackground": "internal/system — scene background",
    "BackgroundBeams": "internal/system — scene background",
    "GradientMesh": "internal/system — scene background",
    "SmokeWisp": "internal/system — scene layer",
    "FocusVignette": "internal/system — scene layer",
    "GlowBorder": "internal/system — BRollVideo internal",
    "NoiseOverlay": "internal/system — global film grain",
    "AnimatedBackground": "internal/system — scene layer",
    "AnimatedGrid": "internal/system — scene layer",
    "AnimatedDivider": "internal/system — scene layer",
    "HookIntroScene": "internal/system — scene block",
    "SkillActivationScene": "internal/system — scene block",
    "SkillQuestionsScene": "internal/system — scene block",
    "ImageLayer": "internal/system — composition layer",
    "Caption": "internal/system — subtitle layer",
    "TransitionWrapper": "internal/system — animation wrapper",
    "CircuitTrace": "internal/system — decorative",
    "EmojiReactions": "internal/system — decorative",
    "Confetti": "internal/system — decorative",
    "FloatingIcons": "internal/system — decorative",
    "GlitchOverlay": "internal/system — decorative",
    "IconOrbit": "internal/system — decorative",
    "ImageAutoSlider": "internal/system — decorative",
    "LetterboxCinematic": "internal/system — scene layer",
    "MorphBlob": "internal/system — decorative",
    "ParticleNetwork": "internal/system — decorative",
    "ProgressDots": "internal/system — decorative",
    "PrismFlare": "internal/system — decorative",
    "PulsingOrb": "internal/system — decorative",
    "RadialBurst": "internal/system — decorative",
    "RipplePulse": "internal/system — decorative",
    "ShimmerBar": "internal/system — decorative",
    "SpotlightBeam": "internal/system — decorative",
    "SweepReveal": "internal/system — decorative",
    "ZoomParallax": "internal/system — decorative",
    "PunchInZoom": "internal/system — FramedImage internal",
    "AuroraGlow": "internal/system — decorative",
    # Display-mode only
    "AppWindow": "display-mode only — use display: 'app-window'",
    "GuidedDemo": "display-mode only — use display: 'guided-demo'",
    "ImageGrid2x2": "display-mode only — use display: 'image-grid-2x2'",
    "ScrollImage": "display-mode only — use display: 'scroll-image'",
    # Non-overlay content presenters
    "AvatarVideo": "non-overlay — drives avatar lane entries",
    "BRollVideo": "non-overlay — drives demo/broll lane entries",
    "FramedImage": "non-overlay — drives demo/broll lane entries",
    # Deprecated
    "NumberCounter": "deprecated — use StatCounter",
    "ClaudeLogoReveal": "deprecated — use LogoOverlay with bounce:true",
    "CodeReveal": "deprecated — use TypewriterCode",
    # YouTube-pipeline only
    "LinkOverlay": "YouTube-only — not for vertical reels",
    "SubscribeCTA": "YouTube-only — not for vertical reels",
    "EndScreen": "YouTube-only — not for vertical reels",
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


# ── Audit helpers ─────────────────────────────────────────────────────────

def discover_registry(tsx_path: Path | None = None) -> set[str]:
    """Parse OVERLAY_REGISTRY entries from GenericReelComposition.tsx.
    Returns set of component names found in the registry block.
    """
    path = tsx_path or GENERIC_REEL_PATH
    if not path.exists():
        return set()

    text = path.read_text(encoding="utf-8")
    # Extract the OVERLAY_REGISTRY block
    match = re.search(r"OVERLAY_REGISTRY[^{]*\{(.+?)\};", text, re.DOTALL)
    if not match:
        return set()

    block = match.group(1)
    # Find bare identifiers (not comments)
    names: set[str] = set()
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("//") or not stripped:
            continue
        # Match bare identifiers (possibly followed by comma or comment)
        m = re.match(r"([A-Z][A-Za-z0-9]+)", stripped)
        if m:
            names.add(m.group(1))
    return names


def discover_candidate_set_components(md_path: Path | None = None) -> set[str]:
    """Parse component names mentioned in Step 2b beat-class candidate tables
    in component-mapping.md.  Returns set of component names.

    The candidate tables live under #### subheadings between
    '### Step 2b' and '### Component Role Reference'.
    """
    path = md_path or COMPONENT_MAPPING_PATH
    if not path.exists():
        return set()

    text = path.read_text(encoding="utf-8")

    # Delimit the section that contains the beat-class candidate tables
    start_marker = "#### Emotional keyword"   # first candidate table heading
    end_marker   = "### Component Role Reference"

    start = text.find(start_marker)
    end   = text.find(end_marker, start)
    if start == -1:
        return set()
    section = text[start:end] if end != -1 else text[start:]

    # Extract backtick-quoted component names from table rows.
    # Accept PascalCase identifiers ≥ 5 chars that are not ALL_CAPS.
    names: set[str] = set()
    for m in re.finditer(r"`([A-Z][A-Za-z0-9]+(?:\s*\(clippkit\))?)`", section):
        raw = m.group(1)
        # Strip the *(clippkit)* suffix if present
        name = re.sub(r"\s*\(clippkit\)$", "", raw)
        if len(name) >= 5 and not name.isupper():
            names.add(name)
    return names


def audit_selection(components_dir: Path | None = None,
                    tsx_path: Path | None = None,
                    md_path: Path | None = None) -> None:
    """Advisory audit: compare built components, OVERLAY_REGISTRY, and Step 2b candidate sets.
    Prints a report to stdout. Exit code 0 always (advisory only — no hard failures).
    """
    built = discover_components(components_dir)
    registry = discover_registry(tsx_path)
    candidate_set = discover_candidate_set_components(md_path)

    # Selectable set: in registry AND in candidate sets AND not excluded
    selectable = registry & candidate_set - set(EXCLUDED_FROM_SELECTION.keys())

    print("=" * 64)
    print("  Component Selection Coverage Audit")
    print("=" * 64)
    print(f"  Built component files:        {len(built)}")
    print(f"  In OVERLAY_REGISTRY:          {len(registry)}")
    print(f"  In Step 2b candidate sets:    {len(candidate_set)}")
    print(f"  Fully selectable (both):      {len(selectable)}")
    print()

    # 1. Built but not in OVERLAY_REGISTRY (excluding excluded set)
    not_registered = built - registry - set(EXCLUDED_FROM_SELECTION.keys())
    if not_registered:
        print(f"[GAP] Built but NOT in OVERLAY_REGISTRY ({len(not_registered)}):")
        for name in sorted(not_registered):
            print(f"  - {name}")
        print()
    else:
        print("[OK] All non-excluded built components are in OVERLAY_REGISTRY")
        print()

    # 2. In OVERLAY_REGISTRY but not in Step 2b (excluding excluded set)
    registry_not_candidate = (registry - candidate_set
                               - set(EXCLUDED_FROM_SELECTION.keys()))
    if registry_not_candidate:
        print(f"[ADVISORY] In OVERLAY_REGISTRY but not in Step 2b candidate sets ({len(registry_not_candidate)}):")
        for name in sorted(registry_not_candidate):
            print(f"  - {name}")
        print("  These can be used in timelines but won't be selected during Phase 4b-ii scoring.")
        print("  Add to candidate sets only if they have genuine semantic fit for a beat class.")
        print()

    # 3. In Step 2b but not in OVERLAY_REGISTRY (would fail to render)
    candidate_not_registry = candidate_set - registry - set(EXCLUDED_FROM_SELECTION.keys())
    if candidate_not_registry:
        print(f"[WARNING] In Step 2b candidate sets but NOT in OVERLAY_REGISTRY ({len(candidate_not_registry)}):")
        for name in sorted(candidate_not_registry):
            print(f"  - {name}  ← would fail to render; add to OVERLAY_REGISTRY")
        print()

    # 4. Excluded components summary
    print(f"[INFO] Excluded from selection ({len(EXCLUDED_FROM_SELECTION)}) — internal/system/deprecated/display-mode/YouTube-only")
    print("  Run with --show-excluded to list them.")
    print()

    # 5. Coverage summary
    print("[SUMMARY]")
    print(f"  Fully selectable components:  {len(selectable)}")
    print(f"  Coverage gaps (not in Step 2b): {len(registry_not_candidate)}")
    print(f"  Render gaps (not in registry):  {len(candidate_not_registry)}")


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

    elif cmd == "audit-selection":
        show_excluded = "--show-excluded" in args[1:]
        audit_selection()
        if show_excluded:
            print("\n[EXCLUDED FROM SELECTION]")
            for name, reason in sorted(EXCLUDED_FROM_SELECTION.items()):
                print(f"  {name}: {reason}")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
