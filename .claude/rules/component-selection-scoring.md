---
description: Weighted scoring criteria, repetition penalties, and underused component encouragement for Phase 4b-ii selection
globs: ["**/shot-list.md"]
---

# Component Selection Scoring

Read alongside `component-mapping.md` during Phase 4b-ii. This file defines how to choose among the candidate set — it does not define what the candidates are (that's in component-mapping.md Step 2b).

---

## Why Scoring Exists

Component mapping provides a curated candidate set for each beat class. Scoring selects among valid options in a principled way — preventing habitual selection of the same defaults while remaining structurally controlled.

This is not randomization. It is structured selection with explicit criteria.

---

## Visual Role & Layout Role Taxonomy

Component names alone cannot detect fake variety — using `CharKeyword` instead of `KeywordFadeIn` is a different component but the same visual function. These two taxonomies measure what the viewer *experiences*, not what the component is named.

### Visual Roles — what visual function does this beat perform?

| Visual role | What the viewer sees | Components |
|---|---|---|
| `text-emphasis` | Words on screen ARE the beat — the text is the primary visual event | `OverlayKeyword`, `KeywordFadeIn`, `CharKeyword`, `HeroTextCard` (as emphasis), `GlitchText` |
| `proof-display` | Product evidence as primary visual — screenshot, demo video, or mockup | `FramedImage` (standalone), `BRollVideo`, `FeatureMockup`, `TypingText` (demo context) |
| `annotation-focus` | Proof visual with a directing element that focuses attention on a specific element | `FramedImage` + `AnnotationCircle`, `FramedImage` + `CursorClick` |
| `credibility-signal` | Short-burst authority evidence — institutional trust or social proof | `ToastCard`, `BadgePopup` (as primary), `LogoOverlay` (trust context), `FramedImage` + `BadgePopup` |
| `avatar-anchor` | Human face is the primary visual; narrator presence IS the beat | `AvatarVideo` full-screen with minimal overlay |
| `comparison` | Side-by-side or before/after structure; the contrast IS the message | `ComparisonGrid`, `StrikethroughSwap` |
| `list-structure` | Enumerated items as primary visual pattern | `CardStack`, `NumberPopup` series |
| `reset-interrupt` | Editorial break that interrupts and resets the current visual flow | `FlashReset`, `ChapterDivider`, `LightLeakOverlay`, `HeroTextCard` (section label) |

### Layout Roles — how does this beat occupy the frame?

| Layout role | Frame structure | Typical components |
|---|---|---|
| `text-on-avatar` | Words overlaid on the avatar face; face visible behind text | `OverlayKeyword` on `AvatarVideo` full-screen |
| `split-content` | Product content top 40%, avatar bottom 60% | `FramedImage`, `KeywordFadeIn`, `FeatureMockup`, `NumberPopup` |
| `center-full` | Full frame to product content; avatar hidden | `BRollVideo` center-full, `FramedImage` center-full |
| `full-frame-card` | Full frame to text or graphic card; no avatar | `HeroTextCard`, `ChapterDivider`, `ComparisonGrid`, `CardStack`, `CharKeyword`, `GlitchText` |
| `annotation-overlay` | Split-content with annotation drawn on top of the proof visual | `FramedImage` + `AnnotationCircle` combo |
| `full-screen-avatar` | Avatar fills entire frame; no product content | `AvatarVideo` direct address |
| `corner-micro` | Small badge/logo in a corner; primary layout unchanged beneath | `BadgePopup`, `LogoOverlay` (corner), `ToastCard`, `NumberPopup` (brief) |
| `side-by-side` | Two equal-weight panels; content fills both halves | `ComparisonGrid`, `StrikethroughSwap` (full-frame) |

---

## Scoring Criteria

Score each candidate 1–10 on each criterion. Multiply by weight, sum the products. Highest score wins.

| Criterion | Weight | What it measures |
|---|---|---|
| **Semantic fit** | 35% | Does this component render exactly what the narrator is saying at this moment? 10 = component is purpose-built for this narration pattern. 5 = works but generic. 1 = technically possible but wrong register. |
| **Asset fitness** | 20% | Does the best available asset work well with this component? 10 = MATCH (shows exactly what narrator describes). 6 = PARTIAL (requires annotation or crop). 1 = MISSING (no suitable asset). |
| **Proof strength** | 15% | Does this component make the claim convincing? 10 = viewer sees the evidence directly. 5 = viewer sees a supporting visual. 1 = viewer has to take narrator's word for it. |
| **Reel novelty** | 15% | How many times has this component type already appeared this reel? 10 = first use. 7 = second use. 4 = third use. 1 = fourth or more. |
| **Motion load compatibility** | 10% | Is the surrounding sequence already motion-dense? 10 = this component adds appropriate energy to a calm section. 5 = neutral. 1 = adding this to an already-dense sequence creates overload. |
| **Cross-reel novelty** | 5% | Was this the primary emphasis component in the most recent reel on this same product? 10 = no. 5 = similar use but different beat context. 1 = same component in the same role. |

### Tie-breaking

If two candidates are within 5 total points of each other: prefer the one with higher reel novelty score. Variety breaks ties.

---

## Repetition Penalties

Apply these as negative adjustments to the candidate's score BEFORE final comparison. Penalties stack.

| Condition | Score penalty | Why |
|---|---|---|
| `KeywordFadeIn` used as primary overlay 2+ times already this reel | −25 | Signal drops fast; viewer stops reading it after the second appearance |
| `OverlayKeyword` appears in 4+ beats already this reel | −20 | Loses emphasis weight through frequency |
| Same component type in the directly preceding beat | −15 | Adjacent sameness is the most visible repetition |
| Same component type in both preceding beats (streak of 3) | −30 | Hard cap — do not allow streaks beyond 2 |
| Text-only emphasis (`KeywordFadeIn`, `OverlayKeyword`, `HeroTextCard`) when a proof component scores ≥ 6 on semantic fit | −10 | Text proof is weaker than visual proof when a visual fits |
| Same component family (text-dominant / image-dominant / motion-dominant) in both adjacent beats | −10 | Family monotony is less obvious but equally damaging |
| Same component used in the same beat class in the previous reel on this product | −8 | Cross-reel staleness; body choices should feel fresh |

### Role-Based Repetition Penalties

These penalize same *function*, regardless of whether the component name changed. Apply in addition to the component-level penalties above.

| Condition | Penalty | Why |
|---|---|---|
| Same primary **visual role** in the directly preceding beat | −20 | Adjacent same-function beats register as repetition even when the component name differs — the viewer experiences the same visual job twice |
| Same primary **visual role** in 3 consecutive beats | −35 | Function streak — three beats performing the same visual job is the canonical "fake variety" failure |
| `text-emphasis` visual role in 3 of the last 5 body beats | −30 | Text-emphasis overload; signal collapses to wallpaper even when different text components are used |
| No `proof-display` or `annotation-focus` beat in any 6-beat body window | −25 | The viewer is being told but never shown; every 6-beat window needs at least one visual evidence beat |
| Same primary **layout role** in 3 consecutive beats | −20 | Layout monotony is immediately visible — the frame divides the same way and the eye stops seeking variety |
| `text-on-avatar` layout role in 4+ consecutive beats | −25 | The avatar face becomes a text billboard; the human element loses its anchoring function |

---

## Underused Component Encouragement

These components are underused relative to their editorial value. Apply a **+10 bonus** when:
1. It would be the first use of this component type in the current reel, AND
2. Its semantic fit score is ≥ 6/10 (it genuinely fits — not a stretch)

| Component | Beat classes where bonus applies | Why it's underused |
|---|---|---|
| `AnnotationCircle` | Trust/credibility, Number+proof, Explanation over visual | Adds specificity without clutter — pointing at the exact element the narrator names is almost always better than not pointing |
| `ToastCard` | Trust/credibility, Staccato claim (brief callout sub-card) | Feels native and live; rarely considered as a trust beat device |
| `FeatureMockup` | Explanation over visual, Name reveal | More specific than a generic screenshot crop; underused when real screenshots are imprecise |
| `GlitchText` | Emotional keyword (pain/drama), Contradiction/negation | High visual impact for one beat; underused because it requires tonal confidence |
| `TypingText` | Explanation over visual (CLI or prompt input), Name reveal (tool output) | Perfect for CLI demos and AI chat mockups; screenshot replaces it by default |
| `StrikethroughSwap` | Contradiction/negation, Objection handling | Built for this beat type but OverlayKeyword is chosen instead |
| `CharKeyword` | Emotional keyword (1–3 explosive words) | More kinetic than KeywordFadeIn but rarely chosen as the first option |
| `ComparisonGrid` | Comparison, Contradiction/negation (visual A vs B) | Only component built for side-by-side; underused outside explicit "vs" framing |
| `CardStack` | List item (3–5 items as a run) | Better rhythm than five consecutive NumberPopup+KeywordFadeIn pairs; rarely selected |
| `LogoOverlay` in body beats | Name reveal, Tool intro (body beat naming a brand) | Required when a brand is named but often forgotten outside the hook |
| `StatCounter` | Number+proof (single headline stat with count-up animation) | Animated number reveals feel more dynamic than static overlays; OverlayKeyword or HeroTextCard is chosen by default even when the number should move |
| `ChartBar` | Number+proof (multi-value benchmark or comparison), Comparison | The only component that renders a full bar chart; replaces proof screenshots when data is better shown as bars than raw screenshot crops |
| `ProgressSteps` | Explanation over visual (sequential workflow), List item (3–5 sequential steps) | Better for sequential dependencies than NumberPopup series; the connecting vertical line communicates order; rarely considered because NumberPopup is the reflex |
| `ComparisonSlider` | Contradiction/negation (before/after transformation), Comparison (same subject two states) | Communicates transformation better than ComparisonGrid for same-subject before/after; divider sweep IS the editorial argument |
| `TextHighlight` | Trust/credibility (quoted claim with key phrase emphasis), Reframe/montage | Animated color sweep on specific words is more precise than HeroTextCard for sentence-level emphasis; rarely considered because HeroTextCard is the text reflex |
| `HighlightBox` | Explanation over visual (rectangular UI region during demo) | Rectangular annotation beats AnnotationCircle ellipse for rectangular UI targets (buttons, panels, tables); never considered because AnnotationCircle is the annotation reflex |
| `SourceProofCard` | Trust/credibility (named person, expert, or social post) | The only component that renders a styled attribution card with name + handle + animated highlight; raw screenshot replaces it by default |
| `LowerThird` | Name reveal (mid-reel tool introduction), Direct address (speaker identification) | Adds broadcast-style authority; almost always replaced by a LogoOverlay or BadgePopup even when the context calls for identification |
| `PunchText` | Emotional keyword (the reel's single hardest-hitting moment) | Slam + echo ripple is the most physically impactful text component; CharKeyword is chosen by default even when maximum physical weight is needed |
| `KineticQuote` | Trust/credibility (direct quote from authority), Reframe/montage (dramatic payoff statement) | Word-by-word spring entrance with `accentWords` is more editorial than HeroTextCard; rarely considered when a quote or payoff statement is needed |
| `ProgressRing` | CTA (countdown or progress urgency signal overlay) | Only component that adds a visible temporal signal during the CTA; OverlayKeyword is chosen by default even when urgency is the right energy |
| `TerminalWindow` | Explanation over visual (multi-line CLI workflow, developer tool-use) | Full macOS terminal chrome with per-line typing is more credible than TypingText for developer-focused reels; TypingText is chosen by default even when 3+ command lines are needed |
| `TypingInput` | Explanation over visual (user typing a prompt into a product input field) | Product-accurate input field animation is more demonstrative than a static screenshot; TypingText is chosen by default even when the act of typing is the proof |
| `TypewriterCode` | Staccato claim (single technical line), Explanation over visual (one-line command) | Single-line terminal typing with cursor is lighter than TerminalWindow for simple one-liners; TypingText is chosen by default even when the terminal register is right |
| `SceneBreak` | Section transition/bridge (kinetic flash at cut point) | GPU-safe whip/iris flash adds kinetic energy to a cut without spending the full FlashReset flash budget; jump-cut is used by default even when a brief energy flash would improve the edit |

---

## Aspirational Components

These components do **not yet exist** in the codebase. When built, they should be registered in the OVERLAY_REGISTRY and receive the same +10 encouragement bonus. **Verify availability before using in any timeline.**

| Component | Purpose when built | Beat class |
|---|---|---|
| `GlassCard` | Frosted glass card presenting proof stats or feature list | Number+proof, List item |
| `GuidedDemo` | Animated cursor walkthrough overlaid on a screenshot — guided UI tour with waypoints | Explanation over visual |

> **Previously aspirational, now built and in OVERLAY_REGISTRY:** SourceProofCard, LowerThird, SceneBreak, HighlightBox, PunchText, KineticQuote. These are fully selectable with the +10 encouragement bonus — see the Underused Component Encouragement table above.

---

## Zone-Specific Scoring

### Hook zone (beats within the first 2–3 seconds)

**Skip candidate scoring entirely.** Resolve to the archetype from `hook-grammar.md`:
- Archetype A → FramedImage + AvatarVideo (split) + LogoOverlay
- Archetype B → ScrollingIconGrid + AvatarVideo (split) + OverlayKeyword
- Archetype C → BRollVideo (responsive) + AvatarVideo + LogoOverlay

Hook beats are NOT counted in repetition tallies when computing body penalties.

### Body zone (beat 2 onward)

Apply full candidate scoring. Apply all repetition penalties. Apply underused component bonuses.

### Structural beats (FlashReset, ChapterDivider, LightLeakOverlay)

These are structural rather than semantic — no scoring needed. Select by style:
- `FlashReset` → editorial-authority, hard section break
- `LightLeakOverlay` → cinematic-presenter, soft scene transition (max 1 per reel)
- `ChapterDivider` → any style, tool introduction (creates full visual reset)

---

## Component Exclusion List

These components must **never** appear in Step 2b candidate sets. They serve non-editorial or pipeline-only roles and are not selectable through Phase 4b-ii scoring. If a candidate set cites one of these, remove it before proceeding.

### Internal / System-only — scene infrastructure, not content

These handle backgrounds, effects layers, and composition scaffolding. They are wired directly in `ReelComposition.tsx` — never placed via the overlays lane in `timeline.json`.

`AuroraBackground`, `BackgroundBeams`, `GradientMesh`, `SmokeWisp`, `FocusVignette`, `GlowBorder`, `NoiseOverlay`, `AnimatedBackground`, `AnimatedDivider`, `AnimatedGrid`, `HookIntroScene`, `SkillActivationScene`, `SkillQuestionsScene`, `ImageLayer`, `CircuitTrace`, `FloatingIcons`, `GlitchOverlay`, `ZoomParallax`, `LetterboxCinematic`, `ShimmerBar`, `SpotlightBeam`, `SweepReveal`, `MorphBlob`, `ParticleNetwork`, `PrismFlare`, `PulsingOrb`, `RadialBurst`, `RipplePulse`, `EmojiReactions`, `IconOrbit`, `ImageAutoSlider`, `PunchInZoom`, `TransitionWrapper`, `Caption`

### Display-mode only — invoked via `display:` field, not overlays lane

These are selected by setting `display: "..."` on a demo or broll lane entry. They control how demo content is framed (window chrome, full-screen, scroll, grid) — they are not scored as overlay candidates.

`AppWindow` (`display: "app-window"`), `GuidedDemo` (`display: "guided-demo"`), `ImageGrid2x2` (`display: "image-grid-2x2"`), `ScrollImage` (`display: "scroll-image"`)

### Deprecated — replaced by named component

| Deprecated | Replacement |
|---|---|
| `NumberCounter` | `StatCounter` — same animated count-up, improved spring entry and label support |
| `ClaudeLogoReveal` | `LogoOverlay` with `bounce: true, trail: true` — more flexible, works for any brand |
| `CodeReveal` | `TypewriterCode` — identical capability, consistent naming |

### YouTube-pipeline only — not for vertical 9:16 reels

These components exist for the horizontal YouTube composition (1920×1080) and are never appropriate in vertical reel timelines.

`LinkOverlay`, `SubscribeCTA`, `EndScreen`

---

## Justification Format

For every significant component selection, write one line in the shot list:

```
beat-XX: [Component]. Won: [one reason]. Alt: [1-2 alternatives considered]. Avoids: [specific weakness or repetition].
```

**Good:**
> `beat-05`: AnnotationCircle on memory-benchmark screenshot. Won: narrator says "look at this number" — specific element to circle. Alt: OverlayKeyword (rejected: 3rd use this reel, text weaker than annotation). Avoids: 3rd consecutive text overlay.

**Bad:**
> `beat-05`: FramedImage. Won: screenshot available. Alt: other options. Avoids: nothing.

The bad example fails because: it doesn't explain why FramedImage won over other candidates, doesn't acknowledge repetition state, and doesn't name the specific alternative.

---

## Scoring Examples

### Same beat class, different valid outcomes

**Beat class: emotional keyword, narration "ZERO"**

*Reel context A:* First keyword beat. No prior OverlayKeyword or CharKeyword use.
- CharKeyword: semantic fit 9, asset fitness 10 (no asset needed), proof strength 6, reel novelty 10, motion load 8, cross-reel 8 → strong score. +10 underused bonus = wins clearly.
- OverlayKeyword: semantic fit 8, reel novelty 10 → also strong, but CharKeyword's explosive energy better serves a single-word reveal.

*Reel context B:* KeywordFadeIn used twice, OverlayKeyword used three times.
- OverlayKeyword: −20 penalty (4th use approaching). Score drops below CharKeyword or GlitchText.
- GlitchText: semantic fit 7, +10 underused bonus (first use), no penalties → may win if the beat has dramatic energy.
- CharKeyword: semantic fit 9, +10 underused bonus if first use → wins.

---

**Beat class: trust/credibility, narration "peer-reviewed at ICLR 2026"**

*Reel context A:* Research screenshot available. First AnnotationCircle use.
- FramedImage + AnnotationCircle: semantic fit 9, asset fitness 9 (circles the paper title), proof strength 10, reel novelty 10 for AnnotationCircle use, +10 bonus = wins decisively.
- FramedImage + BadgePopup: semantic fit 7 (badge label is less specific than annotation). Loses.

*Reel context B:* No screenshot available. Brief beat (0.8s).
- ToastCard: semantic fit 8 (brief institutional callout), +10 underused bonus if first use, proof strength 6 (no visual evidence — just the assertion). Can win for brief credibility sub-beats.
- HeroTextCard: semantic fit 6, proof strength 5. Weaker — no visual credibility signal.

---

**Beat class: explanation over visual, narration "it compresses how AI stores data"**

*Reel context A:* Diagram screenshot available and specific.
- FramedImage + AnnotationCircle: semantic fit 9 (diagram shows compression), +10 bonus for AnnotationCircle. Wins.

*Reel context B:* Only generic architecture diagram available (PARTIAL fitness).
- FeatureMockup: semantic fit 7, asset fitness 10 (no real asset needed — mockup IS the asset), +10 bonus. May win over PARTIAL screenshot.
- FramedImage with PARTIAL asset: asset fitness 5. Needs annotation or crop to be compelling.

---

## Sequence-Level Review

Run this pass **after** all individual beats are scored and the component mapping table is drafted — before writing flow validation. Beat-level scoring selects the best candidate per beat. Sequence-level review catches patterns that only emerge across the full reel.

### 1. Role Dominance Check

Label each body beat with its primary visual role. Count beats per role. No single visual role should exceed **40% of body beats**.

If one role is above 40%:
1. Identify the 2–3 beats where that role has the weakest semantic fit
2. Re-run scoring for those beats with the role-dominance penalty applied
3. Confirm the alternative wins, or document why the dominance is intentional

### 2. Mode Alternation Check

Classify each body beat as one of two modes:
- **Presenter mode**: `avatar-anchor`, `text-on-avatar`, `text-emphasis` (words-only beats)
- **Proof mode**: `proof-display`, `annotation-focus`, `comparison`, `list-structure`

The sequence should alternate modes. Flag if:
- 4+ consecutive presenter-mode beats without a proof-mode beat — reel feels like a podcast
- 4+ consecutive proof-mode beats without a presenter-mode beat — reel loses its human anchor

### 3. Fake Variety Detector

Re-label the component sequence using visual roles instead of component names. If the role sequence would fail the same-component streak rule, the component selection has fake variety regardless of how many different components are named.

```
Component sequence: OverlayKeyword → CharKeyword → KeywordFadeIn → HeroTextCard → GlitchText
Role sequence:      text-emphasis  → text-emphasis → text-emphasis → text-emphasis → text-emphasis
```

The components look varied. The roles reveal a 5-beat `text-emphasis` chain. That is fake variety. Apply the −35 role streak penalty retroactively and re-select the weakest beats.

### 4. Proof Coverage Check

Count `proof-display` + `annotation-focus` beats in the reel body:

| Reel duration | Minimum proof-mode beats |
|---|---|
| 25–35s | 3 |
| 35–50s | 5 |
| 50s+ | 7 |

If below minimum, identify the weakest "narrator says it, no visual confirms it" beats. These are candidates for conversion to `proof-display` beats — find or capture the supporting asset.

### 5. Reset Coverage Check

Count `reset-interrupt` beats in the body (FlashReset, ChapterDivider, LightLeakOverlay, HeroTextCard as section label):

| Reel duration | Minimum reset beats |
|---|---|
| Sub-35s | 0 (optional) |
| 35–50s | 1 |
| 50s+ | 2 |

If absent and the reel is 35s+, flag: **"no editorial reset — reel may feel relentless without a breathing point."** This is a warning, not a blocker, but warrants a deliberate decision.
