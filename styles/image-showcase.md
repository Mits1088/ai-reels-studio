# Image Showcase

**Style ID:** `image-showcase`

---

## Rule Precedence

When this style is active, it overrides baseline defaults.

Resolution order for conflicts:

1. `styles/image-showcase.md` (this file)
2. Project `output/motion-intent.md`
3. Baseline `.claude/rules/visual-style.md`
4. Baseline `.claude/rules/qa-gates.md`
5. Baseline assembly/workflow defaults

Specifically, when this style conflicts with:
- **visual-style.md** backgrounds (Aurora/GradientMesh/Beams) → this style's neutral backgrounds win
- **visual-style.md** avatar defaults (split-screen dominant) → this style's gallery-dominant defaults win
- **creative-feedback.json** VIDEO-FIRST hard rule → gallery beats are suspended from VIDEO-FIRST (see below)
- **body-grammar.md** avatar presence minimums → image-showcase explicitly permits extended avatar absence in gallery sections

QA must evaluate against **this style's thresholds**, not generic reel defaults.

---

## Style Activation Contract

When active, these declarations are **required**:

| Artifact | Required declaration |
|---|---|
| `project.json` | `"style": "image-showcase"` |
| `shot-list.md` | Every beat tagged with its gallery mode (`center-full`, `gallery-2x2`, `scroll-vertical`, `scroll-horizontal`, `avatar-pip`, `avatar-full`) |
| `output/motion-intent.md` | Must declare `style_profile: image-showcase` at the top |
| `output/timeline.json` | Gallery beats must include `"galleryMode": "<mode>"` |
| `output/qa-report.md` | Must include an **Image Showcase Compliance** section |

---

## Philosophy

**The images ARE the content.**

This style is for reels where the product's output — generated images, design outputs, creative assets — speaks for itself. The viewer should feel like they're being shown a gallery, not a presentation. The avatar is a curator who introduces the collection and closes it, but never competes with the imagery for visual real estate.

When a creator has invested in finding 10+ distinct, beautiful visual outputs, the pipeline's job is to get out of the way and let those images breathe at full attention.

---

## When to Use

- Reel subject IS visual outputs (AI image model, design tool, creative portfolio, art generator)
- Creator has provided 8+ distinct visual output images
- The images themselves demonstrate the value claim without needing annotation or explanation
- Visual range/variety IS the proof (style showcase, language range, capability breadth)
- "Look at what it made" is more powerful than "let me explain what it made"

**Do NOT use when:**
- The proof is a workflow or process (use cinematic-presenter)
- The reel is a claim-and-prove structure with single stats (use editorial-authority)
- The product output is video/interactive, not images

---

## Feel

Revelatory, gallery-quality. Like being walked through a curated exhibition where each room shows something unexpected. The pace is measured — not slow, but giving the viewer enough time to genuinely see each image before the next arrives. The avatar is a trusted guide, not the host of a talk show.

---

## Pacing

- **Visual change frequency:** every 2.5-4 seconds (slightly longer than cinematic-presenter — images need time to be *seen*)
- **Typical duration:** 35-50 seconds
- **Beat density:** 8-14 beats
- **Word density:** LOW (100-130 wpm spoken) — fewer words because images carry the message
- **Hold time for single images:** up to 3s (vs 2s standard) before requiring zoom/scroll

The reel should feel like it has BREATHING ROOM for the images. If the narration is dense and the images cycle fast, the viewer processes neither.

---

## Avatar Behavior

**Avatar is the curator, not the anchor.**

| Beat type | Avatar layout |
|---|---|
| Gallery beats (center-full, grid, scroll) | HIDDEN |
| Brief setup/transition beats | pip (avatar-pip: 20% of frame height at bottom) |
| Short verbal callouts over a single image | pip OR off-screen (depends on image composition) |
| CTA | full-screen |

**Presence targets:**
- **Target:** ≤25% of total reel duration
- **Hard maximum:** ≤35% (if exceeded → restructure gallery sections, not avatar sections)
- **Avatar absence preferred max:** 20s
- **Avatar absence hard max:** 35s (one sustained block only, and only when the gallery section has continuous scroll/grid motion)

