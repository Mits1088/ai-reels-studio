---
description: Narration-to-component candidate sets, asset fitness audit, and flow validation for beat-by-beat visual planning
globs: ["**/shot-list.md", "**/beat-map.json", "**/catalog.json"]
---

# Component Mapping & Asset Fitness

This rule governs Phase 4b-ii of the reel workflow. It runs after visual assignment (4b-i) and before technical planning (4b-iii).

Its job is to answer two questions for every beat:
1. **Which Remotion component** best renders what the narrator is saying?
2. **Does the chosen asset** actually match the narration?

**Component selection is no longer a lookup table.** For each beat class, this file provides a candidate set — multiple valid options with explicit conditions. Scoring rules in `component-selection-scoring.md` select among them. The result is authored variety rather than habitual defaults.

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
| **Objection handling** | Pre-empting or rebutting a viewer doubt | "You might think this is just a demo — it's not.", "But this doesn't work for real code." |
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

## Step 2 — Select the Component

Component selection runs in five sub-steps. Do not skip to 2b without checking zone first.

### Step 2a — Zone Check

**If this beat is in the hook zone (within the first 2–3 seconds of the reel):**
- Resolve directly to the archetype from `hook-grammar.md`
- Do not run candidate scoring
- Do not apply repetition penalties to hook beats

**If this beat is in the body zone (beat 2 onward through CTA):**
- Proceed to Step 2b

**If this beat is a structural beat (FlashReset, ChapterDivider, LightLeakOverlay):**
- Select by style: FlashReset → editorial-authority; LightLeakOverlay → cinematic-presenter (max 1); ChapterDivider → any style for tool introductions
- No scoring needed

---

### Step 2b — Candidate Set by Beat Class

For each beat class, the table below lists valid candidates with: when each is strongest, when to suppress it, and its repetition risk. Read all rows before selecting.

After reviewing the candidates, score them using `component-selection-scoring.md` criteria and apply repetition penalties. The highest-scoring candidate wins.

---

#### Emotional keyword

| Candidate | Strongest when | Suppressed when | Repetition risk |
|---|---|---|---|
| `CharKeyword` | Single-word explosive reveal (1–3 words maximum); narrator delivers with punch energy | Multi-word phrase; calm or explanatory tone | Low — first-choice for single-word emphasis but each reel only needs 1–2 |
| `OverlayKeyword` | Word or phrase floats ON the avatar face during delivery; editorial-authority style | Already used 3+ times this reel; word needs explosive kinetic energy | High — default choice, easily overused |
| `GlitchText` *(clippkit)* | Pain payoff or dramatic negation; the word IS the dramatic moment | Factual/educational tone; the reel has not established drama yet | Low — rare and high-impact; wrong tone kills it |
| `HeroTextCard` | Keyword is the entire beat and avatar should step back; section-opening emphasis | Avatar presence needed for the emotion to land | Medium |

---

#### Staccato claim

| Candidate | Strongest when | Suppressed when | Repetition risk |
|---|---|---|---|
| `OverlayKeyword` | 2-5 word claim floats on avatar; editorial-authority style; avatar face reinforces the claim | Claim is 6+ words; OverlayKeyword already dominant this reel | High |
| `HeroTextCard` | Claim needs full-frame visual gravity; section-opening beat; avatar should step back | Avatar presence reinforces the claim delivery | Medium |
| `KeywordFadeIn` | Multi-word phrase benefits from word-by-word reveal; cinematic-presenter style | Single emphasis word (CharKeyword is stronger); already used twice this reel | Medium-high |
| `TypingText` *(clippkit)* | Claim is a command, terminal output, or AI prompt text; the typing IS the proof | Claim is emotional/personal; not a technical string | Low |

---

#### Name reveal

| Candidate | Strongest when | Suppressed when | Repetition risk |
|---|---|---|---|
| `HeroTextCard` | Product or concept name needs full-frame visual gravity; editorial-authority first introduction | Name was already established earlier; avatar should stay visible | Medium |
| `KeywordFadeIn` with glow | Name appears above the avatar in split-screen; cinematic-presenter style; avatar stays visible | Editorial-authority style (HeroTextCard wins instead) | Medium |
| `LogoOverlay` | Brand name with SVG logo available; logo IS the reveal | No logo asset available; brand is abstract concept without visual identity | Low — mandatory when brand has a logo |
| `LottieOverlay` | Brand has an animated Lottie logo file; more premium than static SVG | No Lottie JSON available for this brand | Low |
| `TypingText` *(clippkit)* | Name appears as AI output or terminal response (the product "reveals itself" by typing) | Name is said by narrator as a declaration | Low |

