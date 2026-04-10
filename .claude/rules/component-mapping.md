---
description: Narration-to-component decision guide and asset fitness audit for beat-by-beat visual planning
globs: ["**/shot-list.md", "**/beat-map.json", "**/catalog.json"]
---

# Component Mapping & Asset Fitness

This rule governs Phase 4b-ii of the reel workflow. It runs after visual assignment (4b-i) and before technical planning (4b-iii).

Its job is to answer two questions for every beat:
1. **Which Remotion component** best renders what the narrator is saying?
2. **Does the chosen asset** actually match the narration?

---

## Step 1 — Classify the Narration

Read the beat text from `audio/beat-map.json`. Every beat's words fall into one of these classifications:

| Classification | Pattern | Examples |
|---|---|---|
| **Emotional keyword** | Single word or short phrase that IS the emphasis | "WRONG", "ZERO", "MORE", "GONE.", "FREE" |
| **Staccato claim** | 2-5 word declarative with a period feel | "No retraining.", "Works on any model.", "Zero accuracy loss." |
| **Name reveal** | Introduces a product, feature, or concept name | "called TurboQuant", "Jevons' Paradox", "LMArena.ai" |
| **Number + proof** | Stat with visual evidence available | "6x less memory" + chart exists, "crashed 14%" + stock chart |
| **Explanation over visual** | Describing what a visual shows | "It compresses how AI stores data" + diagram |
| **Direct address** | Talking to viewer, no visual needed | "Here's why.", "But here's what nobody expected" |
| **Trust/credibility** | Citing authority or source | "peer-reviewed at ICLR 2026" + research page |
| **Contradiction/negation** | Striking through or negating something | "people don't use less", "you're doing it wrong" |
| **List item** | Numbered or bulleted item in a series | "Number one: LMArena", "Number two: DesignArena" |
| **Comparison** | Side-by-side or A vs B | "ChatGPT vs Gemini", "before and after" |
| **CTA** | Call to action | "Follow for more", "Comment AI" |
| **Section transition** | Gap between major sections | (silence or breath between sections) |
| **Hook opening** | First 2-5 seconds, must stop the scroll | "If you're paying for AI tools" |
| **Reframe/montage** | Summary or multi-source validation | "Cheaper AI means AI everywhere" |
| **Tool intro/chapter** | New section introducing a tool by name + logo | "First up: Pinokio" |

A single beat can combine classifications (e.g. "Number + proof" + "Staccato claim").

---

## Step 2 — Select the Component and Verify Design Quality

Use the classification to select a Remotion component. The selection depends on the project's `style` field.

### Design quality check (frontend-design)

After selecting a component, verify it will render **distinctively**. Consult the `frontend-design` skill if:
- The component's default styling feels generic or flat
- Typography choices need refinement (weight contrast, size contrast, font pairing)
- Color choices need alignment with the project's theme (read `theme_primary` and `theme_secondary` from `project.json`)
- A new component needs to be built — frontend-design guides typography, color, motion, and spatial composition for 1080x1920

**Rule:** Every component should feel intentionally designed for mobile viewing, not default. If the component's treatment would look the same in every reel regardless of topic, it needs design work.

### Theme integration

When selecting colors for components, read `project.json` for `theme`, `theme_primary`, `theme_secondary`. These values come from the `theme-factory` skill (Phase 0b) and should drive:
- HeroTextCard background colors (use theme_primary for brand beats, contrast colors for emphasis)
- OverlayKeyword colors (use theme_primary or theme_secondary)
- NumberPopup / BadgePopup accent colors
- Aurora blob tints (cinematic-presenter style)
- ScrollingIconGrid overlay gradient (editorial-authority style)

### Universal components (both styles)

| Classification | Component | Avatar behavior |
|---|---|---|
| **Section transition** | `FlashReset` | Hidden during flash |
| **CTA** | `AvatarVideo` + `OverlayKeyword` | Full-screen, text overlaid on face |
| **Comparison** | `ComparisonGrid` | Hidden |
| **Tool intro/chapter** | `ChapterDivider` | Hidden |

### Editorial-authority component selection

| Classification | Primary component | Avatar layout | Content zone |
|---|---|---|---|
| **Emotional keyword** | `OverlayKeyword` on avatar | Full-screen | Center on face |
| **Staccato claim** | `OverlayKeyword` on avatar | Full-screen | Center on face |
| **Name reveal** | `HeroTextCard` | Hidden | Full frame |
| **Number + proof** (with asset) | `FramedImage` + `OverlayKeyword` | Split-screen (bottom) | Top 40-45% |
| **Number + proof** (no asset) | `HeroTextCard` | Hidden | Full frame |
| **Explanation over visual** | `FramedImage` | Split-screen (bottom) | Top 40-45% |
| **Direct address** | `AvatarVideo` | Full-screen | — |
| **Trust/credibility** | `FramedImage` + `AnnotationCircle` + `BadgePopup` | Split-screen (bottom) | Top 40-45% |
| **Contradiction/negation** | `OverlayKeyword` with strikethrough | Full-screen | Center on face |
| **List item** | `CardStack` editorial variant OR `HeroTextCard` sequence | Hidden or split | Depends on card count |
| **Hook opening** | `ScrollingIconGrid` + `OverlayKeyword` | Split-screen (bottom) | Top 45% grid + text |
| **Reframe/montage** | Multiple `FramedImage` entries in rapid sequence (ImageMontage/StackedImageReveal not yet built) | Hidden | Full frame |