**No split-screen avatar during gallery sections.** The standard 40/60 split is incompatible with this style's center-full gallery beats. Avatar appears as either full-screen or as a small pip below the image zone — never sharing a 40% content zone.

---

## Layout Modes (New + Existing)

### `center-full` (existing)
Single image fills the full frame. Avatar hidden.
- Use for: single powerful images that need full visual real estate
- Image: `objectFit: cover`, `objectPosition: center`
- Motion: motivated zoom OR vertical scroll OR horizontal pan (see Motion section)

### `gallery-2x2` (new — requires `ImageGrid2x2` component)
Four images in a 2×2 grid. Avatar hidden.
- Use for: style variety showcase, rapid capability breadth proof
- Grid fills full frame (4 cells × ~50% width, ~50% height each)
- Motion: staggered spring entry per cell, then hold (see Component Specs below)
- Between grid sets: 8-frame crossfade to next set of 4

### `scroll-vertical` (new — requires `ScrollImage` component with vertical mode)
Single tall image (aspect ratio > 2:1 portrait) with animated vertical pan. Avatar hidden.
- Use for: storybook sequences, infographic columns, tall narrative images
- Container: full frame
- Animation: top offset 0 → -(imageOverflow) over full beat duration
- The ENTIRE image height must be traversed before the beat ends

### `scroll-horizontal` (new — requires `ImageStrip` component)
3-6 images in a horizontal row, animated from right to left. Avatar hidden.
- Use for: language comparison sets, style family sequences, before/after chains
- Strip width: (numImages × imageWidth) with small gap between
- Animation: translateX 0 → -(stripWidth - containerWidth) over beat duration

### `book-spread-pan` (new — requires `BookSpread` or `objectPosition` animation on `FramedImage`)
Single landscape/book-spread image with animated horizontal pan. Avatar hidden.
- Use for: open-book photography spreads, diptych compositions, magazine spreads
- Animation: `objectPosition` from `left center` → `right center` over beat duration
- Zoom in to left side first, then pan right — gives viewer time to read both halves

### `avatar-pip` (new)
Image fills ~80% of frame, avatar appears as a small pip (20%) at bottom. Used sparingly for brief verbal callouts where the face adds delivery energy without competing with the image.
- Avatar zone: `position: absolute, bottom: 0, height: 20%, width: 100%`
- Image zone: full frame, avatar overlaps the bottom 20% (avatar appears ON TOP of image)
- Use sparingly — only for the 1-2 brief moments where the face genuinely adds value

---

## Component Specifications

### `ImageGrid2x2`

**Path:** `remotion/src/components/gallery/ImageGrid2x2.tsx`
**Status:** Build required at Phase 5

```
Props:
  images: [string, string, string, string]  // paths to 4 images
  staggerDelay?: number  // frames between each cell entry, default 5
  springConfig?: { mass, damping, stiffness }  // default: mass 1, damping 14, stiffness 90
  transitionToNext?: boolean  // whether to crossfade to next grid set
  transitionDuration?: number  // frames for crossfade, default 8

Layout:
  display: grid
  grid-template-columns: 50% 50%
  grid-template-rows: 50% 50%
  width: 100%
  height: 100%
  gap: 2px  // thin seam between cells

Cell motion:
  Each cell enters with spring scale from 0.92 → 1.0
  Entry order: top-left (frame 0), top-right (frame +staggerDelay), 
               bottom-left (frame +staggerDelay×2), bottom-right (frame +staggerDelay×3)
  Hold: each cell uses `still` mode (no ambient drift — 4 images simultaneously = motion chaos)

Note: Images in each cell use objectFit:cover, objectPosition:center
      The cell proportions (50%×50%) work well for portrait images
      For landscape images in cells: use objectPosition "center top" to favor the interesting area
```

### `ScrollImage`

