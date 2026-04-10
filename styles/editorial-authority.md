# Editorial Authority

**Style ID:** `editorial-authority`

---

## Rule Precedence

**When this style is active, it overrides baseline defaults.**

Resolution order for conflicts:

1. `styles/editorial-authority.md` (this file)
2. Reference-specific overrides (e.g. Lindsay feedback)
3. Project `output/motion-intent.md`
4. Baseline `.claude/rules/visual-style.md`
5. Baseline `.claude/rules/qa-gates.md`
6. Baseline assembly/workflow defaults

Specifically, when this style conflicts with:
- **visual-style.md** backgrounds (Aurora/GradientMesh/Beams) → this style's solid backgrounds win
- **visual-style.md** motion language (Ken Burns, ambient breathe, push-in) → this style's "no ambient motion" wins
- **qa-gates.md** generic thresholds (flash max 1, avatar absence 15s) → this style's thresholds win
- **visual-style.md** display mode defaults → this style's full-frame defaults win

QA must evaluate against **this style's thresholds**, not generic reel defaults.

---

## Style Activation Contract

This style is not just guidance — it is an enforceable pipeline mode. When active, these declarations are **required**:

| Artifact | Required declaration |
|---|---|
| `project.json` | `"style": "editorial-authority"` |
| `shot-list.md` | Every beat tagged with both broad intent AND editorial sub-class |
| `output/motion-intent.md` | Must declare `style_profile: editorial-authority` at the top |
| `output/timeline.json` | Every demo/proof beat must include `"proof_protected": true/false` |
| `output/qa-report.md` | Must include an **Editorial Authority Compliance** section |

If any of these declarations are missing, QA must flag it as a blocker.

---

## Feel

Fast, punchy, proof-led. The edit IS the authority. Every claim is visually confirmed within 45 frames. Talking head exists for trust but is subordinate to the visual evidence. The reel feels like a confident expert showing receipts, not a presenter walking through a feature.

## When to Use

- Listicles ("5 free AI tools", "3 sites you're missing")
- Comparisons ("X vs Y", "why you're doing it wrong")
- Claim-and-prove news ("this just changed everything")
- Tool roundups and rankings
- "Stop paying for X" or "you don't need X" persuasion reels

## Reference Style

- micro-claim → visual proof → replace cycle
- hard cuts over smooth transitions
- giant center-weighted typography on color cards
- screenshot swaps with flash resets between sections
- talking-head used as trust anchoring, not narrative throughline
- aggressive pacing — no moment overstays

---

## Pacing

- **Visual change frequency:** every 1-3 seconds
- **Typical duration:** 25-40 seconds
- **Beat density:** 12-20 beats (more beats, shorter each)
- **Word density:** high (160-190 wpm spoken)
- **Hold time:** no proof frame may remain unchanged for more than 60 frames (2s) unless it is a title card or CTA hold
- **Dead air:** no empty editorial gaps. Every frame must be owned by one of: outgoing hold, incoming proof, title-card reset, flash reset, or avatar reaction frame. Silence is allowed only when visually owned.

---

## Beat Sub-Classes

Every beat has a broad intent (hook, setup, proof, trust, CTA) from the standard pipeline. Editorial-authority adds **sub-classes** that refine how the beat renders:

| Sub-class | Broad intent | Visual behavior |
|---|---|---|
| `hook-card` | hook | ScrollingIconGrid + avatar split, or title card |
| `talking-head` | setup, trust, CTA | Avatar full-screen, overlay text optional |
| `proof-screenshot` | proof | Full-frame screenshot, hard cut in/out, 1.5-2s |
| `proof-chart` | proof | Full-frame chart/data visual, hard cut |
| `proof-video` | proof | Full-frame video clip, hard cut |
| `contradiction-card` | proof | Avatar full-screen + strikethrough overlay |
| `numbered-card-stack` | proof | Cards slide-stack in sequence |
| `chapter-divider` | setup | Logo + wordmark on white, gentle scale |
| `comparison-layout` | proof | Side-by-side screenshots |
| `cta-overlay` | CTA | Avatar full-screen + text overlay, hold to end |

