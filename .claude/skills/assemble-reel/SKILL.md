---
name: assemble-reel
description: Compose final reel timeline from approved shot list, motion intent, and validated assets.
disable-model-invocation: true
---


# Assemble Reel Skill

Use this skill when the project has:
- an **approved shot list** (`shot-list.md`) — required
- an **approved motion intent** (`output/motion-intent.md`) — required
- validated timing from real narration
- available and registered assets
- a defined reel structure
- captions ready or derivable from `audio/captions.json`

**The timeline is built FROM the approved shot list + motion intent**, not from scratch.
The shot list is the blueprint (what). The motion intent is the direction (how).
Assembly translates both into `output/timeline.json` and into a composition that is clear, social-first, and retention-optimized.

### Motion Intent Requirement

Assembly **must not begin** without an approved `output/motion-intent.md`.

The motion intent defines for every beat:
- Purpose, visual change, motion hierarchy (1 hero / 1 support / 1 accent)
- Landing event on the spoken emphasis word
- Handoff into the next beat
- Gap ownership for every speech pause
- Background seam behavior at every background change

Without this document, assembly produces "a good edit" — not an expert motion-designed reel. The motion intent is what elevates the edit.

### B-Roll Enhancement During Assembly

During assembly, review the b-roll scene library against the beat map:
- For each avatar-only or concept beat: does a b-roll insert exist that would improve comprehension?
- For each bridge/gap > 15 frames: would a brief b-roll flash add anticipation?
- Only use b-roll that adds understanding — not decoration
- B-roll should have been initially assigned during shot-list construction (Phase 4b). Assembly is the implementation pass, not the first review.

### Demo Clip Inspection

Before using any demo clip in the timeline:
1. Extract a frame from the clip at the trim point that will be visible in the reel
2. Visually inspect for: personal data, browser chrome, narrative mismatch
3. If personal data or chrome is found: use the Claude premium mock (`lib/capture/templates/claude-premium-mock.html`) to re-capture a clean version
4. If narrative mismatch is found: flag as a blocker — the clip must match what the narrator says

---

## Primary Goal

Build a reel that feels:
- **human-led**
- **proof-dense**
- **easy to follow**
- **visually fresh every 1–2 seconds**
- **trustworthy**
- **CTA-earned, not bolted on**

Assembly is not just about placing clips on a timeline.  
It is about making the viewer keep watching.

---

## Creative Intent Summary — Required When Structure Changes

If this assembly represents a **material structural change** — new beat layout, major component revision, new proof method, or significant reorganization of the timeline — produce a 6-field Creative Intent Summary (template in `CLAUDE.md` → "Creative Intent Summary" section) and wait for user confirmation before proceeding.

**Material structural change means:** adding, removing, or reordering beats; changing a component from one visual role to another; changing the proof method for a beat; changing avatar layout across a section. It does not mean: adjusting a zoom coordinate, tweaking an SFX level, fixing a missing asset reference.

**Not required for:** first assembly from an approved shot-list and motion-intent (those approvals already served as the Creative Intent confirmation). Required when assembly diverges from the approved blueprint.

---

## Retention-First Principles

These principles override default “clean demo” instincts.

1. **Face first, software second**  
   The avatar is the anchor. Software is the evidence.

2. **Proof before explanation**  
   Show the result or movement early, then explain what is happening.

3. **Do not let the middle go flat**  
   Long uninterrupted demo sections reduce retention.

4. **Every beat must visibly do a job**  
   Hook, setup, proof, mechanism, trust, recap, CTA.

5. **Show outcomes, not just process**  
   Deck created, file saved, permission prompt shown, result visible.

6. **Refresh the eye regularly**  
   Crop change, punch-in, badge, layout shift, face return, or new overlay.

7. **The CTA must feel earned**  
   Prefer recap + ask over a generic end screen.

---

## Remotion Reference

Before modifying Remotion components during assembly, consult the relevant rules at:

`remotion/.agents/skills/remotion-best-practices/rules/`

- **SFX**: `rules/sfx.md`
- **Transitions**: `rules/transitions.md`
- **Audio**: `rules/audio.md`
- **Sequencing**: `rules/sequencing.md`
- **Timing**: `rules/timing.md`

Load the full rule file before implementing changes in that area.

## Design Quality Reference

If any component feels generic, flat, or visually weak during assembly, consult the `frontend-design` skill before finalizing. This applies to:
- Typography decisions (weight, size, font pairing)
- Color choices (should align with project theme from `project.json`)
- Motion treatment (should feel designed, not default)
- Spatial composition (content placement within 1080x1920)

**Do not ship generic-looking components.** A component that would look the same in every reel regardless of topic needs design attention.

## Theme Reference

Read `project.json` for `theme`, `theme_primary`, `theme_secondary`. These values drive:
- Background colors (Aurora blobs, mesh gradients, solid backgrounds)
- Overlay accent colors (NumberPopup, BadgePopup, KeywordFadeIn, OverlayKeyword)
- HeroTextCard background palette
- Brand-aligned visual consistency

