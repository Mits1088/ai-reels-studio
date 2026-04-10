"""
Reel learning capture — post-render knowledge extraction.

Adapted from ruflo's SONA self-learning pattern, sized for
single-operator reel pipeline. Generates learnings.md from
project artifacts after a successful render.

CLI:
    PYTHONPATH=. python -m lib.learn capture projects/<slug>
    PYTHONPATH=. python -m lib.learn compare projects/<slug>
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# ── Helpers ─────────────────────────────────────────────────────────────────

def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


# ── Learning extraction ─────────────────────────────────────────────────────

def _extract_metrics(project_dir: Path) -> dict:
    """Extract quantitative metrics from project artifacts."""
    project = _load_json(project_dir / "project.json")
    beat_map = _load_json(project_dir / "audio" / "beat-map.json")
    timeline = _load_json(project_dir / "output" / "timeline.json")
    qa_report = _load_json(project_dir / "output" / "qa_report.json")

    beats = beat_map.get("beats", [])
    lanes = timeline.get("lanes", {})
    total_dur = beat_map.get("total_duration", timeline.get("total_duration", 0))

    # Beat count
    beat_count = len(beats)

    # SFX count
    sfx_count = len(lanes.get("sfx", []))

    # Screenshot / demo video count
    screenshot_count = 0
    demo_video_count = 0
    image_exts = {".png", ".jpg", ".jpeg", ".webp"}
    video_exts = {".mp4", ".webm", ".mov"}

    seen_assets = set()
    for lane_name in ("demo", "support", "broll"):
        for entry in lanes.get(lane_name, []):
            asset = entry.get("asset", "")
            if asset and asset not in seen_assets:
                seen_assets.add(asset)
                suffix = Path(asset).suffix.lower()
                if suffix in image_exts:
                    screenshot_count += 1
                elif suffix in video_exts:
                    demo_video_count += 1

    # Avatar on-screen percentage
    avatar_entries = lanes.get("avatar", [])
    avatar_time = sum(e.get("end", 0) - e.get("start", 0) for e in avatar_entries)
    avatar_pct = round(avatar_time / total_dur * 100, 1) if total_dur > 0 else 0

    # Visual change frequency
    all_visual = []
    for lane_name in ("avatar", "demo", "support", "broll"):
        all_visual.extend(lanes.get(lane_name, []))
    visual_count = len(all_visual)
    visual_freq = round(total_dur / visual_count, 1) if visual_count > 0 else 0

    # QA info
    qa_verdict = qa_report.get("verdict", "(no QA report)")
    qa_blockers = qa_report.get("blockers", 0)
    qa_warnings = qa_report.get("warnings", 0)

    return {
        "slug": project.get("slug", project_dir.name),
        "style": project.get("style", "cinematic-presenter"),
        "input_quality": project.get("input_quality", "(not set)"),
        "duration": round(total_dur, 1),
        "beat_count": beat_count,
        "sfx_count": sfx_count,
        "screenshot_count": screenshot_count,
        "demo_video_count": demo_video_count,
        "avatar_pct": avatar_pct,
        "visual_freq": visual_freq,
        "qa_verdict": qa_verdict,
        "qa_blockers": qa_blockers,
        "qa_warnings": qa_warnings,
    }


def _detect_hook_pattern(project_dir: Path) -> str:
    """Try to detect the hook pattern from script.md or beat map."""
    script = _read_text(project_dir / "script.md")
    if not script:
        return "(no script found)"

    script_lower = script.lower()
    first_lines = "\n".join(script.split("\n")[:20]).lower()

    if any(w in first_lines for w in ("cost", "paying", "price", "free", "save")):
        return "cost tension"
    elif any(w in first_lines for w in ("secret", "hidden", "nobody", "most people")):
        return "secret knowledge"
    elif any(w in first_lines for w in ("result", "built", "created", "made", "shipped")):
        return "result-first"
    elif any(w in first_lines for w in ("number", "#", "top", "best")):
        return "number + outcome"
    else:
        return "(review needed)"


def capture_learnings(project_dir: Path) -> str:
    """Generate learnings.md from project artifacts.

    Returns the path to the generated file.
    """
    project_dir = Path(project_dir)
    metrics = _extract_metrics(project_dir)
    hook_pattern = _detect_hook_pattern(project_dir)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    md = f"""# Reel Learnings: {metrics['slug']}

