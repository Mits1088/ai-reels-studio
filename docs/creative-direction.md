# Creative Direction

This file is the authorship identity layer for the reel system.
Read it before applying style-profile defaults, visual-style rules, motion-intent choices, or component mapping.
It sits above all technical rules in the creative hierarchy — technical correctness is necessary but not sufficient.

---

## Creative Philosophy

Every reel must feel **authored**, not assembled.

"Assembled" means: technically correct, every gate passed, every component chosen from the approved table, every transition within spec. A reel can be assembled without any taste being exercised.

"Authored" means: the specific choices made for this beat — this screenshot, this component, this motion, this zoom target — feel like they were made by someone who understood what the narrator was saying and wanted the viewer to feel something specific at that moment.

The system exists to enforce correctness. Creative direction exists to enforce quality above correctness.

---

## Hook Identity — Keep Stable

The hook grammar should stay **recognizable across reels**. Stability creates a brand signature — viewers who watch multiple reels should feel a consistent creative hand.

### What stays stable

- **Structure:** real product UI visible in the first frame, bouncing brand logo, split-screen avatar, caption with value claim, SFX hit on entry
- **Energy level:** hooks must have ≥4 simultaneous visual elements in motion (see `visual-style.md` Hook Motion Accounting)
- **Proof-first commitment:** the hook either shows the result or teases the contrast — it never opens with setup
- **Avatar position:** avatar is always anchored at the bottom in split-screen during the hook; never full-screen alone at open

### What changes per reel

