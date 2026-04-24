"""
lib.brain.models — Data model for a project diagnosis.

Read-only. No mutations. No I/O. Pure data.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ── Sub-models ────────────────────────────────────────────────────────────────


@dataclass
class GateInventory:
    """Gate state at diagnosis time."""
    passed: list[str]                 # gates in gates_passed AND in GATE_ORDER
    missing: list[str]                # gates in GATE_ORDER not yet passed
    next_required: str | None         # lowest unpassed gate in GATE_ORDER
    unknown_gates: list[str]          # in project.json but not in GATE_ORDER (suspicious)
    total: int                        # canonical gate count (11 for reel)


@dataclass
class ArtifactEntry:
    path: str          # relative path inside project dir
    present: bool
    size_bytes: int    # 0 when not present


@dataclass
class StalenessResult:
    """A single detected staleness signal for a downstream artifact."""
    downstream: str            # relative path of the potentially-stale artifact
    upstream: str              # relative path of the artifact that changed
    confidence: str            # high / medium / low
    reason: str                # why downstream may be stale
    recommended_action: str    # what to do about it
    age_delta_seconds: float   # how much newer the upstream is (seconds)


@dataclass
class ArtifactInventory:
    """Status of key pipeline artifacts."""
    entries: list[ArtifactEntry]
    gate_artifact_mismatches: list[str]    # "gate X set but artifact Y missing"
    stale_hints: list[str]                 # human-readable summary (compat)
    staleness_results: list[StalenessResult]  # structured Phase-2 signals


@dataclass
class QAStatus:
    """Summary of the most recent QA report (if any)."""
    available: bool           # qa_report.json exists on disk
    verdict: str              # PASS / PASS_WITH_WARNINGS / FAIL / not_run
    blockers: int             # count of BLOCK findings
    warnings: int             # count of WARN findings
    top_blockers: list[str]   # up to 3 human-readable blocker messages
    report_timestamp: str     # ISO timestamp from report, or ""


@dataclass
class CriticStatus:
    """Summary of the most recent critic report (if any)."""
    available: bool           # critic-report.json exists on disk
    status: str               # critic_passed / critic_warnings / critic_blocked / not_run
    findings_count: int       # total findings at any severity
    highest_severity: str     # block / warn / suggest / none
    top_findings: list[str]   # up to 3 human-readable finding messages
    findings: list[dict] = field(default_factory=list)       # structured findings for repair steps
    # Phase 5 — hard-mode gate fields (default False → no behavior change)
    hard_blocked: bool = False                               # True when allowlisted BLOCK findings remain after waivers
    hard_blocked_findings: list[dict] = field(default_factory=list)  # the specific blocking findings
    applied_waivers: list[dict] = field(default_factory=list)        # waivers that matched this report


@dataclass
class AutonomyVerdict:
    """Can the pipeline continue without human input right now?"""
    can_continue_autonomously: bool  # Claude/code can proceed without human gate
    human_required: bool             # next gate requires human review/approval
    human_required_reason: str       # e.g. "visual_assignment_approved requires human review"
    next_action: str                 # short description of what to do next
    next_action_actor: str           # code / claude / human / human+claude / unknown
    next_action_command: str         # concrete command hint
    confidence: str                  # high / medium / low


# ── Top-level Diagnosis ───────────────────────────────────────────────────────


@dataclass
class Diagnosis:
    """Complete read-only snapshot of a project's diagnostic state."""

    # Identity
    slug: str
    title: str
    project_dir: str

    # project.json health
    project_json_found: bool
    schema_version: int | None
    schema_ok: bool
    phase: str              # from project.json, or "unknown"
    status: str             # from project.json, or "unknown"
    style: str              # cinematic-presenter / editorial-authority / ...
    theme: str
    theme_primary: str
    validation_errors: list[str]

    # Gate state
    gates: GateInventory

    # Artifact state
    artifacts: ArtifactInventory

    # External signal: QA
    qa: QAStatus

    # External signal: critic
    critic: CriticStatus

    # Decision output
    autonomy: AutonomyVerdict

    # Meta
    diagnosis_timestamp: str

    # Mode flags (default False — never changes existing behavior)
    critic_hard_mode: bool = False

    # ── Convenience properties ────────────────────────────────────────────────

    @property
    def critic_hard_blocked(self) -> bool:
        """True when critic_hard_mode is active AND there are allowlisted BLOCK findings
        remaining after waivers.  False by default — no behavior change without opt-in."""
        return self.critic_hard_mode and self.critic.hard_blocked

    @property
    def healthy(self) -> bool:
        """True when project.json is valid, no gate mismatches, and QA is green (or not yet run).
        In critic_hard_mode, only allowlisted BLOCK findings (after waivers) mark unhealthy."""
        if not self.project_json_found or self.validation_errors:
            return False
        if self.artifacts.gate_artifact_mismatches:
            return False
        if self.qa.available and self.qa.verdict == "FAIL":
            return False
        if self.critic_hard_blocked:
            return False
        return True

    @property
    def brain_critic_status(self) -> str:
        """Brain-level interpretation of the critic status using the 5-state vocabulary.

        not_run        — no critic report exists
        advisory_pass  — critic ran, no issues
        advisory_warn  — critic ran, warnings only (never a blocker)
        advisory_fail  — critic blocked, but advisory mode (default) OR not in hard-block allowlist
        hard_blocked   — critic hard-blocked: critic_hard_mode active AND allowlisted BLOCK
                         findings remain after waivers
        """
        if not self.critic.available or self.critic.status in ("not_run", "critic_unavailable"):
            return "not_run"
        if self.critic.status == "critic_blocked":
            return "hard_blocked" if self.critic_hard_blocked else "advisory_fail"
        mapping = {
            "critic_passed": "advisory_pass",
            "critic_warnings": "advisory_warn",
        }
        return mapping.get(self.critic.status, "not_run")

    @property
    def critic_advisory_signal(self) -> bool:
        """True when critic has block-severity findings but we are NOT in hard mode.
        Signals the caller to surface findings as a warning without blocking advancement."""
        return (
            not self.critic_hard_mode
            and self.critic.available
            and self.critic.status == "critic_blocked"
        )

    def to_dict(self) -> dict:
        return {
            "slug": self.slug,
            "title": self.title,
            "project_dir": self.project_dir,
            "project_json_found": self.project_json_found,
            "schema_version": self.schema_version,
            "schema_ok": self.schema_ok,
            "phase": self.phase,
            "status": self.status,
            "style": self.style,
            "theme": self.theme,
            "theme_primary": self.theme_primary,
            "validation_errors": self.validation_errors,
            "gates": {
                "passed": self.gates.passed,
                "missing": self.gates.missing,
                "next_required": self.gates.next_required,
                "unknown_gates": self.gates.unknown_gates,
                "total": self.gates.total,
            },
            "artifacts": {
                "entries": [
                    {"path": e.path, "present": e.present, "size_bytes": e.size_bytes}
                    for e in self.artifacts.entries
                ],
                "gate_artifact_mismatches": self.artifacts.gate_artifact_mismatches,
                "stale_hints": self.artifacts.stale_hints,
                "staleness_results": [
                    {
                        "downstream": r.downstream,
                        "upstream": r.upstream,
                        "confidence": r.confidence,
                        "reason": r.reason,
                        "recommended_action": r.recommended_action,
                        "age_delta_seconds": r.age_delta_seconds,
                    }
                    for r in self.artifacts.staleness_results
                ],
            },
            "qa": {
                "available": self.qa.available,
                "verdict": self.qa.verdict,
                "blockers": self.qa.blockers,
                "warnings": self.qa.warnings,
                "top_blockers": self.qa.top_blockers,
                "report_timestamp": self.qa.report_timestamp,
            },
            "critic": {
                "available": self.critic.available,
                "status": self.critic.status,
                "brain_status": self.brain_critic_status,
                "findings_count": self.critic.findings_count,
                "highest_severity": self.critic.highest_severity,
                "top_findings": self.critic.top_findings,
                "findings": self.critic.findings,
                "hard_blocked": self.critic.hard_blocked,
                "applied_waivers": self.critic.applied_waivers,
            },
            "autonomy": {
                "can_continue_autonomously": self.autonomy.can_continue_autonomously,
                "human_required": self.autonomy.human_required,
                "human_required_reason": self.autonomy.human_required_reason,
                "next_action": self.autonomy.next_action,
                "next_action_actor": self.autonomy.next_action_actor,
                "next_action_command": self.autonomy.next_action_command,
                "confidence": self.autonomy.confidence,
            },
            "healthy": self.healthy,
            "critic_advisory_signal": self.critic_advisory_signal,
            "critic_hard_mode": self.critic_hard_mode,
            "critic_hard_blocked": self.critic_hard_blocked,
            "diagnosis_timestamp": self.diagnosis_timestamp,
        }
