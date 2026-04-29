"""
lib.brain.sweep — Portfolio health scan across all active projects.

Walks projects/, runs diagnose_project() on each, and returns a sorted
summary table. Read-only — never mutates any project file.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .diagnose import diagnose_project


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class ProjectSummary:
    """Compact health snapshot for one project."""
    slug: str
    phase: str
    project_type: str         # reel / youtube / unknown
    gates_passed: int
    gates_total: int
    healthy: bool
    qa_status: str            # PASS / FAIL / not_run / ...
    critic_status: str        # critic_passed / critic_warnings / critic_blocked / not_run
    stale_count: int          # count of high-confidence staleness signals
    can_continue: bool        # brain says code can advance autonomously
    human_required: bool      # waiting for human approval gate
    recommended_action: str   # human-readable next step


# ── Main entry point ──────────────────────────────────────────────────────────

def sweep_projects(projects_dir: Path, critic_hard_mode: bool = False) -> list[ProjectSummary]:
    """
    Diagnose every project directory under projects_dir.

    Skips directories that start with '_' (shared, templates).
    Skips directories without a project.json.
    Silently swallows per-project exceptions so one broken project
    does not abort the sweep.

    Returns summaries sorted:
      1. Blocked (not healthy, not human_required, not can_continue) — need attention
      2. Human-required (waiting for approval)
      3. Stale / unhealthy (healthy=False or stale signals)
      4. Healthy (no action needed)
    """
    projects_dir = Path(projects_dir).resolve()
    summaries: list[ProjectSummary] = []

    candidates = sorted(
        p for p in projects_dir.iterdir()
        if p.is_dir() and not p.name.startswith("_")
    )

    for candidate in candidates:
        if not (candidate / "project.json").exists():
            continue
        try:
            d = diagnose_project(candidate, critic_hard_mode=critic_hard_mode)
        except Exception:
            continue

        stale_count = sum(
            1 for r in d.artifacts.staleness_results
            if r.confidence == "high"
        )

        summaries.append(ProjectSummary(
            slug=d.slug,
            phase=d.phase,
            project_type=getattr(d, "project_type", "reel"),
            gates_passed=len(d.gates.passed),
            gates_total=d.gates.total,
            healthy=d.healthy,
            qa_status=d.qa.verdict if d.qa.available else "not_run",
            critic_status=d.critic.status if d.critic.available else "not_run",
            stale_count=stale_count,
            can_continue=d.autonomy.can_continue_autonomously,
            human_required=d.autonomy.human_required,
            recommended_action=d.autonomy.next_action,
        ))

    summaries.sort(key=_sort_key)
    return summaries


def format_sweep_table(summaries: list[ProjectSummary]) -> str:
    """Render summaries as a compact console table."""
    if not summaries:
        return "No projects found."

    W = 82
    sep = "─" * W
    lines: list[str] = [sep]
    lines.append(
        f"  {'Project':<30}  {'Type':<8}  {'Phase':<14}  {'Gates':<7}  {'QA':<8}  Action"
    )
    lines.append(sep)

    # Group: reels first, then non-reel (youtube / unknown)
    reels    = [s for s in summaries if s.project_type == "reel"]
    non_reel = [s for s in summaries if s.project_type != "reel"]

    def _row(s: ProjectSummary) -> None:
        icon = _status_icon(s)
        type_str = _truncate(s.project_type, 8)
        gates_str = f"{s.gates_passed}/{s.gates_total}" if s.gates_total else "n/a"
        qa_str = _truncate(s.qa_status, 8)
        slug_str = _truncate(s.slug, 30)
        phase_str = _truncate(s.phase, 14)
        next_str = _truncate(s.recommended_action, 20)
        stale_tag = f"  ⚠×{s.stale_count}" if s.stale_count else ""
        lines.append(
            f"  {icon} {slug_str:<29}  {type_str:<8}  {phase_str:<14}  "
            f"{gates_str:<7}  {qa_str:<8}  {next_str}{stale_tag}"
        )

    for s in reels:
        _row(s)

    if non_reel:
        lines.append(f"  {'─'*78}")
        lines.append(f"  {'Non-reel projects (youtube / unknown):'}")
        for s in non_reel:
            _row(s)

    lines.append(sep)

    total = len(summaries)
    n_reel    = len(reels)
    n_youtube = sum(1 for s in summaries if s.project_type == "youtube")
    n_unknown = sum(1 for s in summaries if s.project_type == "unknown")
    n_advance = sum(1 for s in reels if s.can_continue)
    n_human   = sum(1 for s in reels if s.human_required)
    n_blocked = sum(
        1 for s in reels
        if not s.healthy and not s.human_required and not s.can_continue
    )
    n_done    = sum(
        1 for s in reels
        if not s.gates_total or s.gates_passed == s.gates_total
    )

    lines.append(
        f"  {total} project(s): {n_reel} reel  {n_youtube} youtube  {n_unknown} unknown"
    )
    lines.append(
        f"  Reels —  "
        f"▶ {n_advance} can advance   "
        f"⏸ {n_human} waiting   "
        f"✗ {n_blocked} blocked   "
        f"✓ {n_done} complete"
    )
    lines.append(sep)

    return "\n".join(lines)


def format_sweep_json(summaries: list[ProjectSummary]) -> str:
    """Render summaries as JSON array."""
    return json.dumps([asdict(s) for s in summaries], indent=2, ensure_ascii=False)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sort_key(s: ProjectSummary) -> tuple:
    """
    Non-reel projects (youtube / unknown) sort after all reel projects (tier 4).
    Among reels:
      Tier 0 — blocked: not healthy, not human_required, not can_continue, no stale signals
      Tier 1 — human_required: waiting for approval
      Tier 2 — stale/unhealthy: degraded but not hard-blocked (includes stale-only projects)
      Tier 3 — healthy: no action needed
    Within tier: more gates passed → later (more work done → lower priority)
    """
    if s.project_type != "reel":
        # Non-reel projects are grouped at the bottom, sorted by type then slug
        return (4, 0, s.project_type, s.slug)
    is_blocked = (
        not s.healthy and not s.human_required and not s.can_continue
        and s.stale_count == 0
    )
    if is_blocked:
        tier = 0
    elif s.human_required:
        tier = 1
    elif not s.healthy or s.stale_count > 0:
        tier = 2
    else:
        tier = 3
    return (tier, -s.gates_passed, "", s.slug)


def _status_icon(s: ProjectSummary) -> str:
    is_blocked = not s.healthy and not s.human_required and not s.can_continue
    if is_blocked:
        return "✗"
    if s.human_required:
        return "⏸"
    if s.can_continue:
        return "▶"
    if s.healthy and s.gates_passed == s.gates_total:
        return "✓"
    return "·"


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"
