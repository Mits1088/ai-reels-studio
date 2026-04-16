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


# ── Phase A: lib/grammar/ + edit_plan.schema.json drift detectors ────────────


class TestProofClasses(unittest.TestCase):
    """lib/grammar/proof_classes.py — proof class validation."""

    def test_seven_proof_classes(self):
        from lib.grammar import PROOF_ORDER, PROOF_CLASSES
        self.assertEqual(len(PROOF_ORDER), 7)
        self.assertEqual(PROOF_ORDER[0], "existence")
        self.assertEqual(PROOF_ORDER[-1], "cta")
        self.assertEqual(set(PROOF_ORDER), set(PROOF_CLASSES))

    def test_valid_proof_classes(self):
        from lib.grammar import is_valid_proof_class
        for c in ("existence", "breadth", "process", "output",
                  "integration", "authority", "cta"):
            self.assertTrue(is_valid_proof_class(c), f"{c} should be valid")
        self.assertTrue(is_valid_proof_class(None))
        self.assertFalse(is_valid_proof_class("evidence"))
        self.assertFalse(is_valid_proof_class(""))

    def test_proof_arc_forward(self):
        from lib.grammar import validate_proof_arc
        self.assertEqual(
            validate_proof_arc(["existence", "breadth", "process", "output", "cta"]),
            [],
        )

    def test_proof_arc_with_nones(self):
        from lib.grammar import validate_proof_arc
        # Nones are transparent — they neither advance nor regress the arc
        self.assertEqual(
            validate_proof_arc(["existence", None, "breadth", None, "cta"]),
            [],
        )

    def test_proof_arc_repeats_allowed(self):
        from lib.grammar import validate_proof_arc
        # Same class twice in a row is fine — only backward jumps are errors
        self.assertEqual(
            validate_proof_arc(["existence", "existence", "breadth", "breadth", "cta"]),
            [],
        )

    def test_proof_arc_backward_jump(self):
        from lib.grammar import validate_proof_arc
        errors = validate_proof_arc(["existence", "process", "breadth"])
        self.assertEqual(len(errors), 1)
        self.assertIn("backward", errors[0])

    def test_proof_arc_backward_jump_to_existence(self):
        from lib.grammar import validate_proof_arc
        errors = validate_proof_arc(["cta", "existence"])
        self.assertEqual(len(errors), 1)
        self.assertIn("backward", errors[0])

    def test_proof_arc_unknown_class(self):
        from lib.grammar import validate_proof_arc
        errors = validate_proof_arc(["existence", "evidence", "cta"])
        self.assertTrue(any("unknown" in e for e in errors))


