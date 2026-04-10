"""
Gate enforcement for the reel pipeline.

Programmatic enforcement of the 11-gate system defined in
.claude/rules/gate-enforcement.md. Every skill must pass its
gate check before starting work.

CLI:
    PYTHONPATH=. python -m lib.gates check  projects/<slug> <skill-name>
    PYTHONPATH=. python -m lib.gates set    projects/<slug> <gate-id>
    PYTHONPATH=. python -m lib.gates reset  projects/<slug> <gate-id>
    PYTHONPATH=. python -m lib.gates status projects/<slug>
"""

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from lib.constants import VALID_GATE_IDS, GATE_ORDER, YOUTUBE_GATE_ORDER


# ── Skill-to-gate mapping ───────────────────────────────────────────────────
# From .claude/rules/gate-enforcement.md — coded as data.

SKILL_PREREQS: dict[str, dict] = {
    # Reel skills
    "source-brief":      {"gates": [],                                                          "files": []},
    "theme-factory":     {"gates": [],                                                          "files": ["project.json"]},
    "reel-script":       {"gates": ["brief_approved", "theme_set"],                             "files": ["brief.md", "project.json"]},
    "broll-pipeline":    {"gates": ["script_approved"],                                         "files": ["script.md"]},
    "ingest-voice":      {"gates": ["script_approved"],                                         "files": ["script.md"]},
    "script-reconcile":  {"gates": [],                                                          "files": ["audio/voice.json", "script.md"]},
    "caption-polish":    {"gates": ["reconciliation_resolved"],                                 "files": ["audio/captions.json", "audio/beat-map.json"]},
    "capture-demo":      {"gates": ["reconciliation_resolved"],                                 "files": ["audio/beat-map.json"]},
    "shot-list":         {"gates": ["reconciliation_resolved"],                                 "files": ["audio/beat-map.json"]},
    "shot-list-4b-i":    {"gates": ["reconciliation_resolved"],                                 "files": ["audio/beat-map.json"]},
    "shot-list-4b-ii":   {"gates": ["visual_assignment_approved"],                              "files": ["shot-list.md"]},
    "shot-list-4b-iii":  {"gates": ["asset_fitness_passed"],                                    "files": ["shot-list.md"]},
    "motion-intent":     {"gates": ["technical_planning_approved"],                             "files": ["shot-list.md"]},
    "asset-prep":        {"gates": ["technical_planning_approved"],                             "files": []},
    "assemble-reel":     {"gates": ["motion_intent_reviewed", "assets_validated"],              "files": ["output/motion-intent.md"]},
    "qa-reel":           {"gates": ["preview_passed"],                                          "files": ["output/timeline.json"]},
    "render":            {"gates": ["qa_passed"],                                               "files": ["output/qa-report.md"]},
    # YouTube skills
    "youtube-ingest":    {"gates": [],                                                          "files": []},
    "youtube-overlay":   {"gates": ["video_ingested"],                                          "files": ["audio/beat-map.json"]},
    # Cross-phase / utility skills
    "frontend-design":   {"gates": [],                                                          "files": []},
    "apply-change":      {"gates": [],                                                          "files": ["output/timeline.json"]},
}


# ── Data classes ─────────────────────────────────────────��──────────────────

