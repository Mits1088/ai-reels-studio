"""
lib.analytics.reports — Pre-built SQL reports for the analytics database.

All functions return plain text suitable for printing to stdout.
Reports are read-only — they never modify the database.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .db import connect, DEFAULT_DB_PATH

# ── Helpers ───────────────────────────────────────────────────────────────────

def _pct(n: int, total: int) -> str:
    if total == 0:
        return "  0%"
    return f"{round(100 * n / total):3d}%"


def _bar(n: int, total: int, width: int = 20) -> str:
    filled = round(width * n / total) if total else 0
    return "█" * filled + "░" * (width - filled)


def _row_count(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


# ── report: projects ──────────────────────────────────────────────────────────

def report_projects(db_path: Path = DEFAULT_DB_PATH) -> str:
    conn = connect(db_path)
    lines: list[str] = []

    total = _row_count(conn, "projects")
    if total == 0:
        conn.close()
        return "No projects ingested yet. Run: python -m lib.analytics ingest-all"

    # ── Summary counts ────────────────────────────────────────────────────────
    healthy = conn.execute("SELECT COUNT(*) FROM projects WHERE healthy = 1").fetchone()[0]
    rendered = conn.execute("SELECT COUNT(*) FROM projects WHERE has_render = 1").fetchone()[0]

    lines.append("━" * 64)
    lines.append(f"  Projects overview  ({total} total)")
    lines.append("━" * 64)
    lines.append(f"  Healthy         {healthy:>3} / {total}  {_pct(healthy, total)}")
    lines.append(f"  Rendered        {rendered:>3} / {total}  {_pct(rendered, total)}")

    # ── Phase distribution ────────────────────────────────────────────────────
    phase_rows = conn.execute(
        "SELECT COALESCE(phase,'(none)') AS phase, COUNT(*) AS n "
        "FROM projects GROUP BY phase ORDER BY n DESC"
    ).fetchall()
    if phase_rows:
        lines.append("")
        lines.append("  Phase breakdown:")
        for row in phase_rows:
            bar = _bar(row["n"], total, width=16)
            lines.append(f"    {row['phase']:<28} {row['n']:>3}  {bar}")

    # ── Style distribution ────────────────────────────────────────────────────
    style_rows = conn.execute(
        "SELECT COALESCE(style,'(none)') AS style, COUNT(*) AS n "
        "FROM projects GROUP BY style ORDER BY n DESC"
    ).fetchall()
    if style_rows:
        lines.append("")
        lines.append("  Style breakdown:")
        for row in style_rows:
            lines.append(f"    {row['style']:<28} {row['n']:>3}")

    # ── QA verdict distribution ───────────────────────────────────────────────
    qa_rows = conn.execute(
        "SELECT COALESCE(qa_verdict,'(none)') AS verdict, COUNT(*) AS n "
        "FROM projects GROUP BY verdict ORDER BY n DESC"
    ).fetchall()
    if qa_rows:
        lines.append("")
        lines.append("  QA verdict:")
        for row in qa_rows:
            lines.append(f"    {row['verdict']:<28} {row['n']:>3}")

    # ── Gate completion distribution ─────────────────────────────────────────
    lines.append("")
    lines.append("  Gate completion (gates_passed / gates_total):")
    gate_rows = conn.execute(
        "SELECT gates_passed, gates_total, COUNT(*) AS n "
        "FROM projects GROUP BY gates_passed, gates_total ORDER BY gates_passed DESC"
    ).fetchall()
    for row in gate_rows:
        label = f"{row['gates_passed']:>2}/{row['gates_total']}"
        bar = _bar(row["gates_passed"], row["gates_total"], width=12)
        lines.append(f"    {label}  {bar}  {row['n']} project(s)")

    # ── Per-project table ─────────────────────────────────────────────────────
    lines.append("")
    lines.append(f"  {'Slug':<36} {'Phase':<14} {'Gates':<8} {'QA':<24} {'Render'}")
    lines.append("  " + "─" * 92)

    proj_rows = conn.execute(
        "SELECT slug, phase, gates_passed, gates_total, qa_verdict, has_render, healthy "
        "FROM projects ORDER BY ingested_at DESC"
    ).fetchall()
    for p in proj_rows:
        qa = (p["qa_verdict"] or "—")[:22]
        render = "✓" if p["has_render"] else "·"
        health = "●" if p["healthy"] else "○"
        gates = f"{p['gates_passed']}/{p['gates_total']}"
        phase = (p["phase"] or "—")[:13]
        lines.append(f"  {health} {p['slug']:<34} {phase:<14} {gates:<8} {qa:<24} {render}")

    lines.append("━" * 64)
    conn.close()
    return "\n".join(lines)


# ── report: qa ────────────────────────────────────────────────────────────────

def report_qa(db_path: Path = DEFAULT_DB_PATH) -> str:
    conn = connect(db_path)
    lines: list[str] = []

    total_projects = _row_count(conn, "projects")
    total_findings = _row_count(conn, "qa_findings")
    total_critic = _row_count(conn, "critic_findings")

    if total_projects == 0:
        conn.close()
        return "No projects ingested yet. Run: python -m lib.analytics ingest-all"

    lines.append("━" * 64)
    lines.append(f"  QA + Critic quality report  ({total_projects} projects)")
    lines.append("━" * 64)

    # ── QA summary ────────────────────────────────────────────────────────────
    qa_with_data = conn.execute(
        "SELECT COUNT(*) FROM projects WHERE qa_verdict != 'not_run'"
    ).fetchone()[0]
    qa_pass = conn.execute(
        "SELECT COUNT(*) FROM projects WHERE qa_verdict IN ('PASS','PASS_WITH_WARNINGS')"
    ).fetchone()[0]
    qa_fail = conn.execute(
        "SELECT COUNT(*) FROM projects WHERE qa_verdict = 'FAIL'"
    ).fetchone()[0]

    lines.append("")
    lines.append("  QA run status:")
    lines.append(f"    Projects with QA data   {qa_with_data:>3} / {total_projects}")
    lines.append(f"    PASS / PASS_WITH_WARNINGS  {qa_pass:>3}")
    lines.append(f"    FAIL                    {qa_fail:>3}")
    lines.append(f"    Total QA findings       {total_findings:>5}")

    # ── Most common QA gates blocked ─────────────────────────────────────────
    if total_findings > 0:
        top_gates = conn.execute(
            "SELECT COALESCE(gate,'(global)') AS gate, COUNT(*) AS n "
            "FROM qa_findings WHERE severity = 'block' "
            "GROUP BY gate ORDER BY n DESC LIMIT 10"
        ).fetchall()
        if top_gates:
            lines.append("")
            lines.append("  Most blocked QA gates:")
            for row in top_gates:
                lines.append(f"    {row['gate']:<38} {row['n']:>3} blocker(s)")

        # ── Common blocker messages ───────────────────────────────────────────
        top_messages = conn.execute(
            "SELECT message, COUNT(*) AS n "
            "FROM qa_findings WHERE severity = 'block' "
            "GROUP BY message ORDER BY n DESC LIMIT 5"
        ).fetchall()
        if top_messages:
            lines.append("")
            lines.append("  Most common blocker messages (top 5):")
            for row in top_messages:
                msg = row["message"][:68]
                lines.append(f"    ({row['n']:>2}x)  {msg}")

    # ── Critic summary ────────────────────────────────────────────────────────
    lines.append("")
    lines.append("  Critic status:")

    critic_rows = conn.execute(
        "SELECT COALESCE(critic_status,'not_run') AS status, COUNT(*) AS n "
        "FROM projects GROUP BY status ORDER BY n DESC"
    ).fetchall()
    for row in critic_rows:
        lines.append(f"    {row['status']:<30} {row['n']:>3}")

    lines.append(f"    Total critic findings   {total_critic:>5}")

    if total_critic > 0:
        sev_rows = conn.execute(
            "SELECT severity, COUNT(*) AS n FROM critic_findings "
            "GROUP BY severity ORDER BY n DESC"
        ).fetchall()
        if sev_rows:
            lines.append("")
            lines.append("  Critic finding severity breakdown:")
            for row in sev_rows:
                lines.append(f"    {row['severity']:<30} {row['n']:>5}")

        top_checks = conn.execute(
            "SELECT check_name, COUNT(*) AS n FROM critic_findings "
            "WHERE severity IN ('block','warn') "
            "GROUP BY check_name ORDER BY n DESC LIMIT 8"
        ).fetchall()
        if top_checks:
            lines.append("")
            lines.append("  Most common critic check failures (block/warn):")
            for row in top_checks:
                lines.append(f"    {row['check_name']:<40} {row['n']:>3}")

    # ── Staleness summary ─────────────────────────────────────────────────────
    stale_total = _row_count(conn, "staleness_signals")
    if stale_total > 0:
        lines.append("")
        lines.append(f"  Staleness signals: {stale_total} total")
        stale_high = conn.execute(
            "SELECT COUNT(*) FROM staleness_signals WHERE confidence = 'high'"
        ).fetchone()[0]
        lines.append(f"    High confidence  {stale_high:>3}")

        top_stale = conn.execute(
            "SELECT upstream, downstream, COUNT(*) AS n "
            "FROM staleness_signals WHERE confidence = 'high' "
            "GROUP BY upstream, downstream ORDER BY n DESC LIMIT 5"
        ).fetchall()
        if top_stale:
            lines.append("")
            lines.append("  Most common high-confidence stale pairs:")
            for row in top_stale:
                lines.append(f"    {row['upstream']} → {row['downstream']}  ({row['n']}x)")

    # ── Projects needing attention ────────────────────────────────────────────
    needs_attention = conn.execute(
        "SELECT slug, qa_verdict, critic_status, staleness_high "
        "FROM projects "
        "WHERE healthy = 0 AND phase NOT IN ('archived','done') "
        "   OR qa_verdict = 'FAIL' "
        "   OR staleness_high > 0 "
        "ORDER BY ingested_at DESC LIMIT 12"
    ).fetchall()
    if needs_attention:
        lines.append("")
        lines.append("  Projects needing attention:")
        for p in needs_attention:
            qa = (p["qa_verdict"] or "—")[:20]
            critic = (p["critic_status"] or "—")[:22]
            stale = f"stale×{p['staleness_high']}" if p["staleness_high"] else ""
            lines.append(f"    {p['slug']:<36} qa={qa:<22} critic={critic:<24} {stale}")

    lines.append("━" * 64)
    conn.close()
    return "\n".join(lines)


# ── report: gates ─────────────────────────────────────────────────────────────

def report_gates(db_path: Path = DEFAULT_DB_PATH) -> str:
    conn = connect(db_path)
    lines: list[str] = []

    total_projects = _row_count(conn, "projects")
    if total_projects == 0:
        conn.close()
        return "No projects ingested yet."

    lines.append("━" * 64)
    lines.append(f"  Gate pass rates  ({total_projects} projects)")
    lines.append("━" * 64)

    gate_rows = conn.execute(
        "SELECT gate_id, gate_order, "
        "  SUM(passed) AS passed_count, COUNT(*) AS total_count "
        "FROM gates GROUP BY gate_id, gate_order ORDER BY gate_order"
    ).fetchall()

    for row in gate_rows:
        p = row["passed_count"]
        t = row["total_count"]
        bar = _bar(p, t, width=16)
        lines.append(f"  {row['gate_id']:<36} {p:>3}/{t}  {bar}  {_pct(p, t)}")

    lines.append("━" * 64)
    conn.close()
    return "\n".join(lines)
