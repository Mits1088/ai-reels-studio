"""
Frame renderer — composites visual layers into 1080x1920 frames using Pillow.

Renders one frame at a time. Each frame is determined by:
  - Current time position
  - Which lane entries are active at that time
  - The scene layout for the current beat
  - Transition state (if between scenes)
"""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from . import layout as L


# ── Color palette (defaults, overridden by brand kit) ────────────────────────

COLORS = {
    "bg":             (10, 10, 15),        # near-black background
    "caption_bg":     (0, 0, 0, 180),      # semi-transparent black
    "caption_text":   (255, 255, 255),      # white
    "pip_border":     (255, 255, 255),      # white circle border
    "placeholder_bg": (30, 30, 40),         # dark placeholder for missing assets
    "placeholder_fg": (100, 100, 120),      # placeholder text color
    "hook_accent":    (255, 70, 70),        # red accent for hook text
    "cta_accent":     (70, 200, 255),       # blue accent for CTA
}


# ── Asset loading ────────────────────────────────────────────────────────────

_asset_cache: dict[str, Image.Image] = {}


def load_asset(path: Path, target_size: tuple[int, int] | None = None) -> Image.Image:
    """Load and optionally resize an asset image. Caches results."""
    cache_key = f"{path}:{target_size}"
    if cache_key in _asset_cache:
        return _asset_cache[cache_key]

    if path.exists():
        img = Image.open(path).convert("RGBA")
    else:
        # Placeholder for missing assets
        img = _make_placeholder(target_size or (L.WIDTH, L.HEIGHT), path.name)

    if target_size and img.size != target_size:
        img = _fit_cover(img, target_size)

    _asset_cache[cache_key] = img
    return img


def clear_asset_cache():
    _asset_cache.clear()


def _make_placeholder(size: tuple[int, int], label: str) -> Image.Image:
    """Generate a labeled placeholder image."""
    img = Image.new("RGBA", size, COLORS["placeholder_bg"])
    draw = ImageDraw.Draw(img)
    font = _get_font(24)
    # Center the label
    text = f"[{label}]"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size[0] - tw) // 2
    y = (size[1] - th) // 2
    draw.text((x, y), text, fill=COLORS["placeholder_fg"], font=font)
    return img


def _fit_cover(img: Image.Image, target: tuple[int, int]) -> Image.Image:
    """Resize image to cover target size, cropping excess (center crop)."""
    tw, th = target
    iw, ih = img.size
    scale = max(tw / iw, th / ih)
    new_w, new_h = int(iw * scale), int(ih * scale)
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    # Center crop
    left = (new_w - tw) // 2
    top = (new_h - th) // 2
    return img.crop((left, top, left + tw, top + th))


# ── Font loading ─────────────────────────────────────────────────────────────

_font_cache: dict[int, ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}