class TestMotionPresets(unittest.TestCase):
    """lib/grammar/motion_presets.py — preset vocabulary and budget."""

    def _load_timeline_schema(self) -> dict:
        path = Path(__file__).resolve().parent / "schemas" / "timeline.schema.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_renderer_enter_matches_timeline_schema(self):
        """Drift detector: Python renderer enums must match timeline.schema.json."""
        from lib.grammar import RENDERER_ENTER_PRESETS
        schema = self._load_timeline_schema()
        schema_enter = set(
            schema["$defs"]["transition_preset"]["properties"]["enter"]["enum"]
        )
        self.assertEqual(
            set(RENDERER_ENTER_PRESETS), schema_enter,
            "RENDERER_ENTER_PRESETS in lib/grammar drifted from timeline.schema.json"
        )

    def test_renderer_exit_matches_timeline_schema(self):
        from lib.grammar import RENDERER_EXIT_PRESETS
        schema = self._load_timeline_schema()
        schema_exit = set(
            schema["$defs"]["transition_preset"]["properties"]["exit"]["enum"]
        )
        self.assertEqual(
            set(RENDERER_EXIT_PRESETS), schema_exit,
            "RENDERER_EXIT_PRESETS in lib/grammar drifted from timeline.schema.json"
        )

    def test_editorial_subset_of_renderer(self):
        from lib.grammar import (
            RENDERER_ENTER_PRESETS, RENDERER_EXIT_PRESETS,
            EDITORIAL_ENTER_PRESETS, EDITORIAL_EXIT_PRESETS,
        )
        self.assertTrue(EDITORIAL_ENTER_PRESETS.issubset(RENDERER_ENTER_PRESETS))
        self.assertTrue(EDITORIAL_EXIT_PRESETS.issubset(RENDERER_EXIT_PRESETS))

    def test_motion_budget_requires_hero(self):
        from lib.grammar import MotionBudget, validate_motion_budget
        errors = validate_motion_budget(MotionBudget())
        self.assertTrue(any("hero" in e for e in errors))

    def test_motion_budget_valid_minimal(self):
        from lib.grammar import MotionBudget, MotionEvent, validate_motion_budget
        b = MotionBudget(
            hero=MotionEvent(kind="scale-entrance", preset="scale-pop", duration_frames=5),
        )
        self.assertEqual(validate_motion_budget(b), [])

    def test_motion_budget_full_three_slots(self):
        from lib.grammar import MotionBudget, MotionEvent, validate_motion_budget
        b = MotionBudget(
            hero=MotionEvent(kind="wipe", preset="wipe-up", duration_frames=5),
            support=MotionEvent(kind="settle", preset="fade", duration_frames=4),
            accent=MotionEvent(kind="pulse", preset="scale-pop", duration_frames=4),
        )
        self.assertEqual(validate_motion_budget(b), [])
        self.assertEqual(b.used_slots(), 3)
        self.assertEqual(len(b.events()), 3)

    def test_motion_budget_rejects_non_editorial_preset(self):
        from lib.grammar import MotionBudget, MotionEvent, validate_motion_budget
        b = MotionBudget(hero=MotionEvent(kind="glitch", preset="glitch"))
        errors = validate_motion_budget(b, enforce_editorial=True)
        self.assertTrue(any("glitch" in e for e in errors))

    def test_motion_budget_accepts_renderer_preset_when_lax(self):
        from lib.grammar import MotionBudget, MotionEvent, validate_motion_budget
        b = MotionBudget(hero=MotionEvent(kind="glitch", preset="glitch"))
        # glitch is in renderer enter set, so should be accepted in lax mode
        self.assertEqual(validate_motion_budget(b, enforce_editorial=False), [])

    def test_motion_budget_duration_bounds_enter(self):
        from lib.grammar import MotionBudget, MotionEvent, validate_motion_budget
        b = MotionBudget(
            hero=MotionEvent(kind="wipe", preset="wipe-up", duration_frames=20),
        )
        errors = validate_motion_budget(b)
        self.assertTrue(any("outside bounds" in e for e in errors))

    def test_motion_budget_duration_bounds_exit(self):
        from lib.grammar import MotionBudget, MotionEvent, validate_motion_budget
        b = MotionBudget(
            hero=MotionEvent(kind="exit", preset="fade", duration_frames=10),
        )
        errors = validate_motion_budget(b)
        # 10 is within enter bounds [3,10], so this should pass — fade is in BOTH sets
        # but the validator picks enter set first via `if in_enter`
        self.assertEqual(errors, [])

    def test_preferred_presets_for_hook(self):
        from lib.grammar import preferred_presets_for
        prefs = preferred_presets_for("hook")
        self.assertIn("hero", prefs)
        self.assertIn("punch", prefs["hero"])

    def test_preferred_presets_for_unknown(self):
        from lib.grammar import preferred_presets_for
        self.assertEqual(preferred_presets_for("nonsense"), {})

    def test_beat_categories(self):
        from lib.grammar import BEAT_CATEGORIES
        self.assertEqual(
            BEAT_CATEGORIES,
            frozenset({"avatar", "demo", "concept", "return", "hook", "cta"}),
        )

    def test_is_editorial_helpers(self):
        from lib.grammar import (
            is_editorial_enter, is_editorial_exit,
            is_renderer_enter, is_renderer_exit,
        )
        self.assertTrue(is_editorial_enter("wipe-up"))
        self.assertFalse(is_editorial_enter("glitch"))
        self.assertTrue(is_renderer_enter("glitch"))
        self.assertTrue(is_editorial_exit("fade"))
        self.assertTrue(is_renderer_exit("blur-out"))


