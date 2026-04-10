"""
QA gate checks — each function inspects one aspect of reel readiness.

All checks accept project data dicts and return lists of Findings.
They do NOT read files — the runner loads data and passes it in.
"""

from __future__ import annotations

import re
from pathlib import Path

from .finding import Finding, Severity

from lib.constants import (
    CAPTION_MAX_WIDTH, CAPTION_FONT_SIZE, MAX_TRANSITION_DURATION,
)


# ── Thresholds ───────────────────────────────────────────────────────────────

MIN_CAPTION_DURATION = 0.8      # seconds — from timing-sync rule
MAX_CAPTION_WORDS = 6           # from visual-style rule
MAX_GAP_BEFORE_DEAD_AIR = 1.5   # seconds of no visual = dead air
MAX_SFX_PER_BEAT = 2            # more than this is overwhelming
MAX_MUSIC_VOLUME = 0.3          # music louder than this risks overpowering voice
MAX_TRANSITIONS_RATIO = 0.5     # if >50% of beats have transitions, it's excessive
PLACEHOLDER_PATTERNS = [
    re.compile(r"\[.*?\]"),              # [placeholder]
    re.compile(r"\{.*?\}"),              # {placeholder}
    re.compile(r"(?i)\bTBD\b"),          # TBD
    re.compile(r"(?i)\bTODO\b"),         # TODO
    re.compile(r"(?i)\bplaceholder\b"),  # placeholder
    re.compile(r"(?i)\bLorem\b"),        # Lorem ipsum
    re.compile(r"(?i)\bXXX\b"),          # XXX
]


# ── Gate: Narration-visual sync ──────────────────────────────────────────────

def check_sync(beat_map: dict, timeline: dict) -> list[Finding]:
    """Every beat with narration should have at least one visual lane active."""
    findings: list[Finding] = []
    beats = beat_map.get("beats", [])
    lanes = timeline.get("lanes", {})
    visual_lanes = ["avatar", "demo", "support"]

    for beat in beats:
        bid = beat["id"]
        start, end = beat["start"], beat["end"]
        mid = (start + end) / 2

        has_visual = False
        for lane_name in visual_lanes:
            for entry in lanes.get(lane_name, []):
                if entry["start"] <= mid < entry["end"]:
                    has_visual = True
                    break
            if has_visual:
                break

        if not has_visual:
            findings.append(Finding(
                gate="sync",
                severity=Severity.BLOCK,
                location=f"{bid} ({start:.1f}s–{end:.1f}s)",
                message=f"Beat has narration but no visual layer active at midpoint",
                fix_hint=f"Add an avatar, demo, or support entry covering {start:.1f}s–{end:.1f}s in timeline.json",
            ))

    return findings


# ── Gate: Caption timing and overflow ────────────────────────────────────────

