---
description: Post-hook creative rules — variety minimums, repetition limits, pattern interrupts, motion language, and transition grammar for reel body beats
globs: ["**/shot-list.md", "**/motion-intent.md", "**/timeline.json"]
---

# Body Grammar

This rule governs everything after the hook (beat 2 onward). The hook is fixed — the body is where creative variety lives.

Body grammar gives that variety structure. Without structure, variety becomes chaos. Without variety, the body becomes a template. This file defines the constraints that make flexibility coherent.

---

## Scope

Applies to: all beats after the hook opening (typically beat 2 through the CTA).
Does not apply to: the hook (see `hook-grammar.md`).
Works alongside: `visual-style.md` (technical layout rules), `component-mapping.md` (component selection), `motion-intent.md` (beat-level motion direction).

---

## Creative Override Path

Body grammar limits are **default blockers** — if a limit is exceeded, the shot list or motion-intent must be revised before proceeding to the next phase. But the strongest reel occasionally justifies breaking a rule. An intentional override is different from a careless omission.

**Permitted overrides (document the justification):**
- Any repetition limit (component type, layout, entry preset, family count)
- Minimum variety counts (shot family, component family, proof method)
- Pattern interrupt count
- Avatar presence timing limits

**How to override:**
1. Identify which limit is being broken
2. Write a one-sentence justification in the shot list or motion-intent: *why does this override increase authorship, proof clarity, or pacing quality?*
3. The justification must be specific to the beat — "the content required it" does not qualify
4. Confirm at QA that the override held up visually

**Not overridable by creative intent:**
- QA safety checks (encoding, safe zones, asset validity, caption readability)
- Gate enforcement (phases are sequential and required)
- Timing-sync rules (audio timing is not a creative choice)
- Asset presence (a missing asset cannot be substituted by taste)

**Example of a valid override:**
> `beat-07`: 4th consecutive FramedImage. Override justified: this beat is a 4-cut rapid-fire sequence at 3 frames each — the rapid cutting IS the variety. The rule targets monotonous holds, not intentional rapid montage.

**Example of an invalid override:**
> `beat-07`: 4th consecutive FramedImage. Override: the content worked better this way.

---

## Minimum Variety Rules

### Shot family variety

The **shot family** (what type of content is on screen) must change at least once every 4 consecutive beats.

Shot families:
- `avatar-only` — talking head, no content behind
- `split-image` — avatar + static screenshot
- `split-video` — avatar + demo video (responsive)
- `center-full` — demo video or b-roll, avatar hidden
- `text-card` — HeroTextCard or full-frame text treatment (avatar hidden)
- `avatar-overlay` — avatar full-screen with text/graphic overlay on top

If 4 consecutive beats share the same shot family: redesign the 3rd or 4th to break the pattern.

### Component family variety

The body must include at least **3 different component families** in any reel longer than 25 seconds:

| Family | Examples |
|---|---|
| **Text-dominant** | KeywordFadeIn, OverlayKeyword, HeroTextCard, CharKeyword, GlitchText |
| **Image-dominant** | FramedImage, ComparisonGrid, AnnotationCircle on screenshot |
| **Motion-dominant** | BRollVideo, demo video (center-full), StrikethroughSwap |
| **Avatar-dominant** | AvatarVideo full-screen or overlay-heavy |
| **Card/badge** | NumberPopup, BadgePopup, ToastCard, FeatureMockup, CardStack |
| **Annotation** | AnnotationCircle, LogoOverlay at a beat (not just hook) |

A reel that uses only text-dominant and image-dominant families will feel like a slideshow with words.

### Proof method variety

Any reel longer than 25 seconds must use at least **2 different proof methods**:

| Proof method | What it looks like |
|---|---|
| Screenshot at rest | Static FramedImage with zoom |
| Demo video | center-full product walkthrough |
| Annotated screenshot | FramedImage + AnnotationCircle (circle or underline) |
| Data/chart | FramedImage of a results chart or benchmark table |
| Animated component | FeatureMockup, TypingText, ToastCard |
| Side-by-side | ComparisonGrid |
| Logo reveal | LogoOverlay appearing at the moment a brand is named |

Screenshot-only proof sections longer than 3 beats are a signal to add a different proof method.

### Face-return cadence

After every 3 consecutive proof/image/center-full beats (avatar hidden or in split-screen for >6s continuous): insert a face-return beat before continuing the proof section.

Exception: if the proof section is supported by a center-full demo video with its own internal motion and narration is actively explaining visible on-screen action, up to 4 consecutive hidden-avatar beats are allowed.

---

## Repetition Limits

| Dimension | Max consecutive | Action if exceeded |
|---|---|---|
| Same component type | 3 | Insert a different component type before the 4th |
| Same avatar layout (split / full / hidden) | 3 | Insert a layout change |
| Same entry preset | 2 | Next entry must use a different entry preset |
| Text-dominant family (KeywordFadeIn, OverlayKeyword, HeroTextCard) without a proof beat between | 4 | Insert an image-dominant or motion-dominant beat |
| Zoom as primary motion (Ken Burns or punch-in zoom on most beats) | 2 | Next beat must use a different motion as its hero (wipe, punch, fade entry) |

