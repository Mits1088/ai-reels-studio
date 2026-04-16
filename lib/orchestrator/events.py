"""
lib/orchestrator/events.py — Event logging for orchestration transitions.

Every approval, rejection, invalidation, and state transition is written
to projects/<slug>/output/orchestration-log.jsonl.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal


Actor = Literal["code", "claude", "human"]
Result = Literal["success", "blocked", "failed", "paused", "approved", "rejected", "invalidated"]


@dataclass
class OrchestratorEvent:
    timestamp: str
    project_slug: str
    actor: str
    action: str
    phase: str | None
    prior_state: str | None
    next_state: str | None
    gates_before: list[str]
    gates_after: list[str]
    artifacts_produced: list[str]
    validations_run: list[str]
    result: str
    notes: str


def log_event(
    project_dir: Path,
    *,
    actor: str,
    action: str,
    phase: str | None = None,
    prior_state: str | None = None,
    next_state: str | None = None,
    gates_before: list[str] | None = None,
    gates_after: list[str] | None = None,
    artifacts_produced: list[str] | None = None,
    validations_run: list[str] | None = None,
    result: str = "success",
    notes: str = "",
) -> None:
    """Append one event to the project's orchestration log."""
    slug = project_dir.name
    event = OrchestratorEvent(
        timestamp=datetime.now(timezone.utc).isoformat(),
        project_slug=slug,
        actor=actor,
        action=action,
        phase=phase,
        prior_state=prior_state,
        next_state=next_state,
        gates_before=gates_before or [],
        gates_after=gates_after or [],
        artifacts_produced=artifacts_produced or [],
        validations_run=validations_run or [],
        result=result,
        notes=notes,
    )

    log_path = project_dir / "output" / "orchestration-log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")


def read_events(project_dir: Path) -> list[dict]:
    """Read all events from the orchestration log."""
    log_path = project_dir / "output" / "orchestration-log.jsonl"
    if not log_path.exists():
        return []
    events = []
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return events