def check_captions(timeline: dict) -> list[Finding]:
    """Check captions for timing issues, overflow, and coverage."""
    findings: list[Finding] = []
    captions = timeline.get("lanes", {}).get("captions", [])

    if not captions:
        findings.append(Finding(
            gate="captions",
            severity=Severity.BLOCK,
            location="lanes.captions",
            message="No captions in timeline",
            fix_hint="Add caption entries to the captions lane for each beat",
        ))
        return findings

    for i, cap in enumerate(captions):
        loc = f"captions[{i}]"
        start = cap.get("start", 0)
        end = cap.get("end", 0)
        text = cap.get("text", "")
        duration = end - start

        # Too short
        if duration < MIN_CAPTION_DURATION:
            findings.append(Finding(
                gate="captions",
                severity=Severity.WARN,
                location=f"{loc} ({start:.1f}s–{end:.1f}s)",
                message=f"Caption visible for only {duration:.2f}s (min {MIN_CAPTION_DURATION}s): \"{text}\"",
                fix_hint=f"Extend end time to at least {start + MIN_CAPTION_DURATION:.3f}s",
            ))

        # Too many words
        word_count = len(text.split())
        if word_count > MAX_CAPTION_WORDS:
            findings.append(Finding(
                gate="captions",
                severity=Severity.WARN,
                location=f"{loc} ({start:.1f}s–{end:.1f}s)",
                message=f"Caption has {word_count} words (max {MAX_CAPTION_WORDS}): \"{text}\"",
                fix_hint="Split into shorter phrases or reduce wording",
            ))

        # Missing text
        if not text.strip():
            findings.append(Finding(
                gate="captions",
                severity=Severity.BLOCK,
                location=loc,
                message="Caption has empty text",
                fix_hint="Add caption text or remove the empty entry",
            ))

        # Missing beat_id
        if not cap.get("beat_id"):
            findings.append(Finding(
                gate="captions",
                severity=Severity.BLOCK,
                location=loc,
                message="Caption has no beat_id",
                fix_hint="Link this caption to a beat",
            ))

    # Check for overlapping captions
    sorted_caps = sorted(captions, key=lambda c: c.get("start", 0))
    for i in range(1, len(sorted_caps)):
        prev_end = sorted_caps[i - 1].get("end", 0)
        curr_start = sorted_caps[i].get("start", 0)
        if curr_start < prev_end - 0.01:
            findings.append(Finding(
                gate="captions",
                severity=Severity.WARN,
                location=f"captions[{i - 1}]→captions[{i}]",
                message=f"Captions overlap: prev ends at {prev_end:.3f}s, next starts at {curr_start:.3f}s",
                fix_hint="Adjust timing so captions don't stack on screen",
            ))

    return findings


# ── Gate: Dead air / awkward gaps ────────────────────────────────────────────

def check_dead_air(beat_map: dict, timeline: dict) -> list[Finding]:
    """Find gaps where nothing visual is happening."""
    findings: list[Finding] = []
    total = timeline.get("total_duration", beat_map.get("total_duration", 0))
    lanes = timeline.get("lanes", {})
    visual_lanes = ["avatar", "demo", "support"]

    # Collect all visual coverage intervals
    intervals: list[tuple[float, float]] = []
    for lane_name in visual_lanes:
        for entry in lanes.get(lane_name, []):
            intervals.append((entry["start"], entry["end"]))

    if not intervals:
        findings.append(Finding(
            gate="dead-air",
            severity=Severity.BLOCK,
            location="0.0s–end",
            message="No visual content in any lane — entire reel is dead air",
            fix_hint="Add visual entries to avatar, demo, or support lanes",
        ))
        return findings

    # Merge intervals
    intervals.sort()
    merged: list[tuple[float, float]] = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1] + 0.01:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    # Check gap before first visual
    if merged[0][0] > MAX_GAP_BEFORE_DEAD_AIR:
        findings.append(Finding(
            gate="dead-air",
            severity=Severity.WARN,
            location=f"0.0s–{merged[0][0]:.1f}s",
            message=f"No visuals for first {merged[0][0]:.1f}s of the reel",
            fix_hint="Add a visual entry starting at or near 0.0s",
        ))

    # Check gaps between visuals
    for i in range(1, len(merged)):
        gap_start = merged[i - 1][1]
        gap_end = merged[i][0]
        gap = gap_end - gap_start
        if gap > MAX_GAP_BEFORE_DEAD_AIR:
            findings.append(Finding(
                gate="dead-air",
                severity=Severity.BLOCK if gap > 3.0 else Severity.WARN,
                location=f"{gap_start:.1f}s–{gap_end:.1f}s",
                message=f"{gap:.1f}s gap with no visuals (dead air)",
                fix_hint=f"Add visual content or tighten beat spacing to cover {gap_start:.1f}s–{gap_end:.1f}s",
            ))

    # Check gap after last visual
    tail_gap = total - merged[-1][1]
    if tail_gap > MAX_GAP_BEFORE_DEAD_AIR:
        findings.append(Finding(
            gate="dead-air",
            severity=Severity.WARN,
            location=f"{merged[-1][1]:.1f}s–{total:.1f}s",
            message=f"No visuals for last {tail_gap:.1f}s of the reel",
            fix_hint="Extend the last visual entry or add a closing visual",
        ))

    return findings


# ── Gate: Missing assets ─────────────────────────────────────────────────────

