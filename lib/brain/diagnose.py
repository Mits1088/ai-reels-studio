"""
lib.brain.diagnose — Core diagnostic logic.

Read-only. Aggregates signals from:
  - project.json (gates, phase, status, validation)
  - filesystem (artifact presence, mtime-based stale hints)
  - output/qa_report.json (if present — not re-run)
  - output/critic-report.json (if present — not re-run)

Returns a Diagnosis dataclass. Never mutates any file.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from lib.constants import GATE_ORDER, CURRENT_SCHEMA_VERSION, VALID_GATE_IDS
from lib.validate import validate_project

from .models import (
    ArtifactEntry,
    ArtifactInventory,
    AutonomyVerdict,
    CriticStatus,
    Diagnosis,
    GateInventory,
    QAStatus,
)
from .staleness import detect_staleness
from .waiver import load_waivers, is_waived


# ── Critic hard-mode allowlist ────────────────────────────────────────────────
# Only checks in this set can trigger a hard-mode render block.
# Evidence requirement: ≥5 BLOCK findings across ≥5 projects before adding.
# Current selection: asset_overreuse (6 BLOCKs / 9 projects),
#                    visual_novelty (7 BLOCKs / 9 projects).
CRITIC_HARD_ALLOWLIST: frozenset[str] = frozenset({
    "asset_overreuse",
    "visual_novelty",
})


# ── Gate knowledge ────────────────────────────────────────────────────────────

# Gates that require a human to review/approve before they can be set.
HUMAN_GATES: set[str] = {
    "brief_approved",
    "script_approved",
    "visual_assignment_approved",
    "technical_planning_approved",
    "motion_intent_reviewed",
    "preview_passed",
}

# Gates set automatically by code/Claude pipelines.
AUTO_GATES: set[str] = {
    "theme_set",
    "reconciliation_resolved",
    "asset_fitness_passed",
    "assets_validated",
    "qa_passed",
}

# For each gate: (action_description, actor, command_hint)
GATE_NEXT_ACTION: dict[str, tuple[str, str, str]] = {
    "brief_approved": (
        "Review brief.md — approve the creative direction",
        "human",
        "Say 'approve the brief' in conversation",
    ),
    "theme_set": (
        "Run theme-factory to select brand colors and set theme in project.json",
        "claude",
        "/theme-factory  (or: in conversation invoke the theme-factory skill)",
    ),
    "script_approved": (
        "Review script.md — approve narration for voice generation",
        "human",
        "Say 'script approved' in conversation",
    ),
    "reconciliation_resolved": (
        "Run script-reconcile to compare approved script against actual audio transcript",
        "claude",
        "In conversation: /script-reconcile",
    ),
    "visual_assignment_approved": (
        "Review shot-list.md Phase 4b-i visual assignments and approve",
        "human",
        "Review shot-list.md Phase 4b-i section then say 'visual assignment approved'",
    ),
    "asset_fitness_passed": (
        "Run shot-list Phase 4b-ii — component mapping and asset fitness audit",
        "claude",
        "In conversation: continue shot-list Phase 4b-ii",
    ),
    "technical_planning_approved": (
        "Review shot-list Phase 4b-iii technical plan (zoom coords, SFX, backgrounds) and approve",
        "human",
        "Review shot-list.md Phase 4b-iii section then say 'technical plan approved'",
    ),
    "motion_intent_reviewed": (
        "Review output/motion-intent.md and confirm motion direction",
        "human",
        "Review output/motion-intent.md then say 'motion intent reviewed'",
    ),
    "assets_validated": (
        "Run asset-prep — encode and validate all assets for Remotion",
        "claude",
        "In conversation: /asset-prep",
    ),
    "preview_passed": (
        "Quick preview: open Remotion Studio, scrub 5 key frames, confirm structure",
        "human",
        "cd remotion && npx remotion studio  (then say 'preview passed')",
    ),
    "qa_passed": (
        "Run QA — all 23 checks must pass before render",
        "code",
        "PYTHONPATH=. python -m lib.qa.cli projects/<slug>",
    ),
}

# Artifacts expected to exist once a given gate is passed.
GATE_TO_ARTIFACTS: dict[str, list[str]] = {
    "brief_approved":              ["brief.md"],
    "theme_set":                   [],
    "script_approved":             ["script.md"],
    "reconciliation_resolved":     ["audio/reconciliation.md"],
    "visual_assignment_approved":  ["shot-list.md"],
    "asset_fitness_passed":        ["shot-list.md"],
    "technical_planning_approved": ["shot-list.md"],
    "motion_intent_reviewed":      ["output/motion-intent.md"],
    "assets_validated":            [],          # remotion/public/ contents vary
    "preview_passed":              ["output/timeline.json"],
    "qa_passed":                   ["output/qa-report.md"],
}

# All key artifacts the brain checks, regardless of gates.
KEY_ARTIFACTS: list[str] = [
    "brief.md",
    "script.md",
    "audio/beat-map.json",
    "audio/captions.json",
    "audio/source.wav",
    "audio/reconciliation.md",
    "shot-list.md",
    "output/motion-intent.md",
    "output/timeline.json",
    "output/qa-report.md",
    "output/qa_report.json",
    "output/critic-report.json",
    "output/edit-plan.json",
]

# STALE_PAIRS removed — replaced by lib.brain.artifacts.DEPENDENCY_MAP
# and lib.brain.staleness.detect_staleness (Phase 2).


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_json_safe(path: Path) -> dict | None:
    """Load JSON from path; return None on any error."""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _mtime(path: Path) -> float:
    """Return mtime as float; 0.0 if file doesn't exist."""
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _artifact_entry(project_dir: Path, rel: str) -> ArtifactEntry:
    full = project_dir / rel
    exists = full.exists() and full.is_file()
    size = full.stat().st_size if exists else 0
    return ArtifactEntry(path=rel, present=exists, size_bytes=size)


