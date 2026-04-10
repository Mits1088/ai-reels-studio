"""
Project migration — normalize all projects to current schema.

Handles the messy heterogeneous project.json formats across projects:
old phase names, numeric phases, compound strings, missing fields,
old status values, absent gates_passed arrays.

CLI:
    PYTHONPATH=. python -m lib.migrate --dry-run              # preview all
    PYTHONPATH=. python -m lib.migrate                         # apply all
    PYTHONPATH=. python -m lib.migrate --project <slug>        # single project
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from lib.constants import (
    VALID_PHASES, VALID_STATUSES, GATE_ORDER, YOUTUBE_GATE_ORDER,
    CURRENT_SCHEMA_VERSION,
)


# ── Phase normalization ─────────────────────────────────────────────────────

PHASE_MAP = {
    # Old string values
    "brief": "source-brief",
    "rendered": "done",
    "render": "render",
    "done": "done",
    # Compound strings
    "6-qa": "qa",
    "6-qa-failed": "qa",
    "qa-reel": "qa",
    # Skill names used as phases
    "reel-script": "script",
    "voice_ingest": "voice",
    "ingest-voice": "voice",
    "shot-list": "shot-list",
    "motion-intent": "motion-intent",
    "asset-prep": "asset-prep",
    # Numeric phases (from older projects)
    "0": "source-brief",
    "1": "script",
    "2": "voice",
    "3": "beat-map",
    "4": "capture",
    "5": "assembly",
    "6": "qa",
    "7": "render",
}


def normalize_phase(phase_val) -> str:
    """Normalize any observed phase value to a valid schema phase."""
    if phase_val is None:
        return "init"

    s = str(phase_val).strip()

    # Already valid
    if s in VALID_PHASES:
        return s

    # Check map
    if s in PHASE_MAP:
        return PHASE_MAP[s]

    # Try as integer
    try:
        return PHASE_MAP.get(str(int(float(s))), "init")
    except (ValueError, TypeError):
        pass

    return "init"


# ── Status normalization ────────────────────────────────────────────────────

STATUS_MAP = {
    "qa_passed": "completed",
    "qa_failed": "failed",
    "voice_ready": "completed",
    "assets_ready": "completed",
    "assembled": "completed",
    "wip": "in_progress",
    "rendered": "completed",
    "done": "completed",
}


def normalize_status(status_val) -> str:
    """Normalize any observed status value to a valid schema status."""
    if status_val is None:
        return "initialized"

    s = str(status_val).strip()

    if s in VALID_STATUSES:
        return s

    if s in STATUS_MAP:
        return STATUS_MAP[s]

    return "initialized"


# ── Gate inference ──────────────────────────────────────────────────────────

def infer_gates(project_dir: Path, project: dict) -> list[str]:
    """Conservatively infer which gates should be passed based on file existence.

    Only infers gates for which there is strong file evidence.
    Does not infer gates that require human approval judgement.
    """
    gates: list[str] = []

    # brief_approved — brief.md exists and has substantive content
    brief = project_dir / "brief.md"
    if brief.exists() and len(brief.read_text(encoding="utf-8").strip()) > 50:
        gates.append("brief_approved")

    # theme_set — theme fields are populated in project.json
    if project.get("theme") and project.get("theme_primary") and project.get("theme_secondary"):
        gates.append("theme_set")

    # script_approved — script.md exists
    script = project_dir / "script.md"
    if script.exists() and len(script.read_text(encoding="utf-8").strip()) > 50:
        gates.append("script_approved")

    # reconciliation_resolved — beat-map exists (implies audio was processed)
    beat_map = project_dir / "audio" / "beat-map.json"
    if beat_map.exists():
        gates.append("reconciliation_resolved")

    # visual_assignment_approved — shot-list.md exists with visual assignment section
    shot_list = project_dir / "shot-list.md"
    if shot_list.exists():
        content = shot_list.read_text(encoding="utf-8")
        if "visual assignment" in content.lower() or "4b-i" in content:
            gates.append("visual_assignment_approved")

        # asset_fitness_passed — shot-list has component mapping section
        if "component mapping" in content.lower() or "4b-ii" in content or "asset fitness" in content.lower():
            gates.append("asset_fitness_passed")

        # technical_planning_approved — shot-list has technical planning section
        if "technical planning" in content.lower() or "4b-iii" in content:
            gates.append("technical_planning_approved")

    # motion_intent_reviewed — motion-intent.md exists
    motion = project_dir / "output" / "motion-intent.md"
    if motion.exists():
        gates.append("motion_intent_reviewed")

    # assets_validated — timeline exists (implies assets were prepared)
    timeline = project_dir / "output" / "timeline.json"
    if timeline.exists():
        gates.append("assets_validated")

    # preview_passed — timeline exists and has been assembled
    if timeline.exists():
        gates.append("preview_passed")

    # qa_passed — qa_report.json exists with passing verdict
    qa_report = project_dir / "output" / "qa_report.json"
    if qa_report.exists():
        try:
            with open(qa_report, "r", encoding="utf-8") as f:
                report = json.load(f)
            if report.get("verdict") in ("PASS", "PASS_WITH_WARNINGS"):
                gates.append("qa_passed")
        except (json.JSONDecodeError, KeyError):
            pass

    # Also check old status values that imply QA passed
    status = project.get("status", "")
    if status in ("qa_passed", "rendered", "done"):
        if "qa_passed" not in gates:
            gates.append("qa_passed")

    # YouTube-specific gates
    if project.get("project_type") == "youtube" or project.get("type") == "youtube":
        yt_gates = []
        # video_ingested — video file + beat-map exist
        beat_map = project_dir / "audio" / "beat-map.json"
        if beat_map.exists():
            yt_gates.append("video_ingested")
        # overlay_plan_approved — overlay-plan.md exists
        overlay = project_dir / "output" / "overlay-plan.md"
        if overlay.exists():
            yt_gates.append("overlay_plan_approved")
        return [g for g in YOUTUBE_GATE_ORDER if g in yt_gates]

    # Ensure gate order is preserved
    ordered = [g for g in GATE_ORDER if g in gates]
    return ordered


# ── Migration ───────────────────────────────────────────────────────────────

def migrate_project(project_dir: Path, dry_run: bool = True) -> list[str]:
    """Normalize a project's project.json to current schema.

    Returns a list of changes made (or that would be made in dry_run mode).
    """
    pj_path = project_dir / "project.json"
    if not pj_path.exists():
        return [f"SKIP: {project_dir.name} — no project.json"]

    with open(pj_path, "r", encoding="utf-8") as f:
        original = f.read()
    project = json.loads(original)
    changes: list[str] = []

    slug = project.get("slug", project_dir.name)

    # Add schema_version if missing
    if "schema_version" not in project:
        project["schema_version"] = CURRENT_SCHEMA_VERSION
        changes.append(f"schema_version: added {CURRENT_SCHEMA_VERSION}")

    # Infer and add project_type if missing
    if "project_type" not in project:
        # Detect youtube projects by type field or video_file field
        if project.get("type") == "youtube" or "video_file" in project:
            project["project_type"] = "youtube"
        else:
            project["project_type"] = "reel"
        changes.append(f"project_type: inferred '{project['project_type']}'")

    # Normalize 'name' to 'title' (new-reel used 'name', schema uses 'title')
    if "name" in project and "title" not in project:
        project["title"] = project.pop("name")
        changes.append(f"title: renamed from 'name'")

    # Normalize 'created_at' to 'created' (new-reel used 'created_at')
    if "created_at" in project and "created" not in project:
        project["created"] = project.pop("created_at")
        changes.append(f"created: renamed from 'created_at'")

    # Normalize phase
    old_phase = project.get("phase")
    new_phase = normalize_phase(old_phase)
    if str(old_phase) != new_phase:
        changes.append(f"phase: {old_phase!r} -> {new_phase!r}")
        project["phase"] = new_phase

    # Normalize status
    old_status = project.get("status")
    new_status = normalize_status(old_status)
    if str(old_status) != new_status:
        changes.append(f"status: {old_status!r} -> {new_status!r}")
        project["status"] = new_status

    # Add missing required fields
    if "slug" not in project:
        project["slug"] = project_dir.name
        changes.append(f"slug: added '{project_dir.name}'")

    if "title" not in project:
        project["title"] = project_dir.name.replace("-", " ").title()
        changes.append(f"title: added '{project['title']}'")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if "created" not in project:
        project["created"] = now
        changes.append("created: added current timestamp")
    if "updated" not in project:
        project["updated"] = now
        changes.append("updated: added current timestamp")

    # Default style
    if "style" not in project or project["style"] is None:
        project["style"] = "cinematic-presenter"
        changes.append("style: defaulted to 'cinematic-presenter'")

    # Infer gates if empty
    existing_gates = project.get("gates_passed", [])
    if not existing_gates:
        inferred = infer_gates(project_dir, project)
        if inferred:
            project["gates_passed"] = inferred
            changes.append(f"gates_passed: inferred {len(inferred)} gates: {', '.join(inferred)}")
    else:
        changes.append(f"gates_passed: already has {len(existing_gates)} gates (kept as-is)")

    # Remove non-schema fields that cause additionalProperties: false to fail
    # (keep them — the schema may evolve, and removing data is destructive)

    if not changes:
        return [f"OK: {slug} — no changes needed"]

    if not dry_run:
        project["updated"] = now
        with open(pj_path, "w", encoding="utf-8") as f:
            json.dump(project, f, indent=2, ensure_ascii=False)
            f.write("\n")

    prefix = "WOULD" if dry_run else "APPLIED"
    return [f"{prefix}: {slug} — {len(changes)} change(s)"] + [f"  - {c}" for c in changes]


def migrate_all(projects_root: Path, dry_run: bool = True) -> list[str]:
    """Migrate all projects in a directory."""
    all_output: list[str] = []
    for d in sorted(projects_root.iterdir()):
        if d.is_dir() and (d / "project.json").exists():
            output = migrate_project(d, dry_run=dry_run)
            all_output.extend(output)
            all_output.append("")
    return all_output


# ── CLI ─────────────────────────────────────────────────────────────────────

USAGE = """\
Usage:
  python -m lib.migrate [--dry-run] [--project <slug>]

