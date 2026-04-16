"""
lib/critic/gate.py — Phase E3 conditional critic gate (shadow mode).

The gate reads a critic report and returns a GateDecision — a structured
answer to the question "would this project's editorial findings be enough
to refuse compile?".

Phase E3 ships this in SHADOW MODE only:
  - The decision is computed and written to output/critic-gate.json for
    visibility and audit.
  - compile is NOT refused unless the caller explicitly sets hard_gate_enabled
    AND the gate is blocked AND no override is used.
  - Default behavior is advisory — the artifact exists so humans and skills
    can see what a hard gate WOULD do, without actually changing compile
    behavior.

Gate rules (Phase E3 starting set, validated by E2.5 calibration):

  asset_overreuse      BLOCK → always enabled
                       (8 real BLOCKs across 9 projects, confidence 1.0)

  visual_novelty       BLOCK → always enabled
                       (7 real BLOCKs across 9 projects, confidence 0.9)

  dead_holds           BLOCK → requires edit_plan.json
                       (downshift logic in Phase E2 prevents false positives
                       when editorial zoom intent is not yet authored)

  caption_competition  BLOCK → requires full enrichment
                       (text_density data must exist to trust the threshold)

  claim_to_proof_latency → advisory only
                       (low fire rate, narrow regex; needs wider validation)

  proof_relevance      → advisory only
                       (per-beat WARN path needs editorial_tags that Phase B
                       enrichment does not auto-generate)

Promotion path: as more real data accumulates (more enriched projects, more
projects with edit-plans, broader claim-keyword coverage), the conditional
checks can move to always-enabled and the advisory-only checks can gain
conditional rules. Each promotion is a single constant change in this file.

The evaluator is a pure function. No I/O. The critic CLI calls it in shadow
mode and writes the artifact; the compile CLI calls it inline with its own
hard_mode and override flags.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .runner import STATUS_UNAVAILABLE
from .finding import SEVERITY_BLOCK


GATE_VERSION = "lib.critic.gate@1.0.0"


# ── Gate statuses ──────────────────────────────────────────────────────────

GATE_PASSED = "gate_passed"
GATE_BLOCKED = "gate_blocked"
GATE_UNAVAILABLE = "gate_unavailable"
GATE_SKIPPED = "gate_skipped"

VALID_GATE_STATUSES = frozenset({
    GATE_PASSED, GATE_BLOCKED, GATE_UNAVAILABLE, GATE_SKIPPED,
})


# ── Rule kinds ─────────────────────────────────────────────────────────────

RULE_ALWAYS = "always_enabled"
RULE_REQUIRES_EDIT_PLAN = "requires_edit_plan"
RULE_REQUIRES_ENRICHMENT = "requires_full_enrichment"
RULE_ADVISORY = "advisory_only"

# Maps check name → gate rule kind. Changing this is the promotion mechanism.
CHECK_RULES: dict[str, str] = {
    "asset_overreuse":        RULE_ALWAYS,
    "visual_novelty":         RULE_ALWAYS,
    "dead_holds":             RULE_REQUIRES_EDIT_PLAN,
    "caption_competition":    RULE_REQUIRES_ENRICHMENT,
    "claim_to_proof_latency": RULE_ADVISORY,
    "proof_relevance":        RULE_ADVISORY,
}


# ── Gate context ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class GateContext:
    """Context beyond the critic report itself that gate rules may consult.

    Derived from the critic report's inputs_present + enrichment_state when
    not supplied explicitly. Callers (tests, compile CLI) can pass their own
    context to override derivation.
    """
    edit_plan_present: bool = False
    enrichment_full: bool = False  # all catalog assets in enrichment.status = "full"


# ── Gate decision ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class GateDecision:
    """Structured gate verdict. All fields serializable to critic-gate.json."""
    gate_status: str
    blocking_findings: tuple[dict, ...] = ()
    conditional_findings: tuple[dict, ...] = ()
    advisory_findings: tuple[dict, ...] = ()
    would_refuse_compile: bool = False
    hard_gate_enabled: bool = False
    override_used: bool = False
    actual_refuse_compile: bool = False
    rationale: str = ""
    rule_summary: dict = field(default_factory=dict)

    def to_dict(self, *, project: str = "") -> dict:
        out: dict[str, Any] = {
            "schema_version": 1,
            "gate_version": GATE_VERSION,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "mode": "hard" if self.hard_gate_enabled else "shadow",
            "gate_status": self.gate_status,
            "would_refuse_compile": self.would_refuse_compile,
            "hard_gate_enabled": self.hard_gate_enabled,
            "override_used": self.override_used,
            "actual_refuse_compile": self.actual_refuse_compile,
            "blocking_findings": list(self.blocking_findings),
            "conditional_findings": list(self.conditional_findings),
            "advisory_findings": list(self.advisory_findings),
            "rule_summary": dict(self.rule_summary),
            "rationale": self.rationale,
        }
        if project:
            out["project"] = project
        return out


# ── Helpers ────────────────────────────────────────────────────────────────


def _rule_enabled(rule: str, context: GateContext) -> bool:
    """Return True if a conditional rule's precondition is met in this context."""
    if rule == RULE_ALWAYS:
        return True
    if rule == RULE_REQUIRES_EDIT_PLAN:
        return context.edit_plan_present
    if rule == RULE_REQUIRES_ENRICHMENT:
        return context.enrichment_full
    return False  # RULE_ADVISORY and unknowns never gate