# ── Gate inventory ────────────────────────────────────────────────────────────

def _build_gate_inventory(gates_passed_raw: list) -> GateInventory:
    passed_set = set(gates_passed_raw)
    passed = [g for g in GATE_ORDER if g in passed_set]
    missing = [g for g in GATE_ORDER if g not in passed_set]
    unknown = [g for g in gates_passed_raw if g not in VALID_GATE_IDS]
    next_required = missing[0] if missing else None
    return GateInventory(
        passed=passed,
        missing=missing,
        next_required=next_required,
        unknown_gates=unknown,
        total=len(GATE_ORDER),
    )


# ── Artifact inventory ────────────────────────────────────────────────────────

def _build_artifact_inventory(project_dir: Path, gates_passed: list[str]) -> ArtifactInventory:
    passed_set = set(gates_passed)
    entries = [_artifact_entry(project_dir, rel) for rel in KEY_ARTIFACTS]

    # Gate–artifact mismatches: gate set but expected file missing
    mismatches: list[str] = []
    for gate_id, artifacts in GATE_TO_ARTIFACTS.items():
        if gate_id in passed_set:
            for rel in artifacts:
                full = project_dir / rel
                if not full.exists():
                    mismatches.append(
                        f"Gate '{gate_id}' is set but '{rel}' is missing"
                    )

    # Phase 2: structured staleness detection via dependency map
    staleness_results = detect_staleness(project_dir)

    # Back-compat: human-readable summary from structured results
    stale_hints = [
        f"[{r.confidence}] '{r.upstream}' is newer than '{r.downstream}' "
        f"by {r.age_delta_seconds:.0f}s — {r.reason.split('.')[0]}"
        for r in staleness_results
    ]

    return ArtifactInventory(
        entries=entries,
        gate_artifact_mismatches=mismatches,
        stale_hints=stale_hints,
        staleness_results=staleness_results,
    )


# ── QA status ─────────────────────────────────────────────────────────────────

def _build_qa_status(project_dir: Path) -> QAStatus:
    report_path = project_dir / "output" / "qa_report.json"
    data = _load_json_safe(report_path)

    if data is None:
        # Try the markdown report as a presence signal only
        md_path = project_dir / "output" / "qa-report.md"
        if md_path.exists():
            return QAStatus(
                available=True,
                verdict="unknown",
                blockers=0,
                warnings=0,
                top_blockers=["qa_report.json not found — only qa-report.md present; run QA again to get structured data"],
                report_timestamp="",
            )
        return QAStatus(
            available=False,
            verdict="not_run",
            blockers=0,
            warnings=0,
            top_blockers=[],
            report_timestamp="",
        )

    verdict = data.get("verdict", "unknown")
    findings = data.get("findings", [])
    blockers = [f for f in findings if f.get("severity") == "block"]
    warnings = [f for f in findings if f.get("severity") == "warn"]

    top_blockers = [
        f"{f.get('gate', '?')} @ {f.get('location', '?')}: {f.get('message', '?')}"
        for f in blockers[:3]
    ]

    return QAStatus(
        available=True,
        verdict=verdict,
        blockers=len(blockers),
        warnings=len(warnings),
        top_blockers=top_blockers,
        report_timestamp=data.get("timestamp", ""),
    )


# ── Critic status ─────────────────────────────────────────────────────────────

