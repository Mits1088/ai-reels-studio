"""
lib/brain/smoke_test.py — Minimal smoke tests for the brain diagnostic layer.

Run:
    PYTHONPATH=. python lib/brain/smoke_test.py

Tests (Phase 1):
  1. diagnose_project returns a valid Diagnosis for a complete project
  2. diagnose_project handles a missing project.json gracefully
  3. All Diagnosis fields are populated (no AttributeError)
  4. to_dict() serialises cleanly (no unserializable types)
  5. Human and JSON renderers don't crash
  6. Gate inventory is correct for a known project
  7. Unknown gate in gates_passed is flagged
  8. Gate–artifact mismatch detection

Tests (Phase 2 — staleness):
  9.  No staleness when all files are written in correct order
  10. High-confidence staleness: motion-intent newer than timeline
  11. Staleness filtered below tolerance (same-run writes)
  12. Multiple dependencies: script change cascades to beat-map and reconciliation
  13. Review-feedback-after-QA signal
  14. staleness_results serialises in to_dict()
  15. Missing downstream → no false positive (dep skipped)
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

# Ensure we can import from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lib.brain import diagnose_project
from lib.brain.artifacts import ARTIFACT_REGISTRY, DEPENDENCY_MAP
from lib.brain.models import Diagnosis
from lib.brain.staleness import detect_staleness, STALE_TOLERANCE_SECONDS


# ── helpers ───────────────────────────────────────────────────────────────────

def ok(msg: str) -> None:
    print(f"  \033[32m✓\033[0m  {msg}")

def fail(msg: str, exc: Exception | None = None) -> None:
    print(f"  \033[31m✗\033[0m  {msg}")
    if exc:
        print(f"      {type(exc).__name__}: {exc}")
    sys.exit(1)


# ── test 1: missing project.json ──────────────────────────────────────────────

def test_missing_project():
    with tempfile.TemporaryDirectory() as tmp:
        d = diagnose_project(Path(tmp))
        assert not d.project_json_found, "Expected project_json_found=False"
        assert d.autonomy.next_action_actor in ("human", "unknown")
        assert isinstance(d.gates.missing, list) and len(d.gates.missing) > 0
    ok("missing project.json → returns Diagnosis with project_json_found=False")


# ── test 2: minimal valid project.json ───────────────────────────────────────

_MINIMAL_PJ = {
    "schema_version": 2,
    "project_type": "reel",
    "slug": "test-smoke",
    "title": "Smoke Test Reel",
    "phase": "script",
    "status": "in_progress",
    "gates_passed": ["brief_approved", "theme_set"],
    "created": "2026-01-01T00:00:00Z",
    "updated": "2026-01-01T00:00:00Z",
    "style": "cinematic-presenter",
    # theme fields required when theme_set gate is passed (validate_project enforces this)
    "theme": "test",
    "theme_primary": "#000000",
    "theme_secondary": "#FFFFFF",
}

def test_minimal_project():
    with tempfile.TemporaryDirectory() as tmp:
        pj = Path(tmp) / "project.json"
        pj.write_text(json.dumps(_MINIMAL_PJ), encoding="utf-8")

        d = diagnose_project(Path(tmp))

        assert d.project_json_found, "Expected project_json_found=True"
        assert d.slug == "test-smoke"
        assert "brief_approved" in d.gates.passed
        assert "theme_set" in d.gates.passed
        assert "script_approved" in d.gates.missing
        assert d.gates.next_required == "script_approved"
        assert d.autonomy.human_required is True, "script_approved requires human"
    ok("minimal project.json → correct gate inventory and human_required=True")


# ── test 3: all gates passed ──────────────────────────────────────────────────

_ALL_GATES_PJ = {k: v for k, v in _MINIMAL_PJ.items()}
_ALL_GATES_PJ["gates_passed"] = [
    "brief_approved", "theme_set", "script_approved",
    "reconciliation_resolved", "visual_assignment_approved",
    "asset_fitness_passed", "technical_planning_approved",
    "motion_intent_reviewed", "assets_validated",
    "preview_passed", "qa_passed",
]
_ALL_GATES_PJ["phase"] = "render"
_ALL_GATES_PJ["status"] = "approved"

def test_all_gates_passed():
    with tempfile.TemporaryDirectory() as tmp:
        pj = Path(tmp) / "project.json"
        pj.write_text(json.dumps(_ALL_GATES_PJ), encoding="utf-8")

        d = diagnose_project(Path(tmp))
        assert d.gates.next_required is None
        assert d.autonomy.can_continue_autonomously is True
        assert d.autonomy.human_required is False
    ok("all 11 gates passed → can_continue_autonomously=True")


# ── test 4: to_dict() is JSON-serialisable ───────────────────────────────────

def test_to_dict_serialisable():
    with tempfile.TemporaryDirectory() as tmp:
        pj = Path(tmp) / "project.json"
        pj.write_text(json.dumps(_MINIMAL_PJ), encoding="utf-8")
        d = diagnose_project(Path(tmp))
        try:
            serialised = json.dumps(d.to_dict())
            assert len(serialised) > 100
        except (TypeError, ValueError) as e:
            fail("to_dict() is not JSON-serialisable", e)
    ok("to_dict() produces clean JSON-serialisable dict")


# ── test 5: human renderer doesn't crash ─────────────────────────────────────

def test_human_renderer():
    from lib.brain.__main__ import _render_human
    with tempfile.TemporaryDirectory() as tmp:
        pj = Path(tmp) / "project.json"
        pj.write_text(json.dumps(_MINIMAL_PJ), encoding="utf-8")
        d = diagnose_project(Path(tmp))
        try:
            rendered = _render_human(d)
            assert "test-smoke" in rendered
        except Exception as e:
            fail("Human renderer crashed", e)
    ok("Human renderer produces output containing the slug")


# ── test 6: unknown gate in gates_passed is flagged ──────────────────────────

def test_unknown_gate():
    pj_data = dict(_MINIMAL_PJ)
    pj_data["gates_passed"] = ["brief_approved", "fantasy_gate_xyz"]
    with tempfile.TemporaryDirectory() as tmp:
        pj = Path(tmp) / "project.json"
        pj.write_text(json.dumps(pj_data), encoding="utf-8")
        d = diagnose_project(Path(tmp))
        assert "fantasy_gate_xyz" in d.gates.unknown_gates
    ok("Unknown gate in gates_passed is surfaced in unknown_gates list")


# ── test 7: gate–artifact mismatch detection ─────────────────────────────────

def test_gate_artifact_mismatch():
    pj_data = dict(_MINIMAL_PJ)
    pj_data["gates_passed"] = ["brief_approved", "theme_set", "script_approved"]
    with tempfile.TemporaryDirectory() as tmp:
        pj = Path(tmp) / "project.json"
        pj.write_text(json.dumps(pj_data), encoding="utf-8")
        # brief_approved is set but brief.md is NOT on disk → should flag mismatch
        d = diagnose_project(Path(tmp))
        mismatches = d.artifacts.gate_artifact_mismatches
        assert any("brief_approved" in m for m in mismatches), (
            f"Expected brief_approved mismatch, got: {mismatches}"
        )
    ok("Gate set but artifact missing → flagged as gate_artifact_mismatch")


# ── test 8: real project (if available) ──────────────────────────────────────

def test_real_project():
    repo_root = Path(__file__).resolve().parents[2]
    # Try a few known slugs
    for slug in ("claude-managed-agents", "gemma-4", "chatgpt-secret-codes"):
        proj = repo_root / "projects" / slug
        if proj.exists():
            try:
                d = diagnose_project(proj)
                assert d.project_json_found
                assert d.slug == slug
                # Serialise to confirm no surprises
                json.dumps(d.to_dict())
                ok(f"Real project '{slug}' → Diagnosis({len(d.gates.passed)}/{d.gates.total} gates, "
                   f"healthy={d.healthy})")
            except Exception as e:
                fail(f"Real project '{slug}' crashed", e)
            return  # one real project is enough
    print("  \033[33m-\033[0m  No real projects found to test against (skipped)")


# ── Phase 2: staleness helpers ────────────────────────────────────────────────

def _write(path: Path, content: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _touch(path: Path, offset_seconds: float = 0.0) -> None:
    """Set a file's mtime to now + offset_seconds."""
    now = time.time() + offset_seconds
    os.utime(path, (now, now))


