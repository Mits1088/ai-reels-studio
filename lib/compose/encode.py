"""
Video encoding — generates ffmpeg commands for final render.

This module does NOT require ffmpeg to be installed at import time.
It builds the command spec so that encoding can be done when ffmpeg is available.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from . import layout as L


class EncoderNotReady(RuntimeError):
    pass


def check_ffmpeg() -> str | None:
    """Return ffmpeg path if available, None otherwise."""
    return shutil.which("ffmpeg")


def build_encode_command(
    frame_dir: Path,
    audio_path: Path,
    output_path: Path,
    *,
    fps: int = L.FPS,
    music_path: Path | None = None,
    music_volume: float = 0.15,
) -> list[str]:
    """
    Build an ffmpeg command to encode frames + audio into MP4.

    Args:
        frame_dir: Directory containing numbered frames (frame_0001.png, ...)
        audio_path: Voice audio file
        output_path: Output MP4 path
        fps: Frames per second
        music_path: Optional background music file
        music_volume: Music volume (0-1)

    Returns:
        Command as list of strings ready for subprocess.run()
    """
    ffmpeg = check_ffmpeg()
    if not ffmpeg:
        raise EncoderNotReady(
            "ffmpeg not found. Install ffmpeg to encode video. "
            "Frame sequence is ready at: {frame_dir}"
        )

    cmd = [ffmpeg]

    # Input: frame sequence
    cmd.extend(["-framerate", str(fps)])
    cmd.extend(["-i", str(frame_dir / "frame_%04d.png")])

    # Input: voice audio
    cmd.extend(["-i", str(audio_path)])

    # Input: optional music
    if music_path:
        cmd.extend(["-i", str(music_path)])

    # Video encoding
    cmd.extend([
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "18",
        "-r", str(fps),
    ])

    # Audio mixing
    if music_path:
        # Mix voice (full volume) + music (reduced volume)
        cmd.extend([
            "-filter_complex",
            f"[1:a]volume=1.0[voice];[2:a]volume={music_volume}[music];[voice][music]amix=inputs=2:duration=first[out]",
            "-map", "0:v",
            "-map", "[out]",
        ])
    else:
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])

    # Output
    cmd.extend([
        "-movflags", "+faststart",
        "-y",
        str(output_path),
    ])

    return cmd


def build_encode_spec(
    project_dir: Path,
    timeline: dict,
) -> dict:
    """
    Build a complete encoding specification for the project.

    Returns a dict that documents exactly how to encode the reel,
    even if ffmpeg isn't available yet.
    """
    lanes = timeline.get("lanes", {})
    music_entries = lanes.get("music", [])

    spec = {
        "resolution": f"{L.WIDTH}x{L.HEIGHT}",
        "fps": L.FPS,
        "codec_video": "H.264",
        "codec_audio": "AAC",
        "format": "MP4",
        "duration": timeline.get("total_duration"),
        "voice_audio": str(project_dir / "audio" / "voice.wav"),
        "frame_dir": str(project_dir / "output" / "frames"),
        "output": str(project_dir / "output" / "reel.mp4"),
        "music": None,
        "ffmpeg_available": check_ffmpeg() is not None,
    }

    if music_entries:
        spec["music"] = {
            "file": str(project_dir / "assets" / music_entries[0]["asset"]),
            "volume": music_entries[0].get("volume", 0.15),
        }

    return spec
