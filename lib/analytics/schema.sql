-- lib/analytics/schema.sql — Analytics database schema v1
--
-- This database is a derived index of project artifacts.
-- It is safe to DELETE and REBUILD at any time.
-- Source of truth: project JSON/MD files on disk.
--
-- Schema version: 1
-- Upgrade path: DELETE data/analytics.db && python -m lib.analytics rebuild

-- ── Metadata ─────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS db_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- ── Projects ──────────────────────────────────────────────────────────────────
-- One row per project. Replaced on every ingest.

CREATE TABLE IF NOT EXISTS projects (
    slug                   TEXT PRIMARY KEY,
    title                  TEXT,
    project_dir            TEXT NOT NULL,
    schema_version         INTEGER,
    phase                  TEXT,
    status                 TEXT,
    style                  TEXT,
    theme                  TEXT,
    theme_primary          TEXT,
    input_quality          TEXT,
    target_duration_s      INTEGER,  -- from project.json target_duration_seconds
    actual_duration_s      REAL,     -- from project.json actual_duration (if set)
    gates_passed           INTEGER   NOT NULL DEFAULT 0,
    gates_total            INTEGER   NOT NULL DEFAULT 11,
    healthy                INTEGER   NOT NULL DEFAULT 0,  -- bool
    has_render             INTEGER   NOT NULL DEFAULT 0,  -- bool: output/*.mp4 exists
    qa_verdict             TEXT,     -- PASS / PASS_WITH_WARNINGS / FAIL / not_run
    qa_blockers            INTEGER,
    qa_warnings            INTEGER,
    critic_status          TEXT,     -- critic_passed / critic_warnings / critic_blocked / not_run
    critic_blockers        INTEGER,
    staleness_high         INTEGER   NOT NULL DEFAULT 0,
    staleness_total        INTEGER   NOT NULL DEFAULT 0,
    created_at             TEXT,     -- from project.json
    updated_at             TEXT,     -- from project.json
    ingested_at            TEXT      NOT NULL
);

-- ── Gates ─────────────────────────────────────────────────────────────────────
-- One row per gate per project.

CREATE TABLE IF NOT EXISTS gates (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    project_slug   TEXT    NOT NULL REFERENCES projects(slug) ON DELETE CASCADE,
    gate_id        TEXT    NOT NULL,
    gate_order     INTEGER NOT NULL,
    passed         INTEGER NOT NULL DEFAULT 0,
    ingested_at    TEXT    NOT NULL,
    UNIQUE(project_slug, gate_id)
);

-- ── Artifacts ─────────────────────────────────────────────────────────────────
-- One row per tracked artifact per project.

CREATE TABLE IF NOT EXISTS artifacts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    project_slug   TEXT    NOT NULL REFERENCES projects(slug) ON DELETE CASCADE,
    path           TEXT    NOT NULL,
    present        INTEGER NOT NULL DEFAULT 0,
    size_bytes     INTEGER NOT NULL DEFAULT 0,
    ingested_at    TEXT    NOT NULL,
    UNIQUE(project_slug, path)
);

-- ── Staleness signals ─────────────────────────────────────────────────────────
-- One row per stale pair per project. Fully replaced on re-ingest.

CREATE TABLE IF NOT EXISTS staleness_signals (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    project_slug         TEXT    NOT NULL REFERENCES projects(slug) ON DELETE CASCADE,
    upstream             TEXT    NOT NULL,
    downstream           TEXT    NOT NULL,
    confidence           TEXT    NOT NULL,
    age_delta_seconds    REAL    NOT NULL,
    reason               TEXT,
    recommended_action   TEXT,
    ingested_at          TEXT    NOT NULL,
    UNIQUE(project_slug, upstream, downstream)
);

-- ── QA findings ───────────────────────────────────────────────────────────────
-- All findings from the most recent qa_report.json per project.

CREATE TABLE IF NOT EXISTS qa_findings (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    project_slug   TEXT    NOT NULL REFERENCES projects(slug) ON DELETE CASCADE,
    qa_timestamp   TEXT,
    qa_verdict     TEXT,
    gate           TEXT,
    severity       TEXT    NOT NULL,  -- block / warn
    location       TEXT,
    message        TEXT    NOT NULL,
    fix_hint       TEXT,
    ingested_at    TEXT    NOT NULL
);

-- ── Critic findings ───────────────────────────────────────────────────────────
-- All findings from the most recent critic-report.json per project.
-- Includes both global findings and per-beat findings.

CREATE TABLE IF NOT EXISTS critic_findings (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    project_slug   TEXT    NOT NULL REFERENCES projects(slug) ON DELETE CASCADE,
    generated_at   TEXT,
    finding_id     TEXT,
    check_name     TEXT    NOT NULL,
    severity       TEXT    NOT NULL,  -- block / warn / suggest (normalised lower)
    confidence     REAL,
    reason         TEXT    NOT NULL,
    suggested_fix  TEXT,
    scope          TEXT,              -- global / beat
    beat_id        TEXT,             -- NULL for global findings
    ingested_at    TEXT    NOT NULL
);

-- ── Review rounds ─────────────────────────────────────────────────────────────
-- Future: populated when output/review-feedback.md files are detected.
-- Defined now so the schema is complete; currently empty.

CREATE TABLE IF NOT EXISTS review_rounds (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    project_slug         TEXT    NOT NULL REFERENCES projects(slug) ON DELETE CASCADE,
    round_number         INTEGER NOT NULL DEFAULT 1,
    captured_at          TEXT,
    feedback_raw         TEXT,   -- full text of review-feedback.md
    hard_rules_count     INTEGER NOT NULL DEFAULT 0,
    soft_prefs_count     INTEGER NOT NULL DEFAULT 0,
    ingested_at          TEXT    NOT NULL
);

-- ── Indexes ───────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_gates_project   ON gates(project_slug);
CREATE INDEX IF NOT EXISTS idx_gates_passed    ON gates(passed);
CREATE INDEX IF NOT EXISTS idx_artifacts_proj  ON artifacts(project_slug);
CREATE INDEX IF NOT EXISTS idx_qa_project      ON qa_findings(project_slug);
CREATE INDEX IF NOT EXISTS idx_qa_severity     ON qa_findings(severity);
CREATE INDEX IF NOT EXISTS idx_qa_gate         ON qa_findings(gate);
CREATE INDEX IF NOT EXISTS idx_critic_project  ON critic_findings(project_slug);
CREATE INDEX IF NOT EXISTS idx_critic_severity ON critic_findings(severity);
CREATE INDEX IF NOT EXISTS idx_critic_check    ON critic_findings(check_name);
CREATE INDEX IF NOT EXISTS idx_stale_project   ON staleness_signals(project_slug);
CREATE INDEX IF NOT EXISTS idx_stale_conf      ON staleness_signals(confidence);
