---
name: asset-prep
description: Crop, encode, validate, and copy assets to remotion/public/ for rendering.
disable-model-invocation: true
---

# Asset Prep Skill

Use this skill when:
- demo capture is complete
- shot list is approved (all three phases)
- raw assets need processing before they can be used in Remotion
- the user says "prep assets", "encode videos", "clean up assets", or similar

This is **Phase 4d** — asset preparation.
It runs after the shot list is approved (Phase 4b) and can run **in parallel with motion intent (Phase 4c)**.

This phase exists because raw assets — screen recordings, manual screenshots, b-roll clips — are almost never render-ready. Browser chrome, wrong frame rates, missing audio tracks, personal data in sidebars, and incorrect keyframe intervals all cause Remotion to fail silently or produce bad output. Every one of these problems has happened in past projects.

---

## Primary Goal

Transform every raw asset into a Remotion-ready file that:
- passes `ffprobe` validation
- has correct encoding (libx264, yuv420p, 30fps, -g 1, faststart)
- has personal data and browser chrome removed
- has a calculated playback rate for beat fitting
- has been visually verified with at least one extracted frame
- lives in `remotion/public/` ready for composition

---

## When to Trigger

Use this skill when:
- demo capture (Phase 4) has produced raw assets
- shot list (Phase 4b) is approved and references specific asset files
- assets need encoding, cropping, or validation before assembly
- QA previously flagged encoding issues

Do not use this skill for:
- capturing demos (use `capture-demo`)
- deciding what the viewer sees (use `shot-list`)
- building the timeline (use `assemble-reel`)

---

## Global Rule References

This skill must follow:
- `.claude/rules/reel-workflow.md` — encoding requirements, cleanup rules
- `.claude/rules/demo-capture-strategy.md` — Stage 2b user recording handling
- `.claude/rules/qa-gates.md` — video encoding checks

### Rule precedence

1. **Workflow rules** — encoding spec, keyframe interval, audio track requirements
2. **QA gates** — encoding validation criteria
3. **This skill** — processing decisions inside those constraints

---

## Workflow Alignment

This skill runs in **Phase 4d — asset preparation**.

Before starting:
- Demo capture (Phase 4) has produced raw assets
- Shot list (Phase 4b) is approved — we know which assets are needed
- `assets/catalog.json` lists all raw assets

After this skill completes:
- `remotion/public/` contains all processed assets
- Assembly (Phase 5) can begin without encoding concerns
- No video will cause `HTMLVideoElement.errorHandler` failures in Remotion

### Parallelization

**This phase can run in parallel with Phase 4c (motion intent).**

Motion intent is editorial (deciding how things move). Asset prep is technical (encoding files). They are independent. Both depend on the approved shot list (Phase 4b-iii), and both must complete before assembly (Phase 5).

---

## Required Inputs

- `assets/catalog.json` — registered assets with metadata
- `shot-list.md` — approved, to know which assets are referenced
- `audio/beat-map.json` — beat timing for playback rate calculation
- Raw asset files in `assets/` or user-provided locations

---

## Responsibilities

- clean `remotion/public/` of stale project-specific assets
- crop browser chrome from screen recordings
- crop sidebar personal data
- re-encode all videos to Remotion spec
- add silent audio tracks to videos without audio
- convert non-30fps videos to 30fps
- calculate playback rates for sped-up videos
- copy all processed assets to `remotion/public/`
- validate every asset with ffprobe
- extract one frame per asset for visual verification
- produce a validation report

---

## Step 1 — Clean remotion/public/

Before copying new assets, remove stale project-specific files from `remotion/public/`:

**Remove:**
- `source.wav` (previous project's audio)
- `avatar*.mp4` (previous project's avatar)
- `timeline.json` (previous project's timeline)
- `demo-*.mp4`, `demo-*.png` (previous project's demos)
- `broll-*.mp4` (previous project's b-roll)
- Project-specific support images

**Keep:**
- Shared SFX files (`.mp3` in SFX/)
- `claude-logo.png` and other shared assets
- Any assets explicitly referenced by the current project

**Why:** `remotion/public/` accumulates assets from every project. Old `source.wav` causes audio/lip sync mismatch. Old `timeline.json` causes stale beat structures.

---

## Step 2 — Crop browser chrome

For screen recordings (user-provided MP4s):

**Check for browser chrome:**
- Inspect the first frame for: browser tabs, address bar, bookmarks bar, extension icons, Windows taskbar
- If present, crop with FFmpeg:

```bash
# Remove top 60px (browser chrome)
ffmpeg -i input.mp4 -vf "crop=in_w:in_h-60:0:60" ...

# Remove top 60px + left sidebar (280px for personal data)
ffmpeg -i input.mp4 -vf "crop=in_w-280:in_h-60:280:60" ...
```

**Check for personal data:**
- Inspect sidebar for: GPT conversation names, project names, account names, email addresses
- If present, crop the left side
- If both chrome and sidebar: combine crops in one filter

---

## Step 3 — Re-encode all videos

Every video placed in `remotion/public/` must meet this encoding spec:

```bash
ffmpeg -i input.mp4 \
  -r 30 \
  -c:v libx264 -profile:v high -pix_fmt yuv420p \
  -g 1 \
  -movflags +faststart \
  -c:a aac -b:a 128k \
  output.mp4
```

**Required parameters:**

| Parameter | Value | Why |
|---|---|---|
| `-r 30` | 30fps | Must match project fps |
| `-c:v libx264` | H.264 codec | Maximum browser compatibility |
| `-profile:v high` | High profile | Quality + compatibility |
| `-pix_fmt yuv420p` | 4:2:0 chroma | Browser playback requirement |
| `-g 1` | Every frame is a keyframe | Remotion seeks frame-by-frame |
| `-movflags +faststart` | Moov atom at file start | Instant browser playback |
| `-c:a aac -b:a 128k` | AAC audio | Audio track required |

**If source has no audio track:**
```bash
ffmpeg -i input.mp4 \
  -f lavfi -i anullsrc=r=44100:cl=mono \
  -r 30 -c:v libx264 -profile:v high -pix_fmt yuv420p \
  -g 1 -movflags +faststart \
  -c:a aac -b:a 128k \
  -shortest \
  output.mp4
```

**Source fps conversion:**
- 25fps → 30fps: `-r 30` (FFmpeg handles frame interpolation)
- 24fps → 30fps: `-r 30`
- 60fps → 30fps: `-r 30`

---

## Step 4 — Calculate playback rates

For every demo video that must fit within a specific beat duration:

```
playbackRate = source_video_duration / beat_duration
```

| playbackRate | Action |
|---|---|
| 1.0 | Video fits perfectly — no speed change needed |
| 1.0–2.5 | Acceptable speed-up — set `playbackRate` in timeline entry |
| > 2.5 | Video too long — flag for re-capture or split across multiple beats |
| < 1.0 | Video shorter than beat — will need hold frame or padding |

Record the calculated playback rate for each video asset.

---

## Step 5 — Copy processed assets to remotion/public/

After encoding, copy all processed files:
- `avatar.mp4` → `remotion/public/avatar.mp4`
- `source.wav` → `remotion/public/source.wav`
- Demo clips → `remotion/public/demo-*.mp4` or `demo-*.png`
- B-roll clips → `remotion/public/broll-*.mp4`
- Support images → `remotion/public/`
- SFX files → `remotion/public/` (from `SFX/` shared library)

**Naming:** Use descriptive names with the project slug prefix when possible. No spaces in filenames.

---

## Step 6 — Validate every asset

Run `ffprobe` on every video in `remotion/public/`:

```bash
ffprobe -v quiet -show_entries stream=codec_name,r_frame_rate,pix_fmt,codec_type -of compact <file>
```

**Expected values:**
- `codec_name=h264`
- `r_frame_rate=30/1`
- `pix_fmt=yuv420p`
- Audio stream present (`codec_type=audio`)

**Also check:**
- File size > 1KB (not empty/corrupt)
- Duration matches or exceeds target beat duration
- Correct orientation (portrait or landscape as expected)
- Can decode first frame without error

For image assets (`.png`, `.jpg`):
- File exists and is non-empty
- Dimensions are reasonable for the display mode (split-screen vs center-full)
- No corruption (can be opened)

For audio assets (`.mp3` SFX):
- File exists and > 1KB
- Duration > 0.1s
- Not silent (has audible content)

---

## Step 7 — Frame extraction and automated visual verification

For every processed video, extract one frame at the midpoint:

```bash
ffmpeg -i video.mp4 -ss <midpoint> -frames:v 1 -q:v 2 frame-check.jpg
```

**Then read each extracted frame using the Read tool.** Claude Code can open image files directly and see their contents. This is not optional — every frame must be visually inspected by reading the file.

For each frame, check:
- **Personal data** — names, emails, account info, bookmarks, conversation history visible anywhere in the frame
- **Browser chrome** — tabs, address bar, bookmarks bar, extension icons still present after crop
- **Narrative match** — cross-reference `audio/beat-map.json` to confirm the visible content matches what the narrator says during this beat's time range
- **Visual clarity** — text and UI elements are readable at mobile scale (1080x1920)
- **Sidebar content** — GPT conversation names, project names, account identifiers in sidebars

If any issue is found:
- Re-crop with tighter FFmpeg parameters
- Re-capture with mock HTML template
- Flag as a blocker — do not pass the asset to assembly

**Do not skip visual verification.** A filename like `demo-prompt.mp4` tells you nothing about what's actually visible in the frame. Read the file and look.

---

## Validation Report

Produce an asset validation log.

### Required structure

```markdown
# Asset Prep Report: [project-slug]

## Summary
- Assets processed: [count]
- Videos re-encoded: [count]
- Chrome cropped: [count]
- Silent audio tracks added: [count]
- Playback rates calculated: [count]
- All validations passed: [YES/NO]

## Asset Validation

| Asset | Type | Codec | FPS | Pix Fmt | Audio | Duration | PlaybackRate | Status |
|---|---|---|---|---|---|---|---|---|
| avatar.mp4 | video | h264 | 30 | yuv420p | aac | 34.48s | — | PASS |
| demo-prompt.mp4 | video | h264 | 30 | yuv420p | aac | 8.2s | 1.6x | PASS |
| source.wav | audio | pcm | — | — | — | 34.48s | — | PASS |
| demo-result.png | image | png | — | — | — | — | — | PASS |

## Frame Inspection

| Asset | Frame extracted | Chrome? | Personal data? | Narrative match? | Status |
|---|---|---|---|---|---|
| demo-prompt.mp4 | midpoint (4.1s) | No | No | Yes | PASS |
| avatar.mp4 | midpoint (17.2s) | No | No | N/A | PASS |

## Issues Found
- [List any issues, or "None"]

## Files Copied to remotion/public/
- [List all files]
```

---

## Relationship to Other Skills

**capture-demo**
Produces the raw assets that this skill processes.

**shot-list**
Approved shot list tells this skill which assets are needed and which display modes they'll use.

**motion-intent**
Runs in parallel with this skill after Phase 4b-iii approval.

**assemble-reel**
Uses the processed, validated assets in `remotion/public/`.

**qa-reel**
Checks encoding, but this skill should catch all encoding issues before QA.

This skill should eliminate all "video won't play in Remotion" issues before they reach assembly.

---

## Stop Condition

Stop after:
- all assets are processed and copied to `remotion/public/`
- all videos pass ffprobe validation
- all frames are visually verified
- validation report is produced
- any issues are listed

Do not begin assembly until all assets are validated.
Assembly with unvalidated assets produces rendering failures that are expensive to debug.