**Path:** `remotion/src/components/gallery/ScrollImage.tsx`
**Status:** Build required at Phase 5

```
Props:
  src: string
  direction: "vertical" | "horizontal"
  imageAspectRatio: number  // actual image aspect ratio (e.g. 0.4 for ultra-tall portrait)
  durationInFrames: number
  easing?: "linear" | "ease-in-out"  // default: linear (consistent scroll speed)
  zoomMultiplier?: number  // optional: slight scale-up before scrolling, default 1.0

Vertical scroll:
  Container: 100% × 100% of frame, overflow hidden
  Image: width 100%, height auto (preserving actual aspect ratio → overflows container)
  Animation: interpolate(frame, [0, durationInFrames], [0, -(imageOverflow)])
             where imageOverflow = imageHeight - containerHeight
  
Horizontal scroll (for ImageStrip with single tall panoramic):
  Similar but on the X axis

Important: The scroll MUST complete the full traversal within the beat.
           If the image is 3× the container height, the scroll covers all 3× height.
           Calibrate scroll speed so the viewer sees the beginning AND the end.
```

### `ImageStrip`

**Path:** `remotion/src/components/gallery/ImageStrip.tsx`
**Status:** Build required at Phase 5

```
Props:
  images: string[]  // 3-6 image paths
  durationInFrames: number
  imageWidth?: number  // width per image in pixels, default: frameWidth / 2.2
  gap?: number  // px between images, default 8
  easing?: "linear" | "ease-in-out"

Layout:
  Row of images, each imageWidth wide, objectFit:cover
  Total strip width: images.length × (imageWidth + gap)
  Animation: translateX from 0 → -(stripWidth - containerWidth)
  
Entry animation:
  First image: visible from frame 0
  No stagger — the strip scrolls as one unit
  Smooth linear pan (or ease-in-out for cinematic feel)
```

---

## Motion Defaults

**Gallery beats inherit the ALWAYS MOTION rule** — every beat needs active motion. For gallery beats, motion is image-native:

| Layout mode | Required motion | Forbidden motion |
|---|---|---|
| `center-full` (single image) | motivated zoom OR book-spread pan | ambient Ken Burns only (no named target) |
| `gallery-2x2` | staggered spring cell entries | any per-cell Ken Burns (4 images moving = visual chaos) |
| `scroll-vertical` | full vertical scroll | any zoom during scroll |
| `scroll-horizontal` | full horizontal pan | any zoom during pan |
| `book-spread-pan` | horizontal objectPosition pan | scale zoom (would crop the spread) |

**Transition defaults:**

| Context | Enter | Exit | Duration |
|---|---|---|---|
| Gallery image entry | `wipe-up` or `fade` | `fade` | enterDur: 5, exitDur: 3 |
| Grid entry (ImageGrid2x2) | `fade` (full grid) | `fade` | enterDur: 4, exitDur: 3 |
| Scroll image entry | `fade` | `fade` | enterDur: 5, exitDur: 3 |
| Avatar pip entry | `fade` | `fade` | enterDur: 3, exitDur: 2 |
| Avatar full-screen (CTA) | `punch` | hold | enterDur: 4 |

**No hard cuts between gallery beats.** All gallery-to-gallery transitions use fade or wipe-up. Hard cuts are reserved for the hook before/after flash only.

---

## VIDEO-FIRST Rule Suspension (Gallery Beats)

The global `creative-feedback.json` VIDEO-FIRST hard rule states: *"Always use real video clips as the primary demo asset. Static screenshots are ONLY permitted as freeze frames."*

**In image-showcase style, this rule is SUSPENDED for gallery beats.** Here is why and what replaces it:

**Why:** The product being demonstrated IS a static image generator. The outputs are images by definition — not video clips. Requiring video of an image generator misrepresents the product (video of the generation process is not the output — the output IS the image). The VIDEO-FIRST rule was designed for reels about AI TOOLS where you show the tool in use. For reels about AI IMAGE OUTPUT, the image IS the thing.

