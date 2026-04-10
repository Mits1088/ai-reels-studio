"""
Scene grammar — maps beats to scene types based on position and content.

V1 scene grammar for 20-60s Instagram reels:
  hook → context → demo → proof → news-hit → CTA

Not every reel uses all scene types. The grammar assigns scene types
based on beat position within the total duration.
"""

from __future__ import annotations


# Default scene sequence for a standard reel
DEFAULT_GRAMMAR = ["hook", "context", "demo", "proof", "cta"]

# Extended grammar when reel is 40s+
EXTENDED_GRAMMAR = ["hook", "context", "demo", "proof", "news-hit", "cta"]


def assign_scene_types(
    beats: list[dict],
    total_duration: float,
    grammar: list[str] | None = None,
) -> list[dict]:
    """
    Assign a scene_type to each beat based on its position in the reel.

    Mutates beats in-place (adds 'scene_type' key) and returns them.

    Strategy:
      - First beat is always 'hook'
      - Last beat is always 'cta'
      - Middle beats are distributed across remaining grammar slots
      - If more beats than grammar slots, adjacent beats share a scene type
    """
    if not beats:
        return beats

    if grammar is None:
        grammar = EXTENDED_GRAMMAR if total_duration >= 40 else DEFAULT_GRAMMAR

    n_beats = len(beats)

    if n_beats == 1:
        beats[0]["scene_type"] = grammar[0]
        return beats

    if n_beats == 2:
        beats[0]["scene_type"] = grammar[0]
        beats[-1]["scene_type"] = grammar[-1]
        return beats

    # First = hook, last = cta, distribute middle beats across middle grammar slots
    beats[0]["scene_type"] = grammar[0]
    beats[-1]["scene_type"] = grammar[-1]

    middle_beats = n_beats - 2
    middle_grammar = grammar[1:-1]

    if middle_beats <= len(middle_grammar):
        # Fewer beats than grammar slots: pick evenly spaced grammar entries
        for i in range(middle_beats):
            idx = round(i * (len(middle_grammar) - 1) / max(middle_beats - 1, 1))
            beats[i + 1]["scene_type"] = middle_grammar[idx]
    else:
        # More beats than grammar slots: distribute grammar across beats
        for i in range(middle_beats):
            idx = round(i * (len(middle_grammar) - 1) / max(middle_beats - 1, 1))
            beats[i + 1]["scene_type"] = middle_grammar[idx]

    return beats
