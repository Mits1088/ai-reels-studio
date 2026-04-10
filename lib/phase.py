"""
Phase runner — thin enforcement wrapper around every pipeline phase.

Validates project state, checks gates, and reports readiness before
any skill begins work. After work completes, validates outputs and
updates project state.

CLI:
    python -m lib.phase check  <skill> <project-dir>   # Pre-flight only
    python -m lib.phase pre    <skill> <project-dir>    # Alias for check
    python -m lib.phase post   <skill> <project-dir>    # Post-flight validation
    python -m lib.phase status <project-dir>             # Full project health

This is enforcement, not orchestration. It does not run skills —
it validates that a skill CAN run (pre) or DID run correctly (post).
"""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from lib.constants import CURRENT_SCHEMA_VERSION, VALID_PROJECT_TYPES
from lib.gates import check_gates, SKILL_PREREQS
from lib.validate import validate_project, ValidationError


# ── Result types ───────────────────────────────────────────────────────────

@dataclass
class PreflightResult:
    """Result of pre-flight checks before a skill runs."""
    skill: str
    project_dir: Path
    ready: bool
    issues: list[str] = field(default_factory=list)

    def summary(self) -> str:
        slug = self.project_dir.name
        if self.ready:
            return f"READY: {self.skill} can proceed on {slug}."
        lines = [f"BLOCKED: {self.skill} cannot run on {slug}. {len(self.issues)} issue(s):"]
        for issue in self.issues:
            lines.append(f"  - {issue}")
        return "\n".join(lines)


@dataclass
class PostflightResult:
    """Result of post-flight checks after a skill completes."""
    skill: str
    project_dir: Path
    valid: bool
    issues: list[str] = field(default_factory=list)

    def summary(self) -> str:
        slug = self.project_dir.name
        if self.valid:
            return f"VALID: {self.skill} output on {slug} is clean."
        lines = [f"ISSUES: {self.skill} output on {slug} has {len(self.issues)} problem(s):"]
        for issue in self.issues:
            lines.append(f"  - {issue}")
        return "\n".join(lines)


@dataclass
class ProjectHealth:
    """Full project health report."""
    project_dir: Path
    schema_ok: bool
    validation_errors: list[str] = field(default_factory=list)
    gate_summary: str = ""
    next_skills: list[str] = field(default_factory=list)

    def summary(self) -> str:
        slug = self.project_dir.name
        lines = [f"Project: {slug}"]
        lines.append(f"Schema:  {'OK' if self.schema_ok else 'NEEDS MIGRATION'}")
        if self.validation_errors:
            lines.append(f"Errors:  {len(self.validation_errors)}")
            for e in self.validation_errors:
                lines.append(f"  - {e}")
        else:
            lines.append("Errors:  none")
        if self.gate_summary:
            lines.append("")
            lines.append(self.gate_summary)
        if self.next_skills:
            lines.append("")
            lines.append(f"Ready to run: {', '.join(self.next_skills)}")
        return "\n".join(lines)


# ── Core functions ─────────────────────────────────────────────────────────

def _load_project(project_dir: Path) -> dict:
    pj_path = project_dir / "project.json"
    if not pj_path.exists():
        raise FileNotFoundError(f"project.json not found in {project_dir}")
    with open(pj_path, "r", encoding="utf-8") as f:
        return json.load(f)


def preflight(skill: str, project_dir: Path) -> PreflightResult:
    """Run all pre-flight checks before a skill executes.

    Checks in order:
    1. project.json exists and loads
    2. schema_version is current (or suggests migration)
    3. project.json passes validation
    4. skill gates are satisfied
    """
    issues: list[str] = []

    # 1. Load project
    try:
        project = _load_project(project_dir)
    except FileNotFoundError as e:
        return PreflightResult(skill=skill, project_dir=project_dir,
                               ready=False, issues=[str(e)])

    # 2. Schema version check
    sv = project.get("schema_version")
    if sv is None:
        issues.append(
            f"schema_version missing — run: python -m lib.migrate --project {project_dir.name}")
    elif sv < CURRENT_SCHEMA_VERSION:
        issues.append(
            f"schema_version is {sv}, current is {CURRENT_SCHEMA_VERSION} "
            f"— run: python -m lib.migrate --project {project_dir.name}")

    # 3. Project type check
    pt = project.get("project_type")
    if pt is None:
        issues.append(
            f"project_type missing — run: python -m lib.migrate --project {project_dir.name}")
    elif pt not in VALID_PROJECT_TYPES:
        issues.append(f"unknown project_type: {pt!r}")

    # 4. Validate project.json
    validation_errors = validate_project(project)
    for ve in validation_errors:
        issues.append(f"validation: {ve}")

    # 5. Gate check
    if skill in SKILL_PREREQS:
        gate_result = check_gates(project_dir, skill)
        if not gate_result.passed:
            for f in gate_result.failures:
                issues.append(f"gate: {f}")
    elif skill != "__status__":
        issues.append(f"unknown skill: {skill!r}")

    return PreflightResult(
        skill=skill,
        project_dir=project_dir,
        ready=len(issues) == 0,
        issues=issues,
    )


