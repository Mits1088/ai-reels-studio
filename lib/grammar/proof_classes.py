"""
Proof classes — the 7-step escalation arc that retention-first reels follow.

Source of truth for proof_class values across:
  - training/training-schema.json   (segment.proof_class enum)
  - lib/schemas/edit_plan.schema.json (beat_plan.proof_class oneOf)
  - lib/critic/                     (Phase E — proof arc validation)
  - lib/edit_plan/compile.py        (Phase C — propagates proof_class)

The order encodes the canonical escalation. The critic in Phase E will
flag any backward jump in proof_class as a structural error.
"""

from __future__ import annotations


# Canonical escalation order. Values appear top-to-bottom as a reel progresses.
PROOF_ORDER: list[str] = [
    "existence",     # the thing exists / is real
    "breadth",       # it covers many domains, surfaces, or use cases
    "process",       # show how it works — the demo
    "output",        # show real artifacts the user gets
    "integration",   # it plays nicely with other tools / workflows
    "authority",     # someone trustworthy validates it
    "cta",           # call to action — the ask
]

PROOF_CLASSES: frozenset[str] = frozenset(PROOF_ORDER)


def is_valid_proof_class(value: str | None) -> bool:
    """A proof class value is valid if it is None or one of the 7 known classes."""
    return value is None or value in PROOF_CLASSES


def validate_proof_arc(arc: list[str | None]) -> list[str]:
    """Validate that a sequence of proof_class values does not jump backward.

    None values (beats with no proof_class) are transparent — they
    neither advance nor regress the arc.

    Returns a list of error strings. Empty list = valid arc.
    """
    errors: list[str] = []
    last_index = -1
    last_class: str | None = None

    for i, value in enumerate(arc):
        if value is None:
            continue
        if value not in PROOF_CLASSES:
            errors.append(f"position {i}: unknown proof_class {value!r}")
            continue
        idx = PROOF_ORDER.index(value)
        if idx < last_index:
            errors.append(
                f"position {i}: proof_class {value!r} appears after "
                f"{last_class!r} — proof arc must escalate forward, "
                f"not jump backward"
            )
        if idx >= last_index:
            last_index = idx
            last_class = value

    return errors
