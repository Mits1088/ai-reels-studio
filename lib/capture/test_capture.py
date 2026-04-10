"""
Tests for demo capture and asset registration.

Run: python -m pytest lib/capture/test_capture.py -v
  or: python lib/capture/test_capture.py
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lib.capture.catalog import (
    Catalog, AssetEntry, load_catalog, save_catalog,
)
from lib.capture.register import (
    register_asset, register_demo, finalize_assets,
    make_asset_id, RegisterError, ASSET_ID_RE,
)
from lib.capture.validate_catalog import validate_catalog


# ── Helpers ──────────────────────────────────────────────────────────────────

BEAT_IDS = {"beat-01", "beat-02", "beat-03", "beat-04", "beat-05", "beat-06"}


def _make_project(tmpdir: Path) -> Path:
    """Create a minimal project directory with beat-map."""
    proj = tmpdir / "projects" / "test-reel"
    (proj / "audio").mkdir(parents=True)
    (proj / "assets").mkdir(parents=True)
    (proj / "output").mkdir(parents=True)

    # project.json
    with open(proj / "project.json", "w") as f:
        json.dump({
            "slug": "test-reel", "title": "Test", "brand": None, "template": None,
            "phase": "voice", "status": "voice_ready",
            "created": "2026-03-19T10:00:00Z", "updated": "2026-03-19T10:00:00Z",
            "voice_file": "audio/voice.wav", "duration_s": 12.5,
        }, f)

    # beat-map.json with 6 beats
    with open(proj / "audio" / "beat-map.json", "w") as f:
        json.dump({
            "total_duration": 12.5,
            "beats": [
                {"id": f"beat-{i:02d}", "scene": (i - 1) // 2 + 1, "phrase": f"phrase {i}",
                 "start": (i - 1) * 2.0, "end": i * 2.0,
                 "words": [{"word": f"w{i}", "start": (i - 1) * 2.0, "end": i * 2.0}],
                 "visual_intent": "", "asset_refs": []}
                for i in range(1, 7)
            ],
        }, f)

    return proj


def _make_dummy_file(tmpdir: Path, name: str, size: int = 100) -> Path:
    """Create a dummy file for testing."""
    p = tmpdir / name
    p.write_bytes(b"\x00" * size)
    return p


# ── Catalog model tests ─────────────────────────────────────────────────────

class TestCatalogModel(unittest.TestCase):

    def test_empty_catalog(self):
        cat = Catalog()
        self.assertEqual(len(cat.assets), 0)
        self.assertEqual(cat.to_dict(), {"assets": []})

    def test_add_and_get(self):
        entry = AssetEntry(
            id="demo_click_beat-03", filename="demo_click_beat-03.mp4",
            type="video", role="demo", linked_beats=["beat-03"],
            description="Deploy button click",
        )
        cat = Catalog(assets=[entry])
        self.assertEqual(cat.get("demo_click_beat-03"), entry)
        self.assertIsNone(cat.get("nonexistent"))

    def test_ids_and_filenames(self):
        entries = [
            AssetEntry(id="a", filename="a.png", type="image", role="support",
                       linked_beats=["beat-01"], description="Test"),
            AssetEntry(id="b", filename="b.mp4", type="video", role="demo",
                       linked_beats=["beat-02"], description="Test"),
        ]
        cat = Catalog(assets=entries)
        self.assertEqual(cat.ids(), {"a", "b"})
        self.assertEqual(cat.filenames(), {"a.png", "b.mp4"})

    def test_by_role_and_beat(self):
        entries = [
            AssetEntry(id="a", filename="a.mp4", type="video", role="demo",
                       linked_beats=["beat-01", "beat-02"], description="D"),
            AssetEntry(id="b", filename="b.png", type="image", role="support",
                       linked_beats=["beat-02"], description="S"),
        ]
        cat = Catalog(assets=entries)
        self.assertEqual(len(cat.by_role("demo")), 1)
        self.assertEqual(len(cat.by_beat("beat-02")), 2)
        self.assertEqual(len(cat.by_beat("beat-03")), 0)

    def test_save_and_load_roundtrip(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            entry = AssetEntry(
                id="test", filename="test.png", type="image", role="support",
                linked_beats=["beat-01"], description="Desc", dimensions={"w": 100, "h": 200},
            )
            cat = Catalog(assets=[entry])
            path = tmpdir / "catalog.json"
            save_catalog(cat, path)

            loaded = load_catalog(path)
            self.assertEqual(len(loaded.assets), 1)
            self.assertEqual(loaded.assets[0].id, "test")
            self.assertEqual(loaded.assets[0].dimensions, {"w": 100, "h": 200})
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ── Naming tests ─────────────────────────────────────────────────────────────

class TestNaming(unittest.TestCase):

    def test_basic_naming(self):
        aid = make_asset_id("demo", "deploy button click", ["beat-03"])
        self.assertTrue(ASSET_ID_RE.match(aid), f"Invalid ID: {aid}")
        self.assertIn("demo", aid)
        self.assertIn("beat-", aid)

    def test_multi_beat_naming(self):
        aid = make_asset_id("avatar", "talking head", ["beat-01", "beat-04"])
        self.assertIn("01", aid)
        self.assertIn("04", aid)

    def test_many_beat_naming(self):
        aid = make_asset_id("music", "background music", ["beat-01", "beat-02", "beat-03", "beat-04"])
        self.assertIn("to", aid)  # range notation

    def test_special_chars_cleaned(self):
        aid = make_asset_id("support", "Success! Animation #1", ["beat-04"])
        self.assertTrue(ASSET_ID_RE.match(aid), f"Invalid ID: {aid}")
        self.assertNotIn("!", aid)
        self.assertNotIn("#", aid)


# ── Registration tests ───────────────────────────────────────────────────────

class TestRegistration(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.project = _make_project(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_register_image(self):
        src = _make_dummy_file(self.tmpdir, "screenshot.png")
        entry = register_asset(
            src, self.project,
            asset_type="image", role="support",
            linked_beats=["beat-01"],
            description="Landing page screenshot",
        )
        self.assertIn("beat-", entry.id)
        self.assertTrue((self.project / "assets" / entry.filename).exists())

        # Catalog was written
        cat = load_catalog(self.project / "assets" / "catalog.json")
        self.assertEqual(len(cat.assets), 1)

    def test_register_demo(self):
        src = _make_dummy_file(self.tmpdir, "recording.mp4")
        entry = register_demo(
            src, self.project,
            linked_beats=["beat-03"],
            description="Deploy button click",
        )
        self.assertEqual(entry.type, "video")
        self.assertEqual(entry.role, "demo")
        self.assertEqual(entry.source, "capture")

    def test_register_multiple_assets(self):
        for i, name in enumerate(["a.png", "b.mp4", "c.mp3"]):
            src = _make_dummy_file(self.tmpdir, name)
            types = {"png": "image", "mp4": "video", "mp3": "sfx"}
            roles = {"png": "support", "mp4": "demo", "mp3": "sfx"}
            ext = name.split(".")[-1]
            register_asset(
                src, self.project,
                asset_type=types[ext], role=roles[ext],
                linked_beats=[f"beat-{i + 1:02d}"],
                description=f"Asset {i + 1}",
            )

        cat = load_catalog(self.project / "assets" / "catalog.json")
        self.assertEqual(len(cat.assets), 3)
        self.assertEqual(len(cat.ids()), 3)  # all unique

    def test_reject_missing_file(self):
        with self.assertRaises(RegisterError) as ctx:
            register_asset(
                Path("nonexistent.png"), self.project,
                asset_type="image", role="support",
                linked_beats=["beat-01"], description="Test",
            )
        self.assertIn("not found", str(ctx.exception))

    def test_reject_unsupported_extension(self):
        src = _make_dummy_file(self.tmpdir, "document.pdf")
        with self.assertRaises(RegisterError) as ctx:
            register_asset(
                src, self.project,
                asset_type="image", role="support",
                linked_beats=["beat-01"], description="Test",
            )
        self.assertIn("Unsupported", str(ctx.exception))

    def test_reject_no_linked_beats(self):
        src = _make_dummy_file(self.tmpdir, "orphan.png")
        with self.assertRaises(RegisterError) as ctx:
            register_asset(
                src, self.project,
                asset_type="image", role="support",
                linked_beats=[],
                description="Orphan image",
            )
        self.assertIn("orphan", str(ctx.exception).lower())

    def test_reject_empty_description(self):
        src = _make_dummy_file(self.tmpdir, "img.png")
        with self.assertRaises(RegisterError) as ctx:
            register_asset(
                src, self.project,
                asset_type="image", role="support",
                linked_beats=["beat-01"], description="  ",
            )
        self.assertIn("description", str(ctx.exception))

    def test_reject_duplicate_id(self):
        src = _make_dummy_file(self.tmpdir, "img.png")
        register_asset(
            src, self.project,
            asset_type="image", role="support",
            linked_beats=["beat-01"], description="First",
            asset_id="my-asset",
        )
        src2 = _make_dummy_file(self.tmpdir, "img2.png")
        with self.assertRaises(RegisterError) as ctx:
            register_asset(
                src2, self.project,
                asset_type="image", role="support",
                linked_beats=["beat-02"], description="Second",
                asset_id="my-asset",
            )
        self.assertIn("already exists", str(ctx.exception))

    def test_reject_invalid_type(self):
        src = _make_dummy_file(self.tmpdir, "img.png")
        with self.assertRaises(RegisterError):
            register_asset(
                src, self.project,
                asset_type="hologram", role="support",
                linked_beats=["beat-01"], description="Test",
            )

    def test_reject_invalid_role(self):
        src = _make_dummy_file(self.tmpdir, "img.png")
        with self.assertRaises(RegisterError):
            register_asset(
                src, self.project,
                asset_type="image", role="hero-shot",
                linked_beats=["beat-01"], description="Test",
            )

    def test_custom_id(self):
        src = _make_dummy_file(self.tmpdir, "logo.png")
        entry = register_asset(
            src, self.project,
            asset_type="logo", role="support",
            linked_beats=["beat-01"], description="Brand logo",
            asset_id="brand-logo-v1",
        )
        self.assertEqual(entry.id, "brand-logo-v1")
        self.assertEqual(entry.filename, "brand-logo-v1.png")

    def test_image_gets_dimensions(self):
        # Create a real 1x1 PNG using Pillow (available in this env)
        from PIL import Image
        src = self.tmpdir / "real.png"
        Image.new("RGB", (1080, 1920), "red").save(src)

        entry = register_asset(
            src, self.project,
            asset_type="image", role="support",
            linked_beats=["beat-01"], description="Red background",
        )
        self.assertEqual(entry.dimensions, {"w": 1080, "h": 1920})


# ── Validation tests ─────────────────────────────────────────────────────────

class TestCatalogValidation(unittest.TestCase):

    def _valid_entry(self, **overrides) -> dict:
        base = {
            "id": "demo_click_beat-03",
            "filename": "demo_click_beat-03.mp4",
            "type": "video",
            "role": "demo",
            "linked_beats": ["beat-03"],
            "description": "Deploy button click recording",
            "source": "capture",
        }
        base.update(overrides)
        return base

    def test_valid_catalog_passes(self):
        data = {"assets": [self._valid_entry()]}
        errs = validate_catalog(data, beat_ids=BEAT_IDS)
        self.assertEqual(errs, [])

    def test_empty_catalog(self):
        errs = validate_catalog({"assets": []})
        self.assertTrue(any("empty" in e.message for e in errs))

    def test_missing_required_field(self):
        for field in ("id", "filename", "type", "role", "linked_beats", "description"):
            entry = self._valid_entry()
            del entry[field]
            errs = validate_catalog({"assets": [entry]})
            self.assertTrue(any(field in e.field for e in errs),
                            f"Should catch missing {field}")

    def test_duplicate_id(self):
        errs = validate_catalog({"assets": [self._valid_entry(), self._valid_entry()]})
        self.assertTrue(any("duplicate" in e.message for e in errs))

    def test_duplicate_filename(self):
        e1 = self._valid_entry(id="a")
        e2 = self._valid_entry(id="b")  # same filename
        errs = validate_catalog({"assets": [e1, e2]})
        self.assertTrue(any("duplicate filename" in e.message for e in errs))

    def test_no_linked_beats(self):
        entry = self._valid_entry(linked_beats=[])
        errs = validate_catalog({"assets": [entry]})
        self.assertTrue(any("no linked beats" in e.message for e in errs))

    def test_nonexistent_beat_reference(self):
        entry = self._valid_entry(linked_beats=["beat-99"])
        errs = validate_catalog({"assets": [entry]}, beat_ids=BEAT_IDS)
        self.assertTrue(any("nonexistent beat" in e.message for e in errs))

    def test_invalid_type(self):
        entry = self._valid_entry(type="hologram")
        errs = validate_catalog({"assets": [entry]})
        self.assertTrue(any("invalid type" in e.message for e in errs))

    def test_extension_mismatch(self):
        entry = self._valid_entry(type="image", filename="test.mp4")
        errs = validate_catalog({"assets": [entry]})
        self.assertTrue(any("extension" in e.message for e in errs))

    def test_empty_description(self):
        entry = self._valid_entry(description="")
        errs = validate_catalog({"assets": [entry]})
        self.assertTrue(any("description" in e.message for e in errs))

    def test_missing_file_on_disk(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            (tmpdir / "assets").mkdir()
            entry = self._valid_entry()
            errs = validate_catalog({"assets": [entry]}, assets_dir=tmpdir / "assets")
            self.assertTrue(any("not found on disk" in e.message for e in errs))
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_orphan_file_detected(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            assets_dir = tmpdir / "assets"
            assets_dir.mkdir()
            # Create a file not in the catalog
            (assets_dir / "stray-file.png").write_bytes(b"\x00")
            # Valid catalog with different file
            entry = self._valid_entry(filename="demo_click_beat-03.mp4")
            (assets_dir / "demo_click_beat-03.mp4").write_bytes(b"\x00")
            errs = validate_catalog({"assets": [entry]}, assets_dir=assets_dir)
            self.assertTrue(any("orphan" in e.message.lower() or "not in the catalog" in e.message for e in errs))
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ── Finalize tests ───────────────────────────────────────────────────────────

class TestFinalize(unittest.TestCase):

    def test_finalize_updates_project(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            proj = _make_project(tmpdir)
            finalize_assets(proj)

            with open(proj / "project.json") as f:
                data = json.load(f)
            self.assertEqual(data["phase"], "assets")
            self.assertEqual(data["status"], "assets_ready")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ── End-to-end: registration + validation ────────────────────────────────────

class TestEndToEnd(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.project = _make_project(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_register_then_validate(self):
        # Register several assets
        from PIL import Image

        # 1. Demo recording
        vid = _make_dummy_file(self.tmpdir, "deploy-recording.mp4")
        register_demo(
            vid, self.project,
            linked_beats=["beat-03", "beat-04"],
            description="Screen recording of deploy flow",
            scene=2,
        )

        # 2. Support image
        img_path = self.tmpdir / "success-screen.png"
        Image.new("RGB", (1080, 1920), "green").save(img_path)
        register_asset(
            img_path, self.project,
            asset_type="image", role="support",
            linked_beats=["beat-05"],
            description="Success confirmation screen",
        )

        # 3. Logo
        logo_path = self.tmpdir / "logo.png"
        Image.new("RGBA", (200, 200), "blue").save(logo_path)
        register_asset(
            logo_path, self.project,
            asset_type="logo", role="support",
            linked_beats=["beat-01", "beat-06"],
            description="Brand logo watermark",
            source="brand-kit",
        )

        # Validate
        cat = load_catalog(self.project / "assets" / "catalog.json")
        errs = validate_catalog(
            cat,
            assets_dir=self.project / "assets",
            beat_ids=BEAT_IDS,
        )
        self.assertEqual(errs, [], f"Validation errors: {errs}")
        self.assertEqual(len(cat.assets), 3)

        # Check image got dimensions
        logo = cat.get(cat.assets[2].id)
        self.assertEqual(logo.dimensions, {"w": 200, "h": 200})

    def test_full_workflow_with_finalize(self):
        # Register one asset
        src = _make_dummy_file(self.tmpdir, "clip.mp4")
        register_demo(
            src, self.project,
            linked_beats=["beat-03"],
            description="Demo clip",
        )

        # Finalize
        finalize_assets(self.project)

        with open(self.project / "project.json") as f:
            proj = json.load(f)
        self.assertEqual(proj["status"], "assets_ready")


if __name__ == "__main__":
    unittest.main(verbosity=2)