def postflight(skill: str, project_dir: Path) -> PostflightResult:
    """Run post-flight checks after a skill completes.

    Checks:
    1. project.json still validates
    2. Expected output artifacts exist (skill-specific)
    """
    issues: list[str] = []

    # 1. Validate project.json
    try:
        project = _load_project(project_dir)
    except FileNotFoundError as e:
        return PostflightResult(skill=skill, project_dir=project_dir,
                                valid=False, issues=[str(e)])

    validation_errors = validate_project(project)
    for ve in validation_errors:
        issues.append(f"validation: {ve}")

    # 2. Check expected outputs per skill
    expected_outputs = _expected_outputs(skill)
    for rel_path in expected_outputs:
        full_path = project_dir / rel_path
        if not full_path.exists():
            issues.append(f"expected output missing: {rel_path}")

    return PostflightResult(
        skill=skill,
        project_dir=project_dir,
        valid=len(issues) == 0,
        issues=issues,
    )


def project_health(project_dir: Path) -> ProjectHealth:
    """Full project health check — schema, validation, gates, next steps."""
    try:
        project = _load_project(project_dir)
    except FileNotFoundError as e:
        return ProjectHealth(
            project_dir=project_dir, schema_ok=False,
            validation_errors=[str(e)])

    # Schema check
    sv = project.get("schema_version")
    schema_ok = sv is not None and sv >= CURRENT_SCHEMA_VERSION

    # Validation
    v_errors = [str(e) for e in validate_project(project)]

    # Gate status
    from lib.gates import gate_status
    g_summary = gate_status(project_dir)

    # Find which skills can run right now
    ready_skills = []
    for skill_name in SKILL_PREREQS:
        result = check_gates(project_dir, skill_name)
        if result.passed:
            ready_skills.append(skill_name)

    return ProjectHealth(
        project_dir=project_dir,
        schema_ok=schema_ok,
        validation_errors=v_errors,
        gate_summary=g_summary,
        next_skills=ready_skills,
    )


# ── Expected outputs per skill ─────────────────────────────────────────────

def _expected_outputs(skill: str) -> list[str]:
    """Return relative paths of artifacts a skill should produce."""
    outputs = {
        "source-brief":     ["brief.md", "source-research.md"],
        "theme-factory":    [],  # Updates project.json only
        "reel-script":      ["script.md"],
        "ingest-voice":     ["audio/source.wav", "audio/voice.json",
                             "audio/beat-map.json", "audio/captions.json"],
        "script-reconcile": ["audio/reconciliation.md"],
        "caption-polish":   ["audio/captions.json"],
        "capture-demo":     [],  # Assets vary per project
        "shot-list":        ["shot-list.md"],
        "shot-list-4b-i":   ["shot-list.md"],
        "shot-list-4b-ii":  ["shot-list.md"],
        "shot-list-4b-iii": ["shot-list.md"],
        "motion-intent":    ["output/motion-intent.md"],
        "asset-prep":       [],  # Assets in remotion/public/
        "assemble-reel":    ["output/timeline.json"],
        "qa-reel":          ["output/qa-report.md", "output/qa_report.json"],
        "youtube-ingest":   ["audio/source.wav", "audio/beat-map.json"],
        "youtube-overlay":  ["output/overlay-plan.md", "output/youtube-timeline.json"],
    }
    return outputs.get(skill, [])


# ── CLI ────────────────────────────────────────────────────────────────────

USAGE = """\
Usage:
  python -m lib.phase check  <skill> <project-dir>   Pre-flight: can this skill run?
  python -m lib.phase pre    <skill> <project-dir>   Alias for check
  python -m lib.phase post   <skill> <project-dir>   Post-flight: did skill produce valid output?
  python -m lib.phase status <project-dir>            Full project health report

Examples:
  python -m lib.phase check reel-script projects/my-reel
  python -m lib.phase post  ingest-voice projects/my-reel
  python -m lib.phase status projects/my-reel

Skills: {skills}
""".format(skills=", ".join(sorted(SKILL_PREREQS)))


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 2:
        print(USAGE)
        sys.exit(1)

    cmd = args[0]

    if cmd in ("check", "pre"):
        if len(args) < 3:
            print("Usage: python -m lib.phase check <skill> <project-dir>")
            sys.exit(1)
        skill = args[1]
        project_dir = Path(args[2])
        result = preflight(skill, project_dir)
        print(result.summary())
        sys.exit(0 if result.ready else 1)

    elif cmd == "post":
        if len(args) < 3:
            print("Usage: python -m lib.phase post <skill> <project-dir>")
            sys.exit(1)
        skill = args[1]
        project_dir = Path(args[2])
        result = postflight(skill, project_dir)
        print(result.summary())
        sys.exit(0 if result.valid else 1)

    elif cmd == "status":
        project_dir = Path(args[1])
        result = project_health(project_dir)
        print(result.summary())
        sys.exit(0 if result.schema_ok and not result.validation_errors else 1)

    else:
        print(f"Unknown command: {cmd}")
        print(USAGE)
        sys.exit(1)


if __name__ == "__main__":
    main()
