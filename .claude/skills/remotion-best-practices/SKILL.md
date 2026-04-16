---
name: remotion-best-practices
description: Core Remotion coding rules — animation primitives, reserved names, constants-first design, edit modes, split-screen contract, and the error correction loop. MUST be loaded before any Remotion code change.
---

# Remotion Best Practices

Load this skill before writing or modifying ANY file inside `remotion/`. No exceptions.

See `.claude/rules/remotion-skill-required.md` for enforcement rules.

---

## Required reading by task

| Task | Required sections |
|---|---|
| Assembly (Phase 5) | Sequencing, Animations, Transitions, SFX, Images, Videos, Split-screen contract |
| New component | Animations, Timing, Text animations, Constants-first |
| Caption work | Captions, Subtitles |
| Video embedding | Videos, Trimming |
| Audio / SFX | Audio, SFX |
| Debugging | Animations, Sequencing, Can-decode checklist |
| Split-screen layout | Split-screen contract, AvatarVideo boundary |
| Mid-session changes | Edit modes, Error correction loop |
| GuidedDemo highlights | GuidedDemo highlight placement protocol |

---

## Reserved names

**Never shadow these Remotion identifiers.** Shadowing causes silent runtime bugs that are nearly impossible to debug — the component appears to work but produces wrong values.

```
spring          interpolate      useCurrentFrame    useVideoConfig
AbsoluteFill    Sequence         fps                width
height
```

**Wrong:**
```tsx
const { fps, width, height } = useVideoConfig();  // OK — destructuring, not redefining
const height = someOtherValue;                     // WRONG — shadows the destructured height above
const spring = { damping: 14 };                    // WRONG — shadows the remotion spring function
```

**Right:**
```tsx
const { fps } = useVideoConfig();
const springConfig = { damping: 14, stiffness: 200 };  // named clearly, not "spring"
const containerHeight = "60%";                          // not "height"
```

---

## Constants-first design

Extract ALL magic numbers and strings to named constants at the top of the component body, before any hooks or logic. Group by category.

```tsx
export const MyComponent: React.FC<Props> = ({ text, durationInFrames }) => {
  // ── Colors ──────────────────────────────────────────────────────────────
  const COLOR_ACTIVE   = "#D97757";
  const COLOR_INACTIVE = "rgba(255,255,255,0.4)";
  // ── Layout ──────────────────────────────────────────────────────────────
  const FONT_SIZE = 72;
  const PADDING_PX = 24;
  // ── Timing ──────────────────────────────────────────────────────────────
  const ENTER_FRAMES = 6;
  const EXIT_FRAMES  = 4;
  // ── Animation ───────────────────────────────────────────────────────────
  const SPRING_CONFIG = { damping: 14, stiffness: 200, mass: 0.8 };
  const SCALE_FROM    = 0.85;
  // ────────────────────────────────────────────────────────────────────────

  const frame = useCurrentFrame();
  // ... rest of component
};
```

**Why:** Magic numbers in JSX make it impossible to know what `1.06` means, why `768` was chosen, or whether `60` and `40` are related. Named constants make the intent self-documenting and changes safe.

### Cross-component constants

When a constant must be consistent across multiple components (e.g. the split-screen boundary), export it from `utils.ts`:

```ts
// remotion/src/utils.ts — single source of truth for split-screen
export const SPLIT_HEIGHT_PCT = 60;                          // avatar bottom zone
export const CONTENT_HEIGHT_PCT = 100 - SPLIT_HEIGHT_PCT;   // content top zone
```

Both `AvatarVideo.tsx` and every content container import from `utils.ts`. If you change one, the other adjusts automatically. **Never hardcode "60%" or "40%" in component JSX.**

---

## Two edit modes

Choose the edit mode based on how much of the file is changing.

### Mode A — Targeted replacement (< 30% of file changing)

Use when: fixing a prop name, changing a constant value, adding one prop, repositioning one element.

**Tool:** `Edit` with `old_string` / `new_string`

**Rules:**
- `old_string` must be unique in the file — include enough context to disambiguate
- Change only what was asked — do not reformat or restructure surrounding code
- Verify the edit did not affect adjacent blocks

### Mode B — Full replacement (> 50% of file changing)

Use when: complete component rewrite, adding a major feature that affects most of the file, large refactor.

**Tool:** `Write` with the entire new file content

**Rules:**
- Read the current file first — never overwrite without understanding the existing code
- Preserve all existing prop interfaces exactly (no silent prop removals)
- Add a comment at the top explaining what changed and why

### Mode decision table

