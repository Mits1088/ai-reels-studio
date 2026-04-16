"""Tests for lib/capture/enrich.py.

Covers the five test categories the user requested for Phase B:
  - image asset
  - video asset (mocked — we don't ship a real fixture mp4)
  - missing optional deps (cv2, tesseract, pillow, ffprobe)
  - already-enriched asset (idempotency)
  - malformed asset metadata

Image fixtures are generated at test time with Pillow into a tmp dir,
so no binary files live in the repo.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Path setup so the tests run via either `python -m pytest` or direct invocation
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lib.capture import enrich
from lib.capture.enrich import (
    enrich_asset,
    enrich_project,
    is_enriched,
    _normalize_aspect,
    _derive_quality_flags,
    _derive_usable_display_modes,
    _classify_skip,
    _determine_status,
    ENRICHMENT_SCHEMA_VERSION,
    ENRICHER_VERSION,
)


def _make_test_image(path: Path, size=(100, 100), color=(255, 0, 0)) -> Path:
    """Generate a tiny test PNG. Requires Pillow."""
    from PIL import Image
    img = Image.new("RGB", size, color)
    img.save(path, format="PNG")
    return path


# ── Pure helpers (no I/O) ─────────────────────────────────────────────────


class TestEnrichmentHelpers(unittest.TestCase):
    """Pure-function helpers — no fs/IO required, no optional deps."""

    def test_normalize_aspect_16_9(self):
        label, decimal = _normalize_aspect(1920, 1080)
        self.assertEqual(label, "16:9")
        self.assertAlmostEqual(decimal, 1.7778, places=3)

    def test_normalize_aspect_9_16(self):
        label, _ = _normalize_aspect(1080, 1920)
        self.assertEqual(label, "9:16")

    def test_normalize_aspect_square(self):
        label, _ = _normalize_aspect(500, 500)
        self.assertEqual(label, "1:1")

    def test_normalize_aspect_4_3(self):
        label, _ = _normalize_aspect(800, 600)
        self.assertEqual(label, "4:3")

    def test_normalize_aspect_unusual(self):
        label, decimal = _normalize_aspect(123, 100)
        self.assertEqual(label, "123:100")
        self.assertAlmostEqual(decimal, 1.23)

    def test_normalize_aspect_missing(self):
        self.assertEqual(_normalize_aspect(0, 1080), (None, None))
        self.assertEqual(_normalize_aspect(None, 1080), (None, None))
        self.assertEqual(_normalize_aspect(1920, None), (None, None))

    def test_quality_flags_low_res(self):
        flags = _derive_quality_flags(
            {"type": "image"},
            {"width": 320, "height": 200, "has_audio": True},
        )
        self.assertIn("low_resolution", flags)

    def test_quality_flags_no_audio(self):
        flags = _derive_quality_flags(
            {"type": "video"},
            {"width": 1920, "height": 1080, "has_audio": False, "fps": 30, "pix_fmt": "yuv420p"},
        )
        self.assertIn("no_audio_track", flags)
        self.assertNotIn("non_standard_fps", flags)

    def test_quality_flags_non_standard_fps(self):
        flags = _derive_quality_flags(
            {"type": "video"},
            {"width": 1920, "height": 1080, "has_audio": True, "fps": 25, "pix_fmt": "yuv420p"},
        )
        self.assertIn("non_standard_fps", flags)

    def test_quality_flags_non_standard_pix_fmt(self):
        flags = _derive_quality_flags(
            {"type": "video"},
            {"width": 1920, "height": 1080, "has_audio": True, "fps": 30, "pix_fmt": "yuv422p"},
        )
        self.assertIn("non_standard_pix_fmt", flags)

    def test_usable_display_modes_portrait(self):
        modes = _derive_usable_display_modes({"width": 1080, "height": 1080}, "image")
        self.assertIn("split-screen", modes)

    def test_usable_display_modes_landscape(self):
        modes = _derive_usable_display_modes({"width": 1920, "height": 1080}, "video")
        self.assertIn("center-full", modes)
        self.assertIn("responsive", modes)
        self.assertIn("hook-reveal", modes)

    def test_usable_display_modes_sfx(self):
        self.assertEqual(_derive_usable_display_modes({"width": 0, "height": 0}, "sfx"), [])


# ── Skip classification + status determination ───────────────────────────


class TestSkipClassification(unittest.TestCase):
    def test_classify_ran(self):
        self.assertEqual(_classify_skip(None), "ran")

    def test_classify_not_applicable(self):
        self.assertEqual(_classify_skip("not_a_video"), "not_applicable")
        self.assertEqual(_classify_skip("not_visual_asset"), "not_applicable")
        self.assertEqual(_classify_skip("unsupported_extension"), "not_applicable")

    def test_classify_dep_missing(self):
        self.assertEqual(_classify_skip("cv2_unavailable"), "dep_missing")
        self.assertEqual(_classify_skip("pillow_unavailable"), "dep_missing")
        self.assertEqual(_classify_skip("ffmpeg_unavailable"), "dep_missing")
        self.assertEqual(_classify_skip("ffprobe_unavailable"), "dep_missing")

    def test_classify_error(self):
        self.assertEqual(_classify_skip("ffprobe_error: TimeoutExpired"), "error")
        self.assertEqual(_classify_skip("cv2_error: ValueError"), "error")
        self.assertEqual(_classify_skip("imread_failed"), "error")
        self.assertEqual(_classify_skip("frame_extraction_failed"), "error")

    def test_status_full_when_all_ran(self):
        ms = [
            {"skipped_reason": None},
            {"skipped_reason": None},
            {"skipped_reason": "not_a_video"},
        ]
        self.assertEqual(_determine_status(ms), "full")

    def test_status_partial_when_dep_missing(self):
        ms = [
            {"skipped_reason": None},
            {"skipped_reason": "cv2_unavailable"},
        ]
        self.assertEqual(_determine_status(ms), "partial")

    def test_status_failed_when_no_runs(self):
        ms = [
            {"skipped_reason": "imread_failed"},
            {"skipped_reason": "ffprobe_error: x"},
        ]
        self.assertEqual(_determine_status(ms), "failed")

    def test_status_full_when_only_not_applicable(self):
        ms = [
            {"skipped_reason": "not_a_video"},
            {"skipped_reason": "not_visual_asset"},
        ]
        self.assertEqual(_determine_status(ms), "full")


# ── Image enrichment (real Pillow + cv2 if available) ───────────────────


@unittest.skipUnless(enrich.HAVE_PIL, "Pillow required for image enrichment tests")
class TestEnrichImage(unittest.TestCase):
    """Image asset enrichment using a Pillow-generated tmp fixture."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmppath = Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_enrich_image_full_path(self):
        img_path = self.tmppath / "test.png"
        _make_test_image(img_path, size=(800, 600))

        asset = {
            "id": "test", "filename": "test.png", "type": "image",
            "role": "support", "linked_beats": ["beat-01"], "description": "test",
        }
        result = enrich_asset(asset, img_path)

        self.assertIn("enrichment", result)
        e = result["enrichment"]
        self.assertEqual(e["schema_version"], ENRICHMENT_SCHEMA_VERSION)
        self.assertEqual(e["derived_by"], ENRICHER_VERSION)
        self.assertIn(e["status"], ("full", "partial"))
        self.assertEqual(e["aspect_ratio"], "4:3")
        self.assertEqual(e["technical"]["width"], 800)
        self.assertEqual(e["technical"]["height"], 600)
        self.assertIsInstance(e["quality_flags"], list)
        self.assertIsInstance(e["editorial_tags"], list)
        self.assertIsInstance(e["usable_display_modes"], list)

    def test_enrich_image_idempotent_default(self):
        img_path = self.tmppath / "test2.png"
        _make_test_image(img_path)
        asset = {
            "id": "test", "filename": "test2.png", "type": "image",
            "role": "support", "linked_beats": ["beat-01"], "description": "test",
        }
        first = enrich_asset(asset, img_path)
        second = enrich_asset(first, img_path)
        # Without force, second call returns the input unchanged (same dict identity)
        self.assertIs(first, second)

    def test_enrich_image_force_re_runs(self):
        img_path = self.tmppath / "test3.png"
        _make_test_image(img_path)
        asset = {
            "id": "test", "filename": "test3.png", "type": "image",
            "role": "support", "linked_beats": ["beat-01"], "description": "test",
        }
        first = enrich_asset(asset, img_path)
        second = enrich_asset(first, img_path, force=True)
        # Force returns a new dict and re-derives the technical block
        self.assertIsNot(first, second)
        self.assertEqual(second["enrichment"]["technical"]["width"], 100)

    def test_enrich_does_not_mutate_input(self):
        img_path = self.tmppath / "test4.png"
        _make_test_image(img_path)
        asset = {
            "id": "test", "filename": "test4.png", "type": "image",
            "role": "support", "linked_beats": ["beat-01"], "description": "test",
        }
        result = enrich_asset(asset, img_path)
        self.assertNotIn("enrichment", asset, "Input asset must not be mutated")
        self.assertIn("enrichment", result)

    def test_enrich_preserves_editorial_tags_on_force(self):
        img_path = self.tmppath / "test5.png"
        _make_test_image(img_path)
        asset = {
            "id": "test", "filename": "test5.png", "type": "image",
            "role": "support", "linked_beats": ["beat-01"], "description": "test",
            "enrichment": {
                "status": "full",
                "schema_version": 1,
                "derived_at": "2026-01-01T00:00:00Z",
                "derived_by": "old",
                "editorial_tags": ["product-demo", "manually-tagged"],
            },
        }
        result = enrich_asset(asset, img_path, force=True)
        self.assertEqual(
            sorted(result["enrichment"]["editorial_tags"]),
            ["manually-tagged", "product-demo"],
        )


