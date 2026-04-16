"""
Edit-plan dataclasses.

Mirrors lib/schemas/edit_plan.schema.json. Frozen dataclasses for immutability;
explicit from_dict / to_dict converters so the round-trip is testable.

The model deliberately separates editorial decisions (BeatPlan) from render
output (verbatim_lanes). This lets reverse-engineered plans round-trip legacy
timeline shapes exactly without losing information.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any


EDIT_PLAN_SCHEMA_VERSION = 1
COMPILER_VERSION = "lib.edit_plan.compile@1.0.0"


# ── Sub-records ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CandidateAsset:
    asset_id: str
    score: float
    reason: str

    @classmethod
    def from_dict(cls, d: dict) -> "CandidateAsset":
        return cls(
            asset_id=str(d["asset_id"]),
            score=float(d["score"]),
            reason=str(d["reason"]),
        )

    def to_dict(self) -> dict:
        return {"asset_id": self.asset_id, "score": self.score, "reason": self.reason}


@dataclass(frozen=True)
class MotionEvent:
    kind: str
    preset: str | None = None
    duration_frames: int | None = None

    @classmethod
    def from_dict(cls, d: dict) -> "MotionEvent":
        return cls(
            kind=str(d["kind"]),
            preset=d.get("preset"),
            duration_frames=d.get("duration_frames"),
        )

    def to_dict(self) -> dict:
        out: dict[str, Any] = {"kind": self.kind}
        if self.preset is not None:
            out["preset"] = self.preset
        if self.duration_frames is not None:
            out["duration_frames"] = self.duration_frames
        return out


@dataclass(frozen=True)
class MotionBudget:
    hero: MotionEvent
    support: MotionEvent | None = None
    accent: MotionEvent | None = None

    @classmethod
    def from_dict(cls, d: dict) -> "MotionBudget":
        if "hero" not in d:
            raise ValueError("motion_budget.hero is required")
        return cls(
            hero=MotionEvent.from_dict(d["hero"]),
            support=MotionEvent.from_dict(d["support"]) if d.get("support") else None,
            accent=MotionEvent.from_dict(d["accent"]) if d.get("accent") else None,
        )

    def to_dict(self) -> dict:
        out: dict[str, Any] = {"hero": self.hero.to_dict()}
        if self.support is not None:
            out["support"] = self.support.to_dict()
        if self.accent is not None:
            out["accent"] = self.accent.to_dict()
        return out


@dataclass(frozen=True)
class ZoomMoment:
    at: float
    x: float
    y: float
    scale: float
    holdFor: float | None = None

    @classmethod
    def from_dict(cls, d: dict) -> "ZoomMoment":
        return cls(
            at=float(d["at"]),
            x=float(d["x"]),
            y=float(d["y"]),
            scale=float(d["scale"]),
            holdFor=float(d["holdFor"]) if d.get("holdFor") is not None else None,
        )

    def to_dict(self) -> dict:
        out: dict[str, Any] = {"at": self.at, "x": self.x, "y": self.y, "scale": self.scale}
        if self.holdFor is not None:
            out["holdFor"] = self.holdFor
        return out


# ── BeatPlan ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BeatPlan:
    """Editorial decisions for one beat.

    The mandatory Phase D fields (candidate_assets, selected_asset_id,
    selection_confidence, selection_reason, fallback_asset_ids,
    human_review_required) are required by the schema and the validator.

    selected_asset_filename is the catalog-free hint: when set, the compiler
    uses it directly. When absent, the compiler walks the catalog using
    selected_asset_id.

    render_overrides is a free-form dict that the compiler attaches verbatim
    to the emitted content lane entry. Used by reverse-engineering to capture
    render-only fields (transition_preset, display, clipStartTime, etc.)
    that the editorial schema does not model.
    """

    # Identification + editorial
    beat_id: str
    template_id: str
    avatar_mode: str
    caption_mode: str
    split_ratio: str

    # Phase D mandatory asset selection fields
    candidate_assets: tuple[CandidateAsset, ...]
    selected_asset_id: str | None
    selection_confidence: float
    selection_reason: str
    fallback_asset_ids: tuple[str, ...]
    human_review_required: bool

    # Motion + rationale
    motion_budget: MotionBudget
    rationale: str

    # Optional editorial extras
    proof_class: str | None = None
    proof_protected: bool = False
    notes: str | None = None

    # Catalog-free hint
    selected_asset_filename: str | None = None

    # Render hints
    zoom_moments: tuple[ZoomMoment, ...] = ()
    playback_rate: float | None = None
    render_overrides: dict | None = None

    @classmethod
    def from_dict(cls, d: dict) -> "BeatPlan":
        return cls(
            beat_id=str(d["beat_id"]),
            template_id=str(d["template_id"]),
            avatar_mode=str(d["avatar_mode"]),
            caption_mode=str(d["caption_mode"]),
            split_ratio=str(d["split_ratio"]),
            candidate_assets=tuple(
                CandidateAsset.from_dict(c) for c in d.get("candidate_assets", [])
            ),
            selected_asset_id=d.get("selected_asset_id"),
            selection_confidence=float(d["selection_confidence"]),
            selection_reason=str(d.get("selection_reason", "")),
            fallback_asset_ids=tuple(d.get("fallback_asset_ids", [])),
            human_review_required=bool(d.get("human_review_required", False)),
            motion_budget=MotionBudget.from_dict(d["motion_budget"]),
            rationale=str(d.get("rationale", "")),
            proof_class=d.get("proof_class"),
            proof_protected=bool(d.get("proof_protected", False)),
            notes=d.get("notes"),
            selected_asset_filename=d.get("selected_asset_filename"),
            zoom_moments=tuple(
                ZoomMoment.from_dict(z) for z in d.get("zoom_moments", [])
            ),
            playback_rate=d.get("playback_rate"),
            render_overrides=d.get("render_overrides"),
        )

    def to_dict(self) -> dict:
        out: dict[str, Any] = {
            "beat_id": self.beat_id,
            "template_id": self.template_id,
            "avatar_mode": self.avatar_mode,
            "caption_mode": self.caption_mode,
            "split_ratio": self.split_ratio,
            "candidate_assets": [c.to_dict() for c in self.candidate_assets],
            "selected_asset_id": self.selected_asset_id,
            "selection_confidence": self.selection_confidence,
            "selection_reason": self.selection_reason,
            "fallback_asset_ids": list(self.fallback_asset_ids),
            "human_review_required": self.human_review_required,
            "motion_budget": self.motion_budget.to_dict(),
            "rationale": self.rationale,
        }
        if self.proof_class is not None:
            out["proof_class"] = self.proof_class
        if self.proof_protected:
            out["proof_protected"] = True
        if self.notes is not None:
            out["notes"] = self.notes
        if self.selected_asset_filename is not None:
            out["selected_asset_filename"] = self.selected_asset_filename
        if self.zoom_moments:
            out["zoom_moments"] = [z.to_dict() for z in self.zoom_moments]
        if self.playback_rate is not None:
            out["playback_rate"] = self.playback_rate
        if self.render_overrides is not None:
            out["render_overrides"] = dict(self.render_overrides)
        return out


# ── EditPlan (top-level) ──────────────────────────────────────────────────


@dataclass(frozen=True)
class EditPlan:
    schema_version: int
    project_slug: str
    beats: tuple[BeatPlan, ...]
    # style is optional so reverse-engineered plans can faithfully round-trip
    # legacy timelines that have no style field at the top level. New plans
    # produced by Phase D's planner should always set this.
    style: str | None = None
    generated_at: str | None = None
    compiler_version: str | None = None
    audio: str | None = None
    avatar_file: str | None = None
    project: str | None = None
    total_duration: float | None = None
    meta: dict | None = None
    verbatim_lanes: dict | None = None  # {lane_name: [entry, ...]}

    @classmethod
    def from_dict(cls, d: dict) -> "EditPlan":
        if "beats" not in d or not isinstance(d["beats"], list):
            raise ValueError("edit-plan.beats is required and must be a list")
        style = d.get("style")
        return cls(
            schema_version=int(d.get("schema_version", EDIT_PLAN_SCHEMA_VERSION)),
            project_slug=str(d["project_slug"]),
            style=str(style) if style is not None else None,
            beats=tuple(BeatPlan.from_dict(b) for b in d["beats"]),
            generated_at=d.get("generated_at"),
            compiler_version=d.get("compiler_version"),
            audio=d.get("audio"),
            avatar_file=d.get("avatar_file"),
            project=d.get("project"),
            total_duration=d.get("total_duration"),
            meta=d.get("meta"),
            verbatim_lanes=d.get("verbatim_lanes"),
        )

    def to_dict(self) -> dict:
        out: dict[str, Any] = {
            "schema_version": self.schema_version,
            "project_slug": self.project_slug,
            "beats": [b.to_dict() for b in self.beats],
        }
        if self.style is not None:
            out["style"] = self.style
        if self.generated_at is not None:
            out["generated_at"] = self.generated_at
        if self.compiler_version is not None:
            out["compiler_version"] = self.compiler_version
        if self.audio is not None:
            out["audio"] = self.audio
        if self.avatar_file is not None:
            out["avatar_file"] = self.avatar_file
        if self.project is not None:
            out["project"] = self.project
        if self.total_duration is not None:
            out["total_duration"] = self.total_duration
        if self.meta is not None:
            out["meta"] = dict(self.meta)
        if self.verbatim_lanes is not None:
            out["verbatim_lanes"] = {
                lane: list(entries) for lane, entries in self.verbatim_lanes.items()
            }
        return out

    def beat_by_id(self, beat_id: str) -> BeatPlan | None:
        for b in self.beats:
            if b.beat_id == beat_id:
                return b
        return None