If theme fields are missing in project.json, run `theme-factory` before continuing assembly.

## Style-Aware Assembly

Read `project.json` for the `style` field before starting assembly. The style changes defaults throughout this skill.

### Style defaults table

| Decision | `cinematic-presenter` | `editorial-authority` |
|---|---|---|
| Default transition | `fade` (enterDur: 3, exitDur: 2) | `hard-cut` (enterDur: 0, exitDur: 0) |
| Text entry | `scale-pop` | `scale-pop-overshoot` |
| Section divider | scene background crossfade | `FlashReset` (2-3 frame white flash) |
| Avatar on-screen | 60-70% | 30-45% |
| Avatar layout | split-screen + full-screen | full-screen only (no split-screen) |
| Max consecutive center-full | 2 | 8 (full-frame is the default) |
| Avatar absence limit | 8s (12s with b-roll) | 18s |
| Demo display | center-full for video, split-screen for screenshot | full-screen (everything fills the frame) |
| Background style | Aurora/Beams for demos, GradientMesh for CTA | Solid colors, white for proof, dark for CTA |
| SFX minimum | 6-8 entries | 8-12 entries |
| SFX on hard cuts | required | not required (cut IS the punctuation) |
| Ken Burns | yes on static content | no — static holds are fine |
| Motion budget | 1 hero + 1 support + 1 accent | 1 hero + 0-1 support + 0-1 accent |
| Overlay types | NumberPopup, KeywordFadeIn, BadgePopup | HeroTextCard, OverlayKeyword, FlashReset, CursorClick |
| Gap ownership | required for all pauses | no gaps — every frame filled |

When the style is `editorial-authority`, also reference `styles/editorial-authority.md` for the full component list, color system, and editing formula.

---

## Global Rule References

This skill must follow these global rule files in addition to its local instructions:

- `.claude/rules/reel-workflow.md` (includes gate enforcement)
- `.claude/rules/timing-sync.md`
- `.claude/rules/visual-style.md`
- `.claude/rules/style-profiles.md`
- `.claude/rules/qa-gates.md`
- `.claude/rules/remotion-skill-required.md` — load `remotion-best-practices` rule files before writing Remotion code

### Rule precedence

When rules overlap, use this order:

1. **Workflow rules** — phase order, approval gates, shot-list-before-assembly
2. **Timing rules** — actual narration timing, beat structure, visual sync
3. **QA gates** — hard implementation and export blockers
4. **Visual style rules** — rendering defaults, backgrounds, overlays, layout system
5. **This skill** — editorial assembly decisions inside those constraints

### Important display-mode exception

`visual-style.md` defines the rendering default that demo videos should almost always be `center-full`.

For this retention-first assembly skill, that remains the **default technical assumption** for full-attention demo moments.

However, beat intent may override that default when:
- presenter anchoring is more important than maximum demo size
- the beat is hook, setup, mechanism, trust, recap, or explanation-led
- split-screen or responsive layout materially improves retention or clarity

In short:
- use `center-full` by default for short proof bursts and true full-attention demo moments
- allow split / responsive override when the reel is stronger with the avatar visibly anchoring the beat

---

## Responsibilities

- create `output/timeline.json`
- assign assets to lanes
- define scene order
- translate beat intent into visual behavior
- map beats to visuals and overlays
- insert captions
- insert transitions and SFX intentionally
- preserve social-first presenter anchoring
- prepare composition data for rendering
- document any deviation from `shot-list.md`
- **render preview frames after every major beat is added to the timeline (not at the end)**

### Mandatory: beat-by-beat preview render during assembly

Do not write the entire `timeline.json` and then render preview frames at the end. **Render after every major beat is added.** Static reading of component source isn't sufficient — visual issues (z-index, color, layout, animation timing, gap rendering) only become visible in actual frames.

The preview render is now scripted:

```bash
python -m lib.preview_beats projects/<slug>
```

This reads `output/timeline.json`, finds the midpoint of every editorial beat, and renders all of them as PNG stills via `npx remotion still`. Outputs go to `projects/<slug>/output/preview/`.

**Required workflow:**

1. Add 1-3 beats to `timeline.json`
2. Run `python -m lib.preview_beats projects/<slug>` to render the new beats
3. Read each rendered PNG via the Read tool and visually verify:
   - Component is visible (z-index correct)
   - Color renders as expected (especially SVGs — see `feedback_svg_color_through_img.md`)
   - Layout matches the shot list (split-screen ratio, avatar position)
   - Overlays don't cover the avatar's face during avatar beats
   - Background color is correct (warm beige / dark / content-driven)
   - Caption is readable
4. Fix any issues before adding the next beat
5. Repeat

