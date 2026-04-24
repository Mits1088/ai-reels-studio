"""
lib.analytics CLI — analytics database management.

Usage:
  python -m lib.analytics init [--db PATH] [--force]
  python -m lib.analytics ingest <project_dir> [--db PATH]
  python -m lib.analytics ingest-all [projects_dir] [--db PATH] [--quiet]
  python -m lib.analytics rebuild [projects_dir] [--db PATH]
  python -m lib.analytics report projects [--db PATH]
  python -m lib.analytics report qa [--db PATH]
  python -m lib.analytics report gates [--db PATH]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .db import DEFAULT_DB_PATH, init_db
from .ingest_all import ingest_all
from .ingest_project import ingest_project
from .reports import report_gates, report_projects, report_qa


def _cmd_init(args: argparse.Namespace) -> int:
    db_path = Path(args.db)
    msg = init_db(db_path, force=args.force)
    print(msg)
    return 0


def _cmd_ingest(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir)
    db_path = Path(args.db)

    init_db(db_path)
    result = ingest_project(project_dir, db_path)
    if result.status == "ok":
        print(f"✓  {result.slug}  —  {result.message}")
        return 0
    else:
        print(f"✗  {result.slug}  —  ERROR: {result.message}", file=sys.stderr)
        return 1


def _cmd_ingest_all(args: argparse.Namespace) -> int:
    projects_dir = Path(args.projects_dir)
    db_path = Path(args.db)

    batch = ingest_all(projects_dir, db_path, quiet=args.quiet)
    return 0 if batch.errors == 0 else 1


def _cmd_rebuild(args: argparse.Namespace) -> int:
    db_path = Path(args.db)
    projects_dir = Path(args.projects_dir)

    msg = init_db(db_path, force=True)
    print(msg)
    batch = ingest_all(projects_dir, db_path, quiet=False)
    return 0 if batch.errors == 0 else 1


def _cmd_report(args: argparse.Namespace) -> int:
    db_path = Path(args.db)
    sub = args.report_type

    if sub == "projects":
        print(report_projects(db_path))
    elif sub == "qa":
        print(report_qa(db_path))
    elif sub == "gates":
        print(report_gates(db_path))
    else:
        print(f"Unknown report type: {sub}", file=sys.stderr)
        print("Available: projects, qa, gates", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m lib.analytics",
        description="Analytics database management for the reel production pipeline.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── init ──────────────────────────────────────────────────────────────────
    p_init = sub.add_parser("init", help="Create or verify the analytics database")
    p_init.add_argument("--db", default=str(DEFAULT_DB_PATH), metavar="PATH")
    p_init.add_argument("--force", action="store_true", help="Drop and recreate all tables")

    # ── ingest ────────────────────────────────────────────────────────────────
    p_ingest = sub.add_parser("ingest", help="Ingest a single project")
    p_ingest.add_argument("project_dir", help="Path to the project directory")
    p_ingest.add_argument("--db", default=str(DEFAULT_DB_PATH), metavar="PATH")

    # ── ingest-all ────────────────────────────────────────────────────────────
    p_all = sub.add_parser("ingest-all", help="Ingest all projects")
    p_all.add_argument("projects_dir", nargs="?", default="projects",
                       help="Parent directory containing all projects (default: projects/)")
    p_all.add_argument("--db", default=str(DEFAULT_DB_PATH), metavar="PATH")
    p_all.add_argument("--quiet", action="store_true", help="Suppress per-project output")

    # ── rebuild ───────────────────────────────────────────────────────────────
    p_rebuild = sub.add_parser("rebuild", help="Drop, recreate, and re-ingest all projects")
    p_rebuild.add_argument("projects_dir", nargs="?", default="projects",
                           help="Parent directory containing all projects (default: projects/)")
    p_rebuild.add_argument("--db", default=str(DEFAULT_DB_PATH), metavar="PATH")

    # ── report ────────────────────────────────────────────────────────────────
    p_report = sub.add_parser("report", help="Print a pre-built report")
    p_report.add_argument("report_type", choices=["projects", "qa", "gates"],
                          help="Which report to print")
    p_report.add_argument("--db", default=str(DEFAULT_DB_PATH), metavar="PATH")

    args = parser.parse_args(argv)

    dispatch = {
        "init": _cmd_init,
        "ingest": _cmd_ingest,
        "ingest-all": _cmd_ingest_all,
        "rebuild": _cmd_rebuild,
        "report": _cmd_report,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
