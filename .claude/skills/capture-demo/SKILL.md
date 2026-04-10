---
name: capture-demo
description: Capture demo clips and supporting assets via the 4-stage fallback chain.
disable-model-invocation: true
---

# Capture Demo Skill

Use this skill when:
- a beat map exists
- the script is approved
- visuals must now be gathered
- the reel needs real proof assets, not generic screen coverage

This phase is not just about collecting footage.
It is about capturing **edit-ready proof**.

A good demo capture phase makes assembly faster and makes the reel more convincing.

---

## Primary Goal

Capture assets that make the reel feel:
- real
- outcome-led
- visually clear
- easy to edit
- retention-safe
- proof-dense

Every captured asset should help the editor answer at least one of these:
- what happened?
- where is the proof?
- what is the result?
- why should the viewer care?
- what moment needs emphasis?

---

## Global Rule References

This skill must follow these global rule files in addition to its local instructions:

- `.claude/rules/reel-workflow.md`
- `.claude/rules/demo-capture-strategy.md`
- `.claude/rules/visual-style.md`

### Rule precedence

When rules overlap, use this order:

1. **Workflow rules** — phase order and approval gates
2. **Demo capture strategy** — capture fallback chain and config requirements
3. **Visual style rules** — zoom coordinate handling, crop awareness, layout support
4. **This skill** — editorial capture choices inside those constraints

---

## Workflow Alignment

This skill runs in **Phase 4 — demo capture**.

Do not skip the workflow order:
- script must already be approved
- actual audio timing should exist or be close to final
- demos are captured before final shot-list approval
- b-roll may exist already, but demos come first
- shot list is built after demos are captured
- timeline assembly happens only after shot-list approval

### Important workflow rule

**Demos come first.**
B-roll fills gaps and scenes without dedicated demo coverage.

Do not capture demos casually and assume b-roll will save weak proof later.

---

## Responsibilities

- identify exactly what must be shown visually
- define capture plan for demos and supporting assets
- plan proof packets, not just long screen recordings
- capture edit-ready demo clips
- capture visible result states and outcome moments
- capture trust/permission moments where relevant
- capture alternates for hook, recap, and CTA support
- register demo clips and support assets
- connect assets to beat IDs and scene purpose
- validate that the story has enough proof to be assembled strongly

---

## Core Editorial Principle

Do not capture software passively.

Capture it in a way that supports:
- hook proof
- mechanism clarity
- visible outcomes
- save/output confirmation
- trust reassurance
- recap flashes
- avatar-led social editing

Assembly should not have to "invent" proof from weak source captures.

---

## Required Inputs

Before capture planning, review:

- `script.md`
- `audio/beat-map.json`
- `project.json`
- `brief.md` if available
- `source-research.md` if available
- `shot-list.md` if already drafted
- existing asset inventory if any

If the beat map and script disagree, use:
- the beat map for timing structure
- the approved script for spoken intent
- the approved brief/source research for proof priority

---

## Required Config Files

This skill should prepare and use:

- `lib/capture/demo-config.json`
- `screenshots/zoom-hints.json` when generated
- `assets/catalog.json`

### `demo-config.json`
This file defines each demo:
- `id`
- `beat_id`
- `prompt`
- `response`
- `target_asset`
- optional product/template metadata

Prepare `demo-config.json` **before any capture run**.

### `zoom-hints.json`
When produced by Stage 1 or Stage 3 capture, it should include:
- `id`
- `beat_id`
- `source`
- `zoom_moments`

Stage 1 and Stage 3 zoom hints can be used directly later.
Stage 2 manual screenshots require Claude review before zoom moments are finalized.

---

## Asset Types

Supported asset categories include:

- avatar video
- demo video
- screenshots
- still images
- logos
- charts
- UI crops
- support cards
- SFX references
- music references

Additional editorial capture types strongly encouraged:
- result-state screenshots
- save/output screenshots
- permission/trust screenshots
- recap flashes
- zoom target notes
- alternate hook crops
- alternate proof inserts

---

## Capture Philosophy

### Bad capture
- long generic screen recording
- no clear result moment
- no save/output shown
- no alternate angles or hold frames
- no trust prompt captured
- no note of where emphasis should happen

### Good capture
- short purposeful clips
- visible input → result progression
- result state held clearly
- save/output moment captured
- permission prompt captured if relevant
- screenshots taken for key frames
- zoom targets noted precisely
- alternates available for hook, recap, and CTA

