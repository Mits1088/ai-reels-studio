"""
Beat map generation.

A beat = one phrase of narration with its timing. Beats are the atomic unit
that all visual decisions reference. Each beat maps to exactly one phrase
from the transcript.

Scene assignment: beats from the same transcript segment share a scene number.
"""

from __future__ import annotations

from dataclasses import asdict
from .transcribe import Transcript, WordTiming
from .phrases import Phrase, extract_phrases
from .captions import Caption, phrases_to_captions


def generate_beats(transcript: Transcript, **phrase_kwargs) -> dict:
    """
    Generate a beat-map.json from a transcript.

    Returns the beat map dict conforming to lib/schemas/beat_map.schema.json.
    Also returns captions with beat_ids assigned.
    """
    phrases = extract_phrases(transcript.segments, **phrase_kwargs)
    captions = phrases_to_captions(phrases)

    # Assign scene numbers: each transcript segment = one scene
    scene_map: dict[int, int] = {}  # segment_index -> scene number
    scene_counter = 0
    for phrase in phrases:
        if phrase.segment_index not in scene_map:
            scene_counter += 1
            scene_map[phrase.segment_index] = scene_counter

    beats = []
    for i, phrase in enumerate(phrases):
        beat_id = f"beat-{i + 1:02d}"

        # Assign beat_id to the corresponding caption
        captions[i].beat_id = beat_id

        beats.append({
            "id": beat_id,
            "scene": scene_map[phrase.segment_index],
            "phrase": phrase.text,
            "start": phrase.start,
            "end": phrase.end,
            "words": [asdict(w) for w in phrase.words],
            "visual_intent": "",  # filled by human or later AI step
            "asset_refs": [],
        })

    beat_map = {
        "total_duration": transcript.total_duration,
        "beats": beats,
    }

    return beat_map, captions
