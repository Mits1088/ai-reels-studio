"""Tests for lib/orchestrate/.

Coverage of the user-requested fixture categories:
  - enriched catalog path
  - legacy non-enriched catalog path
  - missing asset metadata
  - low-confidence fallback behavior
  - deterministic tie-breaking
  - motion budget enforcement
  - gap ownership edge cases
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lib.capture.catalog import AssetEntry, Catalog
from lib.orchestrate.match_assets import (
    match_assets,
    match_assets_for_project,
    score_asset_for_beat,
    SCORE_WEIGHTS,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_LOW,
)
from lib.orchestrate.motion_plan import (
    plan_motion,
    plan_beat_motion,
    classify_beat_category,
    BEAT_CATEGORY_DEFAULTS,
)
from lib.orchestrate.gap_owner import (
    assign_gaps,
    OWNERSHIP_MICRO,
    OWNERSHIP_SEAM,
    OWNERSHIP_BREATHING,
)


# ── Fixtures ──────────────────────────────────────────────────────────────


def _enriched_video_asset(
    asset_id="demo-video",
    filename="demo-walkthrough.mp4",
    role="demo",
    duration_s=12.0,
    aspect_ratio_decimal=1.778,
    text_density=0.6,
    quality_flags=None,
    focal_source="manual",
) -> AssetEntry:
    return AssetEntry(
        id=asset_id,
        filename=filename,
        type="video",
        role=role,
        linked_beats=["beat-01"],
        description="enriched video fixture",
        duration_s=duration_s,
        dimensions={"w": 1920, "h": 1080},
        source="capture",
        enrichment={
            "status": "full",
            "schema_version": 1,
            "derived_at": "2026-04-10T12:00:00Z",
            "derived_by": "test",
            "aspect_ratio": "16:9",
            "aspect_ratio_decimal": aspect_ratio_decimal,
            "text": {"method": "test", "skipped_reason": None, "score": text_density},
            "focal_point": {"x": 50, "y": 50, "source": focal_source, "confidence": 0.8},
            "quality_flags": quality_flags or [],
            "editorial_tags": ["product-demo", "interaction"],
            "usable_display_modes": ["center-full", "responsive"],
        },
    )


def _legacy_image_asset(asset_id="img", filename="photo.png", role="support") -> AssetEntry:
    return AssetEntry(
        id=asset_id,
        filename=filename,
        type="image",
        role=role,
        linked_beats=["beat-01"],
        description="legacy non-enriched fixture",
        duration_s=None,
        dimensions=None,
        source="import",
        # No enrichment block at all
    )


def _malformed_asset() -> AssetEntry:
    return AssetEntry(
        id="malformed", filename="x.png", type="", role="",
        linked_beats=[], description="",
    )


def _beat(beat_id="beat-01", intent="demo", start=0.0, end=5.0, text="hello"):
    return {"id": beat_id, "intent": intent, "start": start, "end": end, "text": text}


# ── Score factor unit tests ───────────────────────────────────────────────


class TestScoreFactors(unittest.TestCase):
    def test_score_weights_sum_to_one(self):
        # Drift detector: positive weights must sum to 1.0
        total = sum(SCORE_WEIGHTS.values())
        self.assertAlmostEqual(total, 1.0, places=4)

    def test_enriched_demo_video_high_score(self):
        asset = _enriched_video_asset()
        beat = _beat(intent="demo", start=0, end=5)
        bd = score_asset_for_beat(asset, beat, position=0, total_beats=1)
        self.assertGreater(bd.final_score, 0.7)
        self.assertEqual(bd.role_fit, 1.0)
        self.assertEqual(bd.duration_fit, 1.0)

    def test_legacy_asset_neutral_score(self):
        asset = _legacy_image_asset()
        beat = _beat(intent="demo", start=0, end=5)
        bd = score_asset_for_beat(asset, beat, position=0, total_beats=1)
        # Without enrichment, factors that depend on it return 0.5
        self.assertEqual(bd.proof_fit, 0.5)
        self.assertEqual(bd.aspect_fit, 0.5)
        self.assertEqual(bd.legibility, 0.5)
        self.assertEqual(bd.focal_point, 0.5)
        self.assertEqual(bd.enrichment_bonus, 0.0)

    def test_quality_flags_apply_penalty(self):
        clean = _enriched_video_asset()
        flagged = _enriched_video_asset(quality_flags=["low_resolution", "no_audio_track"])
        beat = _beat(intent="demo")
        clean_bd = score_asset_for_beat(clean, beat, 0, 1)
        flagged_bd = score_asset_for_beat(flagged, beat, 0, 1)
        self.assertGreater(flagged_bd.quality_penalty, 0)
        self.assertGreater(clean_bd.final_score, flagged_bd.final_score)

    def test_file_missing_eliminates(self):
        missing = _enriched_video_asset(quality_flags=["file_missing"])
        beat = _beat(intent="demo")
        bd = score_asset_for_beat(missing, beat, 0, 1)
        self.assertEqual(bd.final_score, 0.0)

    def test_short_video_duration_penalty(self):
        short = _enriched_video_asset(duration_s=2.0)
        beat = _beat(intent="demo", start=0, end=10)  # 10s beat, 2s asset
        bd = score_asset_for_beat(short, beat, 0, 1)
        self.assertLess(bd.duration_fit, 0.5)

    def test_image_duration_always_full(self):
        img = _legacy_image_asset()
        beat = _beat(intent="proof", start=0, end=10)
        bd = score_asset_for_beat(img, beat, 0, 1)
        self.assertEqual(bd.duration_fit, 1.0)

    def test_text_density_rewards_demo(self):
        high_text = _enriched_video_asset(text_density=0.9)
        low_text = _enriched_video_asset(text_density=0.1)
        beat = _beat(intent="demo")
        high_bd = score_asset_for_beat(high_text, beat, 0, 1)
        low_bd = score_asset_for_beat(low_text, beat, 0, 1)
        self.assertGreater(high_bd.legibility, low_bd.legibility)

    def test_text_density_punishes_hook(self):
        high_text = _enriched_video_asset(text_density=0.9)
        low_text = _enriched_video_asset(text_density=0.1)
        beat = _beat(intent="hook")
        high_bd = score_asset_for_beat(high_text, beat, 0, 1)
        low_bd = score_asset_for_beat(low_text, beat, 0, 1)
        self.assertLess(high_bd.legibility, low_bd.legibility)


# ── End-to-end matching ──────────────────────────────────────────────────


class TestMatchAssets(unittest.TestCase):
    def test_enriched_path(self):
        catalog = Catalog(assets=[_enriched_video_asset()])
        beats = [_beat()]
        matches = match_assets(beats, catalog)
        self.assertEqual(len(matches), 1)
        m = matches[0]
        self.assertEqual(m.selected_asset_id, "demo-video")
        self.assertGreater(m.selection_confidence, 0.7)
        self.assertFalse(m.human_review_required)
        self.assertEqual(m.enrichment_status, "full")

    def test_legacy_non_enriched_path(self):
        catalog = Catalog(assets=[_legacy_image_asset()])
        beats = [_beat(intent="proof")]
        matches = match_assets(beats, catalog)
        self.assertEqual(len(matches), 1)
        m = matches[0]
        # Should still pick the asset, but with lower confidence and review flag
        self.assertEqual(m.selected_asset_id, "img")
        self.assertLess(m.selection_confidence, CONFIDENCE_HIGH)
        self.assertTrue(m.human_review_required)
        self.assertEqual(m.enrichment_status, "none")

    def test_missing_metadata_does_not_crash(self):
        catalog = Catalog(assets=[_malformed_asset()])
        beats = [_beat()]
        matches = match_assets(beats, catalog)
        self.assertEqual(len(matches), 1)
        # The malformed asset has no role, so it's a low score, but should not crash
        m = matches[0]
        self.assertIsNotNone(m)

    def test_low_confidence_fallback_marks_review(self):
        # Build a catalog where every asset is low quality
        bad = _enriched_video_asset(
            asset_id="bad-asset",
            quality_flags=["low_resolution", "non_standard_fps", "wrong_orientation"],
            text_density=0.9,  # bad fit for hook
        )
        catalog = Catalog(assets=[bad])
        beats = [_beat(intent="hook")]
        matches = match_assets(beats, catalog)
        m = matches[0]
        self.assertTrue(m.human_review_required)
        self.assertIn(m.review_reason, ("low_confidence", "medium_confidence", "narrow_margin"))

    def test_no_acceptable_candidate_returns_none(self):
        # Asset with file_missing → score 0.0 → below CONFIDENCE_LOW
        broken = _enriched_video_asset(quality_flags=["file_missing"])
        catalog = Catalog(assets=[broken])
        beats = [_beat()]
        matches = match_assets(beats, catalog)
        m = matches[0]
        self.assertIsNone(m.selected_asset_id)
        self.assertTrue(m.human_review_required)
        self.assertEqual(m.review_reason, "no_acceptable_candidate")

    def test_deterministic_tie_break(self):
        # Two identical assets except for asset_id — alphabetical first should win
        a = _enriched_video_asset(asset_id="zzz-second", filename="z.mp4")
        b = _enriched_video_asset(asset_id="aaa-first", filename="a.mp4")
        catalog = Catalog(assets=[a, b])  # Insert in reverse-alpha order
        beats = [_beat()]
        matches = match_assets(beats, catalog)
        self.assertEqual(matches[0].selected_asset_id, "aaa-first")
        # Re-run to confirm stability
        matches2 = match_assets(beats, catalog)
        self.assertEqual(matches[0].selected_asset_id, matches2[0].selected_asset_id)

    def test_filters_out_avatar_and_sfx(self):
        avatar = _enriched_video_asset(asset_id="av", role="avatar")
        sfx = AssetEntry(
            id="bg-music", filename="bgm.mp3", type="music", role="music",
            linked_beats=["beat-01"], description="bg music",
        )
        catalog = Catalog(assets=[avatar, sfx])
        beats = [_beat()]
        matches = match_assets(beats, catalog)
        # Both filtered → no candidates
        m = matches[0]
        self.assertIsNone(m.selected_asset_id)

    def test_fallback_chain_populated(self):
        a1 = _enriched_video_asset(asset_id="a1", filename="a1.mp4", text_density=0.6)
        a2 = _enriched_video_asset(asset_id="a2", filename="a2.mp4", text_density=0.5)
        a3 = _enriched_video_asset(asset_id="a3", filename="a3.mp4", text_density=0.4)
        catalog = Catalog(assets=[a1, a2, a3])
        beats = [_beat(intent="demo")]
        matches = match_assets(beats, catalog)
        m = matches[0]
        # Top candidate selected, others should be in fallback
        self.assertIsNotNone(m.selected_asset_id)
        self.assertEqual(len(m.fallback_asset_ids), 2)


# ── Motion plan ────────────────────────────────────────────────────────────


class TestMotionPlan(unittest.TestCase):
    def test_classify_explicit_intent(self):
        cat, conf = classify_beat_category({"intent": "hook"}, 0, 5)
        self.assertEqual(cat, "hook")
        self.assertEqual(conf, 1.0)

    def test_classify_legacy_context_maps_to_concept(self):
        cat, conf = classify_beat_category({"intent": "context"}, 2, 5)
        self.assertEqual(cat, "concept")

    def test_classify_position_fallback_first(self):
        cat, conf = classify_beat_category({}, 0, 5)
        self.assertEqual(cat, "hook")
        self.assertEqual(conf, 0.6)

    def test_classify_position_fallback_last(self):
        cat, conf = classify_beat_category({}, 4, 5)
        self.assertEqual(cat, "cta")

    def test_classify_default(self):
        cat, conf = classify_beat_category({}, 2, 5)
        self.assertEqual(cat, "concept")
        self.assertEqual(conf, 0.4)

    def test_plan_beat_motion_high_confidence(self):
        beat = {"id": "beat-01", "intent": "demo", "start": 0, "end": 5}
        plan = plan_beat_motion(beat, 0, 5)
        self.assertEqual(plan.beat_category, "demo")
        self.assertEqual(plan.confidence, 1.0)
        self.assertEqual(plan.violations, [])
        self.assertIn("hero", plan.motion_budget)

    def test_plan_motion_uses_grammar_presets(self):
        beat = {"id": "beat-01", "intent": "hook", "start": 0, "end": 2}
        plan = plan_beat_motion(beat, 0, 5)
        # Hero preset should be one of the editorial enter presets
        from lib.grammar import EDITORIAL_ENTER_PRESETS
        hero_preset = plan.motion_budget["hero"].get("preset")
        self.assertIn(hero_preset, EDITORIAL_ENTER_PRESETS)

    def test_plan_motion_cta_has_smooth_push(self):
        beat = {"id": "beat-end", "intent": "CTA", "start": 30, "end": 33}
        plan = plan_beat_motion(beat, 5, 6)
        self.assertEqual(plan.beat_category, "cta")
        # cta uses smooth-push from preferred_presets_for
        self.assertEqual(plan.motion_budget["hero"]["preset"], "smooth-push")

    def test_plan_motion_for_all_beats(self):
        beats = [
            {"id": "beat-01", "intent": "hook", "start": 0, "end": 2},
            {"id": "beat-02", "intent": "demo", "start": 2, "end": 8},
            {"id": "beat-03", "intent": "CTA", "start": 8, "end": 10},
        ]
        plans = plan_motion(beats)
        self.assertEqual(len(plans), 3)
        self.assertEqual(plans[0].beat_category, "hook")
        self.assertEqual(plans[1].beat_category, "demo")
        self.assertEqual(plans[2].beat_category, "cta")

    def test_motion_budget_validation_enforced(self):
        # All defaults should produce valid budgets — no violations expected
        for category in BEAT_CATEGORY_DEFAULTS.keys():
            beat = {"id": "beat-x", "intent": category, "start": 0, "end": 5}
            plan = plan_beat_motion(beat, 0, 1)
            self.assertEqual(
                plan.violations, [],
                f"Category {category!r} default budget has violations: {plan.violations}",
            )


# ── Gap owner ──────────────────────────────────────────────────────────────


class TestGapOwner(unittest.TestCase):
    def test_no_gaps_when_one_beat(self):
        gaps = assign_gaps([{"id": "beat-01", "start": 0, "end": 5}])
        self.assertEqual(gaps, [])

    def test_no_gaps_empty_list(self):
        self.assertEqual(assign_gaps([]), [])

    def test_micro_gap(self):
        beats = [
            {"id": "beat-01", "start": 0, "end": 5},
            {"id": "beat-02", "start": 5.1, "end": 10},  # 0.1s gap
        ]
        gaps = assign_gaps(beats)
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0].ownership_type, OWNERSHIP_MICRO)
        self.assertEqual(gaps[0].owner_beat_id, "beat-01")
        self.assertAlmostEqual(gaps[0].gap_duration, 0.1, places=3)

    def test_seam_gap(self):
        beats = [
            {"id": "beat-01", "start": 0, "end": 5},
            {"id": "beat-02", "start": 5.5, "end": 10},  # 0.5s gap
        ]
        gaps = assign_gaps(beats)
        self.assertEqual(gaps[0].ownership_type, OWNERSHIP_SEAM)
        self.assertEqual(gaps[0].owner_beat_id, "beat-01")

    def test_breathing_gap(self):
        beats = [
            {"id": "beat-01", "start": 0, "end": 5},
            {"id": "beat-02", "start": 6.5, "end": 10},  # 1.5s gap
        ]
        gaps = assign_gaps(beats)
        self.assertEqual(gaps[0].ownership_type, OWNERSHIP_BREATHING)

    def test_overlap_detected(self):
        beats = [
            {"id": "beat-01", "start": 0, "end": 5.5},
            {"id": "beat-02", "start": 5.0, "end": 10},  # 0.5s overlap
        ]
        gaps = assign_gaps(beats)
        self.assertEqual(gaps[0].ownership_type, "overlap")

    def test_threshold_boundary_micro_to_seam(self):
        # Use exactly representable floats to avoid IEEE-754 noise. 0.5 - 0.0 = 0.5
        # exactly. The epsilon in gap_owner also handles 5.3 - 5.0 = 0.29999...
        # but constructing the test values cleanly is more readable.
        beats = [
            {"id": "beat-01", "start": 0.0, "end": 0.0},
            {"id": "beat-02", "start": 0.3, "end": 1.0},  # 0.3 gap (with epsilon → seam)
        ]
        gaps = assign_gaps(beats)
        self.assertEqual(gaps[0].ownership_type, OWNERSHIP_SEAM)

    def test_threshold_boundary_below_micro(self):
        beats = [
            {"id": "beat-01", "start": 0.0, "end": 0.0},
            {"id": "beat-02", "start": 0.25, "end": 1.0},  # 0.25 < 0.3 → micro
        ]
        gaps = assign_gaps(beats)
        self.assertEqual(gaps[0].ownership_type, OWNERSHIP_MICRO)

    def test_threshold_boundary_seam_to_breathing(self):
        beats = [
            {"id": "beat-01", "start": 0.0, "end": 0.0},
            {"id": "beat-02", "start": 0.8, "end": 2.0},  # 0.8 gap (with epsilon → breathing)
        ]
        gaps = assign_gaps(beats)
        self.assertEqual(gaps[0].ownership_type, OWNERSHIP_BREATHING)

    def test_multiple_gaps_in_sequence(self):
        beats = [
            {"id": "beat-01", "start": 0, "end": 2},
            {"id": "beat-02", "start": 2.05, "end": 5},   # micro
            {"id": "beat-03", "start": 5.5, "end": 8},    # seam
            {"id": "beat-04", "start": 9.5, "end": 12},   # breathing
        ]
        gaps = assign_gaps(beats)
        self.assertEqual(len(gaps), 3)
        self.assertEqual(gaps[0].ownership_type, OWNERSHIP_MICRO)
        self.assertEqual(gaps[1].ownership_type, OWNERSHIP_SEAM)
        self.assertEqual(gaps[2].ownership_type, OWNERSHIP_BREATHING)


# ── Project-level entry tests ────────────────────────────────────────────


class TestProjectEntries(unittest.TestCase):
    def test_match_for_project_skips_when_no_beat_map(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            proj = Path(td) / "empty"
            proj.mkdir()
            result = match_assets_for_project(proj)
            self.assertTrue(result["skipped"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
