"""
Voice ingestion pipeline — main orchestrator.

Three modes:
  1. Full pipeline: input → extract → transcribe → beats → captions
  2. Extract-only:  input → extract audio to source.wav (then manual beat-map/captions)
  3. Audio copy:    audio input → copy to project (then manual or auto transcription)

Outputs (all written to project_dir/audio/):
  - source.wav    — extracted/copied audio (always)
  - voice.json    — raw transcript with word-level timestamps (full pipeline only)
  - beat-map.json — phrase-level beats for visual assembly (full pipeline or manual)
  - captions.json — time-bound caption entries (full pipeline or manual)

Also updates project.json status.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .extract import (
    AudioExtractor,
    extract_audio,
    get_default_extractor,
    is_video,
    is_audio,
    probe_duration,
)
from .transcribe import TranscriptionProvider, Transcript
from .beats import generate_beats
from .captions import captions_to_dicts


class IngestError(RuntimeError):
    pass


class IngestResult:
    """Container for pipeline outputs."""
    def __init__(self, voice_json: dict | None, beat_map: dict | None,
                 captions: list[dict] | None,
                 audio_path: Path, project_dir: Path,
                 duration: float | None = None):
        self.voice_json = voice_json
        self.beat_map = beat_map
        self.captions = captions
        self.audio_path = audio_path
        self.project_dir = project_dir
        self._duration = duration

    @property
    def total_duration(self) -> float:
        if self.voice_json:
            return self.voice_json["total_duration"]
        if self._duration:
            return self._duration
        return 0.0

    @property
    def beat_count(self) -> int:
        if self.beat_map:
            return len(self.beat_map["beats"])
        return 0


def _write_json(path: Path, data: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _read_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Extract-only mode ───────────────────────────────────────────────────────

def extract_only(
    input_path: Path,
    project_dir: Path,
    *,
    extractor: AudioExtractor | None = None,
) -> IngestResult:
    """
    Extract audio from a video file without transcription.

    Use this when you want to:
      - Extract audio from a HeyGen avatar MP4
      - Then manually create beat-map.json and captions.json

    The avatar MP4 can live anywhere. A common convention is:
      projects/<slug>/audio/avatar.mp4

    Output is always:
      projects/<slug>/audio/source.wav

    Args:
        input_path: Path to HeyGen avatar MP4 or any video/audio file.
        project_dir: Project directory (e.g., projects/my-reel/).
        extractor: Audio extraction backend. Defaults to ffmpeg-python.

    Returns:
        IngestResult with audio_path set, other fields None.
    """
    if not input_path.exists():
        raise IngestError(f"Input file not found: {input_path}")

    if not is_video(input_path) and not is_audio(input_path):
        raise IngestError(
            f"Unsupported file type: {input_path.suffix}. "
            f"Expected video (.mp4, .webm, .mov, .avi, .mkv) "
            f"or audio (.wav, .mp3, .m4a, .aac, .ogg, .flac)"
        )

    audio_dir = project_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    output_path = audio_dir / "source.wav"

    ext = extractor or get_default_extractor()

    if is_video(input_path):
        extract_audio(input_path, output_path, extractor=ext)
    else:
        # Audio input — convert to canonical WAV format
        extract_audio(input_path, output_path, extractor=ext)

    # Probe duration
    duration: float | None = None
    try:
        duration = probe_duration(output_path, extractor=ext)
    except Exception:
        pass  # Duration is nice-to-have at this stage

    # Update project.json
    project_json_path = project_dir / "project.json"
    if project_json_path.exists():
        project = _read_json(project_json_path)
        project["phase"] = "voice"
        project["status"] = "voice_ready"
        project["voice_file"] = "audio/source.wav"
        project["duration_s"] = duration
        project["updated"] = datetime.now(timezone.utc).isoformat()
        _write_json(project_json_path, project)

    return IngestResult(
        voice_json=None,
        beat_map=None,
        captions=None,
        audio_path=output_path,
        project_dir=project_dir,
        duration=duration,
    )


# ── Full pipeline ───────────────────────────────────────────────────────────

def ingest(
    input_path: Path,
    project_dir: Path,
    provider: TranscriptionProvider,
    *,
    copy_source: bool = True,
    extractor: AudioExtractor | None = None,
) -> IngestResult:
    """
    Run the full voice ingestion pipeline.

    Args:
        input_path: Path to narration audio or HeyGen avatar video.
        project_dir: Path to the reel project directory.
        provider: Transcription provider to use.
        copy_source: Whether to copy/extract source into project audio/ dir.
        extractor: Audio extraction backend. Defaults to ffmpeg-python.

    Returns:
        IngestResult with all generated artifacts.
    """
    # ── Validate input ───────────────────────────────────────────────────
    if not input_path.exists():
        raise IngestError(f"Input file not found: {input_path}")

    if not is_audio(input_path) and not is_video(input_path):
        raise IngestError(
            f"Unsupported file type: {input_path.suffix}. "
            f"Expected audio (.wav, .mp3, .m4a, .aac, .ogg, .flac) "
            f"or video (.mp4, .webm, .mov, .avi, .mkv)"
        )

    audio_dir = project_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    ext = extractor or get_default_extractor()

    # ── Step 1: Get audio ────────────────────────────────────────────────
    if is_video(input_path):
        audio_path = audio_dir / "source.wav"
        extract_audio(input_path, audio_path, extractor=ext)
    elif copy_source:
        audio_path = audio_dir / f"voice{input_path.suffix}"
        shutil.copy2(input_path, audio_path)
    else:
        audio_path = input_path

    # ── Step 2: Transcribe ───────────────────────────────────────────────
    transcript: Transcript = provider.transcribe(audio_path)

    if not transcript.segments:
        raise IngestError("Transcription returned no segments. Is the audio silent?")

    # ── Step 3: Write voice.json ─────────────────────────────────────────
    voice_json = transcript.to_voice_json()
    _write_json(audio_dir / "voice.json", voice_json)

    # ── Step 4: Generate beats and captions ──────────────────────────────
    beat_map, captions = generate_beats(transcript)
    captions_dicts = captions_to_dicts(captions)

    _write_json(audio_dir / "beat-map.json", beat_map)
    _write_json(audio_dir / "captions.json", captions_dicts)

    # ── Step 5: Update project.json ──────────────────────────────────────
    project_json_path = project_dir / "project.json"
    if project_json_path.exists():
        project = _read_json(project_json_path)
        project["phase"] = "voice"
        project["status"] = "voice_ready"
        project["voice_file"] = str(audio_path.relative_to(project_dir))
        project["duration_s"] = transcript.total_duration
        project["updated"] = datetime.now(timezone.utc).isoformat()
        _write_json(project_json_path, project)

    return IngestResult(
        voice_json=voice_json,
        beat_map=beat_map,
        captions=captions_dicts,
        audio_path=audio_path,
        project_dir=project_dir,
    )
