# Editorial Authority — Component Build Spec

Components needed for the editorial-authority style. Build these before using the style on a project.

---

## P0 — Core (must build first)

### HeroTextCard

Large center-weighted text on a solid color background. The primary visual element of this style.

**Props:**
- `text: string` — the hero word(s)
- `durationInFrames: number`
- `backgroundColor: string` — solid color or simple gradient
- `textColor?: string` — default white
- `fontSize?: number` — default 120
- `withOvershoot?: boolean` — default true (scale 0.85 → 1.03 → 1.0)
- `shadowStrength?: "none" | "subtle" | "strong"` — default "subtle"

**Motion:**
- Entry: spring scale 0.85 → 1.03 → 1.0 over 5 frames (overshoot settle)
- Hold: completely static — no breathe, no drift
- Exit: instant opacity 1 → 0 in 1 frame (hard cut)

**Layout:**
- AbsoluteFill with flexbox center/center
- Text fills ~70% of frame width max
- If text is too long, reduce fontSize automatically

**Reference:** 0:00 "Paying for AI Tools", 2:7 "WRONG", 14:93 chapter titles

**Existing similar:** `PunchText` — but PunchText has echo ripples and glow which are too cinematic. HeroTextCard is intentionally simpler: just big text, slight overshoot, done.

---

### FlashReset

2-3 frame white flash transition between major sections.

**Props:**
- `durationInFrames?: number` — default 3
- `color?: string` — default "#FFFFFF"
- `peakOpacity?: number` — default 1.0

**Motion:**
- Frame 0: opacity 0
- Frame 1: opacity → peakOpacity
- Frame 2: opacity → peakOpacity * 0.6
- Frame 3: opacity → 0

**Usage:** placed as an overlay between sections. Not a component wrapper — it's a standalone element in a `<Sequence>`.

**Existing similar:** `PunchText` has a white flash built in, but it's tied to the text slam. FlashReset is standalone and reusable.

---

## P1 — Important

### CursorClick

Cursor icon with click ripple animation at a specified coordinate.

**Props:**
- `x: number` — percentage position (0-100)
- `y: number` — percentage position (0-100)
- `durationInFrames: number`
- `cursorDelay?: number` — frames before cursor appears (default 0)
- `clickFrame?: number` — frame when click ripple fires (default 8)
- `cursorColor?: string` — default black
- `rippleColor?: string` — default "rgba(0,0,0,0.15)"

**Motion:**
- Cursor fades in at position (3 frames)
- Optional slight drift to position if `cursorDelay > 0`
- Click ripple: expanding circle from cursor tip, 0 → 40px radius, opacity 0.4 → 0 over 8 frames
- Cursor holds briefly, then fades out

**Reference:** cursor-click overlays on buttons in the reference video

---

### ComparisonGrid

Side-by-side screenshot layout with optional VS divider.

**Props:**
- `leftImage: string` — staticFile path
- `rightImage: string` — staticFile path
- `leftLabel?: string`
- `rightLabel?: string`
- `dividerType?: "vs" | "line" | "none"` — default "vs"
- `durationInFrames: number`

**Layout:**
- Full frame, split vertically (left 48% | divider 4% | right 48%)
- Images use objectFit: "cover" within their half
- Labels below each image, 24px, bold
- VS circle or thin line between

**Motion:**
- Entry: both images scale 0.95 → 1.0 (3 frames)
- Hold: static
- Exit: hard cut (instant)

**Reference:** 18:83 comparison thumbnails, side-by-side throughout

---

### StackedNumberCards → IMPLEMENTED as CardStack `variant="editorial"`

**Status:** Built. Not a separate component — implemented as the `editorial` variant of the existing `CardStack` component.

Use `<CardStack variant="editorial" items={[...]} />` to get:
- White card backgrounds (not dark translucent)
- Number badges on left (colored)
- Rotation on entry (8deg → 0deg spring)
- Overlapping card layout (margin-top: -8px)
- Stronger spring (damping 12, stiffness 160)

**Reference:** 3:37-5:10 numbered cards stacking in Lindsay.ai video

---

### OverlayKeyword

Large word placed over the talking-head video at chest level.

