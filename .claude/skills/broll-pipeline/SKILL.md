---
name: broll-pipeline
description: Generate, split, classify, match, and cut cinematic b-roll clips.
disable-model-invocation: true
---

# B-Roll Pipeline Skill

Use this skill when:
- the user wants cinematic b-roll for the reel
- a NotebookLM cinematic video needs to be generated from the source URL
- existing b-roll footage needs to be split, classified, and matched to beats
- the user says "b-roll", "cinematic", "NotebookLM video", or similar

This is **Phase 1b** — b-roll generation and classification.
It runs after script approval (Phase 1) and can run **in parallel with voice ingest (Phase 2)**.

**B-roll is optional.** Not every reel needs it. The system must ASK the user before generating b-roll. Never assume b-roll is wanted.

---

## B-Roll Decision Gate

Before doing any b-roll work, ask the user:

> "Do you want NotebookLM cinematic b-roll for this reel? It adds visual texture and can help explain concepts, but demos and proof screenshots come first. If yes, I'll generate a cinematic video from your source material and extract scenes."

If the user says no → skip this entire skill. Proceed to Phase 2.
If the user says yes → continue with the pipeline below.

---

## Source Options

B-roll can come from two sources:

### Option A: Generate via NotebookLM (preferred for new projects)

Uses the `notebooklm-py` library to generate a cinematic video from the source URL.

**Requirements:**
- `notebooklm-py` installed (`pip install notebooklm-py`)
- Google account logged in (`notebooklm login` — one-time browser auth)
- NotebookLM cinematic video feature is free — no paid subscription required

**The customization prompt** is the key creative input. It directs NotebookLM's cinematic engine like a director directing scenes — not listing features, but describing what the viewer should SEE and FEEL at each story moment.

The prompt is built from **both** `brief.md` (scope, audience, differentiator) AND `script.md` (the actual narrative arc). The script is the creative backbone. The brief provides the constraints.

#### The Director's Approach

NotebookLM's cinematic engine creates visuals. Give it **visual instructions**, not feature descriptions.

| Bad (feature list) | Good (directing) |
|---|---|
| "Show code export" | "Designs dissolve into streams of code — the mockup becomes the real thing" |
| "Show pricing" | "A counter rising to 350. Freedom. The credit card fading away unused" |
| "Show multi-screen generation" | "A single line of text is a seed — app screens bloom outward like pages of a book assembling themselves" |
| "Explain how it works" | "The compression feels like squeezing a library into a pocket — nothing lost, everything accessible" |

**Rules:**
- Describe what the viewer should **SEE**, not what the narrator should **SAY**
- Use **analogies** for abstract concepts ("like pages assembling themselves", "streams of code")
- Direct the **feeling** of each scene (weight, freedom, discovery, proof, urgency)
- Every scene must survive **vertical 9:16 crop** — compose for center-frame
- Match pacing to narration tempo — each scene should feel like 3-5 seconds, not 15

#### Building the prompt: step by step

**Step 1 — Read the inputs**

Read `script.md` for the narrative beats and their emotional arc.
Read `brief.md` for topic, audience, differentiator, scope boundaries, and style.

**Step 2 — Write the context block**

The opening paragraph tells NotebookLM what this video is for:

```
I'm creating a short-form vertical video about [TOPIC]. The narration is
already recorded. I need cinematic visuals that ACCOMPANY the following
script — not replace it. These visuals will be extracted as individual
scenes and used as b-roll footage in a [DURATION]s reel.
```

**Step 3 — Translate each script beat into a visual scene**

For each major beat in the script, write one paragraph that includes:

1. **What the narrator SAYS** — so NotebookLM knows the story moment
2. **What the viewer should SEE** — the visual metaphor, not a literal screenshot
3. **The FEELING** — emotional direction (weight, freedom, discovery, proof, urgency)
4. **An ANALOGY** — when the concept is abstract, give NotebookLM an image to work from

**Per-beat template:**
```
[BEAT NAME] — The narrator says "[key phrase from script]."
I need visuals that [VISUAL DIRECTION — what to show].
Think [ANALOGY — a reference image or metaphor the AI can work from].
The feeling should be [EMOTION — one or two words].
```

**Step 4 — Map beat intents to visual energy**