# ── test 9: no staleness when files are in correct chronological order ─────────

def test_no_staleness_clean_project():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        t0 = time.time() - 1000  # anchor in the past

        # Write files in pipeline order with 60s gaps between each
        pairs = [
            ("script.md",             t0),
            ("audio/reconciliation.md", t0 + 60),
            ("audio/beat-map.json",   t0 + 120),
            ("audio/captions.json",   t0 + 180),
            ("shot-list.md",          t0 + 240),
            ("output/motion-intent.md", t0 + 300),
            ("output/timeline.json",  t0 + 360),
            ("output/qa_report.json", t0 + 420),
        ]
        for rel, ts in pairs:
            fp = p / rel
            _write(fp)
            os.utime(fp, (ts, ts))

        results = detect_staleness(p)
        assert results == [], (
            f"Expected no staleness but got: {[(r.upstream, r.downstream) for r in results]}"
        )
    ok("Clean pipeline order → no staleness detected")


# ── test 10: high-confidence staleness: motion-intent newer than timeline ──────

def test_high_confidence_staleness():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        t0 = time.time() - 5000

        # timeline written first, motion-intent updated much later
        _write(p / "output/timeline.json")
        _write(p / "output/motion-intent.md")
        os.utime(p / "output/timeline.json",    (t0,          t0))
        os.utime(p / "output/motion-intent.md", (t0 + 3600,   t0 + 3600))

        results = detect_staleness(p)
        motions = [r for r in results
                   if r.upstream == "output/motion-intent.md"
                   and r.downstream == "output/timeline.json"]
        assert motions, "Expected motion-intent → timeline staleness"
        assert motions[0].confidence == "high", (
            f"Expected high confidence, got {motions[0].confidence}"
        )
        assert motions[0].age_delta_seconds >= 3598
    ok("motion-intent 1h newer than timeline → high-confidence staleness")


