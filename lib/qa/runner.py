"""
QA runner — loads project data, runs all gates, produces a report.

This is the main entry point for the QA workflow.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .finding import Finding, Severity
from .checks import (
    check_sync,
    check_captions,
    check_dead_air,
    check_missing_assets,
    check_transitions,
    check_audio_balance,
    check_timeline_consistency,
    check_placeholders,
    check_safe_zones_from_captions,
    check_duration,
    # New style-aware checks
    check_avatar_absence,
    check_center_full_streak,
    check_sfx_coverage,
    check_video_encoding,
    check_screenshot_hold,
    check_flash_budget,
    check_style_compliance,
    check_overlay_positioning,
)


# ── Gate registry ────────────────────────────────────────────────────────────
# Signature: (beat_map, timeline, assets_dir, project, style, video_probes)

GATES = [
    # Original 10 gates
    ("duration",         lambda bm, tl, ad, pj, st, vp: check_duration(bm)),
    ("sync",             lambda bm, tl, ad, pj, st, vp: check_sync(bm, tl)),
    ("captions",         lambda bm, tl, ad, pj, st, vp: check_captions(tl)),
    ("dead-air",         lambda bm, tl, ad, pj, st, vp: check_dead_air(bm, tl)),
    ("missing-assets",   lambda bm, tl, ad, pj, st, vp: check_missing_assets(tl, ad)),
    ("transitions",      lambda bm, tl, ad, pj, st, vp: check_transitions(tl, bm)),
    ("audio-balance",    lambda bm, tl, ad, pj, st, vp: check_audio_balance(tl, bm)),
    ("consistency",      lambda bm, tl, ad, pj, st, vp: check_timeline_consistency(tl, bm)),
    ("placeholders",     lambda bm, tl, ad, pj, st, vp: check_placeholders(bm, tl)),
    ("safe-zones",       lambda bm, tl, ad, pj, st, vp: check_safe_zones_from_captions(tl)),
    # New style-aware gates
    ("avatar-absence",       lambda bm, tl, ad, pj, st, vp: check_avatar_absence(tl, st)),
    ("center-full-streak",   lambda bm, tl, ad, pj, st, vp: check_center_full_streak(tl, st)),
    ("sfx-coverage",         lambda bm, tl, ad, pj, st, vp: check_sfx_coverage(tl, bm, st)),
    ("video-encoding",       lambda bm, tl, ad, pj, st, vp: check_video_encoding(vp)),
    ("screenshot-hold",      lambda bm, tl, ad, pj, st, vp: check_screenshot_hold(tl)),
    ("flash-budget",         lambda bm, tl, ad, pj, st, vp: check_flash_budget(tl, st)),
    ("style-compliance",     lambda bm, tl, ad, pj, st, vp: check_style_compliance(tl, bm, pj, st)),
    ("overlay-positioning",  lambda bm, tl, ad, pj, st, vp: check_overlay_positioning(tl)),
]


# ── Video probing ────────────────────────────────────────────────────────────

VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".mkv"}


def _probe_videos(directory: Path) -> list[dict]:
    """Run ffprobe on every video file in a directory.

    Returns a list of dicts with: path, codec, fps, pix_fmt, has_audio.
    Handles ffprobe not being installed gracefully.
    """
    results: list[dict] = []

    if not directory.exists():
        return results

    video_files = [f for f in directory.iterdir() if f.suffix.lower() in VIDEO_EXTENSIONS and f.is_file()]

    for vf in video_files:
        probe = {"path": str(vf), "codec": "", "fps": "", "pix_fmt": "", "has_audio": False}

        try:
            # Probe video stream
            cmd_video = [
                "ffprobe", "-v", "quiet",
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_name,r_frame_rate,pix_fmt",
                "-of", "json", str(vf),
            ]
            out = subprocess.run(cmd_video, capture_output=True, text=True, timeout=10)
            if out.returncode == 0:
                data = json.loads(out.stdout)
                streams = data.get("streams", [])
                if streams:
                    probe["codec"] = streams[0].get("codec_name", "")
                    probe["fps"] = streams[0].get("r_frame_rate", "")
                    probe["pix_fmt"] = streams[0].get("pix_fmt", "")

            # Probe for audio stream existence
            cmd_audio = [
                "ffprobe", "-v", "quiet",
                "-select_streams", "a:0",
                "-show_entries", "stream=codec_name",
                "-of", "json", str(vf),
            ]
            out_a = subprocess.run(cmd_audio, capture_output=True, text=True, timeout=10)
            if out_a.returncode == 0:
                data_a = json.loads(out_a.stdout)
                probe["has_audio"] = len(data_a.get("streams", [])) > 0

        except FileNotFoundError:
            probe["codec"] = "probe_failed"
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            probe["codec"] = "probe_failed"

        results.append(probe)

    return results


# ── Report ───────────────────────────────────────────────────────────────────

class QAReport:
    """Structured QA report with pass/fail verdict."""

    def __init__(self, findings: list[Finding], project_slug: str = ""):
        self.findings = findings
        self.project_slug = project_slug
        self.timestamp = datetime.now(timezone.utc).isoformat()

    @property
    def blockers(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == Severity.BLOCK]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == Severity.WARN]

    @property
    def passed(self) -> bool:
        return len(self.blockers) == 0

    @property
    def verdict(self) -> str:
        if self.passed:
            if self.warnings:
                return "PASS_WITH_WARNINGS"
            return "PASS"
        return "FAIL"

    def to_dict(self) -> dict:
        return {
            "project": self.project_slug,
            "timestamp": self.timestamp,
            "verdict": self.verdict,
            "blockers": len(self.blockers),
            "warnings": len(self.warnings),
            "total_findings": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
            "gates_run": list({f.gate for f in self.findings}) or [g[0] for g in GATES],
        }

    def summary(self) -> str:
        """Human-readable summary."""
        lines = []
        lines.append(f"QA Report: {self.project_slug or 'unnamed'}")
        lines.append(f"Verdict:   {self.verdict}")
        lines.append(f"Blockers:  {len(self.blockers)}")
        lines.append(f"Warnings:  {len(self.warnings)}")
        lines.append("")

        if self.blockers:
            lines.append("── BLOCKING ISSUES (must fix) ──")
            for f in self.blockers:
                lines.append(f"  [{f.gate}] {f.location}")
                lines.append(f"    {f.message}")
                lines.append(f"    Fix: {f.fix_hint}")
                lines.append("")

        if self.warnings:
            lines.append("── WARNINGS (review recommended) ──")
            for f in self.warnings:
                lines.append(f"  [{f.gate}] {f.location}")
                lines.append(f"    {f.message}")
                lines.append(f"    Fix: {f.fix_hint}")
                lines.append("")

        if self.passed and not self.warnings:
            lines.append("All gates passed. Ready for export.")

        return "\n".join(lines)


# ── Runner ───────────────────────────────────────────────────────────────────

def run_qa(
    beat_map: dict,
    timeline: dict,
    assets_dir: Path | None = None,
    project: dict | None = None,
    style: str = "cinematic-presenter",
    video_probes: list[dict] | None = None,
    project_slug: str = "",
) -> QAReport:
    """Run all QA gates and return a report."""
    all_findings: list[Finding] = []
    pj = project or {}
    vp = video_probes or []

    for gate_name, gate_fn in GATES:
        try:
            findings = gate_fn(beat_map, timeline, assets_dir, pj, style, vp)
            all_findings.extend(findings)
        except Exception as e:
            all_findings.append(Finding(
                gate=gate_name,
                severity=Severity.BLOCK,
                location="gate-runner",
                message=f"Gate crashed: {type(e).__name__}: {e}",
                fix_hint="Fix the underlying data issue and re-run QA",
            ))

    return QAReport(all_findings, project_slug=project_slug)


def run_qa_on_project(project_dir: Path) -> QAReport:
    """Load project files and run full QA."""

    def _load(path: Path) -> dict:
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    project = _load(project_dir / "project.json")
    beat_map = _load(project_dir / "audio" / "beat-map.json")
    timeline = _load(project_dir / "output" / "timeline.json")
    assets_dir = project_dir / "assets"

    slug = project.get("slug", project_dir.name)
    style = project.get("style", "cinematic-presenter")

    # Pre-flight: check required files exist
    findings: list[Finding] = []
    if not beat_map:
        findings.append(Finding(
            gate="pre-flight",
            severity=Severity.BLOCK,
            location="audio/beat-map.json",
            message="Beat map not found — voice ingestion must run first",
            fix_hint="Run the ingest-voice pipeline before QA",
        ))
    if not timeline:
        findings.append(Finding(
            gate="pre-flight",
            severity=Severity.BLOCK,
            location="output/timeline.json",
            message="Timeline not found — assembly must run first",
            fix_hint="Run the assemble-reel pipeline before QA",
        ))

    if findings:
        return QAReport(findings, project_slug=slug)

    # Probe video files in remotion/public/
    remotion_public = project_dir.parent.parent / "remotion" / "public"
    if not remotion_public.exists():
        # Try from repo root
        remotion_public = project_dir.parent.parent / "remotion" / "public"
    video_probes = _probe_videos(remotion_public)

    report = run_qa(
        beat_map, timeline, assets_dir,
        project=project, style=style, video_probes=video_probes,
        project_slug=slug,
    )

    # Write report to project
    report_path = project_dir / "output" / "qa_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

    # Update project.json status + gates
    pj_path = project_dir / "project.json"
    if pj_path.exists():
        with open(pj_path, "r", encoding="utf-8") as f:
            pj = json.load(f)

        pj["phase"] = "qa"
        pj["updated"] = datetime.now(timezone.utc).isoformat()

        gates = pj.get("gates_passed", [])
        if report.passed:
            pj["status"] = "completed"
            if "qa_passed" not in gates:
                gates.append("qa_passed")
        else:
            pj["status"] = "failed"
            gates = [g for g in gates if g != "qa_passed"]

        pj["gates_passed"] = gates

        with open(pj_path, "w", encoding="utf-8") as f:
            json.dump(pj, f, indent=2, ensure_ascii=False)
            f.write("\n")

    return report
