"""
Caption generation from phrases.

Produces time-bound caption entries ready for the captions lane in timeline.json.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from .phrases import Phrase


@dataclass
class Caption:
    text: str
    start: float
    end: float
    beat_id: str  # will be set during beat map generation

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 3)


def phrases_to_captions(phrases: list[Phrase]) -> list[Caption]:
    """
    Convert phrases into caption entries.
    Each phrase becomes one caption. beat_id is placeholder until beat map assigns them.
    """
    captions: list[Caption] = []
    for i, phrase in enumerate(phrases):
        captions.append(Caption(
            text=phrase.text,
            start=phrase.start,
            end=phrase.end,
            beat_id="",  # assigned when beats are created
        ))
    return captions


def captions_to_dicts(captions: list[Caption]) -> list[dict]:
    """Serialize captions for JSON output."""
    return [
        {"text": c.text, "start": c.start, "end": c.end, "beat_id": c.beat_id}
        for c in captions
    ]
