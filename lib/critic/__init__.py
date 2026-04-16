"""
lib/critic/ — advisory editorial critic.

Phase E1 scope: read planning artifacts (asset-matches.json, motion-plan.json,
gap-ownership.json, beat-map.json, optional edit-plan.json + catalog) and
produce a critic-report.{json,md} with structured editorial findings.

Six checks (per Phase E framing):
  - claim_to_proof_latency  : claims must have visual proof within 1.5s
  - dead_holds              : static images held > 2.5s without zoom plan
  - asset_overreuse         : same asset selected for too many beats
  - proof_relevance         : asset editorial_tags should match beat intent
  - caption_competition     : high-text-density assets should suppress captions
  - visual_novelty          : adjacent beats should show different content

Phase E1 is **advisory only**. Findings are written but the compiler does
NOT consult them. Phase E2 will add a soft gate (project.json status flag).
Phase E3 will promote blocker-level findings into a hard compile gate.

Every CriticFinding carries the 5 user-required fields:
  severity, confidence, reason, evidence, suggested_fix
plus check name and optional beat_id for beat-scoped findings.
"""

from .finding import (
    CriticFinding,
    SEVERITY_BLOCK,
    SEVERITY_WARN,
    SEVERITY_SUGGEST,
    SCOPE_BEAT,
    SCOPE_GLOBAL,
    make_finding,
    make_finding_id,
)
from .checks import (
    check_claim_to_proof_latency,
    check_dead_holds,
    check_asset_overreuse,
    check_proof_relevance,
    check_caption_competition,
    check_visual_novelty,
    CHECK_REGISTRY,
)
from .runner import (
    CriticReport,
    run_critic,
    run_critic_for_project,
    build_critic_status_dict,
    CRITIC_VERSION,
    STATUS_PASSED,
    STATUS_WARNINGS,
    STATUS_BLOCKED,
    STATUS_UNAVAILABLE,
)
from .markdown import render_critic_markdown
from .gate import (
    GateContext,
    GateDecision,
    evaluate_gate,
    GATE_VERSION,
    GATE_PASSED,
    GATE_BLOCKED,
    GATE_UNAVAILABLE,
    GATE_SKIPPED,
    RULE_ALWAYS,
    RULE_REQUIRES_EDIT_PLAN,
    RULE_REQUIRES_ENRICHMENT,
    RULE_ADVISORY,
    CHECK_RULES,
)

__all__ = [
    "CriticFinding",
    "SEVERITY_BLOCK",
    "SEVERITY_WARN",
    "SEVERITY_SUGGEST",
    "SCOPE_BEAT",
    "SCOPE_GLOBAL",
    "make_finding",
    "make_finding_id",
    "check_claim_to_proof_latency",
    "check_dead_holds",
    "check_asset_overreuse",
    "check_proof_relevance",
    "check_caption_competition",
    "check_visual_novelty",
    "CHECK_REGISTRY",
    "CriticReport",
    "run_critic",
    "run_critic_for_project",
    "build_critic_status_dict",
    "CRITIC_VERSION",
    "STATUS_PASSED",
    "STATUS_WARNINGS",
    "STATUS_BLOCKED",
    "STATUS_UNAVAILABLE",
    "render_critic_markdown",
    # gate (Phase E3)
    "GateContext",
    "GateDecision",
    "evaluate_gate",
    "GATE_VERSION",
    "GATE_PASSED",
    "GATE_BLOCKED",
    "GATE_UNAVAILABLE",
    "GATE_SKIPPED",
    "RULE_ALWAYS",
    "RULE_REQUIRES_EDIT_PLAN",
    "RULE_REQUIRES_ENRICHMENT",
    "RULE_ADVISORY",
    "CHECK_RULES",
]