class TestTemplateRegistry(unittest.TestCase):
    """lib/grammar/templates.py — template registry loader."""

    def test_load_default_registry(self):
        from lib.grammar import load_template_registry
        reg = load_template_registry()
        self.assertGreaterEqual(len(reg.templates), 1)
        for tid, tmpl in reg.templates.items():
            self.assertEqual(tmpl.id, tid)
            self.assertIn(tmpl.template_class, {"ANCHOR", "PROOF"})

    def test_known_template_avatar_direct(self):
        from lib.grammar import load_template_registry
        reg = load_template_registry()
        if reg.has("avatar-direct"):
            t = reg.get("avatar-direct")
            self.assertEqual(t.template_class, "ANCHOR")
            self.assertEqual(reg.caption_mode_for("avatar-direct"), "headline")

    def test_caption_mode_for_demo_fullscreen(self):
        from lib.grammar import load_template_registry
        reg = load_template_registry()
        if reg.has("demo-fullscreen"):
            self.assertEqual(reg.caption_mode_for("demo-fullscreen"), "suppressed")

    def test_caption_mode_unknown_template(self):
        from lib.grammar import load_template_registry
        reg = load_template_registry()
        self.assertIsNone(reg.caption_mode_for("nonexistent-template"))

    def test_by_class_partition(self):
        from lib.grammar import load_template_registry
        reg = load_template_registry()
        anchors = reg.by_class("ANCHOR")
        proofs = reg.by_class("PROOF")
        self.assertEqual(len(anchors) + len(proofs), len(reg.templates))

    def test_by_class_invalid_returns_empty(self):
        from lib.grammar import load_template_registry
        reg = load_template_registry()
        self.assertEqual(reg.by_class("WHATEVER"), [])

    def test_by_proof_class(self):
        from lib.grammar import load_template_registry
        reg = load_template_registry()
        # demo-fullscreen serves "process" in the nicholas-puru registry
        if reg.has("demo-fullscreen"):
            templates = reg.by_proof_class("process")
            self.assertTrue(any(t.id == "demo-fullscreen" for t in templates))

    def test_missing_registry_returns_empty(self):
        from lib.grammar import load_template_registry
        reg = load_template_registry(
            registry_path=Path("/nonexistent/registry.json"),
            caption_modes_path=Path("/nonexistent/captions.json"),
        )
        self.assertEqual(reg.templates, {})
        self.assertEqual(reg.template_to_caption_mode, {})
        self.assertEqual(reg.derived_from, ())


