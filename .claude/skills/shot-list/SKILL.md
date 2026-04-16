---
name: shot-list
description: Build a beat-by-beat visual plan for a reel by orchestrating visual assignment, component mapping, asset fitness audit, and technical planning into a single approved shot list document.
---

# Shot List Skill

Use this skill when:
- beat-map.json exists with real narration timing
- demo capture is complete (or enough assets exist to plan visuals)
- the reel needs a visual plan before assembly
- the user is ready to decide what the viewer sees per beat

This is **Phase 4b** — the visual planning phase.
It runs after demo capture (Phase 4) and before motion intent (Phase 4c).

This phase is not just a table. It is the creative and technical blueprint that assembly will translate into a timeline. Every assembly decision traces back to a row in this document.

---

## Primary Goal

Produce a single `shot-list.md` that answers three questions for every beat:

1. **What does the viewer see?** (visual assignment — Phase 4b-i)
2. **Which component renders it, and does the asset match?** (component mapping + fitness — Phase 4b-ii)
3. **How does it render technically?** (backgrounds, SFX, transitions, zoom — Phase 4b-iii)

The shot list must be complete enough that assembly can begin without ad-hoc visual decisions.

---

## When to Trigger

Use this skill when:
- `audio/beat-map.json` exists with real timing
- `assets/catalog.json` has registered assets
- demo capture is complete or enough assets exist to assign visuals
- the project is ready for visual planning
- the user says "shot list", "visual plan", "what should each beat show", or similar

Do not use this skill for:
- writing the script (use `reel-script`)
- capturing demos (use `capture-demo`)
- building the timeline (use `assemble-reel`)
- writing motion direction (use `motion-intent`)
- doing QA (use `qa-reel`)

---

## Global Rule References

This skill must follow these global rule files in addition to its local instructions:

- `.claude/rules/reel-workflow.md`
- `.claude/rules/component-mapping.md`
- `.claude/rules/visual-style.md`
- `.claude/rules/style-profiles.md`
- `.claude/rules/timing-sync.md`
- `.claude/rules/template-grammar.md` (when style is `proof-escalation-editorial`)

### Rule precedence

When rules overlap, use this order:

1. **Workflow rules** — phase order, approval gates, screenshot minimums
2. **Component mapping rules** — narration classification, component selection tables, fitness scoring
3. **Visual style rules** — display modes, zoom formulas, background mapping, motion budget
4. **Style profiles** — cinematic-presenter vs editorial-authority defaults
5. **This skill** — editorial visual decisions inside those constraints

---

## Workflow Alignment

This skill runs in **Phase 4b — shot list assembly**.

Before starting, these must be true:
- script is approved
- real narration audio exists and beat-map.json has actual timing
- demo capture is complete (or enough assets exist)
- if b-roll was classified in Phase 1b, `broll_scenes/scene_list.json` exists

After this skill completes:
- motion intent (Phase 4c) uses the approved shot list to write motion direction
- asset prep (Phase 4d) uses technical planning to encode and validate assets
- assembly (Phase 5) uses the approved shot list as its blueprint

### Important workflow rule

**This skill has TWO approval gates:**

1. **After Phase 4b-i** (visual assignment) — STOP for user approval before component mapping
2. **After Phase 4b-ii** (component mapping + asset fitness) — auto-block if ANY MISMATCH or MISSING scores exist. Resolve before continuing to technical planning.

Phase 4b-iii (technical planning) completes the document. The full shot-list.md is then ready for motion intent.

---

## Required Inputs

Before starting, gather:

- `audio/beat-map.json` — beat IDs, timing, phrases, visual intent
- `assets/catalog.json` — registered assets with metadata
- `project.json` — slug, style, theme colors
- `audio/captions.json` — caption chunks (for timing reference)
- `brief.md` — hook direction, proof promise
- `script.md` — spoken content, beat structure

If b-roll exists:
- `broll_scenes/scene_list.json` — classified scenes with content tags, mood, visual_strength, proof_risk

If demo capture produced zoom hints:
- `screenshots/zoom-hints.json` — auto-calculated zoom coordinates

---

## Responsibilities

- assign a visual to every beat (no gaps)
- classify every beat's narration
- select the correct Remotion component per beat and style
- audit every visual asset for fitness against its narration
- block on mismatches and missing assets
- define backgrounds, SFX placement, transitions, and zoom coordinates
- validate flow (rhythm, layout variety, component variety, screenshot variety)
- produce a complete shot-list.md with all three sub-phase sections

