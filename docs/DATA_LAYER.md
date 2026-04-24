# Data Layer — Analytics Database

**Module:** `lib/analytics/`  
**Database:** `data/analytics.db` (SQLite, WAL mode)  
**Schema version:** 1  

---

## Purpose

`lib.analytics` is a **derived, rebuildable index** of all project artifacts. It exists to answer cross-project questions like:

- Which gates are failing most often across the portfolio?
- Which projects have stale artifacts with high confidence?
- Which critic checks keep blocking the most reels?
- What is the distribution of QA verdicts across all rendered projects?

**Canonical data lives in project JSON/MD files on disk.** The database is always safe to delete and rebuild — it contains no information that does not exist in the source files.

---

## Architecture

```
projects/<slug>/project.json    ─┐
projects/<slug>/output/*.json   ─┤  source of truth (never modified by this layer)
projects/<slug>/output/*.md     ─┤
projects/<slug>/audio/*.json    ─┘
                                          ↓  lib.brain.diagnose_project()
                                          ↓  lib.analytics.ingest_project()
                                    data/analytics.db   (derived index)
                                          ↓
                                    python -m lib.analytics report qa
```

---

## CLI

```bash
# Create the database (no-op if already at current schema version)
python -m lib.analytics init

# Force-recreate (drops all tables and re-applies schema)
python -m lib.analytics init --force

# Ingest a single project
python -m lib.analytics ingest projects/<slug>

# Ingest all projects under projects/ (skips _shared, _template)
python -m lib.analytics ingest-all

# Drop, recreate, and re-ingest everything
python -m lib.analytics rebuild

# Reports
python -m lib.analytics report projects   # overview: health, phase, QA verdicts, gate completion
python -m lib.analytics report qa         # QA + critic findings, staleness, projects needing attention
python -m lib.analytics report gates      # per-gate pass rates across all projects

# Custom DB path (all commands accept --db)
python -m lib.analytics ingest-all --db /tmp/test.db
```

---

## Schema (v1)

### `db_meta`

Key/value store for database metadata.

| Key | Value |
|---|---|
| `schema_version` | Current schema version integer |
| `created_at` | ISO 8601 timestamp when DB was created |
| `last_rebuilt_at` | ISO 8601 timestamp of most recent rebuild |

### `projects`

One row per project. Replaced on every ingest.

| Column | Type | Source |
|---|---|---|
| `slug` | TEXT PK | project directory name |
| `title` | TEXT | `project.json` → title |
| `project_dir` | TEXT | absolute path on disk |
| `schema_version` | INTEGER | `project.json` → schema_version |
| `phase` | TEXT | `lib.brain.Diagnosis.phase` |
| `status` | TEXT | `lib.brain.Diagnosis.status` |
| `style` | TEXT | `project.json` → style |
| `theme` | TEXT | `project.json` → theme |
| `theme_primary` | TEXT | `project.json` → theme_primary |
| `input_quality` | TEXT | `project.json` → input_quality |
| `target_duration_s` | INTEGER | `project.json` → target_duration_seconds |
| `actual_duration_s` | REAL | `project.json` → actual_duration |
| `gates_passed` | INTEGER | `len(Diagnosis.gates.passed)` |
| `gates_total` | INTEGER | `Diagnosis.gates.total` (always 11) |
| `healthy` | INTEGER | `int(Diagnosis.healthy)` (bool) |
| `has_render` | INTEGER | `output/*.mp4` exists (bool) |
| `qa_verdict` | TEXT | `Diagnosis.qa.verdict` |
| `qa_blockers` | INTEGER | `Diagnosis.qa.blockers` |
| `qa_warnings` | INTEGER | `Diagnosis.qa.warnings` |
| `critic_status` | TEXT | `Diagnosis.critic.status` |
| `critic_blockers` | INTEGER | `critic-report.json` → totals.blockers |
| `staleness_high` | INTEGER | count of high-confidence staleness signals |
| `staleness_total` | INTEGER | total staleness signals |
| `created_at` | TEXT | `project.json` → created |
| `updated_at` | TEXT | `project.json` → updated |
| `ingested_at` | TEXT | ingest timestamp (UTC ISO 8601) |

### `gates`

One row per gate per project. Replaced on re-ingest.

| Column | Notes |
|---|---|
| `project_slug` | FK → projects.slug (CASCADE) |
| `gate_id` | e.g. `brief_approved` |
| `gate_order` | integer position in GATE_ORDER |
| `passed` | 0 / 1 |

