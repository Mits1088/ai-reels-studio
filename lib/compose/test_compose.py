"""
Tests for the reel composition engine.

Run: python -m pytest lib/compose/test_compose.py -v
  or: python lib/compose/test_compose.py
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lib.compose import layout as L
from lib.compose.scene_grammar import assign_scene_types, DEFAULT_GRAMMAR, EXTENDED_GRAMMAR
from lib.compose.renderer import (
    compose_frame, render_caption, render_primary, render_pip,
    render_lower_third, apply_transition, load_asset, clear_asset_cache,
    _make_placeholder, _fit_cover,
)
from lib.compose.assembler import (
    resolve_layers, generate_keyframes, generate_composition_report,
    collect_sfx_events, render_preview_sheet, ActiveLayers,
)
from lib.compose.encode import build_encode_spec, check_ffmpeg


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _make_beat_map(n_beats=6, total_duration=12.5):
    beats = []
    dur = total_duration / n_beats
    for i in range(n_beats):
        beats.append({
            "id": f"beat-{i + 1:02d}",
            "scene": (i // 2) + 1,
            "phrase": f"Phrase for beat {i + 1}",
            "start": round(i * dur, 3),
            "end": round((i + 1) * dur, 3),
            "words": [{"word": f"w{i}", "start": round(i * dur, 3), "end": round((i + 1) * dur, 3)}],
            "visual_intent": "",
            "asset_refs": [],
        })
    return {"total_duration": total_duration, "beats": beats}


def _make_timeline(beat_map, assets_dir=None):
    beats = beat_map["beats"]
    return {
        "total_duration": beat_map["total_duration"],
        "lanes": {
            "avatar": [
                {"beat_id": beats[0]["id"], "start": beats[0]["start"], "end": beats[0]["end"], "asset": "avatar.png"},
                {"beat_id": beats[-1]["id"], "start": beats[-1]["start"], "end": beats[-1]["end"], "asset": "avatar.png"},
            ],
            "demo": [
                {"beat_id": beats[2]["id"], "start": beats[2]["start"], "end": beats[3]["end"], "asset": "demo.png",
                 "transition": {"type": "fade", "duration": 0.2}},
            ],
            "support": [
                {"beat_id": beats[4]["id"], "start": beats[4]["start"], "end": beats[4]["end"], "asset": "support.png"},
            ],
            "captions": [
                {"beat_id": b["id"], "start": b["start"], "end": b["end"], "text": b["phrase"]}
                for b in beats
            ],
            "sfx": [
                {"start": beats[2]["start"] + 0.5, "end": beats[2]["start"] + 1.0, "asset": "whoosh.wav", "beat_id": beats[2]["id"]},
            ],
            "music": [
                {"start": 0.0, "end": beat_map["total_duration"], "asset": "bg.mp3", "volume": 0.15},
            ],
        },
    }


def _make_assets_dir(tmpdir: Path) -> Path:
    """Create dummy asset files."""
    assets = tmpdir / "assets"
    assets.mkdir(parents=True)
    # Create colored test images
    Image.new("RGB", (1080, 1920), (200, 50, 50)).save(assets / "avatar.png")
    Image.new("RGB", (1080, 1920), (50, 50, 200)).save(assets / "demo.png")
    Image.new("RGB", (1080, 1920), (50, 200, 50)).save(assets / "support.png")
    return assets


# ── Layout tests ─────────────────────────────────────────────────────────────

class TestLayout(unittest.TestCase):

    def test_canvas_dimensions(self):
        self.assertEqual(L.WIDTH, 1080)
        self.assertEqual(L.HEIGHT, 1920)

    def test_safe_zones(self):
        self.assertEqual(L.SAFE_MARGIN, 64)
        self.assertEqual(L.BOTTOM_RESERVED, 300)
        self.assertGreater(L.SAFE_WIDTH, 0)
        self.assertGreater(L.SAFE_HEIGHT, 0)
        self.assertEqual(L.SAFE_WIDTH, L.WIDTH - 2 * L.SAFE_MARGIN)

    def test_pip_in_safe_zone(self):
        # PiP must be within safe bounds
        self.assertGreaterEqual(L.PIP_X, L.SAFE_LEFT)
        self.assertLessEqual(L.PIP_X + L.PIP_SIZE, L.SAFE_RIGHT)
        self.assertLessEqual(L.PIP_Y + L.PIP_SIZE, L.SAFE_BOTTOM)

    def test_caption_above_reserved(self):
        self.assertLess(L.CAPTION_Y, L.HEIGHT - L.BOTTOM_RESERVED)

    def test_all_scene_types_defined(self):
        for scene in ["hook", "context", "demo", "proof", "news-hit", "cta"]:
            self.assertIn(scene, L.SCENE_LAYOUTS)

    def test_scene_layouts_have_required_lanes(self):
        for name, scene in L.SCENE_LAYOUTS.items():
            for lane in ("avatar", "demo", "support"):
                self.assertIn(lane, scene, f"Scene '{name}' missing lane '{lane}'")


# ── Scene grammar tests ─────────────────────────────────────────────────────

class TestSceneGrammar(unittest.TestCase):

    def test_single_beat(self):
        beats = [{"id": "beat-01"}]
        assign_scene_types(beats, 5.0)
        self.assertEqual(beats[0]["scene_type"], "hook")

    def test_two_beats(self):
        beats = [{"id": "beat-01"}, {"id": "beat-02"}]
        assign_scene_types(beats, 10.0)
        self.assertEqual(beats[0]["scene_type"], "hook")
        self.assertEqual(beats[1]["scene_type"], "cta")

    def test_standard_reel(self):
        beats = [{"id": f"beat-{i:02d}"} for i in range(1, 7)]
        assign_scene_types(beats, 15.0)
        # First = hook, last = cta
        self.assertEqual(beats[0]["scene_type"], "hook")
        self.assertEqual(beats[-1]["scene_type"], "cta")
        # All have a scene_type
        for b in beats:
            self.assertIn("scene_type", b)

    def test_extended_grammar_for_long_reels(self):
        beats = [{"id": f"beat-{i:02d}"} for i in range(1, 9)]
        assign_scene_types(beats, 45.0)
        self.assertEqual(beats[0]["scene_type"], "hook")
        self.assertEqual(beats[-1]["scene_type"], "cta")
        # Middle should include more scene types
        middle_types = {b["scene_type"] for b in beats[1:-1]}
        self.assertGreater(len(middle_types), 1)

    def test_custom_grammar(self):
        beats = [{"id": "beat-01"}, {"id": "beat-02"}, {"id": "beat-03"}]
        assign_scene_types(beats, 10.0, grammar=["hook", "demo", "cta"])
        self.assertEqual(beats[0]["scene_type"], "hook")
        self.assertEqual(beats[1]["scene_type"], "demo")
        self.assertEqual(beats[2]["scene_type"], "cta")


# ── Renderer tests ───────────────────────────────────────────────────────────

class TestRenderer(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.assets = _make_assets_dir(self.tmpdir)
        clear_asset_cache()

    def tearDown(self):
        clear_asset_cache()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_compose_frame_hook(self):
        frame = compose_frame(
            "hook", self.assets,
            avatar_file="avatar.png",
            caption_text="What if you could deploy?",
        )
        self.assertEqual(frame.size, (L.WIDTH, L.HEIGHT))
        self.assertEqual(frame.mode, "RGBA")

    def test_compose_frame_demo_with_pip(self):
        frame = compose_frame(
            "demo", self.assets,
            avatar_file="avatar.png",
            demo_file="demo.png",
            caption_text="Just click deploy",
        )
        self.assertEqual(frame.size, (L.WIDTH, L.HEIGHT))

    def test_compose_frame_proof(self):
        frame = compose_frame(
            "proof", self.assets,
            avatar_file="avatar.png",
            support_file="support.png",
        )
        self.assertEqual(frame.size, (L.WIDTH, L.HEIGHT))

    def test_compose_frame_cta(self):
        frame = compose_frame(
            "cta", self.assets,
            avatar_file="avatar.png",
            support_file="support.png",
            caption_text="Try it free!",
        )
        self.assertEqual(frame.size, (L.WIDTH, L.HEIGHT))

    def test_compose_frame_missing_assets(self):
        # Should use placeholders, not crash
        frame = compose_frame(
            "demo", self.assets,
            avatar_file="nonexistent.png",
            demo_file="also-missing.png",
        )
        self.assertEqual(frame.size, (L.WIDTH, L.HEIGHT))

    def test_compose_frame_no_assets(self):
        frame = compose_frame("hook", self.assets)
        self.assertEqual(frame.size, (L.WIDTH, L.HEIGHT))

    def test_caption_rendering(self):
        frame = Image.new("RGBA", (L.WIDTH, L.HEIGHT), (0, 0, 0, 255))
        result = render_caption(frame, "Hello world")
        self.assertEqual(result.size, (L.WIDTH, L.HEIGHT))
        # Caption area should not be all black anymore
        # Check a pixel in the caption zone
        self.assertNotEqual(result, frame)

    def test_caption_long_text_wraps(self):
        frame = Image.new("RGBA", (L.WIDTH, L.HEIGHT), (0, 0, 0, 255))
        result = render_caption(frame, "This is a very long caption that should wrap to multiple lines")
        self.assertEqual(result.size, (L.WIDTH, L.HEIGHT))

    def test_transition_cut(self):
        a = Image.new("RGBA", (L.WIDTH, L.HEIGHT), (255, 0, 0, 255))
        b = Image.new("RGBA", (L.WIDTH, L.HEIGHT), (0, 0, 255, 255))
        result = apply_transition(a, b, "cut", 0.5)
        self.assertEqual(result.size, (L.WIDTH, L.HEIGHT))
        # Cut at any progress < 1.0 returns frame_a
        pixel = result.getpixel((540, 960))
        self.assertEqual(pixel[:3], (255, 0, 0))

    def test_transition_fade_midpoint(self):
        a = Image.new("RGBA", (L.WIDTH, L.HEIGHT), (255, 0, 0, 255))
        b = Image.new("RGBA", (L.WIDTH, L.HEIGHT), (0, 0, 255, 255))
        result = apply_transition(a, b, "fade", 0.5)
        pixel = result.getpixel((540, 960))
        # Should be roughly purple (mix of red and blue)
        self.assertGreater(pixel[0], 50)  # some red
        self.assertGreater(pixel[2], 50)  # some blue

    def test_transition_fade_complete(self):
        a = Image.new("RGBA", (L.WIDTH, L.HEIGHT), (255, 0, 0, 255))
        b = Image.new("RGBA", (L.WIDTH, L.HEIGHT), (0, 0, 255, 255))
        result = apply_transition(a, b, "fade", 1.0)
        pixel = result.getpixel((540, 960))
        self.assertEqual(pixel[:3], (0, 0, 255))

    def test_transition_slide_up(self):
        a = Image.new("RGBA", (L.WIDTH, L.HEIGHT), (255, 0, 0, 255))
        b = Image.new("RGBA", (L.WIDTH, L.HEIGHT), (0, 0, 255, 255))
        result = apply_transition(a, b, "slide-up", 0.5)
        self.assertEqual(result.size, (L.WIDTH, L.HEIGHT))

    def test_placeholder_generation(self):
        img = _make_placeholder((400, 400), "test.png")
        self.assertEqual(img.size, (400, 400))
        self.assertEqual(img.mode, "RGBA")

    def test_fit_cover_landscape(self):
        src = Image.new("RGB", (1920, 1080), "red")
        result = _fit_cover(src, (1080, 1920))
        self.assertEqual(result.size, (1080, 1920))

    def test_fit_cover_portrait(self):
        src = Image.new("RGB", (500, 1000), "blue")
        result = _fit_cover(src, (1080, 1920))
        self.assertEqual(result.size, (1080, 1920))

    def test_render_primary_fills_canvas(self):
        frame = Image.new("RGBA", (L.WIDTH, L.HEIGHT), (0, 0, 0, 255))
        asset = Image.new("RGBA", (1080, 1920), (255, 0, 0, 255))
        result = render_primary(frame, asset)
        pixel = result.getpixel((540, 960))
        self.assertEqual(pixel[:3], (255, 0, 0))

    def test_render_pip_size_and_position(self):
        frame = Image.new("RGBA", (L.WIDTH, L.HEIGHT), (0, 0, 0, 255))
        asset = Image.new("RGBA", (200, 200), (0, 255, 0, 255))
        result = render_pip(frame, asset)
        # Check PiP center area has green
        cx = L.PIP_X + L.PIP_SIZE // 2
        cy = L.PIP_Y + L.PIP_SIZE // 2
        pixel = result.getpixel((cx, cy))
        self.assertEqual(pixel[:3], (0, 255, 0))


# ── Assembler tests ──────────────────────────────────────────────────────────

class TestAssembler(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.assets = _make_assets_dir(self.tmpdir)
        self.beat_map = _make_beat_map()
        self.timeline = _make_timeline(self.beat_map)
        clear_asset_cache()

    def tearDown(self):
        clear_asset_cache()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_resolve_layers_at_start(self):
        assign_scene_types(self.beat_map["beats"], self.beat_map["total_duration"])
        layers = resolve_layers(self.timeline, self.beat_map, 0.5)
        self.assertIsNotNone(layers.beat_id)
        self.assertEqual(layers.avatar_file, "avatar.png")
        self.assertIsNotNone(layers.caption_text)

    def test_resolve_layers_during_demo(self):
        assign_scene_types(self.beat_map["beats"], self.beat_map["total_duration"])
        # Beat 3 starts at ~4.17s
        t = self.beat_map["beats"][2]["start"] + 0.5
        layers = resolve_layers(self.timeline, self.beat_map, t)
        self.assertEqual(layers.demo_file, "demo.png")

    def test_resolve_layers_no_active_entries(self):
        assign_scene_types(self.beat_map["beats"], self.beat_map["total_duration"])
        # Time way past the end
        layers = resolve_layers(self.timeline, self.beat_map, 999.0)
        self.assertIsNone(layers.avatar_file)
        self.assertIsNone(layers.demo_file)

    def test_collect_sfx_events(self):
        events = collect_sfx_events(self.timeline)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].file, "whoosh.wav")

    def test_generate_keyframes(self):
        keyframes = generate_keyframes(self.timeline, self.beat_map, self.assets)
        self.assertEqual(len(keyframes), 6)
        for t, beat_id, frame in keyframes:
            self.assertIsInstance(t, float)
            self.assertTrue(beat_id.startswith("beat-"))
            self.assertEqual(frame.size, (L.WIDTH, L.HEIGHT))

    def test_keyframes_are_chronological(self):
        keyframes = generate_keyframes(self.timeline, self.beat_map, self.assets)
        times = [t for t, _, _ in keyframes]
        self.assertEqual(times, sorted(times))

    def test_composition_report(self):
        report = generate_composition_report(self.timeline, self.beat_map)
        self.assertEqual(len(report), 6)
        for entry in report:
            self.assertIn("beat_id", entry)
            self.assertIn("scene_type", entry)
            self.assertIn("time", entry)
            self.assertIn("layers", entry)
            self.assertIn("transition", entry)
            self.assertIn("sfx", entry)

    def test_report_first_is_hook(self):
        report = generate_composition_report(self.timeline, self.beat_map)
        self.assertEqual(report[0]["scene_type"], "hook")

    def test_report_last_is_cta(self):
        report = generate_composition_report(self.timeline, self.beat_map)
        self.assertEqual(report[-1]["scene_type"], "cta")

    def test_report_shows_sfx(self):
        report = generate_composition_report(self.timeline, self.beat_map)
        # SFX is in beat-03's time range
        beat_03_report = next(r for r in report if r["beat_id"] == "beat-03")
        self.assertGreater(len(beat_03_report["sfx"]), 0)

    def test_preview_sheet(self):
        keyframes = generate_keyframes(self.timeline, self.beat_map, self.assets)
        sheet = render_preview_sheet(keyframes)
        self.assertIsInstance(sheet, Image.Image)
        self.assertGreater(sheet.width, 0)
        self.assertGreater(sheet.height, 0)


# ── Encoder spec tests ───────────────────────────────────────────────────────

class TestEncodeSpec(unittest.TestCase):

    def test_encode_spec_structure(self):
        timeline = _make_timeline(_make_beat_map())
        spec = build_encode_spec(Path("projects/test"), timeline)
        self.assertEqual(spec["resolution"], "1080x1920")
        self.assertEqual(spec["fps"], 30)
        self.assertEqual(spec["codec_video"], "H.264")
        self.assertEqual(spec["codec_audio"], "AAC")
        self.assertEqual(spec["format"], "MP4")
        self.assertIn("ffmpeg_available", spec)

    def test_encode_spec_includes_music(self):
        timeline = _make_timeline(_make_beat_map())
        spec = build_encode_spec(Path("projects/test"), timeline)
        self.assertIsNotNone(spec["music"])
        self.assertEqual(spec["music"]["volume"], 0.15)


# ── Smoke render test (full pipeline) ────────────────────────────────────────

class TestSmokeRender(unittest.TestCase):
    """End-to-end: generate keyframes, preview sheet, and composition report from sample data."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.assets = _make_assets_dir(self.tmpdir)
        self.output = self.tmpdir / "output"
        self.output.mkdir()
        clear_asset_cache()

    def tearDown(self):
        clear_asset_cache()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_smoke_render(self):
        beat_map = _make_beat_map()
        timeline = _make_timeline(beat_map)

        # 1. Generate keyframes
        keyframes = generate_keyframes(timeline, beat_map, self.assets)
        self.assertEqual(len(keyframes), 6)

        # 2. Save individual keyframes
        for t, beat_id, frame in keyframes:
            path = self.output / f"{beat_id}.png"
            frame.convert("RGB").save(path)
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 0)

        # 3. Generate preview sheet
        sheet = render_preview_sheet(keyframes)
        sheet_path = self.output / "preview_sheet.png"
        sheet.save(sheet_path)
        self.assertTrue(sheet_path.exists())

        # 4. Generate composition report
        report = generate_composition_report(timeline, beat_map)
        report_path = self.output / "composition_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        self.assertTrue(report_path.exists())

        # 5. Generate encode spec
        spec = build_encode_spec(self.tmpdir, timeline)
        spec_path = self.output / "encode_spec.json"
        with open(spec_path, "w") as f:
            json.dump(spec, f, indent=2)
        self.assertTrue(spec_path.exists())

        # Verify outputs
        output_files = list(self.output.iterdir())
        self.assertGreaterEqual(len(output_files), 8)  # 6 keyframes + sheet + report + spec


if __name__ == "__main__":
    unittest.main(verbosity=2)