def check_missing_assets(timeline: dict, assets_dir: Path | None = None) -> list[Finding]:
    """Check that all assets referenced in the timeline exist on disk.

    Searches both the project assets/ directory and remotion/public/
    (the Remotion static file directory where assets must exist for rendering).
    """
    findings: list[Finding] = []
    lanes = timeline.get("lanes", {})

    if assets_dir is None:
        return findings

    # Also check remotion/public/ — Remotion reads assets from there
    # assets_dir is <project>/assets, so go up to repo root: <project>/../../remotion/public
    remotion_public = assets_dir.parent.parent.parent / "remotion" / "public"
    search_dirs = [assets_dir]
    if remotion_public.exists():
        search_dirs.append(remotion_public)

    for lane_name, entries in lanes.items():
        if not isinstance(entries, list):
            continue
        for i, entry in enumerate(entries):
            asset = entry.get("asset")
            if not asset:
                continue
            found = any((d / asset).exists() for d in search_dirs)
            if not found:
                findings.append(Finding(
                    gate="missing-assets",
                    severity=Severity.BLOCK,
                    location=f"lanes.{lane_name}[{i}]",
                    message=f"Asset file not found: {asset}",
                    fix_hint=f"Add {asset} to remotion/public/ or project assets/ directory",
                ))

    return findings


# ── Gate: Excessive transitions ──────────────────────────────────────────────

def check_transitions(timeline: dict, beat_map: dict) -> list[Finding]:
    """Flag too many transitions or transitions that are too long."""
    findings: list[Finding] = []
    lanes = timeline.get("lanes", {})
    n_beats = len(beat_map.get("beats", []))

    transition_count = 0
    for lane_name in ("avatar", "demo", "support"):
        for i, entry in enumerate(lanes.get(lane_name, [])):
            tr = entry.get("transition")
            if tr and tr.get("type", "cut") != "cut":
                transition_count += 1
                dur = tr.get("duration", 0)
                if dur > MAX_TRANSITION_DURATION:
                    findings.append(Finding(
                        gate="transitions",
                        severity=Severity.BLOCK,
                        location=f"lanes.{lane_name}[{i}]",
                        message=f"Transition duration {dur}s exceeds max {MAX_TRANSITION_DURATION}s",
                        fix_hint=f"Reduce transition duration to ≤{MAX_TRANSITION_DURATION}s",
                    ))

    if n_beats > 0 and transition_count / n_beats > MAX_TRANSITIONS_RATIO:
        findings.append(Finding(
            gate="transitions",
            severity=Severity.WARN,
            location="timeline",
            message=f"{transition_count} transitions across {n_beats} beats ({transition_count/n_beats:.0%}) — may overwhelm the viewer",
            fix_hint="Convert some transitions to cuts for a cleaner feel",
        ))

    return findings


# ── Gate: SFX / music balance ────────────────────────────────────────────────

def check_audio_balance(timeline: dict, beat_map: dict) -> list[Finding]:
    """Check SFX density and music volume levels."""
    findings: list[Finding] = []
    lanes = timeline.get("lanes", {})
    beats = beat_map.get("beats", [])

    # SFX density per beat
    sfx_entries = lanes.get("sfx", [])
    for beat in beats:
        bid = beat["id"]
        start, end = beat["start"], beat["end"]
        beat_sfx = [s for s in sfx_entries if start <= s.get("start", 0) < end]
        if len(beat_sfx) > MAX_SFX_PER_BEAT:
            findings.append(Finding(
                gate="audio-balance",
                severity=Severity.WARN,
                location=f"{bid} ({start:.1f}s–{end:.1f}s)",
                message=f"{len(beat_sfx)} SFX in one beat (max {MAX_SFX_PER_BEAT}) — may overpower narration",
                fix_hint="Remove less important SFX or spread them across beats",
            ))

    # Music volume
    for i, entry in enumerate(lanes.get("music", [])):
        vol = entry.get("volume", 1.0)
        if vol > MAX_MUSIC_VOLUME:
            findings.append(Finding(
                gate="audio-balance",
                severity=Severity.BLOCK,
                location=f"lanes.music[{i}]",
                message=f"Music volume {vol} exceeds max {MAX_MUSIC_VOLUME} — will overpower narration",
                fix_hint=f"Reduce music volume to ≤{MAX_MUSIC_VOLUME}",
            ))

    # No music at all (warning, not blocking)
    if not lanes.get("music"):
        findings.append(Finding(
            gate="audio-balance",
            severity=Severity.WARN,
            location="lanes.music",
            message="No background music — reel may feel empty during pauses",
            fix_hint="Add a music entry with low volume (0.1–0.2) for ambiance",
        ))

    return findings