**Editorial-authority key rule:** Text goes ON the avatar whenever possible. Only use HeroTextCard (which hides the avatar) for name reveals, concept cards, and section labels.

### Cinematic-presenter component selection

| Classification | Primary component | Avatar layout | Content zone |
|---|---|---|---|
| **Emotional keyword** | `KeywordFadeIn` | Split-screen or full-screen | Top zone (split) or above center (full) |
| **Staccato claim** | `KeywordFadeIn` or `BadgePopup` | Split-screen | Top zone |
| **Name reveal** | `KeywordFadeIn` with glow | Full-screen | Above avatar head |
| **Number + proof** (with asset) | `FramedImage` + `NumberPopup` | Split-screen | Top 40% |
| **Number + proof** (no asset) | `NumberPopup` | Full-screen | Top-left or top-center |
| **Explanation over visual** | `FramedImage` | Split-screen | Top 40% |
| **Direct address** | `AvatarVideo` | Full-screen | — |
| **Trust/credibility** | `FramedImage` + `BadgePopup` | Split-screen | Top 40% |
| **Contradiction/negation** | `StrikethroughSwap` | Full-screen | Center |
| **List item** | `NumberPopup` + `KeywordFadeIn` | Split-screen | Top zone |
| **Hook opening** | `AvatarVideo` + `FramedImage` (responsive/hook-reveal) | Hook-reveal or split | Top portion reveals |
| **Reframe/montage** | Multiple `FramedImage` entries in rapid sequence (StackedImageReveal not yet built) | Split-screen | Top 40% |

**Cinematic-presenter key rule:** Avatar is the anchor. Content always shares the frame with the face via split-screen. Full-screen content is reserved for short proof bursts only.

---

## Step 3 — Audit Asset Fitness

For every beat that uses a visual asset, fill in the fitness matrix:

### Required columns

| Column | What it checks |
|---|---|
| **Beat** | Beat ID from beat-map |
| **Narration** | Exact words the narrator says |
| **What viewer must SEE** | What visual would make these words land (specific, not vague) |
| **Available assets** | All assets from `catalog.json` that could potentially work |
| **Best match** | Which asset fits best |
| **Fitness score** | MATCH / PARTIAL / MISMATCH / MISSING |
| **Issue** | What's wrong if not MATCH |
| **Action** | What to capture/crop/replace if needed |

### Fitness scoring

| Score | Meaning | Action |
|---|---|---|
| **MATCH** | Asset shows exactly what the narrator describes | Use as-is |
| **PARTIAL** | Asset is related but shows the wrong section, angle, or detail | Crop, zoom, or annotate to focus on the right area |
| **MISMATCH** | Asset exists but doesn't match what the narrator says | Find a different asset or re-capture |
| **MISSING** | No asset exists for what the narrator describes | Capture: screenshot, mock, or build animated component |

### Fitness rules

- **Every MISMATCH or MISSING is a blocker.** Do not proceed to technical planning until resolved.
- **PARTIAL scores** need a documented plan (crop coordinates, zoom target, or overlay to compensate).
- **Narrator says a tool name** → the tool's logo or UI must be visible. If not, it's a MISMATCH.
- **Narrator says a number/stat** → the proof visual must show that number or a chart supporting it.
- **Narrator says "look at this" or implies pointing** → a specific visual must be on screen. Generic b-roll is not acceptable.
- **Narrator describes an action** ("it compresses", "it builds") → the visual must show the action or its result, not a static concept image.

---

## Step 4 — Validate Flow

After component selection and asset fitness, read the component sequence and check:

### Rhythm check

Read the component types in order. Flag if:
- More than **3 consecutive beats** use the same component type
- More than **3 consecutive beats** have the avatar in the same layout (all full-screen or all split-screen)
- A **dense section** (proof screenshots, cards) runs longer than 8 seconds without a face return
- A **sparse section** (avatar direct address) runs longer than 5 seconds without visual support

### Layout flow check

The sequence of avatar layouts should feel intentional:

**Good flow:** split → full → split → hidden → split → full → hidden → full
**Bad flow:** full → full → full → full → hidden → hidden → hidden → full

### Component variety check

Count unique component types used across the reel:
- **Minimum 4** for a 25-30s reel
- **Minimum 6** for a 35-50s reel
- **Minimum 8** for a 50s+ reel

If below minimum, the reel will feel visually monotonous.