| Beat intent | Visual energy | Director's language |
|---|---|---|
| **hook** | Tension, contrast, disruption | "Show the weight of... then a clean break" |
| **setup** | Orientation, context, grounding | "Establish the world — show where we are" |
| **proof** | Revelation, payoff, clarity | "The result materialises — undeniable, specific" |
| **demo** | Action, process, transformation | "Watch it happen — input becomes output" |
| **mechanism** | Understanding, insight, "how" | "The inner workings — think [analogy]" |
| **trust** | Safety, control, reassurance | "Calm. Deliberate. The user is in charge" |
| **recap** | Momentum, collection, earned value | "A cascade of everything we just saw — fast, confident" |
| **CTA** | Resolution, invitation, confidence | "Clean. Resolved. Someone building something real" |

**Step 5 — Add style and production notes**

Close the prompt with visual constraints:

```
VISUAL STYLE NOTES:
- [Palette direction — clean/warm/dark/high-contrast, informed by project theme]
- [Composition — "every scene must survive vertical 9:16 crop, compose for center-frame"]
- [Contrast — "sharp difference between old way and new way" or "build from simple to complex"]
- [Pacing — "match the tempo of a [DURATION]s narration — each scene should feel like 3-5 seconds"]
- [What to avoid — "no cluttered dashboards, no generic stock footage energy, no wide panoramic shots that lose detail when cropped vertical"]
```

**Step 6 — Present for user review**

Present the complete prompt to the user before sending to NotebookLM. This is the creative control point — the user may adjust analogies, add references, or change the emotional direction.

#### Full prompt structure

```
[CONTEXT — 2-3 sentences: what this is for, narration exists, visuals are b-roll]

[SCENE 1: HOOK — narrator says "...", show [visual], think [analogy], feel [emotion]]

[SCENE 2: SETUP/REVEAL — narrator says "...", show [visual], think [analogy], feel [emotion]]

[SCENE 3: PROOF/DEMO — narrator says "...", show [visual], think [analogy], feel [emotion]]

[SCENE 4: MECHANISM — narrator says "...", show [visual], think [analogy], feel [emotion]]

[SCENE 5: TRUST/KICKER — narrator says "...", show [visual], think [analogy], feel [emotion]]

[SCENE 6: RECAP/CTA — narrator says "...", show [visual], feel [emotion]]

VISUAL STYLE NOTES:
- [palette]
- [composition — 9:16 crop survival]
- [contrast direction]
- [pacing — match narration tempo]
- [avoid — what NOT to show]
```

#### Example: Google TurboQuant

**From script beats + brief:**

```
I'm creating a short-form vertical video about Google's TurboQuant
breakthrough. The narration is already recorded. I need cinematic visuals
that ACCOMPANY the script — not replace it. These will be extracted as
individual scenes and used as b-roll in a 40-second reel.

OPENING — The narrator says "Google just mass produced a way to compress
AI." I need visuals that show the sheer scale of AI — think server farms
stretching to the horizon, rivers of data flowing through glowing
infrastructure. Massive. Overwhelming. Then: compression. Everything
tightens, condenses, becomes small and powerful. The feeling should be
awe turning into precision.

THE PROBLEM — The narrator explains that AI models keep growing and
memory is the bottleneck. Show the wall — literally. A massive structure
growing taller and taller until it hits a ceiling. Data piling up with
nowhere to go. Think of a library that's run out of shelves — books
stacking on the floor, spilling over. The feeling should be pressure.

THE BREAKTHROUGH — The narrator reveals TurboQuant: 6x less memory,
8x faster. Show the compression moment — that overflowing library
suddenly fits into a single elegant cabinet. Nothing lost. Every book
still accessible. Think of a zip file for intelligence — the same
knowledge in a fraction of the space. The feeling should be relief
and wonder.

THE SHOCKWAVE — The narrator says Micron's stock crashed 14%. Show
the ripple effect — the compression breakthrough sending shockwaves
outward. Think of a stone dropped in still water — except the ripples
reach trading floors, chip factories, data centres. Numbers falling.
The feeling should be consequence — this isn't theoretical.

THE TWIST — The narrator reveals Jevons' Paradox: more efficient AI
means MORE AI, not less. Show the paradox visually — the compressed
AI multiplying, spreading everywhere. Like making cars fuel-efficient
didn't reduce driving — it put a car in every driveway. The small,
efficient AI unit replicating across the world. The feeling should be
realisation — the satisfying "oh" moment.

THE CLOSE — Resolution. A world running on efficient AI. Clean,
powerful, inevitable. The feeling should be earned confidence.

VISUAL STYLE NOTES:
- Clean, modern palette with deep blues and whites (Google research aesthetic)
- Every scene must survive vertical 9:16 crop — compose for center-frame,
  avoid wide panoramic shots
- Sharp contrast between "before" (overwhelming, heavy) and "after"
  (compressed, elegant)
- Pace the transitions to match a 40-second narration — each visual scene
  should feel like 4-6 seconds of footage, not long slow establishes
- No generic stock footage energy — every visual should feel purposeful
  and connected to the specific story being told
- Avoid: cluttered dashboards, talking heads, text-heavy screens
```