| Change | Mode |
|---|---|
| Fix one constant value | A |
| Change one prop name | A |
| Move one element | A |
| Add one overlay entry | A |
| Change spring config | A |
| Add a new feature (new props + new render path) | B |
| Restructure all state management | B |
| Rewrite animation system | B |

**If uncertain:** default to Mode A with enough context to be unique.

---

## Split-screen boundary contract

The split-screen layout is a cross-component contract. Both sides must agree on the boundary or a white gap appears.

```
AvatarVideo (bottom):   height = SPLIT_HEIGHT_PCT%   = 60%
Content containers (top): height = CONTENT_HEIGHT_PCT% = 40%
```

**Before any split-screen change:**
1. Read `AvatarVideo.tsx` and note the `SPLIT_HEIGHT_PCT` in use
2. Read `utils.ts` to confirm the exported values
3. Use `CONTENT_HEIGHT_PCT` in content containers — never hardcode `40%`

```tsx
import { CONTENT_HEIGHT_PCT } from "../../utils";

// Split-screen content container — always 40%
<div style={{
  position: "absolute", top: 0, left: 0, right: 0,
  height: `${CONTENT_HEIGHT_PCT}%`,
  overflow: "hidden", zIndex: 10,
}}>
```

---

## GuidedDemo highlight placement protocol

Derived from real production errors. Every rule below corresponds to a specific bug that
reached a rendered frame. Follow the full protocol for every `highlight_moments` entry —
new, corrected, or reviewed.

---

### Step 0 — Classify cover scale direction (do this first, always)

GuidedDemo renders images with `objectFit: cover`. Which axis overflows determines
which pan axis does anything. Misidentifying this wastes all downstream calculations.

```
contentH = compHeight - contentTop - contentBottom   // = 1920 - 96 - 96 = 1728 for default margins

coverScale = max(compWidth / imgW,  contentH / imgH)

WIDTH-DOMINANT  (compWidth/imgW > contentH/imgH):
  dispW = compWidth             ← no horizontal overflow; panX has ZERO effect on position
  dispH = imgH * coverScale     ← vertical overflow exists; panY moves the image

HEIGHT-DOMINANT  (contentH/imgH > compWidth/imgW):
  dispH = contentH              ← no vertical overflow; panY has ZERO effect on position
  dispW = imgW * coverScale     ← horizontal overflow exists; panX moves the image
```

**Write the classification at the top of any highlight calculation. Do not proceed without it.**

Common cases:
| Image shape | Typical result |
|---|---|
| Tall portrait (e.g. 540×9698 scroll) | WIDTH-DOMINANT — only panY scrolls |
| Wide landscape (e.g. 2560×1340 screenshot) | HEIGHT-DOMINANT — only panX pans |
| Near-square or exact-fit | check the formula, don't assume |

---

### Step 1 — Define the target precisely

State exactly what is being highlighted before measuring anything:

| Target type | Example |
|---|---|
| Text label only | the blue hyperlink text for "content-strategy" |
| Full row (label + description) | the entire table row containing "content-strategy" |
| Input box | the rounded prompt textarea, including padding and send button |
| Full prompt box incl. controls | textarea + model selector + send button |
| Icon + label | the skill icon and its name, not the surrounding card |

**Do not switch target definition mid-task.** If the user says "the whole prompt bit",
that means the entire input container — not just the first visible line of text.

---

### Step 2 — Crop rule (the most commonly broken rule)

When an asset has been cropped, recalculate y-coordinates using the correct formula.

```
BOTTOM CROP (removing Npx from bottom — e.g. cutting a tooltip artifact):
  new_height = old_height - N
  y_px is UNCHANGED  (top-left origin does not move)
  new_y_pct = y_px / new_height          ← denominator shrinks, pct increases

TOP CROP (removing Npx from top — e.g. cutting browser chrome):
  new_height = old_height - N
  y_px = old_y_px - N                    ← origin shifts downward
  new_y_pct = y_px / new_height

BOTH CROPS:
  apply top crop adjustment first, then recalculate pct with new_height
```

**Never apply the top-crop formula to a bottom crop.** This moves the highlight
above the actual target by the crop amount — the single most common highlight error.

---

### Step 3 — Asset invalidation rule

**Any change to asset dimensions, crop, aspect ratio, or pan setup invalidates ALL
`highlight_moments` for that beat until recomputed.**

When an asset is modified:
1. Add `"NEEDS_RECOMPUTE": true` to every `highlight_moments` entry for that beat
2. Do not render or declare highlights correct until each entry is recomputed
3. Remove the flag only after the verification gate (Step 5) passes

---

### Step 4 — Mandatory transform chain (fill this out for every highlight fix)

