---
name: motion-intent
description: Write beat-by-beat motion direction with preset mapping that translates editorial intent into Remotion animation values, required between shot-list approval and timeline assembly.
---

# Motion Intent Skill

Use this skill when:
- `shot-list.md` exists and is approved (all three phases complete)
- the project needs motion direction before assembly
- the user says "motion intent", "motion direction", "how should each beat move", or similar

This is **Phase 4c** — the motion direction phase.
It runs after the approved shot list (Phase 4b) and before asset prep (Phase 4d) and assembly (Phase 5).

Without this document, assembly produces "a good edit" — not an expert motion-designed reel. The motion intent is what elevates the edit from functional to intentional.

---

## Primary Goal

Produce `output/motion-intent.md` that tells the assembly phase exactly how every beat should move, enter, exit, and hand off to the next beat.

Every beat must answer five questions:
1. **Purpose** — what is this beat's editorial job?
2. **Visual change** — what shifts on screen and what stays?
3. **Motion hierarchy** — hero / support / accent (max 3 elements)
4. **Landing** — what happens on the spoken emphasis word?
5. **Handoff** — how does this beat give way to the next?

The motion intent must also define:
- gap ownership for every speech pause
- background seam behavior at every background change
- beat category for every beat
- preset mapping from editorial intent to Remotion values

---

## When to Trigger

Use this skill when:
- shot-list.md is complete and approved (all three phases: visual assignment, component mapping, technical planning)
- the project is ready for motion direction
- the user wants to define how each beat moves before assembly

Do not use this skill for:
- deciding what the viewer sees (use `shot-list`)
- building the timeline (use `assemble-reel`)
- writing the script (use `reel-script`)
- doing QA (use `qa-reel`)

---

## Global Rule References

This skill must follow these global rule files in addition to its local instructions:

- `.claude/rules/reel-workflow.md` — preset vocabulary, duration bounds
- `.claude/rules/motion-grammar.md` — **read first** — motion modes, anti-patterns, stillness doctrine, beat-level examples
- `.claude/rules/visual-style.md` — gap ownership, flash budget, background seams
- `.claude/rules/style-profiles.md` — cinematic-presenter vs editorial-authority motion defaults
- `styles/cinematic-presenter.md` — motion defaults, transition table, background mapping
- `styles/editorial-authority.md` — hard cuts, no ambient motion

### Rule precedence

When rules overlap, use this order:

1. **Workflow rules** — preset vocabulary (exact preset names), duration bounds
2. **Style profile** — cinematic-presenter or editorial-authority motion defaults
3. **Visual style rules** — motion budget, gap ownership, flash budget, beat categories
4. **This skill** — editorial motion decisions inside those constraints

---

## Workflow Alignment

This skill runs in **Phase 4c — motion intent**.

Before starting, these must be true:
- shot-list.md is complete with all three phases (4b-i, 4b-ii, 4b-iii)
- shot-list.md is approved by the user
- beat-map.json exists with real timing

After this skill completes:
- asset prep (Phase 4d) uses motion direction to know which assets need encoding
- assembly (Phase 5) uses motion-intent.md as the "how" blueprint alongside the shot-list "what" blueprint

### Important workflow rule

**Motion intent is a required approval gate.** Assembly must not begin without an approved `output/motion-intent.md`.

---

## Required Inputs

Before starting, read:

- `shot-list.md` — visual assignment, component mapping, technical planning
- `audio/beat-map.json` — beat IDs, timing, phrases
- `project.json` — style, theme
- `audio/captions.json` — for timing reference on emphasis words

---

## Responsibilities

- categorize every beat (avatar, demo, concept/proof, return)
- define motion hierarchy per beat (1 hero + 1 support + 1 accent max)
- map editorial intent to exact Remotion preset values
- define gap ownership for every speech pause
- define background seam transitions
- enforce the flash/accent budget
- enforce transition consistency (max 2 types per direction)
- produce a complete motion-intent.md

---

## Core Principle

**Motion is editorial, not decorative.**

