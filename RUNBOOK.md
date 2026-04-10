# Operator Runbook

How to produce an Instagram reel from HeyGen avatar or source audio, end to end.

## Prerequisites

- Python 3.10+
- `pip install pillow ffmpeg-python`
- ffmpeg binary in PATH ([download](https://ffmpeg.org/download.html))
- OpenAI API key (optional — only if using Whisper for transcription)
- Node.js 18+ (for Remotion rendering and capture scripts)
- Run `npm install` once from repo root (installs Playwright)
- Run `cd remotion && npm install` once (installs Remotion dependencies)
- Run `npx playwright install chromium` once (installs headless browser for capture)

## Where to Put the Avatar File

Place your HeyGen avatar MP4 anywhere accessible. Common convention:

```
projects/<slug>/audio/avatar.mp4
```

The extraction command accepts any path — it does not need to be inside the project. The output always goes to:

```
projects/<slug>/audio/source.wav
```

## Where to Put Assets for Remotion

All media files referenced in `timeline.json` must be copied to `remotion/public/` before previewing or rendering. This includes:

- `avatar.mp4` — HeyGen avatar video (visual only, muted in composition)
- `source.wav` — extracted narration audio (the primary audio track)
- Any demo screenshots, B-roll videos, support images, and SFX files

```bash
cp projects/<slug>/audio/source.wav remotion/public/source.wav
cp projects/<slug>/audio/avatar.mp4 remotion/public/avatar.mp4
cp assets/demo-screenshot.png remotion/public/demo-screenshot.png
# etc.
```

The `timeline.json` used by Remotion lives at `remotion/public/timeline.json`. Always keep it in sync with `projects/<slug>/output/timeline.json`:

```bash
cp projects/<slug>/output/timeline.json remotion/public/timeline.json
```

---

## Quick Start (Skill-Driven Workflow)

```
Phase 0:   /source-brief        -> research URL, produce brief.md
Phase 0b:  /theme-factory       -> select product-aligned theme (MANDATORY)
Phase 1:   /reel-script         -> ElevenLabs-ready script (approve before audio)
Phase 1b:  /broll-pipeline      -> classify available b-roll (optional, ask first)
Phase 2:   /ingest-voice        -> extract audio, generate beat-map + captions
Phase 2b:  /script-reconcile    -> diff script vs transcript, lock source of truth
Phase 3:   Beat map from reconciled transcript
Phase 3b:  /caption-polish      -> spelling, chunks, emphasis, artifact removal
Phase 3c:  Demo config from beat map
Phase 4:   /capture-demo        -> screenshots, mock captures, SFX
Phase 4b:  /shot-list           -> 3 sub-phases:
           - 4b-i:   Visual assignment (what viewer sees per beat)
           - 4b-ii:  Component mapping + asset fitness audit
           - 4b-iii: Technical planning (backgrounds, SFX, zoom coordinates)
Phase 4c:  /motion-intent       -> beat-by-beat motion direction (parallel with 4d)
Phase 4d:  /asset-prep          -> crop, encode, validate for Remotion (parallel with 4c)
Phase 5:   /assemble-reel       -> timeline.json + ReelComposition.tsx
Phase 5b:  Quick preview        -> scrub 5 key frames in Remotion studio
Phase 6:   /qa-reel             -> qa-report.md (must pass before render)
Phase 7:   cd remotion && npx remotion render ReelComposition --output out/reel.mp4
```

### Style Selection (set early — affects all downstream decisions)

| Reel type | Style |
|---|---|
| Feature demo, tutorial, single-tool showcase | `cinematic-presenter` |
| Listicle, comparison, claim-and-prove, tool roundup | `editorial-authority` |

Set in `project.json`: `"style": "editorial-authority"`

### Theme Selection (Phase 0b — before scripting)

Run `/theme-factory` to select a product-aligned color theme. Pre-sets: Claude, Google, ChatGPT, Gemini, Tech Neutral. Records `theme`, `theme_primary`, `theme_secondary` in project.json.

### Component Mapping (Phase 4b-ii — before technical planning)

See `.claude/rules/component-mapping.md`. For every beat:
1. Classify narration (keyword? claim? proof? explanation?)
2. Select Remotion component (style-specific table)
3. Audit asset fitness (MATCH/PARTIAL/MISMATCH/MISSING)
4. Validate flow (component variety, layout rhythm)

**MISMATCH or MISSING = blocker.** Capture before continuing.

---

## Gate Enforcement

Every skill checks gates before starting. 11 gates control the pipeline:

| # | Gate ID | Set by | Required before |
|---|---|---|---|
| 1 | `brief_approved` | User approval after source-brief | reel-script |
| 2 | `theme_set` | theme-factory | reel-script |
| 3 | `script_approved` | User approval after reel-script | ingest-voice, broll-pipeline |
| 4 | `reconciliation_resolved` | script-reconcile | beat-map, caption-polish, capture-demo, shot-list |
| 5 | `visual_assignment_approved` | User approval after shot-list 4b-i | shot-list 4b-ii |
| 6 | `asset_fitness_passed` | shot-list 4b-ii (auto) | shot-list 4b-iii |
| 7 | `technical_planning_approved` | User approval after shot-list 4b-iii | motion-intent, asset-prep |
| 8 | `motion_intent_reviewed` | User review after motion-intent | assemble-reel |
| 9 | `assets_validated` | asset-prep | assemble-reel |
| 10 | `preview_passed` | Quick preview after assembly | qa-reel |
| 11 | `qa_passed` | qa-reel | render |

### Gate CLI

```bash
# Check if a skill can run
PYTHONPATH=. python -m lib.gates check projects/<slug> <skill-name>

# Mark a gate as passed
PYTHONPATH=. python -m lib.gates set projects/<slug> <gate-id>

# Reset a gate and all downstream gates (cascading)
PYTHONPATH=. python -m lib.gates reset projects/<slug> <gate-id>

# Show all gate statuses
PYTHONPATH=. python -m lib.gates status projects/<slug>
```

Example output:
```
Project: my-reel
Phase:   assembly
Status:  in_progress
Gates:   7/11

  [x] brief_approved
  [x] theme_set
  [x] script_approved
  [x] reconciliation_resolved
  [x] visual_assignment_approved
  [x] asset_fitness_passed
  [x] technical_planning_approved
  [ ] motion_intent_reviewed
  [ ] assets_validated
  [ ] preview_passed
  [ ] qa_passed
```

---

## Quick Start (CLI Workflow — legacy)

```bash
# 1. Create a new project from the starter template
cp -r templates/instagram-reel-avatar projects/my-reel
# Edit project.json: set slug, title, style, theme
# Edit brief.md: fill in goal, audience, hook, CTA

# 2. Write the script
# Edit script.md: write beat-by-beat narration

# 3a. Extract audio from HeyGen avatar (recommended path):
PYTHONPATH=. python -m lib.ingest.cli extract projects/my-reel/audio/avatar.mp4 projects/my-reel

# 3b. Then manually create beat-map.json and captions.json
#     (see "Manual Beat-Map Workflow" below)

# OR 3c. Full auto pipeline (requires transcription provider):
PYTHONPATH=. python -m lib.ingest.cli full narration.wav projects/my-reel --provider whisper --api-key $OPENAI_API_KEY

# 4. Register assets
PYTHONPATH=. python -m lib.capture.cli register path/to/demo.png projects/my-reel \
  --type image --role demo --beats beat-03 --desc "Demo screenshot"
# Repeat for each asset...
PYTHONPATH=. python -m lib.capture.cli finalize projects/my-reel

# 5. Build timeline
# Create projects/my-reel/output/timeline.json (see timeline schema)

# 6. Validate contracts
PYTHONPATH=. python lib/validate.py projects/my-reel

# 7. Run QA
PYTHONPATH=. python -m lib.qa.cli projects/my-reel
```

## Two Ingestion Paths

### Path A: Extract + Manual (no Whisper needed)

This is the primary workflow when you have a HeyGen avatar video.

```bash
# Step 1: Extract audio
PYTHONPATH=. python -m lib.ingest.cli extract avatar.mp4 projects/my-reel
# Output: projects/my-reel/audio/source.wav
# Updates: project.json -> voice phase

# Step 2: Listen to source.wav, then create beat-map.json and captions.json
# by hand (see templates below)
```

### Path B: Full Auto Pipeline

This path auto-generates everything from audio via transcription.

```bash
PYTHONPATH=. python -m lib.ingest.cli full audio.wav projects/my-reel --provider whisper --api-key KEY
# Output: source.wav + voice.json + beat-map.json + captions.json
```

### Path comparison

| | Path A (extract + manual) | Path B (full auto) |
|---|---|---|
| Requires ffmpeg | Yes | Yes (for video input) |
| Requires Whisper | No | Yes |
| beat-map.json | You create it | Auto-generated |
| captions.json | You create it | Auto-generated |
| Best for | HeyGen avatar video | Raw narration audio |

## Manual Beat-Map Workflow

After extracting audio, create these two files by hand.

### `audio/beat-map.json`

Listen to `source.wav` and note phrase boundaries. Create beats matching your script:

```json
{
  "total_duration": 27.5,
  "beats": [
    {
      "id": "beat-01",
      "scene": 1,
      "phrase": "What if your terminal could write code?",
      "start": 0.000,
      "end": 3.200,
      "words": [
        { "word": "What", "start": 0.000, "end": 0.280 },
        { "word": "if", "start": 0.300, "end": 0.420 },
        { "word": "your", "start": 0.440, "end": 0.640 },
        { "word": "terminal", "start": 0.660, "end": 1.200 },
        { "word": "could", "start": 1.220, "end": 1.480 },
        { "word": "write", "start": 1.500, "end": 1.800 },
        { "word": "code?", "start": 1.820, "end": 3.200 }
      ],
      "visual_intent": "Avatar full-screen with bold text",
      "asset_refs": ["avatar-narrator"]
    }
  ]
}
```

**Rules:**
- Beat IDs: `beat-01`, `beat-02`, or sub-beats `beat-01a`, `beat-01b` (zero-padded, optional letter suffix)
- Each beat needs: id, scene, phrase, start, end, words, visual_intent
- Words array: each word with start/end in seconds (3 decimal places)
- Beats must not overlap
- Last beat end must not exceed total_duration

### `audio/captions.json`

One caption per beat, with simplified display text:

```json
{
  "captions": [
    {
      "beat_id": "beat-01",
      "start": 0.000,
      "end": 3.200,
      "text": "Your terminal writes code"
    }
  ]
}
```

**Rules:**
- Max 6 words per caption text
- Every beat should have a caption
- start/end must match beat timing

Then validate: `PYTHONPATH=. python lib/validate.py projects/my-reel`

---

## Detailed Phase Reference

### Phase 0: Source Brief (when starting from a URL)

```bash
node lib/capture/source-brief.js --url https://... --project <slug>
```

Produces: `source-research.md`, `source-research.json`, `assets/source/`

**Stop condition:** Brief direction approved. Sets `brief_approved` gate.

### Phase 0b: Theme Selection (mandatory)

Run `/theme-factory`. Sets `theme_set` gate when `theme`, `theme_primary`, `theme_secondary` are populated in project.json.

### Phase 1: Script (`/reel-script`)

**Input:** Approved `brief.md` + theme set in project.json.

**Output:** `script.md` — ElevenLabs-ready script.

**Stop condition:** Script approved. Sets `script_approved` gate.

### Phase 2: Voice Ingest

See "Two Ingestion Paths" above.

### Phase 2b: Script Reconciliation (`/script-reconcile`)

Diffs the approved script against actual spoken transcript. Flags changed words, dropped phrases, altered tool names. **The transcript wins** — all downstream references must match what was actually spoken.

**Output:** `audio/reconciliation.md`. Sets `reconciliation_resolved` gate.

### Phase 3b: Caption Polish (`/caption-polish`)

Corrects product spelling, splits chunks for mobile readability, tags emphasis words, strips ElevenLabs artifacts.

**Output:** `audio/captions.json` (polished version replaces auto-generated).

### Phase 4: Asset Registration

```bash
PYTHONPATH=. python -m lib.capture.cli register SOURCE projects/<slug> \
  --type TYPE --role ROLE --beats BEAT,BEAT --desc "Description"
PYTHONPATH=. python -m lib.capture.cli validate projects/<slug>
PYTHONPATH=. python -m lib.capture.cli finalize projects/<slug>
```

### Phase 4b: Shot List (3 sub-phases)

**4b-i: Visual assignment** — map every beat to its visual type and asset. **Stop for approval.** Sets `visual_assignment_approved`.

**4b-ii: Component mapping + asset fitness** — select Remotion components, audit asset fitness. **Blocks on MISMATCH/MISSING.** Auto-sets `asset_fitness_passed`.

**4b-iii: Technical planning** — backgrounds, SFX placement, zoom coordinates. **Stop for approval.** Sets `technical_planning_approved`.

### Phase 4c: Motion Intent (`/motion-intent`)

Beat-by-beat motion direction with preset mapping. Runs **in parallel** with Phase 4d.

**Output:** `output/motion-intent.md`. Sets `motion_intent_reviewed` after user review.

### Phase 4d: Asset Prep (`/asset-prep`)

Crop, encode, validate all assets for Remotion. Runs **in parallel** with Phase 4c.

Sets `assets_validated` gate after all assets pass ffprobe validation.

### Phase 5: Timeline Assembly

**Output:** `output/timeline.json` + `ReelComposition.tsx` updates.

```bash
PYTHONPATH=. python lib/validate.py projects/<slug>
cp projects/<slug>/output/timeline.json remotion/public/timeline.json
```

### Phase 5b: Quick Preview

Open Remotion studio, scrub 5 key frames. Sets `preview_passed` gate.

### Phase 6: QA

```bash
PYTHONPATH=. python -m lib.qa.cli projects/<slug>
```

**18 automated checks** including: sync, captions, dead-air, missing-assets, transitions, audio-balance, consistency, placeholders, safe-zones, duration, avatar-absence, center-full-streak, sfx-coverage, video-encoding, screenshot-hold, flash-budget, style-compliance, overlay-positioning.

Sets `qa_passed` gate on pass. Sets status to `failed` on fail.

### Phase 7: Render (Remotion)

```bash
cd remotion
npx remotion studio       # preview
npx remotion render ReelComposition --output out/reel.mp4   # final render
```

Output: `remotion/out/reel.mp4` — 1080x1920, 30fps, ready for Instagram.

---

## Reel Learning (Post-Render)

After a successful render, capture what worked:

```bash
# Generate learnings.md from project artifacts
PYTHONPATH=. python -m lib.learn capture projects/<slug>

# Find similar projects and compare learnings
PYTHONPATH=. python -m lib.learn compare projects/<slug>
```

Output: `output/learnings.md` with auto-computed metrics (duration, beat count, SFX count, avatar %, visual frequency) plus `(fill in)` placeholders for subjective assessment.

---

## Project Migration

Normalize old projects to current schema:

```bash
# Preview changes (safe — writes nothing)
PYTHONPATH=. python -m lib.migrate --dry-run

# Apply changes to all projects
PYTHONPATH=. python -m lib.migrate

# Single project
PYTHONPATH=. python -m lib.migrate --project <slug>
```

Fixes: old phase names, old status values, missing required fields, empty `gates_passed` arrays (inferred from file existence).

---

## File Reference

| File | Purpose | Created by |
|---|---|---|
| `source-research.md` | Feature intelligence from source URL | source-brief script |
| `source-research.json` | Machine-readable version of above | source-brief script |
| `assets/source/` | Images + screenshots from source URL | source-brief script |
| `project.json` | Project metadata, phase tracking, gates | new-reel / manual |
| `brief.md` | Goal, audience, hook, CTA | manual (informed by source-research) |
| `script.md` | Beat-by-beat narration | reel-script skill |
| `assets-needed.md` | Asset checklist | manual |
| `audio/source.wav` | Extracted/copied narration audio | ingest pipeline |
| `audio/voice.json` | Word-level transcript | full pipeline only |
| `audio/beat-map.json` | Phrase-level timing | full pipeline or manual |
| `audio/captions.json` | Time-bound captions | caption-polish skill |
| `audio/reconciliation.md` | Script vs transcript diff | script-reconcile skill |
| `assets/catalog.json` | Asset registry | capture pipeline |
| `shot-list.md` | Visual assignment + component mapping + technical planning | shot-list skill |
| `output/motion-intent.md` | Beat-by-beat motion direction | motion-intent skill |
| `output/timeline.json` | 6-lane composition spec | assemble-reel skill |
| `output/qa_report.json` | QA gate results | QA pipeline |
| `output/qa-report.md` | Human-readable QA report | qa-reel skill |
| `output/learnings.md` | Post-render knowledge capture | learn.py |
| `screenshots/zoom-hints.json` | Auto-calculated zoom coords | capture-demo script |

## CLI Reference

### Python pipeline

```bash
# Validate all contracts
PYTHONPATH=. python lib/validate.py projects/<slug>

# Gate enforcement
PYTHONPATH=. python -m lib.gates check  projects/<slug> <skill-name>
PYTHONPATH=. python -m lib.gates set    projects/<slug> <gate-id>
PYTHONPATH=. python -m lib.gates reset  projects/<slug> <gate-id>
PYTHONPATH=. python -m lib.gates status projects/<slug>

# Audio extraction (Path A — no Whisper needed)
PYTHONPATH=. python -m lib.ingest.cli extract INPUT projects/<slug>

# Full pipeline (Path B — auto transcription)
PYTHONPATH=. python -m lib.ingest.cli full INPUT projects/<slug> --provider whisper|mock

# Asset registration
PYTHONPATH=. python -m lib.capture.cli register SOURCE projects/<slug> --type TYPE --role ROLE --beats B1,B2 --desc "..."
PYTHONPATH=. python -m lib.capture.cli validate projects/<slug>
PYTHONPATH=. python -m lib.capture.cli finalize projects/<slug>

# QA
PYTHONPATH=. python -m lib.qa.cli projects/<slug> [--json]

# Learning capture
PYTHONPATH=. python -m lib.learn capture projects/<slug>
PYTHONPATH=. python -m lib.learn compare projects/<slug>

# Project migration
PYTHONPATH=. python -m lib.migrate --dry-run
PYTHONPATH=. python -m lib.migrate [--project <slug>]
```

### Node.js capture scripts

```bash
# Phase 0 — research a URL and produce brief intelligence
node lib/capture/source-brief.js --url https://... --project <slug>

# Extract frames from broll videos at specific timestamps
node lib/capture/extract-frames.js --video broll-el10.mp4 --times 0.8,3.8

# Capture demo screenshots with 3-stage fallback (live -> manual -> mock HTML)
node lib/capture/capture-demo.js
node lib/capture/capture-demo.js --stage 3          # skip straight to mock
node lib/capture/capture-demo.js --demo el10        # single demo only

# Apply zoom coordinates from capture output into timeline.json
node lib/capture/apply-zoom-hints.js
node lib/capture/apply-zoom-hints.js --lane broll   # target broll lane
node lib/capture/apply-zoom-hints.js --dry-run      # preview without writing
```

## Common Issues

**"ffmpeg binary not found"** — Install ffmpeg and add to PATH.

**"ffmpeg-python is not installed"** — Run `pip install ffmpeg-python`.

**"Beat map not found"** — Run voice ingest (or create manually) before QA.

**"Timeline not found"** — Create timeline.json before QA.

**"Gate check failed / BLOCKED"** — Run `PYTHONPATH=. python -m lib.gates status projects/<slug>` to see which gates are missing, then run the required skill.

**"Unknown phase / status"** — Run `PYTHONPATH=. python -m lib.migrate --project <slug>` to normalize old project.json formats.

**"Video encoding errors in Remotion"** — Re-encode with: `ffmpeg -i input.mp4 -r 30 -c:v libx264 -profile:v high -pix_fmt yuv420p -g 1 -movflags +faststart -c:a aac -b:a 128k output.mp4`

**Validator import error** — Run with `PYTHONPATH=.` from repo root.

**Unicode error on Windows** — Run with `PYTHONIOENCODING=utf-8`.

**Mock provider gives wrong beat count** — The mock always returns 4 beats. Use extract-only mode and create beat-map.json manually instead.