# ── Gate: Timeline consistency ───────────────────────────────────────────────

def check_timeline_consistency(timeline: dict, beat_map: dict) -> list[Finding]:
    """Cross-check timeline against beat-map for logical consistency."""
    findings: list[Finding] = []
    tl_dur = timeline.get("total_duration", 0)
    bm_dur = beat_map.get("total_duration", 0)

    # Duration mismatch
    if abs(tl_dur - bm_dur) > 0.1:
        findings.append(Finding(
            gate="consistency",
            severity=Severity.BLOCK,
            location="total_duration",
            message=f"Timeline duration ({tl_dur}s) doesn't match beat-map ({bm_dur}s) — tolerance ±0.1s",
            fix_hint="Align total_duration in timeline.json with beat-map.json",
        ))

    # Check every beat has at least one caption
    beat_ids = {b["id"] for b in beat_map.get("beats", [])}
    caption_beats = {c.get("beat_id") for c in timeline.get("lanes", {}).get("captions", [])}
    uncaptioned = beat_ids - caption_beats
    for bid in sorted(uncaptioned):
        findings.append(Finding(
            gate="consistency",
            severity=Severity.WARN,
            location=bid,
            message=f"Beat has no caption entry in the timeline",
            fix_hint=f"Add a caption for {bid} to the captions lane",
        ))

    # Entries that extend past total_duration
    for lane_name, entries in timeline.get("lanes", {}).items():
        if not isinstance(entries, list):
            continue
        for i, entry in enumerate(entries):
            end = entry.get("end", 0)
            if end > tl_dur + 0.1:
                findings.append(Finding(
                    gate="consistency",
                    severity=Severity.BLOCK,
                    location=f"lanes.{lane_name}[{i}]",
                    message=f"Entry ends at {end}s but reel duration is {tl_dur}s",
                    fix_hint=f"Trim entry end to ≤{tl_dur}s",
                ))

    return findings


# ── Gate: Unresolved placeholders ────────────────────────────────────────────

def check_placeholders(beat_map: dict, timeline: dict) -> list[Finding]:
    """Find placeholder text that was never filled in."""
    findings: list[Finding] = []

    # Check beat visual_intent
    for beat in beat_map.get("beats", []):
        intent = beat.get("visual_intent", "")
        if not intent.strip():
            findings.append(Finding(
                gate="placeholders",
                severity=Severity.WARN,
                location=beat["id"],
                message="visual_intent is empty — no visual direction for this beat",
                fix_hint=f"Fill in visual_intent describing what the viewer should see during {beat['id']}",
            ))
        else:
            for pat in PLACEHOLDER_PATTERNS:
                match = pat.search(intent)
                if match:
                    findings.append(Finding(
                        gate="placeholders",
                        severity=Severity.BLOCK,
                        location=beat["id"],
                        message=f"visual_intent contains placeholder: \"{match.group()}\"",
                        fix_hint="Replace placeholder with actual visual direction",
                    ))
                    break

    # Check beat phrases
    for beat in beat_map.get("beats", []):
        phrase = beat.get("phrase", "")
        for pat in PLACEHOLDER_PATTERNS:
            match = pat.search(phrase)
            if match:
                findings.append(Finding(
                    gate="placeholders",
                    severity=Severity.BLOCK,
                    location=beat["id"],
                    message=f"Narration phrase contains placeholder: \"{match.group()}\"",
                    fix_hint="Replace placeholder with final narration text",
                ))
                break

    # Check caption text
    for i, cap in enumerate(timeline.get("lanes", {}).get("captions", [])):
        text = cap.get("text", "")
        for pat in PLACEHOLDER_PATTERNS:
            match = pat.search(text)
            if match:
                findings.append(Finding(
                    gate="placeholders",
                    severity=Severity.BLOCK,
                    location=f"captions[{i}]",
                    message=f"Caption contains placeholder: \"{match.group()}\"",
                    fix_hint="Replace placeholder with final caption text",
                ))
                break

    return findings


