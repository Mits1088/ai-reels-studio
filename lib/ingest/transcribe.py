"""
Transcription providers — pluggable interface for speech-to-text with word timestamps.

To swap providers: implement TranscriptionProvider and pass it to the pipeline.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


# ── Data model ───────────────────────────────────────────────────────────────

@dataclass
class WordTiming:
    word: str
    start: float  # seconds, 3 decimal places
    end: float

    def __post_init__(self):
        self.start = round(self.start, 3)
        self.end = round(self.end, 3)


@dataclass
class Segment:
    """A sentence or phrase-level segment from the transcriber."""
    text: str
    start: float
    end: float
    words: list[WordTiming] = field(default_factory=list)

    def __post_init__(self):
        self.start = round(self.start, 3)
        self.end = round(self.end, 3)


@dataclass
class Transcript:
    """Full transcription result."""
    total_duration: float
    segments: list[Segment]
    language: str = "en"

    def __post_init__(self):
        self.total_duration = round(self.total_duration, 3)

    def to_voice_json(self) -> dict:
        """Produce voice.json conforming to the timing-sync contract."""
        return {
            "total_duration": self.total_duration,
            "language": self.language,
            "sentences": [
                {
                    "text": seg.text,
                    "start": seg.start,
                    "end": seg.end,
                    "words": [asdict(w) for w in seg.words],
                }
                for seg in self.segments
            ],
        }


# ── Provider interface ───────────────────────────────────────────────────────

class TranscriptionProvider(ABC):
    """Abstract base for transcription providers."""

    @abstractmethod
    def transcribe(self, audio_path: Path) -> Transcript:
        """Transcribe audio file and return word-level timestamps."""
        ...


# ── OpenAI Whisper API provider ──────────────────────────────────────────────

class WhisperAPIProvider(TranscriptionProvider):
    """
    Uses OpenAI's Whisper API (or compatible endpoint) for transcription.
    Requires OPENAI_API_KEY in environment or passed directly.
    """

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.openai.com/v1",
                 model: str = "whisper-1"):
        import os
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY required for WhisperAPIProvider")
        self.base_url = base_url.rstrip("/")
        self.model = model

    def transcribe(self, audio_path: Path) -> Transcript:
        import requests

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        url = f"{self.base_url}/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        with open(audio_path, "rb") as f:
            resp = requests.post(
                url,
                headers=headers,
                files={"file": (audio_path.name, f, "audio/wav")},
                data={
                    "model": self.model,
                    "response_format": "verbose_json",
                    "timestamp_granularities[]": "word",
                },
                timeout=120,
            )

        if resp.status_code != 200:
            raise RuntimeError(f"Whisper API error {resp.status_code}: {resp.text}")

        data = resp.json()
        return self._parse_response(data)

    def _parse_response(self, data: dict) -> Transcript:
        total_duration = round(data.get("duration", 0.0), 3)

        # Build word timings from the words array
        all_words = []
        for w in data.get("words", []):
            all_words.append(WordTiming(
                word=w["word"].strip(),
                start=w["start"],
                end=w["end"],
            ))

        # Build segments from the segments array, attaching words by time overlap
        segments = []
        for seg in data.get("segments", []):
            seg_start = round(seg["start"], 3)
            seg_end = round(seg["end"], 3)
            seg_words = [w for w in all_words if w.start >= seg_start - 0.01 and w.end <= seg_end + 0.01]
            segments.append(Segment(
                text=seg["text"].strip(),
                start=seg_start,
                end=seg_end,
                words=seg_words,
            ))

        return Transcript(total_duration=total_duration, segments=segments)


# ── Local Whisper provider (no API key required) ─────────────────────────────

class LocalWhisperProvider(TranscriptionProvider):
    """
    Uses the openai-whisper package for local transcription.
    No API key or network access required.
    """

    def __init__(self, model: str = "base"):
        self.model_name = model

    def transcribe(self, audio_path: Path) -> Transcript:
        import whisper

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        model = whisper.load_model(self.model_name)
        result = model.transcribe(str(audio_path), word_timestamps=True, verbose=False)
        return self._parse_result(result)

    def _parse_result(self, result: dict) -> Transcript:
        total_duration = round(result.get("duration") or 0.0, 3)
        segments = []
        for seg in result.get("segments", []):
            words = []
            for w in seg.get("words", []):
                words.append(WordTiming(
                    word=w["word"].strip(),
                    start=w["start"],
                    end=w["end"],
                ))
            segments.append(Segment(
                text=seg["text"].strip(),
                start=round(seg["start"], 3),
                end=round(seg["end"], 3),
                words=words,
            ))
        if not total_duration and segments:
            total_duration = segments[-1].end
        return Transcript(total_duration=total_duration, segments=segments)


# ── Mock provider for testing ────────────────────────────────────────────────

class MockProvider(TranscriptionProvider):
    """Returns a fixed transcript for testing without real audio or API keys."""

    def __init__(self, transcript: Transcript | None = None):
        self._transcript = transcript or self._default_transcript()

    def transcribe(self, audio_path: Path) -> Transcript:
        return self._transcript

    @staticmethod
    def _default_transcript() -> Transcript:
        return Transcript(
            total_duration=12.500,
            segments=[
                Segment(
                    text="What if you could deploy in one click?",
                    start=0.000, end=2.800,
                    words=[
                        WordTiming("What", 0.000, 0.320),
                        WordTiming("if", 0.320, 0.480),
                        WordTiming("you", 0.500, 0.680),
                        WordTiming("could", 0.700, 0.960),
                        WordTiming("deploy", 1.000, 1.480),
                        WordTiming("in", 1.500, 1.600),
                        WordTiming("one", 1.620, 1.900),
                        WordTiming("click?", 1.920, 2.800),
                    ],
                ),
                Segment(
                    text="No pipelines. No waiting.",
                    start=3.200, end=5.400,
                    words=[
                        WordTiming("No", 3.200, 3.500),
                        WordTiming("pipelines.", 3.520, 4.200),
                        WordTiming("No", 4.400, 4.650),
                        WordTiming("waiting.", 4.670, 5.400),
                    ],
                ),
                Segment(
                    text="Just hit deploy and you're live.",
                    start=5.800, end=8.600,
                    words=[
                        WordTiming("Just", 5.800, 6.080),
                        WordTiming("hit", 6.100, 6.350),
                        WordTiming("deploy", 6.380, 6.900),
                        WordTiming("and", 6.950, 7.100),
                        WordTiming("you're", 7.130, 7.500),
                        WordTiming("live.", 7.520, 8.600),
                    ],
                ),
                Segment(
                    text="Try it free. Link in bio.",
                    start=9.000, end=12.500,
                    words=[
                        WordTiming("Try", 9.000, 9.300),
                        WordTiming("it", 9.320, 9.500),
                        WordTiming("free.", 9.520, 10.100),
                        WordTiming("Link", 10.600, 11.000),
                        WordTiming("in", 11.020, 11.200),
                        WordTiming("bio.", 11.220, 12.500),
                    ],
                ),
            ],
        )
