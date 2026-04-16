"""
Critic runner — loads project artifacts gracefully, runs the 6 checks,
post-processes findings (linking + summary), and aggregates into a CriticReport.

Phase E2 additions:
  - Computes catalog enrichment state and passes it to checks that need it
    (proof_relevance, caption_competition) so they can dedup data-gap noise.
  - Post-processes findings to link related ones (asset_overreuse +
    visual_novelty + dead_holds about the same asset get cross-referenced).
  - Builds a top-level summary section: data_quality_limitations,
    root_cause_clusters, highest_confidence_blockers.
  - Computes critic_status (critic_passed / critic_warnings / critic_blocked).
  - Supports severity_floor filtering (totals show pre-filter counts so the
    audit trail is preserved).

Still advisory only — the runner produces structured output but exits 0
regardless of severity. Phase E3 will add gating behavior.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lib.capture.catalog import Catalog, load_catalog

from .finding import (
    CriticFinding,
    SEVERITY_BLOCK,
    SEVERITY_WARN,
    SEVERITY_SUGGEST,
)
from .checks import (
    CHECK_REGISTRY,
    check_claim_to_proof_latency,
    check_dead_holds,
    check_asset_overreuse,
    check_proof_relevance,
    check_caption_competition,
    check_visual_novelty,
)


CRITIC_VERSION = "lib.critic@1.1.0-advisory"

VERDICT_PASS = "advisory_pass"
VERDICT_WARNINGS = "advisory_warnings"
VERDICT_BLOCKED = "advisory_blocked"

# Phase E2 — soft project-level status (informational, file-only, NOT in project.json).
# Phase E2.5: STATUS_UNAVAILABLE distinguishes "critic could not form an opinion"
# (required inputs missing) from "critic ran and found nothing" (critic_passed).
# This matters once status is wired into anything downstream.
STATUS_PASSED = "critic_passed"
STATUS_WARNINGS = "critic_warnings"
STATUS_BLOCKED = "critic_blocked"
STATUS_UNAVAILABLE = "critic_unavailable"

# Inputs the critic considers "required" before it claims an opinion. Without
# beat_map there is nothing to analyze; without asset_matches the editorial
# checks have no asset selections to reason about. With both present, the
# critic can produce a meaningful pass/warn/block verdict.
_REQUIRED_INPUTS = ("beat_map", "asset_matches")

# Severity ordering for filter floor
_SEVERITY_RANK = {
    SEVERITY_SUGGEST: 0,
    SEVERITY_WARN:    1,
    SEVERITY_BLOCK:   2,
}


# ── CriticReport ──────────────────────────────────────────────────────────


@dataclass
class CriticReport:
    project: str
    findings: list[CriticFinding]
    inputs_present: dict[str, bool] = field(default_factory=dict)
    enrichment_state: dict[str, int] = field(default_factory=dict)
    severity_floor: str = SEVERITY_SUGGEST
    # Pre-filter totals (preserved when severity_floor filters out findings)
    pre_filter_total: int = 0
    pre_filter_blockers: int = 0
    pre_filter_warnings: int = 0
    pre_filter_suggestions: int = 0
    # Phase E2.5: number of beats with a non-null selected_asset_id. When 0,
    # the critic has nothing meaningful to analyze even if the matches file exists.
    selected_match_count: int = 0

    @property
    def blockers(self) -> list[CriticFinding]:
        return [f for f in self.findings if f.severity == SEVERITY_BLOCK]

    @property
    def warnings(self) -> list[CriticFinding]:
        return [f for f in self.findings if f.severity == SEVERITY_WARN]

    @property
    def suggestions(self) -> list[CriticFinding]:
        return [f for f in self.findings if f.severity == SEVERITY_SUGGEST]

    @property
    def verdict(self) -> str:
        # Verdict reflects the pre-filter state (the actual editorial situation)
        if self.pre_filter_blockers > 0:
            return VERDICT_BLOCKED
        if self.pre_filter_warnings > 0:
            return VERDICT_WARNINGS
        return VERDICT_PASS

    @property
    def critic_status(self) -> str:
        # Phase E2.5: distinguish "no findings because clean" from
        # "no findings because the critic couldn't form an opinion".
        for required in _REQUIRED_INPUTS:
            if not self.inputs_present.get(required, False):
                return STATUS_UNAVAILABLE
        # Even when asset-matches.json exists, if no beat has a selected
        # asset (e.g. catalog was empty), the critic has nothing to analyze.
        if self.selected_match_count == 0:
            return STATUS_UNAVAILABLE
        if self.pre_filter_blockers > 0:
            return STATUS_BLOCKED
        if self.pre_filter_warnings > 0:
            return STATUS_WARNINGS
        return STATUS_PASSED

    def per_check_totals(self) -> dict[str, dict[str, int]]:
        out: dict[str, dict[str, int]] = {}
        for check_name in CHECK_REGISTRY.keys():
            out[check_name] = {"blockers": 0, "warnings": 0, "suggestions": 0}
        for f in self.findings:
            bucket = out.setdefault(f.check, {"blockers": 0, "warnings": 0, "suggestions": 0})
            if f.severity == SEVERITY_BLOCK:
                bucket["blockers"] += 1
            elif f.severity == SEVERITY_WARN:
                bucket["warnings"] += 1
            elif f.severity == SEVERITY_SUGGEST:
                bucket["suggestions"] += 1
        return out

    def per_beat_findings(self) -> dict[str, list[CriticFinding]]:
        out: dict[str, list[CriticFinding]] = {}
        for f in self.findings:
            if f.beat_id:
                out.setdefault(f.beat_id, []).append(f)
        return out

    def to_dict(self) -> dict:
        per_check = self.per_check_totals()
        per_beat = self.per_beat_findings()
        global_findings = [f for f in self.findings if f.beat_id is None]

        return {
            "schema_version": 1,
            "project": self.project,
            "critic_version": CRITIC_VERSION,
            "advisory": True,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "verdict": self.verdict,
            "critic_status": self.critic_status,
            "severity_floor": self.severity_floor,
            "totals": {
                "blockers":    len(self.blockers),
                "warnings":    len(self.warnings),
                "suggestions": len(self.suggestions),
                "total":       len(self.findings),
                "pre_filter": {
                    "blockers":    self.pre_filter_blockers,
                    "warnings":    self.pre_filter_warnings,
                    "suggestions": self.pre_filter_suggestions,
                    "total":       self.pre_filter_total,
                },
            },
            "checks": {
                name: {
                    "description": CHECK_REGISTRY[name],
                    **per_check.get(name, {"blockers": 0, "warnings": 0, "suggestions": 0}),
                }
                for name in CHECK_REGISTRY
            },
            "inputs_present": dict(self.inputs_present),
            "enrichment_state": dict(self.enrichment_state),
            "summary": {
                "data_quality_limitations": _build_data_quality_limitations(
                    self.inputs_present, self.enrichment_state,
                ),
                "root_cause_clusters": _build_root_cause_clusters(self.findings),
                "highest_confidence_blockers": _highest_confidence_blockers(self.findings),
            },
            "beats": [
                {
                    "beat_id":  beat_id,
                    "findings": [f.to_dict() for f in beat_findings],
                }
                for beat_id, beat_findings in sorted(per_beat.items())
            ],
            "global_findings": [f.to_dict() for f in global_findings],
        }


# ── Enrichment state ─────────────────────────────────────────────────────


def _enrichment_state(catalog: Catalog | None) -> dict[str, int]:
    """Return counts: full / partial / none / total across the catalog."""
    if not catalog or not getattr(catalog, "assets", None):
        return {"full": 0, "partial": 0, "none": 0, "total": 0}
    counts = {"full": 0, "partial": 0, "none": 0}
    for a in catalog.assets:
        e = getattr(a, "enrichment", None)
        if isinstance(e, dict) and e.get("status") == "full":
            counts["full"] += 1
        elif isinstance(e, dict) and e.get("status") == "partial":
            counts["partial"] += 1
        else:
            counts["none"] += 1
    counts["total"] = sum(counts.values())
    return counts


def _is_enrichment_globally_absent(state: dict[str, int]) -> bool:
    return state["total"] > 0 and (state["full"] + state["partial"]) == 0


# ── Related-finding linker ───────────────────────────────────────────────


def _link_related_findings(findings: list[CriticFinding]) -> list[CriticFinding]:
    """Cross-reference findings that share the same asset_id in evidence.

    Each finding gets a `related_ids` tuple containing the IDs of the other
    findings about the same asset. This lets the markdown report (and any
    consumer) collapse asset_overreuse + visual_novelty + dead_holds for the
    same asset into a single root-cause cluster.
    """
    by_asset: dict[str, list[CriticFinding]] = {}
    for f in findings:
        asset_id = f.evidence.get("asset_id")
        if asset_id:
            by_asset.setdefault(asset_id, []).append(f)

    new_findings: list[CriticFinding] = []
    for f in findings:
        asset_id = f.evidence.get("asset_id")
        if asset_id and len(by_asset[asset_id]) > 1:
            related = tuple(
                other.finding_id
                for other in by_asset[asset_id]
                if other.finding_id and other.finding_id != f.finding_id
            )
            new_findings.append(replace(f, related_ids=related))
        else:
            new_findings.append(f)
    return new_findings


# ── Summary section builders ─────────────────────────────────────────────


def _build_data_quality_limitations(
    inputs_present: dict[str, bool],
    enrichment_state: dict[str, int],
) -> list[str]:
    notes: list[str] = []

    if not inputs_present.get("edit_plan"):
        notes.append(
            "edit-plan.json is absent — dead_holds severity is downshifted "
            "because zoom intent cannot be confirmed"
        )

    total = enrichment_state.get("total", 0)
    full_or_partial = enrichment_state.get("full", 0) + enrichment_state.get("partial", 0)
    if total > 0 and full_or_partial == 0:
        notes.append(
            f"Catalog enrichment is globally absent ({total} assets, 0 enriched) — "
            f"proof_relevance and caption_competition emit one global SUGGEST instead "
            f"of per-beat findings"
        )
    elif total > 0 and full_or_partial < total:
        notes.append(
            f"Catalog enrichment is partial ({full_or_partial}/{total} assets enriched) — "
            f"some beats may have lower-confidence findings"
        )

    if not inputs_present.get("asset_matches"):
        notes.append(
            "asset-matches.json is absent — most checks emit SUGGEST findings noting the data gap"
        )
    if not inputs_present.get("motion_plan"):
        notes.append(
            "motion-plan.json is absent — beat category context is unavailable"
        )

    return notes


def _build_root_cause_clusters(findings: list[CriticFinding]) -> list[dict]:
    """Group findings by shared asset_id into root-cause clusters."""
    by_asset: dict[str, list[CriticFinding]] = {}
    for f in findings:
        asset_id = f.evidence.get("asset_id")
        if asset_id:
            by_asset.setdefault(asset_id, []).append(f)

    clusters: list[dict] = []
    cluster_index = 0
    # Sort by asset_id for deterministic cluster IDs
    for asset_id in sorted(by_asset.keys()):
        group = by_asset[asset_id]
        if len(group) < 2:
            continue
        cluster_index += 1
        max_severity = _max_severity_in(group)
        max_confidence = max((f.confidence for f in group), default=0.0)
        clusters.append({
            "cluster_id": f"cluster-{cluster_index:02d}",
            "asset_id":   asset_id,
            "root_cause": (
                f"Asset {asset_id!r} flagged across {len(group)} findings from "
                f"{len(set(f.check for f in group))} different checks"
            ),
            "finding_ids":   [f.finding_id for f in group if f.finding_id],
            "checks_involved": sorted(set(f.check for f in group)),
            "max_severity":   max_severity,
            "max_confidence": round(max_confidence, 4),
        })
    return clusters


def _max_severity_in(findings: list[CriticFinding]) -> str:
    rank = max((_SEVERITY_RANK.get(f.severity, 0) for f in findings), default=0)
    for sev, r in _SEVERITY_RANK.items():
        if r == rank:
            return sev
    return SEVERITY_SUGGEST


def _highest_confidence_blockers(findings: list[CriticFinding], limit: int = 5) -> list[dict]:
    blockers = sorted(
        (f for f in findings if f.severity == SEVERITY_BLOCK),
        key=lambda f: -f.confidence,
    )
    return [
        {
            "finding_id":  f.finding_id,
            "check":       f.check,
            "beat_id":     f.beat_id,
            "confidence":  round(f.confidence, 4),
            "reason":      f.reason,
            "related_ids": list(f.related_ids),
        }
        for f in blockers[:limit]
    ]


# ── Severity filtering ───────────────────────────────────────────────────


def _apply_severity_floor(
    findings: list[CriticFinding], floor: str
) -> list[CriticFinding]:
    """Return only findings whose severity is >= floor."""
    if floor not in _SEVERITY_RANK:
        return findings
    floor_rank = _SEVERITY_RANK[floor]
    return [f for f in findings if _SEVERITY_RANK.get(f.severity, 0) >= floor_rank]


# ── Runner ────────────────────────────────────────────────────────────────


def run_critic(
    beat_map: dict | None,
    asset_matches: dict | None,
    motion_plan: dict | None,
    gap_ownership: dict | None,
    edit_plan: dict | None,
    catalog: Catalog | None,
    project_slug: str = "",
    severity_floor: str = SEVERITY_SUGGEST,
) -> CriticReport:
    """Pure function. Run all 6 checks against the supplied inputs."""
    beats = (beat_map or {}).get("beats", [])
    matches = (asset_matches or {}).get("beats")
    motion_beats = (motion_plan or {}).get("beats")

    enrichment_state = _enrichment_state(catalog)
    enrichment_globally_absent = _is_enrichment_globally_absent(enrichment_state)

    findings: list[CriticFinding] = []
    findings.extend(check_claim_to_proof_latency(beats, matches, motion_beats))
    findings.extend(check_dead_holds(beats, matches, edit_plan))
    findings.extend(check_asset_overreuse(matches))
    findings.extend(check_proof_relevance(
        beats, matches, catalog,
        enrichment_globally_absent=enrichment_globally_absent,
    ))
    findings.extend(check_caption_competition(
        beats, matches, catalog, edit_plan,
        enrichment_globally_absent=enrichment_globally_absent,
    ))
    findings.extend(check_visual_novelty(matches))

    # Phase E2: cross-link related findings BEFORE filtering, so the filtered
    # report still has correct related_ids pointing at filtered-out findings
    findings = _link_related_findings(findings)

    # Capture pre-filter totals so the verdict + critic_status reflect the
    # full editorial state, even when severity_floor hides some findings
    pre_blockers    = sum(1 for f in findings if f.severity == SEVERITY_BLOCK)
    pre_warnings    = sum(1 for f in findings if f.severity == SEVERITY_WARN)
    pre_suggestions = sum(1 for f in findings if f.severity == SEVERITY_SUGGEST)
    pre_total       = len(findings)

    findings = _apply_severity_floor(findings, severity_floor)

    # Phase E2.5: count beats with a real selection so critic_status can
    # distinguish "matched and clean" from "matcher had nothing to pick from"
    selected_match_count = 0
    if matches:
        selected_match_count = sum(1 for m in matches if m.get("selected_asset_id"))

    return CriticReport(
        project=project_slug,
        findings=findings,
        inputs_present={
            "beat_map":      beat_map is not None,
            "asset_matches": asset_matches is not None,
            "motion_plan":   motion_plan is not None,
            "gap_ownership": gap_ownership is not None,
            "edit_plan":     edit_plan is not None,
            "catalog":       catalog is not None,
        },
        enrichment_state=enrichment_state,
        severity_floor=severity_floor,
        pre_filter_total=pre_total,
        pre_filter_blockers=pre_blockers,
        pre_filter_warnings=pre_warnings,
        pre_filter_suggestions=pre_suggestions,
        selected_match_count=selected_match_count,
    )


def _load_optional(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def run_critic_for_project(
    project_dir: Path,
    severity_floor: str = SEVERITY_SUGGEST,
) -> dict:
    """Project-level entry. Reads files and returns the critic report dict."""
    bm  = _load_optional(project_dir / "audio" / "beat-map.json")
    am  = _load_optional(project_dir / "output" / "asset-matches.json")
    mp  = _load_optional(project_dir / "output" / "motion-plan.json")
    go  = _load_optional(project_dir / "output" / "gap-ownership.json")
    ep  = _load_optional(project_dir / "output" / "edit-plan.json")

    cat_path = project_dir / "assets" / "catalog.json"
    catalog = load_catalog(cat_path) if cat_path.exists() else None

    report = run_critic(
        beat_map=bm,
        asset_matches=am,
        motion_plan=mp,
        gap_ownership=go,
        edit_plan=ep,
        catalog=catalog,
        project_slug=project_dir.name,
        severity_floor=severity_floor,
    )
    return report.to_dict()


def build_critic_status_dict(report_dict: dict) -> dict:
    """Slim subset of the full report — written to output/critic-status.json.

    Phase E2: this lives as a separate file (NOT in project.json) so the
    write path is reversible and isolated from project migration logic.
    """
    return {
        "schema_version": 1,
        "project":         report_dict["project"],
        "critic_version":  report_dict["critic_version"],
        "generated_at":    report_dict["generated_at"],
        "advisory":        True,
        "critic_status":   report_dict["critic_status"],
        "verdict":         report_dict["verdict"],
        "totals":          report_dict["totals"],
        "data_quality_limitations":
            report_dict.get("summary", {}).get("data_quality_limitations", []),
        "highest_confidence_blockers":
            report_dict.get("summary", {}).get("highest_confidence_blockers", []),
    }