---

## Core Editorial Principle

**The viewer must always see what the narrator is talking about.**

If the narrator says "6x less memory" — the viewer must see a chart or number showing that.
If the narrator says "Claude" — Claude's logo or UI must be visible.
If the narrator says "look at this" — something specific must be on screen.

Generic b-roll is not proof. Avatar-only is not proof. The visual must match the claim.

---

## Phase 4b-i — Visual Assignment

This is the creative/editorial pass. For every beat, decide what the viewer sees.

### Step 1 — Inventory available assets

Read `assets/catalog.json` and list all assets by type:
- demo videos
- demo screenshots
- b-roll clips
- support images (logos, charts, icons)
- SFX files

If `broll_scenes/scene_list.json` exists, cross-reference the classification labels.

### Step 2 — Assign visuals per beat

For every beat in `audio/beat-map.json`, assign:

| Column | What to fill |
|---|---|
| **Beat** | Beat ID from beat-map |
| **Time** | Start–End from beat-map |
| **Narration** | Exact spoken words |
| **Visual Type** | avatar, demo video, demo image, b-roll, image montage, support, animated mock |
| **Asset** | Specific filename from catalog, or "avatar" if face-only |
| **Notes** | Editorial reasoning, crop notes, or b-roll scene reference |

**Additional columns when style is `proof-escalation-editorial`:**

| **template_id** | Template from `training/derived/template-registry.json` (e.g. `proof-overlay-split`, `card-carousel`, `demo-fullscreen`). Read the registry and select based on the beat's proof class and avatar need. See `.claude/rules/template-grammar.md`. |
| **proof_class** | One of: `existence`, `breadth`, `process`, `output`, `integration`, `authority`, `cta`, or null. Declares this beat's role in the proof escalation arc. |

### Visual type definitions

| Type | When to use |
|---|---|
| **avatar** | Direct address, setup, CTA — face is the focus |
| **demo video** | Product walkthrough, recorded interaction, typing demo |
| **demo image** | Static screenshot with zoom moments |
| **b-roll** | Cinematic footage that illustrates a concept (not proof) |
| **image montage** | Multiple related images shown in sequence (StackedImageReveal) |
| **support** | Logo, chart, icon, or headline card |
| **animated mock** | TypingInput, IconOrbit, SourceProofCard, or other animated component |

### Assignment rules

- **Demos come first.** Assign demo coverage to proof, mechanism, and trust beats before anything else.
- **B-roll fills gaps.** Assign b-roll to concept, bridge, and texture beats — never to proof beats that need specific evidence.
- **Avatar is the default for direct address.** If the narrator is speaking TO the viewer with no visual claim, use avatar.
- **No beat may be empty.** Every beat must have a visual assignment.
- **Match b-roll by editorial intent**, not visual similarity. A "trust beat" narration matches a "proof_risk: low" scene, not a pretty landscape.

### Screenshot variety rules (mandatory)

- No single static screenshot may hold on screen for more than **2 seconds** without a zoom change or cut to a different image.
- Any proof section longer than **2.5 seconds** must use **multiple different screenshots** with hard cuts between them.
- Extract **at least 2-3 different frames** showing different states, angles, or features of the product.
- Each screenshot in a sequence must show a **visibly different** part of the product.

### Screenshot count minimums

| Reel duration | Minimum unique screenshots |
|---|---|
| 25-35s | 6 |
| 35-45s | 8 |
| 45-55s | 10 |

After completing the table, count total unique screenshots. If below minimum, go back and extract more.

### Style-specific tagging

If `project.json` has `"style": "editorial-authority"`:
- Tag every beat with both **broad intent** (hook, setup, proof, demo, etc.) AND **editorial sub-class** (hook-card, talking-head, proof-screenshot, proof-chart, contradiction-card, etc.)
- Mark proof beats as `proof_protected: true`

### Output

Produce the **Phase 4b-i — Visual Assignment** section of `shot-list.md`.

### STOP GATE

**Present the visual assignment table to the user for approval.**

Do not proceed to component mapping until the user approves the visual assignment.

If the user requests changes, update the table and re-present.

---

## Phase 4b-ii — Component Mapping + Asset Fitness

This phase runs after the user approves visual assignment. It answers two questions per beat:
1. Which Remotion component renders this beat?
2. Does the assigned asset actually match what the narrator says?

### Step 1 — Classify the narration

