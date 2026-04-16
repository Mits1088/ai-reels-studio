"""
lib/orchestrator/validators.py — Artifact existence checks and parity enforcement.

Used by the CLI before critical phases to surface blockers early.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .spec import PHASES, PARITY_REQUIRED_BEFORE
from .state import ProjectSnapshot


@dataclass
class ValidationFailure:
    phase: str
    kind: str   # "missing_file" | "missing_gate" | "parity_failed"
    message: str
    fix_hint: str


def validate_phase_preconditions(
    phase_key: str,
    snap: ProjectSnapshot,
) -> list[ValidationFailure]:
    """
    Check all preconditions for a phase: required gates, required files,
    and parity (if the phase is parity-critical).
    Returns a list of failures (empty = all clear).
    """
    failures: list[ValidationFailure] = []
    spec = PHASES.get(phase_key)
    if spec is None:
        failures.append(ValidationFailure(
            phase=phase_key,
            kind="missing_file",
            message=f"Unknown phase: {phase_key!r}",
            fix_hint="Check the phase key against lib/orchestrator/spec.py PHASES",
        ))
        return failures

    g = set(snap.gates_passed)

    # Check required gates
    for gate in spec.required_gates:
        if gate not in g:
            failures.append(ValidationFailure(
                phase=phase_key,
                kind="missing_gate",
                message=f"Gate '{gate}' not passed",
                fix_hint=f"python -m lib.orchestrator approve {snap.slug} {gate}",
            ))

    # Check required files
    for rel_path in spec.required_files:
        full_path = snap.project_dir / rel_path
        if not full_path.exists():
            failures.append(ValidationFailure(
                phase=phase_key,
                kind="missing_file",
                message=f"Required file missing: {rel_path}",
                fix_hint=f"Run the phase that produces {rel_path}",
            ))

    # Parity checks for critical phases
    if phase_key in PARITY_REQUIRED_BEFORE:
        parity_failures = _run_parity_checks(phase_key)
        failures.extend(parity_failures)

    return failures


def _run_parity_checks(phase_key: str) -> list[ValidationFailure]:
    """Run lib.parity checks. Return failures as ValidationFailure objects."""
    failures: list[ValidationFailure] = []
    try:
        from lib.parity import run_checks
        results = run_checks()
        for r in results:
            if not r.passed:
                label = "REQUIRED" if r.check.must_match else "FORBIDDEN"
                failures.append(ValidationFailure(
                    phase=phase_key,
                    kind="parity_failed",
                    message=f"[{label}] {r.check.description} — {r.detail}",
                    fix_hint=r.check.fix_hint,
                ))
    except ImportError:
        pass  # parity module not available — skip silently
    return failures


def check_required_artifacts(snap: ProjectSnapshot) -> list[str]:
    """
    Return list of expected pipeline artifacts that are missing.
    Used by `diagnose` to surface the full picture.
    """
    g = set(snap.gates_passed)
    project_dir = snap.project_dir
    missing: list[str] = []

    # Artifacts expected at each gate level
    artifact_gates: list[tuple[str, str]] = [
        ("brief_approved", "brief.md"),
        ("script_approved", "script.md"),
        ("reconciliation_resolved", "audio/beat-map.json"),
        ("reconciliation_resolved", "audio/reconciliation.md"),
        ("reconciliation_resolved", "audio/captions.json"),
        ("visual_assignment_approved", "shot-list.md"),
        ("motion_intent_reviewed", "output/motion-intent.md"),
        ("assets_validated", "assets/sourced/catalog.json"),
        ("preview_passed", "output/timeline.json"),
        ("qa_passed", "output/qa-report.md"),
    ]

    for gate, artifact in artifact_gates:
        if gate in g:
            full_path = project_dir / artifact
            if not full_path.exists():
                missing.append(f"{artifact} (expected: gate '{gate}' was passed)")

    return missing