# ── test 11: below-tolerance writes are NOT flagged ────────────────────────────

def test_below_tolerance_not_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        t0 = time.time() - 100

        _write(p / "output/timeline.json")
        _write(p / "output/motion-intent.md")
        # motion-intent is only 1s newer — within STALE_TOLERANCE_SECONDS (2s)
        os.utime(p / "output/timeline.json",    (t0,      t0))
        os.utime(p / "output/motion-intent.md", (t0 + 1,  t0 + 1))

        results = detect_staleness(p)
        motions = [r for r in results
                   if r.upstream == "output/motion-intent.md"
                   and r.downstream == "output/timeline.json"]
        assert not motions, (
            f"Should not flag sub-tolerance write (1s delta), got: {motions}"
        )
    ok(f"Delta ≤ {STALE_TOLERANCE_SECONDS}s (same-run write) → not flagged")


# ── test 12: script change cascades to beat-map and reconciliation ─────────────

def test_script_change_cascades():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        t0 = time.time() - 7200  # 2 hours ago

        # Original pipeline order
        for rel, ts in [
            ("audio/beat-map.json",      t0),
            ("audio/reconciliation.md",  t0 + 60),
            ("script.md",                t0 + 120),  # Script written AFTER both
        ]:
            fp = p / rel
            _write(fp)
            os.utime(fp, (ts, ts))

        # Script was later edited (now 1 hour newer than downstream artifacts)
        new_script_ts = t0 + 3600
        os.utime(p / "script.md", (new_script_ts, new_script_ts))

        results = detect_staleness(p)
        downstreams = {r.downstream for r in results}
        assert "audio/reconciliation.md" in downstreams, (
            "Expected script → reconciliation staleness"
        )
        assert "audio/beat-map.json" in downstreams, (
            "Expected script → beat-map staleness"
        )
    ok("Edited script → staleness detected for both reconciliation and beat-map")


# ── test 13: review-feedback after QA signals re-run ──────────────────────────