These are hard limits. If the shot list violates any row, fix it before proceeding to technical planning.

---

## Pattern Interrupt Requirements

For longer reels, the body needs deliberate resets to prevent the viewer's attention from flattening out.

| Reel duration | Required pattern interrupts |
|---|---|
| <35s | 0 required (but 1 is encouraged if the proof section is dense) |
| 35–45s | At least 1 pattern interrupt |
| 45s+ | At least 2 pattern interrupts |

**What counts as a pattern interrupt:**

- `FlashReset` component between sections (editorial-authority style)
- A center-full beat after 3+ split-screen beats (forced layout change)
- An avatar full-screen return beat after 3+ proof/hidden beats (face re-entry with strong settle energy)
- A `HeroTextCard` section label that creates a full-frame text reset
- A `ChapterDivider` (tool introduction) that fully clears the previous visual context
- A `LightLeakOverlay` transition (cinematic-presenter) — max 1 per reel

Pattern interrupts should align with natural editorial pivots (end of proof section, start of CTA, section-to-section transition) — not inserted at random to hit the count.

---

## Avatar Presence Rules (Body)

These govern avatar visibility in the body, separate from the hook.

- **Max continuous avatar absence:** 12s (cinematic-presenter), 8s (editorial-authority)
  - Hard max: 15s (cinematic), 12s (editorial) — only one such block per reel, proof-protected only
- **After absence >6s:** the return beat must use stronger entry energy (see Return Beat Energy section below)
- **No more than 3 consecutive avatar full-screen beats** without a proof/image beat between them — even setup/direct-address runs should be broken by visual support
- **Avatar full-screen is reserved for:** direct address, CTA, setup beats where the face is the message. Do not use full-screen for every avatar beat by default.

---

## Caption Suppression Rules (Body)

Captions may be suppressed in the body under specific conditions.

**Valid when:**
- The entry is `display: "center-full"` and the visual contains readable on-screen text (UI labels, product copy, command output, results)
- The entry is a `card-carousel` or `CardStack` where text is baked into the visual
- Proof-escalation-editorial style: `demo-fullscreen` and `card-carousel` entries per the template registry

**Not valid when:**
- Avatar is full-screen or in split-screen and speaking narrated claims
- The visual is abstract b-roll with no readable on-screen text
- The narrator is delivering a claim that needs caption reinforcement (proof claims, CTA)
- The beat has an OverlayKeyword that paraphrases the narration — do not suppress the caption AND the overlay simultaneously

**Coverage target:** Caption suppression should cover 24–36% of total reel duration in proof-escalation-editorial style. In other styles, suppress only when the visual genuinely makes captions redundant.

---

## Transition Stack

The approved transitions for body beats in avatar-led AI reels. Transitions should be **invisible** — if the viewer notices the cut, the transition failed.

| Technique | When to use |
|---|---|
| **Clean jump cut** | Default between beats — no effect needed |
| **Punch-in zoom** | Narrator references a specific UI element, button, or result |
| **Cut on beat** | Hard cut timed to a word landing or SFX hit |
| **J-cut** | Audio from next scene starts before the visual cuts — bridges demos smoothly |
| **Soft fade / dip to white** | End of reel, or transition from demo back to avatar |
| **Speed ramp** | Reserved for high-energy moments (CTA reveal, proof payoff) |
| **Gesture match cut** | Cut on a matching movement — narrator hand gesture lines up with a visual action |

**Transition consistency rule:** Use at most 2 entry transition types and at most 2 exit transition types across the entire body. The reel should feel like one coherent edit, not a showcase of available presets.

---

## Text and Number Overlay Grammar

Use these components to reinforce spoken content with on-screen text at key body beats.

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
- **Max 4 consecutive beats with KeywordFadeIn** as the primary overlay (repetition limit from the component section above applies here too)

### Assembly checklist for narrated list items

For each "Number one, [tool name]" moment:
1. Add a `NumberPopup` at the number mention timestamp
2. Add a `KeywordFadeIn` at the tool name timestamp (0.5–1s after number)
3. Add a subtle click SFX at the number mention
4. Colors should follow the product brand or cycle through a palette

---

## Motion Language System

Every reel must have a **defined motion language** — a small set of consistent decisions that make every beat feel like it belongs to the same piece. Motion language is not about adding more transitions. It is about defining *how every beat behaves*, not just what asset plays when.

### Motion Budget Rule

Every beat gets exactly:
- **1 hero motion** — the primary visual event (wipe, scale entrance, focus crop)
- **1 support motion** — a secondary element that reinforces the hero (avatar settle, divider fade, caption lock)
- **1 accent** — a micro-event tied to a spoken emphasis word or editorial moment (scale pulse, opacity flash, SFX hit)