**Why this matters:** in the past, all visual issues were discovered at the Phase 5b preview gate at the end of assembly, leading to multiple iteration cycles. Catching issues at the beat where they occur reduces total iterations and prevents compounding bugs. See `feedback_render_frames_early.md` in user memory.

### Vendored libraries to check before building anything new

- `remotion/src/components/effects/clippkit/` — vendored from clippkit (MIT). BarWaveform, CircularWaveform, GlitchText, TypingText, ToastCard. See `clippkit/NOTICE.md`.
- `lib/feature_mockups/presets.json` — pre-built `FeatureMockup` configs (12 presets across security, observability, infrastructure, platform, performance categories). Pull via `from lib.feature_mockups import preset`.
- `lib/edit_plan/` — edit-plan compiler (`validate`, `compile`, `summary`, `parity`). Compiles `output/edit-plan.json` into `output/timeline.json` deterministically. Use it instead of hand-writing timeline JSON when the project has a structured edit plan.

---

## Preconditions

- **`shot-list.md` must exist and be approved** — including:
  - Phase 4b-i: Visual assignment (approved)
  - Phase 4b-ii: Component mapping + asset fitness (all MATCH or PARTIAL with documented plan, zero MISMATCH/MISSING)
  - Phase 4b-iii: Technical planning (backgrounds, SFX, transitions)
- **Component mapping must be complete** — every beat must have a named Remotion component, avatar layout, and content zone. See `.claude/rules/component-mapping.md`.
- **Asset fitness must pass** — no MISMATCH or MISSING scores. All PARTIAL scores must have a documented fix (crop, zoom, or annotate).
- `audio/source.wav` must exist
- `audio/beat-map.json` must exist
- `audio/captions.json` should exist when available
- `audio/voice.json` is helpful but optional
- `assets/catalog.json` must contain at least one approved asset
- all referenced assets must be real and readable

## Workflow and Timing Authority

Assembly may begin only when all of the following are true:

- `shot-list.md` exists and is approved
- `audio/source.wav` exists
- `audio/beat-map.json` exists
- actual timing is coming from real narration audio or extracted final avatar audio
- referenced assets are registered and available

Do not begin timeline assembly from script-estimated timing when real audio exists.

Do not skip the workflow order:
- demos are captured before shot list finalization
- b-roll matching/cutting happens before shot-list approval when used
- the approved shot list is the blueprint for `output/timeline.json`
- QA happens after assembly and before render

If project artifacts conflict:
- actual narration timing wins
- approved shot list wins over speculative assembly ideas
- missing or unapproved inputs block assembly

---

## Core Inputs

Assembly should read and reconcile:

- `shot-list.md`
- `audio/beat-map.json`
- `audio/captions.json`
- `assets/catalog.json`
- `project.json`

If any of these disagree, **real narration timing is the source of truth**.

---

## Output Files

- `output/timeline.json`
- `output/caption.md` — Instagram caption (required, see Caption Generation below)
- optional assembly summary in `output/assembly-notes.md`
- updated `project.json` with `status → assembled`

---

## Timeline Lanes

The timeline should support at minimum:

- `avatar`
- `demo`
- `broll`
- `support_visuals`
- `captions`
- `overlays`
- `sfx`
- `music`

Every lane entry must be traceable to:
- a beat ID
- a scene purpose
- a timing source
- an asset source

---

## Required Metadata Per Visual Entry

Each visual entry should include, when applicable:

- `beat_id`
- `intent`
- `start`
- `end`
- `asset`
- `lane`
- `display`
- `transition_preset`
- `zoom_moments`
- `overlay_refs`
- `notes`

**Additional fields when style is `proof-escalation-editorial`:**

- `template_id` — from shot-list (e.g. `proof-overlay-split`, `demo-fullscreen`). Copied from the approved shot list.
- `captionMode` — derived from template_id via `training/derived/caption-modes.json` → `template_to_caption_mode` lookup. Values: `headline`, `suppressed`, `section-label`, `badge-overlay`, `standard`.
- `splitRatio` — derived from template_id via `training/derived/template-registry.json` → `split_ratio` field. Values: `50/50`, `65/35`, `100/0`, `0/100`.
- `proof_class` — from shot-list. Used by QA to validate proof escalation order.

When `captionMode` is `suppressed`, the composition must NOT render caption text during this entry's time range. When `splitRatio` differs from the default 40/60, the composition must adjust the content container and avatar boundary accordingly.

Do not create orphan visuals with no beat ownership.

---

## Beat Intent System

Every beat must be tagged with one of these intents:

- `hook`
- `setup`
- `proof`
- `demo`
- `mechanism`
- `trust`
- `recap`
- `cta`

If the shot list does not include intent, infer it during assembly and note it.

### Intent behavior map

#### 1. Hook
Goal: create curiosity instantly and show early proof.

Visual rules:
- avatar should be dominant
- reveal the result early
- use `responsive` or a custom hook split layout
- allow a fast screen reveal over or above the avatar
- do not start with a static software-only screen unless the software visual is inherently shocking