def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Get a font at the given size. Falls back to default if no system font found."""
    if size in _font_cache:
        return _font_cache[size]

    font_paths = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for fp in font_paths:
        if Path(fp).exists():
            font = ImageFont.truetype(fp, size)
            _font_cache[size] = font
            return font

    font = ImageFont.load_default(size=size)
    _font_cache[size] = font
    return font


# ── Caption rendering ────────────────────────────────────────────────────────

def render_caption(
    frame: Image.Image,
    text: str,
    y_offset: int | None = None,
) -> Image.Image:
    """
    Render a caption with background pill onto the frame.

    Captions are placed in the mobile-safe zone above the bottom reserved area.
    """
    draw = ImageDraw.Draw(frame)
    font = _get_font(L.CAPTION_FONT_SIZE)

    # Word wrap
    lines = _wrap_text(text, font, L.CAPTION_MAX_WIDTH, draw)
    if not lines:
        return frame

    # Calculate total text block height
    line_heights = []
    line_widths = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_widths.append(bbox[2] - bbox[0])
        line_heights.append(bbox[3] - bbox[1])

    block_height = sum(line_heights) + (len(lines) - 1) * (L.CAPTION_LINE_HEIGHT - line_heights[0])
    max_width = max(line_widths)

    # Position: centered horizontally, in caption zone
    y = y_offset if y_offset is not None else L.CAPTION_Y - block_height
    x_center = L.WIDTH // 2

    # Draw background pill
    pad = L.CAPTION_BG_PADDING
    bg_left = x_center - max_width // 2 - pad
    bg_top = y - pad
    bg_right = x_center + max_width // 2 + pad
    bg_bottom = y + block_height + pad

    # Draw rounded rectangle background
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [bg_left, bg_top, bg_right, bg_bottom],
        radius=L.CAPTION_BG_RADIUS,
        fill=COLORS["caption_bg"],
    )
    frame = Image.alpha_composite(frame, overlay)

    # Draw text
    draw = ImageDraw.Draw(frame)
    current_y = y
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        tx = x_center - tw // 2
        draw.text((tx, current_y), line, fill=COLORS["caption_text"], font=font)
        current_y += L.CAPTION_LINE_HEIGHT

    return frame


def _wrap_text(text: str, font, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Simple word-wrap."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    return lines


# ── Layer compositing ────────────────────────────────────────────────────────

def render_primary(frame: Image.Image, asset: Image.Image) -> Image.Image:
    """Place asset as full-screen primary layer."""
    sized = _fit_cover(asset.copy(), (L.WIDTH, L.HEIGHT))
    frame.paste(sized, (0, 0), sized if sized.mode == "RGBA" else None)
    return frame


def render_pip(frame: Image.Image, asset: Image.Image) -> Image.Image:
    """Place asset as circular picture-in-picture overlay."""
    # Resize to PiP size
    pip = _fit_cover(asset.copy(), (L.PIP_SIZE, L.PIP_SIZE))

    # Create circular mask
    mask = Image.new("L", (L.PIP_SIZE, L.PIP_SIZE), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse([0, 0, L.PIP_SIZE, L.PIP_SIZE], fill=255)

    # Draw border circle on frame first
    frame_draw = ImageDraw.Draw(frame)
    border = 4
    frame_draw.ellipse(
        [L.PIP_X - border, L.PIP_Y - border,
         L.PIP_X + L.PIP_SIZE + border, L.PIP_Y + L.PIP_SIZE + border],
        fill=COLORS["pip_border"],
    )

    # Paste PiP with circular mask
    frame.paste(pip, (L.PIP_X, L.PIP_Y), mask)
    return frame


def render_lower_third(frame: Image.Image, asset: Image.Image) -> Image.Image:
    """Place asset in the lower third of the safe area."""
    h = L.SAFE_HEIGHT // 3
    w = L.SAFE_WIDTH
    sized = _fit_cover(asset.copy(), (w, h))
    y = L.SAFE_BOTTOM - h
    x = L.SAFE_LEFT
    frame.paste(sized, (x, y), sized if sized.mode == "RGBA" else None)
    return frame


# ── Transition rendering ────────────────────────────────────────────────────

def apply_transition(
    frame_a: Image.Image,
    frame_b: Image.Image,
    transition_type: str,
    progress: float,
) -> Image.Image:
    """
    Blend two frames according to transition type and progress (0.0 to 1.0).

    Supported: cut, fade, slide-up, slide-down
    """
    if transition_type == "cut" or progress <= 0:
        return frame_a.copy()
    if progress >= 1.0:
        return frame_b.copy()

    if transition_type == "fade":
        return Image.blend(frame_a, frame_b, progress)

    elif transition_type == "slide-up":
        result = frame_a.copy()
        offset = int(L.HEIGHT * (1.0 - progress))
        result.paste(frame_b, (0, offset))
        return result

    elif transition_type == "slide-down":
        result = frame_a.copy()
        offset = int(-L.HEIGHT * (1.0 - progress))
        result.paste(frame_b, (0, offset))
        return result

    # Fallback: crossfade
    return Image.blend(frame_a, frame_b, progress)


# ── Full frame compositor ────────────────────────────────────────────────────

def compose_frame(
    scene_type: str,
    assets_dir: Path,
    *,
    avatar_file: str | None = None,
    demo_file: str | None = None,
    support_file: str | None = None,
    caption_text: str | None = None,
) -> Image.Image:
    """
    Compose a single frame for a given scene type and active assets.

    This is the main entry point for rendering one moment in time.
    """
    from .layout import SCENE_LAYOUTS

    frame = Image.new("RGBA", (L.WIDTH, L.HEIGHT), COLORS["bg"])
    scene = SCENE_LAYOUTS.get(scene_type, SCENE_LAYOUTS["context"])

    # Layer order: primary → lower-third → pip → caption (back to front)

    # Primary layer
    primary_file = None
    if scene["avatar"] == "primary" and avatar_file:
        primary_file = avatar_file
    elif scene["demo"] == "primary" and demo_file:
        primary_file = demo_file
    elif scene["support"] == "primary" and support_file:
        primary_file = support_file

    if primary_file:
        asset = load_asset(assets_dir / primary_file, (L.WIDTH, L.HEIGHT))
        frame = render_primary(frame, asset)

    # Lower-third layer
    lower_file = None
    if scene.get("support") == "lower-third" and support_file:
        lower_file = support_file
    elif scene.get("demo") == "lower-third" and demo_file:
        lower_file = demo_file

    if lower_file:
        asset = load_asset(assets_dir / lower_file)
        frame = render_lower_third(frame, asset)

    # PiP layer
    pip_file = None
    if scene.get("avatar") == "pip" and avatar_file:
        pip_file = avatar_file
    elif scene.get("demo") == "pip" and demo_file:
        pip_file = demo_file

    if pip_file:
        asset = load_asset(assets_dir / pip_file)
        frame = render_pip(frame, asset)

    # Caption layer (always on top)
    if caption_text:
        frame = render_caption(frame, caption_text)

    return frame