```
Asset: <filename>  |  source: WxH px  →  cropped: WxH px
Crop: [none | top Npx | bottom Npx | top Npx + bottom Npx]

Cover scale classification: [WIDTH-DOMINANT | HEIGHT-DOMINANT]
  coverScale = <value>
  dispW = <px>,  dispH = <px>
  Overflow axis: [X / Y],  overflow_px = <px>

Target definition: <exact description>
Target bbox in SOURCE image (px): x1=___, y1=___, x2=___, y2=___
Target bbox in CROPPED image (px): x1=___, y1=___, x2=___, y2=___
  (same as source if bottom crop; subtract crop_top from y values if top crop)

Target as % of cropped image:
  x = x1/W*100 = ___%
  y = y1/H*100 = ___%
  w = (x2-x1)/W*100 = ___%
  h = (y2-y1)/H*100 = ___%

Annotation region (with padding):
  region: { x: ___, y: ___, w: ___, h: ___ }

Containment check (annotation must contain target):
  annotation left  = x_pct * W = ___ px  ≤  target x1 = ___ px  ✓/✗
  annotation top   = y_pct * H = ___ px  ≤  target y1 = ___ px  ✓/✗
  annotation right = (x+w)_pct * W = ___ px  ≥  target x2 = ___ px  ✓/✗
  annotation bot   = (y+h)_pct * H = ___ px  ≥  target y2 = ___ px  ✓/✗
```

All four containment checks must pass before proceeding.

---

### Step 5 — Verification gate

A highlight is only "fixed" when ALL six of these are present:

- [ ] Target bbox in source image (measured, not guessed)
- [ ] Target bbox in cropped image (crop formula applied correctly)
- [ ] Target as image-space percentages
- [ ] Annotation region with padding
- [ ] Containment check passed (all four edges)
- [ ] Rendered verification frame at peak opacity (fade-in complete)

**Do not use the words "verified", "resolved", "confirmed", or "ready to render"
until every checkbox above is ticked.** Partial completion is not verification.

### Peak opacity frame calculation

```
# highlight fires at clip_at seconds after Sequence start
# Sequence starts at absolute frame: seq_start = toFrame(beat.start)
# At clip_at: highlight local_frame = 0

local_frame_at_peak = fadeDur
  where fadeDur = min(6, floor(duration_frames * 0.2))

abs_frame_at_peak = seq_start + round(clip_at * fps) + fadeDur
```

Render that frame. If the highlight box is not visible at expected position → recalculate.

---

### Pixel scanning tools

Use Python/PIL to locate targets without guessing:

```python
from PIL import Image
import numpy as np

img = Image.open("remotion/public/demo-frames/frame_018.jpg")
arr = np.array(img)
H, W = arr.shape[:2]

# Find blue hyperlinks (GitHub link color ~rgb(9,105,218))
blue_mask = (arr[:,:,0] < 60) & (arr[:,:,1] > 70) & (arr[:,:,1] < 140) & (arr[:,:,2] > 160)

# Find gray box borders (~rgb(200-225,200-225,200-225))
def is_gray(px, lo=130, hi=230):
    r,g,b = int(px[0]),int(px[1]),int(px[2])
    return max(r,g,b)-min(r,g,b) < 20 and lo < r < hi

# Find dark text (R<80, G<80, B<80)
dark_mask = (arr[:,:,0] < 80) & (arr[:,:,1] < 80) & (arr[:,:,2] < 80)
```

Scan vertically at multiple x positions to find top/bottom edges.
Scan horizontally at multiple y positions to find left/right edges.
Report every run as: `y=NNN-NNN  center=NNN  (NN.NN%)`

Do not estimate coordinates by eye from a thumbnail. Scan first, then apply the transform chain.

---

### Common errors and their fixes

| Error | Cause | Fix |
|---|---|---|
| Highlight entirely above target | Bottom crop treated as top crop | `new_y_pct = y_px / new_height` — y_px unchanged for bottom crop |
| Highlight misses by one row | Used center of text run as region.y (not top-left) | `region.y = center_pct - (h/2)` |
| panX changes have no visual effect | Image is width-dominant, panX overflows nothing | Classify cover scale first; use panY for tall images |
| Highlight drifts as pan animates | Highlight coords not accounting for pan offset | Verify at the exact pan value active when highlight fires, not at t=0 |
| Box covers target in studio but shifts in render | Used render-space coords instead of image-space pcts | Always work in image-space %; GuidedDemo does the transform |

---

### Forbidden patterns

