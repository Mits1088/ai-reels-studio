"""
lib.brain.repair — Structured repair plan generation from a Diagnosis.

Read-only. Branches on every failure mode the brain can detect and produces
a prioritised, actor-labelled list of steps to resolve them.

Never mutates any file. The caller (autonomous-reel, CLI) decides which
steps to actually execute after presenting the plan to the user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .diagnose import diagnose_project
from .models import Diagnosis


# ── Data model ─────────────────────────────────────────────────────────────

@dataclass
class RepairStep:
    """One concrete step in a repair sequence."""
    order: int
    actor: Literal["code", "claude", "human"]
    description: str
    command: str                  # runnable command or empty string
    gate_target: str | None       # gate this step is trying to set
    why: str                      # reason this step is needed
    files_to_inspect: list[str] = field(default_factory=list)
    specialist_agent: str | None = None   # agent best suited for this step
    critic_id: str | None = None          # finding_id from the critic report (Phase 2)
    severity: str | None = None           # BLOCK / WARN / SUGGEST (Phase 2)

    def to_dict(self) -> dict:
        return {
            "order": self.order,
            "actor": self.actor,
            "description": self.description,
            "command": self.command,
            "gate_target": self.gate_target,
            "why": self.why,
            "files_to_inspect": self.files_to_inspect,
            "specialist_agent": self.specialist_agent,
            "critic_id": self.critic_id,
            "severity": self.severity,
        }


@dataclass
class RepairPlan:
    """Complete repair plan produced for a blocked or unhealthy project."""
    project_slug: str
    status: Literal["healthy", "blocked", "human_required", "unknown"]
    blocked_reason: str
    steps: list[RepairStep]
    estimated_human_touchpoints: int
    confidence: Literal["high", "medium", "low"] = "high"
    notes: str = ""
    specialist_agents: list[str] = field(default_factory=list)
    critic_mode: str = "advisory"   # "advisory" | "hard" — kept for Phase 2 compat

    # Backward-compat alias so callers that read .slug still work
    @property
    def slug(self) -> str:
        return self.project_slug

    def to_dict(self) -> dict:
        return {
            "project_slug": self.project_slug,
            "status": self.status,
            "blocked_reason": self.blocked_reason,
            "steps": [s.to_dict() for s in self.steps],
            "estimated_human_touchpoints": self.estimated_human_touchpoints,
            "confidence": self.confidence,
            "notes": self.notes,
            "specialist_agents": self.specialist_agents,
            "critic_mode": self.critic_mode,
        }

    def render(self) -> str:
        """Format for terminal output."""
        status_icons = {
            "healthy": "✓",
            "blocked": "✗",
            "human_required": "⏸",
            "unknown": "?",
        }
        icon = status_icons.get(self.status, "?")
        lines = [
            "🔧  REPAIR PLAN",
            "",
            f"  Project  : {self.project_slug}",
            f"  Status   : {icon} {self.status}",
            f"  Blocker  : {self.blocked_reason}",
            f"  Confidence: {self.confidence}",
            f"  Human touchpoints: {self.estimated_human_touchpoints}",
        ]

        if self.notes:
            lines.append(f"  Notes    : {self.notes}")

        if self.critic_mode == "advisory":
            lines.append(
                "  Critic mode: advisory "
                "(critic findings do not block — use --critic-hard-mode to enforce)"
            )
        else:
            lines.append("  Critic mode: hard (critic_blocked is a render blocker)")

        if self.specialist_agents:
            agents_str = ", ".join(self.specialist_agents)
            lines.append(f"  Suggested agents: {agents_str}")

        lines.append("")

        if not self.steps:
            lines.append("  No specific repair steps — project appears healthy.")
        else:
            lines.append("  Steps to resolve:")
            for s in self.steps:
                badge = f"[{s.actor}]"
                agent_tag = f"  [agent: {s.specialist_agent}]" if s.specialist_agent else ""
                lines.append(f"    {s.order}. {badge} {s.description}{agent_tag}")
                if s.command:
                    lines.append(f"       Run: {s.command}")
                if s.why:
                    lines.append(f"       Why: {s.why}")
                if s.files_to_inspect:
                    lines.append(f"       Inspect: {', '.join(s.files_to_inspect)}")
                lines.append("")

        if self.status != "healthy":
            lines.append("  Waiting for your approval to proceed.")
        return "\n".join(lines)


# ── Main entry points ──────────────────────────────────────────────────────

def repair_project(
    project_dir: Path,
    critic_hard_mode: bool = False,
    include_critic: bool = False,
) -> RepairPlan:
    """Diagnose project_dir and generate a repair plan."""
    project_dir = Path(project_dir).resolve()
    diag = diagnose_project(project_dir, critic_hard_mode=critic_hard_mode)
    return generate_repair_plan(
        diag, critic_hard_mode=critic_hard_mode, include_critic=include_critic
    )


def generate_repair_plan(
    diagnosis: Diagnosis,
    critic_hard_mode: bool = False,
    include_critic: bool = False,
) -> RepairPlan:
    """
    Build a repair plan from a completed Diagnosis.

    Priority order:
      1. Validation errors (block everything else)
      2. Gate–artifact mismatches (gate claimed but output missing)
      3. QA failures (blockers from qa_report.json)
      4. Critic blocked (creative revision needed)
      5. High-confidence staleness signals
      6. Fallback: manual investigation

    Status assignment:
      healthy        — project is healthy, no steps needed
      blocked        — at least one hard blocker identified
      human_required — next action requires human approval
      unknown        — no specific cause found
    """
    d = diagnosis
    steps: list[RepairStep] = []
    order = 1
    specialist_agents: list[str] = []

    # ── Priority 1: Validation errors ─────────────────────────────────────
    if d.validation_errors:
        steps.append(RepairStep(
            order=order,
            actor="human",
            description=(
                f"Fix {len(d.validation_errors)} project.json validation error(s)"
            ),
            command=f"PYTHONPATH=. python -m lib.validate projects/{d.slug}",
            gate_target=None,
            why=(
                "Validation errors block all downstream phases — "
                "every other repair step depends on a valid project.json."
            ),
            files_to_inspect=["project.json"],
            specialist_agent=None,
        ))
        order += 1
        for err in d.validation_errors[:3]:
            steps.append(RepairStep(
                order=order,
                actor="human",
                description=f"  ↳ {err}",
                command="",
                gate_target=None,
                why="",
                files_to_inspect=[],
            ))
            order += 1
        if len(d.validation_errors) > 3:
            steps.append(RepairStep(
                order=order,
                actor="human",
                description=(
                    f"  ↳ … and {len(d.validation_errors) - 3} more "
                    "(run validate for full list)"
                ),
                command="",
                gate_target=None,
                why="",
                files_to_inspect=[],
            ))
            order += 1

    # ── Priority 2: Gate–artifact mismatches ──────────────────────────────
    for mismatch in d.artifacts.gate_artifact_mismatches:
        gate_id = _extract_gate_id(mismatch)
        missing_file = _extract_missing_file(mismatch)
        hint = _GATE_PHASE_HINTS.get(gate_id, {})
        cmd = hint.get("command", "")
        files_to_inspect = ["project.json"]
        if missing_file:
            files_to_inspect.append(missing_file)

        agent: str | None = None
        if gate_id == "assets_validated":
            agent = "asset-auditor"
            if agent not in specialist_agents:
                specialist_agents.append(agent)
        elif gate_id == "preview_passed":
            agent = "timeline-critic"
            if agent not in specialist_agents:
                specialist_agents.append(agent)

        steps.append(RepairStep(
            order=order,
            actor="claude",
            description=f"Regenerate missing artifact for gate '{gate_id}'",
            command=cmd.replace("<slug>", d.slug),
            gate_target=gate_id,
            why=(
                f"Gate '{gate_id}' is set in project.json but its expected output "
                f"file is missing from disk. The phase must be re-run."
            ),
            files_to_inspect=files_to_inspect,
            specialist_agent=agent,
        ))
        order += 1

    # ── Priority 3: QA failures ────────────────────────────────────────────
    if d.qa.available and d.qa.verdict == "FAIL":
        if "qa-runner" not in specialist_agents:
            specialist_agents.append("qa-runner")
        steps.append(RepairStep(
            order=order,
            actor="claude",
            description=f"Fix {d.qa.blockers} QA blocker(s) then re-run QA",
            command=f"PYTHONPATH=. python -m lib.qa.cli projects/{d.slug}",
            gate_target="qa_passed",
            why=(
                "QA must pass before render. All BLOCK-severity findings "
                "must be resolved."
            ),
            files_to_inspect=[
                "output/qa_report.json",
                "output/qa-report.md",
                "output/timeline.json",
            ],
            specialist_agent="qa-runner",
        ))
        order += 1
        for blocker in d.qa.top_blockers:
            steps.append(RepairStep(
                order=order,
                actor="claude",
                description=f"  ↳ {blocker}",
                command="",
                gate_target=None,
                why="",
                files_to_inspect=[],
            ))
            order += 1
        if d.qa.blockers > 3:
            steps.append(RepairStep(
                order=order,
                actor="claude",
                description=(
                    f"  ↳ … and {d.qa.blockers - 3} more "
                    "(run qa.cli for full list)"
                ),
                command="",
                gate_target=None,
                why="",
                files_to_inspect=[],
            ))
            order += 1

    # ── Priority 4: Critic blocked ─────────────────────────────────────────
    if d.critic.available and d.critic.status == "critic_blocked" and d.critic.findings_count > 0:
        hard_blocked = getattr(d.critic, "hard_blocked", False)
        hbf = getattr(d.critic, "hard_blocked_findings", []) or []
        if critic_hard_mode and hard_blocked:
            hbf_count = len(hbf)
            label = (
                f"[BLOCKER] Resolve {hbf_count or d.critic.findings_count} "
                "hard-blocked critic finding(s) before render"
            )
            why = (
                "Allowlisted BLOCK findings (asset_overreuse, visual_novelty) are a render "
                "blocker when --critic-hard-mode is active. "
                "Fix path: read output/critic-report.json, revise the edit plan or shot list, "
                "then re-run `python -m lib.critic projects/<slug>` to clear the gate. "
                "Alternatively, add a documented waiver to critic_waivers.json."
            )
        elif critic_hard_mode:
            # Hard mode active but no allowlisted BLOCKs — still advisory
            label = (
                f"[advisory] Address {d.critic.findings_count} critic finding(s) "
                f"(highest: {d.critic.highest_severity}) — not in hard-block allowlist"
            )
            why = (
                "Critic findings are advisory even in hard mode when they are not in the "
                "BLOCK allowlist (asset_overreuse, visual_novelty). Advancement is not blocked. "
                "Fix path: read output/critic-report.json, revise the edit plan or shot list."
            )
        else:
            label = (
                f"[advisory] Address {d.critic.findings_count} critic finding(s) "
                f"(highest: {d.critic.highest_severity}) — does not block advancement"
            )
            why = (
                "Critic findings are advisory in default mode. Advancement is not blocked. "
                "Fix path: read output/critic-report.json, revise the edit plan or shot list. "
                "Run with --critic-hard-mode to enforce allowlisted findings as a render blocker."
            )
        steps.append(RepairStep(
            order=order,
            actor="claude",
            description=label,
            command=f"PYTHONPATH=. python -m lib.critic projects/{d.slug}",
            gate_target=None,
            why=why,
            files_to_inspect=["output/critic-report.json", "output/edit-plan.json"],
            specialist_agent="creative-critic",
        ))
        order += 1

        # include_critic=True → structured per-finding steps with critic_id and severity.
        # Default (False) → string sub-steps from top_findings for backward compat.
        structured = getattr(d.critic, "findings", []) or []
        if include_critic and structured:
            for f in structured:
                check = f.get("check", "unknown")
                finding_id = f.get("finding_id", check)
                sev = f.get("severity", "")
                reason = f.get("reason", "")
                suggested_fix = f.get("suggested_fix", "")
                agent = _critic_specialist(check)
                if agent not in specialist_agents:
                    specialist_agents.append(agent)
                steps.append(RepairStep(
                    order=order,
                    actor="claude",
                    description=f"  ↳ [{sev}] {check}: {reason}",
                    command="",
                    gate_target=None,
                    why=suggested_fix,
                    files_to_inspect=["output/critic-report.json"],
                    specialist_agent=agent,
                    critic_id=finding_id,
                    severity=sev,
                ))
                order += 1
        else:
            for finding in d.critic.top_findings:
                steps.append(RepairStep(
                    order=order,
                    actor="claude",
                    description=f"  ↳ {finding}",
                    command="",
                    gate_target=None,
                    why="",
                    files_to_inspect=[],
                ))
                order += 1

    # ── Priority 5: High-confidence staleness ─────────────────────────────
    high_stale = [
        r for r in d.artifacts.staleness_results if r.confidence == "high"
    ]
    for r in high_stale:
        delta_s = int(r.age_delta_seconds)
        agent = None
        if "timeline" in r.downstream:
            agent = "timeline-critic"
            if agent not in specialist_agents:
                specialist_agents.append(agent)
        steps.append(RepairStep(
            order=order,
            actor="claude",
            description=(
                f"Regenerate '{r.downstream}' — stale by {delta_s}s "
                f"('{r.upstream}' changed)"
            ),
            command=f"# {r.recommended_action}",
            gate_target=None,
            why=r.reason,
            files_to_inspect=[r.upstream, r.downstream],
            specialist_agent=agent,
        ))
        order += 1

    # ── Status, confidence, blocked_reason ────────────────────────────────
    if d.healthy and not steps:
        status: str = "healthy"
        confidence: str = "high"
        blocked_reason = "Project is healthy — no repair needed."
        notes = "All gates passed, QA passing, no staleness signals."
    elif d.autonomy.human_required:
        status = "human_required"
        confidence = "high"
        blocked_reason = (
            d.autonomy.human_required_reason or d.autonomy.next_action or
            "Human approval required"
        )
        notes = (
            f"Next gate: {d.gates.next_required}. "
            "Awaiting manual approval before pipeline can continue."
        )
    elif d.validation_errors:
        status = "blocked"
        confidence = "high"
        blocked_reason = (
            f"{len(d.validation_errors)} validation error(s) in project.json"
        )
        notes = "Fix project.json before any other step can run."
    elif d.artifacts.gate_artifact_mismatches:
        status = "blocked"
        confidence = "high"
        blocked_reason = (
            f"{len(d.artifacts.gate_artifact_mismatches)} gate-artifact mismatch(es)"
        )
        notes = "Gates are set but expected output files are missing — re-run phases."
    elif d.qa.available and d.qa.verdict == "FAIL":
        status = "blocked"
        confidence = "high"
        blocked_reason = f"QA FAIL — {d.qa.blockers} blocker(s)"
        notes = "Resolve all QA blockers before render."
    elif d.critic.available and d.critic.status == "critic_blocked":
        _hard_blocked = getattr(d.critic, "hard_blocked", False)
        status = "blocked" if (critic_hard_mode and _hard_blocked) else "unknown"
        confidence = "medium"
        blocked_reason = (
            f"Critic blocked — {d.critic.findings_count} finding(s)"
        )
        notes = (
            "Critic findings are advisory unless --critic-hard-mode is set "
            "and allowlisted BLOCK findings (asset_overreuse, visual_novelty) are present."
            if not (critic_hard_mode and _hard_blocked)
            else "Allowlisted BLOCK findings block render in hard mode."
        )
    elif high_stale:
        status = "blocked"
        confidence = "medium"
        blocked_reason = (
            f"{len(high_stale)} high-confidence staleness signal(s)"
        )
        notes = "Downstream artifacts are out of date relative to their sources."
    elif not steps:
        # Fallback: no cause found, generate a generic investigation step
        steps.append(RepairStep(
            order=1,
            actor="human",
            description="Run full project validation to identify the root cause",
            command=f"PYTHONPATH=. python -m lib.validate projects/{d.slug}",
            gate_target=None,
            why=(
                "No specific failure mode was identified from the current "
                "diagnosis — full validation output may reveal the cause."
            ),
            files_to_inspect=["project.json"],
        ))
        status = "unknown"
        confidence = "low"
        blocked_reason = d.autonomy.next_action or "unknown — no specific cause identified"
        notes = "Run validate and diagnose to gather more information."
    else:
        status = "unknown"
        confidence = "low"
        blocked_reason = d.autonomy.next_action or "unknown — no specific cause identified"
        notes = ""

    # ── Human touchpoints ─────────────────────────────────────────────────
    human_steps = sum(
        1 for s in steps
        if s.actor == "human" and not s.description.startswith(" ")
    )

    return RepairPlan(
        project_slug=d.slug,
        status=status,
        blocked_reason=blocked_reason,
        steps=steps,
        estimated_human_touchpoints=human_steps,
        confidence=confidence,
        notes=notes,
        specialist_agents=specialist_agents,
        critic_mode="hard" if critic_hard_mode else "advisory",
    )


# ── Helpers ────────────────────────────────────────────────────────────────

def _extract_gate_id(mismatch_msg: str) -> str:
    """Extract gate_id from 'Gate 'X' is set but 'Y' is missing'."""
    try:
        start = mismatch_msg.index("'") + 1
        end = mismatch_msg.index("'", start)
        return mismatch_msg[start:end]
    except ValueError:
        return "unknown"


def _extract_missing_file(mismatch_msg: str) -> str | None:
    """Extract missing file path from 'Gate 'X' is set but 'Y' is missing'."""
    try:
        first_end = mismatch_msg.index("'") + 1
        mismatch_msg.index("'", first_end)
        second_start_search = mismatch_msg.index("'", first_end) + 1
        second_start = mismatch_msg.index("'", second_start_search) + 1
        second_end = mismatch_msg.index("'", second_start)
        return mismatch_msg[second_start:second_end]
    except ValueError:
        return None


def _critic_specialist(check: str) -> str:
    """Return the specialist agent best suited to address a given critic check."""
    mapping = {
        "claim_to_proof_latency": "qa-runner",
        "dead_holds": "timeline-critic",
        "asset_overreuse": "asset-auditor",
        "proof_relevance": "asset-auditor",
        "caption_competition": "timeline-critic",
        "visual_novelty": "timeline-critic",
    }
    return mapping.get(check, "creative-critic")


# Maps each gate to the skill/command that regenerates its expected artifact.
_GATE_PHASE_HINTS: dict[str, dict[str, str]] = {
    "brief_approved": {
        "skill": "source-brief",
        "command": "node lib/capture/source-brief.js --url <url> --project <slug>",
    },
    "theme_set": {
        "skill": "theme-factory",
        "command": "In conversation: /theme-factory",
    },
    "script_approved": {
        "skill": "reel-script",
        "command": "In conversation: /reel-script",
    },
    "reconciliation_resolved": {
        "skill": "script-reconcile",
        "command": "In conversation: /script-reconcile",
    },
    "visual_assignment_approved": {
        "skill": "shot-list",
        "command": "In conversation: continue shot-list Phase 4b-i",
    },
    "asset_fitness_passed": {
        "skill": "shot-list",
        "command": "In conversation: continue shot-list Phase 4b-ii",
    },
    "technical_planning_approved": {
        "skill": "shot-list",
        "command": "In conversation: continue shot-list Phase 4b-iii",
    },
    "motion_intent_reviewed": {
        "skill": "motion-intent",
        "command": "In conversation: /motion-intent",
    },
    "assets_validated": {
        "skill": "asset-prep",
        "command": "In conversation: /asset-prep",
    },
    "preview_passed": {
        "skill": "assemble-reel",
        "command": "cd remotion && npx remotion studio",
    },
    "qa_passed": {
        "skill": "qa-reel",
        "command": "PYTHONPATH=. python -m lib.qa.cli projects/<slug>",
    },
}