Read each beat's text from `audio/beat-map.json`. Classify using the narration classification system from `.claude/rules/component-mapping.md`:

| Classification | Pattern |
|---|---|
| **Emotional keyword** | Single word or short phrase that IS the emphasis |
| **Staccato claim** | 2-5 word declarative with a period feel |
| **Name reveal** | Introduces a product, feature, or concept name |
| **Number + proof** | Stat with visual evidence available |
| **Explanation over visual** | Describing what a visual shows |
| **Direct address** | Talking to viewer, no visual needed |
| **Trust/credibility** | Citing authority or source |
| **Contradiction/negation** | Striking through or negating something |
| **List item** | Numbered or bulleted item in a series |
| **Comparison** | Side-by-side or A vs B |
| **CTA** | Call to action |
| **Section transition** | Gap between major sections |
| **Hook opening** | First 2-5 seconds, must stop the scroll |
| **Reframe/montage** | Summary or multi-source validation |
| **Tool intro/chapter** | New section introducing a tool by name + logo |

A single beat can combine classifications.

### Step 2 — Registry lookup (run before reasoning)

**Before** applying the component selection tables from `component-mapping.md`, run the beat registry lookup for the current style and classification. This gives you the deterministic answer — components, avatar layout, transition, background, SFX, and mandatory extras — without per-beat reasoning.

```bash
# Single beat lookup
python -m lib.beat_registry lookup <style> <classification>

# Examples:
python -m lib.beat_registry lookup editorial-authority number_proof_with_asset
python -m lib.beat_registry lookup cinematic-presenter hook_opening
```

Registry classification key mapping (snake_case):
`emotional_keyword`, `staccato_claim`, `name_reveal`, `number_proof_with_asset`,
`number_proof_no_asset`, `explanation_over_visual`, `direct_address`,
`trust_credibility`, `contradiction_negation`, `list_item`, `comparison`,
`cta`, `section_transition`, `hook_opening`, `reframe_montage`, `tool_intro_chapter`

If the registry returns a result, use it directly. Only fall back to manual table reasoning if the classification is absent from the registry (add a new entry after completing the reel).

Also check for matching beat fragments:

```bash
python -m lib.beat_fragments find <style> <classification>
```

If a fragment exists, adapt it instead of constructing the timeline entry from scratch.


### Step 2 — Select the component

Use the style-specific component selection tables from `.claude/rules/component-mapping.md`.

Read `project.json` for the `style` field:
- If `cinematic-presenter` or missing: use the cinematic-presenter table
- If `editorial-authority`: use the editorial-authority table

For each beat, determine:
- **Component** — which Remotion component (e.g. FramedImage, HeroTextCard, OverlayKeyword)
- **Avatar layout** — full-screen, split-screen, or hidden
- **Content zone** — where content renders (top 40%, center, full frame)

### Design quality check

After selecting a component, verify it will render **distinctively**. Consult the `frontend-design` skill if:
- The component's default styling feels generic or flat
- Typography choices need refinement for mobile viewing
- Color choices need alignment with the project's theme (`theme_primary`, `theme_secondary` from `project.json`)
- A new component needs to be built

### Theme integration

Read `project.json` for `theme`, `theme_primary`, `theme_secondary`. These values should drive:
- HeroTextCard background colors
- OverlayKeyword colors
- NumberPopup / BadgePopup accent colors
- Aurora blob tints (cinematic-presenter style)
- Background solid colors (editorial-authority style)

### Step 3 — Audit asset fitness (automated visual inspection)

For every beat that uses a visual asset, **read the asset file** using the Read tool and visually verify it matches the narration. Do not score fitness based on filenames alone — actually look at the image/frame.

Fill the fitness matrix.

| Column | What it checks |
|---|---|
| **Beat** | Beat ID |
| **Narration** | Exact words the narrator says |
| **What viewer must SEE** | What visual would make these words land (specific, not vague) |
| **Available assets** | All potentially matching assets from catalog |
| **Best match** | Which asset fits best |
| **Fitness score** | MATCH / PARTIAL / MISMATCH / MISSING |
| **Issue** | What's wrong if not MATCH |
| **Action** | What to capture/crop/replace if needed |

### Fitness scoring

| Score | Meaning | Action |
|---|---|---|
| **MATCH** | Asset shows exactly what the narrator describes | Use as-is |
| **PARTIAL** | Related but wrong section, angle, or detail | Document crop/zoom/annotate plan |
| **MISMATCH** | Asset exists but doesn't match narration | Find different asset or re-capture |
| **MISSING** | No asset exists for what the narrator describes | Capture: screenshot, mock, or animated component |