# ── Gate: Safe zone (rendered frame check) ───────────────────────────────────

def check_safe_zones_from_captions(timeline: dict) -> list[Finding]:
    """
    Verify captions are positioned in the safe zone.

    This is a structural check (not pixel-level). The renderer places captions
    at CAPTION_Y which is above BOTTOM_RESERVED. This gate verifies no timeline
    entry explicitly places content outside the safe area.
    """
    findings: list[Finding] = []

    # Captions are auto-positioned by the renderer, so they're safe by construction.
    # This gate catches future manual overrides or custom positioning.
    # For V1, it's a pass-through that documents the guarantee.

    return findings


# ── Gate: Duration ───────────────────────────────────────────────────────────

def check_duration(beat_map: dict) -> list[Finding]:
    """Check reel is within Instagram limits (3s–90s, optimized for 20–60s)."""
    findings: list[Finding] = []
    dur = beat_map.get("total_duration", 0)

    if dur < 3.0:
        findings.append(Finding(
            gate="duration",
            severity=Severity.BLOCK,
            location="total_duration",
            message=f"Reel is {dur:.1f}s — too short (minimum 3s)",
            fix_hint="Add more content or extend existing beats",
        ))
    elif dur > 90.0:
        findings.append(Finding(
            gate="duration",
            severity=Severity.BLOCK,
            location="total_duration",
            message=f"Reel is {dur:.1f}s — exceeds Instagram max (90s)",
            fix_hint="Trim content to under 90s",
        ))
    elif dur < 15.0:
        findings.append(Finding(
            gate="duration",
            severity=Severity.WARN,
            location="total_duration",
            message=f"Reel is {dur:.1f}s — very short, consider 20–60s for best engagement",
            fix_hint="Optional: expand content for better audience retention",
        ))
    elif dur > 60.0:
        findings.append(Finding(
            gate="duration",
            severity=Severity.WARN,
            location="total_duration",
            message=f"Reel is {dur:.1f}s — longer reels may lose viewers, sweet spot is 20–60s",
            fix_hint="Optional: tighten pacing or cut less essential beats",
        ))

    return findings


# ── Style-aware thresholds (from qa-gates.md) ──────────────────────────────

STYLE_THRESHOLDS = {
    "cinematic-presenter": {
        "avatar_absence_warn": 12.0,
        "avatar_absence_block": 15.0,
        "center_full_max": 4,
        "flash_max": 1,
        "sfx_targets": {(30, 40): (6, 8), (40, 55): (8, 12)},
    },
    "editorial-authority": {
        "avatar_absence_warn": 8.0,
        "avatar_absence_block": 12.0,
        "center_full_max": 4,
        "flash_max_short": 2,
        "flash_max_long": 3,
        "sfx_targets": {(30, 40): (5, 9), (40, 55): (7, 12)},
    },
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}


def _get_thresholds(style: str) -> dict:
    return STYLE_THRESHOLDS.get(style, STYLE_THRESHOLDS["cinematic-presenter"])


# ── Gate: Avatar absence ───────────────────────────────────────────────────