def _precondition_note(rule: str) -> str:
    if rule == RULE_REQUIRES_EDIT_PLAN:
        return "would gate if edit-plan.json were present"
    if rule == RULE_REQUIRES_ENRICHMENT:
        return "would gate if all catalog assets were enriched"
    if rule == RULE_ADVISORY:
        return "advisory-only check — never gates"
    return ""


def _context_from_report(report: dict) -> GateContext:
    inputs = report.get("inputs_present", {}) or {}
    enr = report.get("enrichment_state", {}) or {}
    total = enr.get("total", 0) or 0
    full = enr.get("full", 0) or 0
    return GateContext(
        edit_plan_present=bool(inputs.get("edit_plan", False)),
        enrichment_full=(total > 0 and full == total),
    )


def _collect_findings(report: dict) -> list[dict]:
    findings: list[dict] = []
    for beat_block in report.get("beats", []) or []:
        for f in beat_block.get("findings", []) or []:
            findings.append(f)
    for f in report.get("global_findings", []) or []:
        findings.append(f)
    return findings


def _finding_summary(f: dict, rule: str, precondition_met: bool) -> dict:
    return {
        "check":            f.get("check", ""),
        "finding_id":       f.get("finding_id", ""),
        "beat_id":          f.get("beat_id"),
        "severity":         f.get("severity", ""),
        "confidence":       f.get("confidence", 0.0),
        "reason":           f.get("reason", ""),
        "rule":             rule,
        "precondition_met": precondition_met,
    }


def _build_rationale(
    gate_status: str,
    blocking: list[dict],
    conditional: list[dict],
    advisory: list[dict],
    hard_gate_enabled: bool,
    override_used: bool,
    actual_refuse: bool,
) -> str:
    parts: list[str] = []

    if gate_status == GATE_SKIPPED:
        parts.append("Gate SKIPPED: no critic report available.")
    elif gate_status == GATE_UNAVAILABLE:
        parts.append("Gate UNAVAILABLE: critic could not form an opinion (required inputs missing).")
    elif gate_status == GATE_PASSED:
        parts.append(f"Gate PASSED: no blocking findings from enabled rules ({len(blocking)} blockers).")
    elif gate_status == GATE_BLOCKED:
        parts.append(f"Gate BLOCKED by {len(blocking)} finding(s) from enabled rules.")
        for f in blocking[:3]:
            where = f.get("beat_id") or "global"
            parts.append(f"  - [{f['check']}] {where}: {f.get('reason', '')[:80]}")

    if conditional:
        checks = sorted({c["check"] for c in conditional})
        parts.append(
            f"{len(conditional)} finding(s) from conditional rules did not gate "
            f"(unmet preconditions): {', '.join(checks)}."
        )

    if advisory:
        checks = sorted({a["check"] for a in advisory})
        parts.append(
            f"{len(advisory)} advisory-only finding(s) recorded but never gate: "
            f"{', '.join(checks)}."
        )

    if not hard_gate_enabled:
        parts.append("Running in SHADOW mode — compile will proceed regardless.")
    elif actual_refuse:
        parts.append("HARD mode: compile will be REFUSED.")
    elif override_used:
        parts.append("HARD mode + --allow-critic-blocked: override bypassed the gate.")
    else:
        parts.append("HARD mode: compile will proceed (gate not blocking).")

    return " ".join(parts)


