"""
Contract validation tests.

Run: python -m pytest lib/test_contracts.py -v
  or: python lib/test_contracts.py
"""

import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.validate import (
    validate_project,
    validate_beat_map,
    validate_timeline,
    validate_project_dir,
)

# ── Fixtures ─────────────────────────────────────────────────────────────────

VALID_PROJECT = {
    "schema_version": 2,
    "project_type": "reel",
    "slug": "test-reel",
    "title": "Test Reel",
    "phase": "init",
    "status": "initialized",
    "gates_passed": [],
    "created": "2026-03-19T10:00:00Z",
    "updated": "2026-03-19T10:00:00Z",
    "voice_file": None,
    "duration_s": None,
}

VALID_BEAT_MAP = {
    "total_duration": 5.000,
    "beats": [
        {
            "id": "beat-01",
            "scene": 1,
            "phrase": "Hello world",
            "start": 0.000,
            "end": 2.500,
            "words": [
                {"word": "Hello", "start": 0.000, "end": 1.200},
                {"word": "world", "start": 1.300, "end": 2.500},
            ],
            "visual_intent": "Text overlay",
            "asset_refs": ["hero.png"],
        },
        {
            "id": "beat-02",
            "scene": 1,
            "phrase": "Check it out",
            "start": 2.600,
            "end": 5.000,
            "words": [
                {"word": "Check", "start": 2.600, "end": 3.100},
                {"word": "it", "start": 3.200, "end": 3.500},
                {"word": "out", "start": 3.600, "end": 5.000},
            ],
            "visual_intent": "Demo clip",
            "asset_refs": ["demo.mp4"],
        },
    ],
}

VALID_TIMELINE = {
    "total_duration": 5.000,
    "lanes": {
        "avatar": [
            {"beat_id": "beat-01", "start": 0.000, "end": 2.500, "asset": "avatar.mp4"},
        ],
        "demo": [
            {"beat_id": "beat-02", "start": 2.600, "end": 5.000, "asset": "demo.mp4"},
        ],
        "support": [],
        "captions": [
            {"beat_id": "beat-01", "start": 0.000, "end": 2.500, "text": "Hello world"},
            {"beat_id": "beat-02", "start": 2.600, "end": 5.000, "text": "Check it out"},
        ],
        "sfx": [],
        "music": [
            {"start": 0.000, "end": 5.000, "asset": "bg.mp3", "volume": 0.2},
        ],
    },
}


def _mutate(base: dict, path: str, value="__DELETE__") -> dict:
    """Deep copy and mutate a nested dict. path like 'beats[0].id'. __DELETE__ removes the key."""
    data = copy.deepcopy(base)
    parts = []
    for p in path.split("."):
        if "[" in p:
            key, idx = p.rstrip("]").split("[")
            parts.append(key)
            parts.append(int(idx))
        else:
            parts.append(p)

    obj = data
    for part in parts[:-1]:
        obj = obj[part]

    if value == "__DELETE__":
        del obj[parts[-1]]
    else:
        obj[parts[-1]] = value
    return data


# ── Tests ────────────────────────────────────────────────────────────────────