class TestEditPlanSchema(unittest.TestCase):
    """lib/schemas/edit_plan.schema.json — structural sanity + drift detection.

    Phase A: schema is contract-only, not yet enforced by any pipeline step.
    These tests verify it loads and that its enums stay aligned with the
    Python grammar. Phase C will add semantic validation in lib/edit_plan/.
    """

    def _load(self) -> dict:
        path = Path(__file__).resolve().parent / "schemas" / "edit_plan.schema.json"
        self.assertTrue(path.exists(), f"edit_plan.schema.json not found at {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_schema_loads(self):
        data = self._load()
        self.assertEqual(data["title"], "edit-plan.json")
        self.assertIn("beats", data["properties"])
        self.assertIn("schema_version", data["properties"])
        self.assertIn("project_slug", data["properties"])
        self.assertIn("style", data["properties"])

    def test_schema_required_top_level(self):
        # Phase C: style was relaxed to optional so reverse-engineered plans
        # can faithfully round-trip legacy timelines without a top-level
        # style field. The validator still checks the value is in the enum
        # when present.
        data = self._load()
        required = set(data["required"])
        self.assertEqual(
            required,
            {"schema_version", "project_slug", "beats"},
        )

    def test_schema_proof_class_enum_matches_grammar(self):
        from lib.grammar import PROOF_ORDER
        data = self._load()
        beat_plan = data["$defs"]["beat_plan"]
        proof_class_def = beat_plan["properties"]["proof_class"]
        enum_values = None
        for branch in proof_class_def["oneOf"]:
            if branch.get("type") == "string":
                enum_values = branch.get("enum", [])
        self.assertIsNotNone(enum_values, "proof_class oneOf has no string branch")
        self.assertEqual(
            set(enum_values), set(PROOF_ORDER),
            "edit_plan.schema.json proof_class enum drifted from grammar.PROOF_ORDER",
        )

    def test_schema_caption_mode_enum_matches_grammar(self):
        from lib.grammar import VALID_CAPTION_MODES
        data = self._load()
        beat_plan = data["$defs"]["beat_plan"]
        caption_mode_enum = set(beat_plan["properties"]["caption_mode"]["enum"])
        self.assertEqual(
            caption_mode_enum, set(VALID_CAPTION_MODES),
            "edit_plan.schema.json caption_mode enum drifted from grammar.VALID_CAPTION_MODES",
        )

    def test_schema_style_enum_matches_constants(self):
        from lib.constants import VALID_STYLES
        data = self._load()
        style_enum = set(data["properties"]["style"]["enum"])
        self.assertEqual(
            style_enum, set(VALID_STYLES),
            "edit_plan.schema.json style enum drifted from lib.constants.VALID_STYLES",
        )

    def test_schema_beat_plan_required_fields(self):
        """Phase D mandatory fields per amendment: candidate_assets, selected_asset_id,
        selection_confidence, selection_reason, fallback_asset_ids, human_review_required."""
        data = self._load()
        required = set(data["$defs"]["beat_plan"]["required"])
        for field in (
            "beat_id",
            "template_id",
            "avatar_mode",
            "caption_mode",
            "split_ratio",
            "candidate_assets",
            "selected_asset_id",
            "selection_confidence",
            "selection_reason",
            "fallback_asset_ids",
            "human_review_required",
            "motion_budget",
            "rationale",
        ):
            self.assertIn(field, required, f"beat_plan must require {field}")

    def test_schema_motion_budget_requires_hero(self):
        data = self._load()
        motion_budget = data["$defs"]["motion_budget"]
        self.assertEqual(motion_budget["required"], ["hero"])


# ── Phase B: catalog v2 schema + migration ─────────────────────────────────


class TestCatalogV2(unittest.TestCase):
    """v2 catalog schema, validator, and dataclass round-trip."""

    def test_catalog_dataclass_writes_schema_version(self):
        from lib.capture.catalog import Catalog, AssetEntry
        cat = Catalog(assets=[
            AssetEntry(
                id="asset-1", filename="x.png", type="image", role="support",
                linked_beats=["beat-01"], description="test",
            )
        ])
        d = cat.to_dict()
        self.assertEqual(d["schema_version"], 2)
        self.assertEqual(len(d["assets"]), 1)

    def test_broll_role_now_valid(self):
        from lib.capture.catalog import ASSET_ROLES
        self.assertIn("broll", ASSET_ROLES)

    def test_url_import_source_now_valid(self):
        from lib.capture.catalog import ASSET_SOURCES
        self.assertIn("url-import", ASSET_SOURCES)

    def test_asset_entry_has_v2_fields(self):
        from lib.capture.catalog import AssetEntry
        a = AssetEntry(
            id="x", filename="x.png", type="image", role="support",
            linked_beats=["beat-01"], description="x",
            source_url="https://example.com/x.png",
            enrichment={"status": "full", "schema_version": 1, "derived_at": "now", "derived_by": "t"},
        )
        d = a.to_dict()
        self.assertEqual(d["source_url"], "https://example.com/x.png")
        self.assertEqual(d["enrichment"]["status"], "full")

    def test_asset_entry_omits_optional_v2_fields_when_none(self):
        from lib.capture.catalog import AssetEntry
        a = AssetEntry(
            id="x", filename="x.png", type="image", role="support",
            linked_beats=["beat-01"], description="x",
        )
        d = a.to_dict()
        self.assertNotIn("source_url", d)
        self.assertNotIn("enrichment", d)

    def test_validator_rejects_v1_catalog_with_migration_hint(self):
        from lib.capture.validate_catalog import validate_catalog
        v1 = {"assets": [
            {"id": "x", "filename": "x.png", "type": "image", "role": "support",
             "linked_beats": ["beat-01"], "description": "x"}
        ]}
        errs = validate_catalog(v1)
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs[0].field, "schema_version")
        self.assertIn("migration", errs[0].message)
        self.assertIn("--target catalog", errs[0].message)

    def test_validator_rejects_unsupported_schema_version(self):
        from lib.capture.validate_catalog import validate_catalog
        bad = {"schema_version": 99, "assets": []}
        errs = validate_catalog(bad)
        self.assertTrue(any("unsupported catalog schema_version" in e.message for e in errs))

    def test_validator_accepts_minimal_v2_catalog(self):
        from lib.capture.validate_catalog import validate_catalog
        v2 = {
            "schema_version": 2,
            "assets": [{
                "id": "x", "filename": "x.png", "type": "image", "role": "support",
                "linked_beats": ["beat-01"], "description": "x",
            }],
        }
        errs = validate_catalog(v2)
        self.assertFalse(any("schema_version" in e.field for e in errs))

    def test_validator_accepts_broll_role(self):
        from lib.capture.validate_catalog import validate_catalog
        v2 = {
            "schema_version": 2,
            "assets": [{
                "id": "x", "filename": "x.mp4", "type": "video", "role": "broll",
                "linked_beats": ["beat-01"], "description": "x",
            }],
        }
        errs = validate_catalog(v2)
        self.assertFalse(any("invalid role" in e.message for e in errs))

    def test_validator_accepts_url_import_source(self):
        from lib.capture.validate_catalog import validate_catalog
        v2 = {
            "schema_version": 2,
            "assets": [{
                "id": "x", "filename": "x.mp4", "type": "video", "role": "broll",
                "linked_beats": ["beat-01"], "description": "x",
                "source": "url-import", "source_url": "https://example.com/x.mp4",
            }],
        }
        errs = validate_catalog(v2)
        self.assertFalse(any("invalid source" in e.message for e in errs))
        self.assertFalse(any("source_url" in e.field for e in errs))

    def test_validator_requires_source_url_when_url_import(self):
        from lib.capture.validate_catalog import validate_catalog
        v2 = {
            "schema_version": 2,
            "assets": [{
                "id": "x", "filename": "x.mp4", "type": "video", "role": "broll",
                "linked_beats": ["beat-01"], "description": "x",
                "source": "url-import",  # missing source_url
            }],
        }
        errs = validate_catalog(v2)
        self.assertTrue(any(
            "source_url" in e.field and "required" in e.message for e in errs
        ))

    def test_validator_accepts_well_formed_enrichment(self):
        from lib.capture.validate_catalog import validate_catalog
        v2 = {
            "schema_version": 2,
            "assets": [{
                "id": "x", "filename": "x.png", "type": "image", "role": "support",
                "linked_beats": ["beat-01"], "description": "x",
                "enrichment": {
                    "status": "full",
                    "schema_version": 1,
                    "derived_at": "2026-04-10T12:00:00Z",
                    "derived_by": "lib.capture.enrich@1.0.0",
                    "aspect_ratio": "16:9",
                    "aspect_ratio_decimal": 1.778,
                    "focal_point": {"x": 50, "y": 50, "source": "center"},
                    "usable_display_modes": ["split-screen"],
                    "quality_flags": [],
                    "editorial_tags": [],
                },
            }],
        }
        errs = validate_catalog(v2)
        enrichment_errs = [e for e in errs if "enrichment" in e.field]
        self.assertEqual(enrichment_errs, [], f"unexpected enrichment errors: {enrichment_errs}")

    def test_validator_rejects_bad_enrichment_status(self):
        from lib.capture.validate_catalog import validate_catalog
        v2 = {
            "schema_version": 2,
            "assets": [{
                "id": "x", "filename": "x.png", "type": "image", "role": "support",
                "linked_beats": ["beat-01"], "description": "x",
                "enrichment": {
                    "status": "BOGUS",
                    "schema_version": 1,
                    "derived_at": "now",
                    "derived_by": "test",
                },
            }],
        }
        errs = validate_catalog(v2)
        self.assertTrue(any("invalid status" in e.message for e in errs))

    def test_validator_rejects_bad_focal_point_source(self):
        from lib.capture.validate_catalog import validate_catalog
        v2 = {
            "schema_version": 2,
            "assets": [{
                "id": "x", "filename": "x.png", "type": "image", "role": "support",
                "linked_beats": ["beat-01"], "description": "x",
                "enrichment": {
                    "status": "full",
                    "schema_version": 1,
                    "derived_at": "now",
                    "derived_by": "test",
                    "focal_point": {"x": 50, "y": 50, "source": "BOGUS"},
                },
            }],
        }
        errs = validate_catalog(v2)
        self.assertTrue(any("focal_point" in e.field for e in errs))

    def test_validator_rejects_bad_display_mode(self):
        from lib.capture.validate_catalog import validate_catalog
        v2 = {
            "schema_version": 2,
            "assets": [{
                "id": "x", "filename": "x.png", "type": "image", "role": "support",
                "linked_beats": ["beat-01"], "description": "x",
                "enrichment": {
                    "status": "full",
                    "schema_version": 1,
                    "derived_at": "now",
                    "derived_by": "test",
                    "usable_display_modes": ["split-screen", "BOGUS"],
                },
            }],
        }
        errs = validate_catalog(v2)
        self.assertTrue(any("usable_display_modes" in e.field for e in errs))

    def test_validator_omitted_enrichment_is_fine(self):
        """Old projects migrated to v2 without enrichment must still validate."""
        from lib.capture.validate_catalog import validate_catalog
        v2 = {
            "schema_version": 2,
            "assets": [{
                "id": "x", "filename": "x.png", "type": "image", "role": "support",
                "linked_beats": ["beat-01"], "description": "x",
            }],
        }
        errs = validate_catalog(v2)
        self.assertFalse(any("enrichment" in e.field for e in errs))


