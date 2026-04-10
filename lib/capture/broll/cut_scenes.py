"""
Step 4: Cut approved b-roll scenes and copy to remotion/public/.

Reads broll_matches.json, cuts each approved scene to the exact duration
needed for its beat, and copies the output to remotion/public/ with the
project naming convention.

Usage:
    python -m lib.capture.broll.cut_scenes <broll_dir> <project_dir> [--pad 0.5]

Input:
    <project_dir>/output/broll_matches.json (with approved: true entries)
    <broll_dir>/scenes/*.mp4

Output:
    remotion/public/broll_<description>_<beat-id>.mp4
    Updates output/timeline.json broll lane
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def slugify(text: str, max_len: int = 30) -> str:
    """Convert text to a filename-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text)
    return text[:max_len].rstrip("-")


def cut_scenes(broll_dir: str, project_dir: str, pad: float = 0.5) -> list[dict]:
    """Cut approved b-roll scenes and prepare for Remotion.

    Args:
        broll_dir: Directory with scenes/ from split_scenes
        project_dir: Project directory with output/broll_matches.json
        pad: Extra seconds to add at start/end of cuts (default 0.5)

    Returns:
        List of broll timeline entries ready for timeline.json
    """
    broll_dir = Path(broll_dir)
    project_dir = Path(project_dir)
    remotion_public = Path("D:/Reel generation/remotion/public")

    matches_path = project_dir / "output" / "broll_matches.json"
    if not matches_path.exists():
        print(f"Error: broll_matches.json not found at {matches_path}")
        print("Run match_scenes first.")
        sys.exit(1)

    with open(matches_path) as f:
        match_data = json.load(f)

    matches = match_data.get("matches", [])
    approved = [m for m in matches if m.get("approved", False)]

    if not approved:
        print("No approved matches found. Set 'approved': true in broll_matches.json first.")
        print(f"  File: {matches_path}")
        return []

    print(f"Cutting {len(approved)} approved b-roll scenes...")
    broll_entries = []

    for match in approved:
        beat_id = match["beat_id"]
        best = match["best_match"]
        scene_file = broll_dir / best["file"]

        if not scene_file.exists():
            print(f"  Warning: Scene file missing: {scene_file}")
            continue

        # Calculate needed duration from beat timing
        beat_start = match.get("beat_start", 0)
        beat_end = match.get("beat_end", beat_start + best["duration"])
        needed_duration = beat_end - beat_start

        # Scene might be longer than needed — trim to fit
        scene_duration = best.get("duration", needed_duration)
        cut_duration = min(scene_duration, needed_duration + pad)

        # Output filename
        desc_slug = slugify(best.get("description", beat_id)[:40])
        out_name = f"broll_{desc_slug}_{beat_id}.mp4"
        out_path = remotion_public / out_name

        print(f"  {beat_id} -> {out_name} ({cut_duration:.2f}s)")

        # Cut with FFmpeg
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(scene_file),
            "-t", str(cut_duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-an",  # strip audio — narration comes from separate track
            str(out_path),
        ], capture_output=True, check=True)

        # Build timeline entry
        broll_entry = {
            "beat_id": beat_id,
            "start": beat_start,
            "end": beat_end,
            "asset": out_name,
            "transition_preset": {
                "enter": "fade",
                "exit": "fade",
                "enterDur": 4,
                "exitDur": 3,
                "kenBurns": False,
            },
            "notes": f"Auto-matched from NotebookLM b-roll: {best.get('description', '')}",
        }
        broll_entries.append(broll_entry)

    # ── Write broll entries for easy pasting into timeline ──
    broll_output_path = project_dir / "output" / "broll_entries.json"
    with open(broll_output_path, "w") as f:
        json.dump(broll_entries, f, indent=2)

    print(f"\nDone. {len(broll_entries)} clips cut to remotion/public/")
    print(f"Timeline entries: {broll_output_path}")
    print("\nNext: merge these into output/timeline.json broll lane, then preview in Remotion.")
    return broll_entries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cut approved b-roll scenes for Remotion")
    parser.add_argument("broll_dir", help="Directory with scenes/ from split_scenes")
    parser.add_argument("project_dir", help="Project directory")
    parser.add_argument("--pad", type=float, default=0.5,
                        help="Extra seconds padding on cuts (default 0.5)")
    args = parser.parse_args()
    cut_scenes(args.broll_dir, args.project_dir, args.pad)