Every motion choice must serve the beat's job. If removing a motion element and the beat still reads correctly, the element was decorative and should stay removed.

The motion intent is not about "making it look better." It is about making the viewer **feel** the editorial rhythm — curiosity on the hook, confidence on the proof, trust on the permission beat, urgency on the CTA.

---

## Style Declaration

The motion intent document must declare the style profile at the top:

```markdown
**Style profile:** cinematic-presenter
```
or
```markdown
**Style profile:** editorial-authority
```

This declaration gates which defaults, presets, and budgets apply throughout the document.

---

## Creative Intent Summary — Required

Before writing any motion direction, produce a 6-field Creative Intent Summary (template in `CLAUDE.md` → "Creative Intent Summary" section) and wait for user confirmation.

**Trigger:** any new motion-intent document, or any revision that changes motion modes, beat categories, or the overall motion language (e.g. shifting from ambient-heavy to still-first, changing entry presets across a section).

The summary must name: the specific motion problem being solved (e.g. ambient overrun, stacked motion on proof beats), which motion patterns are validated and must not change, what specific mode or preset changes are being made and why, the main anti-pattern risk from `motion-grammar.md`, the relevant feedback entries (taste-rules as tie-breaks only), and what the still-mode percentage and ambient-mode beat count should be after the change.

Do not proceed to motion mode selection until the summary is confirmed.

---

## Motion Mode Selection

Before assigning entry presets or beat categories, assign exactly one **motion mode** to every beat. The motion mode governs what happens during the hold — which is where most motion fatigue originates.

Full definitions and selection algorithm: `.claude/rules/motion-grammar.md` → The Four Motion Modes.

| Mode | One-line definition | Default for |
|---|---|---|
| `still` | No camera motion during the hold | **Body default** — short beats, annotation beats, return beats, any beat after a punchy entry |
| `ambient` | Slow drift toward focal point (~1.0 → 1.015–1.02) | Long holds (>2.0s) with a named focal point and no other motion — opt-in only |
| `motivated` | Zoom tied to a specific narration target (pre-defined zoom coordinates) | Beats where narrator names a UI element or stat; coordinates must exist in Phase 4b-iii |
| `transition-led` | Motion lives in the entry transition; hold is still | Short beats (<2s); after high-energy edit points; when reel is ambient-heavy |

**Selection order:** short beat? → `still`/`transition-led`. Named narration target with coordinates? → `motivated`. Long hold with focal point, no competing motion? → `ambient`. Default: `still`.

**Hard rules:**
- Do not stack `zoom-in` entry preset + ambient drift hold on the same beat (Stacked Motion anti-pattern)
- Do not assign `ambient` to holds shorter than 2.0s (Drift Without Purpose anti-pattern)
- `motivated` requires pre-defined zoom coordinates from Phase 4b-iii — no improvised zoom targets at this phase
- Hook motion modes are set by hook-grammar.md archetypes and do not constrain body beat defaults

---

## The Four Beat Categories

Every beat belongs to exactly one category. Each has a defined motion principle.

### 1. Avatar beats
**Motion principle:** push-in, caption lock, eye-line priority

| Phase | Motion |
|---|---|
| Entry | Subtle scale settle (1.03-1.05 → 1.00 over 4-8 frames) |
| Hold | `still` by default — natural speech motion is sufficient. Assign `ambient` only if hold >2.5s and there is a specific focal point to drift toward (not generic drift). |
| Accent | Spoken emphasis word — no visual effects unless also a visual reveal |
| Exit | Hold last frame or soft opacity ease |

### 2. Demo beats
**Motion principle:** focus crop, pointer emphasis, panel framing — UI is *read* not just shown

| Phase | Motion |
|---|---|
| Entry | clipPath wipe from top OR fast scale (1.08 → 1.00 over 5 frames) |
| Hold | Assign `motivated` if zoom_moment coordinates pre-defined in Phase 4b-iii. Assign `ambient` only if hold >2.0s, no zoom_moment fires, and there is a clear focal point. Assign `still` if clip has cursor/typing motion — the clip handles hold. Default: `still`. |
| Accent | 2-frame scale pulse on container (1.0 → 1.02 → 1.0). One per beat max |
| Exit | Opacity 1 → 0 over 3-4 frames, or clipPath reverse |

