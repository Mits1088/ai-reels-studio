---
name: youtube
description: YouTube content creation suite — script, SEO, hooks, thumbnails, demo ingest, and Remotion motion graphics for long-form YouTube videos. Run alongside the Instagram reel workflow from the same source brief.
---

# YouTube Content Skill

This skill produces YouTube long-form content in parallel with the reel pipeline.

When the user provides a source URL for a reel and also wants a YouTube video, this skill suite runs from the same `brief.md` but produces a separate set of YouTube-specific outputs.

This is **NOT** the reel workflow. Do not mix reel phases and YouTube phases.

---

## YouTube Workflow Phases

| Phase | Command | What it needs | What it produces |
|---|---|---|---|
| **Y0** | `/youtube demo-ingest` | Demo flow voice recording (WAV/M4A) | `youtube/demo-flow.md` |
| **Y1** | `/youtube script` | `brief.md` + top-performing video URL + `youtube/demo-flow.md` | `youtube/script.md` + `youtube/reference-analysis.md` |
| **Y2** | `/youtube hook` | `youtube/script.md` | `youtube/hooks.md` |
| **Y3** | `/youtube seo` | `youtube/script.md` | `youtube/seo-package.md` |
| **Y4** | `/youtube thumbnail` | `youtube/seo-package.md` + `project.json` theme | `youtube/thumbnail-brief.md` |
| **Y5** | `/youtube motion` | `youtube/script.md` + `output/timeline.json` (reel) | `youtube/motion-package.md` |

Run in order. Each phase depends on the previous one.

---

## Sub-skill Routing

When the user invokes `/youtube [command]`, read the corresponding sub-skill file and follow its instructions completely.

| Command | Sub-skill file |
|---|---|
| `/youtube demo-ingest` | `.claude/skills/youtube/sub-skills/demo-ingest.md` |
| `/youtube script` | `.claude/skills/youtube/sub-skills/script.md` |
| `/youtube hook` | `.claude/skills/youtube/sub-skills/hook.md` |
| `/youtube seo` | `.claude/skills/youtube/sub-skills/seo.md` |
| `/youtube thumbnail` | `.claude/skills/youtube/sub-skills/thumbnail.md` |
| `/youtube motion` | `.claude/skills/youtube/sub-skills/motion.md` |

---

## Reference Guides to Load

Before each sub-skill, load the reference guides it specifies. These live in `.claude/skills/youtube/references/`.

| Sub-skill | Load these references |
|---|---|
| demo-ingest | (none) |
| script | `algorithm-guide.md`, `retention-guide.md`, `voice-profile.md`, `jack-roberts-techniques.md`, `script-structure.md` |
| hook | `retention-guide.md`, `voice-profile.md`, `jack-roberts-techniques.md` |
| seo | `seo-playbook.md` |
| thumbnail | `thumbnail-ctr.md` |
| motion | (none — invokes `remotion-best-practices` skill instead) |

---

## Project Folder Structure

All YouTube outputs live under `projects/<slug>/youtube/`:

```
projects/<slug>/youtube/
├── demo-recording.wav         (user-provided — demo flow voice recording)
├── demo-flow.md               (Phase Y0 — transcribed and structured demo steps)
├── reference-analysis.md      (Phase Y1 — top-performing video breakdown)
├── script.md                  (Phase Y1 — full YouTube script with demo cues)
├── hooks.md                   (Phase Y2 — 5 hook variants with ratings)
├── seo-package.md             (Phase Y3 — titles, description, tags, schema)
├── thumbnail-brief.md         (Phase Y4 — 3 A/B thumbnail design briefs)
└── motion-package.md          (Phase Y5 — Remotion export + composition plan)
```

---

## User Inputs Required

The YouTube workflow requires two inputs the user must supply:

**1. Top-performing YouTube video URL**
A video on the same topic that has performed well. Used for: structure benchmarking, hook type analysis, key claims research, chapter flow reference. Provide this at Phase Y1.

**2. Demo flow voice recording**
A rough spoken voice note (2-5 minutes) where the creator talks through what they'll show on screen during the video. Not a script — just informal planning notes: "I'll start by showing X, then click into Y, then demonstrate Z." Provide the audio file path at Phase Y0.

---

## Integration with the Reel Workflow

The YouTube workflow reads from the reel workflow but does not write back to it.

**What it borrows from the reel:**
- `projects/<slug>/brief.md` — the source brief drives both reel and YouTube content
- `projects/<slug>/project.json` — theme colors (theme_primary, theme_secondary) for thumbnail and motion consistency
- `projects/<slug>/output/timeline.json` — at Phase Y5, to identify which reel Remotion elements can be exported as YouTube clips
- `remotion/public/brands/` — brand SVGs already downloaded for the reel are reused in YouTube Remotion composition

**Minimum gate to start:** `brief_approved` must be in `gates_passed` in `project.json`.

**The YouTube script and reel script are entirely different documents.** The reel is 20-60 seconds spoken naturally for ElevenLabs. The YouTube script is 8-20 minutes with production cues, pattern interrupts, and chapter timestamps.

---

## Standalone Script Creation (no pipeline required)

If the user wants a YouTube script **without** an existing reel project (no `brief.md`, no `project.json`, no gates), use the `youtube-script-creator` skill instead. It is a standalone 5-step workflow that produces a complete shoot-ready package from just a topic or URL.

---

## Stop Condition

Each sub-skill has its own stop condition. After routing to a sub-skill, follow its instructions and stop where it specifies. Do not chain multiple YouTube phases automatically.