**What replaces it:** The ALWAYS MOTION rule still fully applies. Every gallery beat with a static image MUST have one of:
1. Motivated zoom with pre-defined coordinates (zoom into a specific element the narrator names)
2. Vertical scroll animation (`scroll-vertical` mode) for tall images
3. Horizontal pan animation (`book-spread-pan` mode) for wide images
4. Staggered spring entry (for `gallery-2x2` grids)

No gallery beat may hold a static image without at least one of these motion mechanisms. VIDEO-FIRST is suspended, ALWAYS MOTION is not.

**Scope of suspension:** Gallery beats only. If the reel includes any actual DEMO VIDEO (e.g. screen recording of typing a prompt into ChatGPT), VIDEO-FIRST applies to that beat normally.

---

## Background Mapping

| Scene type | Background | Why |
|---|---|---|
| All gallery beats (any layout mode) | `#F8F8F8` off-white or `#FFFFFF` pure white | Images pop against neutral; Aurora blobs compete with image color |
| Avatar pip beats | `#F8F8F8` (same as gallery — pip appears over the image) | Continuity |
| Avatar full-screen (setup, brief) | `#F8F8F8` light for short setup beats; `#0D0D0D` dark if the tone shifts | Match scene energy |
| CTA | `#0D0D0D` near-black | Clear register shift: proof is over, human asks the question |

**No Aurora.** AuroraBackground's drifting color blobs compete with image color palettes. A generated image in jewel tones placed over an Aurora background with conflicting blob colors creates visual confusion.

**No GradientMesh** on gallery beats. The mesh is atmospheric for CTA/outro but looks like a blurred TV behind a crisp image.

**No BackgroundBeams** on gallery beats. Horizontal beam lines create a structured visual grid that clashes with image compositions.

Background seam transitions: 8-12 frame crossfade at scene boundaries (never hard-cut backgrounds).

---

## Caption Behavior

| Beat type | Caption mode | Why |
|---|---|---|
| Gallery beats with images (no text overlay) | `suppressed` | Images carry the communication; captions create visual competition |
| Gallery beats where narrator names a specific element | `brief-keyword` (OverlayKeyword, 2-3 words max) | Name the thing, don't re-narrate it |
| `gallery-2x2` beats | `suppressed` | 4 images + caption = impossible to read either |
| `scroll-vertical` / `scroll-horizontal` beats | `suppressed` | Scrolling image + moving text = motion chaos |
| Avatar pip beats | `standard` | Avatar is speaking, captions reinforce |
| Avatar full-screen beats | `standard` | Normal caption behavior |
| CTA | `standard` | Reinforce the ask |

**Caption suppression target:** 50-65% of total reel duration. This is the highest suppression rate of any style — the images literally do not need words accompanying them.

---

## SFX Character

Image-showcase SFX should be **ambient and contextual**, not punchy and emphatic.

| Moment | SFX type | Character |
|---|---|---|
| Gallery image entry | Soft whoosh (low velocity) | Image arrives, doesn't punch |
| Grid stagger (ImageGrid2x2) | 4 soft pops (one per cell, staggered) | Subtle, like cards dealt |
| Scroll start | None | Silence — scroll is the motion event |
| Section transition | Soft slide/whoosh | Context shift |
| Avatar full-screen return | Subtle settle SFX | Re-entry, not alarm |
| CTA | Soft impact | Gentle emphasis |

**Target SFX count:**
- 30-40s reel: 4-7 entries (fewer than standard — gallery sections need quiet space)
- 40-55s reel: 6-10 entries

---

## Typography

- All overlay text is **minimal** — the image should be visually dominant
- Brief keyword overlays: `OverlayKeyword` or `CharKeyword` for single-word emphasis only
- No `KeywordFadeIn` on gallery beats (word-by-word fade competes with image viewing)
- Caption font: standard (system-ui), bottom safe zone, minimal opacity backdrop
- No large header cards during gallery sections (the image IS the header)

---

## Proof Strategy

In image-showcase style, **the image IS the proof**. The narration names what the viewer is seeing — it does not argue for it.