def _build_critic_status(project_dir: Path) -> CriticStatus:
    report_path = project_dir / "output" / "critic-report.json"
    data = _load_json_safe(report_path)

    if data is None:
        return CriticStatus(
            available=False,
            status="not_run",
            findings_count=0,
            highest_severity="none",
            top_findings=[],
        )

    critic_status = data.get("critic_status", "unknown")

    # Collect findings from their actual locations in the report structure.
    # runner.py stores beat-scoped findings in beats[i]["findings"] and global
    # findings in "global_findings" — NOT in a top-level "findings" key.
    all_findings: list[dict] = []
    for beat in data.get("beats", []):
        all_findings.extend(beat.get("findings", []))
    all_findings.extend(data.get("global_findings", []))

    # Runner uses uppercase severity ("BLOCK", "WARN", "SUGGEST").
    sev_rank = {"BLOCK": 2, "WARN": 1, "SUGGEST": 0}
    highest_rank = -1
    highest = "none"
    for f in all_findings:
        s = f.get("severity", "SUGGEST").upper()
        rank = sev_rank.get(s, 0)
        if rank > highest_rank:
            highest_rank = rank
            highest = s.lower()  # normalize to lowercase for display compat

    top_findings = [
        f"{f.get('check', '?')}: {f.get('reason', '?')}"
        for f in all_findings[:3]
    ]

    # Phase 5 — compute hard-blocked state.
    # Hard-blocked only when ALL three conditions hold for a finding:
    #   1. severity == BLOCK
    #   2. check is in CRITIC_HARD_ALLOWLIST
    #   3. finding is not waived by critic_waivers.json
    waivers = load_waivers(project_dir)
    hard_blocked_findings = [
        f for f in all_findings
        if f.get("severity", "").upper() == "BLOCK"
        and f.get("check", "") in CRITIC_HARD_ALLOWLIST
        and not is_waived(f, waivers)
    ]
    applied_waivers = [
        w for w in waivers
        if any(f.get("check", "") == w.get("critic_id", "") for f in all_findings)
    ]

    return CriticStatus(
        available=True,
        status=critic_status,
        findings_count=len(all_findings),
        highest_severity=highest,
        top_findings=top_findings,
        findings=all_findings,
        hard_blocked=len(hard_blocked_findings) > 0,
        hard_blocked_findings=hard_blocked_findings,
        applied_waivers=applied_waivers,
    )


# ── Autonomy verdict ──────────────────────────────────────────────────────────

def _build_autonomy_verdict(
    gates: GateInventory,
    qa: QAStatus,
    validation_errors: list[str],
    critic: CriticStatus | None = None,
    critic_hard_mode: bool = False,
) -> AutonomyVerdict:
    # No project.json → cannot assess
    if not gates.passed and not gates.missing:
        return AutonomyVerdict(
            can_continue_autonomously=False,
            human_required=False,
            human_required_reason="",
            next_action="Cannot determine — project.json is missing or unreadable",
            next_action_actor="unknown",
            next_action_command="",
            confidence="low",
        )

    # Validation errors block everything
    if validation_errors:
        return AutonomyVerdict(
            can_continue_autonomously=False,
            human_required=False,
            human_required_reason="",
            next_action=f"Fix {len(validation_errors)} project.json validation error(s) first",
            next_action_actor="human",
            next_action_command="PYTHONPATH=. python -m lib.validate projects/<slug>",
            confidence="high",
        )

    # All gates passed → check blockers in priority order
    if gates.next_required is None:
        if qa.available and qa.verdict == "FAIL":
            return AutonomyVerdict(
                can_continue_autonomously=False,
                human_required=False,
                human_required_reason="",
                next_action=f"Fix {qa.blockers} QA blocker(s) then re-run QA",
                next_action_actor="code+claude",
                next_action_command="PYTHONPATH=. python -m lib.qa.cli projects/<slug>",
                confidence="high",
            )

        # Hard mode: only allowlisted BLOCK findings (after waivers) prevent render.
        # critic.hard_blocked is computed by _build_critic_status — advisory mode
        # (critic_hard_mode=False) never sets hard_blocked=True, so this branch
        # can only fire when --critic-hard-mode is explicitly passed.
        if (critic_hard_mode
                and critic is not None
                and critic.available
                and critic.hard_blocked):
            hbf = critic.hard_blocked_findings
            if hbf:
                unique_checks = ", ".join(sorted({f.get("check", "?") for f in hbf}))
                findings_msg = (
                    f"{len(hbf)} allowlisted BLOCK finding(s) ({unique_checks})"
                )
            else:
                findings_msg = (
                    f"{critic.findings_count} finding(s) "
                    f"(highest: {critic.highest_severity})"
                )
            return AutonomyVerdict(
                can_continue_autonomously=False,
                human_required=False,
                human_required_reason="",
                next_action=(
                    f"Critic hard-blocked — {findings_msg}. "
                    f"Resolve or waive in critic_waivers.json before render "
                    f"(--critic-hard-mode is active)."
                ),
                next_action_actor="claude",
                next_action_command="PYTHONPATH=. python -m lib.critic projects/<slug>",
                confidence="high",
            )

        return AutonomyVerdict(
            can_continue_autonomously=True,
            human_required=False,
            human_required_reason="",
            next_action="All gates passed — ready to render",
            next_action_actor="code",
            next_action_command="cd remotion && npx remotion render ReelComposition --output out/reel.mp4",
            confidence="high",
        )

    next_gate = gates.next_required
    action_info = GATE_NEXT_ACTION.get(
        next_gate,
        (f"Advance to gate '{next_gate}'", "unknown", ""),
    )
    action_desc, actor, command = action_info

    is_human = next_gate in HUMAN_GATES
    is_auto = next_gate in AUTO_GATES

    # If QA already ran and failed, override with QA fix action
    if qa.available and qa.verdict == "FAIL" and next_gate == "qa_passed":
        return AutonomyVerdict(
            can_continue_autonomously=False,
            human_required=False,
            human_required_reason="",
            next_action=f"Fix {qa.blockers} QA blocker(s): " + "; ".join(qa.top_blockers[:2]),
            next_action_actor="claude",
            next_action_command="PYTHONPATH=. python -m lib.qa.cli projects/<slug>",
            confidence="high",
        )

    return AutonomyVerdict(
        can_continue_autonomously=is_auto and not is_human,
        human_required=is_human,
        human_required_reason=(
            f"Gate '{next_gate}' requires human review before it can be set"
            if is_human else ""
        ),
        next_action=action_desc,
        next_action_actor=actor,
        next_action_command=command,
        confidence="high" if (is_human or is_auto) else "medium",
    )


