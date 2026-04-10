"""
Reel Preprocessing Pipeline

Takes a reference reel video and produces structured data for training examples:
1. Extract audio + Whisper transcription (word-level timestamps)
2. Detect scene cuts (ffmpeg scene filter)
3. Extract keyframes at scene cuts
4. Extract uniform frames (2fps) for visual analysis
5. Output structured JSON skeleton ready for manual annotation

Usage:
    python training/preprocess-reel.py --video "training/references/Video by creator.mp4" --creator "creator-name"

Output:
    training/references/{creator}-processed/
        audio.wav           — extracted audio (16kHz mono)
        audio.json          — Whisper transcription with word timestamps
        transcript.txt      — clean transcript with word timecodes
        scene-cuts.json     — detected scene cuts with timestamps
        cuts/cut_NNN.jpg    — keyframe at each scene cut
        frames/f_NNNN.jpg   — uniform 2fps frames for visual analysis
        skeleton.json       — training example skeleton (needs manual annotation)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def run(cmd, check=True, capture=True, timeout=300):
    """Run a shell command and return stdout."""
    result = subprocess.run(
        cmd, shell=True, capture_output=capture, text=True, timeout=timeout
    )
    if check and result.returncode != 0:
        print(f"FAILED: {cmd}")
        print(result.stderr)
        sys.exit(1)
    return result.stdout.strip() if capture else None


def extract_audio(video_path, out_dir):
    """Extract 16kHz mono WAV for Whisper."""
    audio_path = out_dir / "audio.wav"
    run(
        f'ffmpeg -i "{video_path}" -vn -acodec pcm_s16le -ar 16000 -ac 1 "{audio_path}" -y'
    )
    print(f"  Audio extracted: {audio_path}")
    return audio_path


def transcribe(audio_path, out_dir):
    """Run Whisper with word-level timestamps."""
    run(
        f'python -m whisper "{audio_path}" --model small --language en '
        f'--word_timestamps True --output_format json --output_dir "{out_dir}"',
        timeout=600,
    )

    json_path = out_dir / "audio.json"
    with open(json_path) as f:
        data = json.load(f)

    # Extract word-level data
    words = []
    for seg in data["segments"]:
        for w in seg.get("words", []):
            words.append(
                {
                    "word": w["word"].strip(),
                    "start": round(w["start"], 2),
                    "end": round(w["end"], 2),
                }
            )

    # Write clean transcript
    transcript_path = out_dir / "transcript.txt"
    with open(transcript_path, "w") as f:
        for w in words:
            f.write(f"{w['start']:6.2f} - {w['end']:6.2f}  {w['word']}\n")

    print(f"  Transcription: {len(words)} words")
    return words


def detect_scene_cuts(video_path, out_dir, threshold=0.15):
    """Detect scene cuts using ffmpeg scene filter."""
    result = run(
        f'ffmpeg -i "{video_path}" -vf "select=\'gt(scene,{threshold})\',showinfo" '
        f"-vsync vfr -f null - 2>&1",
        check=False,
    )

    cuts = []
    for line in result.split("\n"):
        m = re.search(r"pts_time:(\d+\.\d+)", line)
        if m:
            cuts.append(round(float(m.group(1)), 3))

    # Also extract keyframes at cut points
    cuts_dir = out_dir / "cuts"
    cuts_dir.mkdir(exist_ok=True)
    run(
        f"ffmpeg -i \"{video_path}\" -vf \"select='gt(scene,{threshold})'\" "
        f'-vsync vfr "{cuts_dir}/cut_%03d.jpg" -y'
    )

    cuts_data = [{"index": i, "time": t} for i, t in enumerate(cuts)]

    cuts_path = out_dir / "scene-cuts.json"
    with open(cuts_path, "w") as f:
        json.dump(cuts_data, f, indent=2)

    print(f"  Scene cuts: {len(cuts)} detected at threshold {threshold}")
    return cuts


def extract_frames(video_path, out_dir, fps=2):
    """Extract uniform frames at given fps."""
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(exist_ok=True)
    run(
        f'ffmpeg -i "{video_path}" -vf "fps={fps}" -q:v 2 "{frames_dir}/f_%04d.jpg" -y'
    )
    frame_count = len(list(frames_dir.glob("*.jpg")))
    print(f"  Frames: {frame_count} at {fps}fps")
    return frame_count


def get_video_info(video_path):
    """Get video metadata via ffprobe."""
    duration = float(
        run(
            f'ffprobe -v quiet -show_entries format=duration -of csv=p=0 "{video_path}"'
        )
    )
    resolution = run(
        f"ffprobe -v quiet -select_streams v:0 "
        f'-show_entries stream=width,height -of csv=p=0 "{video_path}"'
    )
    fps_raw = run(
        f"ffprobe -v quiet -select_streams v:0 "
        f'-show_entries stream=r_frame_rate -of csv=p=0 "{video_path}"'
    )

    w, h = resolution.split(",")
    fps_parts = fps_raw.split("/")
    fps = round(int(fps_parts[0]) / int(fps_parts[1]), 2)

    return {
        "duration_s": round(duration, 2),
        "resolution": f"{w}x{h}",
        "fps": fps,
        "aspect_ratio": "9:16" if int(h) > int(w) else "16:9",
    }


def build_skeleton(video_path, creator, words, scene_cuts, video_info):
    """Build a training example skeleton ready for manual annotation."""
    # Group words into segments based on scene cuts
    segments = []
    cut_times = [0.0] + scene_cuts + [video_info["duration_s"]]

    for i in range(len(cut_times) - 1):
        start = cut_times[i]
        end = cut_times[i + 1]
        seg_words = [w for w in words if w["start"] >= start and w["start"] < end]
        narration = " ".join(w["word"] for w in seg_words) if seg_words else ""

        segments.append(
            {
                "id": f"seg-{i + 1:02d}",
                "time": f"{start:.2f}–{end:.2f}",
                "duration_s": round(end - start, 2),
                "template": "TODO — classify from keyframe",
                "narration": narration,
                "visual": "TODO — describe from keyframe analysis",
                "caption": "TODO — extract from visual or derive from narration",
                "avatar": "TODO — visible/hidden/peek",
                "proof_class": "TODO — existence/breadth/process/output/authority/cta/null",
            }
        )

    skeleton = {
        "meta": {
            "source_video": str(video_path),
            "creator": creator,
            "duration_s": video_info["duration_s"],
            "fps": video_info["fps"],
            "resolution": video_info["resolution"],
            "aspect_ratio": video_info["aspect_ratio"],
            "preprocessing": {
                "transcription": "whisper-small, word_timestamps=true",
                "scene_detection": "ffmpeg select gt(scene,0.15)",
                "frame_extraction": "2fps uniform + scene-cut keyframes",
                "visual_analysis": "PENDING — requires manual frame-by-frame classification",
            },
        },
        "prompt": {
            "topic": "TODO — one-line topic summary",
            "audience": "TODO — target viewer profile",
            "product": "TODO — product/brand name",
            "source_material": "TODO — what source assets exist",
            "style_intent": "TODO — proof-escalation / feature-demo / listicle / story",
            "target_duration_s": round(video_info["duration_s"]),
            "hook_direction": "TODO — hook pattern used",
        },
        "completion": {
            "hook": {
                "text": " ".join(
                    w["word"] for w in words if w["end"] <= (scene_cuts[0] if scene_cuts else 5.0)
                ),
                "duration_s": round(scene_cuts[0] if scene_cuts else 5.0, 2),
                "pattern": "TODO — news-event / result-first / cost-tension / secret-knowledge",
                "first_frame_visual": "TODO — describe first frame",
            },
            "script": " ".join(w["word"] for w in words),
            "proof_escalation": ["TODO — list proof types in order they appear"],
            "segments": segments,
            "template_sequence": [s["template"] for s in segments],
            "scene_cuts": [
                {"time": t, "from": "TODO", "to": "TODO"} for t in scene_cuts
            ],
            "caption_data": {
                "style": {
                    "font_family": "TODO",
                    "case": "TODO — ALL_CAPS / Title_Case / lowercase",
                    "approx_size_pt": "TODO",
                    "color": "TODO",
                    "outline": "TODO",
                    "position_y_pct": "TODO",
                    "max_words_per_chunk": "TODO",
                },
                "emphasis_rules": [],
                "suppression_zones": [],
                "chunks": "TODO — extract from visual analysis",
            },
            "rhythm_data": {
                "total_visual_states": len(segments),
                "avg_visual_change_s": round(
                    video_info["duration_s"] / max(len(segments), 1), 1
                ),
                "scene_cuts_detected": len(scene_cuts),
                "word_count": len(words),
                "words_per_second": round(
                    len(words) / video_info["duration_s"], 1
                ),
            },
            "cta": {
                "type": "TODO — comment-for-dm / follow / link-in-bio",
                "action_word": "TODO",
                "offer": "TODO",
            },
        },
        "style_card": {
            "id": "TODO",
            "name": "TODO",
            "description": "TODO",
            "template_registry": [],
            "rules": {},
        },
    }

    return skeleton


def main():
    parser = argparse.ArgumentParser(description="Preprocess a reference reel for training data")
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--creator", required=True, help="Creator handle/name")
    parser.add_argument("--threshold", type=float, default=0.15, help="Scene cut threshold")
    parser.add_argument("--fps", type=int, default=2, help="Frame extraction rate")
    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Video not found: {video_path}")
        sys.exit(1)

    # Create output directory
    out_dir = video_path.parent / f"{args.creator}-processed"
    out_dir.mkdir(exist_ok=True)

    print(f"Preprocessing: {video_path}")
    print(f"Output: {out_dir}")
    print()

    # Step 1: Video info
    print("1. Video info...")
    info = get_video_info(video_path)
    print(f"  {info['duration_s']}s, {info['resolution']}, {info['fps']}fps, {info['aspect_ratio']}")

    # Step 2: Extract audio
    print("2. Extracting audio...")
    audio_path = extract_audio(video_path, out_dir)

    # Step 3: Transcribe
    print("3. Transcribing (Whisper small)...")
    words = transcribe(audio_path, out_dir)

    # Step 4: Scene cuts
    print("4. Detecting scene cuts...")
    cuts = detect_scene_cuts(video_path, out_dir, args.threshold)

    # Step 5: Extract frames
    print("5. Extracting frames...")
    frame_count = extract_frames(video_path, out_dir, args.fps)

    # Step 6: Build skeleton
    print("6. Building training example skeleton...")
    skeleton = build_skeleton(video_path, args.creator, words, cuts, info)

    skeleton_path = out_dir / "skeleton.json"
    with open(skeleton_path, "w") as f:
        json.dump(skeleton, f, indent=2)

    print(f"  Skeleton: {skeleton_path}")
    print()
    print("DONE. Next steps:")
    print(f"  1. Open {out_dir / 'frames'} and classify each segment visually")
    print(f"  2. Fill in TODO fields in {skeleton_path}")
    print(f"  3. Copy to training-example.json when complete")
    print()
    print(f"  Segments detected: {len(skeleton['completion']['segments'])}")
    print(f"  Scene cuts: {len(cuts)}")
    print(f"  Words transcribed: {len(words)}")
    print(f"  Frames extracted: {frame_count}")


if __name__ == "__main__":
    main()