#### 2. Setup
Goal: orient the viewer quickly.

Visual rules:
- keep the avatar visible full-screen or medium PIP
- introduce labels, feature name, or product context
- avoid long pure exposition over static screens

#### 3. Proof
Goal: show a real outcome happened.

Visual rules:
- prioritize the result moment
- allow short center-full bursts if the proof is strong
- use badge or highlight to make the outcome undeniable

#### 4. Demo
Goal: show how the action unfolds.

Visual rules:
- split-screen is usually preferred if explanation is ongoing
- only use long full-screen demos when narration is minimal and the action is visually self-explanatory
- break long demos into smaller proof packets

#### 5. Mechanism
Goal: explain why it works differently.

Visual rules:
- avatar should usually be visible
- use overlays or UI callouts
- do not let “mechanism” become an energy dip

#### 6. Trust
Goal: remove fear or objection.

Visual rules:
- slow slightly
- isolate the sensitive UI element
- dim surrounding interface if helpful
- make the trust moment feel deliberate

#### 7. Recap
Goal: remind the viewer of the wins they just saw.

Visual rules:
- montage or rapid callbacks
- can be layered behind the avatar
- use 2–4 proof flashes maximum

#### 8. CTA
Goal: convert interest into action.

Visual rules:
- avatar should usually return as dominant
- recap before ask when possible
- do not end on a generic empty frame

---

## Presenter Anchor Cadence

This is a core retention rule.

### Rules
- In the **first 15 seconds**, do not stay away from the face for more than **3.0 seconds** unless a proof moment clearly justifies it.
- After 15 seconds, do not stay away from the face for more than **8.0 seconds** without:
  - returning to the avatar in split-screen or full-screen, or
  - introducing a strong presenter-linked overlay moment, or
  - landing a major proof payoff that clearly advances the reel
- After any center-full run longer than **8 seconds**, a face return **is required** — either:
  - switch the next beat to split-screen, or
  - insert a brief avatar-visible beat before continuing center-full

### Center-full budget

Do not assign `center-full` to every demo beat by default. Apply a maximum:

- **At most 2 consecutive center-full entries** before a split-screen or avatar-visible break
- If 3+ beats are all screenshots, at least one must be split-screen
- Demo **videos** may be `center-full` — but static **screenshots** should default to split-screen unless they require full detail (see `visual-style.md` screenshot defaults)

### Layout variety checklist (run before finalizing timeline)

Before writing the final timeline, verify:

- [ ] At least one split-screen beat appears in the first 15 seconds (usually the hook)
- [ ] Face returns at least once before the 15-second mark
- [ ] No continuous avatar absence longer than 8 seconds
- [ ] No more than 2 consecutive center-full entries
- [ ] If center-full runs are unavoidable (all demos are long videos), compensate with overlays: `BadgePopup`, `KeywordFadeIn`, or section labels so the viewer has visual variety within the center-full section

### Default stance
If unsure, **show the avatar more often**, not less.

---

## Display Mode Assignment

Every demo and b-roll entry must have an intentional `display` mode.

### Important change
**Do NOT default demo videos to `center-full`.**  
Use `center-full` only when the software itself is the entire point of attention for a short, high-value moment.

### Preferred display logic

#### `responsive`
Use for:
- hook openings
- face-led split-screen moments
- proof-while-explaining moments
- any beat where both human presence and UI evidence matter

#### `center-full`
Use for:
- short proof bursts
- cinematic b-roll
- deck reveal moments
- file save confirmations
- UI moments that genuinely need full attention

Do **not** keep long explanatory demo runs in `center-full` by default.

#### `full-screen avatar`
Use for:
- hook opener if face-led
- setup
- CTA
- recap + CTA
- trust explanation if the software visual is secondary

#### `split-screen`
Use for:
- explanation + software proof
- mechanism beats
- deck building beats
- tool walkthroughs that still need presenter anchoring

### Display mode guardrails

Use the visual-style display system as the baseline:

- `center-full` for true full-attention demo or cinematic moments
- `responsive` for hook opening or landscape content that must stay uncropped
- default split when the presenter and the visual both need to remain visible

### Hard implementation rules

When using `center-full`:
- add the entry `{start, end}` range to `centerFullRanges`
- pass `hideRanges={centerFullRanges}` to the avatar component
- keep the BRollVideo container background transparent
- do not let `isHiddenByAvatar` filter out center-full entries

### Background rules

Every scene must have an explicit background scoped to its own time range.

Use:
- `AuroraBackground` for hook split-screen and split-screen demo scenes
- `AuroraBackground + BackgroundBeams` for center-full demo / b-roll scenes
- `GradientMesh` style backgrounds only for avatar full-screen CTA / outro / direct-address scenes

Never let:
- a dark background run behind demo scenes
- a single background run for the full composition
- opaque dark demo containers hide the intended scene background

### Zoom rules

For demo images shown with `objectFit: contain` and `objectPosition: top`, use the visual-style zoom formula:

- `frame_x = image_x`
- `frame_y = image_y × 0.57`

Do not use raw image Y coordinates for split-screen demo image zooms or the punch-in will drift into white space.

---

## Split-Screen Dominance Rules

For retention-led reels, the avatar should often be **slightly larger** than the software.

### Recommended ratios

#### Hook split
- software panel: ~40–45% of frame height
- avatar zone: ~55–60%
- avatar should still feel like the main subject

#### Explanation split
- software panel: ~42–48%
- avatar zone: ~52–58%

#### Trust split
- software panel can temporarily enlarge if the permission prompt needs clarity
- restore avatar dominance after the key trust moment lands

### Rule
Avoid perfectly equal 50/50 split unless there is a specific design reason.  
The face should feel like the anchor and the UI should feel like the evidence.

---

## Proof Packet Logic

When a beat spans more than a simple one-shot reveal, break it into micro-payoffs.

### Preferred packet structure
1. **Input**
2. **Processing**
3. **Result**
4. **Save / output**
5. **Reaction / reframe**

Not every demo needs all five, but long demos should not remain one continuous visual mode.

### Example
For a file workflow:
- files enter
- tool reads
- report builds
- file saves
- avatar or overlay confirms value

### Rule
If a demo section feels like “watching software for several seconds,” split it into proof packets.

---

## Pattern Interrupt Frequency

Assembly must create regular visual freshness.

### Rules
- In the first **12–15 seconds**, do not let more than **1.5 seconds** pass without a meaningful visual refresh.
- After that, do not let more than **2.0 seconds** pass without a refresh unless the current proof moment needs breathing room.

### Acceptable refresh events
- crop change
- zoom punch
- badge
- overlay
- cursor emphasis
- layout shift
- face return
- support card
- recap flash
- result confirmation
- permission isolate

### Not acceptable
- invisible changes
- decorative motion with no editorial purpose
- repeating the same transition rhythm mechanically

---

## Zoom Moments

Each demo and b-roll entry may include `zoom_moments` — timed punch-in targets.