### `artifacts`

One row per tracked artifact per project.

| Column | Notes |
|---|---|
| `project_slug` | FK → projects.slug (CASCADE) |
| `path` | relative path from project root |
| `present` | 0 / 1 |
| `size_bytes` | 0 if absent |

### `staleness_signals`

One row per stale upstream→downstream pair.

| Column | Notes |
|---|---|
| `upstream` | relative path of the newer file |
| `downstream` | relative path of the potentially stale file |
| `confidence` | `high` / `medium` / `low` |
| `age_delta_seconds` | how many seconds newer the upstream is |
| `reason` | human-readable explanation |
| `recommended_action` | concrete next step |

### `qa_findings`

All findings from the most recent `output/qa_report.json`.

| Column | Notes |
|---|---|
| `qa_timestamp` | timestamp from the report |
| `qa_verdict` | verdict at time of report |
| `gate` | which gate the finding relates to |
| `severity` | `block` / `warn` (normalised lowercase) |
| `location` | file or beat reference |
| `message` | human-readable description |
| `fix_hint` | suggested resolution |

### `critic_findings`

All findings from the most recent `output/critic-report.json`. Includes both global and per-beat findings.

| Column | Notes |
|---|---|
| `generated_at` | timestamp from the critic report |
| `finding_id` | critic's internal finding ID |
| `check_name` | e.g. `visual_novelty`, `dead_holds` |
| `severity` | `block` / `warn` / `suggest` (normalised lowercase) |
| `confidence` | 0.0–1.0 float |
| `reason` | explanation |
| `suggested_fix` | recommended action |
| `scope` | `global` or `beat` |
| `beat_id` | NULL for global findings |

### `review_rounds`

One row per review-feedback.md file captured per project.

| Column | Notes |
|---|---|
| `round_number` | always 1 for now (multi-round support is planned) |
| `captured_at` | timestamp from the feedback file (if present) |
| `feedback_raw` | full text of review-feedback.md |
| `hard_rules_count` | populated when feedback-capture parses the file |
| `soft_prefs_count` | populated when feedback-capture parses the file |

---

## Ingest Behaviour

### Idempotency

Re-ingesting a project is safe and idempotent. The ingest function:

1. Deletes all rows for `slug` from the `projects` table
2. All child rows cascade-delete automatically (FK `ON DELETE CASCADE`)
3. Inserts fresh rows for all tables in a single transaction

This means you can run `ingest-all` at any time to refresh stale data.

### Signal source

`ingest_project()` uses `lib.brain.diagnose_project()` as its primary signal source. This means the brain's staleness detection, gate checks, QA verdict, and critic status are all reflected in the database without duplicating logic.

`project.json` is read directly for fields not exposed by the Diagnosis: `target_duration_seconds`, `actual_duration`, `input_quality`, `created`, `updated`.

### Error handling

If `diagnose_project()` raises an exception (e.g. project directory missing, JSON decode error), `ingest_project()` returns `IngestResult(status="error", ...)` rather than raising. `ingest_all` counts these as errors and continues with remaining projects.

---

## Schema Migration

Schema is versioned via `SCHEMA_VERSION = 1` in `db.py` and stored in `db_meta`.

When the schema changes (new column, new table, changed type):

1. Increment `SCHEMA_VERSION` in `db.py`
2. Update `schema.sql` with the new definition
3. Rebuild the database: `python -m lib.analytics rebuild`

The DB will detect the version mismatch on next use and print:
```
Schema mismatch: DB is v1, code expects v2. Run `python -m lib.analytics rebuild`.
```

There is no migration path — the database is always rebuilt from source. This is intentional: it keeps the schema layer simple and avoids migration debt. Since all data is derived from project files, a full rebuild is always correct and complete.

---

## What This Is NOT

- **Not a replacement for `memory/creative-feedback.json`** — taste signal and editorial preferences stay in memory, not the DB
- **Not a promotion engine** — the DB never automatically updates global rules
- **Not a secrets store** — do not ingest API keys, tokens, or personal data
- **Not a write-back layer** — the DB never modifies project files

---

## Quick Reference

```bash
# Standard workflow after completing any project phase
python -m lib.analytics ingest projects/<slug>

# After any batch of changes across projects
python -m lib.analytics rebuild

# Portfolio health check
python -m lib.analytics report projects
python -m lib.analytics report qa
python -m lib.analytics report gates
```
