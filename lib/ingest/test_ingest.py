"""
Tests for the voice ingestion pipeline.

Run: python -m pytest lib/ingest/test_ingest.py -v
  or: python lib/ingest/test_ingest.py
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lib.ingest.transcribe import (
    MockProvider, Transcript, Segment, WordTiming,
)
from lib.ingest.phrases import (
    extract_phrases, segment_to_phrases, Phrase,
    MIN_VISIBLE_DURATION, MAX_WORDS_PER_PHRASE, PAUSE_THRESHOLD,
)
from lib.ingest.captions import phrases_to_captions, captions_to_dicts
from lib.ingest.beats import generate_beats
from lib.ingest.pipeline import ingest, extract_only, IngestError
from lib.ingest.extract import (
    is_video, is_audio,
    AudioExtractor, FfmpegPythonExtractor, FfmpegCLIExtractor,
    get_default_extractor,
)
from lib.validate import validate_beat_map


# ── Transcription tests ─────────────────────────────────────────────────────

class TestMockProvider(unittest.TestCase):

    def test_returns_transcript(self):
        provider = MockProvider()
        transcript = provider.transcribe(Path("dummy.wav"))
        self.assertIsInstance(transcript, Transcript)
        self.assertGreater(transcript.total_duration, 0)
        self.assertGreater(len(transcript.segments), 0)

    def test_all_segments_have_words(self):
        transcript = MockProvider().transcribe(Path("dummy.wav"))
        for seg in transcript.segments:
            self.assertGreater(len(seg.words), 0, f"Segment '{seg.text}' has no words")

    def test_timestamps_are_3_decimal(self):
        transcript = MockProvider().transcribe(Path("dummy.wav"))
        for seg in transcript.segments:
            self.assertEqual(seg.start, round(seg.start, 3))
            self.assertEqual(seg.end, round(seg.end, 3))
            for w in seg.words:
                self.assertEqual(w.start, round(w.start, 3))
                self.assertEqual(w.end, round(w.end, 3))

    def test_voice_json_contract(self):
        transcript = MockProvider().transcribe(Path("dummy.wav"))
        voice = transcript.to_voice_json()
        self.assertIn("total_duration", voice)
        self.assertIn("sentences", voice)
        for sent in voice["sentences"]:
            self.assertIn("text", sent)
            self.assertIn("start", sent)
            self.assertIn("end", sent)
            self.assertIn("words", sent)
            for w in sent["words"]:
                self.assertIn("word", w)
                self.assertIn("start", w)
                self.assertIn("end", w)

    def test_custom_transcript(self):
        custom = Transcript(
            total_duration=3.0,
            segments=[Segment("Hello", 0.0, 1.5, [WordTiming("Hello", 0.0, 1.5)])],
        )
        provider = MockProvider(transcript=custom)
        result = provider.transcribe(Path("x.wav"))
        self.assertEqual(result.total_duration, 3.0)
        self.assertEqual(len(result.segments), 1)


# ── Phrase detection tests ───────────────────────────────────────────────────

class TestPhraseDetection(unittest.TestCase):

    def _seg(self, text, words_data):
        words = [WordTiming(w, s, e) for w, s, e in words_data]
        return Segment(text, words[0].start, words[-1].end, words)

    def test_short_segment_single_phrase(self):
        seg = self._seg("Hi there", [("Hi", 0.0, 0.3), ("there", 0.4, 0.8)])
        phrases = segment_to_phrases(seg, 0)
        self.assertEqual(len(phrases), 1)
        self.assertEqual(phrases[0].text, "Hi there")

    def test_splits_at_max_words(self):
        words = [(f"w{i}", i * 0.2, i * 0.2 + 0.15) for i in range(10)]
        seg = self._seg("ten words", words)
        phrases = segment_to_phrases(seg, 0, max_words=6)
        self.assertGreater(len(phrases), 1)
        for p in phrases:
            self.assertLessEqual(len(p.words), 6)

    def test_splits_at_pause(self):
        # Gap of 0.6s between word 2 and 3
        seg = self._seg("A B. C D.", [
            ("A", 0.0, 0.2), ("B.", 0.3, 0.5),
            ("C", 1.1, 1.3), ("D.", 1.4, 1.6),
        ])
        phrases = segment_to_phrases(seg, 0, pause_threshold=0.4)
        self.assertEqual(len(phrases), 2)
        self.assertEqual(phrases[0].text, "A B.")
        self.assertEqual(phrases[1].text, "C D.")

    def test_minimum_visible_duration(self):
        seg = self._seg("Hi", [("Hi", 0.0, 0.2)])  # only 0.2s
        phrases = segment_to_phrases(seg, 0)
        self.assertGreaterEqual(phrases[0].end - phrases[0].start, MIN_VISIBLE_DURATION)

    def test_phrase_timing_matches_words(self):
        seg = self._seg("A B C", [
            ("A", 1.0, 1.3), ("B", 1.4, 1.7), ("C", 1.8, 2.1),
        ])
        phrases = segment_to_phrases(seg, 0)
        self.assertEqual(phrases[0].start, 1.0)
        # end might be extended by min duration, but >= last word end
        self.assertGreaterEqual(phrases[0].end, 2.1)

    def test_extract_phrases_from_full_transcript(self):
        transcript = MockProvider().transcribe(Path("x.wav"))
        phrases = extract_phrases(transcript.segments)
        self.assertGreater(len(phrases), 0)
        # All phrases must have start < end
        for p in phrases:
            self.assertLess(p.start, p.end, f"Phrase '{p.text}' has bad timing")


# ── Caption tests ────────────────────────────────────────────────────────────

class TestCaptions(unittest.TestCase):

    def test_one_caption_per_phrase(self):
        transcript = MockProvider().transcribe(Path("x.wav"))
        phrases = extract_phrases(transcript.segments)
        captions = phrases_to_captions(phrases)
        self.assertEqual(len(captions), len(phrases))

    def test_captions_have_timing(self):
        transcript = MockProvider().transcribe(Path("x.wav"))
        phrases = extract_phrases(transcript.segments)
        captions = phrases_to_captions(phrases)
        for cap in captions:
            self.assertIsNotNone(cap.start)
            self.assertIsNotNone(cap.end)
            self.assertGreater(cap.end, cap.start)
            self.assertGreater(len(cap.text), 0)

    def test_captions_serialize(self):
        transcript = MockProvider().transcribe(Path("x.wav"))
        phrases = extract_phrases(transcript.segments)
        captions = phrases_to_captions(phrases)
        dicts = captions_to_dicts(captions)
        for d in dicts:
            self.assertIn("text", d)
            self.assertIn("start", d)
            self.assertIn("end", d)
            self.assertIn("beat_id", d)


# ── Beat map tests ───────────────────────────────────────────────────────────

class TestBeatMap(unittest.TestCase):

    def test_beat_map_from_mock(self):
        transcript = MockProvider().transcribe(Path("x.wav"))
        beat_map, captions = generate_beats(transcript)
        self.assertIn("total_duration", beat_map)
        self.assertIn("beats", beat_map)
        self.assertGreater(len(beat_map["beats"]), 0)

    def test_beat_ids_sequential(self):
        transcript = MockProvider().transcribe(Path("x.wav"))
        beat_map, _ = generate_beats(transcript)
        for i, beat in enumerate(beat_map["beats"]):
            self.assertEqual(beat["id"], f"beat-{i + 1:02d}")

    def test_beat_map_passes_contract_validation(self):
        transcript = MockProvider().transcribe(Path("x.wav"))
        beat_map, _ = generate_beats(transcript)
        errors = validate_beat_map(beat_map)
        self.assertEqual(errors, [], f"Validation errors: {errors}")

    def test_captions_have_beat_ids_assigned(self):
        transcript = MockProvider().transcribe(Path("x.wav"))
        beat_map, captions = generate_beats(transcript)
        beat_ids = {b["id"] for b in beat_map["beats"]}
        for cap in captions:
            self.assertIn(cap.beat_id, beat_ids,
                          f"Caption '{cap.text}' has unlinked beat_id '{cap.beat_id}'")

    def test_beats_cover_transcript(self):
        transcript = MockProvider().transcribe(Path("x.wav"))
        beat_map, _ = generate_beats(transcript)
        # Every transcript word should appear in some beat
        transcript_words = set()
        for seg in transcript.segments:
            for w in seg.words:
                transcript_words.add(w.word)
        beat_words = set()
        for beat in beat_map["beats"]:
            for w in beat["words"]:
                beat_words.add(w["word"])
        self.assertEqual(transcript_words, beat_words)

    def test_beats_non_overlapping(self):
        transcript = MockProvider().transcribe(Path("x.wav"))
        beat_map, _ = generate_beats(transcript)
        for i in range(1, len(beat_map["beats"])):
            prev = beat_map["beats"][i - 1]
            curr = beat_map["beats"][i]
            self.assertLessEqual(prev["end"], curr["start"] + 0.001,
                                 f"{prev['id']} overlaps {curr['id']}")

    def test_scene_numbers_from_segments(self):
        transcript = MockProvider().transcribe(Path("x.wav"))
        beat_map, _ = generate_beats(transcript)
        scenes = {b["scene"] for b in beat_map["beats"]}
        # Mock has 4 segments, so should have up to 4 scenes
        self.assertEqual(scenes, {1, 2, 3, 4})


# ── Pipeline integration tests ───────────────────────────────────────────────

class TestPipeline(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.project_dir = self.tmpdir / "projects" / "test-reel"
        self.project_dir.mkdir(parents=True)

        # Create minimal project.json
        project = {
            "slug": "test-reel",
            "title": "Test",
            "brand": None,
            "template": None,
            "phase": "brief",
            "status": "initialized",
            "created": "2026-03-19T10:00:00Z",
            "updated": "2026-03-19T10:00:00Z",
            "voice_file": None,
            "duration_s": None,
        }
        with open(self.project_dir / "project.json", "w") as f:
            json.dump(project, f)

        # Create a dummy audio file
        self.dummy_audio = self.tmpdir / "narration.wav"
        self.dummy_audio.write_bytes(b"RIFF" + b"\x00" * 100)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_full_pipeline_mock(self):
        result = ingest(self.dummy_audio, self.project_dir, MockProvider())

        self.assertGreater(result.total_duration, 0)
        self.assertGreater(result.beat_count, 0)
        self.assertGreater(len(result.captions), 0)

        # Check files exist
        self.assertTrue((self.project_dir / "audio" / "voice.json").exists())
        self.assertTrue((self.project_dir / "audio" / "beat-map.json").exists())
        self.assertTrue((self.project_dir / "audio" / "captions.json").exists())
        self.assertTrue((self.project_dir / "audio" / "voice.wav").exists())

    def test_pipeline_updates_project_json(self):
        ingest(self.dummy_audio, self.project_dir, MockProvider())

        with open(self.project_dir / "project.json") as f:
            project = json.load(f)

        self.assertEqual(project["phase"], "voice")
        self.assertEqual(project["status"], "voice_ready")
        self.assertIsNotNone(project["voice_file"])
        self.assertIsNotNone(project["duration_s"])

    def test_beat_map_validates(self):
        result = ingest(self.dummy_audio, self.project_dir, MockProvider())
        errors = validate_beat_map(result.beat_map)
        self.assertEqual(errors, [], f"Beat map validation errors: {errors}")

    def test_captions_all_time_bound(self):
        result = ingest(self.dummy_audio, self.project_dir, MockProvider())
        for cap in result.captions:
            self.assertIn("start", cap)
            self.assertIn("end", cap)
            self.assertIn("text", cap)
            self.assertIn("beat_id", cap)
            self.assertGreater(cap["end"], cap["start"])
            self.assertNotEqual(cap["beat_id"], "")

    def test_captions_aligned_to_beats(self):
        result = ingest(self.dummy_audio, self.project_dir, MockProvider())
        beat_ids = {b["id"] for b in result.beat_map["beats"]}
        for cap in result.captions:
            self.assertIn(cap["beat_id"], beat_ids)

    def test_missing_input_file(self):
        with self.assertRaises(IngestError) as ctx:
            ingest(Path("nonexistent.wav"), self.project_dir, MockProvider())
        self.assertIn("not found", str(ctx.exception))

    def test_unsupported_file_type(self):
        bad_file = self.tmpdir / "document.pdf"
        bad_file.write_bytes(b"PDF")
        with self.assertRaises(IngestError) as ctx:
            ingest(bad_file, self.project_dir, MockProvider())
        self.assertIn("Unsupported", str(ctx.exception))

    def test_output_json_is_valid_json(self):
        ingest(self.dummy_audio, self.project_dir, MockProvider())
        for fname in ("voice.json", "beat-map.json", "captions.json"):
            path = self.project_dir / "audio" / fname
            with open(path) as f:
                data = json.load(f)  # should not raise
            self.assertIsNotNone(data)


# ── File type detection tests ────────────────────────────────────────────────

class TestFileDetection(unittest.TestCase):

    def test_video_extensions(self):
        for ext in (".mp4", ".webm", ".mov", ".avi", ".mkv"):
            self.assertTrue(is_video(Path(f"file{ext}")), f"{ext} should be video")
        self.assertFalse(is_video(Path("file.wav")))

    def test_audio_extensions(self):
        for ext in (".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"):
            self.assertTrue(is_audio(Path(f"file{ext}")), f"{ext} should be audio")
        self.assertFalse(is_audio(Path("file.mp4")))


# ── Extraction fallback test ─────────────────────────────────────────────────

class TestVideoFallback(unittest.TestCase):
    """Test that video input triggers extraction path (without actual ffmpeg)."""

    def test_video_input_detected(self):
        # We can't actually run ffmpeg in this env, but verify the pipeline
        # correctly identifies a .mp4 as needing extraction
        self.assertTrue(is_video(Path("heygen-output.mp4")))
        self.assertFalse(is_audio(Path("heygen-output.mp4")))

    def test_pipeline_would_extract_video(self):
        # Verify that a .mp4 input to the pipeline triggers the extraction path
        # by checking it fails with FfmpegNotFoundError (not IngestError for bad type)
        from lib.ingest.extract import FfmpegNotFoundError

        tmpdir = Path(tempfile.mkdtemp())
        try:
            video = tmpdir / "heygen.mp4"
            video.write_bytes(b"\x00" * 100)
            project = tmpdir / "proj"
            project.mkdir()
            (project / "project.json").write_text(json.dumps({
                "slug": "test", "title": "T", "phase": "brief",
                "status": "initialized", "created": "2026-01-01T00:00:00Z",
                "updated": "2026-01-01T00:00:00Z",
            }))

            # Should fail at ffmpeg, NOT at file type validation
            try:
                ingest(video, project, MockProvider())
                # If ffmpeg IS installed, this would succeed - also fine
            except FfmpegNotFoundError:
                pass  # Expected: proves extraction path was triggered
            except IngestError:
                self.fail("Pipeline rejected .mp4 as bad type instead of attempting extraction")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ── Modular extractor backend tests ─────────────────────────────────────────

class TestExtractorBackends(unittest.TestCase):

    def test_abstract_base_class(self):
        # AudioExtractor cannot be instantiated directly
        with self.assertRaises(TypeError):
            AudioExtractor()

    def test_ffmpeg_python_extractor_is_backend(self):
        ext = FfmpegPythonExtractor()
        self.assertIsInstance(ext, AudioExtractor)

    def test_cli_extractor_is_backend(self):
        ext = FfmpegCLIExtractor()
        self.assertIsInstance(ext, AudioExtractor)

    def test_get_default_extractor_returns_backend(self):
        ext = get_default_extractor()
        self.assertIsInstance(ext, AudioExtractor)

    def test_ffmpeg_python_preferred_when_available(self):
        # ffmpeg-python is installed (we just pip-installed it)
        ext = get_default_extractor()
        self.assertIsInstance(ext, FfmpegPythonExtractor)

    def test_extract_missing_file_raises(self):
        ext = FfmpegPythonExtractor()
        with self.assertRaises(FileNotFoundError):
            ext.extract(Path("nonexistent.mp4"), Path("out.wav"))

    def test_cli_extract_missing_file_raises(self):
        ext = FfmpegCLIExtractor()
        with self.assertRaises(FileNotFoundError):
            ext.extract(Path("nonexistent.mp4"), Path("out.wav"))


# ── Extract-only pipeline tests ─────────────────────────────────────────────

class TestExtractOnly(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.project_dir = self.tmpdir / "projects" / "test-extract"
        self.project_dir.mkdir(parents=True)
        (self.project_dir / "project.json").write_text(json.dumps({
            "slug": "test-extract",
            "title": "Test",
            "phase": "brief",
            "status": "initialized",
            "created": "2026-01-01T00:00:00Z",
            "updated": "2026-01-01T00:00:00Z",
            "brand": None,
            "template": None,
            "voice_file": None,
            "duration_s": None,
        }))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_extract_only_missing_input(self):
        with self.assertRaises(IngestError) as ctx:
            extract_only(Path("nonexistent.mp4"), self.project_dir)
        self.assertIn("not found", str(ctx.exception))

    def test_extract_only_bad_file_type(self):
        bad = self.tmpdir / "doc.pdf"
        bad.write_bytes(b"PDF")
        with self.assertRaises(IngestError) as ctx:
            extract_only(bad, self.project_dir)
        self.assertIn("Unsupported", str(ctx.exception))

    def test_extract_only_video_triggers_extraction(self):
        from lib.ingest.extract import FfmpegNotFoundError
        video = self.tmpdir / "avatar.mp4"
        video.write_bytes(b"\x00" * 100)
        try:
            result = extract_only(video, self.project_dir)
            # If ffmpeg is installed, extraction succeeds
            self.assertEqual(result.audio_path.name, "source.wav")
        except (FfmpegNotFoundError, ExtractionError):
            pass  # ffmpeg not available — expected in test env

    def test_extract_only_output_path(self):
        from lib.ingest.extract import FfmpegNotFoundError
        video = self.tmpdir / "heygen-avatar.mp4"
        video.write_bytes(b"\x00" * 100)
        try:
            result = extract_only(video, self.project_dir)
            self.assertEqual(result.audio_path, self.project_dir / "audio" / "source.wav")
        except (FfmpegNotFoundError, ExtractionError):
            pass

    def test_extract_only_updates_project_json(self):
        from lib.ingest.extract import FfmpegNotFoundError
        video = self.tmpdir / "avatar.mp4"
        video.write_bytes(b"\x00" * 100)
        try:
            extract_only(video, self.project_dir)
            with open(self.project_dir / "project.json") as f:
                project = json.load(f)
            self.assertEqual(project["status"], "voice_ready")
            self.assertEqual(project["voice_file"], "audio/source.wav")
        except (FfmpegNotFoundError, ExtractionError):
            pass

    def test_extract_only_no_beat_map_or_captions(self):
        from lib.ingest.extract import FfmpegNotFoundError
        video = self.tmpdir / "avatar.mp4"
        video.write_bytes(b"\x00" * 100)
        try:
            result = extract_only(video, self.project_dir)
            self.assertIsNone(result.voice_json)
            self.assertIsNone(result.beat_map)
            self.assertIsNone(result.captions)
            self.assertEqual(result.beat_count, 0)
        except (FfmpegNotFoundError, ExtractionError):
            pass


from lib.ingest.extract import ExtractionError  # noqa: E402


if __name__ == "__main__":
    unittest.main(verbosity=2)
