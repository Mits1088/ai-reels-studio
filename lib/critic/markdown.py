"""
Render a CriticReport as a human-readable critic-report.md document.

Phase E2 layout (high-signal first, data-gap notices last):
  1. Header (verdict, critic_status, totals)
  2. Top-line summary
     - Data quality limitations (one-line each)
     - Highest confidence blockers (top 5)
     - Root cause clusters (collapsed)
  3. Per-check counts table
  4. High-signal findings (BLOCK + WARN, beat-scoped first then global)
  5. Data-gap notices (SUGGEST level, collapsed at the end)
"""

from __future__ import annotations

from .runner import CriticReport, CRITIC_VERSION
from .finding import (
    CriticFinding,
    SEVERITY_BLOCK,
    SEVERITY_WARN,
    SEVERITY_SUGGEST,
)


_SEVERITY_ICON = {
    SEVERITY_BLOCK:   "[BLOCK]",
    SEVERITY_WARN:    "[WARN] ",
    SEVERITY_SUGGEST: "[hint] ",
}


def render_critic_markdown(report: CriticReport) -> str:
    lines: list[str] = []
    lines.append(f"# Critic Report: {report.project}")
    lines.append("")
    lines.append(f"**Critic version:** `{CRITIC_VERSION}`")
    lines.append(f"**Verdict:** `{report.verdict}` &nbsp; **Status:** `{report.critic_status}` _(Phase E2 — advisory only)_")
    lines.append(
        f"**Totals:** {report.pre_filter_blockers} blockers, "
        f"{report.pre_filter_warnings} warnings, "
        f"{report.pre_filter_suggestions} suggestions "
        f"({report.pre_filter_total} total)"
    )
    if report.severity_floor != SEVERITY_SUGGEST:
        lines.append(
            f"_Filtered to severity ≥ `{report.severity_floor}` — showing "
            f"{len(report.findings)}/{report.pre_filter_total} findings_"
        )
    inputs_present = ", ".join(
        f"{k}={'YES' if v else 'no'}" for k, v in sorted(report.inputs_present.items())
    )
    lines.append(f"**Inputs:** {inputs_present}")
    if report.enrichment_state:
        e = report.enrichment_state
        lines.append(
            f"**Enrichment:** full={e.get('full', 0)}, partial={e.get('partial', 0)}, "
            f"none={e.get('none', 0)} ({e.get('total', 0)} assets)"
        )
    lines.append("")

    # ── Top-line summary ──────────────────────────────────────────────────
    summary = _build_summary_dict(report)
    lines.append("## Summary")
    lines.append("")

    dql = summary["data_quality_limitations"]
    if dql:
        lines.append("**Data quality limitations:**")
        for note in dql:
            lines.append(f"- {note}")
        lines.append("")

    blockers = summary["highest_confidence_blockers"]
    if blockers:
        lines.append("**Highest-confidence blockers:**")
        for b in blockers:
            beat_str = f" ({b['beat_id']})" if b.get("beat_id") else " (global)"
            lines.append(
                f"- [BLOCK] `{b['check']}`{beat_str} — confidence {b['confidence']:.2f}"
            )
            lines.append(f"  - {b['reason']}")
        lines.append("")

    clusters = summary["root_cause_clusters"]
    if clusters:
        lines.append("**Root-cause clusters** _(findings linked by shared asset_id)_:")
        for c in clusters:
            lines.append(
                f"- `{c['cluster_id']}` — asset `{c['asset_id']}` "
                f"({len(c['finding_ids'])} findings, max severity `{c['max_severity']}`)"
            )
            lines.append(
                f"  - Checks: {', '.join('`' + ch + '`' for ch in c['checks_involved'])}"
            )
        lines.append("")

    if not (dql or blockers or clusters):
        lines.append("_No summary-level concerns._")
        lines.append("")

    # ── Per-check counts ──────────────────────────────────────────────────
    lines.append("## Checks")
    lines.append("")
    lines.append("| Check | Block | Warn | Suggest |")
    lines.append("|---|---|---|---|")
    per_check = report.per_check_totals()
    for name in sorted(per_check.keys()):
        b = per_check[name]
        lines.append(
            f"| `{name}` | {b['blockers']} | {b['warnings']} | {b['suggestions']} |"
        )
    lines.append("")

    # ── Split findings into high-signal vs data-gap ───────────────────────
    high_signal = [f for f in report.findings if f.severity != SEVERITY_SUGGEST]
    data_gap_findings = [
        f for f in report.findings
        if f.severity == SEVERITY_SUGGEST
        and f.evidence.get("catalog_enrichment_status") == "absent"
    ]
    other_suggestions = [
        f for f in report.findings
        if f.severity == SEVERITY_SUGGEST
        and f not in data_gap_findings
    ]

    # ── High-signal findings (per-beat first, then global) ────────────────
    if high_signal or other_suggestions:
        lines.append("## Findings")
        lines.append("")

        beat_findings: dict[str, list[CriticFinding]] = {}
        global_findings: list[CriticFinding] = []
        for f in high_signal + other_suggestions:
            if f.beat_id:
                beat_findings.setdefault(f.beat_id, []).append(f)
            else:
                global_findings.append(f)

        if beat_findings:
            lines.append("### Per-beat")
            lines.append("")
            for beat_id in sorted(beat_findings.keys()):
                lines.append(f"#### `{beat_id}`")
                lines.append("")
                for f in beat_findings[beat_id]:
                    _render_finding(f, lines)
                lines.append("")

        if global_findings:
            lines.append("### Global")
            lines.append("")
            for f in global_findings:
                _render_finding(f, lines)
            lines.append("")

    # ── Data-gap notices (collapsed at the end) ───────────────────────────
    if data_gap_findings:
        lines.append("## Data quality notices")
        lines.append("")
        lines.append(
            "_The following SUGGEST findings are caused by missing enrichment data, "
            "not by editorial problems. Run `python -m lib.capture.enrich projects/<slug>` "
            "to address them._"
        )
        lines.append("")
        for f in data_gap_findings:
            _render_finding(f, lines)
        lines.append("")

    if not report.findings:
        lines.append("_No findings — critic is silent._")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _build_summary_dict(report: CriticReport) -> dict:
    """Re-derive the summary section from the report (mirrors runner._build_*)."""
    from .runner import (
        _build_data_quality_limitations,
        _build_root_cause_clusters,
        _highest_confidence_blockers,
    )
    return {
        "data_quality_limitations": _build_data_quality_limitations(
            report.inputs_present, report.enrichment_state,
        ),
        "highest_confidence_blockers": _highest_confidence_blockers(report.findings),
        "root_cause_clusters": _build_root_cause_clusters(report.findings),
    }


def _render_finding(f: CriticFinding, lines: list[str]) -> None:
    icon = _SEVERITY_ICON.get(f.severity, f.severity)
    lines.append(
        f"- {icon} **`{f.check}`** (confidence {f.confidence:.2f})"
        + (f" `{f.finding_id}`" if f.finding_id else "")
    )
    lines.append(f"  - **Reason:** {f.reason}")
    if f.evidence:
        ev_keys = ", ".join(f"`{k}`={f.evidence[k]!r}" for k in list(f.evidence.keys())[:5])
        lines.append(f"  - **Evidence:** {ev_keys}")
    if f.related_ids:
        related = ", ".join(f"`{rid}`" for rid in f.related_ids[:5])
        lines.append(f"  - **Related:** {related}")
    lines.append(f"  - **Suggested fix:** {f.suggested_fix}")
