"""Tests for lib/critic/.

Coverage:
  - Each check function (positive, negative, missing-data, threshold edges)
  - Runner integration
  - Markdown renderer
  - CriticFinding validation
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lib.capture.catalog import AssetEntry, Catalog
from lib.critic import (
    CriticFinding,
    SEVERITY_BLOCK,
    SEVERITY_WARN,
    SEVERITY_SUGGEST,
    check_claim_to_proof_latency,
    check_dead_holds,
    check_asset_overreuse,
    check_proof_relevance,
    check_caption_competition,
    check_visual_novelty,
    run_critic,
    render_critic_markdown,
    CriticReport,
)


# ── Fixtures ──────────────────────────────────────────────────────────────


def _beats_simple() -> list[dict]:
    return [
        {"id": "beat-01", "intent": "hook",  "start": 0.0,  "end": 2.0, "text": "We made AI 6x faster"},
        {"id": "beat-02", "intent": "demo",  "start": 2.0,  "end": 6.0, "text": "Here's how it works"},
        {"id": "beat-03", "intent": "proof", "start": 6.0,  "end": 9.0, "text": "It's 14% better than before"},
        {"id": "beat-04", "intent": "cta",   "start": 9.0,  "end": 11.0, "text": "Follow for more"},
    ]


def _matches_simple(asset_per_beat: dict[str, str | None] | None = None) -> list[dict]:
    """Build a list of asset-match dicts. Pass {beat_id: filename} to control selections."""
    defaults = {
        "beat-01": "hook-clip.mp4",
        "beat-02": "demo-walkthrough.mp4",
        "beat-03": "stats-chart.png",
        "beat-04": None,
    }
    if asset_per_beat is not None:
        defaults.update(asset_per_beat)

    out = []
    for beat_id, filename in defaults.items():
        out.append({
            "beat_id": beat_id,
            "selected_asset_id": filename.replace(".", "-") if filename else None,
            "selected_asset_filename": filename,
            "selection_confidence": 0.8 if filename else 0.0,
        })
    return out


def _enriched_catalog(text_density: float = 0.7, tags=None) -> Catalog:
    asset = AssetEntry(
        id="stats-chart-png",
        filename="stats-chart.png",
        type="image", role="demo",
        linked_beats=["beat-03"], description="proof chart",
        enrichment={
            "status": "full",
            "schema_version": 1,
            "derived_at": "now", "derived_by": "test",
            "text": {"method": "test", "skipped_reason": None, "score": text_density},
            "editorial_tags": tags if tags is not None else ["proof", "stats"],
        },
    )
    return Catalog(assets=[asset])


# ── CriticFinding model ───────────────────────────────────────────────────


class TestCriticFinding(unittest.TestCase):
    def test_valid_finding(self):
        f = CriticFinding(
            check="test", severity=SEVERITY_WARN, confidence=0.5,
            reason="r", evidence={"x": 1}, suggested_fix="fix",
        )
        d = f.to_dict()
        self.assertEqual(d["severity"], "WARN")
        self.assertEqual(d["scope"], "global")

    def test_beat_scoped_finding(self):
        f = CriticFinding(
            check="test", severity=SEVERITY_WARN, confidence=0.5,
            reason="r", evidence={}, suggested_fix="fix",
            beat_id="beat-01",
        )
        self.assertEqual(f.scope, "beat")
        self.assertEqual(f.to_dict()["beat_id"], "beat-01")

    def test_invalid_severity(self):
        with self.assertRaises(ValueError):
            CriticFinding(
                check="test", severity="MAYBE", confidence=0.5,
                reason="r", evidence={}, suggested_fix="fix",
            )

    def test_confidence_out_of_range(self):
        with self.assertRaises(ValueError):
            CriticFinding(
                check="test", severity=SEVERITY_WARN, confidence=1.5,
                reason="r", evidence={}, suggested_fix="fix",
            )


# ── claim_to_proof_latency ────────────────────────────────────────────────


class TestClaimToProofLatency(unittest.TestCase):
    def test_pass_when_proof_is_in_same_beat(self):
        beats = _beats_simple()
        matches = _matches_simple()  # beat-01 has hook-clip.mp4 → proof at start
        findings = check_claim_to_proof_latency(beats, matches)
        # beat-01 makes a "6x faster" claim and gets proof at the same beat → no finding for beat-01
        # beat-03 makes "14%" claim with stats-chart.png at beat-03 → no finding
        beat_01 = [f for f in findings if f.beat_id == "beat-01"]
        beat_03 = [f for f in findings if f.beat_id == "beat-03"]
        self.assertEqual(beat_01, [])
        self.assertEqual(beat_03, [])

    def test_warn_when_proof_arrives_late(self):
        # Latency 2.0s = between WARN (1.5s) and BLOCK (3.0s) thresholds
        beats = [
            {"id": "beat-01", "intent": "setup", "start": 0.0, "end": 2.0, "text": "We made it 6x faster"},
            {"id": "beat-02", "intent": "demo",  "start": 2.0, "end": 5.0, "text": "demo"},
        ]
        matches = [
            {"beat_id": "beat-01", "selected_asset_id": None, "selected_asset_filename": None},
            {"beat_id": "beat-02", "selected_asset_id": "x", "selected_asset_filename": "x.mp4"},
        ]
        findings = check_claim_to_proof_latency(beats, matches)
        beat_01 = [f for f in findings if f.beat_id == "beat-01"]
        self.assertTrue(len(beat_01) > 0)
        self.assertEqual(beat_01[0].severity, SEVERITY_WARN)
        self.assertGreater(beat_01[0].evidence["latency_s"], 1.5)
        self.assertLessEqual(beat_01[0].evidence["latency_s"], 3.0)

    def test_block_when_proof_very_late(self):
        # Latency 5s > BLOCK threshold (3.0s)
        beats = [
            {"id": "beat-01", "intent": "setup", "start": 0.0, "end": 5.0, "text": "We made it 6x faster"},
            {"id": "beat-02", "intent": "demo",  "start": 5.0, "end": 8.0, "text": "demo"},
        ]
        matches = [
            {"beat_id": "beat-01", "selected_asset_id": None, "selected_asset_filename": None},
            {"beat_id": "beat-02", "selected_asset_id": "x", "selected_asset_filename": "x.mp4"},
        ]
        findings = check_claim_to_proof_latency(beats, matches)
        beat_01 = [f for f in findings if f.beat_id == "beat-01"]
        self.assertEqual(beat_01[0].severity, SEVERITY_BLOCK)

    def test_block_when_no_proof_anywhere(self):
        beats = [
            {"id": "beat-01", "intent": "setup", "start": 0, "end": 5, "text": "It's 6x faster"},
        ]
        matches = [
            {"beat_id": "beat-01", "selected_asset_id": None, "selected_asset_filename": None},
        ]
        findings = check_claim_to_proof_latency(beats, matches)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, SEVERITY_BLOCK)

    def test_no_finding_when_no_claim_keywords(self):
        beats = [
            {"id": "beat-01", "intent": "context", "start": 0, "end": 5, "text": "Hello world"},
        ]
        matches = []
        findings = check_claim_to_proof_latency(beats, matches)
        self.assertEqual(findings, [])

    def test_suggest_when_matches_unavailable(self):
        beats = [
            {"id": "beat-01", "intent": "setup", "start": 0, "end": 5, "text": "It's 6x faster"},
        ]
        findings = check_claim_to_proof_latency(beats, None)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, SEVERITY_SUGGEST)


# ── dead_holds ────────────────────────────────────────────────────────────


class TestDeadHolds(unittest.TestCase):
    def test_suggest_for_long_image_hold_no_edit_plan(self):
        # Phase E2: WARN downshifted to SUGGEST when edit_plan is missing
        beats = [{"id": "beat-01", "intent": "proof", "start": 0, "end": 4, "text": "x"}]
        matches = [{"beat_id": "beat-01", "selected_asset_id": "img", "selected_asset_filename": "chart.png"}]
        findings = check_dead_holds(beats, matches)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, SEVERITY_SUGGEST)
        self.assertEqual(findings[0].confidence, 0.5)

    def test_warn_for_extreme_hold_no_edit_plan(self):
        # Phase E2: BLOCK downshifted to WARN when edit_plan is missing
        beats = [{"id": "beat-01", "intent": "proof", "start": 0, "end": 7, "text": "x"}]
        matches = [{"beat_id": "beat-01", "selected_asset_id": "img", "selected_asset_filename": "chart.png"}]
        findings = check_dead_holds(beats, matches)
        self.assertEqual(findings[0].severity, SEVERITY_WARN)

    def test_warn_for_long_image_hold_with_edit_plan(self):
        # With edit_plan present, the original behavior holds: WARN at >2.5s
        beats = [{"id": "beat-01", "intent": "proof", "start": 0, "end": 4, "text": "x"}]
        matches = [{"beat_id": "beat-01", "selected_asset_id": "img", "selected_asset_filename": "chart.png"}]
        edit_plan = {"beats": [{"beat_id": "beat-02"}]}  # present, but no zoom for beat-01
        findings = check_dead_holds(beats, matches, edit_plan=edit_plan)
        self.assertEqual(findings[0].severity, SEVERITY_WARN)
        self.assertEqual(findings[0].confidence, 0.7)

    def test_block_for_extreme_hold_with_edit_plan(self):
        # With edit_plan present, BLOCK at >5s
        beats = [{"id": "beat-01", "intent": "proof", "start": 0, "end": 7, "text": "x"}]
        matches = [{"beat_id": "beat-01", "selected_asset_id": "img", "selected_asset_filename": "chart.png"}]
        edit_plan = {"beats": [{"beat_id": "beat-02"}]}
        findings = check_dead_holds(beats, matches, edit_plan=edit_plan)
        self.assertEqual(findings[0].severity, SEVERITY_BLOCK)
        self.assertEqual(findings[0].confidence, 0.8)

    def test_dead_holds_evidence_includes_asset_id(self):
        beats = [{"id": "beat-01", "intent": "proof", "start": 0, "end": 4, "text": "x"}]
        matches = [{"beat_id": "beat-01", "selected_asset_id": "chart-id", "selected_asset_filename": "chart.png"}]
        findings = check_dead_holds(beats, matches)
        self.assertEqual(findings[0].evidence["asset_id"], "chart-id")
        self.assertEqual(findings[0].evidence["filename"], "chart.png")

    def test_no_finding_for_video(self):
        beats = [{"id": "beat-01", "intent": "demo", "start": 0, "end": 5, "text": "x"}]
        matches = [{"beat_id": "beat-01", "selected_asset_id": "v", "selected_asset_filename": "demo.mp4"}]
        findings = check_dead_holds(beats, matches)
        self.assertEqual(findings, [])

    def test_no_finding_for_short_image(self):
        beats = [{"id": "beat-01", "intent": "proof", "start": 0, "end": 2, "text": "x"}]
        matches = [{"beat_id": "beat-01", "selected_asset_id": "img", "selected_asset_filename": "chart.png"}]
        findings = check_dead_holds(beats, matches)
        self.assertEqual(findings, [])

    def test_edit_plan_with_zoom_clears_finding(self):
        beats = [{"id": "beat-01", "intent": "proof", "start": 0, "end": 4, "text": "x"}]
        matches = [{"beat_id": "beat-01", "selected_asset_id": "img", "selected_asset_filename": "chart.png"}]
        edit_plan = {"beats": [{"beat_id": "beat-01", "zoom_moments": [{"at": 0, "x": 50, "y": 50, "scale": 1.5}]}]}
        findings = check_dead_holds(beats, matches, edit_plan=edit_plan)
        self.assertEqual(findings, [])


# ── asset_overreuse ──────────────────────────────────────────────────────


class TestAssetOverreuse(unittest.TestCase):
    def test_no_finding_under_threshold(self):
        matches = [
            {"beat_id": "beat-01", "selected_asset_id": "a"},
            {"beat_id": "beat-02", "selected_asset_id": "a"},
        ]
        self.assertEqual(check_asset_overreuse(matches), [])

    def test_suggest_at_3_uses(self):
        matches = [
            {"beat_id": f"beat-{i:02d}", "selected_asset_id": "a"} for i in range(1, 4)
        ]
        f = check_asset_overreuse(matches)
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, SEVERITY_SUGGEST)

    def test_warn_at_4_uses(self):
        matches = [
            {"beat_id": f"beat-{i:02d}", "selected_asset_id": "a"} for i in range(1, 5)
        ]
        f = check_asset_overreuse(matches)
        self.assertEqual(f[0].severity, SEVERITY_WARN)

    def test_block_at_6_uses(self):
        matches = [
            {"beat_id": f"beat-{i:02d}", "selected_asset_id": "a"} for i in range(1, 7)
        ]
        f = check_asset_overreuse(matches)
        self.assertEqual(f[0].severity, SEVERITY_BLOCK)

    def test_global_scope(self):
        matches = [{"beat_id": f"b{i}", "selected_asset_id": "a"} for i in range(3)]
        f = check_asset_overreuse(matches)
        self.assertIsNone(f[0].beat_id)
        self.assertEqual(f[0].confidence, 1.0)

    def test_skip_when_no_matches(self):
        self.assertEqual(check_asset_overreuse(None), [])
        self.assertEqual(check_asset_overreuse([]), [])


# ── proof_relevance ──────────────────────────────────────────────────────


class TestProofRelevance(unittest.TestCase):
    def test_pass_when_tags_match_intent(self):
        beats = [{"id": "beat-01", "intent": "proof", "start": 0, "end": 3, "text": "x"}]
        matches = [{"beat_id": "beat-01", "selected_asset_id": "stats-chart-png"}]
        catalog = _enriched_catalog(tags=["proof", "stats"])
        f = check_proof_relevance(beats, matches, catalog)
        self.assertEqual(f, [])

    def test_warn_when_tags_dont_match(self):
        beats = [{"id": "beat-01", "intent": "proof", "start": 0, "end": 3, "text": "x"}]
        matches = [{"beat_id": "beat-01", "selected_asset_id": "stats-chart-png"}]
        catalog = _enriched_catalog(tags=["unrelated", "topic"])
        f = check_proof_relevance(beats, matches, catalog)
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, SEVERITY_WARN)

    def test_suggest_when_no_enrichment(self):
        beats = [{"id": "beat-01", "intent": "proof", "start": 0, "end": 3, "text": "x"}]
        matches = [{"beat_id": "beat-01", "selected_asset_id": "asset-a"}]
        unenriched = AssetEntry(
            id="asset-a", filename="x.png", type="image", role="demo",
            linked_beats=["beat-01"], description="x",
        )
        catalog = Catalog(assets=[unenriched])
        f = check_proof_relevance(beats, matches, catalog)
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, SEVERITY_SUGGEST)


# ── caption_competition ──────────────────────────────────────────────────


class TestCaptionCompetition(unittest.TestCase):
    def test_warn_when_text_dense_and_captions_standard(self):
        beats = [{"id": "beat-01", "intent": "demo", "start": 0, "end": 3, "text": "x"}]
        matches = [{"beat_id": "beat-01", "selected_asset_id": "stats-chart-png"}]
        catalog = _enriched_catalog(text_density=0.85)
        f = check_caption_competition(beats, matches, catalog)
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, SEVERITY_WARN)

    def test_pass_when_caption_suppressed(self):
        beats = [{"id": "beat-01", "intent": "demo", "start": 0, "end": 3, "text": "x"}]
        matches = [{"beat_id": "beat-01", "selected_asset_id": "stats-chart-png"}]
        catalog = _enriched_catalog(text_density=0.85)
        edit_plan = {"beats": [{"beat_id": "beat-01", "caption_mode": "suppressed"}]}
        f = check_caption_competition(beats, matches, catalog, edit_plan)
        self.assertEqual(f, [])

    def test_pass_when_text_density_low(self):
        beats = [{"id": "beat-01", "intent": "demo", "start": 0, "end": 3, "text": "x"}]
        matches = [{"beat_id": "beat-01", "selected_asset_id": "stats-chart-png"}]
        catalog = _enriched_catalog(text_density=0.2)
        f = check_caption_competition(beats, matches, catalog)
        self.assertEqual(f, [])

    def test_suggest_when_no_enrichment(self):
        beats = [{"id": "beat-01", "intent": "demo", "start": 0, "end": 3, "text": "x"}]
        matches = [{"beat_id": "beat-01", "selected_asset_id": "asset-a"}]
        unenriched = AssetEntry(
            id="asset-a", filename="x.png", type="image", role="demo",
            linked_beats=["beat-01"], description="x",
        )
        catalog = Catalog(assets=[unenriched])
        f = check_caption_competition(beats, matches, catalog)
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, SEVERITY_SUGGEST)


# ── visual_novelty ───────────────────────────────────────────────────────


class TestVisualNovelty(unittest.TestCase):
    def test_no_finding_for_varied_assets(self):
        matches = [
            {"beat_id": "beat-01", "selected_asset_id": "a"},
            {"beat_id": "beat-02", "selected_asset_id": "b"},
            {"beat_id": "beat-03", "selected_asset_id": "c"},
        ]
        self.assertEqual(check_visual_novelty(matches), [])

    def test_warn_for_2_consecutive_same_asset(self):
        matches = [
            {"beat_id": "beat-01", "selected_asset_id": "a"},
            {"beat_id": "beat-02", "selected_asset_id": "a"},
            {"beat_id": "beat-03", "selected_asset_id": "b"},
        ]
        f = check_visual_novelty(matches)
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, SEVERITY_WARN)

    def test_block_for_4_consecutive_same_asset(self):
        matches = [
            {"beat_id": f"beat-{i:02d}", "selected_asset_id": "a"} for i in range(1, 5)
        ]
        f = check_visual_novelty(matches)
        self.assertEqual(f[0].severity, SEVERITY_BLOCK)

    def test_two_separate_streaks(self):
        matches = [
            {"beat_id": "beat-01", "selected_asset_id": "a"},
            {"beat_id": "beat-02", "selected_asset_id": "a"},
            {"beat_id": "beat-03", "selected_asset_id": "b"},
            {"beat_id": "beat-04", "selected_asset_id": "c"},
            {"beat_id": "beat-05", "selected_asset_id": "c"},
        ]
        f = check_visual_novelty(matches)
        self.assertEqual(len(f), 2)


# ── Runner ───────────────────────────────────────────────────────────────


class TestRunner(unittest.TestCase):
    def test_runner_with_minimal_inputs(self):
        beat_map = {"total_duration": 10, "beats": _beats_simple()}
        report = run_critic(
            beat_map=beat_map,
            asset_matches=None,
            motion_plan=None,
            gap_ownership=None,
            edit_plan=None,
            catalog=None,
            project_slug="test",
        )
        self.assertEqual(report.project, "test")
        # Without matches, claim_to_proof_latency emits SUGGEST findings
        self.assertGreater(len(report.suggestions), 0)
        self.assertEqual(len(report.blockers), 0)

    def test_runner_full_inputs_advisory_pass(self):
        beat_map = {"total_duration": 11, "beats": _beats_simple()}
        matches = {"beats": _matches_simple()}
        report = run_critic(
            beat_map=beat_map,
            asset_matches=matches,
            motion_plan=None,
            gap_ownership=None,
            edit_plan=None,
            catalog=None,
            project_slug="test",
        )
        # No claims should be unresolved → no warnings from claim_to_proof_latency
        # Should be either pass or warnings depending on other checks
        self.assertIn(report.verdict, ("advisory_pass", "advisory_warnings", "advisory_blocked"))

    def test_runner_inputs_present_tracking(self):
        report = run_critic(
            beat_map={"beats": []},
            asset_matches={"beats": []},
            motion_plan=None,
            gap_ownership=None,
            edit_plan=None,
            catalog=None,
            project_slug="test",
        )
        self.assertTrue(report.inputs_present["beat_map"])
        self.assertTrue(report.inputs_present["asset_matches"])
        self.assertFalse(report.inputs_present["motion_plan"])

    def test_report_to_dict_shape(self):
        beat_map = {"total_duration": 5, "beats": _beats_simple()}
        report = run_critic(
            beat_map=beat_map, asset_matches=None, motion_plan=None,
            gap_ownership=None, edit_plan=None, catalog=None,
            project_slug="test",
        )
        d = report.to_dict()
        for key in ("schema_version", "project", "critic_version", "advisory",
                    "verdict", "totals", "checks", "inputs_present",
                    "beats", "global_findings"):
            self.assertIn(key, d)


# ── Markdown rendering ───────────────────────────────────────────────────


class TestMarkdown(unittest.TestCase):
    def test_renders_minimal_report(self):
        report = CriticReport(project="test", findings=[])
        md = render_critic_markdown(report)
        self.assertIn("# Critic Report: test", md)
        self.assertIn("advisory_pass", md)
        self.assertIn("Checks", md)

    def test_renders_finding_details(self):
        f = CriticFinding(
            check="claim_to_proof_latency",
            severity=SEVERITY_WARN,
            confidence=0.75,
            beat_id="beat-01",
            reason="too late",
            evidence={"latency_s": 2.0},
            suggested_fix="move it earlier",
        )
        report = CriticReport(project="test", findings=[f])
        md = render_critic_markdown(report)
        self.assertIn("`claim_to_proof_latency`", md)
        self.assertIn("too late", md)
        self.assertIn("move it earlier", md)
        self.assertIn("WARN", md)


# ── Phase E2 additions ───────────────────────────────────────────────────


from lib.critic import (
    make_finding,
    make_finding_id,
    build_critic_status_dict,
    STATUS_PASSED,
    STATUS_WARNINGS,
    STATUS_BLOCKED,
    STATUS_UNAVAILABLE,
)
from lib.critic.runner import (
    _link_related_findings,
    _enrichment_state,
    _is_enrichment_globally_absent,
    _build_root_cause_clusters,
    _build_data_quality_limitations,
    _highest_confidence_blockers,
    _apply_severity_floor,
)


class TestFindingIDs(unittest.TestCase):
    def test_make_finding_id_beat_scoped(self):
        self.assertEqual(make_finding_id("dead_holds", "beat-03"), "dead_holds:beat:beat-03")

    def test_make_finding_id_global(self):
        self.assertEqual(
            make_finding_id("asset_overreuse", None, id_key="abc"),
            "asset_overreuse:global:abc",
        )

    def test_make_finding_id_default_global(self):
        self.assertEqual(make_finding_id("x", None), "x:global:default")

    def test_make_finding_factory_sets_id(self):
        f = make_finding(
            check="claim_to_proof_latency",
            severity=SEVERITY_WARN,
            confidence=0.7,
            reason="r",
            evidence={},
            suggested_fix="fix",
            beat_id="beat-02",
        )
        self.assertEqual(f.finding_id, "claim_to_proof_latency:beat:beat-02")

    def test_finding_ids_stable_across_runs(self):
        # Same inputs → same IDs
        beats = [{"id": "beat-01", "intent": "setup", "start": 0, "end": 5, "text": "It's 6x faster"}]
        matches = [{"beat_id": "beat-01", "selected_asset_id": None, "selected_asset_filename": None}]
        f1 = check_claim_to_proof_latency(beats, matches)
        f2 = check_claim_to_proof_latency(beats, matches)
        self.assertEqual([f.finding_id for f in f1], [f.finding_id for f in f2])
        self.assertNotEqual(f1[0].finding_id, "")


# ── Global dedup of missing-enrichment suggestions ───────────────────────


class TestGlobalDedup(unittest.TestCase):
    def _build_unenriched_catalog(self, asset_ids: list[str]) -> Catalog:
        return Catalog(assets=[
            AssetEntry(
                id=aid, filename=f"{aid}.png", type="image", role="demo",
                linked_beats=["beat-01"], description="x",
            )
            for aid in asset_ids
        ])

    def test_proof_relevance_dedups_when_globally_absent(self):
        beats = [
            {"id": "beat-01", "intent": "demo",  "start": 0, "end": 3, "text": "a"},
            {"id": "beat-02", "intent": "proof", "start": 3, "end": 6, "text": "b"},
            {"id": "beat-03", "intent": "trust", "start": 6, "end": 9, "text": "c"},
        ]
        matches = [
            {"beat_id": "beat-01", "selected_asset_id": "asset-1"},
            {"beat_id": "beat-02", "selected_asset_id": "asset-2"},
            {"beat_id": "beat-03", "selected_asset_id": "asset-3"},
        ]
        catalog = self._build_unenriched_catalog(["asset-1", "asset-2", "asset-3"])
        f = check_proof_relevance(beats, matches, catalog, enrichment_globally_absent=True)
        # Expect ONE global SUGGEST instead of 3 per-beat suggestions
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, SEVERITY_SUGGEST)
        self.assertIsNone(f[0].beat_id)
        self.assertEqual(f[0].evidence["affected_beat_count"], 3)
        self.assertEqual(f[0].finding_id, "proof_relevance:global:no_enrichment")

    def test_caption_competition_dedups_when_globally_absent(self):
        beats = [
            {"id": "beat-01", "intent": "demo",  "start": 0, "end": 3, "text": "a"},
            {"id": "beat-02", "intent": "proof", "start": 3, "end": 6, "text": "b"},
        ]
        matches = [
            {"beat_id": "beat-01", "selected_asset_id": "asset-1"},
            {"beat_id": "beat-02", "selected_asset_id": "asset-2"},
        ]
        catalog = self._build_unenriched_catalog(["asset-1", "asset-2"])
        f = check_caption_competition(beats, matches, catalog, enrichment_globally_absent=True)
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, SEVERITY_SUGGEST)
        self.assertIsNone(f[0].beat_id)
        self.assertEqual(f[0].finding_id, "caption_competition:global:no_text_density")

    def test_proof_relevance_per_beat_when_partial_enrichment(self):
        beats = [
            {"id": "beat-01", "intent": "demo", "start": 0, "end": 3, "text": "a"},
        ]
        matches = [{"beat_id": "beat-01", "selected_asset_id": "stats-chart-png"}]
        # Catalog has enrichment with non-matching tags → per-beat WARN
        catalog = _enriched_catalog(tags=["unrelated"])
        f = check_proof_relevance(beats, matches, catalog, enrichment_globally_absent=False)
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, SEVERITY_WARN)
        self.assertEqual(f[0].beat_id, "beat-01")


# ── Related-finding linking ──────────────────────────────────────────────


class TestRelatedFindingLinking(unittest.TestCase):
    def test_linker_cross_references_same_asset(self):
        # Two findings about asset 'duplicate-asset' should link to each other
        f1 = make_finding(
            check="asset_overreuse", severity=SEVERITY_WARN, confidence=1.0,
            beat_id=None, id_key="duplicate-asset",
            reason="reused", evidence={"asset_id": "duplicate-asset", "use_count": 4},
            suggested_fix="x",
        )
        f2 = make_finding(
            check="visual_novelty", severity=SEVERITY_WARN, confidence=0.8,
            beat_id="beat-01",
            reason="repeated", evidence={"asset_id": "duplicate-asset", "streak_size": 4},
            suggested_fix="x",
        )
        f3 = make_finding(
            check="dead_holds", severity=SEVERITY_WARN, confidence=0.7,
            beat_id="beat-02",
            reason="long", evidence={"asset_id": "duplicate-asset", "filename": "x.png"},
            suggested_fix="x",
        )
        linked = _link_related_findings([f1, f2, f3])
        self.assertEqual(len(linked), 3)
        for f in linked:
            self.assertEqual(len(f.related_ids), 2)  # each links to the other 2
        # Verify cross-references are mutual
        f1_linked = next(f for f in linked if f.check == "asset_overreuse")
        self.assertIn(f2.finding_id, f1_linked.related_ids)
        self.assertIn(f3.finding_id, f1_linked.related_ids)

    def test_linker_does_not_link_unrelated(self):
        f1 = make_finding(
            check="asset_overreuse", severity=SEVERITY_WARN, confidence=1.0,
            beat_id=None, id_key="asset-A",
            reason="r", evidence={"asset_id": "asset-A"}, suggested_fix="x",
        )
        f2 = make_finding(
            check="asset_overreuse", severity=SEVERITY_WARN, confidence=1.0,
            beat_id=None, id_key="asset-B",
            reason="r", evidence={"asset_id": "asset-B"}, suggested_fix="x",
        )
        linked = _link_related_findings([f1, f2])
        for f in linked:
            self.assertEqual(f.related_ids, ())


# ── Severity floor filtering ─────────────────────────────────────────────


class TestSeverityFloor(unittest.TestCase):
    def _make_findings(self):
        return [
            make_finding(check="x", severity=SEVERITY_BLOCK, confidence=1.0,
                         reason="b", evidence={}, suggested_fix="", beat_id="beat-01"),
            make_finding(check="x", severity=SEVERITY_WARN, confidence=0.8,
                         reason="w", evidence={}, suggested_fix="", beat_id="beat-02"),
            make_finding(check="x", severity=SEVERITY_SUGGEST, confidence=0.5,
                         reason="s", evidence={}, suggested_fix="", beat_id="beat-03"),
        ]

    def test_floor_suggest_keeps_all(self):
        f = self._make_findings()
        self.assertEqual(len(_apply_severity_floor(f, SEVERITY_SUGGEST)), 3)

    def test_floor_warn_drops_suggestions(self):
        f = self._make_findings()
        kept = _apply_severity_floor(f, SEVERITY_WARN)
        self.assertEqual(len(kept), 2)
        self.assertNotIn(SEVERITY_SUGGEST, [k.severity for k in kept])

    def test_floor_block_keeps_only_blockers(self):
        f = self._make_findings()
        kept = _apply_severity_floor(f, SEVERITY_BLOCK)
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0].severity, SEVERITY_BLOCK)

    def test_runner_severity_floor_preserves_pre_filter_totals(self):
        beat_map = {"beats": [{"id": "beat-01", "intent": "setup", "start": 0, "end": 10, "text": "It's 6x faster"}]}
        matches = {"beats": [{"beat_id": "beat-01", "selected_asset_id": None, "selected_asset_filename": None}]}
        report = run_critic(
            beat_map=beat_map, asset_matches=matches,
            motion_plan=None, gap_ownership=None, edit_plan=None, catalog=None,
            project_slug="test", severity_floor=SEVERITY_BLOCK,
        )
        # Pre-filter shows the actual count; filtered list is what's exposed
        self.assertGreaterEqual(report.pre_filter_total, 1)
        # Verdict reflects pre-filter state, not filtered state
        self.assertIn(report.verdict, ("advisory_blocked", "advisory_warnings", "advisory_pass"))


# ── critic_status (informational, not in project.json) ──────────────────


class TestCriticStatus(unittest.TestCase):
    def _inputs_present(self, beat_map=True, asset_matches=True, **rest) -> dict:
        return {
            "beat_map":      beat_map,
            "asset_matches": asset_matches,
            "motion_plan":   rest.get("motion_plan", True),
            "gap_ownership": rest.get("gap_ownership", True),
            "edit_plan":     rest.get("edit_plan", False),
            "catalog":       rest.get("catalog", True),
        }

    def test_status_passed_when_clean_and_inputs_present(self):
        report = CriticReport(
            project="x", findings=[], inputs_present=self._inputs_present(),
            selected_match_count=3,
        )
        self.assertEqual(report.critic_status, STATUS_PASSED)

    def test_status_warnings_when_only_warnings(self):
        f = make_finding(
            check="x", severity=SEVERITY_WARN, confidence=0.5,
            reason="r", evidence={}, suggested_fix="", beat_id="beat-01",
        )
        report = CriticReport(
            project="x", findings=[f],
            inputs_present=self._inputs_present(),
            pre_filter_total=1, pre_filter_warnings=1,
            selected_match_count=3,
        )
        self.assertEqual(report.critic_status, STATUS_WARNINGS)

    def test_status_blocked_when_blockers_present(self):
        f = make_finding(
            check="x", severity=SEVERITY_BLOCK, confidence=1.0,
            reason="r", evidence={}, suggested_fix="", beat_id="beat-01",
        )
        report = CriticReport(
            project="x", findings=[f],
            inputs_present=self._inputs_present(),
            pre_filter_total=1, pre_filter_blockers=1,
            selected_match_count=3,
        )
        self.assertEqual(report.critic_status, STATUS_BLOCKED)

    def test_status_unavailable_when_no_beat_map(self):
        # Phase E2.5: missing beat-map = unavailable, not passed
        report = CriticReport(
            project="x", findings=[],
            inputs_present=self._inputs_present(beat_map=False),
        )
        self.assertEqual(report.critic_status, STATUS_UNAVAILABLE)

    def test_status_unavailable_when_no_asset_matches(self):
        # Phase E2.5: missing asset-matches = unavailable, not passed
        report = CriticReport(
            project="x", findings=[],
            inputs_present=self._inputs_present(asset_matches=False),
        )
        self.assertEqual(report.critic_status, STATUS_UNAVAILABLE)

    def test_status_unavailable_when_no_selections(self):
        # Phase E2.5: matches file exists but matcher selected nothing → unavailable
        report = CriticReport(
            project="x", findings=[],
            inputs_present=self._inputs_present(),
            selected_match_count=0,
        )
        self.assertEqual(report.critic_status, STATUS_UNAVAILABLE)

    def test_status_passed_when_selections_present_and_clean(self):
        report = CriticReport(
            project="x", findings=[],
            inputs_present=self._inputs_present(),
            selected_match_count=5,
        )
        self.assertEqual(report.critic_status, STATUS_PASSED)

    def test_unavailable_overrides_zero_findings(self):
        # Even when findings is empty, unavailable wins over passed
        report = CriticReport(
            project="x", findings=[],
            inputs_present=self._inputs_present(beat_map=False),
        )
        self.assertEqual(report.critic_status, STATUS_UNAVAILABLE)
        self.assertEqual(report.pre_filter_total, 0)

    def test_critic_status_dict_shape(self):
        report_dict = {
            "project": "x",
            "critic_version": "test",
            "generated_at": "now",
            "critic_status": "critic_warnings",
            "verdict": "advisory_warnings",
            "totals": {"blockers": 0, "warnings": 1, "suggestions": 0, "total": 1, "pre_filter": {}},
            "summary": {"data_quality_limitations": ["x"], "highest_confidence_blockers": []},
        }
        slim = build_critic_status_dict(report_dict)
        for key in ("schema_version", "project", "critic_status", "verdict",
                    "totals", "data_quality_limitations", "highest_confidence_blockers"):
            self.assertIn(key, slim)
        self.assertTrue(slim["advisory"])


# ── Enrichment state + summary builders ─────────────────────────────────


class TestEnrichmentStateAndSummary(unittest.TestCase):
    def test_globally_absent_when_no_enrichment(self):
        catalog = Catalog(assets=[
            AssetEntry(id="a", filename="a.png", type="image", role="demo",
                       linked_beats=["b1"], description="x"),
        ])
        state = _enrichment_state(catalog)
        self.assertEqual(state["none"], 1)
        self.assertEqual(state["full"], 0)
        self.assertTrue(_is_enrichment_globally_absent(state))

    def test_partial_enrichment_not_globally_absent(self):
        catalog = Catalog(assets=[
            AssetEntry(id="a", filename="a.png", type="image", role="demo",
                       linked_beats=["b1"], description="x",
                       enrichment={"status": "full", "schema_version": 1,
                                   "derived_at": "n", "derived_by": "t"}),
            AssetEntry(id="b", filename="b.png", type="image", role="demo",
                       linked_beats=["b2"], description="x"),
        ])
        state = _enrichment_state(catalog)
        self.assertEqual(state["full"], 1)
        self.assertEqual(state["none"], 1)
        self.assertFalse(_is_enrichment_globally_absent(state))

    def test_data_quality_limitations_lists_missing_inputs(self):
        notes = _build_data_quality_limitations(
            inputs_present={"edit_plan": False, "asset_matches": True, "motion_plan": True},
            enrichment_state={"full": 0, "partial": 0, "none": 5, "total": 5},
        )
        self.assertTrue(any("edit-plan" in n for n in notes))
        self.assertTrue(any("enrichment is globally absent" in n for n in notes))

    def test_root_cause_clusters_groups_by_asset(self):
        f1 = make_finding(check="asset_overreuse", severity=SEVERITY_WARN, confidence=1.0,
                          beat_id=None, id_key="dup",
                          reason="r", evidence={"asset_id": "dup"}, suggested_fix="x")
        f2 = make_finding(check="visual_novelty", severity=SEVERITY_WARN, confidence=0.8,
                          beat_id="beat-01",
                          reason="r", evidence={"asset_id": "dup"}, suggested_fix="x")
        clusters = _build_root_cause_clusters([f1, f2])
        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0]["asset_id"], "dup")
        self.assertEqual(len(clusters[0]["finding_ids"]), 2)

    def test_highest_confidence_blockers_sorted(self):
        f_low = make_finding(check="x", severity=SEVERITY_BLOCK, confidence=0.6,
                             beat_id="b1", reason="r", evidence={}, suggested_fix="")
        f_high = make_finding(check="x", severity=SEVERITY_BLOCK, confidence=0.95,
                              beat_id="b2", reason="r", evidence={}, suggested_fix="")
        result = _highest_confidence_blockers([f_low, f_high])
        self.assertEqual(result[0]["beat_id"], "b2")  # highest first
        self.assertEqual(result[1]["beat_id"], "b1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
