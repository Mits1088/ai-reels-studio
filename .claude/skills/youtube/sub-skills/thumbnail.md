# YouTube Thumbnail Sub-skill

**Invoked by:** `/youtube thumbnail`

Generate a detailed thumbnail design brief with 3 A/B test variants. Each brief is specific enough for a designer to execute without additional clarification.

---

## Load Reference Guide

Read `.claude/skills/youtube/references/thumbnail-ctr.md` before writing.

---

## Required Inputs

- `projects/<slug>/youtube/seo-package.md` — for the confirmed title variant
- `projects/<slug>/project.json` — for `theme_primary` and `theme_secondary` hex colors
- `projects/<slug>/brief.md` — for the product/topic and audience

The thumbnail palette must align with the reel's theme colors from `project.json`. This creates visual brand consistency across the YouTube video and the Instagram reel.

---

## Design Principles (read first)

**The job of a thumbnail is to answer one question in under one second:** "Is this video for me?"

A thumbnail is not a poster. It is not decoration. It has one job: make the viewer click because they believe the video will give them something they want.

**The five thumbnail laws:**
1. **Focal point** — one dominant subject (face, object, or result). Not two. Not three.
2. **Maximum 3 words** of text overlay (2 is ideal, 1 is better). Every extra word is visual noise.
3. **Maximum 3 colors** — primary, secondary, contrast. More than 3 = visual chaos.
4. **Emotion** — if a face is used, it must communicate a specific, readable emotion. "Excited" is too vague. "Discovering something surprising" is specific.
5. **Information split** — the thumbnail must say something DIFFERENT from the title. Never repeat the title text verbatim in the thumbnail.

---

## Step 1 — Competitor Thumbnail Analysis

Before designing, research 3-5 top-ranking thumbnails for the primary keyword.

Identify:
- **Common patterns** (face + text, result screenshot, before/after, number tiles)
- **Color saturation trends** (are top performers high-contrast or muted?)
- **Face presence** (are top performers face-led or product-led?)
- **Text placement zones** (left third, right third, bottom bar?)
- **What a contrarian thumbnail would look like** — something that stands out against the dominant pattern

Note the competitor patterns in the brief so the designer understands what NOT to copy.

---

## Step 2 — Primary Thumbnail Brief

Generate the primary thumbnail specification:

```markdown
## Primary Thumbnail

### Concept in one sentence
[What this thumbnail communicates, independent of the title]

### Focal Point
- **Primary subject:** [Face / Product screenshot / Result / Object — be specific]
- **Position:** [Rule of thirds: left-third / center / right-third] 
- **Size:** [Percentage of frame — aim for 40-60% for dominant focal point]

### Face / Expression (if face is used)
- **Emotion:** [Specific state — not "excited" but "mid-sentence, eyes wide, eyebrows raised at something off-left"]
- **Eye direction:** [To camera / To text / To object off-frame]
- **Avoid:** [Specific expressions to avoid for this video's tone]

### Background
- **Type:** [Solid color / Gradient / Location / Product UI blurred]
- **Primary color:** [Hex code — from project.json theme_primary or contrast color]
- **Notes:** [Any texture, depth, or treatment notes]

### Text Overlay
- **Text:** [Maximum 3 words — ideally 1-2]
- **Font style:** [Bold, sans-serif / Slab / Display — be specific enough for a designer]
- **Font size:** [Large / Very large — must be readable at 168×94px mobile size]
- **Position:** [Specific: top-left / right-third / bottom-bar]
- **Text color:** [Hex code]
- **Outline/stroke:** [Color + thickness, or "none"]
- **Drop shadow:** [Yes/No + color if yes]

### Color Palette
- **Primary:** [Hex] — [name and purpose]
- **Secondary:** [Hex] — [name and purpose]
- **Contrast / accent:** [Hex] — [name and purpose]
- **Why these colors:** [1 sentence on the psychological effect and brand alignment]

### Composition
- **Layout:** [Describe the visual weight distribution — left-heavy, centered, etc.]
- **Negative space:** [Where — top-right / bottom-left / etc.]
- **Visual flow:** [Where the eye enters and where it lands]
- **Depth treatment:** [Any foreground/background layering]

### Mobile Legibility Check (168×94px)
- **Visible at small size:** [What remains legible]
- **Remove at small size:** [What becomes noise]
- **Text minimum size:** [Is the text large enough to read on a phone?]

### Title-Thumbnail Synergy
- **Information the thumbnail adds that the title does NOT:** [Specific visual element]
- **Emotional signal the thumbnail carries:** [What feeling the viewer gets before reading the title]
- **Curiosity gap created:** [What question the combination raises in the viewer's mind]

### DO NOT Include
1. [Specific element to avoid — with reason]
2. [Specific element to avoid — with reason]
3. [Specific element to avoid — with reason]
```