### Fitness rules

- Every **MISMATCH** or **MISSING** is a **blocker**. Do not continue to technical planning.
- Every **PARTIAL** needs a documented fix plan (crop coordinates, zoom target, or overlay to compensate).
- Narrator says a **tool name** → the tool's logo or UI must be visible.
- Narrator says a **number/stat** → the proof visual must show that number or a supporting chart.
- Narrator says **"look at this"** or implies pointing → a specific visual must be on screen.
- Narrator describes an **action** → the visual must show the action or its result, not a static concept.

### Step 4 — Validate flow

Read the component sequence and check:

**Rhythm check:**
- No more than **3 consecutive beats** use the same component type
- No more than **3 consecutive beats** have the avatar in the same layout
- No dense section runs longer than **8 seconds** without a face return
- No sparse section runs longer than **5 seconds** without visual support

**Layout flow check:**
- Good: split → full → split → hidden → split → full → hidden → full
- Bad: full → full → full → full → hidden → hidden → hidden → full

**Component variety minimums:**

| Reel duration | Minimum unique components |
|---|---|
| 25-30s | 4 |
| 35-50s | 6 |
| 50s+ | 8 |

**Screenshot variety check:**
- No single screenshot holds > 2 seconds without zoom change or hard cut
- Total unique screenshots meet the minimums from Phase 4b-i

**Template validation (proof-escalation-editorial only):**

When style is `proof-escalation-editorial`, additionally check:
- Every beat has a `template_id` from `training/derived/template-registry.json`
- Template class sequence (ANCHOR/PROOF) respects oscillation bounds from `training/derived/rhythm-bounds.json`
- `proof_class` values progress forward through the proof arc (existence → breadth → process → output → authority → cta) — no backward jumps
- Caption behavior is consistent with template: `demo-fullscreen` and `card-carousel` must have caption suppressed

### Output

Produce the **Phase 4b-ii — Component Mapping** and **Asset Fitness Audit** and **Flow Validation** sections of `shot-list.md`.

### BLOCKER GATE

If ANY asset has a **MISMATCH** or **MISSING** fitness score:
- List every blocker with the specific action needed to resolve it
- Do not proceed to Phase 4b-iii
- Present blockers to the user

When all blockers are resolved, continue to technical planning.

---

## Phase 4b-iii — Technical Planning

With component mapping and asset fitness approved, define how each beat renders.

### Step 1 — Assign backgrounds

Read the style and assign backgrounds per beat:

**cinematic-presenter:**
| Scene type | Background |
|---|---|
| Hook split-screen | AuroraBackground (white) |
| Split-screen demo | AuroraBackground |
| Center-full demo/broll | AuroraBackground + BackgroundBeams (#FAFAFA) |
| Avatar full-screen CTA | GradientMesh (dark) |

**editorial-authority:**
| Scene type | Background |
|---|---|
| Hook | Solid color (e.g. #2D1B69 purple) |
| Proof screenshot | Solid white (#FFFFFF) |
| Contradiction/negation | Solid gray |
| Tool section | Product brand color |
| CTA | Solid dark |

**proof-escalation-editorial:**
Backgrounds are template-driven. Read `training/derived/template-registry.json` → `background` field.
| Template background value | Actual background |
|---|---|
| `warm-beige` | Solid #F0EBE0 |
| `dark` | Solid #1A1A1A |
| `natural` | No background component — real environment from avatar video |
| `content-driven` | Match the UI's own background (dark UI = dark, light UI = light) |

### Step 2 — Plan SFX placement

For every beat, determine if SFX is needed. Use the SFX placement guide from `assemble-reel`:

| Moment | SFX type | When to place |
|---|---|---|
| Layout/scene change | whoosh or sweep | At the transition point |
| Key word emphasis | pop or hit | At the spoken word |
| Proof reveal | chime, click, soft impact | When proof appears |
| File save/output | confirmation tick | When save completes |
| CTA | riser, notify | When CTA action word appears |
| NumberPopup | subtle click | At each number reveal |

**SFX count targets:**
- 30-40s reel: minimum 6 entries
- 40-55s reel: minimum 8 entries

### Step 3 — Define zoom coordinates (automated vision analysis)

**Every static screenshot lasting > 1.5 seconds** must have at least one `zoom_moment` with:
- `x`, `y` — percentage coordinates targeting a specific UI element
- `scale` — zoom level (1.3-2.5 typical)
- `holdFor` — seconds to hold

**This step is automated.** Do not ask the user to identify zoom targets. Analyze each screenshot directly.

**Coordinate formula for split-screen images** (objectFit: contain, objectPosition: top):
```
frame_x = image_x
frame_y = image_y * 0.57
```

**Automated process — for every screenshot beat:**

1. **Read the image file** using the Read tool. Claude Code's Read tool opens images and makes them visible for analysis. This is not optional — every screenshot must be visually inspected.

2. **Cross-reference the narration** for that beat from `audio/beat-map.json`. Know what the narrator is saying while this screenshot is on screen.

3. **Identify the focal element** — the specific UI element the narrator is describing:
   - If narrator says "type your prompt here" → find the input/text field
   - If narrator says "the result appears" → find the output/response area
   - If narrator says "click export" → find the export button
   - If narrator says a product name → find the logo or product heading
   - If narrator says a number/stat → find where that number appears on screen

4. **Estimate the element's position** as a percentage of the full image dimensions:
   - `image_x` — horizontal center of the element (0% = left edge, 100% = right edge)
   - `image_y` — vertical center of the element (0% = top edge, 100% = bottom edge)

5. **Apply the letterbox formula** for split-screen display:
   ```
   frame_x = image_x
   frame_y = image_y * 0.57
   ```
   For center-full display, use raw coordinates (no formula needed).

6. **Set scale** based on element size:
   - Small element (button, toggle, single field): `scale: 2.0-2.5`
   - Medium element (text block, card, panel): `scale: 1.5-2.0`
   - Large element (full section, table): `scale: 1.3-1.5`

7. **Set holdFor** to match how long the narrator discusses this element (typically 1.5-3.0s).

8. **If multiple focal points exist** in one beat (narrator moves from input to output):
   - Define multiple zoom_moments with different `at` values
   - Minimum 1.5s gap between moments
   - Only the last moment zooms back out

**Pre-calculated zoom hints:** If `screenshots/zoom-hints.json` exists from capture (Stage 1 or Stage 3), use those values directly — they were auto-calculated from DOM bounding boxes and are more precise than vision estimates.

**If no focal element is identifiable:** The screenshot is wrong for this beat. Flag it and find a better one. Do not write a zoom coordinate that points at nothing.

**Accuracy note:** Vision-estimated coordinates are approximate (~5-10% margin). They are good enough for technical planning. Assembly and QA will verify during preview.

### Step 4 — Confirm playback rates

For every demo video:
- Calculate: `playbackRate = source_video_duration / beat_duration`
- If playbackRate <= 2.5: acceptable, note the value
- If playbackRate > 2.5: video is too long — flag for re-capture or beat splitting

### Step 5 — Note transition preferences

For each beat, note the preferred transition type if it differs from the style default:
- cinematic-presenter default: `fade` enter, `fade` exit
- editorial-authority default: `hard-cut` enter, `hard-cut` exit

Only note transitions that DIFFER from the default.

### Output

Produce the **Phase 4b-iii — Technical Planning** section of `shot-list.md`.

---

## Output Format

`shot-list.md` is the single output file. It contains all three sub-phase sections.

### Required structure

```markdown
# Shot List: [project-slug]

**Style:** [cinematic-presenter / editorial-authority]
**Duration:** [total duration]s ([total frames] frames @ 30fps)
**Beats:** [count]

---

## Phase 4b-i — Visual Assignment

| Beat | Time | Narration | Visual Type | Asset | Notes |
|---|---|---|---|---|---|
| beat-01a | 0.00-1.50 | "If you're paying..." | b-roll + avatar | hook-bg.mp4 | split-screen hook |
| beat-01b | 1.50-3.20 | "there's a free tool..." | avatar | — | direct address |

**Screenshot count:** [X] unique screenshots (minimum [Y] for [Z]s reel) [PASS/FAIL]

---

## Phase 4b-ii — Component Mapping

| Beat | Classification | Component | Avatar Layout | Content Zone | Notes |
|---|---|---|---|---|---|
| beat-01a | hook opening | ScrollingIconGrid + OverlayKeyword | split-screen | top 45% | grid + text |
| beat-01b | direct address | AvatarVideo | full-screen | — | setup energy |

## Asset Fitness Audit

| Beat | Narration | Must SEE | Best Match | Fitness | Issue | Action |
|---|---|---|---|---|---|---|
| beat-03a | "6x less memory" | memory chart | longbench.png | PARTIAL | Shows full benchmark | Crop to memory bars |
| beat-04 | "peer-reviewed" | research page | — | MISSING | No asset | Capture research screenshot |

**Blockers:** [count] MISMATCH + MISSING
[List each blocker with required action]

## Flow Validation

- Component sequence: [list]
- Avatar layout sequence: [list]
- Unique components: [count] [PASS/FAIL vs minimum]
- Max same-component streak: [count] [PASS/FAIL]
- Max same-layout streak: [count] [PASS/FAIL]
- Longest dense run without face: [seconds] [PASS/FAIL]
- Longest sparse run without visual: [seconds] [PASS/FAIL]

---

## Phase 4b-iii — Technical Planning

| Beat | Background | SFX | Transition Override | PlaybackRate | Zoom Coordinates |
|---|---|---|---|---|---|
| beat-01a | Solid #2D1B69 / ScrollingIconGrid | impact @ 0.00 | scale-pop-overshoot | — | — |
| beat-03a | White #FFFFFF | pop @ 9.16 | — | — | at:0.3 x:60 y:34 scale:1.5 holdFor:1.8 |
| beat-05 | White #FFFFFF | — | — | 1.8x | — |

**SFX count:** [X] entries (minimum [Y] for [Z]s reel) [PASS/FAIL]
**Zoom coverage:** [X] of [Y] screenshot beats have zoom coordinates [PASS/FAIL]
```

---

## Validation Checklist

Before presenting the completed shot list, verify:

### Visual assignment (4b-i)
- [ ] Every beat has a visual assignment — no gaps
- [ ] Demos assigned to proof/mechanism/trust beats first
- [ ] B-roll fills gaps, not proof beats
- [ ] No static screenshot holds > 2s without zoom or cut
- [ ] Unique screenshot count meets minimum for reel duration
- [ ] Style-specific sub-classes tagged (editorial-authority only)

### Component mapping (4b-ii)
- [ ] Every beat has a narration classification
- [ ] Every beat has a named Remotion component
- [ ] Every beat has an avatar layout (full-screen, split-screen, or hidden)
- [ ] Component selection matches the style-specific table
- [ ] Asset fitness audit complete for every visual beat
- [ ] Zero MISMATCH or MISSING scores
- [ ] All PARTIAL scores have documented fix plans
- [ ] Component variety meets minimum for reel duration
- [ ] No same-component streak > 3
- [ ] No same-layout streak > 3

### Technical planning (4b-iii)
- [ ] Every beat has an assigned background
- [ ] SFX count meets minimum for reel duration
- [ ] Every screenshot beat > 1.5s has zoom coordinates
- [ ] Zoom coordinates use the contain+top formula (not raw image percentages)
- [ ] PlaybackRate calculated for every demo video
- [ ] No playbackRate > 2.5 without user approval

---

## Relationship to Other Skills

**ingest-voice**
Provides `audio/beat-map.json` — the timing backbone this skill reads.

**capture-demo**
Provides the demo assets and `assets/catalog.json` this skill assigns to beats.

**broll-pipeline**
Provides `broll_scenes/scene_list.json` classification data for b-roll matching.

**theme-factory**
Provides `theme_primary`, `theme_secondary` in `project.json` for component color decisions.

**frontend-design**
Referenced during component selection when a component needs design quality attention.

**motion-intent**
Uses the approved shot list to write beat-by-beat motion direction.

**assemble-reel**
Uses the approved shot list as the blueprint for `output/timeline.json`.

**qa-reel**
Uses the shot list to verify the assembled reel matches the approved visual plan.

This skill should make motion-intent and assembly straightforward — not require them to make visual decisions.

---

## Stop Condition

### After Phase 4b-i:
Stop and present the visual assignment table for user approval.
Do not proceed to component mapping until approved.

### After Phase 4b-ii:
Stop if ANY MISMATCH or MISSING fitness scores exist.
Present blockers to the user with specific actions needed.
Do not proceed to technical planning until all blockers are resolved.

### After Phase 4b-iii:
**STOP for user approval.**
Present the complete technical planning section for review.
Zoom coordinates, SFX placements, and background assignments are expensive to fix after assembly.
Do not proceed to motion intent until the user approves the technical plan.

The shot list is the visual contract. Assembly builds from it, not around it.