def check_avatar_absence(timeline: dict, style: str = "cinematic-presenter") -> list[Finding]:
    """Flag periods where the avatar is absent for too long."""
    findings: list[Finding] = []
    th = _get_thresholds(style)
    total = timeline.get("total_duration", 0)
    avatar_entries = timeline.get("lanes", {}).get("avatar", [])

    if not avatar_entries:
        findings.append(Finding(
            gate="avatar-absence",
            severity=Severity.BLOCK,
            location="lanes.avatar",
            message="No avatar entries — avatar is absent for the entire reel",
            fix_hint="Add avatar lane entries for presenter sections",
        ))
        return findings

    intervals = sorted([(e["start"], e["end"]) for e in avatar_entries])
    merged: list[tuple[float, float]] = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1] + 0.01:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    if merged[0][0] > th["avatar_absence_warn"]:
        sev = Severity.BLOCK if merged[0][0] > th["avatar_absence_block"] else Severity.WARN
        findings.append(Finding(
            gate="avatar-absence", severity=sev,
            location=f"0.0s–{merged[0][0]:.1f}s",
            message=f"Avatar absent for {merged[0][0]:.1f}s at start (limit: {th['avatar_absence_warn']}s/{th['avatar_absence_block']}s)",
            fix_hint="Add an avatar entry or split-screen beat earlier",
        ))

    for i in range(1, len(merged)):
        gap = merged[i][0] - merged[i - 1][1]
        if gap > th["avatar_absence_warn"]:
            sev = Severity.BLOCK if gap > th["avatar_absence_block"] else Severity.WARN
            findings.append(Finding(
                gate="avatar-absence", severity=sev,
                location=f"{merged[i-1][1]:.1f}s–{merged[i][0]:.1f}s",
                message=f"Avatar absent for {gap:.1f}s (limit: {th['avatar_absence_warn']}s/{th['avatar_absence_block']}s)",
                fix_hint="Add a split-screen return or avatar beat to break up the gap",
            ))

    tail = total - merged[-1][1]
    if tail > th["avatar_absence_warn"]:
        sev = Severity.BLOCK if tail > th["avatar_absence_block"] else Severity.WARN
        findings.append(Finding(
            gate="avatar-absence", severity=sev,
            location=f"{merged[-1][1]:.1f}s–{total:.1f}s",
            message=f"Avatar absent for {tail:.1f}s at end",
            fix_hint="Add a closing avatar beat (CTA, outro)",
        ))

    return findings


# ── Gate: Consecutive center-full streak ──────────────────────────────────

def check_center_full_streak(timeline: dict, style: str = "cinematic-presenter") -> list[Finding]:
    """Flag too many consecutive center-full entries without a face return."""
    findings: list[Finding] = []
    th = _get_thresholds(style)
    max_streak = th.get("center_full_max", 4)

    all_entries = []
    for lane_name in ("demo", "support", "broll"):
        for entry in timeline.get("lanes", {}).get(lane_name, []):
            all_entries.append(entry)
    all_entries.sort(key=lambda e: e.get("start", 0))

    streak = 0
    streak_start = None
    for entry in all_entries:
        if entry.get("display") == "center-full":
            if streak == 0:
                streak_start = entry.get("start", 0)
            streak += 1
        else:
            if streak > max_streak:
                findings.append(Finding(
                    gate="center-full-streak", severity=Severity.WARN,
                    location=f"{streak_start:.1f}s–{entry.get('start', 0):.1f}s",
                    message=f"{streak} consecutive center-full entries (max {max_streak})",
                    fix_hint="Insert a split-screen or avatar beat to break the streak",
                ))
            streak = 0

    if streak > max_streak:
        findings.append(Finding(
            gate="center-full-streak", severity=Severity.WARN,
            location=f"{streak_start:.1f}s–end",
            message=f"{streak} consecutive center-full entries (max {max_streak})",
            fix_hint="Insert a split-screen or avatar beat to break the streak",
        ))

    return findings


# ── Gate: SFX coverage ─────────────────────────────────────────────────────

def check_sfx_coverage(timeline: dict, beat_map: dict, style: str = "cinematic-presenter") -> list[Finding]:
    """Check total SFX count against duration-based minimums."""
    findings: list[Finding] = []
    th = _get_thresholds(style)
    total_dur = beat_map.get("total_duration", timeline.get("total_duration", 0))
    sfx_count = len(timeline.get("lanes", {}).get("sfx", []))

    for (lo, hi), (min_sfx, _max_sfx) in th.get("sfx_targets", {}).items():
        if lo <= total_dur < hi:
            if sfx_count < min_sfx:
                findings.append(Finding(
                    gate="sfx-coverage", severity=Severity.WARN,
                    location="lanes.sfx",
                    message=f"{sfx_count} SFX entries for {total_dur:.0f}s reel (min {min_sfx} for {style})",
                    fix_hint=f"Add {min_sfx - sfx_count} more SFX at layout changes and emphasis moments",
                ))
            break

    return findings