---

## Proof Packet Capture

For each important demo beat, capture assets that support a proof packet.

### Preferred proof packet structure
1. **Input**
2. **Processing**
3. **Result**
4. **Save / output**
5. **Reaction support / recap support**

Not every beat needs all five, but long demo sections should not rely on a single continuous recording.

### Example
If the reel claims a tool creates an expense report:
- capture the file import or receipt drop
- capture the tool reading or processing
- capture the report being created
- capture the Excel/output file being saved
- capture a clean result frame for recap or freeze emphasis

---

## The 4-Stage Fallback Chain

Run the demo capture process with the assumption that live AI product sites may fail.

Never assume the live site will be accessible.
Always plan for fallback capture.

### Stage 0 — X/Twitter video capture (preferred when available)
Use when:
- the product team posted a demo video on their official X account
- a credible reviewer posted a clear screen recording on X
- the tweet shows real product UI in action (not a promo graphic)

Capture:
- real product footage at highest available bitrate
- auto re-encoded for Remotion (libx264, 30fps, -g 1, faststart, audio track)

Run:
```bash
node lib/capture/capture-x-video.js --url <tweet-url> --out <filename.mp4> --project <slug>
```

Or batch from `x-sources.json`:
```bash
node lib/capture/capture-x-video.js --list projects/<slug>/x-sources.json
```

Credentials: `AUTH_TOKEN` and `CT0` in `.env` (env-var driven, no storageState file).
If capture fails with auth errors, the session may have expired — grab fresh cookies from browser DevTools.

**Stage 0 videos are source footage.** They may still need:
- trimming to match beat duration
- speed adjustment (playbackRate)
- cropping if they contain browser chrome or personal data

Always inspect frames after capture for privacy and narrative match.

---

### Stage 1 — Real site via Playwright
Use when:
- the site is accessible
- the user is logged in
- automated interaction is feasible
- DOM bounding boxes can be extracted

Capture:
- prompt-entry state
- response/result state
- key moments for proof
- auto-calculated zoom coordinates

Skip Stage 1 if the site shows:
- login walls
- CAPTCHA / "verify you are human"
- unusual traffic / bot blocks
- access denied / 403
- long navigation timeout

### Stage 2 — Manual screenshots from user
Use when:
- the user already has clean screenshots
- the user recorded their own screen
- live automation is blocked but real product visuals are available

Requirements:
- screenshots must be clear and unobstructed
- no notifications or overlays hiding the UI
- no browser chrome or clutter that weakens readability
- manual screenshots need Claude review for zoom targeting

### Stage 2b — User-provided video recordings

When the user provides their own screen recordings (MP4 files from screen capture tools):

**Browser chrome check:**
- Inspect the first frame for browser tabs, address bar, bookmarks bar, extension icons
- If present, crop with FFmpeg: `-vf "crop=in_w:in_h-60:0:60"` (removes top 60px)
- If sidebar shows personal data (GPT names, project names, account info), crop the left side: `-vf "crop=in_w-280:in_h-60:280:60"`
- If both: combine crops in one filter

**Duration fitting:**
- Calculate: `playbackRate = source_video_duration / beat_duration`
- If playbackRate ≤ 2.5: set `playbackRate` in the timeline entry — acceptable speed-up
- If playbackRate > 2.5: video is too long for the beat — ask the user for a shorter recording or split across multiple beats
- Add `playbackRate` to the timeline entry so the video fits exactly within the beat

**Encoding for Remotion:**
- All user-provided videos must be re-encoded before placing in remotion/public/
- Required: `-r 30 -c:v libx264 -profile:v high -pix_fmt yuv420p -g 1 -movflags +faststart`
- Keep audio track even if video will be muted: `-c:a aac -b:a 128k`
- If source has no audio: add silent track with `-f lavfi -i anullsrc=r=44100:cl=mono -shortest`

**Post-processing validation:**
- Extract a frame from the cropped/encoded video and visually verify chrome is removed
- Verify playbackRate calculation: `source_duration / beat_duration`
- Verify the final frame shows the content the user wants visible (important for sped-up videos)

### Stage 3 — Mock HTML
Use when:
- the site is blocked
- no clean real capture is available
- unattended or scripted execution is preferred
- a clean, production-safe fallback is needed