class TestCatalogMigration(unittest.TestCase):
    """lib.migrate.migrate_catalog — v1 → v2 catalog migration."""

    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.TemporaryDirectory()
        self.proj = Path(self.tmpdir.name) / "test-project"
        (self.proj / "assets").mkdir(parents=True)

    def tearDown(self):
        self.tmpdir.cleanup()

    def _write_catalog(self, data):
        with open(self.proj / "assets" / "catalog.json", "w") as f:
            json.dump(data, f, indent=2)

    def _read_catalog(self):
        with open(self.proj / "assets" / "catalog.json") as f:
            return json.load(f)

    def test_v1_catalog_gets_schema_version_stamped(self):
        from lib.migrate import migrate_catalog
        self._write_catalog({
            "assets": [{
                "id": "x", "filename": "x.png", "type": "image", "role": "support",
                "linked_beats": ["beat-01"], "description": "x", "source": "import",
            }]
        })
        out = migrate_catalog(self.proj, dry_run=False)
        data = self._read_catalog()
        self.assertEqual(data["schema_version"], 2)
        self.assertTrue(any("schema_version" in line for line in out))

    def test_url_source_normalized(self):
        from lib.migrate import migrate_catalog
        self._write_catalog({
            "assets": [{
                "id": "x", "filename": "x.mp4", "type": "video", "role": "broll",
                "linked_beats": ["beat-01"], "description": "x",
                "source": "https://example.com/foo.mp4",
            }]
        })
        out = migrate_catalog(self.proj, dry_run=False)
        data = self._read_catalog()
        asset = data["assets"][0]
        self.assertEqual(asset["source"], "url-import")
        self.assertEqual(asset["source_url"], "https://example.com/foo.mp4")
        self.assertEqual(data["schema_version"], 2)

    def test_dry_run_does_not_modify_file(self):
        from lib.migrate import migrate_catalog
        self._write_catalog({
            "assets": [{
                "id": "x", "filename": "x.png", "type": "image", "role": "support",
                "linked_beats": ["beat-01"], "description": "x",
            }]
        })
        out = migrate_catalog(self.proj, dry_run=True)
        data = self._read_catalog()
        self.assertNotIn("schema_version", data)
        self.assertTrue(any("WOULD" in line for line in out))

    def test_idempotent_on_v2(self):
        from lib.migrate import migrate_catalog
        self._write_catalog({
            "schema_version": 2,
            "assets": [{
                "id": "x", "filename": "x.png", "type": "image", "role": "support",
                "linked_beats": ["beat-01"], "description": "x", "source": "import",
            }],
        })
        out = migrate_catalog(self.proj, dry_run=False)
        self.assertTrue(any("OK:" in line for line in out))
        # File unchanged
        data = self._read_catalog()
        self.assertEqual(data["schema_version"], 2)

    def test_missing_catalog_skips_gracefully(self):
        from lib.migrate import migrate_catalog
        out = migrate_catalog(self.proj, dry_run=False)
        self.assertTrue(any("SKIP" in line for line in out))

    def test_migrated_catalog_validates(self):
        """End-to-end: v1 catalog → migrate → validate cleanly (no schema errors)."""
        from lib.migrate import migrate_catalog
        from lib.capture.validate_catalog import validate_catalog
        self._write_catalog({
            "assets": [{
                "id": "x", "filename": "x.mp4", "type": "video", "role": "broll",
                "linked_beats": ["beat-01"], "description": "x",
                "source": "https://example.com/x.mp4",
            }]
        })
        migrate_catalog(self.proj, dry_run=False)
        data = self._read_catalog()
        errs = validate_catalog(data)
        # Schema, role, source, source_url all good. The only possible remaining
        # error would be file-existence, which we don't check (no assets_dir).
        schema_errs = [e for e in errs if "schema_version" in e.field
                       or "role" in e.field or "source" in e.field]
        self.assertEqual(schema_errs, [], f"unexpected post-migration errors: {schema_errs}")