---

#### Number + proof (proof stat)

| Candidate | Strongest when | Suppressed when | Repetition risk |
|---|---|---|---|
| `FramedImage` + `AnnotationCircle` | Screenshot exists with the stat visible AND there's a specific element to annotate (bar, row, number) | Screenshot is too busy to annotate legibly; no specific focal element | Low — high value, underused |
| `NumberPopup` + `FramedImage` | Stat needs a labeled badge AND a proof screenshot; numbered list context | No screenshot available; stat needs to stand alone | Medium |
| `HeroTextCard` (number as hero) | Stat is strong enough to stand alone ("6X fewer tokens. Same quality."); no visual proof exists | A visual proof exists that would be more convincing than text | Low |
| `FramedImage` + `OverlayKeyword` | Screenshot IS dominant proof; number overlaid directly on the chart or result | Number needs more visual emphasis than a text overlay | Medium |
| `NumberPopup` alone | Numbered list item label (not proof stat); no screenshot needed; brief appearance | Stat requires proof visual — naked number without evidence is weak | Low |

---

#### Explanation over visual (interface explanation)

| Candidate | Strongest when | Suppressed when | Repetition risk |
|---|---|---|---|
| `FramedImage` + `AnnotationCircle` | Screenshot clearly shows the thing being described AND there's a specific element to point at | Screenshot is overview-level with no specific focal element | Low — almost always better than annotation-less FramedImage for explanations |
| `FramedImage` (alone) | Screenshot explains itself; no annotation needed; narrator is orienting not pointing | Specific element needs highlighting — "this part right here" language | Medium |
| `FeatureMockup` | Feature is described abstractly and no screenshot exists OR available screenshots aren't specific enough | Real product UI exists and passes MATCH fitness | Low |
| `TypingText` *(clippkit)* | Explanation involves showing an AI typing, CLI command, or prompt-response pattern | Explanation is about a static product state (a dashboard, a settings screen) | Low |
| `BRollVideo` (center-full) | Explanation is about an action or process with video coverage | Explanation is about a visible UI state (static) | Medium |

---

#### Direct address

| Candidate | Strongest when | Suppressed when | Repetition risk |
|---|---|---|---|
| `AvatarVideo` full-screen | Narrator delivers a pivot line, payoff, or insight requiring human connection | Visual proof should be on screen simultaneously to support the claim | High — default, must earn each full-screen use |
| `AvatarVideo` + `OverlayKeyword` | Key phrase can be reinforced with text overlay on the face | Face IS the whole message; overlay would compete with delivery | Medium |
| `AvatarVideo` + `BadgePopup` | Small label adds context without competing with face (e.g. "GOOGLE LABS") | No label adds genuine semantic value | Low |

---

#### Objection handling

| Candidate | Strongest when | Suppressed when | Repetition risk |
|---|---|---|---|
| `AvatarVideo` full-screen | Rebuttal is conversational and energy-based; the face IS the confidence | Rebuttal involves visual proof that should be on screen | Medium |
| `FramedImage` + `AnnotationCircle` | Objection is "does this actually work?" and a proof screenshot answers it directly | Objection is philosophical/conceptual (no visual answers it) | Low |
| `StrikethroughSwap` | Objection is a specific claim being disproved ("people thought X — actually Y"); clean A→B negation | Objection is more complex than a simple value swap | Low — underused |
| `HeroTextCard` | Objection itself is stated as text before being rebutted (setup card) | Rebuttal is immediate — no setup card needed | Medium |

---

#### Trust/credibility (source proof)