**Rendered:** {now}
**Duration:** {metrics['duration']}s
**Style:** {metrics['style']}
**Input quality:** {metrics['input_quality']}
**Revision rounds:** (fill in — how many brief/script/shot-list revisions?)

## Hook
- Pattern: {hook_pattern}
- First frame: (fill in — what was the first visual?)
- Revised: (fill in — yes/no, what changed?)

## Proof
- Screenshots: {metrics['screenshot_count']}
- Demo videos: {metrics['demo_video_count']}
- Fitness blockers resolved: (fill in — how many MISMATCH/MISSING were resolved?)
- Strongest proof moment: (fill in — which beat had the most convincing proof?)

## Pacing
- Beats: {metrics['beat_count']}
- Visual changes: every {metrics['visual_freq']}s average
- Avatar on-screen: {metrics['avatar_pct']}%
- QA pacing flags: {metrics['qa_verdict']} ({metrics['qa_blockers']} blockers, {metrics['qa_warnings']} warnings)

## Technical
- Encoding issues: (fill in — none / list)
- Zoom approach: (fill in — auto / manual / vision-estimated)
- SFX count: {metrics['sfx_count']}

## Repeat
(fill in — what worked well and should be repeated)

## Improve
(fill in — what would be done differently next time)
"""

    output_dir = project_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "learnings.md"
    out_path.write_text(md.strip() + "\n", encoding="utf-8")

    return str(out_path)


# ── Learning comparison ─────────────────────────────────────────────────────

def compare_learnings(project_dir: Path) -> str:
    """Find similar completed projects and show their learnings."""
    project_dir = Path(project_dir)
    project = _load_json(project_dir / "project.json")
    my_style = project.get("style", "cinematic-presenter")
    my_dur = project.get("duration_s") or 0

    projects_root = project_dir.parent
    results: list[tuple[int, str, str]] = []

    for sibling in sorted(projects_root.iterdir()):
        if not sibling.is_dir() or sibling == project_dir:
            continue
        learnings_path = sibling / "output" / "learnings.md"
        if not learnings_path.exists():
            continue

        sib_pj = _load_json(sibling / "project.json")
        sib_style = sib_pj.get("style", "cinematic-presenter")
        sib_dur = sib_pj.get("duration_s") or 0

        # Score relevance: same style = +2, similar duration (±15s) = +1
        score = 0
        if sib_style == my_style:
            score += 2
        if my_dur > 0 and abs(sib_dur - my_dur) < 15:
            score += 1

        # Read first 15 lines as preview
        lines = learnings_path.read_text(encoding="utf-8").split("\n")[:15]
        preview = "\n".join(lines)
        results.append((score, sibling.name, preview))

    # Sort by relevance score descending
    results.sort(key=lambda r: r[0], reverse=True)

    if not results:
        return "No completed projects with learnings found."

    lines = [f"Found {len(results)} project(s) with learnings. Top matches:\n"]
    for score, name, preview in results[:3]:
        lines.append(f"── {name} (relevance: {score}) ──")
        lines.append(preview)
        lines.append("")

    return "\n".join(lines)


# ── CLI ─────────────────────────────────────────────────────────────────────

USAGE = """\
Usage:
  python -m lib.learn capture <project-dir>   Generate learnings.md from project artifacts
  python -m lib.learn compare <project-dir>   Find similar projects and show their learnings
"""


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 2:
        print(USAGE)
        sys.exit(1)

    cmd = args[0]
    project_dir = Path(args[1])

    if not project_dir.exists():
        print(f"ERROR: Directory not found: {project_dir}")
        sys.exit(1)

    if cmd == "capture":
        out_path = capture_learnings(project_dir)
        print(f"Learnings written to: {out_path}")
        sys.exit(0)

    elif cmd == "compare":
        result = compare_learnings(project_dir)
        print(result)
        sys.exit(0)

    else:
        print(f"Unknown command: {cmd}")
        print(USAGE)
        sys.exit(1)


if __name__ == "__main__":
    main()
