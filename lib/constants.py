"""
Shared constants for the reel pipeline.

Single source of truth for enums, gate IDs, and validation patterns.
All modules (validate, gates, qa) import from here to prevent drift.
"""

import re

# ── Schema version ─────────────────────────────────────────────────────────

CURRENT_SCHEMA_VERSION = 2

# Catalog schema version (separate from project schema version, may diverge).
CURRENT_CATALOG_SCHEMA_VERSION = 2

# ── Project types ──────────────────────────────────────────────────────────

VALID_PROJECT_TYPES = {"reel", "youtube"}

# ── Phase & Status enums (from lib/schemas/project.schema.json) ─────────────

REEL_PHASES = {
    "init", "source-brief", "theme", "script", "voice", "reconcile",
    "beat-map", "captions", "capture", "shot-list", "motion-intent",
    "asset-prep", "assembly", "preview", "qa", "render", "done",
}

YOUTUBE_PHASES = {
    "init", "ingest", "overlay-plan", "assembly", "qa", "render", "done",
}

VALID_PHASES = REEL_PHASES | YOUTUBE_PHASES

VALID_STATUSES = {
    "initialized", "in_progress", "awaiting_approval", "approved",
    "blocked", "completed", "failed",
}

VALID_STYLES = {"cinematic-presenter", "editorial-authority", "proof-escalation-editorial"}

# ── Gate IDs (from .claude/rules/gate-enforcement.md) ───────────────────────

REEL_GATE_IDS = {
    "brief_approved", "theme_set", "script_approved",
    "reconciliation_resolved", "visual_assignment_approved",
    "asset_fitness_passed", "technical_planning_approved",
    "motion_intent_reviewed", "assets_validated",
    "preview_passed", "qa_passed",
}

YOUTUBE_GATE_IDS = {
    "video_ingested", "overlay_plan_approved",
}

VALID_GATE_IDS = REEL_GATE_IDS | YOUTUBE_GATE_IDS

# Ordered for downstream cascade — resetting gate N removes all gates at index >= N
GATE_ORDER = [
    "brief_approved",
    "theme_set",
    "script_approved",
    "reconciliation_resolved",
    "visual_assignment_approved",
    "asset_fitness_passed",
    "technical_planning_approved",
    "motion_intent_reviewed",
    "assets_validated",
    "preview_passed",
    "qa_passed",
]

YOUTUBE_GATE_ORDER = [
    "video_ingested",
    "overlay_plan_approved",
]

# ── Validation patterns ─────────────────────────────────────────────────────

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
BEAT_ID_RE = re.compile(r"^beat-\d{2,}[a-z]?$")
COLOR_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

# ── Layout constants (shared by QA checks and validation) ──────────────────

WIDTH = 1080
HEIGHT = 1920
FPS = 30
SAFE_MARGIN = 64
BOTTOM_RESERVED = 300
CAPTION_MAX_WIDTH = 912       # SAFE_WIDTH (952) - 40
CAPTION_FONT_SIZE = 52
MAX_TRANSITION_DURATION = 0.3  # seconds