Options:
  --dry-run       Preview changes without writing (default)
  --project SLUG  Migrate a single project (default: all projects)

Examples:
  python -m lib.migrate --dry-run                    # preview all
  python -m lib.migrate                              # apply all
  python -m lib.migrate --project my-reel            # single project
  python -m lib.migrate --project my-reel --dry-run  # preview single
"""


def main() -> None:
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]

    project_slug = None
    if "--project" in args:
        idx = args.index("--project")
        if idx + 1 < len(args):
            project_slug = args[idx + 1]
        else:
            print("ERROR: --project requires a slug argument")
            sys.exit(1)

    projects_root = Path("projects")
    if not projects_root.exists():
        print("ERROR: projects/ directory not found. Run from repo root.")
        sys.exit(1)

    if project_slug:
        project_dir = projects_root / project_slug
        if not project_dir.exists():
            print(f"ERROR: Project not found: {project_dir}")
            sys.exit(1)
        output = migrate_project(project_dir, dry_run=dry_run)
    else:
        # Default to dry_run if no explicit flag and no --project
        if not args and "--dry-run" not in sys.argv:
            dry_run = False
        output = migrate_all(projects_root, dry_run=dry_run)

    for line in output:
        print(line)

    if dry_run:
        print("\n(Dry run — no files modified. Remove --dry-run to apply.)")


if __name__ == "__main__":
    main()
