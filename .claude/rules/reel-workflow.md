---
description: Enforces the audio-first reel production workflow
globs: ["projects/**", "templates/**"]
---

# Reel Workflow Rules

## Gate Enforcement

Every skill must check `gates_passed` in `project.json` before starting work. See `.claude/rules/gate-enforcement.md` for the full gate check procedure, the 11 gate IDs, and the skill-to-gate mapping.

**Short version:** Read `project.json` → check required gates are in `gates_passed` array → check required files exist on disk → if any check fails, report the failure and stop.

This is not optional. A skill that skips gate checks may produce output that downstream skills cannot use.

## Workflow Order

The required order for every project is:

0. **source-brief** — if the user provides a URL, run this first
   `node lib/capture/source-brief.js --url <url> --project <slug>`
   Produces: source-research.md, brief.md, downloaded assets
   Claude reads the output and proposes brief direction — user approves before continuing
0b. **theme selection** (mandatory) — run `theme-factory` before scripting
   Every project must have a theme. Run `theme-factory` to select or create the theme.
   Record `theme`, `theme_primary`, `theme_secondary` in `project.json`.
   The theme informs: Aurora blob colors, accent tones, overlay colors, HeroTextCard
   background colors, badge colors, and background mesh palettes during assembly.
   If the reel covers a specific product (Claude, Google, ChatGPT, Gemini, etc.),
   use that product's pre-set theme. If no specific product: use "Tech Neutral" theme.
   **Do not proceed to reel-script until theme fields are populated in project.json.**
   See `.claude/skills/theme-factory/SKILL.md` for pre-set themes and custom creation.
1. **reel-script** — write the ElevenLabs-ready voiceover script
   Reads approved brief.md, selects hook + style + engagement trigger, writes script.md
   Stop condition: script approved before any audio is generated