class TestProjectValidation(unittest.TestCase):

    def test_valid_project_passes(self):
        self.assertEqual(validate_project(VALID_PROJECT), [])

    def test_missing_slug(self):
        data = _mutate(VALID_PROJECT, "slug")
        errs = validate_project(data)
        self.assertTrue(any("slug" in e.field for e in errs))

    def test_invalid_slug_format(self):
        data = _mutate(VALID_PROJECT, "slug", "Bad Slug!")
        errs = validate_project(data)
        self.assertTrue(any("slug" in e.field for e in errs))

    def test_invalid_phase(self):
        data = _mutate(VALID_PROJECT, "phase", "brainstorm")
        errs = validate_project(data)
        self.assertTrue(any("phase" in e.field for e in errs))

    def test_invalid_status(self):
        data = _mutate(VALID_PROJECT, "status", "shipped")
        errs = validate_project(data)
        self.assertTrue(any("status" in e.field for e in errs))

    def test_missing_required_fields(self):
        for field in ("title", "phase", "status", "created", "updated"):
            data = _mutate(VALID_PROJECT, field)
            errs = validate_project(data)
            self.assertTrue(any(field in e.field for e in errs), f"Should catch missing {field}")

    def test_valid_style(self):
        data = copy.deepcopy(VALID_PROJECT)
        data["style"] = "editorial-authority"
        self.assertEqual(validate_project(data), [])

    def test_invalid_style(self):
        data = copy.deepcopy(VALID_PROJECT)
        data["style"] = "neon-glitch"
        errs = validate_project(data)
        self.assertTrue(any("style" in e.field for e in errs))

    def test_valid_gates_passed(self):
        data = copy.deepcopy(VALID_PROJECT)
        data["gates_passed"] = ["brief_approved", "theme_set"]
        data["theme"] = "claude"
        data["theme_primary"] = "#D97757"
        data["theme_secondary"] = "#E8B88A"
        self.assertEqual(validate_project(data), [])

    def test_invalid_gate_id(self):
        data = copy.deepcopy(VALID_PROJECT)
        data["gates_passed"] = ["brief_approved", "fake_gate"]
        errs = validate_project(data)
        self.assertTrue(any("unknown gate" in e.message for e in errs))

    def test_theme_set_requires_theme_fields(self):
        data = copy.deepcopy(VALID_PROJECT)
        data["gates_passed"] = ["theme_set"]
        # theme fields missing
        errs = validate_project(data)
        self.assertTrue(any("theme" in e.field for e in errs))

    def test_invalid_color_hex(self):
        data = copy.deepcopy(VALID_PROJECT)
        data["theme_primary"] = "not-a-color"
        errs = validate_project(data)
        self.assertTrue(any("theme_primary" in e.field for e in errs))

    def test_valid_color_hex(self):
        data = copy.deepcopy(VALID_PROJECT)
        data["theme_primary"] = "#D97757"
        self.assertEqual(validate_project(data), [])


class TestBeatMapValidation(unittest.TestCase):

    def test_valid_beat_map_passes(self):
        self.assertEqual(validate_beat_map(VALID_BEAT_MAP), [])

    def test_missing_total_duration(self):
        data = _mutate(VALID_BEAT_MAP, "total_duration")
        errs = validate_beat_map(data)
        self.assertTrue(any("total_duration" in e.field for e in errs))

    def test_empty_beats(self):
        data = copy.deepcopy(VALID_BEAT_MAP)
        data["beats"] = []
        errs = validate_beat_map(data)
        self.assertTrue(any("beats" in e.field for e in errs))

    def test_duplicate_beat_id(self):
        data = copy.deepcopy(VALID_BEAT_MAP)
        data["beats"][1]["id"] = "beat-01"  # duplicate
        errs = validate_beat_map(data)
        self.assertTrue(any("duplicate" in e.message for e in errs))

    def test_invalid_beat_id_format(self):
        data = _mutate(VALID_BEAT_MAP, "beats[0].id", "scene1")
        errs = validate_beat_map(data)
        self.assertTrue(any("invalid beat ID" in e.message for e in errs))

    def test_sub_beat_id_allowed(self):
        data = copy.deepcopy(VALID_BEAT_MAP)
        data["beats"][0]["id"] = "beat-01a"
        errs = validate_beat_map(data)
        self.assertFalse(any("invalid beat ID" in e.message for e in errs))

    def test_beat_end_before_start(self):
        data = copy.deepcopy(VALID_BEAT_MAP)
        data["beats"][0]["end"] = 0.000
        data["beats"][0]["start"] = 2.500
        errs = validate_beat_map(data)
        self.assertTrue(any("end must be > start" in e.message for e in errs))

    def test_overlapping_beats(self):
        data = copy.deepcopy(VALID_BEAT_MAP)
        data["beats"][1]["start"] = 1.000  # overlaps with beat-01 ending at 2.5
        errs = validate_beat_map(data)
        self.assertTrue(any("overlaps" in e.message for e in errs))

    def test_beat_exceeds_total_duration(self):
        data = copy.deepcopy(VALID_BEAT_MAP)
        data["beats"][-1]["end"] = 99.0
        errs = validate_beat_map(data)
        self.assertTrue(any("exceeds total_duration" in e.message for e in errs))

    def test_missing_beat_fields(self):
        for field in ("id", "scene", "phrase", "start", "end", "words", "visual_intent"):
            data = _mutate(VALID_BEAT_MAP, f"beats[0].{field}")
            errs = validate_beat_map(data)
            self.assertTrue(any(field in e.field for e in errs), f"Should catch missing {field}")

    def test_empty_words(self):
        data = copy.deepcopy(VALID_BEAT_MAP)
        data["beats"][0]["words"] = []
        errs = validate_beat_map(data)
        self.assertTrue(any("words" in e.field for e in errs))

    def test_word_end_before_start(self):
        data = copy.deepcopy(VALID_BEAT_MAP)
        data["beats"][0]["words"][0]["end"] = 0.0
        data["beats"][0]["words"][0]["start"] = 1.0
        errs = validate_beat_map(data)
        self.assertTrue(any("word end" in e.message for e in errs))