Do not exceed 3 motion elements per beat. If adding a 4th treatment, remove one first. Decorative layers (shimmer bands, glow borders, vignettes stacked on top of functional motion) are the first sign of template polish overtaking editorial restraint.

**The test:** if a motion element is removed and the beat still reads correctly, the element was decorative and should stay removed.

### Hold Behavior Rule

**Stillness is valid.** Body beats default to the `still` motion mode — no camera motion during the hold unless a specific reason applies.

Motion mode is assigned in Phase 4c (motion-intent) using the selection algorithm in `.claude/rules/motion-grammar.md`. The four modes: `still` (body default), `ambient` (opt-in for long holds with a focal point), `motivated` (pre-defined zoom coordinates tied to narration target), `transition-led` (entry animation carries the energy, hold settles).

During the hold phase:
- **Demo panels:** assign `motivated` if zoom coordinates are pre-defined from Phase 4b-iii. Assign `ambient` only if hold >2.0s, specific focal point, no other motion fires. Default: `still`.
- **Avatar beats:** natural speech motion is sufficient. Do not add breathe oscillation unless the hold is >3s with no visible speech motion.
- **B-roll:** if the clip has its own internal motion, assign `still`. Only add ambient to nearly-static clips with a clear focal point.

**Do not stack `zoom-in` entry preset + ambient hold** on the same beat (Stacked Motion — see `motion-grammar.md`).

### Four Beat Categories

Every beat belongs to exactly one category. Each has a defined motion principle.

#### Avatar beats
- **Motion principle:** push-in, caption lock, eye-line priority
- **Entry:** subtle scale settle (1.03–1.05 → 1.00 over 4–8 frames)
- **Hold:** `still` by default — natural speech motion is sufficient ambient presence. Assign `ambient` only if hold >2.5s and there is a specific focal point to drift toward.
- **Accent:** the spoken emphasis word is the accent — do not add visual effects unless the word is also a visual reveal
- **Exit:** hold last frame or soft opacity ease into next beat

#### Demo beats
- **Motion principle:** focus crop, pointer emphasis, panel framing — UI is *read* not just shown
- **Entry:** clipPath wipe from top OR fast scale entrance (1.08 → 1.00 over 5 frames)
- **Hold:** assign `motivated` if zoom coordinates are pre-defined (Phase 4b-iii); assign `still` if clip has cursor or typing motion; assign `ambient` only if hold >2.0s with clear focal point. Default: `still`.
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

---

## Flash and Accent Budget

- **Maximum 1 flash accent per reel** (any style). A 2-frame white flash or punch-in accent is a signature when used once. Used three times, it becomes a habit. All other bridges and beat endings should use opacity shifts, grade changes, or silence as their accent.
- The flash should be reserved for the single most important moment — typically the CTA reveal or the most impactful proof payoff.
- Editorial-authority exception: up to 2 flashes for reels <35s, up to 3 for 35s+ (governed by qa-gates.md).

---

## Return Beat Energy

When the avatar re-enters after a demo or b-roll section, the re-entry must feel intentional:
- Use a **stronger scale settle** than normal avatar beats (1.05 → 1.00 vs the normal 1.03 → 1.00)
- The background may shift (e.g. beams layer off, returning to clean Aurora)
- For the CTA return: use darker grade, slower push-in, and more confident energy than any other avatar beat — the CTA is the conclusion, not just another talking head insert

The strength of the return should be proportional to how long the avatar was absent. A 3s absence gets a normal stronger settle. A 10s absence gets the full return treatment: background shift + settle + grade change.

---

## Interface Variety as Credibility

When a reel shows multiple interfaces (e.g. Claude.ai web + Claude Code CLI), do not treat the CLI as a problem or inconsistency. Frame it as intentional variety:
- The web UI shows "where to start" (accessible, familiar)
- The CLI shows "the engine room" (technical credibility, proof of depth)
- The motion language (entry wipes, Ken Burns, transitions) should be consistent across both — the viewer never notices the interface changed because the edit rhythm stays the same

---

## Body Grammar Self-Test

At the end of Phase 4b-ii (component mapping), verify:

- [ ] No shot family runs more than 4 consecutive beats
- [ ] At least 3 different component families represented in the body
- [ ] At least 2 different proof methods for reels longer than 25s
- [ ] No component type repeated more than 3 consecutive beats
- [ ] No entry preset repeated more than 2 consecutive beats
- [ ] Text-dominant family not in 5+ consecutive beats without an image/proof break
- [ ] Zoom not the primary motion for more than 2 consecutive beats
- [ ] Pattern interrupt count meets reel duration requirement
- [ ] All avatar absence blocks within style-appropriate limits
- [ ] All gaps in beat map have assigned visual ownership (confirm at motion-intent phase)