# ── Main entry point ──────────────────────────────────────────────────────────

def diagnose_project(project_dir: Path, critic_hard_mode: bool = False) -> Diagnosis:
    """
    Inspect a project directory and return a complete read-only Diagnosis.

    Never mutates any file. All signals are read from existing artifacts.
    Returns a Diagnosis with `project_json_found=False` when project.json
    is absent — the caller decides how to present that.
    """
    now = datetime.now(timezone.utc).isoformat()
    project_dir = Path(project_dir).resolve()

    # ── Load project.json ─────────────────────────────────────────────────────
    pj_path = project_dir / "project.json"
    project = _load_json_safe(pj_path)

    if project is None:
        # Minimal shell — can still report what's on disk
        empty_gates = GateInventory(
            passed=[], missing=list(GATE_ORDER),
            next_required=GATE_ORDER[0] if GATE_ORDER else None,
            unknown_gates=[], total=len(GATE_ORDER),
        )
        return Diagnosis(
            slug=project_dir.name,
            title="",
            project_dir=str(project_dir),
            project_json_found=False,
            schema_version=None,
            schema_ok=False,
            phase="unknown",
            status="unknown",
            style="unknown",
            theme="unknown",
            theme_primary="",
            validation_errors=["project.json not found or unreadable"],
            gates=empty_gates,
            artifacts=_build_artifact_inventory(project_dir, []),
            qa=_build_qa_status(project_dir),
            critic=_build_critic_status(project_dir),
            autonomy=_build_autonomy_verdict(
                empty_gates,
                _build_qa_status(project_dir),
                ["project.json missing"],
                critic=_build_critic_status(project_dir),
                critic_hard_mode=critic_hard_mode,
            ),
            critic_hard_mode=critic_hard_mode,
            diagnosis_timestamp=now,
        )

    # ── Validate project.json ─────────────────────────────────────────────────
    validation_errors = [str(e) for e in validate_project(project)]

    schema_version = project.get("schema_version")
    schema_ok = (
        isinstance(schema_version, int)
        and schema_version == CURRENT_SCHEMA_VERSION
    )

    # ── Build sub-models ──────────────────────────────────────────────────────
    gates_passed_raw = project.get("gates_passed", [])
    gates = _build_gate_inventory(gates_passed_raw)
    artifacts = _build_artifact_inventory(project_dir, gates_passed_raw)
    qa = _build_qa_status(project_dir)
    critic = _build_critic_status(project_dir)
    autonomy = _build_autonomy_verdict(
        gates, qa, validation_errors,
        critic=critic,
        critic_hard_mode=critic_hard_mode,
    )

    return Diagnosis(
        slug=project.get("slug", project_dir.name),
        title=project.get("title", ""),
        project_dir=str(project_dir),
        project_json_found=True,
        schema_version=schema_version,
        schema_ok=schema_ok,
        phase=project.get("phase", "unknown"),
        status=project.get("status", "unknown"),
        style=project.get("style", "unknown"),
        theme=project.get("theme", ""),
        theme_primary=project.get("theme_primary", ""),
        validation_errors=validation_errors,
        gates=gates,
        artifacts=artifacts,
        qa=qa,
        critic=critic,
        autonomy=autonomy,
        critic_hard_mode=critic_hard_mode,
        diagnosis_timestamp=now,
    )
