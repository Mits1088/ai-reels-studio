"""
lib/orchestrator/executors.py — Per-actor execution handlers.

Three executors:
  CodeExecutor   — runs TASKS[phase_key] directly; sets gate on success
  ClaudeExecutor — builds a WorkOrder and returns paused_for_claude
  HumanExecutor  — builds a HumanAction and returns paused_for_human

Routed by actor field on PhaseSpec.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .results import ExecResult, ExecStatus, WorkOrder, HumanAction
from .spec import PHASES, PhaseSpec
from .state import ProjectSnapshot
from .tasks import get_task, TaskResult
from .events import log_event


# ── Code executor ──────────────────────────────────────────────────────────

class CodeExecutor:
    """Executes code-only phases by calling the registered task function."""

    def execute(self, phase_key: str, snap: ProjectSnapshot) -> ExecResult:
        spec = PHASES.get(phase_key)
        if spec is None:
            return _error_result(phase_key, "unknown", f"No phase spec for '{phase_key}'")

        task = get_task(phase_key)
        if task is None:
            return ExecResult(
                phase_key=phase_key,
                phase_name=spec.name,
                actor=spec.actor,
                status=ExecStatus.SKIPPED,
                output=f"No executable task registered for '{phase_key}' — run manually.",
                error=None,
            )

        try:
            task_result: TaskResult = task(snap.project_dir)
        except Exception as e:
            log_event(snap.project_dir, actor="code", action=f"exec {phase_key}",
                      phase=phase_key, result="failed", notes=str(e))
            return _error_result(phase_key, spec.actor, str(e), phase_name=spec.name)

        status = ExecStatus.SUCCESS if task_result.exit_code == 0 else ExecStatus.FAILED
        gate_set = None

        if task_result.exit_code == 0 and task_result.sets_gate:
            _set_gate_silent(snap.project_dir, task_result.sets_gate)
            gate_set = task_result.sets_gate

        log_event(
            snap.project_dir,
            actor="code",
            action=f"exec {phase_key}",
            phase=phase_key,
            gates_before=snap.gates_passed,
            gates_after=_reload_gates(snap.project_dir),
            result=status.value,
            notes=task_result.error or "",
        )

        return ExecResult(
            phase_key=phase_key,
            phase_name=spec.name,
            actor=spec.actor,
            status=status,
            duration_s=task_result.duration_s,
            exit_code=task_result.exit_code,
            output=task_result.output,
            error=task_result.error,
            gate_set=gate_set,
        )


# ── Claude executor ────────────────────────────────────────────────────────

class ClaudeExecutor:
    """
    Builds a WorkOrder for a Claude-required phase and returns
    paused_for_claude. The orchestrator pauses; Claude does the work
    in conversation; human approves to continue.
    """

    def execute(self, phase_key: str, snap: ProjectSnapshot) -> ExecResult:
        spec = PHASES.get(phase_key)
        if spec is None:
            return _error_result(phase_key, "claude", f"No phase spec for '{phase_key}'")

        work_order = _build_work_order(phase_key, spec, snap)

        log_event(
            snap.project_dir,
            actor="code",
            action=f"pause for claude: {phase_key}",
            phase=phase_key,
            result="paused",
            notes="Work order emitted",
        )

        return ExecResult(
            phase_key=phase_key,
            phase_name=spec.name,
            actor=spec.actor,
            status=ExecStatus.PAUSED_FOR_CLAUDE,
            work_order=work_order,
        )


# ── Human executor ─────────────────────────────────────────────────────────

class HumanExecutor:
    """
    Builds a HumanAction checklist and returns paused_for_human.
    """

    def execute(self, phase_key: str, snap: ProjectSnapshot) -> ExecResult:
        spec = PHASES.get(phase_key)
        if spec is None:
            return _error_result(phase_key, "human", f"No phase spec for '{phase_key}'")

        human_action = _build_human_action(phase_key, spec, snap)

        log_event(
            snap.project_dir,
            actor="code",
            action=f"pause for human: {phase_key}",
            phase=phase_key,
            result="paused",
            notes="Human action emitted",
        )

        return ExecResult(
            phase_key=phase_key,
            phase_name=spec.name,
            actor=spec.actor,
            status=ExecStatus.PAUSED_FOR_HUMAN,
            human_action=human_action,
        )


# ── Routing ────────────────────────────────────────────────────────────────

def route_executor(phase_key: str, snap: ProjectSnapshot) -> ExecResult:
    """
    Route a phase to the correct executor based on its actor type.
    For "code+claude" hybrids where code can run first, runs code part
    then pauses for Claude if code succeeds.
    """
    spec = PHASES.get(phase_key)
    if spec is None:
        return _error_result(phase_key, "unknown", f"No phase spec for '{phase_key}'")

    actor = spec.actor

    if actor == "code":
        return CodeExecutor().execute(phase_key, snap)

    elif actor == "claude":
        return ClaudeExecutor().execute(phase_key, snap)

    elif actor == "human":
        return HumanExecutor().execute(phase_key, snap)

    elif actor in ("code+claude", "human+claude"):
        # Code part first (if registered), then pause for Claude
        task = get_task(phase_key)
        if task:
            code_result = CodeExecutor().execute(phase_key, snap)
            if not code_result.succeeded:
                return code_result  # code failed — don't proceed to Claude
        # Pause for Claude
        return ClaudeExecutor().execute(phase_key, snap)

    else:
        # Treat unknown actor as requiring Claude
        return ClaudeExecutor().execute(phase_key, snap)


# ── Work order builder ─────────────────────────────────────────────────────

def _build_work_order(phase_key: str, spec: PhaseSpec, snap: ProjectSnapshot) -> WorkOrder:
    """Build a rich WorkOrder from phase spec + project context."""
    ctx = _load_phase_context(phase_key, snap)
    memory_to_read, rules_to_apply = _phase_reading_list(phase_key)

    # Approval command
    if spec.sets_gate:
        approval_cmd = f"python -m lib.orchestrator approve {snap.slug} {spec.sets_gate}"
    else:
        approval_cmd = f"python -m lib.orchestrator approve {snap.slug} <gate>"

    return WorkOrder(
        phase_key=phase_key,
        phase_name=spec.name,
        purpose=spec.purpose,
        project_slug=snap.slug,
        creative_intent_required=spec.creative_intent_required,
        memory_to_read=memory_to_read,
        rules_to_apply=rules_to_apply,
        context=ctx,
        input_files=list(spec.required_files),
        output_files=list(spec.output_files),
        approval_command=approval_cmd,
        sets_gate=spec.sets_gate,
    )


def _build_human_action(phase_key: str, spec: PhaseSpec, snap: ProjectSnapshot) -> HumanAction:
    """Build a HumanAction checklist for a human-required phase."""
    steps = _human_steps(phase_key, snap)
    if spec.sets_gate:
        approval_cmd = f"python -m lib.orchestrator approve {snap.slug} {spec.sets_gate}"
    else:
        approval_cmd = f"python -m lib.orchestrator approve {snap.slug} <gate>"

    rejection_cmd = f"python -m lib.orchestrator reject {snap.slug} {phase_key}"

    return HumanAction(
        phase_key=phase_key,
        phase_name=spec.name,
        project_slug=snap.slug,
        description=spec.purpose,
        steps=steps,
        approval_command=approval_cmd,
        rejection_command=rejection_cmd,
    )


# ── Phase context loader ───────────────────────────────────────────────────

def _load_phase_context(phase_key: str, snap: ProjectSnapshot) -> dict[str, Any]:
    """Load relevant project context for a Claude work order."""
    proj = snap.project_json
    ctx: dict[str, Any] = {
        "style": snap.style,
        "theme": f"{snap.theme} ({snap.theme_primary})",
    }

    # Standard project fields
    for field in ["target_duration_seconds", "hook_direction", "cta_direction",
                  "topic", "audience", "content_type", "input_quality"]:
        if proj.get(field):
            ctx[field] = proj[field]

    # Beat map context (for shot-list, motion-intent, assembly phases)
    if phase_key in {
        "shot-list-4b-i", "shot-list-4b-ii", "shot-list-4b-iii",
        "motion-intent", "assemble-reel", "qa-reel",
    }:
        beat_map_path = snap.project_dir / "audio" / "beat-map.json"
        if beat_map_path.exists():
            try:
                bm = json.loads(beat_map_path.read_text(encoding="utf-8"))
                beats = bm.get("beats", [])
                ctx["beat_count"] = len(beats)
                ctx["actual_duration_s"] = f"{bm.get('total_duration', 0):.1f}s"
                if bm.get("editorial_grain"):
                    ctx["editorial_grain"] = bm["editorial_grain"]
            except Exception:
                pass

    # Asset catalog context (for visual assignment phases)
    if phase_key in {"shot-list-4b-i", "shot-list-4b-ii"}:
        catalog_path = snap.project_dir / "assets" / "sourced" / "catalog.json"
        if catalog_path.exists():
            try:
                cat = json.loads(catalog_path.read_text(encoding="utf-8"))
                assets = cat.get("assets", [])
                ctx["asset_count"] = len(assets)
                types = list(set(a.get("asset_type", "?") for a in assets))
                ctx["asset_types"] = ", ".join(sorted(types))
            except Exception:
                pass

    # B-roll context
    broll_path = snap.project_dir / "broll_scenes" / "scene_list.json"
    if broll_path.exists() and phase_key in {"shot-list-4b-i"}:
        try:
            bl = json.loads(broll_path.read_text(encoding="utf-8"))
            ctx["broll_scenes"] = len(bl.get("scenes", bl if isinstance(bl, list) else []))
        except Exception:
            pass

    return ctx


def _phase_reading_list(phase_key: str) -> tuple[list[str], list[str]]:
    """Return (memory_to_read, rules_to_apply) for each Claude phase."""

    CREATIVE_CORE = [
        "docs/creative-direction.md",
        "memory/creative-feedback.json",
        "training/derived/taste-rules.json",
    ]
    HOOK_BODY = [
        ".claude/rules/hook-grammar.md",
        ".claude/rules/body-grammar.md",
    ]
    COMPONENT_RULES = [
        ".claude/rules/component-mapping.md",
        ".claude/rules/component-selection-scoring.md",
    ]
    MOTION_RULES = [
        ".claude/rules/motion-grammar.md",
    ]

    mapping: dict[str, tuple[list[str], list[str]]] = {
        "reel-script": (
            CREATIVE_CORE,
            HOOK_BODY + [".claude/rules/reel-workflow.md"],
        ),
        "shot-list-4b-i": (
            CREATIVE_CORE,
            HOOK_BODY + [".claude/rules/reel-workflow.md"],
        ),
        "shot-list-4b-ii": (
            ["memory/creative-feedback.json"],
            COMPONENT_RULES,
        ),
        "shot-list-4b-iii": (
            [],
            [".claude/rules/visual-style.md", ".claude/rules/reel-workflow.md"],
        ),
        "motion-intent": (
            ["memory/creative-feedback.json"],
            MOTION_RULES + [".claude/rules/body-grammar.md"],
        ),
        "assemble-reel": (
            ["memory/creative-feedback.json"],
            [".claude/rules/remotion-skill-required.md"],
        ),
        "script-reconcile": (
            [],
            [".claude/rules/timing-sync.md"],
        ),
        "source-brief": (
            CREATIVE_CORE,
            [".claude/rules/reel-workflow.md"],
        ),
        "feedback-capture": (
            ["memory/creative-feedback.json"],
            [".claude/rules/reel-learning.md"],
        ),
        "revision": (
            CREATIVE_CORE,
            [".claude/rules/change-pipeline.md"],
        ),
    }
    return mapping.get(phase_key, ([], []))


# ── Human steps builder ────────────────────────────────────────────────────

def _human_steps(phase_key: str, snap: ProjectSnapshot) -> list[str]:
    """Build numbered step checklist for a human phase."""
    steps_map: dict[str, list[str]] = {
        "ingest-voice": [
            f"Generate ElevenLabs audio from script.md (copy the ElevenLabs script block)",
            "Generate HeyGen portrait (9:16) avatar video using the ElevenLabs audio",
            "Download source.wav from ElevenLabs or extract from avatar video",
            f"Place files: source.wav in project root, avatar*.mp4 in project root",
            "Run beat-map generation: python -m lib.ingest.beat_mapper projects/<slug>",
        ],
        "preview": [
            f"Open Remotion studio: cd remotion && npx remotion studio",
            "Scrub to hook (frames 0–15): logo visible? avatar in split? real product UI?",
            "Scrub to first demo: correct asset? audio sync?",
            "Scrub to midpoint: proof visible? no stale patterns?",
            "Scrub to CTA (last 3s): CTA renders? ends cleanly?",
            "Check captions: mobile-readable? no '--' pause markers? correct spelling?",
        ],
        "benchmark": [
            "Watch the rendered reel once through",
            "Fill in training/benchmark-scorecard.md (9 dimensions, 1–5 scores)",
            "Use projects/_shared/benchmark-review-template.md for structured review",
            "Record the lowest-scoring dimension and its fix",
            "If same dimension scores low in 2+ benchmarks: run /feedback-capture",
        ],
    }
    return steps_map.get(phase_key, [f"Complete the '{phase_key}' phase manually"])


# ── Helpers ────────────────────────────────────────────────────────────────

def _error_result(phase_key: str, actor: str, message: str,
                  phase_name: str = "") -> ExecResult:
    return ExecResult(
        phase_key=phase_key,
        phase_name=phase_name or phase_key,
        actor=actor,
        status=ExecStatus.FAILED,
        error=message,
    )


def _set_gate_silent(project_dir: Path, gate_id: str) -> None:
    """Set a gate without printing output."""
    try:
        from lib.gates import set_gate
        set_gate(project_dir, gate_id)
    except Exception:
        pass


def _reload_gates(project_dir: Path) -> list[str]:
    """Reload gates_passed from project.json."""
    try:
        pf = project_dir / "project.json"
        import json
        return json.loads(pf.read_text(encoding="utf-8")).get("gates_passed", [])
    except Exception:
        return []