| Candidate | Strongest when | Suppressed when | Repetition risk |
|---|---|---|---|
| `FramedImage` + `AnnotationCircle` | Source screenshot exists AND there's a specific element (title, author, institution) to circle | Screenshot is too broad; no specific element worth pointing at | Low — high value |
| `FramedImage` + `BadgePopup` | Source page screenshot exists; badge labels the institution | Source needs more than a label — specific claim in the screenshot needs annotation | Medium |
| `ToastCard` *(clippkit)* | Brief trust callout (0.5–1.5s); "this just happened" framing; sub-card feel | Trust beat requires sustained proof (3s+) — ToastCard is too brief | Low — underused |
| `LogoOverlay` (institution logo) | Credibility is entirely about WHO said it (MIT, Google, Anthropic); logo IS the credential | The claim itself also needs to be visible; logo alone isn't enough | Low |

---

#### Contradiction/negation (contrast/before-after)

| Candidate | Strongest when | Suppressed when | Repetition risk |
|---|---|---|---|
| `StrikethroughSwap` | Clear old value being rejected, new value being revealed; quantitative or named contrast | Contrast is conceptual rather than a specific value swap | Low — purpose-built, underused |
| `ComparisonGrid` | Before/after involves two screenshots or two UI states | Contrast is text-only; no visual assets for both sides | Low |
| `OverlayKeyword` with strikethrough styling | Simple visual negation of a word or short phrase | The swap animation would be more compelling | Medium |
| `GlitchText` *(clippkit)* | Negation is dramatic and the "wrong" side should feel broken | Constructive or neutral tone | Low |

---

#### List item

| Candidate | Strongest when | Suppressed when | Repetition risk |
|---|---|---|---|
| `NumberPopup` + `KeywordFadeIn` | Named numbered item (tool name, feature name) where badge + phrase pairing serves the structure | List items are conceptual/bullet-style with no strong names to emphasize | Medium |
| `CardStack` | 3–5 items presented as a visual run; cards feel native for the list content | Fewer than 3 items (single-card stack looks weak); items need individual screenshot proof | Low |
| `NumberPopup` + `FramedImage` | Each list item has a supporting screenshot; the list is proof-led | No supporting visuals per item | Low |
| `ChapterDivider` | Each list item is a tool or major section that deserves a full visual reset | List should feel continuous — no reset needed between items | Low |

---

#### Comparison

| Candidate | Strongest when | Suppressed when | Repetition risk |
|---|---|---|---|
| `ComparisonGrid` | Two screenshots or UI states available for both sides; visual A vs B | No visual assets for one or both sides | Low — purpose-built |
| `StrikethroughSwap` | Comparison has a clear winner (old → new, wrong → right) | Comparison is genuinely neutral (both sides have merit) | Low |
| `FramedImage` in sequence | Two screenshots presented one after another (cut, not side-by-side) | Side-by-side visual comparison is needed | Medium |

---

#### Reframe/montage

| Candidate | Strongest when | Suppressed when | Repetition risk |
|---|---|---|---|
| Multiple `FramedImage` in rapid sequence | Recapping 3–5 distinct proof moments from earlier in the reel; fast cuts reinforce breadth | New content is being introduced (not a recap) | Medium |
| `FramedImage` + `OverlayKeyword` pairing per image | Each image needs a brief label to name what it shows | Images speak for themselves without labels | Medium |

---

#### CTA

| Candidate | Strongest when | Suppressed when | Repetition risk |
|---|---|---|---|
| `AvatarVideo` full-screen + `OverlayKeyword` | CTA is conversational; "follow for more like this" energy; face + text reinforces the ask | CTA involves a specific action beyond following that needs visual framing | Medium |
| `AvatarVideo` + `HeroTextCard` (split or full-screen) | CTA action word needs maximum visual weight; card can show the action clearly | Energy should stay entirely on the face | Low |

---

#### Section transition (bridge/reset)

| Candidate | Strongest when | Suppressed when | Repetition risk |
|---|---|---|---|
| `FlashReset` | Editorial-authority style; hard editorial break between sections | Cinematic-presenter style (too harsh) | Low — editorial only |
| `AvatarVideo` direct address | Narrator bridges sections verbally; conversational pivot | Silent/ambient transition desired | Medium |
| `HeroTextCard` section label | Explicit chapter/section labeling needed; viewer needs a heading | Transitions should feel fluid — no heading needed | Low |
| `LightLeakOverlay` | Cinematic-presenter style; soft scene transition | Editorial-authority style; or flash budget already spent (max 1 per reel) | Low |

---

### Component Role Reference

