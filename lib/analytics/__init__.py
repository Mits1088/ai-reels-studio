"""
lib.analytics — SQLite-backed evidence store for cross-project querying.

The database is a derived index. All canonical data lives in project JSON/MD files.
Delete data/analytics.db at any time and run `python -m lib.analytics rebuild` to
reconstruct from source.
"""

from .db import connect, init_db, current_version, DEFAULT_DB_PATH
from .ingest_project import ingest_project, IngestResult

__all__ = [
    "connect",
    "init_db",
    "current_version",
    "DEFAULT_DB_PATH",
    "ingest_project",
    "IngestResult",
]