```json
{
  "beat_id": "beat-04",
  "intent": "proof",
  "start": 10.560,
  "end": 17.440,
  "asset": "demo-chatgpt-el10.png",
  "display": "responsive",
  "zoom_moments": [
    { "at": 0.8, "x": 44, "y": 20, "scale": 2.2, "holdFor": 1.2, "reason": "prompt entered" },
    { "at": 2.4, "x": 57, "y": 48, "scale": 1.9, "holdFor": 1.0, "reason": "result appears" },
    { "at": 4.0, "x": 72, "y": 82, "scale": 2.1, "holdFor": 1.4, "reason": "file saved" }
  ]
}


Rules
at is relative to clip start
coordinates must target the actual visible element
do not guess coordinates
zooms should support narration, not replace it
a punch-in should usually land on:
a command
a result
a button
a save/output
a permission prompt
do not add zooms to empty space
Coordinate rules
for video / cover visuals: coordinates map directly
for images / contain visuals: apply the letterbox formula from visual-style.md
Overlay System

Use a simple, repeatable overlay hierarchy.

Overlay types
1. Keyword Emphasis

Use for:

core claims
feature names
short reveal language

Examples:

ONE SENTENCE
REAL FILES
FULL DECK
ASKS FIRST
2. Utility Badge

Use for:

outputs
confirmations
saved states
system decisions

Examples:

SAVED ✓
EXCEL FILE
PERMISSION REQUIRED
YOU DECIDE
3. Progress / Proof Chip

Use for multi-step demos.

Examples:

1/3 INPUT
2/3 BUILD
3/3 SAVE
Rules
prefer one primary overlay at a time
a secondary support badge is allowed
never allow more than two overlays to compete at once
overlays must reinforce the beat’s job, not decorate it
if a beat already has strong visual proof, keep overlaying minimal
Caption Behavior

Captions are part of retention, not just accessibility.

Rules
max 2 lines
chunk into short readable phrases
prefer 3–6 words per phrase
update roughly every 0.6–1.2 seconds
emphasize nouns, verbs, and outcomes
do not highlight filler words unless contrast requires it
Use emphasis on words like
result
built
saved
deck
files
asks
control
follow

Captions must remain readable over all display modes and stay within safe zones.

Transition Preset Names

Use these exact strings in transition_preset.enter and transition_preset.exit:

Enter:
punch, slide-up, slide-left, zoom-in, scale-pop, scale-pop-overshoot, glitch, fade, wipe-up, zoom-through, blur-dissolve, luminance-sweep, iris-reveal, whip-pan, smooth-push, hard-cut, flash-reset, slide-stack

Exit:
punch-out, slide-down, slide-right, scale-down, fade, wipe-down, zoom-through-out, blur-out, whip-out, iris-close, hard-cut

**Editorial-authority defaults:** Use `hard-cut` as the baseline for most entries. Use `scale-pop-overshoot` for HeroTextCard entries. Use `slide-stack` for CardStack entries. `flash-reset` is paired with the FlashReset component placed in a separate Sequence.

Default if omitted:

enter: "fade"
exit: "fade"
enterDur: 3
exitDur: 2
Transition Selection Rules

Every visual entry must have a transition that matches the beat’s intent.

Selection guide
Beat intent	Recommended enter	Recommended exit	Notes
hook reveal	zoom-in, smooth-push, slide-up	fade	fast, confident, proof-first
setup	fade, scale-pop	fade	clean orientation
proof burst	zoom-in, wipe-up, smooth-push	fade	let the payoff land
demo packet	slide-up, whip-pan, smooth-push	fade	keep motion fresh
trust	zoom-in, fade, iris-reveal	fade	precise, controlled
recap	whip-pan, slide-left, zoom-through	fade	quick but readable
CTA	scale-pop, fade	fade	emphasis without chaos
Rules
never use the same enter transition on 3+ consecutive entries
use 3–5 frame enters for punchy moments
use 6–10 frame enters for smoother reveals
exits should usually be fast
use kenBurns on static images only
do not overuse flashy transitions in trust or CTA sections
SFX Placement Rules

SFX must feel editorial, not generic.

Placement guide
Moment	SFX type	Volume	Duration
layout / scene change	whoosh or sweep	0.35–0.55	0.3–0.8s
key word emphasis	pop or hit	0.45–0.65	0.15–0.4s
proof reveal	chime, click, soft impact	0.30–0.50	0.2–0.8s
file save / output	confirmation tick or notify	0.30–0.45	0.2–0.6s
permission prompt	subtle isolate / hush / click	0.20–0.40	0.2–0.6s
CTA	riser, notify, subtle chime	0.30–0.45	0.6–1.5s
Rules
every SFX must land on a narration beat or visible editorial event
do not place SFX arbitrarily
verify files are audible and non-silent
set volume intentionally per entry
avoid overlapping narration peaks
use micro-reward sounds for real proof moments, not just scene changes
Micro-reward sound examples
prompt entered
file dropped
report populated
save completed
slide revealed
permission requested
Reward Moment Holds

Not every moment should move at the same speed.

Hold slightly longer on:
deck reveal
file save
result confirmation
permission prompt
key before/after comparison
Rules
allow a proof moment an extra 6–12 frames if it improves comprehension
do not rush the exact moment that proves the claim
a hold should feel intentional, not slow
Numbered and Keyword Overlays

When the narration uses numbered framing, use:

NumberPopup
KeywordFadeIn

Components:

remotion/src/components/effects/NumberPopup.tsx
remotion/src/components/effects/KeywordFadeIn.tsx
Rules
NumberPopup lands exactly on the spoken number
KeywordFadeIn lands shortly after the tool or feature name
pair with subtle click SFX
use brand-matched styling where appropriate

For non-numbered reels, reuse the same editorial logic with keyword overlays and utility badges.

Layout Flow Pattern

Use this retention-first flow as the default pattern for avatar-led AI demo reels:

Hook
avatar dominant
result reveal early
split or face-led opener
Setup
avatar visible
feature/context introduced fast
support visuals optional
Proof packet 1
demo + overlay + zoom + result
short, clear, outcome-led
Proof packet 2 / mechanism
another real task or explanation
reintroduce avatar if demo has run too long
Trust / objection handling
isolate sensitive moment
reassure visually
Recap
montage or callback flashes
CTA
avatar dominant
ask aligned to the exact value delivered
Important

Do not force b-roll into every beat.
Do not force center-full demos into every demo beat.
Do not let the reel turn into a long software walkthrough.

StackedImageReveal Component — NOT YET BUILT

StackedImageReveal is planned for grouped screenshots or related proof images.
**Until built, use multiple `FramedImage` entries in rapid sequence (3-5 frames each) with `zoom-in` transitions.**

Planned path:
remotion/src/components/effects/StackedImageReveal.tsx

Use it when:

showing multiple outputs
comparing related screens
inserting visual variety between software-heavy sequences

Do not use it as filler.

Scene Background Assignment

Every scene must have an explicit background scoped to its time range via <Sequence>.

Use background choice to support clarity:

bright / clean for hook and setup
neutral / transparent for software proof
slightly darker or more focused for trust moments
premium / intentional for CTA

Background changes should support the emotional beat, not distract from it.

Shot List Translation Rules

Each approved shot-list row becomes one or more timeline entries.

Rules
do not add off-plan visuals without noting the deviation
if a single shot-list beat spans too much narrative work, split it into multiple timeline entries while preserving the original beat ID
timing must remain traceable
every timeline split must improve proof clarity or retention
Assembly Workflow

Follow these steps in order.

Step 1 — Read the blueprint

Read:

shot-list.md
audio/beat-map.json
audio/captions.json
assets/catalog.json

Confirm all assets referenced in the shot list exist.

Step 2 — Tag each beat by intent

Assign each beat one primary intent:

hook
setup
proof
demo
mechanism
trust
recap
CTA
Step 3 — Decide display mode per beat

Choose display based on beat job, not habit.

Ask:

does the face need to remain visible?
is this an explanation or a payoff?
is full-screen proof justified here?
would split-screen improve retention?
Step 4 — Break long demos into proof packets

If a visual run feels flat:

split it
add zooms
add overlays
add result emphasis
return to face when needed
Step 5 — Add transitions

Assign transitions that fit scene purpose.
Avoid repetitive rhythm.

Step 6 — Add overlays

Use keyword emphasis, utility badges, and progress chips.
Do not over-layer.

Step 7 — Add SFX

Support layout changes and proof moments.
Prefer fewer, better SFX over noisy timelines.

Step 8 — Validate cadence

Check:

no dead middle
no long unexplained full-screen demos
no long face absence
proof moments visibly land
CTA feels earned
Step 9 — Write timeline output

Produce output/timeline.json with traceable structure.

Validation Checklist

## Hard Assembly Gates

Before assembly can be considered complete, these implementation gates must pass:

### SFX and transitions
- every scene or layout change must have at least one SFX or a deliberate transition
- every referenced SFX file must exist and be non-empty
- SFX volume must be set per entry
- transitions must render visibly
- no more than 2 consecutive entries may share the same enter transition type
- enter durations must stay within 3–10 frames
- exit durations must stay within 2–4 frames

### Backgrounds and containers
- demo scenes must use white/light backgrounds
- avatar full-screen scenes must use dark backgrounds only where appropriate
- BRollVideo containers must remain transparent
- background changes at layout boundaries must be clean

### Short clip safety
- clips shorter than 30 frames must use proportional fade durations:
  `fadeIn = Math.min(15, Math.floor(durationInFrames * 0.3))`
- center-full entries must remain visible even during avatar hide/full-screen logic
- if timeline JSON typing requires it in implementation, cast imports as `as unknown as Timeline`

### Editorial sync
- demo action appears when referenced
- proof appears during or immediately after the supported claim
- captions and overlays do not cover the key interaction
- dead air or empty visual gaps are not introduced by assembly

Before completing assembly, verify:

Structure
 timeline.json is valid
 all entries map to approved beats
 scene order is understandable
 timing comes from real narration
Retention
 first 15 seconds contain regular visual refreshes
 no long flat demo run without proof packets
 presenter disappears for no excessive stretch
 proof moments are emphasized
 trust moment is visually clear
 CTA is supported by recap or clear payoff memory
Visuals
 display modes are intentional
 avatar scale supports social-first viewing
 zooms target real UI elements
 overlays are readable and not overcrowded
 captions stay inside safe zones
Audio
 SFX align to beats or proof events
 SFX are audible but not overpowering
 music does not compete with narration
Editorial quality
 proof is shown before long explanation
 middle section does not feel repetitive
 transitions vary enough for rhythm
 no decorative motion without purpose
---

## Instagram Caption Generation

Every assembly must produce `output/caption.md`.

The caption is written for readers who may not have watched the reel yet. Its job is to make them want to watch — or to reinforce the value for those who already did. It is **not** a transcript of the voiceover.

---

### Caption structure

Write the caption in this order, with a blank line between each block:

**1. Hook line (standalone paragraph)**
One sentence. No tool name. Value- or outcome-led.
The hook must be a **different line** from the script opening — do not copy the voiceover hook.
Good hooks: "This free Google AI tool is going to save a lot of people hours." / "Most people don't know this tool exists yet." / "I didn't expect this to work as well as it does."

**2. Tool reveal + core proof (1–2 sentences)**
Name the tool. State the single most impressive thing it does.
Example: "It's called Stitch, and it can build a full clickable website from just one prompt."

**3. Feature paragraph(s) (1–2 sentences each, one paragraph per major beat)**
Cover the same features in the same order as the reel beats.
- Lead with personal voice on the first feature: "One feature I really like:", "One thing that surprised me:", "What I didn't expect:"
- Use benefit framing on subsequent features: "for you", "automatically", "in the same workflow", "without doing anything extra"
- Keep each paragraph to 1–2 sentences max

**4. Surprise / kicker feature (1 sentence)**
Use a different setup from the script's version.
Script used "here's the part most people don't expect" → Caption uses "And if that wasn't enough," or "What really got me:"

**5. Recap with pain-point framing (1 sentence)**
Mirror the reel's recap beat but add a pain-point angle the script doesn't have.
Script: "without ever leaving the canvas" → Caption: "So instead of jumping between tools, you can go from concept to prototype without leaving the canvas."

**6. Value anchor (1–2 sentences)**
If the tool is free or easy to access, this is the "best part" moment.
Format: short setup ("Best part?") followed by the value statement.

**7. Follow CTA (1 sentence)**
Specific — name the content niches, not just "more like this".
Format: "Follow for more [niche 1] and [niche 2] discoveries."
Example: "Follow for more AI website builder and free AI tool discoveries."

---

### Caption rules

- **No hashtags** in the body — clean format for IG feed
- **No emojis** unless the project brief explicitly uses them
- **No transcript copying** — every sentence must be rewritten, not lifted from the voiceover
- **Mobile-first paragraphing** — short blocks, blank line between each, max 2 sentences per block
- **Personal voice** on at least one feature — creates trust and a human editorial filter
- **Benefit language** not feature language — "it does X for you" not "X is a feature"
- **Specific CTA** — name the content category the viewer would follow for, not generic "more videos like this"

---

### What to read before writing the caption

- `script.md` — for beat order, features covered, CTA angle, proof promise
- `brief.md` — for hook category, audience, and what makes this tool worth sharing
- `audio/beat-map.json` — to confirm the order features appear in the reel

The caption must mirror the reel's feature order so it feels consistent whether the viewer reads first or watches first.

---

### `output/caption.md` required format

```markdown
# Instagram Caption: [project-slug]