---

## Step 3 — Generate 3 A/B Variants

Each variant changes exactly ONE variable from the primary brief. A/B tests with two variables changed are uninterpretable. One variable per test.

**Variant B:**
```markdown
## Variant B

**Variable changed from Primary:** [Name exactly one thing]
**What changes:** [Specific description of the change]
**Why test this:** [Performance hypothesis — "We expect higher CTR from Browse because..."]
**Target segment:** [Who this variant speaks to better than the Primary]
**Predicted CTR direction:** [Up / Down / Neutral vs Primary — with reason]
```

**Variant C:**
```markdown
## Variant C

**Variable changed from Primary:** [Name exactly one thing]
**What changes:** [Specific description]
**Why test this:** [Performance hypothesis]
**Target segment:** [Who this variant speaks to better]
**Predicted CTR direction:** [Direction vs Primary — with reason]
```

**Variant D:**
```markdown
## Variant D

**Variable changed from Primary:** [Name exactly one thing]
**What changes:** [Specific description]
**Why test this:** [Performance hypothesis]
**Target segment:** [Who this variant speaks to better]
**Predicted CTR direction:** [Direction vs Primary — with reason]
```

**Good variables to A/B test:**
- Face vs no-face (tests whether the product or the creator drives clicks for this topic)
- Text overlay vs no text (tests whether the visual is self-explanatory)
- Background color (tests which color family performs better in the SERP)
- Expression intensity (subtle vs dramatic expression on face)
- Image type (screenshot of result vs creator face — tests proof vs presenter)

---

## Step 4 — Synergy Validation

Check all 5 synergy rules for the Primary brief:

```markdown
## Title-Thumbnail Synergy Check

**Title:** [Selected title from seo-package.md]
**Thumbnail concept:** [One-sentence summary]

| Rule | Pass/Fail | Notes |
|---|---|---|
| 1. Information split — thumbnail adds NEW info, doesn't repeat title text | Pass/Fail | [What each communicates] |
| 2. Emotional alignment — thumbnail emotion matches title's emotional tone | Pass/Fail | [Title tone vs thumbnail emotion] |
| 3. Curiosity amplification — together they raise a question the viewer wants answered | Pass/Fail | [The question created] |
| 4. Text overlap check — no words appear in both title and thumbnail text | Pass/Fail | [Overlap check result] |
| 5. Mobile readability — all key elements visible at 168×94px | Pass/Fail | [What's visible / what's lost] |

**Synergy verdict:** [Pass / Needs revision — state which rule failed and how to fix]
```

---

## Step 5 — CTR Benchmark Context

Provide benchmarks from `thumbnail-ctr.md` for this niche:

```markdown
## CTR Benchmark Context

**Niche:** [Topic area]
**Average CTR for this niche:** [X%]
**Top 10% CTR target:** [Y%]
**What this thumbnail must achieve:** [Specific CTR goal based on channel size]
**Key risk:** [Main reason a viewer might NOT click — design must address this]
```

---

## Reel Brand Consistency

The thumbnail must visually connect to the reel's brand identity:
- Use `theme_primary` from `project.json` as the dominant color or accent
- If the reel uses a specific brand logo (from `remotion/public/brands/`), the thumbnail can include the same logo
- Font weight and style should feel consistent with the reel's text overlays (from the component mapping)

State the brand alignment choices explicitly in the brief.

---

## Output

Produce `projects/<slug>/youtube/thumbnail-brief.md` with:
1. Competitor pattern notes
2. Primary thumbnail brief (full spec)
3. Variants B, C, D
4. Synergy validation table
5. CTR benchmark context

---

## Stop Condition

Deliver `thumbnail-brief.md`. Present for review.

The thumbnail brief is design-ready — a designer can execute it without asking questions. If any field in the primary brief is vague or says "TBD," revise it before delivering.
