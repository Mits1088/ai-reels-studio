"""
lib.analytics.ingest_all — Batch-ingest all projects under a given directory.

Usage:
    python -m lib.analytics ingest-all [projects_dir] [--db DB_PATH] [--quiet]

Walks `projects_dir` (default: "projects/"), skipping non-directories and paths
that start with "_". Ingests each project in alphabetical order. Reports a
per-project status line and a summary at the end.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from .db import DEFAULT_DB_PATH, init_db
from .ingest_project import ingest_project


@dataclass
class BatchResult:
    total: int
    ok: int
    errors: int
    error_slugs: list[str]


def ingest_all(
    projects_dir: Path = Path("projects"),
    db_path: Path = DEFAULT_DB_PATH,
    quiet: bool = False,
) -> BatchResult:
    """
    Ingest every project subdirectory found under `projects_dir`.

    Skips:
    - Non-directory entries
    - Directories whose name starts with '_' (e.g. _shared, _template)

    Returns a BatchResult summarising counts.
    """
    projects_dir = Path(projects_dir).resolve()
    db_path = Path(db_path)

    if not projects_dir.exists():
        raise FileNotFoundError(f"projects directory not found: {projects_dir}")

    # Ensure DB is initialised (no-op if already at current schema version)
    init_db(db_path)

    candidates = sorted(
        p for p in projects_dir.iterdir()
        if p.is_dir() and not p.name.startswith("_")
    )

    if not candidates:
        if not quiet:
            print(f"No project directories found in {projects_dir}")
        return BatchResult(total=0, ok=0, errors=0, error_slugs=[])

    total = len(candidates)
    ok = 0
    errors = 0
    error_slugs: list[str] = []

    for project_dir in candidates:
        result = ingest_project(project_dir, db_path)
        if result.status == "ok":
            ok += 1
            if not quiet:
                print(f"  ✓  {result.slug:<35}  {result.message}")
        else:
            errors += 1
            error_slugs.append(result.slug)
            if not quiet:
                print(f"  ✗  {result.slug:<35}  ERROR: {result.message}", file=sys.stderr)

    if not quiet:
        print()
        print(f"Ingested {ok}/{total} projects  ({errors} errors)")

    return BatchResult(total=total, ok=ok, errors=errors, error_slugs=error_slugs)