---

[Hook line — single sentence, no tool name]

[Tool reveal + core proof — 1–2 sentences]

[Feature 1 — personal voice opener, 1–2 sentences]

[Feature 2 — benefit framing, 1–2 sentences]

[Kicker feature — 1 sentence]

[Recap with pain-point framing — 1 sentence]

[Value anchor — 1–2 sentences]

[Follow CTA — 1 sentence]
```

---

Output Expectations

At the end:

output/timeline.json is valid
output/caption.md is written and follows the caption structure above
composition data is renderable
scene order is clear
timing is traceable
retention logic is visible in the edit plan
project.json updated (status → assembled)

If tradeoffs were made, note them in the assembly summary.

## Mandatory SFX Checklist

SFX planning is not optional and must not be deferred to QA. Every project that defers SFX to QA fails.

### Before completing assembly, verify:

1. **Every layout change has an SFX entry** — count the layout transitions in the timeline (center-full → split-screen, split-screen → center-full, avatar → demo, demo → avatar). Each must have at least one SFX.

2. **Every NumberPopup has a click SFX** — if the reel uses numbered lists with NumberPopup overlays, each number reveal needs a soft click SFX at the same timestamp.

3. **Animated b-roll beats have ambient SFX** — b-roll clips showing data transfer, processing, or transformation (not static illustrations) should have a subtle processing/transition SFX during the animation.

4. **Hook has an opening SFX** — a subtle riser or whoosh at 0.00 to mark the reel start.

5. **CTA has a confirmation SFX** — notification or confirmation tone when the CTA action word appears.

6. **All SFX asset files exist** — run `ls remotion/public/*.mp3` and verify every SFX filename referenced in the timeline exists and is >1KB.

7. **Volume is set per entry** — never rely on default volume. Set volume explicitly (0.18–0.30 range for most SFX).

### SFX count targets
- 30–40s reel: minimum 6 SFX entries
- 40–55s reel: minimum 8 SFX entries
- If the reel has fewer than the minimum, review every layout change and beat transition for missing sound design.

## Avatar Layout Mapping

The avatar lane layout field must match the visual context of co-occurring content. Mismatches cause the face to be covered by overlays.

| Visual context | Avatar layout | Why |
|---|---|---|
| Beat has image/screenshot in top 40% | `split-screen` | Avatar renders in bottom 60%, image sits cleanly above |
| Beat has center-full video or broll | No avatar entry (hidden by centerFullRanges) | Avatar is not visible during center-full |
| Beat has responsive broll in top 40% | `full-screen` | Avatar visible in bottom 60% via responsive layout |
| Beat is avatar-only (no visual overlay) | `full-screen` | Avatar fills the screen |

**Rule:** Never set avatar layout to `full-screen` when an image, screenshot, or split-screen overlay occupies the top portion of the frame. The image will render on top of the avatar's face.

## Layer Overlap Prevention

Do not create overlapping center-full entries across the demo and broll lanes. If two center-full entries overlap in time, one will be invisible (hidden behind the other at the same z-index).

### Rules
- If a demo video spans multiple beats AND a later beat has its own broll entry, the demo must end before the broll starts, OR the broll entry must be removed.
- In ReelComposition.tsx, the demo layer renders BEFORE the broll layer. This means broll entries appear on top when they overlap with demos. If this is not the intended behavior, remove the overlap.
- Before finalizing the timeline, scan all center-full entries across demo and broll lanes and check for time overlaps.

### Pre-assembly asset inventory
Before planning assembly, run `ls assets/` and list all existing files the user has provided. Match each file to a beat. Do not re-capture, substitute, or overlook assets the user has already provided. Update assets-needed.md to reflect what exists.

Stop Condition

Stop after assembly is validated against the checklist above.
Do not assume QA pass automatically.

