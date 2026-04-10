---
name: youtube-ingest
description: Import a YouTube video, extract audio, generate transcript, and produce a beat map with overlay-worthy moments.
disable-model-invocation: true
---

# youtube-ingest

Import a YouTube video into the project, extract audio, generate transcript, and produce a beat map with overlay-worthy moments flagged.

## When to use

When the user provides a YouTube video file (already downloaded) and wants to add Remotion overlays to it.

## Prerequisites

- User has the video file (`.mp4`, `.webm`, `.mov`)
- FFmpeg installed (for audio extraction)
- Whisper installed (for transcription) — or user provides a transcript

## Inputs

| Input | Required | Source |
|---|---|---|
| Video file | Yes | User provides path |
| Transcript | No | Auto-generated via Whisper, or user provides `.srt`/`.txt` |

## Procedure

### Step 1 — Create project structure

```
projects/<slug>/
├── project.json
├── video/
│   └── source.mp4          ← original video
├── audio/
│   ├── source.wav           ← extracted audio
│   ├── transcript.json      ← Whisper output
│   └── beat-map.json        ← timestamped segments
└── output/
    ├── overlay-plan.md      ← Phase 2 output
    └── youtube-timeline.json
```

Initialize `project.json`:

```json
{
  "slug": "<slug>",
  "type": "youtube",
  "title": "<video title>",
  "duration": null,
  "fps": 30,
  "width": 1920,
  "height": 1080,
  "video_file": "source.mp4",
  "phase": "ingest",
  "status": "in_progress",
  "gates_passed": [],
  "created": "<timestamp>",
  "updated": "<timestamp>"
}
```

### Step 2 — Copy and validate video

1. Copy video to `projects/<slug>/video/source.mp4`
2. Probe with FFmpeg:
   ```bash
   ffprobe -v quiet -show_entries format=duration:stream=width,height,r_frame_rate,codec_name -of json source.mp4
   ```
3. Record duration, resolution, fps in `project.json`
4. If not 1920x1080 or 30fps, note the actual values — the composition will adapt

### Step 3 — Extract audio

```bash
ffmpeg -i video/source.mp4 -vn -acodec pcm_s16le -ar 44100 -ac 1 audio/source.wav
```

### Step 4 — Generate transcript

**Option A — Whisper (automatic):**
```bash
whisper audio/source.wav --model medium --output_format json --output_dir audio/
```

**Option B — User provides SRT/transcript:**
Parse the provided file into the same JSON format.

**Option C — YouTube auto-captions:**
If the user has the YouTube `.srt` file, parse it.

### Step 5 — Build beat map

From the transcript, create `audio/beat-map.json`:

```json
{
  "total_duration": 612.5,
  "beats": [
    {
      "id": "seg-001",
      "start": 0.0,
      "end": 8.2,
      "text": "Hey everyone, today we're looking at...",
      "type": "intro",
      "overlay_worthy": false
    },
    {
      "id": "seg-002",
      "start": 8.2,
      "end": 15.6,
      "text": "Claude just shipped a feature called...",
      "type": "tool-mention",
      "overlay_worthy": true,
      "overlay_hint": "BadgePopup — Claude logo + feature name"
    }
  ]
}
```

**Beat types** (for flagging overlay-worthy moments):

| Type | Overlay-worthy? | Typical overlay |
|---|---|---|
| `intro` | Sometimes | LowerThird (speaker name) |
| `tool-mention` | Yes | BadgePopup (logo pill) |
| `feature-name` | Yes | KeywordFadeIn (feature name) |
| `stat` | Yes | NumberPopup or OverlayKeyword |
| `demo-start` | Sometimes | ChapterDivider |
| `demo-action` | Sometimes | HighlightBox on UI element |
| `comparison` | Yes | HeroTextCard or labels |
| `section-change` | Yes | ChapterDivider or FlashReset |
| `cta` | Yes | SubscribeCTA or LinkOverlay |
| `explanation` | No | — |
| `filler` | No | — |

### Step 6 — Copy video to Remotion public

```bash
cp video/source.mp4 ../../remotion/public/yt-source.mp4
```

Use the `yt-` prefix to avoid collisions with reel assets.

### Step 7 — Update project.json

```json
{
  "phase": "ingest",
  "status": "completed",
  "duration": 612.5,
  "gates_passed": ["video_ingested"],
  "updated": "<timestamp>"
}
```

## Output

| Artifact | Path |
|---|---|
| Source video | `video/source.mp4` |
| Extracted audio | `audio/source.wav` |
| Transcript | `audio/transcript.json` |
| Beat map | `audio/beat-map.json` |
| Remotion-ready video | `remotion/public/yt-source.mp4` |

## Gate

Sets: `video_ingested`

**STOP for user review** — present the beat map with overlay-worthy moments highlighted. User approves before overlay planning begins.

## Notes

- The video's own audio stays embedded — Remotion plays it via `<OffthreadVideo muted={false}>`
- SFX and music are additive layers on top of the video's audio
- If the video is very long (>15 min), suggest the user identify key sections to overlay rather than planning overlays for the entire duration
- Transcript quality matters — if Whisper output has errors in tool names, correct them (same as caption-polish for reels)
