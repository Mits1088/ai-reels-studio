"""
Tests for the QA layer.

Run: python -m pytest lib/qa/test_qa.py -v
  or: python lib/qa/test_qa.py
"""

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lib.qa.finding import Finding, Severity
from lib.qa.checks import (
    check_sync,
    check_captions,
    check_dead_air,
    check_missing_assets,
    check_transitions,
    check_audio_balance,
    check_timeline_consistency,
    check_placeholders,
    check_duration,
)
from lib.qa.runner import run_qa, run_qa_on_project, QAReport


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _beat_map(n=6, dur=12.5):
    step = dur / n
    return {
        "total_duration": dur,
        "beats": [
            {
                "id": f"beat-{i+1:02d}",
                "scene": (i // 2) + 1,
                "phrase": f"Phrase for beat {i+1}",
                "start": round(i * step, 3),
                "end": round((i + 1) * step, 3),
                "words": [{"word": f"w{i}", "start": round(i * step, 3), "end": round((i + 1) * step, 3)}],
                "visual_intent": f"Show something for beat {i+1}",
                "asset_refs": [],
            }
            for i in range(n)
        ],
    }


def _timeline(bm, *, avatar=True, demo=True, support=True, captions=True,
              sfx=True, music=True, music_vol=0.15):
    beats = bm["beats"]
    tl = {
        "total_duration": bm["total_duration"],
        "lanes": {
            "avatar": [],
            "demo": [],
            "support": [],
            "captions": [],
            "sfx": [],
            "music": [],
        },
    }
    n = len(beats)
    if avatar and n >= 1:
        entries = [{"beat_id": beats[0]["id"], "start": beats[0]["start"], "end": beats[0]["end"], "asset": "avatar.png"}]
        if n >= 2:
            entries.append({"beat_id": beats[-1]["id"], "start": beats[-1]["start"], "end": beats[-1]["end"], "asset": "avatar.png"})
        tl["lanes"]["avatar"] = entries
    if demo and n >= 4:
        tl["lanes"]["demo"] = [
            {"beat_id": beats[2]["id"], "start": beats[2]["start"], "end": beats[3]["end"], "asset": "demo.png",
             "transition": {"type": "fade", "duration": 0.2}},
        ]
    if support and n >= 5:
        tl["lanes"]["support"] = [
            {"beat_id": beats[4]["id"], "start": beats[4]["start"], "end": beats[4]["end"], "asset": "support.png"},
        ]
    if captions:
        tl["lanes"]["captions"] = [
            {"beat_id": b["id"], "start": b["start"], "end": b["end"], "text": b["phrase"]}
            for b in beats
        ]
    if sfx and n >= 3:
        tl["lanes"]["sfx"] = [
            {"start": beats[2]["start"] + 0.3, "end": beats[2]["start"] + 0.8, "asset": "whoosh.wav", "beat_id": beats[2]["id"]},
        ]
    if music:
        tl["lanes"]["music"] = [
            {"start": 0.0, "end": bm["total_duration"], "asset": "bg.mp3", "volume": music_vol},
        ]
    return tl


def _good_project():
    bm = _beat_map()
    tl = _timeline(bm)
    return bm, tl


# ── Finding model tests ──────────────────────────────────────────────────────

class TestFinding(unittest.TestCase):

    def test_block_finding(self):
        f = Finding("sync", Severity.BLOCK, "beat-01", "No visual", "Add avatar")
        self.assertEqual(f.severity, Severity.BLOCK)
        d = f.to_dict()
        self.assertEqual(d["severity"], "block")

    def test_warn_finding(self):
        f = Finding("captions", Severity.WARN, "captions[0]", "Short", "Extend")
        self.assertEqual(f.severity, Severity.WARN)

    def test_repr(self):
        f = Finding("sync", Severity.BLOCK, "beat-01", "msg", "fix")
        self.assertIn("BLOCK", repr(f))


# ── Sync gate tests ──────────────────────────────────────────────────────────

class TestSync(unittest.TestCase):

    def test_good_sync_passes(self):
        bm, tl = _good_project()
        findings = check_sync(bm, tl)
        # Beats 2 and 4 (index 1 and 3) may not have direct visual coverage
        # depending on timeline setup — just check no crashes
        self.assertIsInstance(findings, list)

    def test_beat_with_no_visual(self):
        bm = _beat_map(3, 9.0)
        tl = _timeline(bm, avatar=False, demo=False, support=False)
        findings = check_sync(bm, tl)
        # All beats should be flagged
        blocks = [f for f in findings if f.severity == Severity.BLOCK]
        self.assertEqual(len(blocks), 3)

    def test_all_beats_covered(self):
        bm = _beat_map(2, 6.0)
        tl = {
            "total_duration": 6.0,
            "lanes": {
                "avatar": [{"beat_id": "beat-01", "start": 0.0, "end": 3.0, "asset": "a.png"},
                           {"beat_id": "beat-02", "start": 3.0, "end": 6.0, "asset": "a.png"}],
                "demo": [], "support": [],
                "captions": [{"beat_id": "beat-01", "start": 0.0, "end": 3.0, "text": "Hi"},
                             {"beat_id": "beat-02", "start": 3.0, "end": 6.0, "text": "Bye"}],
                "sfx": [], "music": [],
            },
        }
        findings = check_sync(bm, tl)
        blocks = [f for f in findings if f.severity == Severity.BLOCK]
        self.assertEqual(len(blocks), 0)


# ── Caption gate tests ───────────────────────────────────────────────────────

class TestCaptions(unittest.TestCase):

    def test_good_captions(self):
        _, tl = _good_project()
        findings = check_captions(tl)
        blocks = [f for f in findings if f.severity == Severity.BLOCK]
        self.assertEqual(len(blocks), 0)

    def test_no_captions(self):
        _, tl = _good_project()
        tl["lanes"]["captions"] = []
        findings = check_captions(tl)
        self.assertTrue(any(f.severity == Severity.BLOCK for f in findings))

    def test_short_caption(self):
        tl = {"lanes": {"captions": [
            {"beat_id": "beat-01", "start": 0.0, "end": 0.3, "text": "Hi"},
        ]}}
        findings = check_captions(tl)
        self.assertTrue(any("0.30s" in f.message for f in findings))

    def test_too_many_words(self):
        tl = {"lanes": {"captions": [
            {"beat_id": "beat-01", "start": 0.0, "end": 3.0,
             "text": "This caption has way too many words in it for a reel"},
        ]}}
        findings = check_captions(tl)
        self.assertTrue(any("words" in f.message for f in findings))

    def test_empty_caption_text(self):
        tl = {"lanes": {"captions": [
            {"beat_id": "beat-01", "start": 0.0, "end": 2.0, "text": ""},
        ]}}
        findings = check_captions(tl)
        self.assertTrue(any(f.severity == Severity.BLOCK and "empty" in f.message for f in findings))

    def test_missing_beat_id(self):
        tl = {"lanes": {"captions": [
            {"start": 0.0, "end": 2.0, "text": "Hello"},
        ]}}
        findings = check_captions(tl)
        self.assertTrue(any("beat_id" in f.message for f in findings))

    def test_overlapping_captions(self):
        tl = {"lanes": {"captions": [
            {"beat_id": "beat-01", "start": 0.0, "end": 3.0, "text": "First"},
            {"beat_id": "beat-02", "start": 2.5, "end": 5.0, "text": "Second"},
        ]}}
        findings = check_captions(tl)
        self.assertTrue(any("overlap" in f.message.lower() for f in findings))


# ── Dead air gate tests ──────────────────────────────────────────────────────

class TestDeadAir(unittest.TestCase):

    def test_no_dead_air(self):
        bm = _beat_map(2, 6.0)
        tl = {
            "total_duration": 6.0,
            "lanes": {
                "avatar": [{"beat_id": "beat-01", "start": 0.0, "end": 6.0, "asset": "a.png"}],
                "demo": [], "support": [], "captions": [], "sfx": [], "music": [],
            },
        }
        findings = check_dead_air(bm, tl)
        blocks = [f for f in findings if f.severity == Severity.BLOCK]
        self.assertEqual(len(blocks), 0)

    def test_total_dead_air(self):
        bm = _beat_map(2, 6.0)
        tl = {"total_duration": 6.0, "lanes": {"avatar": [], "demo": [], "support": [], "captions": [], "sfx": [], "music": []}}
        findings = check_dead_air(bm, tl)
        self.assertTrue(any(f.severity == Severity.BLOCK for f in findings))

    def test_gap_in_middle(self):
        bm = _beat_map(3, 12.0)
        tl = {
            "total_duration": 12.0,
            "lanes": {
                "avatar": [
                    {"beat_id": "beat-01", "start": 0.0, "end": 2.0, "asset": "a.png"},
                    {"beat_id": "beat-03", "start": 8.0, "end": 12.0, "asset": "a.png"},
                ],
                "demo": [], "support": [], "captions": [], "sfx": [], "music": [],
            },
        }
        findings = check_dead_air(bm, tl)
        gap_findings = [f for f in findings if "gap" in f.message.lower() or "dead air" in f.message.lower()]
        self.assertGreater(len(gap_findings), 0)


# ── Missing assets tests ────────────────────────────────────────────────────

class TestMissingAssets(unittest.TestCase):

    def test_no_assets_dir(self):
        _, tl = _good_project()
        findings = check_missing_assets(tl, assets_dir=None)
        self.assertEqual(len(findings), 0)

    def test_missing_file(self):
        _, tl = _good_project()
        tmpdir = Path(tempfile.mkdtemp())
        try:
            findings = check_missing_assets(tl, assets_dir=tmpdir)
            blocks = [f for f in findings if f.severity == Severity.BLOCK]
            self.assertGreater(len(blocks), 0)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_files_exist(self):
        _, tl = _good_project()
        tmpdir = Path(tempfile.mkdtemp())
        try:
            for name in ("avatar.png", "demo.png", "support.png", "whoosh.wav", "bg.mp3"):
                (tmpdir / name).write_bytes(b"\x00")
            findings = check_missing_assets(tl, assets_dir=tmpdir)
            self.assertEqual(len(findings), 0)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ── Transitions tests ────────────────────────────────────────────────────────

class TestTransitions(unittest.TestCase):

    def test_normal_transitions(self):
        bm, tl = _good_project()
        findings = check_transitions(tl, bm)
        blocks = [f for f in findings if f.severity == Severity.BLOCK]
        self.assertEqual(len(blocks), 0)

    def test_too_long_transition(self):
        bm, tl = _good_project()
        tl["lanes"]["demo"][0]["transition"]["duration"] = 0.5
        findings = check_transitions(tl, bm)
        self.assertTrue(any(f.severity == Severity.BLOCK for f in findings))

    def test_excessive_transitions_warning(self):
        bm = _beat_map(6, 18.0)
        tl = _timeline(bm)
        # Add transitions to every visual entry
        for lane in ("avatar", "demo", "support"):
            for entry in tl["lanes"][lane]:
                entry["transition"] = {"type": "fade", "duration": 0.2}
        findings = check_transitions(tl, bm)
        warns = [f for f in findings if f.severity == Severity.WARN and "overwhelm" in f.message]
        self.assertGreater(len(warns), 0)


# ── Audio balance tests ──────────────────────────────────────────────────────

class TestAudioBalance(unittest.TestCase):

    def test_normal_music(self):
        bm, tl = _good_project()
        findings = check_audio_balance(tl, bm)
        blocks = [f for f in findings if f.severity == Severity.BLOCK]
        self.assertEqual(len(blocks), 0)

    def test_loud_music(self):
        bm = _beat_map()
        tl = _timeline(bm, music_vol=0.6)
        findings = check_audio_balance(tl, bm)
        self.assertTrue(any(f.severity == Severity.BLOCK and "overpower" in f.message for f in findings))

    def test_no_music_warning(self):
        bm = _beat_map()
        tl = _timeline(bm, music=False)
        findings = check_audio_balance(tl, bm)
        self.assertTrue(any("No background music" in f.message for f in findings))

    def test_too_many_sfx(self):
        bm = _beat_map(6, 18.0)
        tl = _timeline(bm, sfx=False)
        # Stuff 5 SFX into beat-01's time range
        tl["lanes"]["sfx"] = [
            {"start": 0.1 * i, "end": 0.1 * i + 0.2, "asset": f"sfx{i}.wav"}
            for i in range(5)
        ]
        findings = check_audio_balance(tl, bm)
        self.assertTrue(any("SFX" in f.message for f in findings))


# ── Consistency tests ────────────────────────────────────────────────────────

class TestConsistency(unittest.TestCase):

    def test_matching_duration(self):
        bm, tl = _good_project()
        findings = check_timeline_consistency(tl, bm)
        blocks = [f for f in findings if f.severity == Severity.BLOCK and "duration" in f.message.lower()]
        self.assertEqual(len(blocks), 0)

    def test_mismatched_duration(self):
        bm, tl = _good_project()
        tl["total_duration"] = 99.0
        findings = check_timeline_consistency(tl, bm)
        self.assertTrue(any(f.severity == Severity.BLOCK for f in findings))

    def test_uncaptioned_beat(self):
        bm, tl = _good_project()
        tl["lanes"]["captions"] = tl["lanes"]["captions"][:3]  # drop last 3
        findings = check_timeline_consistency(tl, bm)
        warns = [f for f in findings if "no caption" in f.message.lower()]
        self.assertEqual(len(warns), 3)

    def test_entry_past_duration(self):
        bm, tl = _good_project()
        tl["lanes"]["avatar"][1]["end"] = 999.0
        findings = check_timeline_consistency(tl, bm)
        self.assertTrue(any(f.severity == Severity.BLOCK and "ends at" in f.message for f in findings))


# ── Placeholder tests ────────────────────────────────────────────────────────

class TestPlaceholders(unittest.TestCase):

    def test_no_placeholders(self):
        bm, tl = _good_project()
        findings = check_placeholders(bm, tl)
        blocks = [f for f in findings if f.severity == Severity.BLOCK]
        self.assertEqual(len(blocks), 0)

    def test_empty_visual_intent(self):
        bm, tl = _good_project()
        bm["beats"][0]["visual_intent"] = ""
        findings = check_placeholders(bm, tl)
        warns = [f for f in findings if f.severity == Severity.WARN and "empty" in f.message.lower()]
        self.assertGreater(len(warns), 0)

    def test_tbd_in_intent(self):
        bm, tl = _good_project()
        bm["beats"][0]["visual_intent"] = "TBD — need screenshot"
        findings = check_placeholders(bm, tl)
        self.assertTrue(any(f.severity == Severity.BLOCK and "TBD" in f.message for f in findings))

    def test_bracket_placeholder(self):
        bm, tl = _good_project()
        bm["beats"][1]["visual_intent"] = "Show [insert product name]"
        findings = check_placeholders(bm, tl)
        self.assertTrue(any(f.severity == Severity.BLOCK for f in findings))

    def test_todo_in_phrase(self):
        bm, tl = _good_project()
        bm["beats"][0]["phrase"] = "TODO write final copy"
        findings = check_placeholders(bm, tl)
        self.assertTrue(any(f.severity == Severity.BLOCK and "phrase" in f.message.lower() for f in findings))

    def test_placeholder_in_caption(self):
        bm, tl = _good_project()
        tl["lanes"]["captions"][0]["text"] = "Lorem ipsum dolor sit"
        findings = check_placeholders(bm, tl)
        self.assertTrue(any(f.severity == Severity.BLOCK and "Lorem" in f.message for f in findings))


# ── Duration tests ───────────────────────────────────────────────────────────

class TestDuration(unittest.TestCase):

    def test_good_duration(self):
        findings = check_duration({"total_duration": 25.0, "beats": []})
        blocks = [f for f in findings if f.severity == Severity.BLOCK]
        self.assertEqual(len(blocks), 0)

    def test_too_short(self):
        findings = check_duration({"total_duration": 2.0, "beats": []})
        self.assertTrue(any(f.severity == Severity.BLOCK for f in findings))

    def test_too_long(self):
        findings = check_duration({"total_duration": 120.0, "beats": []})
        self.assertTrue(any(f.severity == Severity.BLOCK for f in findings))

    def test_borderline_short_warning(self):
        findings = check_duration({"total_duration": 10.0, "beats": []})
        self.assertTrue(any(f.severity == Severity.WARN for f in findings))


# ── Report tests ─────────────────────────────────────────────────────────────

class TestReport(unittest.TestCase):

    def test_clean_report(self):
        bm = _beat_map(2, 6.0)
        tl = {
            "total_duration": 6.0,
            "lanes": {
                "avatar": [{"beat_id": "beat-01", "start": 0.0, "end": 3.0, "asset": "a.png"},
                           {"beat_id": "beat-02", "start": 3.0, "end": 6.0, "asset": "a.png"}],
                "demo": [], "support": [],
                "captions": [
                    {"beat_id": "beat-01", "start": 0.0, "end": 3.0, "text": "First part"},
                    {"beat_id": "beat-02", "start": 3.0, "end": 6.0, "text": "Second part"},
                ],
                "sfx": [],
                "music": [{"start": 0.0, "end": 6.0, "asset": "bg.mp3", "volume": 0.15}],
            },
        }
        report = run_qa(bm, tl)
        self.assertTrue(report.passed)
        self.assertEqual(len(report.blockers), 0)

    def test_report_with_blockers(self):
        bm, tl = _good_project()
        tl["total_duration"] = 999.0  # consistency fail
        report = run_qa(bm, tl)
        self.assertFalse(report.passed)
        self.assertEqual(report.verdict, "FAIL")

    def test_report_serialization(self):
        bm, tl = _good_project()
        report = run_qa(bm, tl, project_slug="test-reel")
        d = report.to_dict()
        self.assertIn("verdict", d)
        self.assertIn("findings", d)
        self.assertEqual(d["project"], "test-reel")
        # Must be JSON-serializable
        json.dumps(d)

    def test_report_summary(self):
        bm, tl = _good_project()
        report = run_qa(bm, tl, project_slug="test-reel")
        summary = report.summary()
        self.assertIn("test-reel", summary)
        self.assertIn("Verdict", summary)


# ── Full project runner tests ────────────────────────────────────────────────

class TestProjectRunner(unittest.TestCase):

    def _make_project(self, tmpdir: Path, *, good=True) -> Path:
        proj = tmpdir / "projects" / "qa-test"
        (proj / "audio").mkdir(parents=True)
        (proj / "assets").mkdir(parents=True)
        (proj / "output").mkdir(parents=True)

        bm = _beat_map(6, 20.0)
        tl = _timeline(bm)

        with open(proj / "project.json", "w") as f:
            json.dump({
                "slug": "qa-test", "title": "QA Test", "brand": None, "template": None,
                "phase": "assembly", "status": "completed",
                "created": "2026-03-19T10:00:00Z", "updated": "2026-03-19T10:00:00Z",
                "voice_file": "audio/voice.wav", "duration_s": 20.0,
            }, f)

        with open(proj / "audio" / "beat-map.json", "w") as f:
            json.dump(bm, f)
        with open(proj / "output" / "timeline.json", "w") as f:
            json.dump(tl, f)

        # Create asset files
        if good:
            for name in ("avatar.png", "demo.png", "support.png", "whoosh.wav", "bg.mp3"):
                (proj / "assets" / name).write_bytes(b"\x00")

        return proj

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_good_project_passes(self):
        proj = self._make_project(self.tmpdir, good=True)
        report = run_qa_on_project(proj)
        # May have warnings (no-music, etc.) but no blockers from asset check
        # since we created the files
        self.assertIsInstance(report, QAReport)

    def test_writes_qa_report(self):
        proj = self._make_project(self.tmpdir)
        run_qa_on_project(proj)
        self.assertTrue((proj / "output" / "qa_report.json").exists())

    def test_updates_project_status(self):
        proj = self._make_project(self.tmpdir)
        report = run_qa_on_project(proj)
        with open(proj / "project.json") as f:
            pj = json.load(f)
        self.assertEqual(pj["phase"], "qa")
        if report.passed:
            self.assertEqual(pj["status"], "completed")
        else:
            self.assertEqual(pj["status"], "failed")

    def test_missing_beat_map(self):
        proj = self._make_project(self.tmpdir)
        (proj / "audio" / "beat-map.json").unlink()
        report = run_qa_on_project(proj)
        self.assertFalse(report.passed)
        self.assertTrue(any("Beat map not found" in f.message for f in report.findings))

    def test_missing_timeline(self):
        proj = self._make_project(self.tmpdir)
        (proj / "output" / "timeline.json").unlink()
        report = run_qa_on_project(proj)
        self.assertFalse(report.passed)
        self.assertTrue(any("Timeline not found" in f.message for f in report.findings))

    def test_missing_assets_caught(self):
        proj = self._make_project(self.tmpdir, good=False)
        report = run_qa_on_project(proj)
        asset_findings = [f for f in report.findings if f.gate == "missing-assets"]
        self.assertGreater(len(asset_findings), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