# ── Public API ─────────────────────────────────────────────────────────────


def evaluate_gate(
    critic_report: dict | None,
    context: GateContext | None = None,
    *,
    hard_gate_enabled: bool = False,
    override_used: bool = False,
) -> GateDecision:
    """Pure function. Evaluate gate rules against a critic report.

    Args:
        critic_report: dict from output/critic-report.json. None or {} → gate_skipped.
        context: optional; if None, derived from the report's inputs_present + enrichment_state.
        hard_gate_enabled: when True, actual_refuse_compile reflects would_refuse_compile.
        override_used: when True, actual_refuse_compile is forced to False even in hard mode.

    Returns:
        GateDecision with gate_status, blocking/conditional/advisory findings, and rationale.
    """
    if not critic_report:
        return GateDecision(
            gate_status=GATE_SKIPPED,
            hard_gate_enabled=hard_gate_enabled,
            override_used=override_used,
            rationale=_build_rationale(
                GATE_SKIPPED, [], [], [],
                hard_gate_enabled, override_used, actual_refuse=False,
            ),
        )

    # Critic said it couldn't form an opinion → gate defers too.
    critic_status = critic_report.get("critic_status")
    if critic_status == STATUS_UNAVAILABLE:
        return GateDecision(
            gate_status=GATE_UNAVAILABLE,
            hard_gate_enabled=hard_gate_enabled,
            override_used=override_used,
            rationale=_build_rationale(
                GATE_UNAVAILABLE, [], [], [],
                hard_gate_enabled, override_used, actual_refuse=False,
            ),
        )

    ctx = context if context is not None else _context_from_report(critic_report)

    blocking: list[dict] = []
    conditional: list[dict] = []
    advisory: list[dict] = []
    rule_summary: dict[str, dict] = {}

    def _ensure_rule_entry(check_name: str) -> None:
        if check_name not in rule_summary:
            rule = CHECK_RULES.get(check_name, RULE_ADVISORY)
            rule_summary[check_name] = {
                "rule":             rule,
                "precondition_met": _rule_enabled(rule, ctx),
                "blockers":         0,
                "triggered":        False,
                "note":             _precondition_note(rule),
            }

    for f in _collect_findings(critic_report):
        check = f.get("check", "")
        severity = f.get("severity", "")
        _ensure_rule_entry(check)

        # Only BLOCK-severity findings contribute to gate decisions.
        if severity != SEVERITY_BLOCK:
            continue

        rule = CHECK_RULES.get(check, RULE_ADVISORY)
        rule_summary[check]["blockers"] += 1

        if rule == RULE_ADVISORY:
            advisory.append(_finding_summary(f, rule, precondition_met=False))
            continue

        precondition_met = _rule_enabled(rule, ctx)
        summary = _finding_summary(f, rule, precondition_met=precondition_met)

        if precondition_met:
            blocking.append(summary)
            rule_summary[check]["triggered"] = True
        else:
            conditional.append(summary)

    would_refuse = len(blocking) > 0
    gate_status = GATE_BLOCKED if would_refuse else GATE_PASSED
    actual_refuse = bool(would_refuse and hard_gate_enabled and not override_used)

    rationale = _build_rationale(
        gate_status, blocking, conditional, advisory,
        hard_gate_enabled, override_used, actual_refuse,
    )

    return GateDecision(
        gate_status=gate_status,
        blocking_findings=tuple(blocking),
        conditional_findings=tuple(conditional),
        advisory_findings=tuple(advisory),
        would_refuse_compile=would_refuse,
        hard_gate_enabled=hard_gate_enabled,
        override_used=override_used,
        actual_refuse_compile=actual_refuse,
        rationale=rationale,
        rule_summary=rule_summary,
    )
