"""
lib.analytics.db — SQLite connection management and schema lifecycle.

The database is a derived index. Delete data/analytics.db and run
`python -m lib.analytics rebuild` to reconstruct from source files.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Increment when tables or columns change. Old databases must be rebuilt.
SCHEMA_VERSION = 1

# Default path relative to wherever the CLI is invoked from.
# Callers may pass an explicit path to override.
DEFAULT_DB_PATH = Path("data/analytics.db")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Open a WAL-mode connection with FK enforcement and Row factory.

    Creates the parent directory if it does not exist.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _schema_sql() -> str:
    return (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")


def current_version(db_path: Path = DEFAULT_DB_PATH) -> int | None:
    """Return the schema version stored in the DB, or None if absent."""
    if not Path(db_path).exists():
        return None
    try:
        conn = connect(db_path)
        try:
            row = conn.execute(
                "SELECT value FROM db_meta WHERE key = 'schema_version'"
            ).fetchone()
            return int(row[0]) if row else None
        except sqlite3.OperationalError:
            return None
        finally:
            conn.close()
    except sqlite3.Error:
        return None


def init_db(db_path: Path = DEFAULT_DB_PATH, force: bool = False) -> str:
    """
    Create the database and apply schema.sql.

    If the DB already exists at the correct schema version: returns early unless
    force=True. If force=True: drops all tables and recreates from scratch.

    Returns a human-readable status string.
    """
    db_path = Path(db_path)
    existed = db_path.exists()

    if existed and not force:
        stored = current_version(db_path)
        if stored == SCHEMA_VERSION:
            return f"Already initialised at schema v{SCHEMA_VERSION} ({db_path}). Use --force to recreate."
        if stored is not None:
            return (
                f"Schema mismatch: DB is v{stored}, code expects v{SCHEMA_VERSION}. "
                f"Run `python -m lib.analytics rebuild` to drop and recreate."
            )

    conn = connect(db_path)
    try:
        if force or not existed:
            _DROP_ORDER = [
                "review_rounds", "staleness_signals",
                "qa_findings", "critic_findings",
                "artifacts", "gates", "projects", "db_meta",
            ]
            for tbl in _DROP_ORDER:
                conn.execute(f"DROP TABLE IF EXISTS {tbl}")
            conn.commit()

        conn.executescript(_schema_sql())

        now = _now_iso()
        conn.execute(
            "INSERT OR REPLACE INTO db_meta(key, value) VALUES (?, ?)",
            ("schema_version", str(SCHEMA_VERSION)),
        )
        conn.execute(
            "INSERT OR REPLACE INTO db_meta(key, value) VALUES (?, ?)",
            ("created_at", now),
        )
        conn.execute(
            "INSERT OR REPLACE INTO db_meta(key, value) VALUES (?, ?)",
            ("last_rebuilt_at", now),
        )
        conn.commit()

        verb = "Recreated" if (force and existed) else "Initialised"
        return f"{verb}: {db_path} (schema v{SCHEMA_VERSION})"
    finally:
        conn.close()
