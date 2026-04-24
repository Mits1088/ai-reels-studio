"""
Tests for lib.brain.sweep — portfolio health scan.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lib.brain.sweep import (
    ProjectSummary,
    format_sweep_json,
    format_sweep_table,
    sweep_projects,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_summary(
    slug: str = "proj-a",
    phase: str = "script",
    gates_passed: int = 3,
    gates_total: int = 11,
    healthy: bool = True,
    qa_status: str = "not_run",
    critic_status: str = "not_run",
    stale_count: int = 0,
    can_continue: bool = True,
    human_required: bool = False,
    recommended_action: str = "run phase",
) -> ProjectSummary:
    return ProjectSummary(
        slug=slug,
        phase=phase,
        gates_passed=gates_passed,
        gates_total=gates_total,
        healthy=healthy,
        qa_status=qa_status,
        critic_status=critic_status,
        stale_count=stale_count,
        can_continue=can_continue,
        human_required=human_required,
        recommended_action=recommended_action,
    )


def _make_fake_diag(
    slug: str,
    healthy: bool = True,
    can_continue: bool = True,
    human_required: bool = False,
    gates_passed: int = 3,
    qa_verdict: str = "not_run",
    critic_status: str = "not_run",
    stale_high_count: int = 0,
) -> MagicMock:
    d = MagicMock()
    d.slug = slug
    d.phase = "script"
    d.healthy = healthy

    d.gates.passed = list(range(gates_passed))
    d.gates.total = 11

    d.qa.available = qa_verdict != "not_run"
    d.qa.verdict = qa_verdict

    d.critic.available = critic_status != "not_run"
    d.critic.status = critic_status

    stale = []
    for _ in range(stale_high_count):
        r = MagicMock()
        r.confidence = "high"
        stale.append(r)
    d.artifacts.staleness_results = stale

    d.autonomy.can_continue_autonomously = can_continue
    d.autonomy.human_required = human_required
    d.autonomy.next_action = "run next phase"
    d.autonomy.next_action_actor = "code"

    return d


# ── Required spec tests ────────────────────────────────────────────────────────

class TestSpecRequired:
    """Spec-mandated test names verified here."""

    def test_sweep_skips_underscore_prefixed_dirs(self, tmp_path):
        """Directories starting with '_' must be excluded."""
        (tmp_path / "_shared").mkdir()
        (tmp_path / "_shared" / "project.json").write_text("{}")
        (tmp_path / "proj-real").mkdir()
        (tmp_path / "proj-real" / "project.json").write_text("{}")

        fake_diag = _make_fake_diag("proj-real")
        with patch("lib.brain.sweep.diagnose_project", return_value=fake_diag):
            summaries = sweep_projects(tmp_path)

        slugs = [s.slug for s in summaries]
        assert "proj-real" in slugs
        assert "_shared" not in slugs

    def test_sweep_skips_dirs_without_project_json(self, tmp_path):
        """Directories lacking project.json must be excluded."""
        (tmp_path / "no-json-dir").mkdir()
        (tmp_path / "proj-valid").mkdir()
        (tmp_path / "proj-valid" / "project.json").write_text("{}")

        fake_diag = _make_fake_diag("proj-valid")
        with patch("lib.brain.sweep.diagnose_project", return_value=fake_diag):
            summaries = sweep_projects(tmp_path)

        slugs = [s.slug for s in summaries]
        assert "proj-valid" in slugs
        assert "no-json-dir" not in slugs

    def test_sweep_returns_summary_per_project(self, tmp_path):
        """Each valid project directory produces exactly one ProjectSummary."""
        for name in ("proj-1", "proj-2", "proj-3"):
            (tmp_path / name).mkdir()
            (tmp_path / name / "project.json").write_text("{}")

        diags = {n: _make_fake_diag(n) for n in ("proj-1", "proj-2", "proj-3")}

        def _diagnose(path, **kwargs):
            return diags[path.name]

        with patch("lib.brain.sweep.diagnose_project", side_effect=_diagnose):
            summaries = sweep_projects(tmp_path)

        assert len(summaries) == 3
        assert {s.slug for s in summaries} == {"proj-1", "proj-2", "proj-3"}

    def test_sweep_sorts_blocked_first(self, tmp_path):
        """Blocked projects (not healthy, not human_required, not can_continue)
        must sort before healthy projects."""
        for name in ("healthy-proj", "blocked-proj"):
            (tmp_path / name).mkdir()
            (tmp_path / name / "project.json").write_text("{}")

        diags = {
            "healthy-proj": _make_fake_diag("healthy-proj", healthy=True, can_continue=True),
            "blocked-proj": _make_fake_diag(
                "blocked-proj", healthy=False, can_continue=False, human_required=False
            ),
        }

        def _diagnose(path, **kwargs):
            return diags[path.name]

        with patch("lib.brain.sweep.diagnose_project", side_effect=_diagnose):
            summaries = sweep_projects(tmp_path)

        assert summaries[0].slug == "blocked-proj"

    def test_sweep_supports_json_output(self, tmp_path):
        """format_sweep_json returns valid JSON with required fields."""
        (tmp_path / "proj-a").mkdir()
        (tmp_path / "proj-a" / "project.json").write_text("{}")

        fake_diag = _make_fake_diag("proj-a")
        with patch("lib.brain.sweep.diagnose_project", return_value=fake_diag):
            summaries = sweep_projects(tmp_path)

        raw = format_sweep_json(summaries)
        parsed = json.loads(raw)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["slug"] == "proj-a"
        assert "qa_status" in parsed[0]
        assert "critic_status" in parsed[0]
        assert "stale_count" in parsed[0]
        assert "recommended_action" in parsed[0]


# ── T1: Directory filtering ────────────────────────────────────────────────────

class TestDirectoryFiltering:
    def test_underscore_dirs_skipped(self, tmp_path):
        (tmp_path / "_shared").mkdir()
        (tmp_path / "_shared" / "project.json").write_text("{}")
        (tmp_path / "proj-a").mkdir()
        (tmp_path / "proj-a" / "project.json").write_text("{}")

        fake_diag = _make_fake_diag("proj-a")
        with patch("lib.brain.sweep.diagnose_project", return_value=fake_diag):
            summaries = sweep_projects(tmp_path)

        slugs = [s.slug for s in summaries]
        assert "proj-a" in slugs
        assert "_shared" not in slugs

    def test_dirs_without_project_json_skipped(self, tmp_path):
        (tmp_path / "no-json-dir").mkdir()
        (tmp_path / "proj-b").mkdir()
        (tmp_path / "proj-b" / "project.json").write_text("{}")

        fake_diag = _make_fake_diag("proj-b")
        with patch("lib.brain.sweep.diagnose_project", return_value=fake_diag):
            summaries = sweep_projects(tmp_path)

        slugs = [s.slug for s in summaries]
        assert "proj-b" in slugs
        assert "no-json-dir" not in slugs

    def test_exception_in_diagnose_skipped_silently(self, tmp_path):
        for name in ("proj-ok", "proj-broken"):
            (tmp_path / name).mkdir()
            (tmp_path / name / "project.json").write_text("{}")

        ok_diag = _make_fake_diag("proj-ok")

        def _diagnose(path, **kwargs):
            if path.name == "proj-broken":
                raise RuntimeError("corrupt project")
            return ok_diag

        with patch("lib.brain.sweep.diagnose_project", side_effect=_diagnose):
            summaries = sweep_projects(tmp_path)

        slugs = [s.slug for s in summaries]
        assert "proj-ok" in slugs
        assert "proj-broken" not in slugs


# ── T2: Sorting ────────────────────────────────────────────────────────────────

class TestSorting:
    def test_blocked_before_healthy(self):
        summaries = [
            _make_summary(slug="healthy", healthy=True, can_continue=True),
            _make_summary(slug="blocked", healthy=False, can_continue=False, human_required=False),
        ]
        from lib.brain.sweep import _sort_key
        summaries.sort(key=_sort_key)
        assert summaries[0].slug == "blocked"

    def test_human_required_before_stale(self):
        summaries = [
            _make_summary(slug="stale", healthy=False, can_continue=False,
                          human_required=False, stale_count=2),
            _make_summary(slug="waiting", healthy=False, can_continue=False,
                          human_required=True),
        ]
        from lib.brain.sweep import _sort_key
        summaries.sort(key=_sort_key)
        assert summaries[0].slug == "waiting"

    def test_blocked_before_can_advance(self):
        summaries = [
            _make_summary(slug="advanceable", healthy=False, can_continue=True),
            _make_summary(slug="blocked", healthy=False, can_continue=False,
                          human_required=False),
        ]
        from lib.brain.sweep import _sort_key
        summaries.sort(key=_sort_key)
        assert summaries[0].slug == "blocked"

    def test_sweep_returns_sorted_result(self, tmp_path):
        for name in ("proj-z", "proj-a"):
            (tmp_path / name).mkdir()
            (tmp_path / name / "project.json").write_text("{}")

        diags = {
            "proj-z": _make_fake_diag("proj-z", healthy=False, can_continue=False,
                                       human_required=False),
            "proj-a": _make_fake_diag("proj-a", healthy=True),
        }

        def _diagnose(path, **kwargs):
            return diags[path.name]

        with patch("lib.brain.sweep.diagnose_project", side_effect=_diagnose):
            summaries = sweep_projects(tmp_path)

        assert summaries[0].slug == "proj-z"


# ── T3: Staleness count ────────────────────────────────────────────────────────

class TestStalenessCount:
    def test_stale_count_populated(self, tmp_path):
        (tmp_path / "proj-stale").mkdir()
        (tmp_path / "proj-stale" / "project.json").write_text("{}")

        fake_diag = _make_fake_diag("proj-stale", stale_high_count=3)
        with patch("lib.brain.sweep.diagnose_project", return_value=fake_diag):
            summaries = sweep_projects(tmp_path)

        assert summaries[0].stale_count == 3

    def test_no_stale_when_all_low_confidence(self, tmp_path):
        (tmp_path / "proj-clean").mkdir()
        (tmp_path / "proj-clean" / "project.json").write_text("{}")

        d = _make_fake_diag("proj-clean")
        low = MagicMock()
        low.confidence = "low"
        d.artifacts.staleness_results = [low, low]

        with patch("lib.brain.sweep.diagnose_project", return_value=d):
            summaries = sweep_projects(tmp_path)

        assert summaries[0].stale_count == 0

    def test_stale_count_sorts_unhealthy_tier(self, tmp_path):
        """Stale projects (stale_count>0) sort into tier 2 (unhealthy)."""
        for name in ("proj-stale", "proj-healthy"):
            (tmp_path / name).mkdir()
            (tmp_path / name / "project.json").write_text("{}")

        diags = {
            "proj-stale": _make_fake_diag("proj-stale", healthy=False, stale_high_count=1),
            "proj-healthy": _make_fake_diag("proj-healthy", healthy=True, stale_high_count=0),
        }

        def _diagnose(path, **kwargs):
            return diags[path.name]

        with patch("lib.brain.sweep.diagnose_project", side_effect=_diagnose):
            summaries = sweep_projects(tmp_path)

        assert summaries[0].slug == "proj-stale"


# ── T4: Critic status ─────────────────────────────────────────────────────────

class TestCriticStatus:
    def test_critic_status_in_summary(self, tmp_path):
        (tmp_path / "proj-critic").mkdir()
        (tmp_path / "proj-critic" / "project.json").write_text("{}")

        d = _make_fake_diag("proj-critic", critic_status="critic_blocked")
        with patch("lib.brain.sweep.diagnose_project", return_value=d):
            summaries = sweep_projects(tmp_path)

        assert summaries[0].critic_status == "critic_blocked"

    def test_critic_not_run_when_unavailable(self, tmp_path):
        (tmp_path / "proj-no-critic").mkdir()
        (tmp_path / "proj-no-critic" / "project.json").write_text("{}")

        d = _make_fake_diag("proj-no-critic", critic_status="not_run")
        with patch("lib.brain.sweep.diagnose_project", return_value=d):
            summaries = sweep_projects(tmp_path)

        assert summaries[0].critic_status == "not_run"


# ── T5: format_sweep_table ────────────────────────────────────────────────────

class TestFormatSweepTable:
    def test_no_summaries_returns_message(self):
        result = format_sweep_table([])
        assert "No projects found" in result

    def test_table_contains_slug(self):
        s = _make_summary(slug="my-project")
        result = format_sweep_table([s])
        assert "my-project" in result

    def test_table_contains_phase(self):
        s = _make_summary(slug="proj", phase="beat-map")
        result = format_sweep_table([s])
        assert "beat-map" in result

    def test_table_contains_gates(self):
        s = _make_summary(slug="proj", gates_passed=5, gates_total=11)
        result = format_sweep_table([s])
        assert "5/11" in result

    def test_stale_tag_shown(self):
        s = _make_summary(slug="proj", stale_count=2)
        result = format_sweep_table([s])
        assert "⚠" in result

    def test_no_crash_on_long_slug(self):
        s = _make_summary(slug="a" * 50)
        result = format_sweep_table([s])
        assert result  # must not raise


# ── T6: format_sweep_json ─────────────────────────────────────────────────────

class TestFormatSweepJson:
    def test_json_is_valid(self):
        summaries = [_make_summary(slug="proj-a"), _make_summary(slug="proj-b")]
        raw = format_sweep_json(summaries)
        parsed = json.loads(raw)
        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_json_contains_new_fields(self):
        s = _make_summary(slug="proj-x")
        parsed = json.loads(format_sweep_json([s]))[0]
        assert "qa_status" in parsed
        assert "critic_status" in parsed
        assert "stale_count" in parsed
        assert "recommended_action" in parsed

    def test_json_does_not_contain_old_fields(self):
        s = _make_summary(slug="proj-x")
        parsed = json.loads(format_sweep_json([s]))[0]
        assert "qa_verdict" not in parsed
        assert "stale_high" not in parsed
        assert "next_action" not in parsed
        assert "next_actor" not in parsed

    def test_empty_list_returns_empty_json_array(self):
        raw = format_sweep_json([])
        parsed = json.loads(raw)
        assert parsed == []