Shot-list.md must tag every beat with one of these sub-classes in addition to the broad intent.

---

## Proof-Protected Beats

Proof-protected beats require real evidence assets as their primary visual. B-roll, stock footage, or decorative visuals may not replace the proof asset unless explicitly approved as a style tradeoff.

### B-roll is FORBIDDEN as a primary visual on:

- Numerical proof beats (stats, benchmarks, results)
- Chart/result beats
- Trust/credibility beats with real source screenshots
- Named-source beats (showing a specific product's UI)
- Side-by-side comparison beats
- Ranking/result screens

### B-roll is ALLOWED for:

- Conceptual setup (explaining an idea before proof)
- Mechanism support (illustrating how something works)
- Bridge/reset texture (brief visual between proof blocks)
- CTA support
- Brief reframe support

### Enforcement

In `output/timeline.json`, every demo/proof entry must include:
```json
"proof_protected": true
```
for beats that require real evidence. QA must verify that proof-protected beats use genuine source assets.

---

## Avatar Behavior

Avatar is trust infrastructure, not the star.

- **On screen:** 45-55% of reel
- **Primary use:** hook intro (1-2s), claim delivery, contradiction beat, CTA close
- **Layout:** always full-screen when visible, EXCEPT:
  - Hook (ScrollingIconGrid top 45%, avatar bottom 55%)
  - Proof with narration (screenshot top 40%, avatar bottom 60%)
  - Trust/credibility (screenshot top, avatar bottom)
- **Jump cuts:** tight trims between sentences, never continuous delivery
- **Re-entry:** hard cut back, no scale-settle — the edit is the transition
- **Rule:** avatar never runs more than 4 seconds without a proof visual interrupting

### Avatar absence thresholds

- **Preferred max:** 8 seconds continuous absence
- **Hard max:** 12 seconds continuous absence
- **Single-block rule:** only ONE continuous >8s avatar absence per reel, and only if the entire block is proof-protected beats
- If a second >8s absence block is needed, break it with a face return (even 1-2s)

---

## Transition Defaults

Hard cuts are the default transition. They do not count toward transition variety and do not require compensating SFX. Use animated transitions only for title-card entrances, numbered-card stacks, chapter dividers, and flash resets.

### Transition table

| Context | Enter | Exit | Duration |
|---|---|---|---|
| Title card | `scale-pop-overshoot` | `hard-cut` | enterDur: 5, exitDur: 0 |
| Screenshot proof | `hard-cut` | `hard-cut` | enterDur: 0, exitDur: 0 |
| Section reset | `flash-reset` | — | 2-3 frames white |
| Numbered card | `slide-stack` | `hard-cut` | enterDur: 6, exitDur: 0 |
| Avatar return | `hard-cut` | `hard-cut` | enterDur: 0, exitDur: 0 |
| Chapter divider | `fade` | `fade` | enterDur: 4, exitDur: 3 |
| CTA close | `hard-cut` | hold | enterDur: 0 |

### Implementation mappings

These editorial-authority presets map to Remotion implementation as follows:

| Preset name | Implementation |
|---|---|
| `hard-cut` | enterDur: 0, exitDur: 0, no transition component — instant appear/disappear |
| `flash-reset` | 2-3 frame `<Sequence>` containing `<FlashReset>` component at full white opacity, placed between outgoing and incoming content |
| `scale-pop-overshoot` | HeroTextCard-specific preset — spring scale 0.85 → 1.03 → 1.0 over 5 frames, config: { damping: 12, stiffness: 200, mass: 0.6 } |
| `slide-stack` | Sequential card entrances with 6-frame stagger, translateX from right with slight rotation, spring config |

### Variety rules

- Hard cuts don't count toward transition variety — they're the baseline
- Flash resets: **max 2 per reel for reels under 35s, up to 3 for 35s+**
- Scale pops are for emphasis text only

---

## Typography

This style uses typography as a primary visual element, not just labels.

### Hero Text (HeroTextCard)

- **Size:** 80-140px (massive, fills the frame)
- **Weight:** 900 / black
- **Alignment:** center, vertically and horizontally
- **Font:** system-ui or Inter Black
- **Color:** white on dark, black on white, red for negation
- **Shadow:** subtle dark shadow (2px 2px 8px rgba(0,0,0,0.5))
- **Entry:** scale-pop-overshoot (5 frames)
- **Hold:** completely still — no breathe, no drift
- **Exit:** instant cut (0 frames)
- **Duration:** 0.8-1.5s per card

### When to use hero text (avatar hidden)

- Name reveals ("GOOGLE STITCH")
- Section labels ("THE RESULTS")
- Concept cards ("JEVONS' PARADOX")

### When to use OverlayKeyword (avatar visible)

- Emotional keywords ("FREE", "ZERO", "GONE")
- Staccato claims ("NO RETRAINING")
- Contradiction punches ("MOCKUPS" with strikethrough → "REAL CODE")
- CTA commands ("FREE AI TOOLS")

**Core rule (Lindsay reference):** Text goes ON the avatar whenever possible. Only hide the avatar for name reveals, concept cards, and section labels. Everything else keeps the face visible.

### Caption style

- Bottom safe zone, rounded gray boxes
- Faster chunk timing: 0.5-1.0s per chunk (vs cinematic 0.6-1.2s)

---

## Color System

### Palette per section type

| Section | Background | Text | Accent |
|---|---|---|---|
| Hook/intro | Deep purple (#2D1B69) or black | White | Glow/bloom on icons |
| Proof/screenshot | White (#FFFFFF) — plain, no effects | Black | Product brand color |
| Contradiction | Gray (#1A1A1A) | Red (#DC2626) | — |
| Ranking | Mustard/beige (#F5E6CC) | Dark brown (#3D2B1F) | Gold |
| Tool section | Product brand bg | White | Brand secondary |
| Chapter divider | White (#FFFFFF) | Black | Logo color |
| CTA | Dark (#111111) | White | — |

### Key difference from cinematic

Backgrounds are mostly **solid colors**, not Aurora/GradientMesh/Beams. The visual richness comes from the content and typography, not the background.

### HeroTextCard backgrounds

Solid or near-solid only:
- Solid color fill
- Subtle radial gradient (same hue, 10% lighter at center)
- No Aurora, no mesh gradients, no animated backgrounds

---

## Motion Language

### Philosophy

Motion serves the edit, not the aesthetics. Every motion either:
1. Delivers information faster (screenshot swap)
2. Creates emphasis (scale pop on keyword)
3. Resets attention (flash between sections)

If a motion does none of these, remove it.

### Motion budget per beat

- **1 hero motion** — the visual swap or text entrance
- **0-1 support motion** — cursor click, card slide, screenshot crop
- **0-1 accent** — only on spoken emphasis words, and only scale-pop or color flash
- **No ambient motion** on title cards, screenshots, charts, contradiction cards, or avatar beats. Exception: only native motion inside captured video assets is allowed.
- **No decorative layers** — no shimmer, no glow border, no noise overlay in this style

### Beat category motion rules

**Talking-head beats:**
- Hard cut in, hard cut out
- No scale settle, no push-in
- Overlay text on emphasis keywords (center-chest position)
- Avatar is cropped tight (head + shoulders)

**Title card beats:**
- Scale-pop-overshoot entry (5 frames)
- Hold completely still
- Hard cut exit
- Duration: 0.8-1.5 seconds

**Proof beats (screenshots/video):**
- Hard cut in, hard cut out
- Optional cursor-click or annotation circle on key element
- Duration: 1.5-2s per screenshot (no single screenshot >60 frames unchanged)
- Video clips play at native motion — no added Ken Burns

**Card/list beats:**
- Slide-stack stagger (6 frames between cards)
- Slight rotation on entry
- Hold once visible, hard cut to next section

**CTA beats:**
- Avatar center framed
- Overlay text builds word by word
- Final keyword stays large and readable
- No exit — reel ends on the CTA frame

### Gap ownership

No empty editorial gaps. Every frame must be owned by one of:
- Outgoing beat hold (last frame stays visible)
- Incoming proof (enters before the gap ends)
- Title-card reset
- Flash reset
- Avatar reaction frame

Silence is allowed only when visually owned.

---

## Proof Visibility Rules (machine-checkable)

These replace vague editorial guidance with enforceable thresholds:

1. Every spoken claim containing a **number, tool name, or visible noun** must have matching visual proof within **45 frames** (1.5s), unless the beat is a contradiction card or CTA
2. No proof frame may remain **unchanged for more than 60 frames** (2s) unless it is a title card or CTA hold
3. No more than **2 consecutive beats** may use the same visual sub-class (e.g. two proof-screenshots in a row is fine, three requires a talking-head or card between them)
4. At least **40% of beats** must include direct-source proof or screenshot evidence
5. No more than **3 dense frames** (proof, chart, comparison, card-stack) in a row without a **sparse reset** (talking-head, title card, chapter divider)
6. No more than **2 sparse frames** in a row without dense proof

---

## Center-Full Thresholds

- **Preferred max:** 4 consecutive center-full entries before a face return, card reset, or divider
- **Conditional max:** 5 consecutive center-full entries, but only if at least 3 of those 5 are **materially different sub-classes** (e.g. screenshot → chart → contradiction → screenshot → ranking)
- 5 consecutive entries of the same sub-class (e.g. 5 screenshots) is never allowed

---

## SFX Behavior

SFX are editorial punctuation, not decoration.

### When to use SFX

- **Hit/impact** on title card slams and contradiction beats — short, punchy
- **Subtle click** on cursor-click overlays and screenshot swaps
- **Whoosh** on card slide-ins (quick, not dramatic)
- **Pop** on scale-pop text entries (light, not cartoony)
- **Notification** on CTA shift

### When NOT to use SFX

- **No SFX on hard cuts** — the cut itself is the punctuation
- **No SFX on talking-head segments** — let the voice carry
- **No ambient bed** — voice only, SFX only
- **Do not add SFX just to hit a quota** — every SFX must land on a real editorial event

### Volume and count

- Volume: 0.2-0.5 range
- **Target range for 25-35s reel: 5-9 purposeful SFX**
- Target range for 35-45s reel: 7-12 purposeful SFX

---

## Display Modes

| Mode | When |
|---|---|
| Full-screen avatar | Talking-head segments (cropped tight) |
| Full-screen card | Title cards, contradiction beats, hero text |
| Full-screen proof | Screenshot/video fills the frame |
| Split-screen (hook) | ScrollingIconGrid top 45%, avatar bottom 55% |
| Split-screen (proof) | Screenshot top 40%, avatar bottom 60% |
| Split-screen (trust) | Evidence top 40%, avatar bottom 60% |
| Comparison | Side-by-side screenshots |
| Stacked cards | Numbered list items |

### Split-screen rules

Unlike the original spec, editorial-authority DOES use split-screen for:
- **Hook**: scrolling grid / visual in top 45%, avatar in bottom 55%
- **Proof with narration**: screenshot/chart in top 40%, avatar in bottom 60%
- **Trust/credibility**: evidence in top 40%, avatar in bottom 60%

Split-screen is NOT used for:
- Name reveals (full-screen card)
- Emotional text on face (OverlayKeyword, avatar full-screen)
- Avatar direct address (avatar fills frame)

---

## Editing Formula

The edit follows a persuasion structure:

1. **Hook visually first** — big title or logo before context (0-2s)
2. **Talking head to humanize** — just enough face for trust (2-4s)
3. **Interrupt with contradiction** — negation resets attention
4. **Reveal with proof** — structured, visual evidence
5. **Alternate dense and sparse** — busy proof → clean talking head → busy proof
6. **Giant text on emotional keywords** — one word fills the frame
7. **End with simple command** — CTA is unmistakable, reel ends on it

### Dense/sparse rhythm

The reel must alternate between information-dense frames (screenshots, comparisons, cards) and information-sparse frames (talking head, title cards, dividers).

- Never more than 3 dense frames without a sparse reset
- Never more than 2 sparse frames without dense proof
- The rhythm creates breathing room without losing pace

---

## Component Decision Guide

### Core principle (Lindsay reference)

**Text goes ON the avatar whenever possible.** Only hide the avatar for name reveals, concept cards, section labels, and full-screen proof screenshots.

### Component preference order

| Narration type | First choice | Avoid |
|---|---|---|
| Emotional keyword | OverlayKeyword on avatar | HeroTextCard (hides face) |
| Staccato claim | OverlayKeyword on avatar | HeroTextCard |
| Name reveal | HeroTextCard | OverlayKeyword (name deserves full frame) |
| Number + proof (with asset) | Split FramedImage + OverlayKeyword | Full-screen without number overlay |
| Explanation + visual | Split FramedImage + avatar | Full-screen with no face |
| Direct address | AvatarVideo full-screen | Any visual layer |
| Trust/credibility | Split FramedImage + AnnotationCircle + avatar | Full-screen without face |
| Contradiction | OverlayKeyword with strikethrough on avatar | StrikethroughSwap (too complex) |
| Hook opening | ScrollingIconGrid top + avatar split bottom | Solid color bg (too flat) |
| CTA | AvatarVideo + OverlayKeyword | Dark bg card without face |

---

## Components Used / Not Used

### Used in this style

| Component | Use |
|---|---|
| `HeroTextCard` | Name reveals, section labels, emotional keywords (avatar hidden) |
| `FlashReset` | Section dividers (2-3 frame white flash) |
| `OverlayKeyword` | Emphasis words on avatar face |
| `BadgePopup` | Small pill labels ("FREE", "350/month") |
| `ScrollingIconGrid` | Hook background |
| `FramedImage` | Split-screen proof screenshots |
| `BRollVideo` | Proof video clips (center-full) |
| `AnnotationCircle` | Callout circles on UI elements |
| `CursorClick` | Cursor with click ripple |
| `ComparisonGrid` | Side-by-side screenshots |
| `Caption` | Bottom captions |
| `AvatarVideo` | Talking head |
| `StrikethroughSwap` | Negation with red line |

### NOT used in this style

| Component | Why excluded |
|---|---|
| `AuroraBackground` | Too soft — solid colors only |
| `SmokeWisp` | Too atmospheric |
| `FocusVignette` | Too cinematic |
| `GlowBorder` | Decorative — violates "no decorative layers" |
| `ShimmerBar` | Decorative |
| `NoiseOverlay` | Decorative |
| `GradientMesh` | Too moody — solid darks replace it |
| `BackgroundBeams` | Too soft |
| `KeywordFadeIn` | Cinematic style — editorial uses OverlayKeyword instead |
| `NumberPopup` | Cinematic style — editorial uses OverlayKeyword or BadgePopup |

---

## QA Thresholds (editorial-authority specific)

These override the baseline qa-gates.md thresholds when this style is active.

| Check | Threshold |
|---|---|
| Visual change frequency | every 1-3s |
| Avatar on-screen % | 45-55% |
| Avatar absence (preferred) | 8s max |
| Avatar absence (hard max) | 12s — only ONE >8s block per reel, proof-protected only |
| Consecutive center-full (preferred) | 4 |
| Consecutive center-full (conditional max) | 5, only if 3+ entries are different sub-classes |
| SFX target (25-35s reel) | 5-9 purposeful entries |
| SFX target (35-45s reel) | 7-12 purposeful entries |
| Visual variety (distinct states) | 10-15 |
| Dead air tolerance | 0 (none) |
| Flash resets | 2 for <35s, up to 3 for 35s+ |
| Ken Burns | Not used |
| Ambient motion | Not used |
| Proof frame hold limit | 60 frames (2s) max unchanged |
| Claim-to-proof latency | 45 frames (1.5s) max |