```tsx
// FORBIDDEN — CSS animations break Remotion frame-seeking
const style = { animation: "fadeIn 0.3s ease" };
const style = { transition: "opacity 0.3s" };

// FORBIDDEN — framer-motion is not frame-accurate
import { motion } from "framer-motion";

// FORBIDDEN — native <img> loses Remotion's preloading
<img src={staticFile("logo.svg")} />

// FORBIDDEN — useEffect / useState for animation
const [scale, setScale] = useState(1);
useEffect(() => { ... }, [frame]);
```

### Required patterns

```tsx
// CORRECT — frame-driven animation
const frame = useCurrentFrame();
const { fps } = useVideoConfig();
const opacity = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
const scale = spring({ frame, fps, config: { damping: 14, stiffness: 200 } });

// CORRECT — Remotion image component
import { Img, staticFile } from "remotion";
<Img src={staticFile("logo.svg")} />

// CORRECT — video playback (always muted in splits)
import { OffthreadVideo, staticFile } from "remotion";
<OffthreadVideo src={staticFile("demo.mp4")} muted />
```

### Spring configs reference

| Feel | Config |
|---|---|
| Fast pop (badge, keyword) | `{ damping: 12, stiffness: 300, mass: 0.6 }` |
| Normal settle | `{ damping: 14, stiffness: 200, mass: 0.8 }` |
| Slow settle (layout change) | `{ damping: 18, stiffness: 90, mass: 1.0 }` |
| Overshoot (scale-pop entry) | `{ damping: 10, stiffness: 250, mass: 0.7 }` |

---

## Sequencing rules

```tsx
// Every Sequence needs premountFor for smooth rendering
<Sequence from={startFrame} durationInFrames={dur} premountFor={30}>
  <MyComponent />
</Sequence>

// Short clips need proportional fade durations — fixed durations crash interpolate
const safeEnterDur = Math.min(15, Math.floor(durationInFrames * 0.3));
const opacity = interpolate(frame, [0, safeEnterDur], [0, 1], { extrapolateRight: "clamp" });
```

**Short clip rule:** For any clip < 30 frames, always calculate fade duration proportionally. A fixed `enterDur: 10` on a 5-frame clip causes `inputRange must be strictly monotonically increasing` errors.

---

## SFX rules

Use `@sfx/` shorthand for common sounds — they resolve to `@remotion/sfx` CDN URLs (no local files needed):

| Shorthand | Sound | When to use |
|---|---|---|
| `@sfx/whoosh` | Fast whoosh | Layout transitions, reveals |
| `@sfx/whip` | Sharp whip | Fast cuts, hook landing |
| `@sfx/ding` | Notification ding | Proof moments, trust beats |
| `@sfx/uiSwitch` | Toggle click | UI interaction beats |
| `@sfx/mouseClick` | Single click | Button/zoom moments |
| `@sfx/pageTurn` | Paper flip | Card reveals, transitions |
| `@sfx/shutterModern` | Camera shutter | Screenshot moments |

Local SFX files use `staticFile()` automatically — `resolveSfxAsset()` handles both.

---

## Video encoding requirements

All videos in `remotion/public/` must be encoded before use:

```bash
ffmpeg -i input.mp4 -r 30 -c:v libx264 -profile:v high -pix_fmt yuv420p \
       -g 1 -movflags +faststart -c:a aac -b:a 128k output.mp4
```

**Required:**
- `libx264`, `yuv420p` — browser compatibility
- `-g 1` — every frame is a keyframe (Remotion seeks frame-by-frame)
- `-movflags +faststart` — prevents browser loading errors
- Audio track always present — even if silent (add `-f lavfi -i anullsrc` if source has no audio)

---

## Can-decode checklist

Before assembly, verify every video asset:

```bash
ffprobe -v quiet -show_entries stream=codec_name,r_frame_rate,pix_fmt -of compact <file>
# Expected: codec_name=h264, r_frame_rate=30/1, pix_fmt=yuv420p
```

If ffprobe fails → re-encode. Do not put un-probed videos into `remotion/public/`.

---

## Error correction loop

After every Remotion code change, run TypeScript compilation:

```bash
cd remotion && npx tsc --noEmit
```

If errors are found, use the error correction tool to get a formatted fix prompt:

```bash
python -m lib.compile_fix --prompt
```

This outputs:
- File path, line number, error code
- Surrounding code context with an arrow at the error line
- Fix rules reminding you not to shadow reserved names
- A copy-pasteable prompt ready for Claude

**Do not render before TypeScript compiles clean.**

---

## Remotion render commands

```bash
# Preview (live scrub in browser)
cd remotion && npx remotion studio

# Single frame still
cd remotion && npx remotion still ReelComposition --frame=90 --output=frame90.png

# Full render
cd remotion && npx remotion render ReelComposition --output out/reel.mp4

# Pre-render check
python -m lib.preflight_render projects/<slug>
```