class TestTimelineValidation(unittest.TestCase):

    def test_valid_timeline_passes(self):
        beat_ids = {"beat-01", "beat-02"}
        self.assertEqual(validate_timeline(VALID_TIMELINE, beat_ids=beat_ids), [])

    def test_missing_lane(self):
        data = copy.deepcopy(VALID_TIMELINE)
        del data["lanes"]["captions"]
        errs = validate_timeline(data)
        self.assertTrue(any("captions" in e.field for e in errs))

    def test_caption_without_text(self):
        data = copy.deepcopy(VALID_TIMELINE)
        del data["lanes"]["captions"][0]["text"]
        errs = validate_timeline(data)
        self.assertTrue(any("text" in e.field for e in errs))

    def test_caption_without_beat_id(self):
        data = copy.deepcopy(VALID_TIMELINE)
        del data["lanes"]["captions"][0]["beat_id"]
        errs = validate_timeline(data)
        self.assertTrue(any("beat_id" in e.field for e in errs))

    def test_visual_lane_without_asset(self):
        data = copy.deepcopy(VALID_TIMELINE)
        del data["lanes"]["avatar"][0]["asset"]
        errs = validate_timeline(data)
        self.assertTrue(any("asset" in e.field for e in errs))

    def test_nonexistent_beat_reference(self):
        beat_ids = {"beat-01"}  # beat-02 missing
        errs = validate_timeline(VALID_TIMELINE, beat_ids=beat_ids)
        self.assertTrue(any("nonexistent beat" in e.message for e in errs))

    def test_nonexistent_asset_reference(self):
        asset_files = {"avatar.mp4"}  # demo.mp4 missing
        errs = validate_timeline(VALID_TIMELINE, asset_files=asset_files)
        self.assertTrue(any("nonexistent asset" in e.message for e in errs))

    def test_transition_too_long(self):
        data = copy.deepcopy(VALID_TIMELINE)
        data["lanes"]["demo"][0]["transition"] = {"type": "fade", "duration": 0.5}
        errs = validate_timeline(data)
        self.assertTrue(any("exceeds max" in e.message for e in errs))

    def test_end_before_start(self):
        data = copy.deepcopy(VALID_TIMELINE)
        data["lanes"]["avatar"][0]["start"] = 5.0
        data["lanes"]["avatar"][0]["end"] = 1.0
        errs = validate_timeline(data)
        self.assertTrue(any("end must be > start" in e.message for e in errs))

    def test_missing_total_duration(self):
        data = copy.deepcopy(VALID_TIMELINE)
        del data["total_duration"]
        errs = validate_timeline(data)
        self.assertTrue(any("total_duration" in e.field for e in errs))


class TestExampleProjectValidation(unittest.TestCase):
    """Validates the example project files pass all contracts."""

    def test_example_project_json(self):
        path = Path(__file__).resolve().parent.parent / "templates" / "example-project" / "project.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(validate_project(data), [])

    def test_example_beat_map(self):
        path = Path(__file__).resolve().parent.parent / "templates" / "example-project" / "audio" / "beat-map.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(validate_beat_map(data), [])

    def test_example_timeline(self):
        bm_path = Path(__file__).resolve().parent.parent / "templates" / "example-project" / "audio" / "beat-map.json"
        tl_path = Path(__file__).resolve().parent.parent / "templates" / "example-project" / "output" / "timeline.json"
        bm = json.loads(bm_path.read_text(encoding="utf-8"))
        tl = json.loads(tl_path.read_text(encoding="utf-8"))
        beat_ids = {b["id"] for b in bm["beats"]}
        self.assertEqual(validate_timeline(tl, beat_ids=beat_ids), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