Every component has a visual role (what function does this beat perform?) and a layout role (how does it occupy the frame?). Record these for every selected component — they feed the role-based repetition penalties and sequence-level review in `component-selection-scoring.md`.

Full role definitions are in `component-selection-scoring.md` → Visual Role & Layout Role Taxonomy.

| Component | Visual role | Layout role |
|---|---|---|
| `AvatarVideo` full-screen (minimal overlay) | `avatar-anchor` | `full-screen-avatar` |
| `AvatarVideo` + `OverlayKeyword` | `text-emphasis` | `text-on-avatar` |
| `AvatarVideo` + `BadgePopup` | `avatar-anchor` | `full-screen-avatar` + `corner-micro` |
| `FramedImage` (split-screen, standalone) | `proof-display` | `split-content` |
| `FramedImage` + `AnnotationCircle` | `annotation-focus` | `annotation-overlay` |
| `FramedImage` (center-full) | `proof-display` | `center-full` |
| `BRollVideo` | `proof-display` | `center-full` |
| `FeatureMockup` | `proof-display` | `split-content` |
| `TypingText` (demo context) | `proof-display` | `split-content` or `center-full` |
| `HeroTextCard` (emphasis / name reveal) | `text-emphasis` | `full-frame-card` |
| `HeroTextCard` (section label / chapter) | `reset-interrupt` | `full-frame-card` |
| `OverlayKeyword` (on avatar face) | `text-emphasis` | `text-on-avatar` |
| `KeywordFadeIn` | `text-emphasis` | `split-content` |
| `CharKeyword` | `text-emphasis` | `full-frame-card` or `split-content` |
| `GlitchText` | `text-emphasis` | `full-frame-card` |
| `StrikethroughSwap` | `comparison` | `side-by-side` |
| `ComparisonGrid` | `comparison` | `side-by-side` |
| `CardStack` | `list-structure` | `full-frame-card` |
| `NumberPopup` series | `list-structure` | `corner-micro` or `split-content` |
| `BadgePopup` | `credibility-signal` | `corner-micro` |
| `ToastCard` | `credibility-signal` | `corner-micro` |
| `LogoOverlay` (trust / credibility context) | `credibility-signal` | `corner-micro` |
| `FlashReset` | `reset-interrupt` | `full-frame-card` |
| `ChapterDivider` | `reset-interrupt` | `full-frame-card` |
| `LightLeakOverlay` | `reset-interrupt` | `center-full` |

---

### Step 2c — Score and Select

After reviewing the candidate set:

1. Score each candidate on the 6 criteria from `component-selection-scoring.md` (semantic fit 35%, asset fitness 20%, proof strength 15%, reel novelty 15%, motion load 10%, cross-reel novelty 5%)
2. Apply component-level repetition penalties from `component-selection-scoring.md`
3. Apply role-based repetition penalties from `component-selection-scoring.md` → Role-Based Penalties
4. Apply +10 underused component bonus where applicable
5. Select the highest-scoring candidate
6. Record the winner's **visual role** and **layout role** from the Component Role Reference above — add both to the Component Mapping Table row

For beats where the winner is obvious (first use, clearly best semantic fit, no penalties): skip the arithmetic and note "clear win — first use, best semantic fit."

For beats where two candidates are close: run the full scoring and document it.

---

### Step 2d — Design Quality and Theme Check

After selecting the component, verify it will render distinctively. Consult the `frontend-design` skill if:
- The component's default styling feels generic or flat for this product
- Typography choices need refinement (weight contrast, size contrast, font pairing)
- Color choices need alignment with the project's theme

When selecting colors, read `project.json` for `theme`, `theme_primary`, `theme_secondary`. These drive:
- HeroTextCard background colors (use theme_primary for brand beats, contrast for emphasis)
- OverlayKeyword colors (theme_primary or theme_secondary)
- NumberPopup / BadgePopup accent colors
- Aurora blob tints (cinematic-presenter style)
- ScrollingIconGrid overlay gradient (editorial-authority style)

**Rule:** If this component's treatment would look identical in any other reel regardless of topic, it needs design work. The component should feel chosen for this product, not assembled from defaults.

---

### Step 2e — Write the Justification

For every beat where the selection was non-obvious (alternatives were competitive, repetition penalties applied, or an underused component was chosen), write one line in the shot list:

```
beat-XX: [Component]. Won: [one reason]. Alt: [1-2 candidates considered]. Avoids: [weakness or repetition].
```

Keep this to one line. It is a decision record, not a reasoning dump.

**Good:** `beat-05`: AnnotationCircle on memory-benchmark screenshot. Won: narrator names a specific bar — annotation targets exactly that. Alt: OverlayKeyword (rejected: 3rd use this reel). Avoids: third consecutive text overlay.

**Bad:** `beat-05`: FramedImage. Won: screenshot available. Alt: other options. Avoids: n/a.

---

## Stale Mapping Warnings

These are the most common patterns that produce technically compliant but editorially weak reels. If any of these appear during the Phase 4b-ii review, flag and fix before proceeding.

| Stale pattern | What it looks like | Fix |
|---|---|---|
| **KeywordFadeIn chain** | 4+ consecutive beats using KeywordFadeIn as the primary overlay | Rotate: OverlayKeyword, CharKeyword, HeroTextCard, or no overlay (let proof speak) |
| **OverlayKeyword dominance** | OverlayKeyword appears in 5+ beats of a 30s reel | Reserve OverlayKeyword for 2–3 maximum-emphasis moments; silence is a valid choice |
| **Text-only proof** | Every proof beat uses only text (no screenshot, no demo, no annotation) | At least 2 proof beats must use a visual asset; text narration alone is not proof |
| **Badge as emphasis** | BadgePopup used as the primary emphasis component for 3+ beats | BadgePopup is a sub-card, not a hero — use as supporting element, not the main treatment |
| **Motion to rescue weak choice** | Component chosen doesn't fit the narration → added Ken Burns or scale animation to hide the mismatch | Fix the component choice; motion cannot rescue a semantic mismatch |
| **Screenshot-only proof section** | 4+ consecutive beats all use FramedImage with no animation, annotation, or component variety | Vary: add AnnotationCircle, cut to demo video, insert LogoOverlay, or use FeatureMockup |
| **Same entry preset throughout** | All demo entries use the same `zoom-in` preset for 6+ consecutive beats | Rotate presets after every 2 same-type entries |
| **Invisible avatar absence** | Avatar hidden for 12s+ without any explicit design decision for the absence | Either return avatar sooner or explicitly document the proof-protected justification |

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

After component selection and asset fitness, read the component sequence and check. These checks work alongside `body-grammar.md` repetition limits — any violation here is also a violation of body grammar.

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

Count unique component types used across the reel body (post-hook):
- **Minimum 4** for a 25-30s reel
- **Minimum 6** for a 35-50s reel
- **Minimum 8** for a 50s+ reel

If below minimum, check whether stale mapping warnings apply — the most common cause is text-only proof and KeywordFadeIn dominance. See also `body-grammar.md` → Minimum Variety Rules for component family requirements.

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

### Role distribution check

After completing the component mapping table, run the sequence-level review from `component-selection-scoring.md`. Record results in the Flow Validation block:

1. **Role dominance**: List the visual role distribution. Flag if any single role exceeds 40% of body beats.
2. **Fake variety test**: Re-label the component sequence by visual role. Flag if any role has a streak of 3 that the component-name sequence masked.
3. **Proof coverage**: Count `proof-display` + `annotation-focus` beats. Flag if below the duration minimum.
4. **Mode alternation**: Confirm no 4+ consecutive presenter-mode or proof-mode run.
5. **Reset coverage**: Flag if 35s+ reel has zero `reset-interrupt` beats in the body.

---

## Output Format

Phase 4b-ii produces these sections in `shot-list.md`:

### Component Mapping Table