### Screenshot variety check

Count unique screenshot assets assigned across the reel:
- **Minimum 6** for a 30-40s reel
- **Minimum 8** for a 40-55s reel

Flag if:
- Any single screenshot holds on screen for more than **2 seconds** without a zoom change or hard cut to a different image
- A proof section longer than **2.5 seconds** uses only one screenshot instead of multiple
- Total unique screenshots are below minimum — extract more frames from the source

**One static image doing nothing kills engagement.** Every screenshot beat must either cut to a new image or zoom to a new focal point within 2 seconds.

### Zoom coordinate requirement

Every static screenshot lasting > 1.5 seconds must have at least one `zoom_moment` defined in the technical planning table with specific:
- `x`, `y` — percentage coordinates targeting a specific UI element
- `scale` — zoom level (1.3–2.5 typical)
- `holdFor` — seconds to hold

If a screenshot has no identifiable zoom target, the screenshot is wrong — find a better one. Do not defer zoom planning to assembly or QA.

---

## Output Format

Phase 4b-ii produces these sections in `shot-list.md`:

### Component Mapping Table

```markdown
## Phase 4b-ii — Component Mapping

| Beat | Narration Classification | Component | Avatar Layout | Content Zone | Notes |
|---|---|---|---|---|---|
| beat-01a | hook opening | ScrollingIconGrid + OverlayKeyword | split-screen | top 45% | grid with text overlay |
| beat-02 | direct address | AvatarVideo | full-screen | — | setup energy |
```

### Asset Fitness Matrix

```markdown
## Asset Fitness Audit

| Beat | Narration | Must SEE | Available | Best Match | Fitness | Action |
|---|---|---|---|---|---|---|
| beat-05a | "6x less memory" | memory reduction proof | longbench.png, needle.png | longbench.png | PARTIAL | Crop to memory comparison bars |
```

### Flow Validation

```markdown
## Flow Validation

Component sequence: ScrollingIconGrid → AvatarVideo → HeroTextCard → FramedImage → ...
Avatar layout sequence: split → full → hidden → split → full → ...
Unique components used: 8 ✓
Max same-component streak: 2 ✓
Max same-layout streak: 2 ✓
Longest dense run without face: 5.2s ✓
Longest sparse run without visual: 3.9s ✓
```

---

## Component Inventory Reference

When selecting components, consult this inventory. All components live in `remotion/src/components/`.

### Content presenters
| Component | What it does | Best for |
|---|---|---|
| `AvatarVideo` | Persistent talking-head video | Direct address, setup, CTA, trust |
| `FramedImage` | Static image in frame (split or full) | Screenshots, charts, diagrams, research pages |
| `BRollVideo` | Video clip playback | Demo recordings, cinematic footage |
| `ImageMontage` (planned) | Staggered multi-image stack — **not yet built**, use multiple `FramedImage` entries in sequence | Recap, multi-source validation |

### Text & overlays
| Component | What it does | Best for |
|---|---|---|
| `HeroTextCard` | Giant text on solid bg, fills full frame | Name reveals, concept cards, section labels, emotional keywords (no avatar) |
| `OverlayKeyword` | Large text overlaid on whatever is behind it | Emotional keywords ON avatar, numbers ON charts, CTA text |
| `KeywordFadeIn` | Words fade in with stagger | Feature names, tool names (cinematic style) |
| `NumberPopup` | Colored badge with number + label | Numbered lists, stat reveals (cinematic style) |
| `BadgePopup` | Small pill badge | Labels, tags, source badges |
| `StrikethroughSwap` | Old value crossed out, new value slides in | Before/after, negation (cinematic style) |
| `Caption` | Bottom-of-screen subtitle text | Always present |

### Backgrounds & effects
| Component | What it does | Best for |
|---|---|---|
| `ScrollingIconGrid` | Rotated grid of logo cards, scrolls diagonally | Hook background (editorial style) |
| `AuroraBackground` | White base with drifting pastel blobs | Demo/split scenes (cinematic style) |
| `GradientMesh` | Dark moody gradient | CTA/outro (cinematic style) |
| `FlashReset` | 2-3 frame white flash | Section dividers (editorial style) |
| `ChapterDivider` | Logo + title on solid bg | Tool introductions, section resets |
| `ComparisonGrid` | Side-by-side screenshots with VS divider | A vs B comparisons |
| `CardStack` | Staggered card reveal | Numbered lists, feature lists |
| `AnnotationCircle` | Hand-drawn SVG circle | Calling attention to UI elements |
| `CursorClick` | Cursor with click ripple | Simulating button clicks |
| `NoiseOverlay` | Film grain texture | Always present (subtle) |

### When to build a new component

Only build a new component if:
1. No existing component can render the beat's content
2. The content type will appear in multiple reels (not a one-off)
3. The component can be described in one sentence

If a beat needs a one-off visual, use inline JSX in ReelComposition.tsx instead of creating a new component file.
