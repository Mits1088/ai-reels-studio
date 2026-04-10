"""
Phrase boundary detection.

Groups transcription segments into caption-friendly phrases,
respecting pause boundaries and max word count for readability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from .transcribe import Segment, WordTiming


@dataclass
class Phrase:
    """A display-friendly phrase — a slice of a segment."""
    text: str
    start: float
    end: float
    words: list[WordTiming]
    segment_index: int  # which transcript segment this came from

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 3)


# Minimum visible duration for any text element (from timing-sync rule)
MIN_VISIBLE_DURATION = 0.8

# Max words per caption overlay (from visual-style rule)
MAX_WORDS_PER_PHRASE = 6

# Pause threshold: if gap between words > this, split phrase
PAUSE_THRESHOLD = 0.4


def segment_to_phrases(segment: Segment, segment_index: int,
                       max_words: int = MAX_WORDS_PER_PHRASE,
                       pause_threshold: float = PAUSE_THRESHOLD) -> list[Phrase]:
    """
    Split a transcription segment into display phrases.

    Splitting rules (in priority order):
    1. Split at internal pauses > pause_threshold between words
    2. Split at max_words boundary
    3. Never split below 1 word
    """
    if not segment.words:
        return [Phrase(
            text=segment.text, start=segment.start, end=segment.end,
            words=[], segment_index=segment_index,
        )]

    phrases: list[Phrase] = []
    current_words: list[WordTiming] = []

    for i, word in enumerate(segment.words):
        # Check for pause split
        if current_words:
            gap = word.start - current_words[-1].end
            if gap >= pause_threshold:
                phrases.append(_make_phrase(current_words, segment_index))
                current_words = []

        current_words.append(word)

        # Check for max words split
        if len(current_words) >= max_words:
            phrases.append(_make_phrase(current_words, segment_index))
            current_words = []

    # Flush remaining
    if current_words:
        phrases.append(_make_phrase(current_words, segment_index))

    return phrases


def _make_phrase(words: list[WordTiming], segment_index: int) -> Phrase:
    text = " ".join(w.word for w in words)
    start = words[0].start
    end = words[-1].end

    # Enforce minimum visible duration
    if end - start < MIN_VISIBLE_DURATION:
        end = round(start + MIN_VISIBLE_DURATION, 3)

    return Phrase(
        text=text,
        start=round(start, 3),
        end=round(end, 3),
        words=list(words),
        segment_index=segment_index,
    )


def extract_phrases(segments: list[Segment], **kwargs) -> list[Phrase]:
    """Extract phrases from all segments."""
    phrases: list[Phrase] = []
    for i, seg in enumerate(segments):
        phrases.extend(segment_to_phrases(seg, i, **kwargs))
    return phrases