```markdown
## Phase 4b-ii — Component Mapping

| Beat | Classification | Component | Visual Role | Layout Role | Avatar Layout | Selection Justification |
|---|---|---|---|---|---|---|
| beat-01a | hook opening | ScrollingIconGrid + OverlayKeyword | text-emphasis | text-on-avatar | split-screen | archetype B — zone: hook |
| beat-02 | direct address | AvatarVideo | avatar-anchor | full-screen-avatar | full-screen | clear win: pivot line, face IS the message |
| beat-05 | number + proof | AnnotationCircle on benchmark.png | annotation-focus | annotation-overlay | split-screen | won: specific bar to circle; alt: OverlayKeyword (3rd use, role: text-emphasis streak); avoids: text-only proof |
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

Component sequence: ScrollingIconGrid → AvatarVideo → HeroTextCard → AnnotationCircle → ...
Visual role sequence: text-emphasis → avatar-anchor → text-emphasis → annotation-focus → ...
Avatar layout sequence: split → full → hidden → split → full → ...
Unique components used: 8 ✓
Max same-component streak: 2 ✓
Max same-layout streak: 2 ✓
Longest dense run without face: 5.2s ✓
Longest sparse run without visual: 3.9s ✓
Stale mapping checks: no KeywordFadeIn chain, no text-only proof sections ✓

Role distribution: text-emphasis 25%, proof-display 30%, annotation-focus 20%, avatar-anchor 15%, reset-interrupt 10% — no role exceeds 40% ✓
Fake variety test: role sequence reveals no hidden streaks ✓
Proof coverage: 5 proof-mode beats in a 42s reel — meets minimum ✓
Mode alternation: longest presenter-mode run 2 beats, longest proof-mode run 3 beats ✓
Reset coverage: 1 FlashReset in body of 42s reel — meets minimum ✓
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
| `KeywordFadeIn` | Words fade in with stagger (word-level) | Feature names, tool names, short phrases (cinematic style) |
| `CharKeyword` | Characters pop in individually (char-level, `remotion-animate-text`) | Single-word emphasis: hook words like "WRONG", "ZERO", "FREE", "6X". More explosive than KeywordFadeIn. Presets: explode / rise / cascade |
| `NumberPopup` | Colored badge with number + label | Numbered lists, stat reveals (cinematic style) |
| `BadgePopup` | Small pill badge | Labels, tags, source badges |
| `StrikethroughSwap` | Old value crossed out, new value slides in | Before/after, negation (cinematic style) |
| `LogoOverlay` | SVG logo with optional background card, optional bounce + trail animation, vertical + horizontal positioning | **Brand reveals (mandatory when a brand is named in the script)**, hook brand walls, corner badges. Use `trail={true}` with `bounce={true}` on hook logos for motion blur energy. |
| `LottieOverlay` | Animated brand logo from Lottie JSON file (`@remotion/lottie`) | Brand reveals when a Lottie animation is available — prefer over `LogoOverlay` for animated opens. Same positioning API. Source JSON from LottieFiles.com or brand resources. |
| `FeatureMockup` | Card with SVG icon + label + bullet details | Feature visualizations during pain-elim or proof beats. Pull preset configs from `lib/feature_mockups/presets.json`. |
| `BarWaveform` *(clippkit)* | Audio-driven bar waveform | Bottom-of-frame motion during avatar talking-head beats — visualizes the actual narration audio |
| `CircularWaveform` *(clippkit)* | Audio-driven circular orb | Centered audio orb visualization — alternative to bar waveform |
| `GlitchText` *(clippkit)* | Destabilized RGB-split text | High-impact dramatic emphasis (pain payoffs, "GONE" moments) — pair with FlashReset |
| `TypingText` *(clippkit)* | Terminal/chat typing simulation with blinking cursor | "Claude is typing right now" mockups, CLI command demos, prompt input visualizations |
| `ToastCard` *(clippkit)* | Notification card with spring entry from any corner | Trust beat sub-cards, brief proof callouts, "this just happened" notifications |
| `Caption` | Bottom-of-screen subtitle text | Always present |

### Backgrounds & effects
| Component | What it does | Best for |
|---|---|---|
| `ScrollingIconGrid` | Rotated grid of logo cards, scrolls diagonally | Hook background (editorial style) |
| `AuroraBackground` | White base with drifting pastel blobs | Demo/split scenes (cinematic style) |
| `GradientMesh` | Dark moody gradient | CTA/outro (cinematic style) |
| `FlashReset` | 2-3 frame white flash | Section dividers (editorial style) |
| `LightLeakOverlay` | WebGL cinematic light flare (`@remotion/light-leaks`) | Scene transitions in cinematic-presenter style. Softer than FlashReset — organic flare vs hard flash. Use inside `TransitionSeries.Overlay`. `hueShift` maps to brand color (0=warm, 200=blue, 20=Anthropic orange). Max 1 per reel (same flash budget as FlashReset). |
| `ChapterDivider` | Logo + title on solid bg | Tool introductions, section resets |
| `ComparisonGrid` | Side-by-side screenshots with VS divider | A vs B comparisons |
| `CardStack` | Staggered card reveal | Numbered lists, feature lists |
| `AnnotationCircle` | Hand-drawn SVG annotation (`@remotion/paths` evolvePath) | Ellipse shape: circle around UI elements. Underline shape (`shape="underline"`): underline beneath text or numbers in proof screenshots. Draw-on animation is frame-accurate. |
| `CursorClick` | Cursor with click ripple | Simulating button clicks |
| `NoiseOverlay` | Film grain texture | Always present (subtle) |

### When to build a new component

Only build a new component if:
1. No existing component can render the beat's content
2. The content type will appear in multiple reels (not a one-off)
3. The component can be described in one sentence

**Before building a new component, check the vendored libraries and installed packages:**

1. **`remotion/src/components/effects/clippkit/`** — vendored from clippkit (MIT). Includes BarWaveform, CircularWaveform, GlitchText, TypingText, ToastCard. See `clippkit/NOTICE.md` for the full list and instructions for vendoring more from upstream at https://github.com/reactvideoeditor/clippkit.
2. **`lib/feature_mockups/presets.json`** — pre-built `FeatureMockup` configs (sandboxing, credentials, checkpointing, tracing, monitoring, scaling, integration, performance, automation, permissions, encryption, search). Pull via `from lib.feature_mockups import preset`.
3. **`@remotion/paths`** — `evolvePath()` for SVG draw-on animation. Used by `AnnotationCircle`. Import directly for one-off path animations (arrows, underlines, custom shapes).
4. **`@remotion/motion-blur`** — `Trail` component. Exposed via `LogoOverlay trail={true}`. Import directly for trail on any custom-built animated element.
5. **`@remotion/lottie`** — Lottie JSON playback. Use `LottieOverlay` for brand reveals. Import `Lottie` directly for inline one-off Lottie animations.
6. **`remotion-animate-text`** — Character/word-level text animation. Use `CharKeyword` for single-word explosive reveals. Import `AnimatedText` directly for custom text presets.
7. **`@remotion/light-leaks`** — WebGL light flare. Use `LightLeakOverlay` as-is — no need to import directly.

If a beat needs a one-off visual, use inline JSX in ReelComposition.tsx instead of creating a new component file.

### Mandatory: brand logos at Phase 4b-ii

When a beat names a brand (in narration OR shot list), the brand logo SVG **MUST** be wired into the timeline as a `LogoOverlay` entry. Text-only references to brand names without the logo are a fitness audit failure — they were a recurring gap in past reels until this rule was added.

**Workflow:**
1. At Phase 4b-i, identify every brand named in the script
2. Phase 4b-ii component mapping table must list a `LogoOverlay` for each brand
3. Phase 4d asset prep must ensure the brand SVGs are in `remotion/public/brands/`
4. Phase 5 assembly must include the `LogoOverlay` entries in `timeline.json`

**Sourcing brand logos via `lib.assets`:**

```bash
# AI/LLM brands (LobeHub Mono extraction): Anthropic, Claude, ClaudeCode,
# OpenAI, Gemini, Notion, Mistral, Meta, etc.
python -m lib.assets ai-brand Anthropic --project <slug>
python -m lib.assets ai-brand ClaudeCode --project <slug>
python -m lib.assets ai-brands  # list all available

# SaaS brands (Simple Icons CDN): Asana, Rakuten, GitHub, Atlassian, etc.
python -m lib.assets brand notion --project <slug>
python -m lib.assets brands Asana Rakuten GitHub --project <slug>
```

After fetching, copy the SVGs to `remotion/public/brands/` during Phase 4d.

**Colored variants of LobeHub Mono SVGs:** Remotion's `<Img>` does NOT propagate CSS color into SVG content (SVG-in-img is treated as opaque). To render a logo in a theme color, create a duplicate SVG file with the color baked in:

```svg
<!-- public/brands/ClaudeCode-orange.svg -->
<svg viewBox="0 0 24 24" fill-rule="evenodd">
  <path d="..." fill="#D97757"/>
</svg>
```

Then reference the colored variant from the timeline. See `feedback_svg_color_through_img.md` for details.
