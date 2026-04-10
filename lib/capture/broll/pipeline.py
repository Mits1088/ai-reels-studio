"""
B-Roll Pipeline — Run all 4 steps in sequence or individually.

Usage:
    # Full pipeline (stops after match for review)
    python -m lib.capture.broll.pipeline <video_path> <project_dir> --api-key KEY

    # Individual steps
    python -m lib.capture.broll.split_scenes <video> <broll_dir>
    python -m lib.capture.broll.classify_scenes <broll_dir>
    python -m lib.capture.broll.match_scenes <broll_dir> <project_dir>
    python -m lib.capture.broll.cut_scenes <broll_dir> <project_dir>

Pipeline flow:
    1. split_scenes   → PySceneDetect + FFmpeg → individual scene clips + thumbnails
    2. classify_scenes → Gemini Vision + Embedding → labels, descriptions, embeddings
    3. match_scenes    → Cosine similarity → best b-roll per script beat
    ── STOP: Review broll_matches.json, approve matches ──
    4. cut_scenes      → FFmpeg → trimmed clips in remotion/public/
"""

import argparse
import sys
from pathlib import Path

from lib.capture.broll.split_scenes import split_scenes
from lib.capture.broll.classify_scenes import classify_scenes
from lib.capture.broll.match_scenes import match_scenes
from lib.capture.broll.cut_scenes import cut_scenes


def run_pipeline(video_path: str, project_dir: str, api_key: str | None = None,
                 threshold: float = 27.0, top_k: int = 3,
                 cut: bool = False) -> None:
    """Run the full b-roll pipeline.

    By default, stops after matching (step 3) for human review.
    Pass --cut to also run step 4 (requires approved matches).
    """
    project_dir = Path(project_dir)
    broll_dir = project_dir / "broll_scenes"

    print("=" * 60)
    print("B-ROLL PIPELINE")
    print("=" * 60)

    # Step 1: Split
    print("\n─── STEP 1: Split scenes ───")
    split_scenes(video_path, str(broll_dir), threshold=threshold)

    # Step 2: Classify
    print("\n─── STEP 2: Classify scenes ───")
    classify_scenes(str(broll_dir), api_key=api_key)

    # Step 3: Match
    print("\n─── STEP 3: Match to script beats ───")
    matches = match_scenes(str(broll_dir), str(project_dir), top_k=top_k, api_key=api_key)

    if not cut:
        print("\n" + "=" * 60)
        print("PIPELINE PAUSED — Review matches before cutting")
        print("=" * 60)
        print(f"\n  1. Open: {project_dir / 'output' / 'broll_matches.json'}")
        print("  2. Review each match — check description, similarity score")
        print("  3. Set \"approved\": true for matches you want to use")
        print("  4. Re-run with --cut flag to cut approved scenes:")
        print(f"     python -m lib.capture.broll.pipeline {video_path} {project_dir} --cut")
        return

    # Step 4: Cut (only if --cut flag)
    print("\n─── STEP 4: Cut approved scenes ───")
    cut_scenes(str(broll_dir), str(project_dir))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="B-roll processing pipeline")
    parser.add_argument("video", help="Path to NotebookLM b-roll video")
    parser.add_argument("project_dir", help="Project directory")
    parser.add_argument("--api-key", help="Gemini API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--threshold", type=float, default=27.0,
                        help="Scene detection threshold (default 27)")
    parser.add_argument("--top-k", type=int, default=3,
                        help="Candidate matches per beat (default 3)")
    parser.add_argument("--cut", action="store_true",
                        help="Also run step 4 (cut approved scenes)")
    args = parser.parse_args()
    run_pipeline(args.video, args.project_dir, args.api_key,
                 args.threshold, args.top_k, args.cut)