**Props:**
- `text: string`
- `durationInFrames: number`
- `color?: string` — default white
- `fontSize?: number` — default 72
- `position?: "center" | "center-top" | "center-bottom"` — default "center"
- `withStrikethrough?: boolean` — default false
- `strikethroughColor?: string` — default "#DC2626"
- `strikethroughDelay?: number` — frames before line draws (default 10)

**Motion:**
- Entry: scale 0.9 → 1.0 with spring (4 frames)
- Hold: static
- If `withStrikethrough`: red line wipes left-to-right across the word via clipPath
- Exit: hard cut

**Note:** This is simpler than `StrikethroughSwap` which does old→new replacement. OverlayKeyword just shows a word (optionally struck through) on top of whatever is behind it. It's designed to layer ON the avatar, not replace content.

**Reference:** 32:27-35:03 "SUBSCRIPTION" with strikethrough, "JUST YOUR MACHINE"

---

## P2 — Nice to Have

### AnnotationCircle

Hand-drawn-style circle drawn around a UI element to call attention.

**Props:**
- `x: number` — center percentage (0-100)
- `y: number` — center percentage (0-100)
- `radiusX?: number` — horizontal radius in px (default 60)
- `radiusY?: number` — vertical radius in px (default 40)
- `color?: string` — default "#22C55E" (green)
- `strokeWidth?: number` — default 3
- `drawDuration?: number` — frames to draw the circle (default 10)
- `durationInFrames: number`

**Motion:**
- Circle draws via SVG stroke-dashoffset animation (frame-driven, not CSS)
- Slight wobble in the path for hand-drawn feel (randomized control points)
- Holds after drawn
- Fades out at end (4 frames)

**Reference:** 30:73 green oval annotations on buttons

---

### ChapterDivider

Logo + wordmark centered on white, gentle scale entrance.

**Props:**
- `logoSrc?: string` — staticFile path to logo image
- `title: string` — wordmark / section title
- `durationInFrames: number`
- `backgroundColor?: string` — default "#FFFFFF"

**Layout:**
- White (or solid color) AbsoluteFill
- Logo centered, 80-120px
- Title below logo, 32px, Inter 600, dark text
- Generous whitespace

**Motion:**
- Entry: opacity 0→1 + scale 0.95→1.0 (6 frames, eased)
- Hold: static
- Exit: opacity 1→0 (4 frames)

**Reference:** 14:93 laurel symbol + branding, 25:23 Pinokio icon + wordmark

---

## Existing Components — Style Variants Needed

### CardStack variant

The existing `CardStack` component works for lists but needs a style variant for editorial-authority:
- White/light card backgrounds instead of dark translucent
- Bold number badge on left instead of icon
- No backdrop-blur (too cinematic)
- Rotation on entry

**Approach:** Add a `variant?: "cinematic" | "editorial"` prop rather than building StackedNumberCards from scratch. The existing spring + stagger logic is reusable.

### AvatarVideo crop preset

Editorial-authority needs tighter avatar cropping. Add a `cropPreset?: "standard" | "tight"` prop:
- `standard`: current behavior
- `tight`: objectPosition shifted to show head + shoulders only, slight scale up (1.1x)

---

## Build Order

1. `HeroTextCard` + `FlashReset` (P0 — unlocks the style) — BUILT
2. `OverlayKeyword` + CardStack editorial variant (P1 — core editorial beats) — BUILT
3. `ComparisonGrid` + `CursorClick` (P1 — proof enhancement) — BUILT
4. `AnnotationCircle` + `ChapterDivider` (P2 — polish) — BUILT
5. `ScrollingIconGrid` (hook backgrounds — Lindsay.ai reference) — BUILT

**All editorial-authority components are built and ready for use.**

## Transition Preset Implementation

Add to `remotion/src/components/transitions/presets.ts`:

### hard-cut
- enterDur: 0, exitDur: 0
- No interpolation — element simply appears/disappears with the Sequence

### scale-pop-overshoot
- scale: 0.85 → 1.03 → 1.0
- Use spring with config: { damping: 12, stiffness: 300, mass: 0.6 }
- Duration: 5 frames

### flash-reset
- Not a transition on an element — it's a standalone overlay
- Implemented as the `FlashReset` component placed in its own Sequence
- 2-3 frames, white full-screen

### slide-stack
- translateX: 400 → 0 with spring
- rotate: 8deg → 0deg
- Duration: 6 frames
- Used on card elements, not general content