### 3. Concept / proof beats (b-roll, support visuals)
**Motion principle:** micro-accent overlays, directional cut energy, timing intact

| Phase | Motion |
|---|---|
| Entry | Fast clipPath reveal or scale entrance |
| Hold | Clip's own motion handles this |
| Accent | Light leak or cut-point flash (uses TransitionSeries.Overlay) |
| Exit | Fade or hold into next beat |

### 4. Return beats (avatar re-entry after demo)
**Motion principle:** intentional re-entry — viewer should feel the shift back to the human

| Phase | Motion |
|---|---|
| Entry | Stronger scale settle (1.05 → 1.00) OR grade/background shift |
| Hold | Same as avatar beats |
| Accent | Return often has a payoff line — let words be the accent |
| Exit | Depends on what follows |

### Editorial-authority override

When style is `editorial-authority`, the categories still apply but motion rules change:
- No Ken Burns on any beat
- No ambient motion (breathe, drift)
- Holds are static — stillness is fine
- Motion budget: 1 hero + 0-1 support + 0-1 accent (tighter than cinematic)
- Hard cuts are the default transition (don't count toward variety)

---

## Preset Vocabulary

Motion intent must use these **exact preset names**. No free-form editorial language.

### Enter presets

| Preset | Visual | Typical use |
|---|---|---|
| `wipe-up` | Content reveals from bottom to top | Demo/broll center-full entries |
| `fade` | Opacity 0 → 1 | Gentle entries, b-roll payoffs |
| `zoom-in` | Scale 1.1 → 1.0 with slight push | Screenshots, proof moments |
| `scale-pop` | Spring scale 0.8 → 1.0 | Overlays, badges |
| `slide-up` | Translates up from below | Split-screen content |
| `smooth-push` | Gentle translate + scale | Subtle transitions |
| `punch` | Fast scale 1.2 → 1.0 | High-energy (hook, CTA) |
| `hard-cut` | Instant, no animation | Editorial-authority default |
| `scale-pop-overshoot` | Spring with overshoot | HeroTextCard (editorial) |
| `slide-stack` | 6-frame stagger | CardStack entries (editorial) |
| `flash-reset` | 2-3 frame white flash | Section dividers (editorial) |

### Exit presets

| Preset | Visual | Typical use |
|---|---|---|
| `fade` | Opacity 1 → 0 | Default exit for most entries |
| `scale-down` | Scale 1.0 → 0.9 + fade | Clean exit with depth |
| `slide-down` | Translates down | Split-screen exits |
| `wipe-down` | Content conceals top to bottom | Matching wipe-up entries |
| `hard-cut` | Instant | Editorial-authority default |

### Duration bounds

- `enterDur`: 3-10 frames (0.1-0.33s)
- `exitDur`: 2-4 frames (0.07-0.13s)

### Variety rule

- Max **2 consecutive entries** with the same enter preset
- A reel should use at most **3 transition types** for consistency
- For editorial-authority: hard-cut is the baseline and doesn't count toward variety

---

## Gap Ownership

Every speech pause between beats must be visually owned. No gap may be left undefined.

| Gap duration | Rule | Treatment |
|---|---|---|
| < 0.3s (< 9 frames) | Exiting beat holds through | No special treatment |
| 0.3-0.8s (9-24 frames) | Designed seam | Define: exiting beat fades, entering beat pre-enters, or gap is a background transition moment |
| > 0.8s (> 24 frames) | Breathing space | Must have intentional behavior: visual resolution, designed transition, energy reset, or anticipation build |

For each gap in the beat map, the motion intent must state:
- Which beat owns the gap (exiting or entering)
- What happens visually during the gap

---

## Background Seam Transitions

When the background changes (e.g. GradientMesh → Aurora, or Aurora → solid color):

- Use an **8-12 frame opacity crossfade** between outgoing and incoming backgrounds
- Do not hard-cut backgrounds — the viewer perceives a flash
- Time the crossfade to start at the last frame of the exiting beat
- If the seam coincides with a visual entry (e.g. demo wipe), the crossfade should complete before or during the wipe — not after

---

## Flash and Accent Budget

**cinematic-presenter:** Maximum **1 flash accent** per reel.
**editorial-authority:** Maximum **2 flash accents** for reels <35s, **3** for reels 35s+.

A flash accent is a 2-frame white flash or punch-in accent. It is a signature when used once. All other bridges should use opacity shifts, grade changes, or silence.

Reserve the flash for the single most important moment — typically the hook landing or CTA close.

---

## Motion Intent Per Beat — Required Format

For every beat, produce a row in this table:

```markdown
| Beat | Category | Motion Mode | Hero Motion | Support Motion | Accent | Enter Preset | enterDur | Exit Preset | exitDur | Gap Owner | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| beat-01a | demo | transition-led | wipe-up reveal | avatar settle below | — | wipe-up | 5 | fade | 3 | — | hook opening |
| beat-02 | avatar | still | scale settle 1.03→1.0 | caption lock | emphasis word "free" | fade | 4 | fade | 2 | beat-02 owns gap to beat-03 | setup — pivot line, face is anchor |
| beat-04 | demo | motivated | zoom→x:44,y:20 scale:1.9 | caption lock | zoom fires at 0.4s | wipe-up | 5 | fade | 3 | — | narrator names specific stat |
```

### Column definitions

| Column | What to fill |
|---|---|
| **Beat** | Beat ID from beat-map |
| **Category** | avatar / demo / concept-proof / return |
| **Motion Mode** | still / ambient / motivated / transition-led — from motion-grammar.md selection |
| **Hero Motion** | Primary visual event (wipe, scale entrance, focus crop, or zoom_moment detail) |
| **Support Motion** | Secondary element (avatar settle, divider fade, caption lock) |
| **Accent** | Micro-event on emphasis word (scale pulse, opacity flash, SFX hit) or "—" |
| **Enter Preset** | Exact preset name from vocabulary above |
| **enterDur** | Frames (3-10) |
| **Exit Preset** | Exact preset name from vocabulary above |
| **exitDur** | Frames (2-4) |
| **Gap Owner** | Which beat owns the gap after this beat, or "—" if no gap |
| **Notes** | Motion mode justification for ambient/motivated; background seam notes |

---

## Background Seam Table

Separately, list every background change:

```markdown
## Background Seams

| From Beat | To Beat | Outgoing BG | Incoming BG | Crossfade Duration | Notes |
|---|---|---|---|---|---|
| beat-02 | beat-03a | Aurora white | Aurora + Beams | 10 frames | Demo section starts |
| beat-08 | beat-09 | Aurora white | GradientMesh dark | 12 frames | CTA transition |
```

---

## Validation Checklist

Before presenting the motion intent, verify:

### Motion budget
- [ ] No beat has more than 3 motion elements (1 hero + 1 support + 1 accent)
- [ ] Flash accent count within budget for style and duration
- [ ] No decorative motion without editorial purpose

### Presets
- [ ] Every enter/exit preset is from the vocabulary (no invented names)
- [ ] enterDur within 3-10 frames for every entry
- [ ] exitDur within 2-4 frames for every entry
- [ ] No more than 2 consecutive entries with the same enter preset
- [ ] Reel uses at most 3 transition types

### Gaps
- [ ] Every gap between beats has an owner
- [ ] Gaps > 0.8s have defined visual behavior
- [ ] No undefined gaps

### Background seams
- [ ] Every background change has a crossfade defined (8-12 frames)
- [ ] No hard-cut backgrounds

### Beat categories
- [ ] Every beat has exactly one category (avatar, demo, concept-proof, return)
- [ ] Return beats identified after every demo/concept section

### Style compliance
- [ ] Style profile declared at top of document
- [ ] If editorial-authority: no Ken Burns, no ambient motion, hard-cut default
- [ ] If cinematic-presenter: ambient motion is opt-in — every `ambient` or `motivated` beat has a documented reason in the Notes column; no beats have stacked zoom-in entry + ambient hold

---

## Output Format

`output/motion-intent.md` is the single output file.

### Required structure

```markdown
# Motion Intent: [project-slug]

**Style profile:** [cinematic-presenter / editorial-authority]
**Duration:** [total]s ([frames] frames @ 30fps)
**Beats:** [count]
**Flash budget:** [used] / [max]
**Transition types:** [list of 2-3 types used]

---

## Beat-by-Beat Motion Direction

| Beat | Category | Hero Motion | Support Motion | Accent | Enter Preset | enterDur | Exit Preset | exitDur | Gap Owner | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

---

## Background Seams

| From Beat | To Beat | Outgoing BG | Incoming BG | Crossfade Duration | Notes |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... |

---

## Gap Ownership Summary

| Gap | Between | Duration | Owner | Visual Behavior |
|---|---|---|---|---|
| gap-1 | beat-02 → beat-03 | 0.4s | beat-02 | Hold last frame, fade over 6 frames |
| gap-2 | beat-05 → beat-06 | 1.2s | beat-06 | Breathing space: background seam crossfade + anticipation build |

---

## Validation

- Motion budget: [PASS/FAIL]
- Flash budget: [X] / [max] [PASS/FAIL]
- Preset vocabulary: [PASS/FAIL]
- Gap ownership: [PASS/FAIL]
- Transition variety: [X] types [PASS/FAIL]
- Background seams: [count] defined [PASS/FAIL]
- Stacked Motion check: no zoom-in entry + ambient hold on same beat [PASS/FAIL]
- Ambient motion justified: all ambient/motivated beats have documented reason [PASS/FAIL]

---

## Motion Review

Every entry must name a **specific beat ID** and a **specific reason tied to that beat's content**. Generic phrases ("felt right", "best fit", "to add energy") are not acceptable — if the reason could apply to any beat, rewrite it.

**Still beats:** [name 2–3 beats with still mode — beat ID + one specific reason tied to what is on screen or what the narrator says at that moment. Example: "beat-02: avatar pivot line — face is the whole message, drift competes with eye contact; beat-07: return beat after proof section — the scale settle IS the energy reset"]
**Motion doing real work:** [name 1–2 beats where the mode improves comprehension or proof clarity — beat ID + what specifically the motion directs attention to. Example: "beat-05: motivated zoom arrives at the memory-comparison bar at the exact moment narrator says '6x less memory' — viewer eye is already at the number"; "beat-09: transition-led wipe-up carries the demo's kinetic energy, hold settles so the UI is readable"]
**Motion reduced:** [name 1–2 beats where motion was downgraded from what old defaults would have produced — beat ID + what was removed and why it was wrong. Example: "beat-03: hold is only 1.1s — ambient drift at that duration looks unstable; assigned still"; "beat-06: removed ambient from proof screenshot — drift would shift the pricing row off-center while narrator reads the value aloud"]

If "motion doing real work" cannot be filled with specific beat IDs and specific narration references, the reel's motion needs review before user presentation.
```

---

## Relationship to Other Skills

**shot-list**
Provides the visual plan (what). This skill adds the motion direction (how).

**assemble-reel**
Uses this document as the motion blueprint for timeline construction.
Assembly must not begin without an approved motion intent.

**qa-reel**
Uses this document to verify the assembled reel matches the intended motion design.

**frontend-design**
Referenced when a motion treatment needs design refinement (spring config, easing choice).

This skill should make assembly mechanical — every motion decision is already made.

---

## Stop Condition

Stop after:
- `output/motion-intent.md` is produced with all sections
- validation checklist passes
- the document is presented for user review

Do not proceed to asset prep or assembly until the user reviews the motion intent.

Assembly without motion direction produces ad-hoc motion decisions that weaken the edit.