def test_review_feedback_after_qa():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        t0 = time.time() - 3600

        _write(p / "output/qa_report.json", '{"verdict": "PASS"}')
        _write(p / "output/review-feedback.md")
        os.utime(p / "output/qa_report.json",    (t0,          t0))
        os.utime(p / "output/review-feedback.md", (t0 + 1800,   t0 + 1800))

        results = detect_staleness(p)
        feedback_signals = [
            r for r in results
            if r.upstream == "output/review-feedback.md"
            and r.downstream == "output/qa_report.json"
        ]
        assert feedback_signals, (
            "Expected review-feedback → qa_report staleness signal"
        )
        r = feedback_signals[0]
        assert r.confidence in ("medium", "high"), (
            f"Unexpected confidence: {r.confidence}"
        )
    ok("Review feedback newer than QA report → re-run signal emitted")


# ── test 14: staleness_results serialises in to_dict() ────────────────────────

def test_staleness_results_serialisable():
    pj_data = dict(_MINIMAL_PJ)
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        pj = p / "project.json"
        pj.write_text(json.dumps(pj_data), encoding="utf-8")

        # Make motion-intent newer than timeline
        _write(p / "output/motion-intent.md")
        _write(p / "output/timeline.json")
        t0 = time.time() - 600
        os.utime(p / "output/timeline.json",    (t0,          t0))
        os.utime(p / "output/motion-intent.md", (t0 + 400,    t0 + 400))

        d = diagnose_project(p)
        try:
            serialised = json.dumps(d.to_dict())
            assert "staleness_results" in serialised
        except (TypeError, ValueError) as e:
            fail("staleness_results in to_dict() is not JSON-serialisable", e)
    ok("staleness_results in to_dict() produces clean JSON-serialisable dict")


# ── test 15: missing downstream → no false positive ───────────────────────────

def test_missing_downstream_no_false_positive():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        # Only write the upstream — downstream doesn't exist yet
        _write(p / "output/motion-intent.md")

        results = detect_staleness(p)
        falses = [r for r in results
                  if r.upstream == "output/motion-intent.md"
                  and r.downstream == "output/timeline.json"]
        assert not falses, (
            "Should not flag staleness when downstream is missing"
        )
    ok("Missing downstream artifact → dependency skipped, no false positive")


# ── test 16: artifact registry completeness ────────────────────────────────────

def test_artifact_registry_completeness():
    # Every upstream and downstream in DEPENDENCY_MAP must be in ARTIFACT_REGISTRY
    all_paths = {dep.upstream for dep in DEPENDENCY_MAP} | {dep.downstream for dep in DEPENDENCY_MAP}
    missing = all_paths - set(ARTIFACT_REGISTRY.keys())
    assert not missing, (
        f"DEPENDENCY_MAP references paths not in ARTIFACT_REGISTRY: {missing}"
    )
    ok("All DEPENDENCY_MAP paths are registered in ARTIFACT_REGISTRY")


# ── Phase 3: project_type-aware brain ────────────────────────────────────────

_YOUTUBE_PJ = {
    "schema_version": 2,
    "project_type": "youtube",
    "slug": "test-youtube",
    "title": "Test YouTube Project",
    "phase": "init",
    "status": "in_progress",
    "gates_passed": ["brief_approved"],
    "created": "2026-01-01T00:00:00Z",
    "updated": "2026-01-01T00:00:00Z",
    "style": "editorial-authority",
    "theme": "claude",
    "theme_primary": "#D97757",
    "theme_secondary": "#E8B88A",
}

_NO_TYPE_PJ = {
    "schema_version": 2,
    "slug": "test-no-type",
    "title": "Test No Type Project",
    "phase": "script",
    "status": "in_progress",
    "gates_passed": [],
    "created": "2026-01-01T00:00:00Z",
    "updated": "2026-01-01T00:00:00Z",
    "style": "cinematic-presenter",
    "theme": "test",
    "theme_primary": "#000000",
    "theme_secondary": "#FFFFFF",
}


# ── test 17: reel project uses reel gates (11 gates) ─────────────────────────