@dataclass
class GateCheckResult:
    """Result of checking whether a skill's prerequisites are met."""
    passed: bool
    skill: str
    failures: list[str] = field(default_factory=list)

    def summary(self) -> str:
        if self.passed:
            return f"PASSED — {self.skill} can proceed."
        lines = [f"BLOCKED — {self.skill} cannot start. {len(self.failures)} issue(s):"]
        for f in self.failures:
            lines.append(f"  - {f}")
        return "\n".join(lines)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _load_project(project_dir: Path) -> dict:
    pj_path = project_dir / "project.json"
    if not pj_path.exists():
        raise FileNotFoundError(f"project.json not found in {project_dir}")
    with open(pj_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_project(project_dir: Path, data: dict) -> None:
    pj_path = project_dir / "project.json"
    data["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(pj_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


# ── Core functions ────────────────────────────────────────��─────────────────

def check_gates(project_dir: Path, skill_name: str) -> GateCheckResult:
    """Check whether all prerequisites for a skill are met.

    Reads project.json, verifies required gates are in gates_passed,
    and verifies required files exist on disk.
    """
    if skill_name not in SKILL_PREREQS:
        return GateCheckResult(
            passed=False,
            skill=skill_name,
            failures=[f"Unknown skill: {skill_name!r}. Known skills: {', '.join(sorted(SKILL_PREREQS))}"],
        )

    prereqs = SKILL_PREREQS[skill_name]
    failures: list[str] = []

    # Load project.json
    try:
        project = _load_project(project_dir)
    except FileNotFoundError:
        return GateCheckResult(
            passed=False,
            skill=skill_name,
            failures=[f"project.json not found in {project_dir}"],
        )

    gates_passed = set(project.get("gates_passed", []))

    # Check required gates
    for gate_id in prereqs["gates"]:
        if gate_id not in gates_passed:
            # Find which skill sets this gate
            setter = _gate_setter(gate_id)
            failures.append(f"Gate '{gate_id}' not passed.{f' Run {setter} first.' if setter else ''}")

    # Check required files
    for rel_path in prereqs["files"]:
        full_path = project_dir / rel_path
        if not full_path.exists():
            failures.append(f"Required file not found: {rel_path}")

    return GateCheckResult(
        passed=len(failures) == 0,
        skill=skill_name,
        failures=failures,
    )


def set_gate(project_dir: Path, gate_id: str) -> str:
    """Mark a gate as passed in project.json."""
    if gate_id not in VALID_GATE_IDS:
        return f"ERROR: Unknown gate ID: {gate_id!r}. Valid: {', '.join(GATE_ORDER)}"

    project = _load_project(project_dir)
    gates = project.get("gates_passed", [])

    if gate_id in gates:
        return f"Gate '{gate_id}' is already passed."

    gates.append(gate_id)
    project["gates_passed"] = gates
    _save_project(project_dir, project)
    return f"Gate '{gate_id}' set. ({len(gates)}/{len(GATE_ORDER)} gates passed)"


def reset_gate(project_dir: Path, gate_id: str) -> str:
    """Remove a gate and all downstream gates from project.json.

    Downstream means any gate at a higher index in GATE_ORDER.
    This implements the cascading reset from gate-enforcement.md.
    """
    if gate_id not in VALID_GATE_IDS:
        return f"ERROR: Unknown gate ID: {gate_id!r}. Valid: {', '.join(GATE_ORDER)}"

    project = _load_project(project_dir)
    gates = project.get("gates_passed", [])

    # Find the index of the gate to reset
    try:
        reset_idx = GATE_ORDER.index(gate_id)
    except ValueError:
        return f"ERROR: Gate '{gate_id}' not in GATE_ORDER."

    # Remove this gate and everything downstream
    gates_to_remove = set(GATE_ORDER[reset_idx:])
    removed = [g for g in gates if g in gates_to_remove]
    remaining = [g for g in gates if g not in gates_to_remove]

    if not removed:
        return f"Gate '{gate_id}' was not set (nothing to reset)."

    project["gates_passed"] = remaining
    project["status"] = "in_progress"
    _save_project(project_dir, project)

    return f"Reset {len(removed)} gate(s): {', '.join(removed)}. Remaining: {len(remaining)}/{len(GATE_ORDER)}"


def gate_status(project_dir: Path) -> str:
    """Show all gates and their current status."""
    project = _load_project(project_dir)
    gates_passed = set(project.get("gates_passed", []))
    slug = project.get("slug", project_dir.name)
    phase = project.get("phase", "?")
    status = project.get("status", "?")

    lines = [
        f"Project: {slug}",
        f"Phase:   {phase}",
        f"Status:  {status}",
        f"Gates:   {len(gates_passed)}/{len(GATE_ORDER)}",
        "",
    ]

    for gate_id in GATE_ORDER:
        marker = "[x]" if gate_id in gates_passed else "[ ]"
        lines.append(f"  {marker} {gate_id}")

    # Check for unknown gates in the array
    unknown = gates_passed - VALID_GATE_IDS
    if unknown:
        lines.append("")
        lines.append(f"  WARNING: Unknown gates in array: {', '.join(sorted(unknown))}")

    return "\n".join(lines)


# ── Lookup helper ───────────────────────────────────────────────────────────

_GATE_SETTERS = {
    "brief_approved":               "source-brief (Phase 0) + user approval",
    "theme_set":                    "theme-factory (Phase 0b)",
    "script_approved":              "reel-script (Phase 1) + user approval",
    "reconciliation_resolved":      "script-reconcile (Phase 2b)",
    "visual_assignment_approved":   "shot-list 4b-i + user approval",
    "asset_fitness_passed":         "shot-list 4b-ii (auto — zero MISMATCH/MISSING)",
    "technical_planning_approved":  "shot-list 4b-iii + user approval",
    "motion_intent_reviewed":       "motion-intent (Phase 4c) + user review",
    "assets_validated":             "asset-prep (Phase 4d)",
    "preview_passed":               "quick preview (Phase 5b)",
    "qa_passed":                    "qa-reel (Phase 6)",
}


def _gate_setter(gate_id: str) -> str:
    return _GATE_SETTERS.get(gate_id, "")


# ── CLI ─────────────────────────────────────────────────────────────────────

USAGE = """\
Usage:
  python -m lib.gates check  <project-dir> <skill-name>   Check if skill can run
  python -m lib.gates set    <project-dir> <gate-id>       Mark gate as passed
  python -m lib.gates reset  <project-dir> <gate-id>       Reset gate + downstream
  python -m lib.gates status <project-dir>                 Show all gate statuses

Skills: {skills}
Gates:  {gates}
""".format(
    skills=", ".join(sorted(SKILL_PREREQS)),
    gates=", ".join(GATE_ORDER),
)


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 2:
        print(USAGE)
        sys.exit(1)

    cmd = args[0]
    project_dir = Path(args[1])

    if not project_dir.exists():
        print(f"ERROR: Directory not found: {project_dir}")
        sys.exit(1)

    if cmd == "check":
        if len(args) < 3:
            print("Usage: python -m lib.gates check <project-dir> <skill-name>")
            sys.exit(1)
        result = check_gates(project_dir, args[2])
        print(result.summary())
        sys.exit(0 if result.passed else 1)

    elif cmd == "set":
        if len(args) < 3:
            print("Usage: python -m lib.gates set <project-dir> <gate-id>")
            sys.exit(1)
        msg = set_gate(project_dir, args[2])
        print(msg)
        sys.exit(1 if msg.startswith("ERROR") else 0)

    elif cmd == "reset":
        if len(args) < 3:
            print("Usage: python -m lib.gates reset <project-dir> <gate-id>")
            sys.exit(1)
        msg = reset_gate(project_dir, args[2])
        print(msg)
        sys.exit(1 if msg.startswith("ERROR") else 0)

    elif cmd == "status":
        msg = gate_status(project_dir)
        print(msg)
        sys.exit(0)

    else:
        print(f"Unknown command: {cmd}")
        print(USAGE)
        sys.exit(1)


if __name__ == "__main__":
    main()