**Present this to the user. They adjust, approve, then it goes to NotebookLM.**

#### Generation process

```python
# CLI approach
notebooklm generate cinematic-video "[customization prompt]" --source "[source URL]" --style classic --wait

# Or Python approach
from notebooklm import NotebookLMClient

async with await NotebookLMClient.from_storage() as client:
    notebook = await client.notebooks.create("[project-slug] B-Roll")
    await client.sources.add_url(notebook.id, "[source URL]", wait=True)
    task = await client.artifacts.generate_video(
        notebook.id,
        description="[customization prompt]",
        format="cinematic",
        style="classic"
    )
    await task.wait()
    await task.download("projects/[slug]/broll_scenes/source_cinematic.mp4")
```

**Important notes:**
- Cinematic generation takes 5-30+ minutes — run in background
- The library uses reverse-engineered APIs — may break if Google changes endpoints
- Use a dedicated Google account, not your primary one
- Download the video immediately after generation — don't rely on NotebookLM keeping it

#### Visual style options

| Style | When to use |
|---|---|
| `classic` | Default — clean, professional |
| `whiteboard` | Educational/explainer content |
| `anime` | Playful, younger audience |
| `retro` | Nostalgic feel |
| `watercolor` | Artistic, softer tone |
| `auto` | Let NotebookLM decide |

### Option B: User-provided footage

The user provides existing b-roll video (downloaded from NotebookLM manually, or from other sources).

Drop the file into: `projects/<slug>/broll_scenes/source_cinematic.mp4`

---

## Pipeline Overview

Once b-roll video exists (from Option A or B), the pipeline runs:

Step 0 — Generate cinematic b-roll (Option A) or receive user footage (Option B)
Step 1 — Split scenes
Step 2 — Classify scenes
Step 3 — Match scenes to beats (deferred to Phase 4b-i when beat map exists)
Step 4 — Review match plan
Step 5 — Cut approved scenes
Step 6 — Write markdown handoff docs

---

Step 1 — Split scenes

Break long b-roll footage into scene clips and thumbnails.

Step 2 — Classify scenes

Visually inspect thumbnails and label each scene for editorial use.

Step 3 — Match scenes to beats

Assign scenes only where b-roll adds value and does not weaken proof.

Step 4 — Review match plan

Do not cut automatically until matches are reviewed.

Step 5 — Cut approved scenes

Trim approved scenes to beat-friendly durations and output timeline-ready entries.

Step 6 — Write markdown handoff docs

Produce copy-paste-ready reports for later pipeline phases.