# ── Video asset enrichment (mocked — no real video fixture) ─────────────


class TestEnrichVideoMocked(unittest.TestCase):
    """Verify video enrichment shape with mocked ffprobe + frame extraction.

    We don't ship a real .mp4 fixture in the repo. The motion/appearance/text/faces
    measurements all need a sample frame, which we mock to a Pillow-generated PNG.
    """

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmppath = Path(self.tmpdir.name)
        # Place a fake "video file" — just an empty file with .mp4 extension
        self.video_path = self.tmppath / "fake.mp4"
        self.video_path.write_bytes(b"")
        # And a real PNG that we'll return from the mocked frame sampler
        if enrich.HAVE_PIL:
            self.frame_path = self.tmppath / "frame.png"
            _make_test_image(self.frame_path, size=(1920, 1080))

    def tearDown(self):
        self.tmpdir.cleanup()

    @unittest.skipUnless(enrich.HAVE_PIL, "Pillow required")
    def test_video_technical_via_mocked_ffprobe(self):
        fake_ffprobe = {
            "streams": [
                {"codec_type": "video", "codec_name": "h264", "width": 1920,
                 "height": 1080, "r_frame_rate": "30/1", "pix_fmt": "yuv420p"},
                {"codec_type": "audio", "codec_name": "aac"},
            ],
            "format": {"duration": "8.5"},
        }
        with mock.patch.object(enrich, "_have_ffprobe", lambda: True), \
             mock.patch.object(enrich, "_ffprobe_streams", lambda p: fake_ffprobe):
            result = enrich._measure_technical(self.video_path, "video")
        self.assertIsNone(result["skipped_reason"])
        self.assertEqual(result["codec"], "h264")
        self.assertEqual(result["width"], 1920)
        self.assertEqual(result["height"], 1080)
        self.assertEqual(result["fps"], 30.0)
        self.assertTrue(result["has_audio"])
        self.assertAlmostEqual(result["duration_s"], 8.5)

    @unittest.skipUnless(enrich.HAVE_PIL, "Pillow required")
    def test_full_video_enrich_with_mocked_frames(self):
        fake_ffprobe = {
            "streams": [
                {"codec_type": "video", "codec_name": "h264", "width": 1920,
                 "height": 1080, "r_frame_rate": "30/1", "pix_fmt": "yuv420p"},
                {"codec_type": "audio", "codec_name": "aac"},
            ],
            "format": {"duration": "8.5"},
        }
        # Provide a real PNG path whenever the code asks to sample a frame
        with mock.patch.object(enrich, "_have_ffprobe", lambda: True), \
             mock.patch.object(enrich, "_have_ffmpeg", lambda: True), \
             mock.patch.object(enrich, "_ffprobe_streams", lambda p: fake_ffprobe), \
             mock.patch.object(enrich, "_sample_video_frame", lambda p: self.frame_path):
            asset = {
                "id": "v", "filename": "fake.mp4", "type": "video", "role": "broll",
                "linked_beats": ["beat-01"], "description": "test",
            }
            # Motion measurement runs ffmpeg directly; that path will fail on the empty file
            # but the test asserts the OVERALL shape, not motion success.
            result = enrich_asset(asset, self.video_path)

        e = result["enrichment"]
        self.assertEqual(e["aspect_ratio"], "16:9")
        self.assertEqual(e["technical"]["fps"], 30.0)
        self.assertIn(e["status"], ("full", "partial"))
        # Appearance + text + faces should at least have populated method strings
        self.assertEqual(e["appearance"]["method"], "pillow")


