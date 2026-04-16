"""
lib/orchestrator/ — Workflow state machine for AI Reels Studio.

Implements the orchestration architecture defined in docs/orchestration-spec.md.

Division of responsibility:
  Code  → workflow state, gate enforcement, artifact validation, invalidation
  Claude → script, shot list, motion intent, component selection, revision strategy
  Human → approvals, creative direction, benchmark review, memory promotion

CLI:
  python -m lib.orchestrator status    projects/<slug>
  python -m lib.orchestrator next      projects/<slug>
  python -m lib.orchestrator diagnose  projects/<slug>
  python -m lib.orchestrator approve   projects/<slug> <gate-id>
  python -m lib.orchestrator reject    projects/<slug> <phase-key>
  python -m lib.orchestrator resume    projects/<slug>
  python -m lib.orchestrator invalidate projects/<slug> <artifact>
  python -m lib.orchestrator history   projects/<slug>

Modules:
  spec.py         — phase definitions, state model, invalidation rules
  state.py        — state derivation from project.json
  transitions.py  — legal next action computation
  validators.py   — artifact + parity checks
  invalidation.py — downstream invalidation via lib.gates
  events.py       — orchestration-log.jsonl
  cli.py          — CLI commands
"""

from .state import load_snapshot, ProjectSnapshot, state_label
from .transitions import compute_next_actions, NextAction
from .events import log_event, read_events
from .validators import validate_phase_preconditions
from .invalidation import invalidate_from_change
from .spec import PHASES, INVALIDATION_MAP

__all__ = [
    "load_snapshot",
    "ProjectSnapshot",
    "state_label",
    "compute_next_actions",
    "NextAction",
    "log_event",
    "read_events",
    "validate_phase_preconditions",
    "invalidate_from_change",
    "PHASES",
    "INVALIDATION_MAP",
]
