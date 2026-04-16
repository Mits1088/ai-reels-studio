# YouTube Thumbnail CTR Guide

Reference for the `youtube` skill suite. Read before generating any thumbnail brief.

---

## CTR Benchmarks by Niche

| Niche | Average CTR | Top 10% target |
|---|---|---|
| AI / Technology tools | 5-8% | 10-14% |
| Education / Tutorials | 4-6% | 8-12% |
| Finance / Business | 3-5% | 8-10% |
| Gaming | 7-10% | 14-18% |
| Entertainment / Vlog | 6-9% | 12-16% |

**Channel size effects on CTR:**
- New channel (<10K subs): CTR appears lower because most impressions come from cold Browse audiences. Target 4-6%.
- Growing channel (10K-100K subs): Mix of warm and cold. Target 6-9%.
- Established channel (100K+): Higher proportion of warm subscribers. Target 8-12%.

---

## The CTR Lifecycle of a Video

1. **Upload day (hours 0-24):** Highest CTR — subscriber base is warm, they trust the channel
2. **Days 2-7:** CTR stabilizes as YouTube tests broader audiences
3. **Weeks 2-4:** Mature CTR — now primarily cold Browse audiences
4. **Months+:** Evergreen — CTR stabilizes low but consistent (search traffic dominant)

A thumbnail designed only for warm subscribers (niche references, inside-joke energy) will underperform with cold Browse audiences. Design for the coldest viewer who would plausibly click.

---

## The Anatomy of a High-CTR Thumbnail

### 1. Focal Point (non-negotiable)
One dominant visual subject that the eye lands on in under 0.5 seconds.
- **Face:** Highest universal CTR impact — faces with strong readable emotion outperform faceless thumbnails by an average 20-30%
- **Result/Product:** Strong for tutorials when the result is more compelling than the creator's face
- **Text-only:** Works only when the words themselves are the message (controversial, challenge, revelation)

**Rule:** One focal point. Two competing subjects split the eye and reduce CTR.

### 2. Expression Specificity (when using face)
Generic expressions underperform specific, readable ones.

| Generic (avoid) | Specific (use) |
|---|---|
| Surprised | Eyes wide, mouth open, both hands up — maximum surprise |
| Happy | Smiling directly at camera with genuine warmth |
| Thinking | Chin down, eyes up and to the right, slight squint |
| Excited | Pointing at something off-frame, eyebrows fully raised |

The expression must be readable on a 168×94px mobile thumbnail. If the expression requires the viewer to zoom in to understand it, it won't work.

### 3. Text Overlay
- **Maximum 3 words.** 2 is better. 1 is strongest for simple concepts.
- Every additional word beyond 3 reduces the thumbnail's legibility at small sizes
- Text must add information the title does NOT contain (information split rule)
- Font: bold, high contrast, with stroke or drop shadow — no thin fonts
- Minimum size: readable at 168×94px (a 168px-wide mobile thumbnail)

**Common text overlay mistakes:**
- Repeating the title verbatim (wastes the space — viewer sees it twice)
- Too many words (becomes unreadable at small sizes)
- Low contrast text (light font on light background)
- Decorative fonts that sacrifice legibility

### 4. Color Palette
- **Maximum 3 colors:** primary (background/dominant), secondary (subject), contrast (text/accent)
- High contrast between subject and background drives the eye
- Warm colors (orange, red, yellow) have higher attention grab in Browse feed
- Cool colors (blue, teal) read as authoritative/informational — better for tutorial content
- Black backgrounds with bright accents: dramatic, high-CTR for tech content

**Brand color integration:**
When aligning with the reel's visual brand (from `project.json` theme_primary), use the brand color as one of the three — not necessarily the dominant color. A strong brand color as a contrast accent is more effective than a muted brand color as the dominant background.

### 5. Composition Principles
- **Rule of thirds:** Place focal point at a third-line intersection, not center
- **Negative space:** Leave 30-40% of the frame as negative space — overcrowded thumbnails have lower CTR
- **Visual flow:** The eye should move from the most important element to the second most important, not jump randomly
- **Depth:** Foreground subject slightly in front of background detail creates natural visual hierarchy

---

## The Information Split Rule

**The thumbnail must say something the title does not.**

If the title is: "How I Use Claude to Save 10 Hours Per Week"
- Bad thumbnail text: "Save 10 Hours" — repeats the title
- Good thumbnail visual: The result (a finished project, a clean output on screen) — proves the claim visually
- Good thumbnail text: "AUTOMATE" — adds a word not in the title

The title tells the viewer WHAT the video is about. The thumbnail shows them WHY they should believe it or makes them feel something about it.

---

## Mobile Legibility Check (168×94px)

70%+ of YouTube views are on mobile. Every thumbnail must be checked at 168×94px.

At 168×94px:
- Text under 40pt is typically unreadable
- Subtle textures and gradients collapse to flat colors
- Small faces lose all expression
- Thin borders and lines disappear
- More than 3 visual elements compete for attention

**Design for the small size first, then scale up.**

---

## A/B Testing Framework

YouTube Studio supports A/B testing (up to 3 variants over 2 weeks). YouTube optimizes for watch time share, not just CTR — a lower-CTR thumbnail that leads to higher watch time may still "win."

**What to test (one variable at a time):**
1. **Face vs no face** — Tests whether creator presence or product proof drives more clicks
2. **Text overlay vs no text** — Tests whether the visual is self-explanatory
3. **Background color** — Tests color response in this specific audience
4. **Expression intensity** — Tests subtle vs dramatic emotion
5. **Subject type** — Tests before vs after, input vs output, tool vs result

**What NOT to test:**
- Two completely different thumbnails (can't isolate the variable)
- Thumbnail + title change simultaneously (can't attribute the result)

---

## Do-Not-Include Patterns

These consistently reduce CTR or violate YouTube policy:

**Avoid for performance:**
- More than 3 colors (visual chaos)
- More than 3 words of text (illegible at mobile size)
- Two faces with competing expressions (viewer doesn't know where to look)
- Stock photo backgrounds (read as low-effort, generic)
- Borders with no visual function
- Lens flares and glow effects (dated visual language)

**Avoid for policy:**
- Misleading imagery that doesn't match video content
- Thumbnail that implies a result the video doesn't show
- Sexually suggestive content (immediate policy violation)
- Faces without expressions (empty face thumbnails underperform and feel uncanny)

---

## AI/Tech Niche Specific Notes

For the AI tools and technology tutorial niche:
- **Product UI screenshots as background:** Strong CTR for search-intent viewers already familiar with the tool
- **Creator face + product UI split:** High performer — combines creator trust with proof signal
- **Dark backgrounds (deep navy, black):** High CTR in AI/tech — reads as sophisticated, not consumer
- **Orange/amber accents:** Perform well in AI/tech — warm contrast against dark backgrounds
- **"Before/After" implied:** Thumbnails showing transformation (messy input → clean output) outperform single-state thumbnails
