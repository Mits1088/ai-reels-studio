---
description: Visual and layout standards for vertical reels — display modes, backgrounds, effects, and punch-in zoom technical spec
globs: ["remotion/**", "**/shot-list.md", "**/motion-intent.md", "**/timeline.json"]
---

# Visual Style Rules

## Style Profiles

This file defines the **cinematic-presenter** defaults (the existing default style).

If `project.json` has `"style": "editorial-authority"`, refer to `styles/editorial-authority.md` instead for transitions, backgrounds, typography, avatar behavior, and motion language. The editorial-authority style overrides many defaults in this file.

See `.claude/rules/style-profiles.md` for the full style selector system.

---

## Grammar References

Hook-specific creative mandates live in `.claude/rules/hook-grammar.md`.
Post-hook variation rules live in `.claude/rules/body-grammar.md`.

This file covers technical layout, background assignment, display modes, and rendering defaults — the *how* of implementation, not the *what* or *why* of creative decisions.

---

## Format

Default format:
- aspect ratio: 9:16
- resolution: 1080x1920
- fps: 30
- duration: 20-60 seconds

## Rendering Layer Priority

When elements compete for screen space, this order governs occlusion. Higher-numbered layers must not obscure lower-numbered layers:

1. Captions — always readable, never covered by overlays, demo UI, or avatar
2. Demo or proof visual — screenshot, video, or animated component must be legible
3. Avatar — visible when not excluded by `hideRanges`
4. Text overlays (KeywordFadeIn, OverlayKeyword) — positioned so they do not cover captions or focal demo UI
5. SFX and transition effects — decorative only, must not obstruct any layer above

This is an implementation constraint for z-index and layout decisions during assembly. It is not an editorial priority ordering — for editorial priorities, see `docs/creative-direction.md`.

## Caption Style

- captions must be large enough for mobile
- maintain generous padding from screen edges
- avoid placing captions over critical demo UI
- use consistent emphasis styling
- do not overload the screen with too many simultaneous text elements

## Avatar Usage

Use avatar:
- full-screen for intro or direct address moments
- picture-in-picture for demos
- reduced prominence when the product UI is the focus

## Demo Usage

- demos should be cropped or zoomed for clarity
- cursor motion should be readable
- unnecessary dead space should be removed
- preserve enough context for the viewer to understand the interaction

### Display Modes

Every broll/demo entry can have a `display` field in timeline.json that controls how the content is rendered. Choose based on the content's aspect ratio and importance.

| Display mode | `display` value | When to use | Avatar behavior |
|---|---|---|---|
| **Default split** | _(omit field)_ | Standard demo in split-screen — content fills top 40%, avatar bottom 60% | Visible in bottom 60% |
| **Responsive** | `"responsive"` | Landscape video/image that should auto-size to its aspect ratio (16:9) without cropping. Use when content has important edges that would be cut by a fixed container | Visible below the content |
| **Center-full** | `"center-full"` | Key demo moment that deserves full attention — video/image centered on screen with dark-to-white background, no avatar | Hidden via `hideRanges` |

### Selection criteria