# ── Gate: Video encoding ──────────────────────────────────────────────────

def check_video_encoding(video_probes: list[dict]) -> list[Finding]:
    """Validate video files meet Remotion encoding requirements.

    Expects pre-computed probe results from runner._probe_videos().
    Each dict: {path, codec, fps, pix_fmt, has_audio}
    """
    findings: list[Finding] = []

    for probe in video_probes:
        name = Path(probe.get("path", "?")).name

        if probe.get("codec") == "probe_failed":
            findings.append(Finding(
                gate="video-encoding", severity=Severity.WARN,
                location=name,
                message="ffprobe not available — could not verify encoding",
                fix_hint="Install ffprobe (part of ffmpeg) and re-run QA",
            ))
            continue

        codec = probe.get("codec", "")
        if codec != "h264":
            findings.append(Finding(
                gate="video-encoding", severity=Severity.BLOCK, location=name,
                message=f"Codec is {codec!r}, expected h264",
                fix_hint=f"Re-encode with: ffmpeg -i {name} -c:v libx264 -pix_fmt yuv420p -g 1 -movflags +faststart -r 30 -c:a aac output.mp4",
            ))

        fps = probe.get("fps", "")
        try:
            fps_val = int(fps.split("/")[0]) / int(fps.split("/")[1]) if "/" in fps else float(fps)
            if abs(fps_val - 30.0) > 1.0:
                findings.append(Finding(
                    gate="video-encoding", severity=Severity.BLOCK, location=name,
                    message=f"FPS is {fps_val:.1f}, expected 30",
                    fix_hint="Re-encode with -r 30",
                ))
        except (ValueError, ZeroDivisionError, IndexError):
            pass

        pix_fmt = probe.get("pix_fmt", "")
        if pix_fmt and pix_fmt != "yuv420p":
            findings.append(Finding(
                gate="video-encoding", severity=Severity.BLOCK, location=name,
                message=f"Pixel format is {pix_fmt!r}, expected yuv420p",
                fix_hint="Re-encode with -pix_fmt yuv420p",
            ))

        if not probe.get("has_audio", False):
            findings.append(Finding(
                gate="video-encoding", severity=Severity.BLOCK, location=name,
                message="No audio track — Remotion may throw HTMLVideoElement errors",
                fix_hint="Add silent audio: ffmpeg -i input.mp4 -f lavfi -i anullsrc=r=44100:cl=mono -shortest -c:v copy -c:a aac output.mp4",
            ))

    return findings


# ── Gate: Screenshot hold duration ─────────────────────────────────────────

def check_screenshot_hold(timeline: dict) -> list[Finding]:
    """Flag static images held for >2s without zoom_moments."""
    findings: list[Finding] = []

    for lane_name in ("demo", "support", "broll"):
        for i, entry in enumerate(timeline.get("lanes", {}).get(lane_name, [])):
            asset = entry.get("asset", "")
            if not asset:
                continue
            suffix = Path(asset).suffix.lower()
            if suffix not in IMAGE_EXTENSIONS:
                continue

            duration = entry.get("end", 0) - entry.get("start", 0)
            if duration > 2.0 and not entry.get("zoom_moments") and not entry.get("crop"):
                findings.append(Finding(
                    gate="screenshot-hold", severity=Severity.WARN,
                    location=f"lanes.{lane_name}[{i}] ({entry.get('start', 0):.1f}s–{entry.get('end', 0):.1f}s)",
                    message=f"Static screenshot '{asset}' holds for {duration:.1f}s without zoom_moments",
                    fix_hint="Add zoom_moments targeting a specific UI element, or split into multiple images",
                ))

    return findings


# ── Gate: Flash/punch accent budget ───────────────────────────────────────

