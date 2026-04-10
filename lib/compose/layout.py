"""
Layout constants and safe zone definitions for 1080x1920 vertical reels.

All measurements in pixels unless noted.
"""

# ── Canvas ───────────────────────────────────────────────────────────────────

WIDTH = 1080
HEIGHT = 1920
ASPECT = (9, 16)
FPS = 30

# ── Safe zones ───────────────────────────────────────────────────────────────

SAFE_MARGIN = 64           # inset on all sides for platform UI overlays
BOTTOM_RESERVED = 300      # reserved for captions/CTA (Instagram UI)

SAFE_LEFT = SAFE_MARGIN
SAFE_TOP = SAFE_MARGIN
SAFE_RIGHT = WIDTH - SAFE_MARGIN
SAFE_BOTTOM = HEIGHT - BOTTOM_RESERVED

SAFE_WIDTH = SAFE_RIGHT - SAFE_LEFT       # 952
SAFE_HEIGHT = SAFE_BOTTOM - SAFE_TOP      # 1556

# ── Caption zone ─────────────────────────────────────────────────────────────

CAPTION_Y = HEIGHT - BOTTOM_RESERVED - 40   # just above bottom reserved
CAPTION_MAX_WIDTH = SAFE_WIDTH - 40         # some breathing room
CAPTION_FONT_SIZE = 52
CAPTION_LINE_HEIGHT = 64
CAPTION_BG_PADDING = 16
CAPTION_BG_RADIUS = 12

# ── Avatar PiP (picture-in-picture during demo scenes) ───────────────────────

PIP_SIZE = 280                          # diameter of circular PiP
PIP_MARGIN = 24                         # from safe edge
PIP_X = WIDTH - SAFE_MARGIN - PIP_SIZE - PIP_MARGIN
PIP_Y = HEIGHT - BOTTOM_RESERVED - PIP_SIZE - PIP_MARGIN

# ── Scene layouts ────────────────────────────────────────────────────────────

# Each scene type defines which lanes are visible and how they're arranged.
# "primary" = fills the canvas, "pip" = small overlay, "hidden" = not shown.

SCENE_LAYOUTS = {
    "hook": {
        "avatar": "primary",
        "demo": "hidden",
        "support": "hidden",
        "description": "Avatar fullscreen with bold text overlay",
    },
    "context": {
        "avatar": "primary",
        "demo": "hidden",
        "support": "lower-third",
        "description": "Avatar with context text or support visual in lower area",
    },
    "demo": {
        "avatar": "pip",
        "demo": "primary",
        "support": "hidden",
        "description": "Demo footage fills screen, avatar shrinks to PiP circle",
    },
    "proof": {
        "avatar": "pip",
        "demo": "hidden",
        "support": "primary",
        "description": "Support visual (chart, screenshot, testimonial) fills screen",
    },
    "news-hit": {
        "avatar": "hidden",
        "demo": "hidden",
        "support": "primary",
        "description": "Full-screen support visual with text overlay",
    },
    "cta": {
        "avatar": "primary",
        "demo": "hidden",
        "support": "lower-third",
        "description": "Avatar with CTA text and optional support graphic",
    },
}

# ── Transition defaults ──────────────────────────────────────────────────────

DEFAULT_TRANSITION = {"type": "cut", "duration": 0.0}
MAX_TRANSITION_DURATION = 0.3  # seconds