1. Is this a demo video clip (product walkthrough, app recording)? → `center-full` (always — responsive crops landscape content)
2. Is this cinematic b-roll (NotebookLM clips, abstract visuals)? → `center-full` with white (#FAFAFA) background
3. Is this the hook opening where avatar should be visible below? → `responsive` (b-roll top, avatar bottom)
4. Is this a static demo screenshot in split-screen? → omit `display` (default)
5. Does the content need full viewer attention with no avatar? → `center-full`

**Key rule:** Demo videos should almost always be `center-full`. Responsive mode crops landscape content and loses important edges. Only use responsive for the hook opening split-screen layout.

### Layout ratios

- **Split-screen**: demo/broll container = top 40%, avatar = bottom 60%
- **Responsive**: demo auto-sizes to content aspect ratio, avatar fills remaining space below
- **Center-full**: content centered on full screen, avatar hidden entirely

### Split-screen boundary rule (non-negotiable)

The split-screen boundary is defined by `AvatarVideo.tsx`:
```
isSplit → { position: "absolute", bottom: 0, height: "60%" }
```

This means:
- Avatar occupies **bottom 60%** (from 40% to 100% of frame height)
- Content container MUST be **height: "40%"** to meet the avatar at the boundary
- Any container height other than 40% creates a visible white gap
- **Always read `AvatarVideo.tsx`** before changing split-screen container sizing — if the avatar boundary changes, the content container must change to match

**When using direct `OffthreadVideo` or `<Img>` in split-screen containers** (bypassing BRollVideo):
- Set `objectFit: "cover"` to fill the 40% container completely
- Set `objectPosition: "center"` for balanced cropping
- This eliminates all white gaps between content and avatar

**When using `BRollVideo` in split-screen mode:**
- BRollVideo's default path adds internal padding (20px), aspect ratio constraints, and GlowBorder
- These create small gaps within the container
- For gap-free rendering, bypass BRollVideo and use `OffthreadVideo` directly

### Implementation details

- `BRollVideo.tsx` reads `entry.display` and renders different container layouts
- Center-full uses `zIndex: 12` and `background: "transparent"` (scene background shows through)
- Avatar receives `hideRanges` prop — array of `{start, end}` for center-full broll periods
- `ReelComposition.tsx` computes `centerFullRanges` from broll entries with `display: "center-full"` and passes to `<AvatarVideo>`

### Split-screen image spacing standard

`FramedImage.tsx` renders split-screen images with:
- `alignItems: "center"` — image is vertically centered in the top 40% zone
- `padding: "32px 24px"` — equal top/bottom margins, equal left/right margins

This produces visually balanced spacing: the gap above the image equals the gap between the image and the avatar divider. **Do not change this to `flex-start` or reduce vertical padding.** If the image looks too high or unbalanced, increase the padding value — never anchor the image to the top.

When adding split-screen entries to the avatar lane, ensure the avatar lane entry exists for that time range. If no avatar lane entry covers the period, the avatar will remain invisible even though `centerFullRanges` no longer hides it.

### Screenshot display defaults

Static demo screenshots (`.png`, `.jpg`) should default to **split-screen** (omit `display`), not `center-full`, unless the screenshot genuinely requires full viewer attention (e.g. a large results table, a before/after comparison, a complex dashboard that would be unreadable at 40% width).

The rule of thumb:
- **Demo VIDEO** → `center-full` (motion and full UI walkthrough warrant full screen)
- **Screenshot with 1–2 focal points** → split-screen (avatar + zoomed screenshot is clearer)
- **Screenshot requiring full detail** → `center-full` with overlays to compensate for face absence

## Supporting Visuals

Support visuals can include:
- screenshots
- logos
- icons
- charts
- interface crops
- headline cards
- AI news cards

Each support visual should reinforce a specific spoken point.

### StackedImageReveal (Image Montage) — NOT YET BUILT

`StackedImageReveal` is planned for displaying multiple related images between demo sections (e.g., screenshots of different features, comparison images). Creates a dynamic montage feel.

- **Status: Component does not exist yet.** Until built, use multiple `FramedImage` entries in rapid sequence (3-5 frames each) with `zoom-in` transitions to simulate montage behavior.
- Planned path: `remotion/src/components/effects/StackedImageReveal.tsx`
- Planned behavior: images slide in one-by-one from the right with slight overlap, hold, then exit one-by-one to the left
- Planned props: `images` (array of paths), `durationInFrames`, `staggerDelay` (frames between entrances, default 8)

## Scene Backgrounds

Different scene types use different background treatments. The composition must switch backgrounds at layout boundaries — never let a dark background run behind a demo, or a white background behind a talking-head avatar.

### Available background components

| Component | Style | Use when |
|---|---|---|
| `GradientMesh` + `SmokeWisp` + `FocusVignette` | Dark, moody, premium | Avatar full-screen scenes (CTA, outro, direct address) |
| `AuroraBackground` | White base with soft drifting pastel blobs | Demo/split-screen scenes, hook split-screen — clean, lets product UI pop |
| `BackgroundBeams` | White base with thin luminous SVG beams | Center-full scenes or layered on top of Aurora for extra depth |
| `ImageAutoSlider` | Infinite horizontal scroll of image cards | Behind CTA, proof sections, or as visual texture during transitions |

### Rules

- **Demo scenes must use a white/light background** (Aurora, Beams, or both). Dark backgrounds compete with product UI and reduce clarity.
- **Hook section can use white Aurora background** (not just dark GradientMesh) when split-screen with b-roll at top and avatar at bottom.
- **Only CTA/outro needs dark GradientMesh** — the moody look suits closing direct-address moments.
- **Center-full b-roll clips use white #FAFAFA background** — clean and neutral behind cinematic content.
- **Scope backgrounds to their time range** using `<Sequence>` — do not let one background run for the entire composition.
- **BRollVideo containers must be transparent** (`background: "transparent"`) so the scene background shows through. Never use opaque dark backgrounds on demo containers.
- **AbsoluteFill needs explicit white background** (`#FFFFFF`) to prevent black flash before Aurora renders.
- **Layer backgrounds by z-index**: background components sit at zIndex 0, content layers above. Aurora and Beams can be stacked together for richer scenes.
- **Responsive broll uses zIndex: 10** to render above support visuals that might bleed through.
- **Match background colors to the brand** when possible — use the product's palette for Aurora blob tints (e.g. Google blue/green for Google products).
- Background components are GPU-friendly (transform + opacity only) — no blur filters.

### Assembly checklist

During timeline assembly, for each scene determine:
1. Is this avatar full-screen CTA/outro? → dark background (GradientMesh)
2. Is this hook split-screen? → AuroraBackground (white)
3. Is this split-screen demo? → AuroraBackground
4. Is this center-full demo/broll? → AuroraBackground + BackgroundBeams (white #FAFAFA)
5. Wire the backgrounds in ReelComposition.tsx with matching `<Sequence from/durationInFrames>`

## Effects

Allowed by default:
- punch-in zooms (see Punch-In Zoom section below)
- emphasis pop-ins
- light motion graphics
- restrained SFX
- soft fades and dip-to-white

Never use in a professional/classy reel:
- heavy glitch or VHS distortion
- aggressive camera shake
- spin transitions
- random flashy preset transitions
- using a different transition style every 1–2 seconds
- blur-based transitions (also kills GPU performance)

**Rule of thumb**: if a transition draws attention to itself, it is wrong. Transitions should be invisible — the viewer should notice the content, not the cut.

## Punch-In Zoom

Use punch-in zoom on any demo screenshot or video where the narrator references a specific UI element (button, command, result, field).

### When to use

- narrator types or mentions a specific command → zoom to where it appears on screen
- narrator references an output or result → zoom to that region
- a key button click or toggle is being described → zoom to it
- do NOT zoom just for visual interest — every zoom must match a spoken point

### How coordinates work

Zoom coordinates (`x`, `y`) are percentages of the **element box**, not the raw image. Because demo slides are landscape (16:9) displayed in a near-square split-screen container, the image does not fill the full element height — it letterboxes. You must account for this when setting coordinates.

**Demo images use `objectFit: "contain"` + `objectPosition: "top"`**:
- Image fills the full container width (x maps 1:1)
- Image occupies the top ~57% of the container height (for 16:9 slides in a square-ish container)
- The bottom ~43% of the element is empty white space

**Coordinate formula (must use this, not raw image percentages)**:
```
frame_x = image_x        (direct 1:1 — image fills full width)
frame_y = image_y × 0.57 (image compressed into top 57% of frame)
```

Example: element at image_x:74%, image_y:33% → zoom coords x:74, y:19

**If you skip this formula and use raw image_y values, the zoom will point at white space below the image content.**

### Coordinate reference (frame coordinates after formula)

- `x: 0, y: 0` = top-left corner of the slide
- `x: 50, y: 0` = top-center of the slide
- `x: 50, y: 57` = bottom-center of the slide (anything above 57 is white)
- For 16:9 infographic slides: content is usually between frame_y: 5 and frame_y: 50

### Setting coordinates

1. Open the image and identify the target element (command box, output, button, slider)
2. Estimate its position as a percentage of the full image dimensions: `image_x`, `image_y`
3. Apply the formula: `frame_x = image_x`, `frame_y = image_y × 0.57`
4. Set `scale` between 1.4 (wide view) and 2.5 (tight punch-in)
5. Set `holdFor` to match how long the narrator discusses the element (typically 1.5–3 seconds)

### zoom_moments format in timeline.json

```json
"zoom_moments": [
  { "at": 0.8, "x": 44, "y": 20, "scale": 2.2, "holdFor": 2.8 },
  { "at": 3.8, "x": 60, "y": 55, "scale": 1.9, "holdFor": 2.5 }
]
```

- `at` — seconds after the clip starts (not absolute timeline time)
- `x`, `y` — percent of the visible frame
- `scale` — zoom multiplier (1.0 = no zoom)
- `holdFor` — seconds to hold before zooming back out (only the LAST moment ever zooms back out)

### Multiple zoom moments: timing rules

Only the **latest triggered moment** is ever active. When moment 2 triggers, moment 1 immediately hands off — it does NOT zoom out first. This prevents the "double zoom" appearance where the viewer sees zoom-in → zoom-out → zoom-in.

Because of this, `holdFor` on earlier moments is only used to set how long moment 1 stays zoomed if moment 2 never fires. If moment 2 fires before moment 1's `holdFor` expires, moment 2 simply takes over.

**Minimum gap between moments**: allow at least 1.5s between `moment[n].at` and `moment[n+1].at` so the viewer has time to read the zoomed content before the scene cuts to the next focal point. Tighter than 1.0s will feel rushed.
