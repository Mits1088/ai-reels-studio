"""
Beat-by-beat preview frame renderer.

Reads `output/timeline.json` for a project, finds the midpoint of every
editorial beat (or every distinct overlay/demo entry), and renders one
preview frame for each via `npx remotion still`. Outputs go to
`projects/<slug>/output/preview/`.

The point: instead of rendering at random timestamps after the entire
timeline is built, render at every editorial beat boundary so visual
issues (z-index, color, layout, gaps) are caught at the beat where they
occur, not in a chaotic all-at-once preview pass at the end.

Usage:
    python -m lib.preview_beats projects/claude-managed-agents
    python -m lib.preview_beats projects/claude-managed-agents --beats 1,3,5
    python -m lib.preview_beats projects/claude-managed-agents --frames 0,135,450,1770

Options:
    --composition NAME        Composition ID to render (default: ReelComposition)
    --beats LIST              Comma-separated beat indices to render (default: all)
    --frames LIST             Render specific frame numbers instead of beat midpoints
    --extra LIST              Comma-separated extra timestamps in seconds
    --include-overlays        Also render midpoint of every overlay entry
    --remotion-dir PATH       Override path to the remotion project
    --skip-existing           Don't re-render frames that already exist
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_FPS = 30
DEFAULT_COMPOSITION = "ReelComposition"


def _slug(text: str) -> str:
    """Sanitize a label into a filename fragment."""
    import re
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s[:48] or "frame"


def collect_beats(timeline: dict) -> list[tuple[int, float, str]]:
    """Return list of (frame, t_seconds, label) for every editorial beat.

    Looks at `lanes.avatar` first (each entry is one editorial unit),
    then any `lanes.demo` entries that don't share a beat_id with avatar,
    then standalone overlay beats with unique beat_ids.
    """
    fps = timeline.get("fps", DEFAULT_FPS)
    seen_beats: set[str] = set()
    out: list[tuple[int, float, str]] = []

    def add_entry(entry: dict, lane: str) -> None:
        beat_id = entry.get("beat_id") or f"{lane}-{entry.get('start', 0):.2f}"
        if beat_id in seen_beats:
            return
        seen_beats.add(beat_id)
        start = float(entry.get("start", 0))
        end = float(entry.get("end", start))
        mid = (start + end) / 2
        frame = int(round(mid * fps))
        label = entry.get("label") or entry.get("text") or beat_id
        out.append((frame, mid, f"{beat_id}-{_slug(label)}"))

    for entry in timeline.get("lanes", {}).get("avatar", []):
        add_entry(entry, "avatar")
    for entry in timeline.get("lanes", {}).get("demo", []):
        add_entry(entry, "demo")
    for entry in timeline.get("lanes", {}).get("broll", []) or []:
        add_entry(entry, "broll")

    out.sort(key=lambda x: x[0])
    return out


def collect_overlay_beats(timeline: dict) -> list[tuple[int, float, str]]:
    """Return one frame per overlay entry, midpoint of its time range."""
    fps = timeline.get("fps", DEFAULT_FPS)
    out: list[tuple[int, float, str]] = []
    for i, entry in enumerate(timeline.get("lanes", {}).get("overlays", []) or []):
        start = float(entry.get("start", 0))
        end = float(entry.get("end", start))
        mid = (start + end) / 2
        frame = int(round(mid * fps))
        label = entry.get("type", f"overlay-{i}")
        beat_id = entry.get("beat_id") or f"ov-{i}"
        out.append((frame, mid, f"{beat_id}-{_slug(label)}"))
    return out


def render_frames(
    frames: list[tuple[int, float, str]],
    project_dir: Path,
    remotion_dir: Path,
    composition: str,
    skip_existing: bool = False,
) -> tuple[int, int]:
    """Render the requested frames via `npx remotion still`. Returns (ok, fail)."""
    out_dir = project_dir / "output" / "preview"
    out_dir.mkdir(parents=True, exist_ok=True)
    rel_out = Path("..") / out_dir.relative_to(project_dir.parent)

    ok, fail = 0, 0
    for frame_num, t_sec, label in frames:
        filename = f"frame-{frame_num:04d}-{label}.png"
        target = out_dir / filename

        if skip_existing and target.exists():
            print(f"  ⊙ skip {filename} (exists)")
            ok += 1
            continue

        rel_target = rel_out / filename
        cmd = [
            "npx", "remotion", "still",
            composition,
            str(rel_target),
            f"--frame={frame_num}",
            "--log=error",
        ]
        proc = subprocess.run(
            cmd,
            cwd=str(remotion_dir),
            capture_output=True,
            text=True,
            shell=(sys.platform == "win32"),
        )
        if proc.returncode != 0:
            print(f"  ✗ {filename} (frame {frame_num}, t={t_sec:.2f}s)")
            print(f"    STDERR: {proc.stderr[-300:]}")
            fail += 1
        else:
            print(f"  ✓ {filename} (frame {frame_num}, t={t_sec:.2f}s)")
            ok += 1
    return ok, fail


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m lib.preview_beats",
        description="Render one preview frame per editorial beat",
    )
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--composition", default=DEFAULT_COMPOSITION)
    parser.add_argument("--beats", help="Comma-separated beat indices (1-based)")
    parser.add_argument("--frames", help="Comma-separated absolute frame numbers")
    parser.add_argument("--extra", help="Comma-separated extra timestamps in seconds")
    parser.add_argument("--include-overlays", action="store_true",
                        help="Also render every overlay entry midpoint")
    parser.add_argument("--remotion-dir", type=Path, default=None)
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args(argv)

    project_dir = args.project_dir.resolve()
    if not project_dir.exists():
        print(f"  ! project not found: {project_dir}")
        return 1

    # Resolve remotion dir — default to <repo>/remotion (sibling of projects/)
    remotion_dir = args.remotion_dir
    if remotion_dir is None:
        # Walk up from project_dir until we find remotion/
        cur = project_dir
        for _ in range(5):
            cur = cur.parent
            if (cur / "remotion").exists():
                remotion_dir = cur / "remotion"
                break
    if remotion_dir is None or not remotion_dir.exists():
        print("  ! could not locate remotion/ directory — pass --remotion-dir")
        return 1

    # Load timeline
    timeline_path = project_dir / "output" / "timeline.json"
    if not timeline_path.exists():
        timeline_path = remotion_dir / "public" / "timeline.json"
    if not timeline_path.exists():
        print(f"  ! timeline.json not found in {project_dir}/output/ or {remotion_dir}/public/")
        return 1
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))

    fps = timeline.get("fps", DEFAULT_FPS)

    # Build the frame list
    if args.frames:
        frames = []
        for f in args.frames.split(","):
            f = int(f.strip())
            frames.append((f, f / fps, f"manual-f{f}"))
    else:
        frames = collect_beats(timeline)
        if args.include_overlays:
            frames.extend(collect_overlay_beats(timeline))
        if args.beats:
            indices = {int(b.strip()) - 1 for b in args.beats.split(",")}
            frames = [f for i, f in enumerate(frames) if i in indices]

    if args.extra:
        for t in args.extra.split(","):
            t_sec = float(t.strip())
            frames.append((int(round(t_sec * fps)), t_sec, f"extra-t{t_sec}"))

    # Dedupe by frame number, keep the first label
    seen = set()
    deduped = []
    for f in sorted(frames, key=lambda x: x[0]):
        if f[0] not in seen:
            seen.add(f[0])
            deduped.append(f)
    frames = deduped

    if not frames:
        print("  ! no frames to render")
        return 1

    print(f"Beat-by-beat preview render: {project_dir.name}")
    print(f"  composition: {args.composition}")
    print(f"  total frames: {len(frames)}")
    print(f"  output: {project_dir / 'output' / 'preview'}")
    print()

    ok, fail = render_frames(
        frames,
        project_dir=project_dir,
        remotion_dir=remotion_dir,
        composition=args.composition,
        skip_existing=args.skip_existing,
    )

    print()
    print(f"Done: {ok} ok, {fail} failed")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
