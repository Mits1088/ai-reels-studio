"""LobeHub Icons — AI/LLM brand SVG extractor.

@lobehub/icons is an npm package containing 300+ AI/LLM brand React
components. This module extracts the underlying SVG path data from the
package's Mono.js files and writes standalone SVG files that can be
loaded into Remotion via <Img> or <Icon> components.

Why not use the React components directly?
- The reel pipeline already uses static asset files in remotion/public/
- Static SVGs work with the existing FramedImage / Img / overlay layer
- Avoids adding a Remotion render-time dependency on @lobehub/icons
- One install populates the asset library; reels reference SVG paths

The package must be installed in remotion/node_modules. Run:
  cd remotion && npm install @lobehub/icons

Variants per brand (when available):
  Mono   — single-color path, color via fill="currentColor"
  Color  — multi-color version with brand colors baked in
  Avatar — Mono wrapped in a colored circle background
  Text   — wordmark logo
"""

from __future__ import annotations

import re
from pathlib import Path

from . import catalog as cat


PACKAGE_ROOT = Path("remotion/node_modules/@lobehub/icons/es")
LICENSE = "MIT"


def package_root(repo_root: Path | None = None) -> Path:
    """Return the absolute path to @lobehub/icons/es."""
    base = Path(repo_root) if repo_root else Path.cwd()
    return base / PACKAGE_ROOT


def list_brands(repo_root: Path | None = None) -> list[str]:
    """List all available brand names from the installed package."""
    root = package_root(repo_root)
    if not root.exists():
        raise FileNotFoundError(
            f"@lobehub/icons not installed. Run: cd remotion && npm install @lobehub/icons"
        )
    return sorted(
        d.name
        for d in root.iterdir()
        if d.is_dir() and not d.name.startswith(("_", "."))
    )


def find_brand(query: str, repo_root: Path | None = None) -> str | None:
    """Resolve a fuzzy brand name to its canonical lobehub directory.

    Examples:
      "anthropic"   -> "Anthropic"
      "Claude"      -> "Claude"
      "open-ai"     -> "OpenAI"
      "chatgpt"     -> "ChatGPT" (if exists, else None)
    """
    brands = list_brands(repo_root)
    norm_query = re.sub(r"[\s\-_]+", "", query).lower()
    for brand in brands:
        if re.sub(r"[\s\-_]+", "", brand).lower() == norm_query:
            return brand
    return None


def extract_mono_svg(brand: str, repo_root: Path | None = None) -> str:
    """Extract a standalone SVG string from a brand's Mono.js file.

    Returns the SVG as a UTF-8 string with viewBox="0 0 24 24" and
    fill="currentColor" (the color is set by the consumer at render time).
    """
    canonical = find_brand(brand, repo_root)
    if canonical is None:
        raise ValueError(
            f"Brand '{brand}' not found in @lobehub/icons. "
            f"Try `python -m lib.assets ai-brands` to list available brands."
        )

    mono_path = package_root(repo_root) / canonical / "components" / "Mono.js"
    if not mono_path.exists():
        raise FileNotFoundError(
            f"No Mono variant for '{canonical}' at {mono_path}. "
            f"Try a different variant or use simpleicons.py for this brand."
        )

    js = mono_path.read_text(encoding="utf-8")

    viewbox_match = re.search(r'viewBox:\s*"([^"]+)"', js)
    viewbox = viewbox_match.group(1) if viewbox_match else "0 0 24 24"

    # Capture every <path d="..."/> entry — some icons are multi-path
    path_matches = re.findall(r'd:\s*"([^"]+)"', js)
    if not path_matches:
        raise RuntimeError(
            f"Could not extract SVG path data from {mono_path}. "
            f"The package format may have changed."
        )

    paths_xml = "\n  ".join(
        f'<path d="{d}" fill="currentColor"/>' for d in path_matches
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" '
        f'fill-rule="evenodd">\n'
        f'  <title>{canonical}</title>\n'
        f"  {paths_xml}\n"
        f"</svg>\n"
    )
    return svg


def fetch(
    brand: str,
    out_dir: Path,
    project_dir: Path | None = None,
    filename: str | None = None,
    repo_root: Path | None = None,
) -> Path:
    """Extract a brand SVG to disk.

    Args:
      brand: Brand name (fuzzy-matched against the installed package)
      out_dir: Directory to save the SVG
      project_dir: If provided, register in the project's sourced catalog
      filename: Optional output filename (default: <Brand>.svg)
      repo_root: Override the repo root for testing

    Returns:
      Path to the saved SVG file.
    """
    canonical = find_brand(brand, repo_root)
    if canonical is None:
        raise ValueError(
            f"Brand '{brand}' not found in @lobehub/icons. "
            f"Run `python -m lib.assets ai-brands` to list available brands."
        )

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = filename or f"{canonical}.svg"
    dest = out_dir / name

    svg = extract_mono_svg(canonical, repo_root)
    dest.write_text(svg, encoding="utf-8")

    if project_dir is not None:
        try:
            rel_path = str(dest.relative_to(Path(project_dir)))
        except ValueError:
            rel_path = str(dest)
        cat.register(
            project_dir,
            cat.SourcedAsset(
                source="lobehub",
                asset_type="logo",
                local_path=rel_path,
                query=brand,
                license=LICENSE,
                attribution_required=False,
                metadata={"canonical": canonical, "variant": "Mono"},
            ),
        )

    return dest


def fetch_many(
    brands: list[str],
    out_dir: Path,
    project_dir: Path | None = None,
    repo_root: Path | None = None,
) -> list[Path]:
    """Batch extract a list of brands. Logs failures, returns successes."""
    results: list[Path] = []
    for brand in brands:
        try:
            results.append(
                fetch(brand, out_dir, project_dir=project_dir, repo_root=repo_root)
            )
        except Exception as e:
            print(f"  ! failed: {brand} ({e})")
    return results
