---
description: Visual and layout standards for vertical reels — display modes, backgrounds, transitions, motion language
globs: ["remotion/**", "**/shot-list.md", "**/motion-intent.md", "**/timeline.json"]
---

# Visual Style Rules

## Style Profiles

This file defines the **cinematic-presenter** defaults (the existing default style).

If `project.json` has `"style": "editorial-authority"`, refer to `styles/editorial-authority.md` instead for transitions, backgrounds, typography, avatar behavior, and motion language. The editorial-authority style overrides many defaults in this file.

See `.claude/rules/style-profiles.md` for the full style selector system.

---

## Format

Default format:
- aspect ratio: 9:16
- resolution: 1080x1920
- fps: 30
- duration: 20-60 seconds

## Reel Style

The reel should feel:
- modern
- clean
- high clarity
- technically impressive without being cluttered
- optimized for mobile viewing

## Composition Priorities

Priority order on screen:
1. the message
2. the demo or proof
3. readable captions
4. avatar presence
5. supporting motion and effects

## Hook Motion Accounting (mandatory for all reels)

The first 3 seconds determine whether the viewer keeps watching. **Tame hooks fail.**

For every hook, count visual elements per second in the first 3 seconds. **Aim for ≥4 simultaneous elements in motion**, all visible from the moment the reel starts:

| Element class | Examples |
|---|---|
| **Real product UI** | Screenshot or video clip of actual product (Claude Console, Notion workspace, ChatGPT interface). NOT stock footage. NOT abstract gradients. |
| **Continuously animating element** | Bouncing logo (`LogoOverlay` with `bounce: true`), Ken Burns zoom on a screenshot, scrolling text, cycling demo screenshots, rotating mark |
| **Recognizable brand mark** | `LogoOverlay` showing the actual SVG logo of the product or a named customer |
| **Avatar (in split-screen)** | Talking head must NEVER be the sole element — always paired with at least one other visual |
| **Caption with the value claim** | The first spoken phrase as a visible caption |
| **SFX hit on entry** | Whoosh, impact, or pop on the first frame to mark the reel start |

### Self-test (must pass before approving the hook at Phase 4b-i)

- [ ] First frame contains real product UI (not just an avatar)
- [ ] At least one element is in continuous motion through the entire hook (bounce, zoom, scroll, cycle)
- [ ] At least one brand logo SVG is visible from the first 1-2 seconds
- [ ] Caption is readable in the first frame
- [ ] Total simultaneous visual elements in any frame of the first 3s ≥ 4

### Banned hook patterns

- Avatar full-screen alone with no overlays
- Single text card with no other motion
- Empty warm-beige / dark background with the avatar still fading in
- "Clean minimalism" — minimalism is for body beats, not hooks
- Static screenshot without zoom or motion (it must move)

### Default hook scaffolding

Use this structure as the starting point for any new reel hook:

1. **Top 40%** — split-screen with real product UI screenshot (with Ken Burns zoom)
2. **Bottom 60%** — avatar talking
3. **Top of frame** — bouncing brand logo (e.g. `LogoOverlay` with `bounce: true, bounceAmplitude: 28-32, bounceFrequency: 2.4-3.0 Hz`)
4. **Avatar chest area** — sequential brand logos appearing on each named brand (`LogoOverlay` at `position: center-bottom`)
5. **Captions** — value claim line at the bottom safe zone
6. **SFX** — whoosh on entry + pop per logo entry

That structure produces 4-5 simultaneous elements throughout the first 3 seconds. Iterate from there if a beat needs more.

See `feedback_hook_motion_intensity.md` in user memory for the editorial reasoning.

## Caption Style

- captions must be large enough for mobile
- maintain generous padding from screen edges
- avoid placing captions over critical demo UI
- use consistent emphasis styling
- do not overload the screen with too many simultaneous text elements

## Avatar Usage

Avatar should support the reel, not dominate it.

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

## Transition Stack (talking-head AI reels)

The default stack for avatar-led AI reels. Produces a professional, premium, Instagram-native feel:

| Technique | When to use |
|---|---|
| **Clean jump cut** | Default between beats — no effect needed |
| **Punch-in zoom** | Narrator references a specific UI element, button, or result |
| **Cut on beat** | Hard cut timed to a word landing or SFX hit |
| **J-cut** | Audio from next scene starts before the visual cuts — bridges demos smoothly |
| **Soft fade / dip to white** | End of reel, or transition from demo back to avatar |
| **Speed ramp** | Reserved for high-energy moments (hook, CTA reveal) |
| **Gesture match cut** | Cut on a matching movement — narrator hand gesture lines up with a visual action |

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

## Text & Number Overlays

Use these components to reinforce spoken content with on-screen text at key moments.

### Available overlay components

| Component | Style | Use when |
|---|---|---|
| `NumberPopup` | Colored badge with large number + label, spring pop-in | Narrator says "Number one/two/three" — each numbered point |
| `KeywordFadeIn` | Words fade in one by one with stagger | Narrator says a tool name, key phrase, or important term |
| `BadgePopup` | Small pill badge with icon | Labels, tags, callouts (e.g. "FREE", "GOOGLE LABS") |

### NumberPopup rules

- Place at the exact moment the narrator says the number
- Duration: ~1.0–1.5s (brief — it's a label, not a title card)
- Use the product's brand color for each number (e.g. Google blue, red, green)
- Position: `top-left` for split-screen scenes, `top-center` for center-full scenes
- Include the tool/feature name as the `label` prop

### KeywordFadeIn rules

- Place when the narrator says the tool/feature name (slightly after the number popup)
- Duration: ~1.2–1.8s
- Color should match the number popup for that scene
- Position: `top` for split-screen, `center` for center-full
- Use `withGlow` for emphasis on dark or busy backgrounds
- Do NOT overlap with captions — keywords go near top, captions stay in bottom safe zone

### Assembly checklist

For each narrated list item ("Number one, [tool name]"):
1. Add a `NumberPopup` at the number mention timestamp
2. Add a `KeywordFadeIn` at the tool name timestamp (0.5–1s after number)
3. Add a subtle click SFX at the number mention
4. Colors should follow the product brand or cycle through a palette

## Motion Language System

Every reel must have a defined motion language — a small set of consistent decisions that make every beat feel like it belongs to the same piece. The motion language is not about adding more transitions. It is about defining **how every beat behaves**, not just what asset plays when.

### Motion Budget Rule

Every beat gets exactly:
- **1 hero motion** — the primary visual event (wipe, scale entrance, focus crop)
- **1 support motion** — a secondary element that reinforces the hero (avatar settle, divider fade, caption lock)
- **1 accent** — a micro-event tied to a spoken emphasis word or editorial moment (scale pulse, opacity flash, SFX hit)

Do not exceed 3 motion elements per beat. If you are adding a 4th treatment, remove one first. Decorative layers (shimmer bands, glow borders, vignettes stacked on top of functional motion) are the first sign of "template polish" overtaking editorial restraint.

**The test:** if a motion element is removed and the beat still reads correctly, the element was decorative and should stay removed.

### Hold Behavior Rule

No beat should have a completely static hold longer than 0.5 seconds (15 frames).

During the hold phase of any beat, exactly **one** ambient motion must be active:
- **Demo panels:** slow Ken Burns (1.5–3% scale drift toward the focal point over the beat duration)
- **Avatar beats:** natural speech motion is usually sufficient. If the avatar is still (e.g. a pause), add a 0.3% scale breathe oscillation
- **B-roll:** the clip's own internal motion usually handles this. Only add Ken Burns if the b-roll is nearly static

The ambient motion must be subtle enough to be invisible when consciously watched. If a viewer notices the drift, it is too much.

### Four Beat Categories

Every beat in a reel belongs to exactly one of these categories. Each category has a defined motion principle:

#### Avatar beats
- **Motion principle:** push-in, caption lock, eye-line priority
- **Entry:** subtle scale settle (1.03–1.05 → 1.00 over 4–8 frames)
- **Hold:** natural speech motion from the avatar + slow push-in Ken Burns (1.0 → 1.02 over beat duration)
- **Accent:** the spoken emphasis word is the accent — do not add visual effects unless the word is also a visual reveal
- **Exit:** hold last frame or soft opacity ease into next beat

#### Demo beats
- **Motion principle:** focus crop, pointer emphasis, panel framing — UI is *read* not just shown
- **Entry:** clipPath wipe from top (same direction as hook — establishes system) OR fast scale entrance (1.08 → 1.00 over 5 frames)
- **Hold:** slow Ken Burns toward the focal point of the UI (button, prompt, result). If the demo has a cursor or typing motion, the clip handles the hold — do not add competing motion
- **Accent:** at the spoken emphasis word, a 2-frame scale pulse on the demo container (1.0 → 1.02 → 1.0). One pulse per beat maximum
- **Exit:** opacity 1 → 0 over 3–4 frames, or clipPath wipe reverse

#### Concept / proof beats (b-roll, support visuals)
- **Motion principle:** micro-accent overlays, directional cut energy, timing intact
- **Entry:** fast clipPath reveal or scale entrance
- **Hold:** the clip's own motion handles this
- **Accent:** `TransitionSeries.Overlay` is useful for cut-point flashes or light leaks when you do not want to shorten the timeline
- **Exit:** fade or hold into the next beat's entry

#### Return beats (avatar re-entry after demo)
- **Motion principle:** intentional re-entry — the viewer should feel the shift back to the human
- **Entry:** stronger scale settle (1.05 → 1.00) than normal avatar beats, OR a grade/background shift that marks the return
- **Hold:** same as avatar beats
- **Accent:** if returning from a proof section, the return beat often has a payoff line — let the words be the accent
- **Exit:** depends on what follows

### Gap Ownership Rule

Speech pauses between beats create time gaps where no beat is speaking. Every gap must be visually owned:

- **Gaps < 0.3s (< 9 frames):** the exiting beat holds through the gap. No special treatment needed.
- **Gaps 0.3–0.8s (9–24 frames):** the gap is a **designed seam**. Define whether the exiting beat fades out during the gap, the entering beat pre-enters, or the gap is a background transition moment.
- **Gaps > 0.8s (> 24 frames):** this is a breathing space. It must have intentional visual behavior — either the exiting beat visually resolves, or the gap contains a designed transition (background shift, energy reset, anticipation build).

No gap may be left undefined. If a gap exists in the beat map, the motion intent document must assign ownership.

### Background Seam Transitions

When the background changes (e.g. GradientMesh → Aurora, or Aurora → GradientMesh):
- Use an 8–12 frame opacity crossfade between the outgoing and incoming backgrounds
- Do not hard-cut backgrounds — the viewer will perceive a flash
- Time the crossfade to start at the last frame of the exiting beat and end during the gap or first frames of the entering beat
- If the seam coincides with a visual entry (e.g. demo wipe), the background crossfade should complete before or during the wipe — not after

### Transition Consistency

A reel should use **at most 2 transition types** for entries and **at most 2** for exits:
- One primary entry (e.g. clipPath wipe from top for demos)
- One secondary entry (e.g. scale settle for avatar)
- One primary exit (e.g. opacity fade)
- One secondary exit (e.g. hold into the next beat)

Do not assign different transition types per beat unless the beat category demands it. Transitions should be invisible — if the viewer notices the cut, the transition failed.

## Flash and Accent Budget

- **Maximum 1 flash accent per reel.** A 2-frame white flash or punch-in accent is a signature when used once. Used three times, it becomes a habit. All other bridges and beat endings should use opacity shifts, grade changes, or silence as their accent.
- The flash should be reserved for the single most important moment in the reel — typically the hook landing or the CTA close.

## Return Beat Energy

When the avatar re-enters after a demo or b-roll section, the re-entry must feel intentional:
- Use a **stronger scale settle** than normal avatar beats (1.05 → 1.00 vs the normal 1.03 → 1.00)
- The background may shift (e.g. beams layer off, returning to clean Aurora)
- For the CTA return: use darker grade, slower push-in, and more confident energy than any other avatar beat — the CTA is the conclusion, not just another talking head insert

## Interface Variety as Credibility

When a reel shows multiple interfaces (e.g. Claude.ai web + Claude Code CLI), do not treat the CLI as a problem or inconsistency. Frame it as intentional variety:
- The web UI shows "where to start" (accessible, familiar)
- The CLI shows "the engine room" (technical credibility, proof of depth)
- The motion language (entry wipes, Ken Burns, transitions) should be consistent across both — the viewer never notices the interface changed because the edit rhythm stays the same

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