1b. **b-roll** (optional) — run `broll-pipeline` skill if user wants cinematic b-roll
   **ASK the user first** — b-roll is not required for every reel. Do not assume.
   If yes: generate cinematic video via `notebooklm-py` from source URL (or use user-provided footage).
   The customization prompt is auto-generated from `brief.md` — present it for review before sending.
   Pipeline: NotebookLM generate → split scenes → Claude classify thumbnails by content tags.
   **Classify only** at this stage — do not match to beats yet (beat map doesn't exist).
   **Match + cut** deferred to Phase 4b-i when beat map and shot priorities are known.
   ↓ **GATE: script approved before audio generation**
2. **voice ingest** — HeyGen avatar video or raw audio extraction
2b. **script reconciliation** — run the `script-reconcile` skill
   Compare the approved script text against the Whisper transcript word-by-word.
   Produces: `audio/reconciliation.md`
   Flag: changed words, dropped phrases, altered tool names, changed CTA wording.
   **The transcript wins** — all downstream references (captions, beat text, overlays)
   must match what was ACTUALLY spoken, not what was written.
   If critical content was dropped or changed, flag for user decision: accept or re-record.
3. **beat map** — `beat-map.json` from actual audio with reconciled transcript
3b. **caption polish** — run the `caption-polish` skill
   Captions are not just transcription. This step ensures:
   - correct product/tool spelling (ChatGPT not "chat GPT", Claude not "claud")
   - chunk length control (max 8 words, max 2.0s per chunk)
   - emphasis word tagging
   - readable line breaks at phrase boundaries
   - platform-safe timing (0.6–1.2s preferred)
   Produces: `audio/captions.json` (polished version replaces auto-generated)
3c. **demo config** — exact capture spec for each demo beat
   For each beat that needs a demo, define:
   - `beat_id` and `target_duration` (from beat map)
   - `ui_state` — what page/screen/state must be visible
   - `visible_text` — what prompt/text should appear on screen
   - `interaction_type` — typing, clicking, toggling, scrolling, result display
   - `capture_method` — Stage 1 (live), Stage 2/2b (user recording), Stage 3 (mock), or animated component
   - `playbackRate` — pre-calculated: source_duration / beat_duration (if video)
   Produces: `lib/capture/demo-config.json`
   This tells the user or capture script exactly what to record.
4. **demo capture** — demo screenshots/videos, support visuals, SFX
   Follows the demo-config spec. Inventories existing assets first (`ls assets/`).
4b-i. **visual assignment** — run the `shot-list` skill (Phase 4b-i)
   **Precondition:** If b-roll was classified in Phase 1b, read `broll_scenes/scene_list.json`
   before starting visual assignment. Use the classification labels, mood, visual_strength,
   and proof_risk to inform which scenes match which beats.
   
   Map every beat to its visual. This is the creative/editorial decision:
   - Visual type: avatar, demo video, demo image, b-roll, image montage, support, animated mock
   - Asset: specific filename
   - B-roll matching: cross-reference `broll_scenes/scene_list.json` classification data.
     Match by editorial purpose (e.g. "trust beat" narration + "proof_risk: low" scene).
     Do not assign b-roll by visual similarity alone — match by editorial intent.
   - Demos come first, b-roll fills gaps
   - For each avatar-only beat: would a b-roll insert improve comprehension?
   
   **Screenshot variety rule (mandatory):**
   - No single static screenshot may hold on screen for more than **2 seconds** without either a zoom change or a cut to a different screenshot.
   - Any proof section longer than **2.5 seconds** must use **multiple different screenshots** with hard cuts between them — not one image with a vague zoom.
   - When extracting screenshots from a source video, extract **at least 2-3 different frames** showing different states, angles, or features of the product. One frame per proof section is not enough.
   - Each screenshot in a sequence should show a **visibly different** part of the product (different page, different feature, different design) to prove breadth, not just one static view.
   - Count total screenshots assigned across the reel. A 30-40s reel should have **at minimum 6-8 distinct screenshots**, not 3-4.
   
   **Style activation:** If `editorial-authority`, tag every beat with both broad intent AND editorial sub-class (see `styles/editorial-authority.md` beat sub-classes). Mark proof beats as `proof_protected: true`.
   
   Produces: visual assignment section of `shot-list.md`
   **STOP for user approval** — this is the key visual approval gate.
4b-ii. **component mapping + asset fitness** — which component, does the asset match?
   See `.claude/rules/component-mapping.md` for the full decision guide.
   For every beat:
   1. **Classify the narration** — read the beat text, classify as: emotional keyword,
      staccato claim, name reveal, number+proof, explanation, direct address, trust,
      contradiction, list item, comparison, CTA, hook, reframe, chapter intro
   2. **Select the Remotion component** — use the style-specific component table
      from component-mapping.md to pick the right component for the classification
   3. **Map avatar layout** — full-screen, split-screen, or hidden for each beat
   4. **Audit asset fitness** — for every beat with a visual asset:
      - Does the asset show what the narrator says at that moment? (MATCH/PARTIAL/MISMATCH/MISSING)
      - Is the asset cropped correctly for the content zone?
      - Are there privacy issues?
      - Flag ALL mismatches and missing assets — these are **blockers**
   5. **Validate flow** — read the component sequence, check rhythm, layout variety,
      component variety, dense/sparse alternation
   Produces: component mapping table + asset fitness matrix + flow validation in `shot-list.md`
   **STOP if any MISMATCH or MISSING** — resolve capture gaps before continuing.
4b-iii. **technical planning** — how each beat renders
   With component mapping and asset fitness approved, define the rendering decisions:
   - **Background assignments** per beat (solid colors for editorial, Aurora/Beams for cinematic)
   - **SFX placement** (mandatory checklist — see SFX rules in assemble-reel skill)
   - **Overlay timing** and props (from component mapping)
   - **PlaybackRate** confirmation for sped-up videos
   - **Zoom coordinates** for every static screenshot (mandatory — see below)
   
   **Zoom coordinate rule (mandatory for all static screenshots):**
   - Every screenshot that appears on screen for more than **1.5 seconds** must have at least one `zoom_moment` with specific `x`, `y`, `scale`, and `holdFor` values.
   - Coordinates must target a **specific UI element** the narrator is describing (button, text field, result, chart) — not a vague "center of the image."
   - Open the screenshot, identify the focal element, estimate its position as image percentage, then apply the letterbox formula if split-screen (see `visual-style.md`).
   - Write the zoom coordinates into the technical planning table — do not defer to assembly or QA.
   - If a screenshot has no identifiable focal point worth zooming into, the screenshot is wrong — find a better one.
   
   Produces: technical planning section of `shot-list.md`
   **STOP for user approval** — technical planning (zoom coords, SFX plan, backgrounds)
   must be reviewed before motion intent begins. Incorrect zoom coordinates or
   missing SFX placements are expensive to fix after assembly.
4c. **motion intent** — run the `motion-intent` skill
   Required between shot-list approval and timeline assembly.
   Every beat must answer five questions:
   1. Purpose — what is this beat's editorial job?
   2. Visual change — what shifts on screen and what doesn't?
   3. Motion hierarchy — hero / support / accent (max 3 elements)
   4. Landing — what happens on the spoken emphasis word?
   5. Handoff — how does this beat give way to the next?
   Must also define: gap ownership, background seam behavior, beat category.
   **Must include preset mapping** — translate editorial language to Remotion values:
   ```
   Entry: "reveal upward"  → transition_preset.enter: "wipe-up", enterDur: 5
   Exit: "fade out"         → transition_preset.exit: "fade", exitDur: 4
   ```
   Allowed enter presets: punch, slide-up, slide-left, zoom-in, scale-pop, fade, wipe-up, smooth-push
   Allowed exit presets: punch-out, slide-down, scale-down, fade, wipe-down
   **Style activation:** If `editorial-authority`, declare `style_profile: editorial-authority` at the top of the motion intent document. Use editorial-authority preset names and implementation mappings (see `styles/editorial-authority.md`).
   
   Produces: `output/motion-intent.md`
   **STOP for user review** — no assembly without motion direction for every beat.
4d. **asset prep** — run the `asset-prep` skill (can run **in parallel** with Phase 4c)
   Process every raw asset before assembly:
   - Crop browser chrome from screen recordings (`-vf "crop=in_w:in_h-60:0:60"`)
   - Check sidebars for personal data — crop if needed
   - Re-encode all videos for Remotion (see Encoding Requirements below)
   - Calculate and confirm playbackRate for each video vs beat duration
   - Copy all processed assets to `remotion/public/`
   - **Validate every asset:**
     - readable (ffprobe succeeds)
     - correct duration (matches or exceeds target beat)
     - correct orientation (portrait or landscape as expected)
     - not corrupted (can decode first frame)
     - has audio track (even if silent)
     - named consistently (no spaces in filenames if possible)
   - Extract one frame from each processed asset and visually verify
   Produces: clean assets in `remotion/public/`, validation log
   ↓ **GATE: all assets validated before assembly**
5. **timeline assembly** — build `output/timeline.json` from approved shot list + motion intent + prepared assets
5b. **quick preview** — sanity-check structural correctness before full QA
   Open Remotion studio. Scrub to 5 key frames:
   - Hook (frame 0–15)
   - First demo (first center-full entry)
   - Mid-point (halfway through reel)
   - Reframe/recap beat
   - CTA (last 3 seconds)
   Check: does it render? Avatar visible where expected? Demos showing? Audio playing?
   Captions rendering? No layer overlap?
   If basic rendering fails → fix before full QA.
   If basic rendering works → proceed to Phase 6.
6. **QA** — full editorial + technical + performance QA
7. **render** — final export

**QA always before render.** Never export until all QA gates pass.
Run `python -m lib.qa.cli projects/<slug>` and resolve all blockers before
running `npx remotion render`.

Do not skip steps unless the project already contains validated artifacts.

### Remotion public folder cleanup

Before starting assembly on a new project, clean stale project-specific assets from `remotion/public/`:
- Remove: `source.wav`, `avatar*.mp4`, `timeline.json`, `demo-*.mp4`, `demo-*.png`, `broll-*.mp4`, and project-specific support images from the previous project
- Keep: shared SFX files (`.mp3`), `claude-logo.png`, and other shared assets
- Then copy the new project's assets fresh

**Why:** `remotion/public/` accumulates assets from every project. Old `source.wav` files cause audio/lip sync mismatch when a new avatar is loaded. Old `timeline.json` causes stale beat structures. Clean before every new project.

### Remotion Video Encoding Requirements

All video files placed in `remotion/public/` must meet these encoding requirements before preview or render. Non-compliant videos will cause `HTMLVideoElement.errorHandler` failures in Remotion studio.

**Required encoding command:**
```
ffmpeg -i input.mp4 -r 30 -c:v libx264 -profile:v high -pix_fmt yuv420p -g 1 -movflags +faststart -c:a aac -b:a 128k output.mp4
```

**Rules:**
- **Codec:** libx264, profile high, pix_fmt yuv420p — maximum browser compatibility
- **Keyframes:** `-g 1` — every frame is a keyframe. Remotion seeks frame-by-frame; long keyframe intervals cause jerky playback
- **Faststart:** `-movflags +faststart` — moves moov atom to file start for instant browser playback
- **FPS:** 30 — must match project fps. Source videos at 25fps must be converted
- **Audio track:** Always keep an audio track (`-c:a aac`). Remotion's OffthreadVideo may throw errors on videos with no audio stream, even when `muted` is set
- **If source has no audio:** Add silent track: `-f lavfi -i anullsrc=r=44100:cl=mono -shortest`

**When to encode:** During Phase 4d (Asset Prep) — not during assembly or QA.

**Validation:** Every asset must pass these checks before assembly:
```bash
ffprobe -v quiet -show_entries stream=codec_name,r_frame_rate,pix_fmt -of compact <file>
# Expected: codec_name=h264, r_frame_rate=30/1, pix_fmt=yuv420p
```

### ReelComposition.tsx Update

ReelComposition.tsx contains project-specific code and must be updated for each new project. During Phase 5 (assembly), update:
- timing constants (TOTAL, seam times, beams ranges)
- HookIntroScene props (avatar and panel source files)
- centerFullRanges computation (match timeline lanes)
- render layer order (demo before broll so broll wipes on top)
- composition header comments (beat structure, avatar file, duration)

Do not carry over previous project's hardcoded values.

**Phase 0 rule**: if the user says "here's a URL" at any point before a brief exists,
treat it as a source-brief trigger. Run the script, read source-research.md, produce
brief.md, and wait for approval before continuing to reel-script.

## Phase Gate Rules

At the end of each phase:
- summarize what was created
- summarize what was checked
- list blocking issues
- list manual inputs still required
- stop before moving forward

**Critical approval gates (11 gates):**
- Phase 0: brief direction must be approved before scripting
- Phase 0b: theme must be set in project.json before scripting (mandatory — no default skip)
- Phase 1: script must be approved before audio generation or b-roll classification
- Phase 2b: script reconciliation must flag any critical changes before beat mapping
- Phase 4b-i: visual assignment must be approved before component mapping
- Phase 4b-ii: component mapping + asset fitness must pass before technical planning
- Phase 4b-iii: technical planning must be approved before motion intent (zoom coords, SFX, backgrounds)
- Phase 4c: motion intent must be reviewed before assembly
- Phase 4d: all assets must be validated before assembly begins
- Phase 5b: quick preview must pass before full QA
- Phase 6: QA must pass before render

## Shot List (Phase 4b)

The shot list is produced in two passes:

### Phase 4b-i — Visual Assignment

The creative/editorial pass. Produce a markdown table in `shot-list.md`:

| Beat | Time | Narration | Visual Type | Asset |
|---|---|---|---|---|
| beat-01 | 0.0–2.5 | "Did you know..." | b-roll | broll_scene_03.mp4 |
| beat-02 | 2.5–5.1 | "Hidden codes..." | avatar | — |

**Visual types:** avatar, demo video, demo image, b-roll, image montage, support, animated mock

**Rules:**
- Every beat must have a visual assignment — no gaps
- Demos come first; b-roll fills beats without dedicated demo coverage
- If a beat has no demo or b-roll, assign avatar or support visual
- **No static screenshot may hold for more than 2 seconds** — beats longer than 2.5s must be split into sub-beats with different screenshots
- **Minimum screenshot count:** 6-8 distinct screenshots for a 30-40s reel, 8-12 for a 40-55s reel
- When sourcing screenshots, extract **multiple different frames** showing different product states, pages, or features — one frame per proof section is never enough
- After completing the table, count total unique screenshots. If below minimum, go back and extract more.
- **STOP for user approval** before proceeding to component mapping

### Phase 4b-ii — Component Mapping + Asset Fitness

See `.claude/rules/component-mapping.md` for the full decision guide.

**Component mapping table:**

| Beat | Narration Classification | Component | Avatar Layout | Content Zone | Notes |
|---|---|---|---|---|---|
| beat-01 | hook opening | ScrollingIconGrid + OverlayKeyword | split-screen | top 45% | grid with text |
| beat-02 | direct address | AvatarVideo | full-screen | — | setup |

**Asset fitness matrix:**

| Beat | Narration | Must SEE | Best Match | Fitness | Action |
|---|---|---|---|---|---|
| beat-04 | "compresses data" | compression visual | paper-findings.png | MATCH | — |
| beat-05a | "6x less memory" | memory reduction | longbench.png | PARTIAL | Crop to memory bars |

**Flow validation checklist:**
- [ ] Component variety ≥ 6 for 35s+ reel
- [ ] No same-component streak > 3
- [ ] No same-layout streak > 3
- [ ] Dense sections < 8s without face return
- [ ] Sparse sections < 5s without visual support
- [ ] No single static screenshot holds > 2s without zoom or cut
- [ ] Total unique screenshots ≥ 6 for 30-40s reel
- [ ] Every screenshot beat > 1.5s has zoom coordinates defined

**STOP if any MISMATCH or MISSING** — resolve before continuing.

### Phase 4b-iii — Technical Planning

The rendering/implementation pass. Extend the shot list table:

| Beat | Background | SFX | Transition | PlaybackRate | Zoom Coordinates |
|---|---|---|---|---|---|
| beat-01 | Solid #2D1B69 / ScrollingIconGrid | impact @ 0.00 | scale-pop-overshoot | — | — |
| beat-03a | White #FFFFFF | pop @ 9.16 | hard-cut | — | at:0.3 x:60 y:40 scale:1.5 holdFor:1.8 |

**Zoom coordinate requirement:** Every static screenshot lasting >1.5s must have zoom coordinates targeting a specific UI element. No empty zoom column allowed for screenshot beats.

**Avatar layout mapping:**

| Display context | Avatar layout |
|---|---|
| Image/screenshot in top 40-45% | `split-screen` |
| Center-full video or b-roll | No avatar entry (hidden) |
| Full-frame card (HeroTextCard) | No avatar entry (hidden) |
| Text overlay on face (OverlayKeyword) | `full-screen` |
| Avatar-only | `full-screen` |

## Motion Preset Vocabulary

Motion intent must use these exact preset names — no free-form editorial language that requires translation during assembly.

### Allowed enter presets
| Preset | Visual | Typical use |
|---|---|---|
| `wipe-up` | Content reveals from bottom to top | Demo/b-roll center-full entries |
| `fade` | Opacity 0 → 1 | Gentle entries, b-roll payoffs |
| `zoom-in` | Scale 1.1 → 1.0 with slight push | Screenshots, proof moments |
| `scale-pop` | Spring scale 0.8 → 1.0 | Overlays, badges |
| `slide-up` | Translates up from below | Split-screen content |
| `smooth-push` | Gentle translate + scale | Subtle transitions |
| `punch` | Fast scale 1.2 → 1.0 | High-energy moments (hook, CTA) |

### Allowed exit presets
| Preset | Visual | Typical use |
|---|---|---|
| `fade` | Opacity 1 → 0 | Default exit for most entries |
| `scale-down` | Scale 1.0 → 0.9 + fade | Clean exit with depth |
| `slide-down` | Translates down | Split-screen exits |
| `wipe-down` | Content conceals top to bottom | Matching wipe-up entries |

### Duration bounds
- `enterDur`: 3–10 frames (0.1–0.33s)
- `exitDur`: 2–4 frames (0.07–0.13s)

### Variety rule
- Max 2 consecutive entries with the same enter preset
- Max 3 transition types per reel for consistency

## Project Creation Rules

Every new project must start with:
- a single clear topic
- a target duration
- a defined audience
- a clear hook
- one primary CTA

## Content Scope Rules

A short reel should usually communicate:
- one main idea
- up to three support points
- one clear takeaway

If the draft tries to explain too much, reduce scope before generating timeline or assets.

## Asset Rules

Every asset must have one of these roles:
- beat support
- visual proof
- demo step
- CTA support
- branding support
- cinematic b-roll (scene filler to break up talking-head sections)

No unused or unexplained asset should remain in the active project.

## Timeline Rules

Timeline assembly must be based on:
- approved visual assignment (Phase 4b-i)
- approved component mapping + asset fitness (Phase 4b-ii)
- approved technical planning (Phase 4b-iii)
- actual audio timing from beat map
- motion intent with preset mappings (Phase 4c)
- validated and prepared assets (Phase 4d)

Never create timeline entries that refer to missing assets or undefined beats.
Never begin timeline assembly without approved shot list and prepared assets.