# ── Optional dependency degradation ─────────────────────────────────────


class TestEnrichOptionalDeps(unittest.TestCase):
    """Each optional dep must degrade gracefully — no crashes, clean skip reasons."""

    def test_missing_cv2_skips_face_detection(self):
        with mock.patch.object(enrich, "HAVE_CV2", False):
            result = enrich._measure_faces(Path("/nonexistent.png"))
        self.assertEqual(result["skipped_reason"], "cv2_unavailable")
        self.assertFalse(result["detected"])
        self.assertEqual(result["boxes"], [])

    @unittest.skipUnless(enrich.HAVE_PIL, "Pillow required")
    def test_missing_tesseract_falls_back_to_heuristic(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.png"
            _make_test_image(p)
            with mock.patch.object(enrich, "HAVE_TESSERACT", False):
                result = enrich._measure_text(p)
        self.assertEqual(result["method"], "edge-density-heuristic")
        self.assertIsNone(result["skipped_reason"])
        self.assertIn("score", result)

    def test_missing_pillow_skips_appearance(self):
        with mock.patch.object(enrich, "HAVE_PIL", False):
            result = enrich._measure_appearance(Path("/nonexistent.png"))
        self.assertEqual(result["skipped_reason"], "pillow_unavailable")

    def test_missing_pillow_skips_technical_for_image(self):
        with mock.patch.object(enrich, "HAVE_PIL", False):
            result = enrich._measure_technical(Path("/nonexistent.png"), "image")
        self.assertEqual(result["skipped_reason"], "pillow_unavailable")

    def test_missing_ffprobe_skips_motion(self):
        with mock.patch.object(enrich, "_have_ffprobe", lambda: False):
            result = enrich._measure_motion(Path("/x.mp4"))
        self.assertEqual(result["skipped_reason"], "ffmpeg_unavailable")

    def test_missing_ffprobe_skips_video_technical(self):
        with mock.patch.object(enrich, "_have_ffprobe", lambda: False):
            result = enrich._measure_technical(Path("/x.mp4"), "video")
        self.assertEqual(result["skipped_reason"], "ffprobe_unavailable")

    def test_image_face_detection_does_not_apply_to_audio(self):
        result = enrich._measure_faces(Path("/x.mp3"))
        self.assertEqual(result["skipped_reason"], "not_visual_asset")


# ── Malformed asset metadata ────────────────────────────────────────────


class TestEnrichMalformed(unittest.TestCase):
    """Malformed input must not crash — should produce a failed status."""

    def test_missing_file_marks_failed(self):
        asset = {
            "id": "x", "filename": "x.png", "type": "image", "role": "support",
            "linked_beats": ["beat-01"], "description": "x",
        }
        result = enrich_asset(asset, Path("/definitely/not/a/real/path.png"))
        self.assertEqual(result["enrichment"]["status"], "failed")
        self.assertIn("file_missing", result["enrichment"]["quality_flags"])
        self.assertIsNotNone(result["enrichment"]["failure_reason"])

    @unittest.skipUnless(enrich.HAVE_PIL, "Pillow required")
    def test_asset_without_type_still_enriches(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.png"
            _make_test_image(p)
            asset = {
                "id": "x", "filename": "x.png",
                "linked_beats": ["beat-01"], "description": "x",
            }
            result = enrich_asset(asset, p)
        self.assertIn("enrichment", result)
        # Should have at least technical info even without explicit type
        self.assertIn("technical", result["enrichment"])

    def test_empty_asset_dict_does_not_crash(self):
        result = enrich_asset({}, Path("/missing.png"))
        self.assertIn("enrichment", result)
        self.assertEqual(result["enrichment"]["status"], "failed")


# ── enrich_project flow ─────────────────────────────────────────────────


@unittest.skipUnless(enrich.HAVE_PIL, "Pillow required")
class TestEnrichProject(unittest.TestCase):
    """Full enrich_project flow on a tmp project."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.proj = Path(self.tmpdir.name)
        (self.proj / "assets").mkdir()
        (self.proj / "output").mkdir()
        _make_test_image(self.proj / "assets" / "img.png", size=(640, 360))
        catalog = {
            "schema_version": 2,
            "assets": [
                {
                    "id": "img", "filename": "img.png", "type": "image",
                    "role": "support", "linked_beats": ["beat-01"], "description": "test",
                }
            ],
        }
        with open(self.proj / "assets" / "catalog.json", "w") as f:
            json.dump(catalog, f, indent=2)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_enrich_project_writes_back(self):
        summary = enrich_project(self.proj, write_report=True)
        self.assertEqual(summary["totals"]["total"], 1)
        self.assertGreaterEqual(
            summary["totals"]["full"] + summary["totals"]["partial"], 1
        )

        with open(self.proj / "assets" / "catalog.json") as f:
            data = json.load(f)
        self.assertIn("enrichment", data["assets"][0])
        self.assertIn(data["assets"][0]["enrichment"]["status"], ("full", "partial"))
        self.assertTrue((self.proj / "output" / "enrichment-report.json").exists())

    def test_enrich_project_dry_run_does_not_write(self):
        summary = enrich_project(self.proj, dry_run=True, write_report=True)
        self.assertEqual(summary["totals"]["total"], 1)

        with open(self.proj / "assets" / "catalog.json") as f:
            data = json.load(f)
        self.assertNotIn("enrichment", data["assets"][0])
        self.assertFalse((self.proj / "output" / "enrichment-report.json").exists())

    def test_enrich_project_idempotent(self):
        enrich_project(self.proj, write_report=False)
        second = enrich_project(self.proj, write_report=False)
        self.assertEqual(second["totals"]["skipped_already"], 1)

    def test_enrich_project_force_re_runs(self):
        enrich_project(self.proj, write_report=False)
        result = enrich_project(self.proj, force=True, write_report=False)
        self.assertEqual(result["totals"]["skipped_already"], 0)

    def test_enrich_project_missing_catalog(self):
        empty_proj = Path(self.tmpdir.name) / "empty"
        empty_proj.mkdir()
        summary = enrich_project(empty_proj, write_report=False)
        self.assertTrue(summary["skipped"])

    def test_enrich_project_summary_records_optional_deps(self):
        summary = enrich_project(self.proj, write_report=False)
        self.assertIn("optional_deps", summary)
        for k in ("pillow", "cv2", "tesseract", "ffprobe", "ffmpeg"):
            self.assertIn(k, summary["optional_deps"])


# ── is_enriched ─────────────────────────────────────────────────────────


class TestIsEnriched(unittest.TestCase):
    def test_no_enrichment(self):
        self.assertFalse(is_enriched({}))
        self.assertFalse(is_enriched({"enrichment": None}))
        self.assertFalse(is_enriched({"enrichment": {}}))

    def test_not_enriched_status(self):
        self.assertFalse(is_enriched({"enrichment": {"status": "not_enriched"}}))

    def test_failed_status_not_considered_enriched(self):
        # 'failed' means we tried but couldn't — re-running may help
        self.assertFalse(is_enriched({"enrichment": {"status": "failed"}}))

    def test_full_enriched(self):
        self.assertTrue(is_enriched({"enrichment": {"status": "full"}}))

    def test_partial_enriched(self):
        self.assertTrue(is_enriched({"enrichment": {"status": "partial"}}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
