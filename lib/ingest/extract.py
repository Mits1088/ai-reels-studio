"""
Audio extraction from video files.

Two backends:
  1. FfmpegPythonExtractor  — uses ffmpeg-python (default, preferred)
  2. FfmpegCLIExtractor     — uses subprocess + raw ffmpeg CLI

Both produce identical output: mono 16kHz WAV from any video/audio input.
Switch backends by passing a different extractor to pipeline functions.
"""

from __future__ import annotations

import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path


# ── Errors ──────────────────────────────────────────────────────────────────

class FfmpegNotFoundError(RuntimeError):
    pass


class ExtractionError(RuntimeError):
    pass


# ── Abstract backend ────────────────────────────────────────────────────────

class AudioExtractor(ABC):
    """Interface for audio extraction backends."""

    @abstractmethod
    def extract(self, input_path: Path, output_path: Path,
                sample_rate: int = 16000) -> Path:
        """Extract audio from input file to WAV.

        Args:
            input_path: Video or audio file to extract from.
            output_path: Destination WAV path.
            sample_rate: Target sample rate in Hz.

        Returns:
            Path to the written WAV file.
        """

    @abstractmethod
    def probe_duration(self, file_path: Path) -> float:
        """Return duration of a media file in seconds."""


# ── ffmpeg-python backend ───────────────────────────────────────────────────

class FfmpegPythonExtractor(AudioExtractor):
    """Backend using the ffmpeg-python library."""

    def extract(self, input_path: Path, output_path: Path,
                sample_rate: int = 16000) -> Path:
        if not input_path.exists():
            raise FileNotFoundError(f"Input not found: {input_path}")

        try:
            import ffmpeg as ffmpeg_lib
        except ImportError:
            raise FfmpegNotFoundError(
                "ffmpeg-python is not installed. Run: pip install ffmpeg-python"
            )

        _ensure_ffmpeg_binary()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            (
                ffmpeg_lib
                .input(str(input_path))
                .output(
                    str(output_path),
                    acodec="pcm_s16le",
                    ar=sample_rate,
                    ac=1,
                    vn=None,
                )
                .overwrite_output()
                .run(quiet=True)
            )
        except ffmpeg_lib.Error as e:
            raise ExtractionError(
                f"ffmpeg-python extraction failed: {e.stderr.decode() if e.stderr else e}"
            )

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ExtractionError(f"Extraction produced empty output: {output_path}")

        return output_path

    def probe_duration(self, file_path: Path) -> float:
        try:
            import ffmpeg as ffmpeg_lib
        except ImportError:
            raise FfmpegNotFoundError("ffmpeg-python is not installed.")

        _ensure_ffmpeg_binary()

        try:
            info = ffmpeg_lib.probe(str(file_path))
        except ffmpeg_lib.Error as e:
            raise ExtractionError(
                f"ffprobe failed: {e.stderr.decode() if e.stderr else e}"
            )

        duration = info.get("format", {}).get("duration")
        if duration is None:
            raise ExtractionError(f"Could not determine duration of {file_path}")

        return round(float(duration), 3)


# ── Raw CLI backend (fallback) ──────────────────────────────────────────────

class FfmpegCLIExtractor(AudioExtractor):
    """Backend using raw ffmpeg/ffprobe subprocess calls."""

    def extract(self, input_path: Path, output_path: Path,
                sample_rate: int = 16000) -> Path:
        if not input_path.exists():
            raise FileNotFoundError(f"Input not found: {input_path}")

        ffmpeg = _ensure_ffmpeg_binary()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            ffmpeg, "-i", str(input_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", str(sample_rate),
            "-ac", "1",
            "-y",
            str(output_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise ExtractionError(f"ffmpeg failed:\n{result.stderr}")

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ExtractionError(f"ffmpeg produced empty output: {output_path}")

        return output_path

    def probe_duration(self, file_path: Path) -> float:
        ffprobe = shutil.which("ffprobe")
        if not ffprobe:
            raise FfmpegNotFoundError("ffprobe not found in PATH (part of ffmpeg)")

        cmd = [
            ffprobe, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise ExtractionError(f"ffprobe failed:\n{result.stderr}")

        return round(float(result.stdout.strip()), 3)


# ── Default extractor ───────────────────────────────────────────────────────

def get_default_extractor() -> AudioExtractor:
    """Return the best available extractor.

    Prefers ffmpeg-python; falls back to raw CLI.
    """
    try:
        import ffmpeg as _  # noqa: F401
        return FfmpegPythonExtractor()
    except ImportError:
        return FfmpegCLIExtractor()


# ── Convenience functions (backward-compatible) ─────────────────────────────

def extract_audio(video_path: Path, output_path: Path,
                  sample_rate: int = 16000,
                  extractor: AudioExtractor | None = None) -> Path:
    """Extract audio from a video file to WAV.

    Args:
        video_path: Path to input video.
        output_path: Path for output WAV file.
        sample_rate: Target sample rate (16kHz default for speech models).
        extractor: Backend to use. Defaults to best available.

    Returns:
        Path to extracted WAV file.
    """
    ext = extractor or get_default_extractor()
    return ext.extract(video_path, output_path, sample_rate)


def probe_duration(file_path: Path,
                   extractor: AudioExtractor | None = None) -> float:
    """Get duration of an audio or video file in seconds."""
    ext = extractor or get_default_extractor()
    return ext.probe_duration(file_path)


def ensure_ffmpeg() -> str:
    """Return ffmpeg path or raise FfmpegNotFoundError."""
    return _ensure_ffmpeg_binary()


def is_video(path: Path) -> bool:
    """Check if file is a video based on extension."""
    return path.suffix.lower() in {".mp4", ".webm", ".mov", ".avi", ".mkv"}


def is_audio(path: Path) -> bool:
    """Check if file is an audio file based on extension."""
    return path.suffix.lower() in {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"}


# ── Internal helpers ────────────────────────────────────────────────────────

def _ensure_ffmpeg_binary() -> str:
    """Return ffmpeg binary path or raise."""
    path = shutil.which("ffmpeg")
    if not path:
        raise FfmpegNotFoundError(
            "ffmpeg binary not found in PATH. "
            "Install ffmpeg: https://ffmpeg.org/download.html"
        )
    return path