def test_reel_project_uses_reel_gates():
    from lib.constants import GATE_ORDER
    with tempfile.TemporaryDirectory() as tmp:
        pj = Path(tmp) / "project.json"
        pj.write_text(json.dumps(_MINIMAL_PJ), encoding="utf-8")
        d = diagnose_project(Path(tmp))

        assert d.project_type == "reel", f"Expected project_type=reel, got {d.project_type}"
        assert d.project_type_support == "supported"
        assert d.gates.total == len(GATE_ORDER), (
            f"Expected {len(GATE_ORDER)} gates for reel, got {d.gates.total}"
        )
        assert "gates" in d.to_dict()
        assert d.to_dict()["gates"]["total"] == len(GATE_ORDER)
    ok(f"Reel project → gate_count={len(GATE_ORDER)}, project_type=reel, project_type_support=supported")


# ── test 18: youtube project skips reel gates ─────────────────────────────────

def test_youtube_project_skips_reel_gates():
    with tempfile.TemporaryDirectory() as tmp:
        pj = Path(tmp) / "project.json"
        pj.write_text(json.dumps(_YOUTUBE_PJ), encoding="utf-8")
        d = diagnose_project(Path(tmp))

        d_dict = d.to_dict()

        assert d.project_type == "youtube", f"Expected project_type=youtube, got {d.project_type}"
        assert d.project_type_support == "unsupported", (
            f"Expected project_type_support=unsupported, got {d.project_type_support}"
        )
        assert d_dict["project_type"] == "youtube"
        assert d_dict["project_type_support"] == "unsupported"

        # Reel gate IDs must NOT appear in gates inventory
        reel_gate_ids = {
            "brief_approved", "theme_set", "script_approved", "reconciliation_resolved",
            "visual_assignment_approved", "asset_fitness_passed", "technical_planning_approved",
            "motion_intent_reviewed", "assets_validated", "preview_passed", "qa_passed",
        }
        reported_gates = set(d.gates.passed) | set(d.gates.missing)
        overlap = reported_gates & reel_gate_ids
        assert not overlap, (
            f"YouTube project reported Reel gate IDs: {overlap}"
        )

        # gates.total must be 0 (no Reel gate count reported)
        assert d.gates.total == 0, f"Expected gates.total=0 for YouTube, got {d.gates.total}"

        # Autonomy must be can_continue=False, human_required=False
        assert d.autonomy.can_continue_autonomously is False
        assert d.autonomy.human_required is False
        assert "YouTube" in d.autonomy.human_required_reason or \
               "YouTube" in d.autonomy.next_action, (
            "YouTube autonomy verdict should mention YouTube"
        )

    ok("YouTube project → no Reel gate IDs, project_type_support=unsupported, autonomy blocked")


# ── test 19: unknown project_type → safe stop ─────────────────────────────────

def test_unknown_project_type_safe_stop():
    with tempfile.TemporaryDirectory() as tmp:
        pj = Path(tmp) / "project.json"
        pj.write_text(json.dumps(_NO_TYPE_PJ), encoding="utf-8")
        d = diagnose_project(Path(tmp))

        assert d.project_type == "unknown", f"Expected project_type=unknown, got {d.project_type}"
        assert d.project_type_support == "unknown"

        # Must have a validation_error about project_type
        type_errors = [e for e in d.validation_errors if "project_type" in e]
        assert type_errors, (
            f"Expected validation_error about project_type, got: {d.validation_errors}"
        )

        # Autonomy must not allow autonomous continuation
        assert d.autonomy.can_continue_autonomously is False

        # to_dict() must include the project_type fields
        d_dict = d.to_dict()
        assert d_dict["project_type"] == "unknown"
        assert d_dict["project_type_support"] == "unknown"

    ok("Missing project_type → validation_error, project_type=unknown, can_continue=False")


# ── test 20: autonomous-reel SKILL.md contains project_type check ─────────────

def test_autonomous_reel_stops_on_youtube():
    skill_path = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "autonomous-reel" / "SKILL.md"
    assert skill_path.exists(), f"SKILL.md not found at {skill_path}"
    content = skill_path.read_text(encoding="utf-8")

    assert "project_type check" in content, (
        "SKILL.md should contain 'project_type check' section"
    )
    assert "⛔ Not a reel project" in content, (
        "SKILL.md should contain the stop message for non-reel projects"
    )
    assert "/youtube skill suite" in content, (
        "SKILL.md should mention the /youtube skill suite for YouTube projects"
    )
    assert "set project_type in project.json" in content, (
        "SKILL.md should mention setting project_type for unknown type"
    )

    ok("autonomous-reel SKILL.md contains project_type check at top of Decision Tree")


