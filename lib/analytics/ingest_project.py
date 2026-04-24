"""
lib.analytics.ingest_project — Ingest a single project into the analytics DB.

Calls lib.brain.diagnose_project() to collect all signals, then loads
project.json for any extra fields not surfaced by the Diagnosis. All writes
are idempotent: re-ingesting a project deletes its old rows and inserts fresh
ones within a single transaction.

Read-only on the project side. Never mutates project files.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lib.brain import diagnose_project
from lib.constants import GATE_ORDER

from .db import connect, DEFAULT_DB_PATH


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None


def _has_render(project_dir: Path) -> bool:
    out = project_dir / "output"
    if not out.exists():
        return False
    return any(out.glob("*.mp4"))


@dataclass
class IngestResult:
    slug: str
    status: str          # "ok" | "error"
    message: str         # human-readable detail


def ingest_project(
    project_dir: Path,
    db_path: Path = DEFAULT_DB_PATH,
) -> IngestResult:
    """
    Ingest one project into the analytics database.

    Uses lib.brain.diagnose_project() as the primary signal source.
    Loads project.json directly for extra fields.
    Re-ingesting deletes all previous rows for this project and replaces them.
    """
    project_dir = Path(project_dir).resolve()
    now = _now_iso()

    # ── Diagnose ──────────────────────────────────────────────────────────────
    try:
        diag = diagnose_project(project_dir)
    except Exception as exc:
        slug = project_dir.name
        return IngestResult(slug=slug, status="error", message=str(exc))

    slug = diag.slug

    # ── Load project.json for extra fields ────────────────────────────────────
    pj = _load_json(project_dir / "project.json") or {}

    target_dur = pj.get("target_duration_seconds") or pj.get("target_duration")
    if isinstance(target_dur, str):
        try:
            target_dur = int(target_dur)
        except ValueError:
            target_dur = None

    actual_dur = pj.get("actual_duration") or pj.get("duration_s")
    if isinstance(actual_dur, str):
        try:
            actual_dur = float(actual_dur)
        except ValueError:
            actual_dur = None

    input_quality = pj.get("input_quality")
    created_at = pj.get("created")
    updated_at = pj.get("updated")

    # ── QA counts ─────────────────────────────────────────────────────────────
    qa = diag.qa
    qa_verdict = qa.verdict if qa.available else "not_run"
    qa_blockers = qa.blockers if qa.available else None
    qa_warnings = qa.warnings if qa.available else None

    # ── Critic counts ─────────────────────────────────────────────────────────
    critic = diag.critic
    critic_status = critic.status
    critic_report = _load_json(project_dir / "output" / "critic-report.json") or {}
    critic_blockers = (
        critic_report.get("totals", {}).get("blockers") if critic.available else None
    )

    # ── Staleness summary ─────────────────────────────────────────────────────
    stale_results = diag.artifacts.staleness_results
    stale_high = sum(1 for r in stale_results if r.confidence == "high")

    # ── Write to DB in one transaction ────────────────────────────────────────
    try:
        conn = connect(db_path)
        with conn:
            # Delete existing rows for this slug (children cascade)
            conn.execute("DELETE FROM projects WHERE slug = ?", (slug,))

            # ── projects ──────────────────────────────────────────────────────
            conn.execute(
                """
                INSERT INTO projects (
                    slug, title, project_dir, schema_version, phase, status,
                    style, theme, theme_primary, input_quality,
                    target_duration_s, actual_duration_s,
                    gates_passed, gates_total, healthy, has_render,
                    qa_verdict, qa_blockers, qa_warnings,
                    critic_status, critic_blockers,
                    staleness_high, staleness_total,
                    created_at, updated_at, ingested_at
                ) VALUES (
                    ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                )
                """,
                (
                    slug,
                    diag.title or None,
                    str(project_dir),
                    diag.schema_version,
                    diag.phase,
                    diag.status,
                    diag.style if diag.style not in ("", "unknown") else None,
                    diag.theme if diag.theme not in ("", "unknown") else None,
                    diag.theme_primary or None,
                    input_quality,
                    target_dur,
                    actual_dur,
                    len(diag.gates.passed),
                    diag.gates.total,
                    int(diag.healthy),
                    int(_has_render(project_dir)),
                    qa_verdict,
                    qa_blockers,
                    qa_warnings,
                    critic_status,
                    critic_blockers,
                    stale_high,
                    len(stale_results),
                    created_at,
                    updated_at,
                    now,
                ),
            )

            # ── gates ─────────────────────────────────────────────────────────
            passed_set = set(diag.gates.passed)
            conn.executemany(
                """
                INSERT OR REPLACE INTO gates
                    (project_slug, gate_id, gate_order, passed, ingested_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (slug, gate_id, idx, int(gate_id in passed_set), now)
                    for idx, gate_id in enumerate(GATE_ORDER)
                ],
            )

            # ── artifacts ─────────────────────────────────────────────────────
            conn.executemany(
                """
                INSERT OR REPLACE INTO artifacts
                    (project_slug, path, present, size_bytes, ingested_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (slug, e.path, int(e.present), e.size_bytes, now)
                    for e in diag.artifacts.entries
                ],
            )

            # ── staleness_signals ─────────────────────────────────────────────
            conn.executemany(
                """
                INSERT OR REPLACE INTO staleness_signals
                    (project_slug, upstream, downstream, confidence,
                     age_delta_seconds, reason, recommended_action, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        slug,
                        r.upstream,
                        r.downstream,
                        r.confidence,
                        r.age_delta_seconds,
                        r.reason,
                        r.recommended_action,
                        now,
                    )
                    for r in stale_results
                ],
            )

            # ── qa_findings ───────────────────────────────────────────────────
            qa_report = _load_json(project_dir / "output" / "qa_report.json") or {}
            qa_ts = qa_report.get("timestamp")
            for finding in qa_report.get("findings", []):
                conn.execute(
                    """
                    INSERT INTO qa_findings
                        (project_slug, qa_timestamp, qa_verdict,
                         gate, severity, location, message, fix_hint,
                         ingested_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        slug,
                        qa_ts,
                        qa_verdict,
                        finding.get("gate"),
                        (finding.get("severity") or "").lower(),
                        finding.get("location"),
                        finding.get("message", ""),
                        finding.get("fix_hint"),
                        now,
                    ),
                )

            # ── critic_findings ───────────────────────────────────────────────
            gen_at = critic_report.get("generated_at")
            # Collect global + per-beat findings
            all_critic: list[tuple[Any, ...]] = []
            for f in critic_report.get("global_findings", []):
                all_critic.append((
                    slug, gen_at,
                    f.get("finding_id"),
                    f.get("check", ""),
                    (f.get("severity") or "suggest").lower(),
                    f.get("confidence"),
                    f.get("reason", ""),
                    f.get("suggested_fix"),
                    f.get("scope", "global"),
                    None,   # beat_id
                    now,
                ))
            for beat in critic_report.get("beats", []):
                beat_id = beat.get("beat_id")
                for f in beat.get("findings", []):
                    all_critic.append((
                        slug, gen_at,
                        f.get("finding_id"),
                        f.get("check", ""),
                        (f.get("severity") or "suggest").lower(),
                        f.get("confidence"),
                        f.get("reason", ""),
                        f.get("suggested_fix"),
                        "beat",
                        beat_id,
                        now,
                    ))
            conn.executemany(
                """
                INSERT INTO critic_findings
                    (project_slug, generated_at, finding_id, check_name,
                     severity, confidence, reason, suggested_fix,
                     scope, beat_id, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                all_critic,
            )

            # ── review_rounds ─────────────────────────────────────────────────
            rfp = project_dir / "output" / "review-feedback.md"
            if rfp.exists():
                try:
                    text = rfp.read_text(encoding="utf-8")
                    conn.execute(
                        """
                        INSERT INTO review_rounds
                            (project_slug, round_number, captured_at,
                             feedback_raw, ingested_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (slug, 1, None, text, now),
                    )
                except UnicodeDecodeError:
                    pass  # skip unreadable files

        conn.close()
        g = diag.gates
        return IngestResult(
            slug=slug,
            status="ok",
            message=(
                f"{g.passed.__len__()}/{g.total} gates  "
                f"qa={qa_verdict}  "
                f"stale={len(stale_results)}"
            ),
        )

    except sqlite3.Error as exc:
        return IngestResult(slug=slug, status="error", message=str(exc))