Pattern: *show first, name second*
1. Image appears (gallery beat)
2. Narrator names what it demonstrates: *"Japanese manga panels — every character legible"*
3. No annotation needed unless pointing at a specific sub-element

**Annotation (AnnotationCircle):** Use sparingly — only when the proof point is a *specific sub-element* that would be missed without it. Do not annotate for the sake of having an annotation layer. The image speaks.

**Proof coverage:** Because the images ARE the proof, `proof-display` beats will dominate the role distribution. The normal 50% cap on any single role is SUSPENDED for `proof-display` in image-showcase style. It is expected that 60-80% of body beats are `proof-display` or `annotation-focus`.

---

## Hook in Image-Showcase Style

Hook-grammar.md archetypes (A, B, C) still apply structurally. Adaptations for image-showcase:

**Archetype A (Split-Proof Hook) — default for this style:**
- Top 40%: The MOST STRIKING generated image (not a generic UI screenshot — the OUTPUT is the product)
- Bottom 60%: AvatarVideo split-screen
- Logo: product logo (ChatGPT, Midjourney, etc.) with bounce
- Ken Burns push toward the most interesting element of the image
- The "real product UI" requirement is satisfied by showing a generated image — the output IS the product

**Contrast Hook variant (best for product capability reveals):**
- Shows the "before" state (old limitation, ASCII art, broken text) for 0.8-1.0s
- Hard cut with flash to 2-3 stunning gallery images side-by-side
- Avatar appears with the flash
- This creates immediate recognition + surprise — the most retention-efficient hook for this subject

---

## Shot-List Phase Tags

Additional beat classification for image-showcase shot-list (used in Phase 4b-i visual assignment):

| Tag | Meaning | Typical layout mode |
|---|---|---|
| `image-gallery` | Pure image showcase beat, no specific claim | center-full |
| `style-showcase` | Demonstrating style range | gallery-2x2 or center-full sequence |
| `language-showcase` | Demonstrating multilingual capability | scroll-vertical (tall text image) or scroll-horizontal (language strip) |
| `precision-proof` | Specific technical detail visible in image | center-full + motivated zoom |
| `narrative-image` | Image tells a story (storybook, comic pages) | scroll-vertical or center-full sequence |
| `before-after` | Contrast between old capability and new | hard cut: before (center-full) → flash → after |

---

## Self-Test Before Phase 4b-ii

At the end of Phase 4b-i visual assignment, verify:

- [ ] Avatar presence is ≤25% of planned total duration
- [ ] All gallery beats (≥70% of body beats) use center-full, gallery-2x2, scroll, or book-spread-pan layout
- [ ] No split-screen avatar + image layout (the 40/60 split is not used in this style)
- [ ] No AuroraBackground or GradientMesh assigned to gallery beats
- [ ] Every gallery image >3s has zoom/scroll/grid motion planned
- [ ] VIDEO-FIRST suspension documented for all static image gallery beats
- [ ] At least 8 unique images assigned (30-40s reel) or 12 (40-55s reel)
- [ ] The most striking image is assigned to the hook zone

---

## QA Thresholds (Image Showcase Specific)

See `qa-gates.md` → **Image Showcase Compliance** section for the full QA gate list.

Key thresholds at a glance:

| Threshold | image-showcase |
|---|---|
| Avatar presence hard max | 35% of total duration |
| Avatar absence preferred max | 20s |
| Avatar absence hard max | 35s (one block, proof-protected) |
| Consecutive gallery beats (no avatar) | No limit — by design |
| Min unique images (30-40s reel) | 8 |
| Min unique images (40-55s reel) | 12 |
| Max single image hold w/o motion | 3s |
| Gallery beat background | White only (#F8F8F8 or #FFFFFF) — no Aurora/GradientMesh |
| Caption suppression | 50-65% of total duration |
| VIDEO-FIRST on gallery beats | SUSPENDED — ALWAYS MOTION applies instead |
| proof-display role cap | SUSPENDED — 60-80% proof-display expected |
