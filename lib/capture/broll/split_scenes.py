"""
Step 1: Split a continuous b-roll video into individual scenes.

Uses PySceneDetect for content-aware scene detection, then FFmpeg to cut
each scene into a separate clip. Also extracts a representative thumbnail
from each scene for classification.

Usage:
    python -m lib.capture.broll.split_scenes <video_path> <output_dir> [--threshold 27]

Output:
    <output_dir>/
        scenes/
            scene_001.mp4
            scene_002.mp4
            ...
        thumbnails/
            scene_001.jpg
            scene_002.jpg
            ...
        scene_list.json   ← metadata for each scene
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector


def split_scenes(video_path: str, output_dir: str, threshold: float = 27.0,
                 min_scene_len: float = 1.0) -> list[dict]:
    """Detect and split scenes from a video file.

    Args:
        video_path: Path to the source b-roll video
        output_dir: Directory to write scene clips and thumbnails
        threshold: Content detection threshold (lower = more sensitive, default 27)
        min_scene_len: Minimum scene length in seconds (default 1.0)

    Returns:
        List of scene metadata dicts
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)

    if not video_path.exists():
        print(f"Error: Video not found: {video_path}")
        sys.exit(1)

    scenes_dir = output_dir / "scenes"
    thumbs_dir = output_dir / "thumbnails"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    thumbs_dir.mkdir(parents=True, exist_ok=True)

    # ── Detect scenes ──
    print(f"Detecting scenes in {video_path.name} (threshold={threshold})...")
    video = open_video(str(video_path))
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(
        threshold=threshold,
        min_scene_len=int(min_scene_len * video.frame_rate),
    ))
    scene_manager.detect_scenes(video)
    scene_list = scene_manager.get_scene_list()

    if not scene_list:
        print("No scene cuts detected — treating entire video as one scene.")
        # Get video duration via ffprobe
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(video_path)],
            capture_output=True, text=True
        )
        duration = float(result.stdout.strip())
        scene_list = [(0.0, duration)]

    print(f"Found {len(scene_list)} scenes.")

    # ── Cut each scene + extract thumbnail ──
    scenes_meta = []

    for i, scene in enumerate(scene_list):
        idx = f"{i + 1:03d}"

        # Handle both FrameTimecode objects and raw tuples
        if hasattr(scene[0], 'get_seconds'):
            start_sec = scene[0].get_seconds()
            end_sec = scene[1].get_seconds()
        else:
            start_sec = float(scene[0])
            end_sec = float(scene[1])

        duration = end_sec - start_sec
        scene_file = scenes_dir / f"scene_{idx}.mp4"
        thumb_file = thumbs_dir / f"scene_{idx}.jpg"

        # Cut scene with FFmpeg (re-encode for clean cuts)
        print(f"  Cutting scene {idx}: {start_sec:.2f}s – {end_sec:.2f}s ({duration:.2f}s)")
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(start_sec), "-i", str(video_path),
            "-t", str(duration), "-c:v", "libx264", "-preset", "fast",
            "-crf", "18", "-an", str(scene_file),
        ], capture_output=True, check=True)

        # Extract thumbnail from middle of scene
        mid_time = start_sec + duration / 2
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(mid_time), "-i", str(video_path),
            "-frames:v", "1", "-q:v", "2", str(thumb_file),
        ], capture_output=True, check=True)

        scenes_meta.append({
            "id": f"scene_{idx}",
            "index": i + 1,
            "start": round(start_sec, 3),
            "end": round(end_sec, 3),
            "duration": round(duration, 3),
            "file": f"scenes/scene_{idx}.mp4",
            "thumbnail": f"thumbnails/scene_{idx}.jpg",
            "labels": [],       # filled by classify step
            "embedding": None,  # filled by classify step
        })

    # ── Write metadata ──
    meta_path = output_dir / "scene_list.json"
    with open(meta_path, "w") as f:
        json.dump({
            "source": str(video_path),
            "total_scenes": len(scenes_meta),
            "threshold": threshold,
            "scenes": scenes_meta,
        }, f, indent=2)

    print(f"\nDone. {len(scenes_meta)} scenes written to {output_dir}")
    print(f"Metadata: {meta_path}")
    return scenes_meta


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split b-roll video into scenes")
    parser.add_argument("video", help="Path to the source b-roll video")
    parser.add_argument("output_dir", help="Output directory for scenes and thumbnails")
    parser.add_argument("--threshold", type=float, default=27.0,
                        help="Scene detection threshold (lower=more splits, default 27)")
    parser.add_argument("--min-scene-len", type=float, default=1.0,
                        help="Minimum scene length in seconds (default 1.0)")
    args = parser.parse_args()
    split_scenes(args.video, args.output_dir, args.threshold, args.min_scene_len)