### Important rule
**Stage 3 is the safe default.**
It is not a last resort.

When in doubt, go straight to Stage 3.

---

## Capture Stage Selection Rules

| Situation | Stage |
|---|---|
| Site is accessible and user is logged in | 1 |
| User recorded their own screen or provided screenshots | 2 |
| Site is blocked, unreliable, or unattended | 3 |
| Single clean demo needed quickly | 3 |
| CI / automated run | 3 |

### Operational rule
Always have Stage 3 ready before any capture run.

---

## Mock HTML Rules

### Premium Claude Mock (preferred for all Claude demos)

For Claude.ai demos, always use the premium mock template:
`lib/capture/templates/claude-premium-mock.html`

This template uses:
- Real Claude sparkle logo: `lib/capture/templates/claude-logo.png`
- Design system: Source Serif 4 headings, Inter body, `#FAF9F5` background, `#D97757` accent
- User name: "Mits" (edit in HTML to change)
- States via URL hash: `#homepage`, `#typing`, `#activate`
- Viewport: 540×960 (portrait 9:16) for Playwright `recordVideo`

**Always use this template over basic HTML mocks for Claude demos.** It produces premium, authentic-looking interfaces with no personal data leakage.

### General mock rules

The mock template should:
- match the product being shown
- accept injected prompt/response content
- preserve the UI structure needed for believable demo visuals
- keep stable element IDs for bounding-box-based zoom calculation

If the reel covers different tools:
- Claude → use `claude-premium-mock.html`
- ChatGPT → use `chatgpt-mock.html`
- Gemini, Perplexity, other AI products → create a matching template in `lib/capture/templates/`

### Mock rules
- keep the visual structure believable
- adapt brand colors, labels, and interface style to the product
- keep bounding-box target elements stable
- use neutral, illustrative demo content only

### Post-Capture Frame Inspection Gate

After every capture (Stage 1, 2, or 3), before accepting the clip:
1. Extract at least one frame from the clip at the timestamp that will appear in the reel
2. Visually inspect for: personal data, browser chrome, desktop wallpaper, cursor artifacts
3. Verify the clip content matches the narration it will accompany (no narrative mismatch)
4. If any issue is found: re-capture with a tighter crop, a mock, or a different clip section
5. Do not pass clips to assembly without this inspection

---

## Privacy and Safety Rule

Never record prompts or responses that could expose private user data.

Use:
- neutral examples
- educational examples
- safe illustrative prompts
- non-sensitive responses

Avoid:
- real client data
- personal notes
- private files
- identifying information
- sensitive work content

---

## Capture Planning by Beat Intent

Each beat should be mapped to one of these intents:

- `hook`
- `setup`
- `proof`
- `demo`
- `mechanism`
- `trust`
- `recap`
- `cta`

The capture plan should reflect that intent.

### Hook
Capture:
- early result reveal
- strongest visual proof
- alternate crops that can be used in the first second
- one clean "wow" frame

### Setup
Capture:
- product/interface context
- feature name visible if useful
- clean overview UI
- supportive screenshots for labels or framing

### Proof
Capture:
- the exact moment the claim becomes true
- a held state showing the result
- optional close crop of the proof area

### Demo / Mechanism
Capture:
- the action unfolding clearly
- clean cursor movement
- intentional pacing
- multiple stopping points for editing

### Trust
Capture:
- permission prompt
- confirmation dialog
- sensitive action pause
- any screen that proves the user stays in control

### Recap
Capture:
- short high-readability flashes
- result thumbnails
- save/output screens
- strong summary visuals

### CTA
Capture:
- final product/result state if helpful behind avatar
- quick callback visuals
- anything that reinforces the exact value promised

---

## Demo Capture Rules

### Every demo asset must have a purpose
Each demo clip should answer one of:
- this is the input
- this is the action
- this is the result
- this is the save/output
- this is the trust/control proof

Do not record long generic clips "just in case."

### Prefer short modular clips over one long recording
Capture modular sections that are easy to place on the timeline:
- 1.0–4.0s purpose-built clips
- plus longer masters when needed

### Record clean starts and clean ends
Allow extra handle room:
- start recording slightly before the action
- end slightly after the result lands

Recommended handle:
- at least 0.3–0.8s before
- at least 0.5–1.5s after key action

### Hold the result
When the proof appears, hold it clearly long enough to be usable.
Do not instantly move on.

