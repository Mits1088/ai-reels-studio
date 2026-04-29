# data/

This directory contains the runtime analytics database used by `lib.brain`.

## analytics.db

SQLite database — **not committed** (excluded via `.gitignore`). Regenerated automatically when `lib.brain` runs.

### Tables

| Table | Contents |
|---|---|
| `projects` | One row per project slug — phase, status, gate state |
| `gates` | Gate pass/fail history per project |
| `artifacts` | Tracked output files per project (timeline, scripts, reports) |
| `staleness_signals` | Signals that a project's artifacts may be out of date |
| `qa_findings` | QA report findings indexed by project and severity |
| `critic_findings` | Critic/hard-mode gate findings |
| `review_rounds` | Human review rounds with feedback classification |
| `db_meta` | Schema version |

### Usage

```bash
# Run brain diagnostics (reads/writes analytics.db)
python -m lib.brain diagnose projects/<slug>

# Sweep all projects
python -m lib.brain sweep

# View project status
python -m lib.brain status
```

The database is created fresh if missing — no manual setup required.
