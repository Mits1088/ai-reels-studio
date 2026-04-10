"""
Pre-render validation — checks everything before npx remotion render.

Runs:
  1. Timeline schema validation
  2. Asset existence in remotion/public/
  3. Component existence for overlay types
  4. Video encoding sanity (ffprobe)
  5. TypeScript compile check

CLI:
    python -m lib.preflight_render <project-dir>
    python -m lib.preflight_render projects/gemma-4
"""

import json
import subprocess
import sys
from pathlib import Path


def preflight(project_dir: Path, remotion_dir: Path | None = None) -> list[str]:
    """Run all pre-render checks. Returns list of issues (empty = ready to render)."""
    issues: list[str] = []
    root = project_dir.parent if project_dir.name != "remotion" else project_dir.parent

    if remotion_dir is None:
        remotion_dir = root / "remotion"
    public_dir = remotion_dir / "public"

    # 1. Timeline exists and loads
    tl_path = public_dir / "timeline.json"
    if not tl_path.exists():
        # Try project output
        tl_project = project_dir / "output" / "timeline.json"
        if tl_project.exists():
            issues.append(f"timeline.json not in remotion/public/ — copy from {tl_project}")
        else:
            issues.append("timeline.json not found in remotion/public/ or project output/")
        return issues

    try:
        with open(tl_path, "r", encoding="utf-8") as f:
            timeline = json.load(f)
    except json.JSONDecodeError as e:
        issues.append(f"timeline.json invalid JSON: {e}")
        return issues

    # 2. Required top-level fields
    for field in ("total_duration", "lanes"):
        if field not in timeline:
            issues.append(f"timeline.json missing required field: {field}")

    if "lanes" not in timeline:
        return issues

    # 3. Required lanes
    for lane in ("avatar", "demo", "captions", "sfx"):
        if lane not in timeline["lanes"]:
            issues.append(f"timeline.json missing required lane: {lane}")

    # 4. Audio file exists
    audio = timeline.get("audio", "source.wav")
    if not (public_dir / audio).exists():
        issues.append(f"audio file not found: {audio}")

    # 5. Avatar file exists
    avatar = timeline.get("avatar_file", "avatar.mp4")
    if avatar and not (public_dir / avatar).exists():
        issues.append(f"avatar file not found: {avatar}")

    # 6. All referenced assets exist
    asset_lanes = ["demo", "broll", "support", "sfx", "music"]
    for lane_name in asset_lanes:
        entries = timeline["lanes"].get(lane_name, [])
        for i, entry in enumerate(entries):
            asset = entry.get("asset")
            if asset and not (public_dir / asset).exists():
                issues.append(f"lanes.{lane_name}[{i}]: asset not found: {asset}")

    # 7. Overlay component existence
    overlays = timeline["lanes"].get("overlays", [])
    if overlays:
        try:
            from lib.components import check_components
            types = list({o["type"] for o in overlays if "type" in o})
            comp_issues = check_components(types)
            for ci in comp_issues:
                issues.append(f"overlay component {ci['status']}: {ci['name']} — {ci['hint']}")
        except ImportError:
            pass  # lib.components not available, skip

    # 8. Video encoding spot-check (first 3 video assets)
    video_assets = []
    for lane_name in ["demo", "broll", "support"]:
        for entry in timeline["lanes"].get(lane_name, []):
            asset = entry.get("asset", "")
            if asset and asset.lower().endswith((".mp4", ".webm", ".mov")):
                full = public_dir / asset
                if full.exists() and asset not in video_assets:
                    video_assets.append(asset)
    for asset in video_assets[:3]:
        full = public_dir / asset
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries",
                 "stream=codec_name,r_frame_rate,pix_fmt",
                 "-of", "compact", str(full)],
                capture_output=True, text=True, timeout=10,
            )
            output = result.stdout
            if "codec_name=h264" not in output:
                issues.append(f"encoding: {asset} is not h264")
            if "pix_fmt=yuv420p" not in output:
                issues.append(f"encoding: {asset} is not yuv420p")
        except FileNotFoundError:
            issues.append("ffprobe not found — cannot verify video encoding")
            break
        except subprocess.TimeoutExpired:
            issues.append(f"encoding: ffprobe timeout on {asset}")

    # 9. TypeScript compile check
    try:
        result = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=str(remotion_dir),
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            # Just report first 5 errors
            lines = result.stdout.strip().split("\n")
            for line in lines[:5]:
                if line.strip():
                    issues.append(f"tsc: {line.strip()}")
            if len(lines) > 5:
                issues.append(f"tsc: ... and {len(lines) - 5} more errors")
    except FileNotFoundError:
        issues.append("npx not found — cannot run TypeScript check")
    except subprocess.TimeoutExpired:
        issues.append("tsc: compile check timed out")

    return issues


# ── CLI ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m lib.preflight_render <project-dir>")
        print("  Checks timeline, assets, components, encoding, and TypeScript before render.")
        sys.exit(1)

    project_dir = Path(sys.argv[1])
    if not project_dir.exists():
        print(f"ERROR: Directory not found: {project_dir}")
        sys.exit(1)

    print(f"Pre-render check: {project_dir.name}")
    print("=" * 50)

    issues = preflight(project_dir)

    if not issues:
        print("READY TO RENDER — all checks passed.")
        sys.exit(0)
    else:
        print(f"NOT READY — {len(issues)} issue(s):")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)