# ── test 21: sweep labels project_types ───────────────────────────────────────

def test_sweep_labels_project_types():
    from lib.brain.sweep import sweep_projects, format_sweep_table, format_sweep_json, ProjectSummary

    with tempfile.TemporaryDirectory() as projects_root:
        root = Path(projects_root)

        # Create a reel project
        reel_dir = root / "test-reel-sweep"
        reel_dir.mkdir()
        (reel_dir / "project.json").write_text(json.dumps(_MINIMAL_PJ | {"slug": "test-reel-sweep"}), encoding="utf-8")

        # Create a YouTube project
        yt_dir = root / "test-yt-sweep"
        yt_dir.mkdir()
        (yt_dir / "project.json").write_text(json.dumps(_YOUTUBE_PJ | {"slug": "test-yt-sweep"}), encoding="utf-8")

        # Create an unknown-type project
        unk_dir = root / "test-unk-sweep"
        unk_dir.mkdir()
        (unk_dir / "project.json").write_text(json.dumps(_NO_TYPE_PJ | {"slug": "test-unk-sweep"}), encoding="utf-8")

        summaries = sweep_projects(root)

        # Check project_type field is present and correct
        types_found = {s.slug: s.project_type for s in summaries}
        assert types_found.get("test-reel-sweep") == "reel", (
            f"Reel project should have project_type=reel, got {types_found}"
        )
        assert types_found.get("test-yt-sweep") == "youtube", (
            f"YouTube project should have project_type=youtube, got {types_found}"
        )
        assert types_found.get("test-unk-sweep") == "unknown", (
            f"No-type project should have project_type=unknown, got {types_found}"
        )

        # Sweep table output should contain project_type labels
        table = format_sweep_table(summaries)
        assert "reel" in table, "Sweep table should mention 'reel'"
        assert "youtube" in table, "Sweep table should mention 'youtube'"
        assert "unknown" in table, "Sweep table should mention 'unknown'"

        # Sweep JSON should have project_type field
        sweep_json = format_sweep_json(summaries)
        parsed = json.loads(sweep_json)
        project_types_in_json = {p["slug"]: p["project_type"] for p in parsed}
        assert project_types_in_json.get("test-reel-sweep") == "reel"
        assert project_types_in_json.get("test-yt-sweep") == "youtube"
        assert project_types_in_json.get("test-unk-sweep") == "unknown"

        # YouTube project must NOT count as a broken reel project
        yt_summary = next(s for s in summaries if s.slug == "test-yt-sweep")
        assert yt_summary.gates_total == 0, (
            f"YouTube project should have gates_total=0, not treated as broken reel. "
            f"Got {yt_summary.gates_total}"
        )

    ok("Sweep labels project_types correctly; YouTube not counted as broken reel")


# ── run all ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nlib.brain smoke tests\n")

    print("Phase 1 — diagnostic surface")
    test_missing_project()
    test_minimal_project()
    test_all_gates_passed()
    test_to_dict_serialisable()
    test_human_renderer()
    test_unknown_gate()
    test_gate_artifact_mismatch()
    test_real_project()

    print("\nPhase 2 — staleness detection")
    test_no_staleness_clean_project()
    test_high_confidence_staleness()
    test_below_tolerance_not_flagged()
    test_script_change_cascades()
    test_review_feedback_after_qa()
    test_staleness_results_serialisable()
    test_missing_downstream_no_false_positive()
    test_artifact_registry_completeness()

    print("\nPhase 3 — project_type-aware brain")
    test_reel_project_uses_reel_gates()
    test_youtube_project_skips_reel_gates()
    test_unknown_project_type_safe_stop()
    test_autonomous_reel_stops_on_youtube()
    test_sweep_labels_project_types()

    print("\n\033[32mAll smoke tests passed.\033[0m\n")
