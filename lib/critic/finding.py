"""
CriticFinding dataclass — every critic finding carries the 5 user-required
fields: severity, confidence, reason, evidence, suggested_fix.

Two scopes:
  - SCOPE_BEAT:   the finding applies to a specific beat (beat_id is set)
  - SCOPE_GLOBAL: the finding applies to the whole reel (beat_id is None)

Three severities:
  - SEVERITY_BLOCK:   would gate the compiler in Phase E3 (advisory in E1)
  - SEVERITY_WARN:    editorial concern; review recommended
  - SEVERITY_SUGGEST: optional improvement
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Severity constants
SEVERITY_BLOCK = "BLOCK"
SEVERITY_WARN = "WARN"
SEVERITY_SUGGEST = "SUGGEST"

VALID_SEVERITIES = frozenset({SEVERITY_BLOCK, SEVERITY_WARN, SEVERITY_SUGGEST})

# Scope constants
SCOPE_BEAT = "beat"
SCOPE_GLOBAL = "global"


@dataclass(frozen=True)
class CriticFinding:
    """One editorial finding from a critic check.

    Fields:
        check:         which check produced this (e.g. "claim_to_proof_latency")
        severity:      one of SEVERITY_BLOCK / SEVERITY_WARN / SEVERITY_SUGGEST
        confidence:    [0..1] — how confident the critic is in this finding
        reason:        human-readable explanation
        evidence:      structured machine-readable supporting data
        suggested_fix: actionable hint for resolving the finding
        beat_id:       optional — present for beat-scoped findings
        finding_id:    Phase E2 — stable, deterministic ID `<check>:<scope>:<key>`
        related_ids:   Phase E2 — IDs of related findings (e.g. asset_overreuse and
                       visual_novelty about the same asset)
        scope:         "beat" when beat_id is set, "global" otherwise (computed)
    """
    check: str
    severity: str
    confidence: float
    reason: str
    evidence: dict
    suggested_fix: str
    beat_id: str | None = None
    finding_id: str = ""
    related_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.severity not in VALID_SEVERITIES:
            raise ValueError(
                f"Invalid severity {self.severity!r}; expected one of {sorted(VALID_SEVERITIES)}"
            )
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"confidence {self.confidence} out of range [0,1]"
            )

    @property
    def scope(self) -> str:
        return SCOPE_BEAT if self.beat_id else SCOPE_GLOBAL

    def to_dict(self) -> dict:
        out: dict[str, Any] = {
            "finding_id":    self.finding_id,
            "check":         self.check,
            "severity":      self.severity,
            "confidence":    round(self.confidence, 4),
            "reason":        self.reason,
            "evidence":      dict(self.evidence),
            "suggested_fix": self.suggested_fix,
            "scope":         self.scope,
        }
        if self.beat_id is not None:
            out["beat_id"] = self.beat_id
        if self.related_ids:
            out["related_ids"] = list(self.related_ids)
        return out


def make_finding_id(check: str, beat_id: str | None, id_key: str | None = None) -> str:
    """Compute a stable, deterministic finding ID.

    Format: ``<check>:<scope>:<key>`` where:
      - scope is 'beat' when beat_id is set, 'global' otherwise
      - key is id_key if explicit, else beat_id, else 'default'

    Examples:
      claim_to_proof_latency:beat:beat-03
      asset_overreuse:global:demo-anatomy-artifact
      proof_relevance:global:no_enrichment
      visual_novelty:beat:beat-01

    IDs are deterministic across runs as long as the underlying data is stable.
    """
    if id_key:
        scope_str = SCOPE_BEAT if beat_id else SCOPE_GLOBAL
        return f"{check}:{scope_str}:{id_key}"
    if beat_id:
        return f"{check}:{SCOPE_BEAT}:{beat_id}"
    return f"{check}:{SCOPE_GLOBAL}:default"


def make_finding(
    *,
    check: str,
    severity: str,
    confidence: float,
    reason: str,
    evidence: dict,
    suggested_fix: str,
    beat_id: str | None = None,
    id_key: str | None = None,
    related_ids: tuple[str, ...] = (),
) -> CriticFinding:
    """Construct a CriticFinding with an auto-computed deterministic finding_id.

    Use this factory in check functions instead of constructing CriticFinding
    directly. Test code can still construct CriticFinding directly (finding_id
    defaults to empty string when omitted).
    """
    return CriticFinding(
        check=check,
        severity=severity,
        confidence=confidence,
        reason=reason,
        evidence=evidence,
        suggested_fix=suggested_fix,
        beat_id=beat_id,
        finding_id=make_finding_id(check, beat_id, id_key),
        related_ids=related_ids,
    )
