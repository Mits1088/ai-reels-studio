"""
lib.brain — AI Reels production brain: diagnose, advance, repair, sweep.

Primary entry points:
    from lib.brain import diagnose_project
    from lib.brain import advance_project, repair_project, sweep_projects

CLI:
    python -m lib.brain diagnose projects/<slug>
    python -m lib.brain diagnose projects/<slug> --json
    python -m lib.brain advance  projects/<slug>
    python -m lib.brain advance  projects/<slug> --dry-run
    python -m lib.brain repair   projects/<slug>
    python -m lib.brain sweep    projects/
    python -m lib.brain sweep    projects/ --json
"""

__version__ = "1.4.0"
__phase__ = "Phase 1B v2 — repair status/confidence/notes; sweep qa_status/critic_status/stale_count/recommended_action"

from .diagnose import diagnose_project
from .models import Diagnosis
from .advance import advance_project, AdvanceResult
from .repair import repair_project, generate_repair_plan, RepairPlan, RepairStep
from .sweep import sweep_projects, format_sweep_table, format_sweep_json, ProjectSummary

__all__ = [
    "diagnose_project",
    "Diagnosis",
    "advance_project",
    "AdvanceResult",
    "repair_project",
    "generate_repair_plan",
    "RepairPlan",
    "RepairStep",
    "sweep_projects",
    "format_sweep_table",
    "format_sweep_json",
    "ProjectSummary",
]
