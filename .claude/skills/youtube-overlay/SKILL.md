---
name: youtube-overlay
description: Plan visual overlays for a YouTube video from transcript and beat map.
disable-model-invocation: true
---

# youtube-overlay

Plan visual overlays for a YouTube video from its transcript and beat map. Produces an overlay plan document and a `youtube-timeline.json` ready for Remotion.

## When to use

After `youtube-ingest` completes and the user approves the beat map.

## Prerequisites

| Gate | Required |
|---|---|
| `video_ingested` | Must be in `gates_passed` |
| `audio/beat-map.json` | Must exist with overlay-worthy moments flagged |

## Inputs

| Input | Source |
|---|---|
| Beat map | `audio/beat-map.json` |
| Project config | `project.json` |
| User direction | Optional — "add logos when tools are mentioned", "highlight the demo parts", etc. |

## Procedure

### Step 1 — Read beat map and identify overlay moments

Read `audio/beat-map.json`. For every beat marked `overlay_worthy: true`, decide:

1. **Which component** from the registry
2. **What props** it needs (text, color, position, etc.)
3. **Timing** — start slightly before or at the spoken word, end 1-3s after
4. **Assets needed** — logos, thumbnails, etc.

### Step 2 — Apply overlay rules

**Density rule:** YouTube is not a reel — overlays should breathe. Target:
- **1 overlay every 15-30 seconds** for a calm tutorial
- **1 overlay every 8-15 seconds** for a fast-paced comparison or listicle
- Never more than 2 overlays visible simultaneously

**Timing rule:** Overlays should:
- Appear 0.2-0.5s after the word is spoken (viewer hears, then sees)
- Hold for 1.5-3.0s (longer than reels — YouTube viewers read at normal speed)
- Exit cleanly before the next overlay enters

**Position rule (landscape safe zones):**
- **Top 10%** (0-108px): reserved for YouTube title bar on hover — avoid persistent overlays
- **Bottom 15%** (918-1080px): reserved for YouTube progress bar + captions — avoid
- **Safe zone**: y 10%-85% of frame (108px to 918px)
- **Right 5%**: may be covered by YouTube sidebar suggestions on some layouts — prefer left/center

**Component selection guide:**

| Moment type | Component | Position | Duration |
|---|---|---|---|
| Tool mentioned by name | `BadgePopup` | top-left or top-right | 2-3s |
| Feature name introduced | `KeywordFadeIn` | center or top-center | 2-3s |
| Stat or number | `NumberPopup` or `OverlayKeyword` | center | 2-3s |
| Section/chapter change | `ChapterDivider` | full frame | 1.5-2s |
| URL or link to share | `LinkOverlay` | bottom-right | 3-5s |
| Demo UI element to highlight | `HighlightBox` | over the element | 2-4s |
| Speaker introduction | `LowerThird` | bottom-left | 3-5s |
| Subscribe prompt | `SubscribeCTA` | bottom-center | 3-4s |
| End screen | `EndScreen` | full frame | 15-20s |
| Big emphasis word | `OverlayKeyword` | center | 1.5-2.5s |
| Section title card | `HeroTextCard` | full frame | 2-3s |

### Step 3 — Collect required assets

For each overlay that needs an asset (logo, thumbnail):
1. Check if it exists in `assets/` or `remotion/public/`
2. If not, flag it for the user to provide
3. Copy all needed assets to `remotion/public/` with `yt-` prefix

### Step 4 — Write overlay plan

Produce `output/overlay-plan.md`:

```markdown
# Overlay Plan: <project title>

## Summary
- Total overlays: X
- Average density: 1 per Ys
- Components used: [list]
- Assets needed: [list]

## Overlay Schedule

| # | Time | Spoken word/moment | Component | Props summary | Asset |
|---|---|---|---|---|---|
| 1 | 0:02 | "Hey everyone" | LowerThird | title: "Mits", subtitle: "AI Tools" | — |
| 2 | 0:15 | "Claude" | BadgePopup | text: "Claude", icon: claude-logo | yt-claude-logo.png |
| 3 | 1:20 | "three key features" | ChapterDivider | title: "3 Key Features" | — |
| ... | | | | | |

## Missing Assets
- [ ] claude-logo.png — needed for overlay #2
```

**STOP for user approval** — this is the creative gate. The user reviews which moments get overlays and can add/remove/adjust before assembly.

### Step 5 — Generate youtube-timeline.json

After user approval, produce `output/youtube-timeline.json`:

```json
{
  "total_duration": 612.5,
  "video": "yt-source.mp4",
  "fps": 30,
  "width": 1920,
  "height": 1080,
  "lanes": {
    "overlays": [
      {
        "beat_id": "seg-001",
        "type": "LowerThird",
        "start": 1.5,
        "end": 5.5,
        "props": {
          "title": "Mits",
          "subtitle": "AI Tools & Tutorials",
          "accentColor": "#3B82F6",
          "position": "bottom-left"
        }
      },
      {
        "beat_id": "seg-002",
        "type": "BadgePopup",
        "start": 15.2,
        "end": 18.0,
        "asset": "yt-claude-logo.png",
        "props": {
          "text": "Claude",
          "color": "#D97757"
        }
      }
    ],
    "sfx": [],
    "music": [],
    "captions": []
  }
}
```

### Step 6 — Copy timeline to Remotion

```bash
cp output/youtube-timeline.json ../../remotion/public/youtube-timeline.json
```

### Step 7 — Update project.json

```json
{
  "phase": "overlay-plan",
  "status": "approved",
  "gates_passed": ["video_ingested", "overlay_plan_approved"],
  "updated": "<timestamp>"
}
```

## Output

| Artifact | Path |
|---|---|
| Overlay plan | `output/overlay-plan.md` |
| YouTube timeline | `output/youtube-timeline.json` |
| Remotion timeline | `remotion/public/youtube-timeline.json` |

## Gates

Requires: `video_ingested`
Sets: `overlay_plan_approved`

## After this skill

The user can:
1. **Preview:** `cd remotion && npx remotion studio` → select "YouTubeComposition"
2. **Adjust:** modify `youtube-timeline.json` entries (timing, props)
3. **Render:** `cd remotion && npx remotion render YouTubeComposition --output out/youtube-enhanced.mp4`

## Iteration

Unlike the reel pipeline, YouTube overlay iteration is fast:
- Change an overlay's timing → edit one entry in the JSON
- Add a new overlay → add an entry to the overlays array
- Remove an overlay → delete the entry
- No cascading pipeline effects — each overlay is independent

This makes the YouTube pipeline much lighter than the reel pipeline for mid-session changes.
