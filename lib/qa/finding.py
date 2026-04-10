"""
QA finding data model.

Every QA check produces Findings. Each finding is either:
  - BLOCK: must be fixed before export
  - WARN:  should be reviewed but doesn't prevent export
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    BLOCK = "block"
    WARN = "warn"


@dataclass
class Finding:
    gate: str          # which QA gate produced this
    severity: Severity
    location: str      # where in the project (e.g. "beat-03", "captions[2]", "0.0s–2.8s")
    message: str       # what's wrong
    fix_hint: str      # how to fix it

    def to_dict(self) -> dict:
        return {
            "gate": self.gate,
            "severity": self.severity.value,
            "location": self.location,
            "message": self.message,
            "fix_hint": self.fix_hint,
        }

    def __repr__(self):
        icon = "BLOCK" if self.severity == Severity.BLOCK else " WARN"
        return f"[{icon}] {self.gate} @ {self.location}: {self.message}"