# ── Phase C: timeline schema additions (overlays + planning fields) ──────


class TestTimelineSchemaPhaseC(unittest.TestCase):
    """Drift detection between timeline.schema.json (post-Phase-C) and lib.grammar."""

    def _load(self) -> dict:
        path = Path(__file__).resolve().parent / "schemas" / "timeline.schema.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_overlays_lane_defined(self):
        data = self._load()
        self.assertIn("overlay_lane", data["$defs"])
        self.assertIn("overlays", data["properties"]["lanes"]["properties"])

    def test_visual_lane_has_planning_fields(self):
        data = self._load()
        props = data["$defs"]["visual_lane"]["items"]["properties"]
        for field in (
            "template_id",
            "proof_class",
            "avatar_mode",
            "splitRatio",
            "captionMode",
            "proof_protected",
        ):
            self.assertIn(field, props, f"timeline.schema visual_lane is missing {field}")

    def test_visual_lane_proof_class_enum_matches_grammar(self):
        from lib.grammar import PROOF_ORDER
        data = self._load()
        proof_enum = set(
            data["$defs"]["visual_lane"]["items"]["properties"]["proof_class"]["enum"]
        )
        self.assertEqual(
            proof_enum, set(PROOF_ORDER),
            "timeline.schema proof_class enum drifted from grammar.PROOF_ORDER",
        )

    def test_visual_lane_caption_mode_enum_matches_grammar(self):
        from lib.grammar import VALID_CAPTION_MODES
        data = self._load()
        cm_enum = set(
            data["$defs"]["visual_lane"]["items"]["properties"]["captionMode"]["enum"]
        )
        self.assertEqual(
            cm_enum, set(VALID_CAPTION_MODES),
            "timeline.schema captionMode enum drifted from grammar.VALID_CAPTION_MODES",
        )

    def test_overlay_lane_required_fields(self):
        data = self._load()
        required = set(data["$defs"]["overlay_lane"]["items"]["required"])
        self.assertEqual(required, {"type", "start", "end"})

    def test_visual_lane_has_render_hint_fields(self):
        """display, playbackRate, clipStartTime, zoom_moments, loop, volume should be schema'd."""
        data = self._load()
        props = data["$defs"]["visual_lane"]["items"]["properties"]
        for field in ("display", "playbackRate", "clipStartTime", "zoom_moments", "loop", "volume"):
            self.assertIn(field, props, f"timeline.schema visual_lane is missing render hint {field}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