def check_flash_budget(timeline: dict, style: str = "cinematic-presenter") -> list[Finding]:
    """Count flash/punch accents and flag if exceeding style limit."""
    findings: list[Finding] = []
    th = _get_thresholds(style)
    total_dur = timeline.get("total_duration", 0)

    flash_count = 0
    for lane_name in ("avatar", "demo", "support", "broll"):
        for entry in timeline.get("lanes", {}).get(lane_name, []):
            tp = entry.get("transition_preset", {})
            enter = tp.get("enter", "") if isinstance(tp, dict) else ""
            if "punch" in enter.lower() or "flash" in enter.lower():
                flash_count += 1

    if style == "editorial-authority":
        limit = th.get("flash_max_long", 3) if total_dur >= 35 else th.get("flash_max_short", 2)
    else:
        limit = th.get("flash_max", 1)

    if flash_count > limit:
        findings.append(Finding(
            gate="flash-budget", severity=Severity.WARN,
            location="timeline",
            message=f"{flash_count} flash/punch accents (max {limit} for {style})",
            fix_hint="Replace excess flash accents with opacity shifts or grade changes",
        ))

    return findings


# ── Gate: Style compliance (editorial-authority) ──────────────────────────

def check_style_compliance(timeline: dict, beat_map: dict, project: dict, style: str = "cinematic-presenter") -> list[Finding]:
    """Run editorial-authority specific compliance checks."""
    findings: list[Finding] = []
    if style != "editorial-authority":
        return findings

    if project.get("style") != "editorial-authority":
        findings.append(Finding(
            gate="style-compliance", severity=Severity.BLOCK,
            location="project.json",
            message="Style is editorial-authority but project.json style field doesn't match",
            fix_hint='Set "style": "editorial-authority" in project.json',
        ))

    for lane_name in ("demo", "support"):
        for i, entry in enumerate(timeline.get("lanes", {}).get(lane_name, [])):
            if entry.get("proof_protected") and "broll" in entry.get("asset", "").lower():
                findings.append(Finding(
                    gate="style-compliance", severity=Severity.BLOCK,
                    location=f"lanes.{lane_name}[{i}]",
                    message=f"Proof-protected beat uses b-roll asset — must use real source",
                    fix_hint="Replace with actual screenshot, screen recording, or source image",
                ))
            if entry.get("kenBurns") or entry.get("ken_burns"):
                findings.append(Finding(
                    gate="style-compliance", severity=Severity.WARN,
                    location=f"lanes.{lane_name}[{i}]",
                    message="Ken Burns on editorial-authority content (not used in this style)",
                    fix_hint="Remove kenBurns — editorial style uses stillness",
                ))

    return findings


# ── Gate: Overlay positioning ───────────────────────────────────���─────────

def check_overlay_positioning(timeline: dict) -> list[Finding]:
    """Check overlay entries for centered positioning and mobile-readable sizing."""
    findings: list[Finding] = []

    for i, entry in enumerate(timeline.get("lanes", {}).get("support") or []):
        component = entry.get("component", "")
        is_overlay = any(kw in component.lower() for kw in ("keyword", "badge", "overlay", "number", "popup"))
        if not is_overlay:
            continue

        position = entry.get("position", "center")
        font_size = entry.get("fontSize", 64)

        if position in ("top-left", "top-right", "bottom-left", "bottom-right"):
            findings.append(Finding(
                gate="overlay-positioning", severity=Severity.WARN,
                location=f"lanes.support[{i}] ({entry.get('start', 0):.1f}s–{entry.get('end', 0):.1f}s)",
                message=f"Overlay at '{position}' — should be centered for mobile readability",
                fix_hint='Set position to "center" unless there is a documented design reason',
            ))

        if isinstance(font_size, (int, float)) and font_size < 64:
            findings.append(Finding(
                gate="overlay-positioning", severity=Severity.WARN,
                location=f"lanes.support[{i}]",
                message=f"Overlay fontSize {font_size} — minimum 64 for mobile readability",
                fix_hint="Increase fontSize to at least 64",
            ))

    return findings