### Capture the save/output state
If the narration claims a file, deck, report, or output was created, capture:
- the exact save action if possible
- the saved file name
- the final output visible in context

This is often the most important proof moment.

---

## Hook-Ready Capture

For reels with strong claims, capture hook-ready visuals intentionally.

### Required hook-ready assets
Try to capture at least one of:
- the final deck visible
- the saved report/file visible
- the generated result visible
- a dramatic before/after or input/output frame

### Hook asset rules
- should read quickly on mobile
- should still work in a crop
- should support split-screen or top-panel reveal
- should be recognizable in under 1 second

---

## Trust-Beat Capture

If the product asks permission, confirms actions, warns about sensitive steps, or gives the user control, this must be captured clearly.

### Required trust coverage when relevant
Capture:
- the permission prompt or decision point
- enough surrounding UI to understand context
- a tighter crop or screenshot for clarity
- the state before and after approval if possible

### Rules
- do not rely only on narration to explain trust
- do not skip this if it is one of the product's key advantages
- capture a version that can survive mobile crop and split-screen

---

## Result-State Screenshots

For every major proof beat, capture at least one clean screenshot of the finished state.

Examples:
- finished deck visible
- completed report visible
- saved Excel file visible
- structured plan visible
- permission box visible

These screenshots are valuable for:
- freeze emphasis
- hook reveal
- recap montage
- CTA background support
- quick proof flashes

---

## Recap-Ready Alternates

Capture 2–5 short assets that can be used later in recap or CTA montage.

Good recap-ready assets:
- result flashes
- saved file confirmation
- strongest slide thumbnail
- permission prompt
- major UI win state

These should be:
- visually distinct
- instantly readable
- short and self-contained

---

## Presenter-Aware Capture Support

The reel is avatar-led, so capture should support split-screen editing.

### Prefer captures that work well in:
- top-panel layouts
- split-screen crops
- mobile-safe center regions
- punch-in crops without losing meaning

### Avoid captures that require full-screen to understand
If the UI is too dense:
- capture a closer version
- add a second crop
- take a screenshot focused on the key area

---

## Cursor and Interaction Quality

When recording demos:
- move cursor deliberately
- avoid erratic pointer movement
- pause briefly before key actions
- avoid unnecessary wandering
- keep interaction path clear

A clean cursor path improves edit readability and zoom targeting.

---

## UI Cleanliness Rules

Before recording:
- close irrelevant windows
- remove distracting notifications
- hide sensitive information
- simplify desktop clutter
- use a readable zoom level
- increase browser/app scale if needed for mobile legibility

The source capture should already be clean enough for vertical delivery.

---

## Aspect Ratio and Framing Guidance

Capture with later mobile editing in mind.

### Prefer:
- high-resolution source capture
- enough padding for punch-ins
- centered core actions when possible
- layouts that survive vertical crop

### If capturing screenshots
Take:
- full screenshot
- optional cropped variant
- optional highlighted variant if needed later

---

## Zoom Annotation and Coordinate Rules

For every demo screenshot or video clip, note the key UI elements the narration may reference.

Record:
- **what** — element being discussed
- **x%** — horizontal position
- **y%** — vertical position
- **when** — seconds into the clip relative to clip start
- **why** — what editorial job the zoom serves

### Best zoom targets
- typed command
- uploaded file
- generated result
- saved file name
- permission prompt
- deck title/thumbnail
- confirmation state

### Rules
- do not guess coordinates loosely
- do not annotate empty space
- use a grid, ruler, or careful estimate if needed
- annotate the proof moment, not just the action moment

### Coordinate rule for manual screenshots
For demo images displayed with:
- `objectFit: contain`
- `objectPosition: top`

use the visual-style coordinate formula:

- `frame_x = image_x`
- `frame_y = image_y × 0.57`

Do not use raw image Y percentages for split-screen demo images or the zoom will drift into empty white space.

### Stage-specific zoom rule
- Stage 1 and Stage 3 zoom coordinates can be used directly later
- Stage 2 manual screenshots must be reviewed manually before final zoom moments are trusted

---

## SFX and Music Sourcing (required)

SFX and music are assets.
They must be sourced during this phase, not improvised during assembly.

### SFX

For each reel, identify moments that benefit from sound design:

- **emphasis hits** — key words, reveals, or graphic pops
- **demo transitions** — switching between tools, views, or feature sections
- **scene breaks** — layout changes or beat changes
- **proof moments** — result appears, file saves, output completes
- **trust moments** — permission/approval prompt appears
- **CTA moments** — recap flash, follow ask, final notify/chime

### SFX sources (in priority order)

1. **Shared SFX library** at `SFX/` (project root)
2. **Remotion hosted SFX** via `@remotion/sfx` at `https://remotion.media/`
3. **External royalty-free sources**

### For each planned SFX
- choose/source an audio file
- register it in `assets/catalog.json` with role `sfx`
- link it to beat IDs or scene purpose
- copy to `remotion/public/` if local
- verify that it is audible and non-silent

### Minimum SFX guidance
At least:
- 1 per scene change
- 1–2 proof sounds
- 1 emphasis sound
- 1 CTA support sound

A proof-heavy 30–40s reel often needs more than the bare minimum if multiple results land.

---

## Music

If the reel uses background music:
- source a royalty-free track that matches the reel's energy
- ensure it supports the voice rather than competing
- trim or loop intentionally to duration
- register in the catalog with role `music`
- note intended target volume, usually under narration

If the trust moment needs contrast, note that music may need to dip or simplify there.

---

## Asset Naming Rules

Keep naming unambiguous and editorially useful.

### Prefer names like:
- `demo-cowork-receipt-import.mp4`
- `demo-cowork-report-generated.mp4`
- `support-cowork-permission.png`
- `result-cowork-saved-excel.png`
- `hook-cowork-full-deck.png`

### Avoid names like:
- `screen1.mp4`
- `finalfinal.png`
- `clip-new.mov`

Names should reveal:
- product/topic
- moment
- purpose

---

## Asset Catalog Requirements

`assets/catalog.json` should include, where applicable:

- `id`
- `path`
- `type`
- `role`
- `beat_ids`
- `intent`
- `description`
- `editorial_purpose`
- `duration`
- `source`
- `zoom_notes`
- `sfx_notes`
- `usable_for_hook`
- `usable_for_recap`
- `usable_for_cta`

Every major asset should be traceable to story function, not just file type.

---

## Required Markdown Output

This skill must produce a markdown document that is easy to copy and paste downstream.

### Required file
`assets/capture-report.md`

This document should state:
- what was planned
- which stage was used for each demo
- what was captured successfully
- what zoom data is trusted
- what assets are still missing
- what later phases should know

### Recommended structure

```markdown
# Capture Report: [Project Slug]

## Summary
[Short summary of capture coverage and quality.]

## Demos Planned
- [Demo ID] — [Beat ID] — [Goal]

## Capture Method Used
- [Demo ID] — [Stage 1 / Stage 2 / Stage 3]

## Assets Captured
- [Asset file]
- [Asset file]

## Trusted Zoom Sources
- [Demo ID] — [Stage 1 / Stage 3 auto-calculated]
- [Demo ID] — [Stage 2 manual review needed]

## Missing or Weak Coverage
- [ ] [Specific missing output, trust moment, or recap asset]

## Notes for Shot List
- [Note]

## Notes for Assembly
- [Note]

Validation

Before marking assets ready, verify:

Asset completeness
each important beat has matching visual coverage
all major claims have visible proof assets
trust/control coverage exists where relevant
CTA or recap support assets exist
there is at least one hook-ready proof visual
Stage 3 fallback is ready even if Stage 1 succeeded
Technical
files open correctly
video plays
screenshots are readable
SFX are audible
music is valid
no empty or corrupted files
demo-config.json exists and is usable
Editorial
results are visible
save/output moments are captured
result states are held long enough
assets are usable in split-screen
recap-ready flashes exist
zoom notes target real UI elements
privacy-safe prompt/response content is used

If any of these are missing, list them explicitly before moving on.

Output Expectations

At the end of this phase:

asset folder structure is clear
assets/catalog.json is present with metadata
lib/capture/demo-config.json is prepared
screenshots/zoom-hints.json is present when generated
assets/capture-report.md is written
manual vs automated steps are documented
missing assets are listed explicitly
hook-ready assets are identified
proof moments are covered
trust assets are captured where relevant
recap/CTA support assets are available
project.json updated (status → assets_ready)
Stop Condition

Stop after:

capture planning is complete
assets are registered
missing assets are explicitly listed
proof coverage is validated
project.json is updated

Do not assemble the timeline yet.