- The specific product, logo, and colors
- The value claim (always specific to this reel's topic)
- The screenshot (always real product UI, not generic stock)
- The SFX character (can vary from whoosh to impact to stutter)
- The hook's emotional register (urgency vs. curiosity vs. contrast)

### Hook failure modes

- Hook opens with avatar full-screen and no other elements → FAIL
- Value claim is generic ("AI is changing everything") → FAIL
- No bouncing or cycling element in frame → FAIL
- No real product UI in the first second → FAIL

---

## Post-Hook Sections — Vary More

After the hook, **creative variation is a quality requirement**, not optional. A reel that uses the same 4 components in the same order every time is a template. Templates feel interchangeable.

### Dimensions of variation

1. **Shot family** — changes every 3–4 beats. Don't run 5 straight FramedImage beats.
2. **Component family** — rotate between text-dominant, image-dominant, motion-dominant, and avatar-dominant beats
3. **Proof type** — a single reel should use at least 2–3 distinct proof methods: screenshot + demo video + annotation, or screenshot + FeatureMockup + data card, etc.
4. **Motion family** — not every beat needs the same entry preset. After 3 `zoom-in` entries, the next one should wipe, punch, or slide.

### The test for post-hook variety

List the component types used in order. If any 3 consecutive beats use the same component type, redesign the middle one. If the proof section uses only screenshots (no demo clips, no animated components, no annotations), add variety.

---

## What "Premium" Means

- **Intentional restraint.** Motion serves the narration. A calm, confident hold during a strong spoken claim is more premium than a zoom reflex.
- **Proof visible within the first 3 beats.** Premium reels trust the evidence. They don't bury it behind setup.
- **Typography that feels chosen.** Font weight, size contrast, and color should reflect the beat's emotional register — not default to the same treatment every time.
- **Every screenshot is the right screenshot.** Not just any screenshot of the product — the specific frame that shows exactly what the narrator is claiming at that moment.
- **The CTA feels earned.** Because the proof was real, specific, and cumulative.
- **The reel has a voice.** If you removed the brand and product, the reel still has a recognizable perspective — it has something to say, not just information to deliver.

---

## What "Boring / Plain" Means

A reel is boring when:

- The hook starts with avatar full-screen, no other visual elements
- Any screenshot holds for 4+ seconds with no motion, zoom, or cut
- The same component type appears for 5+ consecutive beats
- No SFX fires at any layout change
- The background choice doesn't match the scene energy (dark background behind a demo screenshot, for example)
- The reel could describe any AI tool with minimal changes — there's nothing specific to this product, this feature, this proof
- Every beat uses the same emotional register — same pace, same weight, same emphasis style
- The reel opens with general context before the payoff — setup before proof

---

## What "Too Much Zoom" Means

Zoom is a precision tool, not a default energy source.

**Too much zoom:**
- Ken Burns active on every beat regardless of content importance
- Zoom starts before the narrator references the zoomed element
- Multiple zoom moments within a 2-second clip (no time to read either)
- Scale exceeds 2.5× on most beats (tight crops lose context)
- Zoom used to add energy to a beat that should be calm and confident
- Every proof beat zooms in for no specific reason

**Zoom correctly used:**
- Fires at the moment the narrator names a specific UI element, result, or claim
- Targets exactly that element (not a vague center crop)
- Holds long enough for the viewer to read what was zoomed into
- At most 2 zoom moments per beat, with ≥1.5s between them
- Sometimes the right choice is no zoom — a clean wide hold on strong proof is authoritative

---

## What "Designed Variation" Means

Designed variation means the reel's visual rhythm was planned, not randomized. Differences between beats feel purposeful.

**Signs of designed variation:**
- The shot family changes at meaningful editorial moments (after proof, before CTA, at section transitions)
- Component choices reflect the narration type (keyword → OverlayKeyword, stat → NumberPopup + annotation, demo → FramedImage + zoom, not all three beat types treated the same way)
- Motion direction changes at narrative pivots (wipe-up entering proof, punch entering CTA)
- The motion energy matches the narration energy: fast, staccato claims get punchy entries; calm explanatory beats get slower reveals

**Signs of non-designed variation (avoid):**
- Different components used on every beat with no pattern — chaotic, not varied
- Same component used for all beats of the same type — monotonous
- Variation introduced at random to hit a "minimum component count" rather than to serve the beat

---

## Anti-Patterns

These patterns produce technically compliant but editorially weak reels. Flag any of these during shot-list, motion-intent, or QA review:

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| **KeywordFadeIn dominance** | Same text treatment for 5+ beats — viewer stops reading | Rotate to OverlayKeyword, HeroTextCard, or silence (let the proof speak) |
| **OverlayKeyword on every avatar beat** | Clutters the face, reduces presenter authority | Reserve OverlayKeyword for the 2–3 most important emphasis words |
| **Generic b-roll where product UI should be** | B-roll doesn't prove anything; product UI does | Replace generic b-roll in proof positions with real screenshots or demo video |
| **Zoom as default energy** | Zoom stops feeling like emphasis — it becomes noise | Reserve zoom for moments with a specific named target |
| **"Clean minimalism" in the hook** | Tame hooks fail; minimalism belongs in body beats | Hook must have ≥4 simultaneous elements |
| **Proof section with one static screenshot** | One image holding for 4s kills engagement | Multiple frames, zoom moments, or cut to demo clip |
| **Every beat the same avatar layout** | All split-screen or all full-screen for 10 beats — feels like a slideshow | Vary layouts; return to avatar face after proof sections |
| **Identical entry presets throughout** | 7 `zoom-in` entries in a row → invisible rhythm | Max 2 consecutive same-type entries |
| **CTA that doesn't match the reel's proof** | Generic "follow for more" after specific technical proof feels disconnected | CTA should reference what was just proven |

---

## Reading Order

This file is read before:
1. `visual-style.md` defaults
2. Style profile selection (cinematic-presenter, editorial-authority, proof-escalation-editorial)
3. Component mapping decisions (phase 4b-ii)
4. Motion-intent writing (phase 4c)
5. QA evaluation of creative quality (phase 6)

After reading this file, also read `memory/creative-feedback.json` for accumulated human taste signal from previous reels.

---

## On the Relationship Between Rules and Taste

Rules prevent failures. Taste produces quality.

A reel can pass every gate, hit every component minimum, stay within every timing bound, and still be mediocre. Rules are a floor, not a ceiling. Creative direction is what you do above the floor.

### Which rules taste can override

**Taste beats style defaults.** When taste is in tension with a style-default rule, favor taste and document the override in the shot list:

- Component-mapping defaults (the table suggests OverlayKeyword, but the beat calls for silence)
- Visual-style defaults (the default background choice, the default transition type)
- Motion-intent preset defaults (the default entry preset for a given beat category)
- Body-grammar limits (a repetition limit that a strong editorial reason justifies breaking)

One sentence of justification in the shot list is sufficient: *"override: this beat needs to breathe — no overlay; justification: the proof is already on screen, text would compete with it."*

### Which rules taste cannot override

**Production and safety rules are not aesthetic preferences.** Do not use creative intent to justify overriding:

- **Timing-sync rules** — audio timing is always the source of truth, not creative instinct
- **Gate enforcement** — phases are sequential and required; taste does not unlock a gate
- **QA safety checks** — encoding validity, safe-zone compliance, asset presence, caption readability
- **Asset-validity rules** — a missing or corrupted asset cannot be excused by creative intent

These rules have production consequences that taste cannot compensate for. A reel that "feels premium" but fails QA is not premium.