Scene Splitting
Command
python -m lib.capture.broll.split_scenes <video_path> <output_dir> [--threshold 27]
Outputs
scenes/*.mp4
thumbnails/*.jpg
scene_list.json
Threshold guidance
27 — default for most cinematic b-roll
20 — more sensitive, use for faster cut-heavy footage
35 — less sensitive, use for slower long takes
Splitting rules
prefer meaningful scene boundaries, not over-splitting every tiny motion shift
the goal is editorially usable scene units
avoid creating a large number of near-duplicate clips if a simpler split works
Scene Classification
Classification goal

Every scene should be described in a way that makes editorial matching easier.

Claude classification outputs

For each scene, write:

description
labels
mood
motion
suitable_for
visual_strength
proof_risk
cropping_notes
Required fields
description

1–2 sentences describing what is visibly happening.

labels

Choose from a controlled taxonomy, such as:

technology
person-talking
close-up
abstract
nature
text-overlay
product-ui
hands
workspace
aerial
motion-graphics
device-use
typing
team
city
desk-detail
mood

Examples:

calm
energetic
dramatic
professional
playful
futuristic
thoughtful
polished
motion

Examples:

static
slow-pan
fast-cut
zoom
tracking
handheld
parallax
animated
suitable_for

One or more:

hook
setup
support
transition
mechanism
recap
CTA
visual_strength

Rate:

high
medium
low

This answers: can this scene read quickly on mobile?

proof_risk

Rate:

low
medium
high

This answers: how risky would it be if this scene replaced real proof?

Examples:

abstract cinematic shot = high proof risk
workspace typing shot = medium proof risk
UI/product-specific scene = lower proof risk depending on beat
cropping_notes

Note whether the scene survives:

center crop
vertical crop
split-screen crop
punch-in
Classification Principle

Do not classify only by content.
Classify by editorial usefulness.

A beautiful shot is not automatically useful.
A shot can be visually strong but still poor for proof-heavy beats.

Matching Rules

This is the most important part.

The matcher must ask:
does this beat truly need b-roll?
is there already stronger proof coverage?
does the b-roll help comprehension or just add decoration?
will the scene improve pacing or dilute it?
does the scene fit the beat intent?
B-roll should usually help these beat types:
setup
support explanation
mechanism support
transition bridge
recap flashes
CTA background support
B-roll should usually NOT replace:
hook proof when a real result exists
file save/output proof
trust/permission UI
product-specific result reveal
any beat where the narration makes a specific visible claim
Beat Intent Matching Rules

Match b-roll based on beat intent, not generic semantic similarity.

Hook

Use only if:

no stronger real proof exists
the b-roll is visually striking
it can support curiosity in under 1 second

Prefer:

bold motion
high-readability visuals
clean crop survival

Avoid:

vague beauty footage if the hook promises a specific result
Setup

Good place for b-roll if it helps orient the viewer.

Prefer:

workspace
typing
device use
product context
light conceptual visuals
Proof

Usually avoid b-roll unless it is directly connected to the real proof.

Proof beats are better served by:

demo footage
screenshots
result states
saved outputs
Mechanism

Can use b-roll to support explanation if direct demos are too repetitive.

Prefer:

process-adjacent scenes
work context
hands / device / workflow visuals
Trust

Do not use cinematic b-roll instead of the real trust UI.

At most, use b-roll as a lead-in or lead-out around the actual trust moment.

Recap

Strong use case for b-roll when mixed with proof flashes.

Prefer:

fast readable scenes
varied visual texture
distinct images that do not compete with recap proof
CTA

Use as background support behind avatar if:

the visual reinforces the exact reel value
it does not distract from the ask
Match Quality Rules

For each proposed beat-to-scene match, check:

semantic relevance
mood alignment
pacing fit
duration fit
crop survivability
non-repetition
proof safety
Avoid:
reusing the same scene across adjacent beats
assigning b-roll to every beat just because footage exists
using weakly related cinematic shots for proof-heavy lines
overusing abstract footage in tool/demo reels
B-Roll Exclusion Rules

A beat should often get no b-roll match when:

the beat already has a strong demo
the beat already has a result-state screenshot
the beat is a trust moment
the beat is a save/output moment
the presenter alone is enough
the best edit is split-screen face + UI

Leaving a beat unmatched is often the correct decision.

Review Gate

After matches are written, stop for review.

Do not auto-approve cutting.

The review should check:

whether any proof beat was wrongly given b-roll
whether scene reuse is too high
whether the hook match is actually strong
whether recap support is varied enough
whether any match is only decorative

Human or editorial review should confirm the plan before cutting.

Cutting Approved Scenes
Command
python -m lib.capture.broll.cut_scenes <broll_dir> <project_dir>
Cut rules
trim to beat-friendly durations
remove original audio unless explicitly needed
ensure handles are sensible when possible
prepare filenames clearly
copy usable clips to remotion/public/ or project asset structure
create timeline-ready entry metadata
Output
broll_entries.json
Display Rules for B-Roll

B-roll display mode must support the beat’s role.

center-full

Use for:

cinematic visual resets
recap flashes
wide establishing shots
pure mood / texture moments
responsive

Use for:

hook support
mixed presenter + b-roll compositions
beats that still need presenter anchoring
split or background support

Use for:

CTA support
recap under avatar
explanation moments where b-roll is secondary
Important

Do not default every b-roll scene to full-screen.
Choose display mode based on editorial job.

Output Files
File	Location	Purpose
scene_list.json	<project>/broll_scenes/	scene inventory with metadata and classification
scenes/*.mp4	<project>/broll_scenes/scenes/	split scene clips
thumbnails/*.jpg	<project>/broll_scenes/thumbnails/	representative scene thumbnails
broll_matches.json	<project>/output/	beat match proposal for review
broll_entries.json	<project>/output/	approved timeline-ready b-roll entries
broll-report.md	<project>/output/	markdown summary of scene quality and match decisions
broll-review.md	<project>/output/	markdown review sheet for approvals and exclusions
Required Markdown Outputs

The b-roll pipeline must produce markdown docs that are easy to copy and paste.

Required

output/broll-report.md

Recommended

output/broll-review.md

These documents should help:

shot-list
assemble-reel
qa-reel
broll-report.md Required Structure
# B-Roll Report: [Project Slug]

**Source video:** [File path or name]  
**Scene count:** [Number]  
**Matching status:** [Draft / Needs Review / Approved]  
**Beat map available:** [Yes / No]

---

## Summary
[Short summary of whether the b-roll is strong, usable, repetitive, weak, etc.]

## Strongest Scenes
1. [Scene ID] — [Why it is strong]
2. [Scene ID] — [Why it is strong]
3. [Scene ID] — [Why it is strong]

## Weak or Risky Scenes
- [Scene ID] — [Why it is weak, repetitive, vague, or risky]
- [Scene ID] — [Why it should probably not be used for proof]

## Match Recommendations
- [Beat ID] → [Scene ID] — [Why this helps]
- [Beat ID] → [No match] — [Why proof or presenter is stronger]

## Hook Support
[Whether the b-roll contains a strong hook-support scene.]

## Recap / CTA Support
[Which scenes are best for recap flashes or CTA background support.]

## Proof Safety Notes
- [Which beats should not use b-roll]
- [Which scenes are too abstract for proof-heavy lines]

## Notes for Shot List
[What to carry forward into shot planning.]

## Notes for Assembly
[Display, timing, or transition guidance.]

## Notes for QA
[What later QA should watch for.]
broll-review.md Recommended Structure
# B-Roll Review: [Project Slug]

## Approved Matches
- [ ] beat-01 → scene-03
- [ ] beat-02 → no b-roll
- [ ] beat-03 → scene-07

## Rejected Matches
- [ ] beat-04 → scene-09 — too decorative
- [ ] beat-05 → scene-02 — demo proof is stronger

## Reuse Watchlist
- [ ] scene-03 appears too often
- [ ] scene-07 and scene-08 feel visually too similar

## Final Notes
[TBD]
Integration With Shot List

After review, approved b-roll should feed into shot-list.md.

Important rules
demos and proof visuals come first
b-roll fills support gaps
do not force b-roll into every beat
note explicit No b-roll decisions where useful

B-roll assignments should be visible in the shot list, not hidden.

Validation Checklist

Before finishing, verify:

Scene processing
 scenes were split successfully
 thumbnails exist
 scene_list.json exists
 scene IDs are stable and readable
Classification
 each scene has description, labels, mood, motion, and suitable_for
 editorial usefulness was considered
 risky scenes are flagged
Matching
 matches are based on beat intent
 no proof-critical beat is wrongly replaced with b-roll
 repetition is controlled
 no unnecessary match inflation
Output
 broll_matches.json exists
 markdown report exists
 review gate is respected
 downstream notes are clear
Important Rules
do not use b-roll as fake proof
do not let cinematic footage overpower real product proof
do not approve matches automatically
do not reuse the same scene excessively
do not treat all beats as needing visual fill
do not classify scenes only by literal objects; classify by editorial use
do not proceed to cut until the match plan is reviewed
Relationship to Other Skills
reel-script

Provides the beat logic and what the visuals need to support.

ingest-voice

Provides the real beat timing for final match and cut decisions.

capture-demo

Provides stronger direct proof footage that often takes priority over b-roll.

assemble-reel

Uses approved b-roll entries where they genuinely improve pacing or support.

qa-reel

Checks whether b-roll helped the reel or diluted proof.

This means b-roll should always remain in service of the reel, not the other way around.

Stop Condition

Stop after:

scenes are split and classified
matches are proposed
markdown review docs are written
approved scenes are cut only after review

Do not auto-approve or auto-assemble the b-roll into the final timeline.