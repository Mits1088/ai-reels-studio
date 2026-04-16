# AI Reels Studio

This project creates short vertical Instagram reels about AI tools, features, and news.

The workflow is audio-first, beat-based, proof-led, built on **Remotion** (React-based video engine).
Composition engine: `remotion/src/ReelComposition.tsx`. `lib/compose/` is legacy — not used for rendering.

---

## Master Rule

**Actual audio timing is the source of truth.**
Do not finalize visuals from estimated duration if actual narration audio exists.

**QA always before render.** Do not export until all QA gates pass.

**Gate enforcement is mandatory.** Run `python -m lib.phase check <skill> <project-dir>` before any skill.

---

## Rule Hierarchy

1. `.claude/rules/reel-workflow.md`
2. `.claude/rules/gate-enforcement.md`
3. `.claude/rules/change-pipeline.md`
4. `.claude/rules/timing-sync.md`
5. `.claude/rules/qa-gates.md`
6. `.claude/rules/visual-style.md`
7. `.claude/rules/style-profiles.md`
8. `.claude/rules/component-mapping.md`
9. `.claude/rules/demo-capture-strategy.md`
10. `.claude/rules/remotion-skill-required.md`
11. `.claude/rules/reel-learning.md`
12. `.claude/rules/template-grammar.md` (when style is `proof-escalation-editorial`)
13. `.claude/skills/*/SKILL.md`
14. `CLAUDE.md`

`visual-style.md` provides rendering defaults. `assemble-reel` may override display choices by beat intent when retention or presenter anchoring is stronger.

---

## Project Goals

Reels are: vertical-first (1080x1920), fast-paced, proof-led, reproducible, reviewable in phases.

## Non-Negotiables

- 1080x1920 output, 30fps default, 20-60s typical
- Captions in mobile-safe zones; demos match narration timing
- Every asset serves a beat, scene, or message purpose
- Do not proceed to next phase without summarizing what was created and validated
- Do not render until QA passes

---

## YouTube Content Workflow (parallel to reel)

When the user requests YouTube content alongside a reel, run the `/youtube` skill suite.

**Required user inputs:**
- Top-performing YouTube video URL on the topic (for structure + content reference)
- Demo flow voice recording (WAV/M4A — informal spoken notes on what to show on screen)

**Phase Y0:** `/youtube demo-ingest` — transcribe demo flow recording → `youtube/demo-flow.md`
**Phase Y1:** `/youtube script` — full YouTube script (8-20 min) with `[DEMO: ...]` cues → `youtube/script.md`
**Phase Y2:** `/youtube hook` — 5 hook variants with drop-off ratings → `youtube/hooks.md`
**Phase Y3:** `/youtube seo` — titles, description, tags, chapters, schema → `youtube/seo-package.md`
**Phase Y4:** `/youtube thumbnail` — 3 A/B thumbnail briefs with hex codes → `youtube/thumbnail-brief.md`
**Phase Y5:** `/youtube motion` — reel clip exports + YouTube Remotion composition (1920×1080) → `youtube/motion-package.md`

All YouTube outputs: `projects/<slug>/youtube/`
Minimum gate to start: `brief_approved` in `project.json`
Full skill documentation: `.claude/skills/youtube/SKILL.md`

**Important:** The YouTube script is a SEPARATE document from the reel script. The reel script is 20-60s ElevenLabs format. The YouTube script is 8-20 minutes with production cues and chapter timestamps. Do not confuse them.

---

## Workflow (compact)

Phases: 0 source-brief → 0b theme-factory → 1 reel-script → 2 ingest-voice → 2b script-reconcile → 3 beat-map → 3b caption-polish → 4 capture-demo → 4b shot-list (i/ii/iii) → 4c motion-intent → 4d asset-prep → 5 assemble-reel → 6 qa-reel → 7 render

11 approval gates. See `.claude/rules/gate-enforcement.md` for the full gate-to-skill mapping.

Pipeline tools:
- Preflight:  `python -m lib.phase check <skill> projects/<slug>`
- Postflight: `python -m lib.phase post <skill> projects/<slug>`
- Health:     `python -m lib.phase status projects/<slug>`
- Validate:   `python -m lib.validate projects/<slug>`
- Gates:      `python -m lib.gates status projects/<slug>`
- Components: `python -m lib.components check <Name>`
- Assets:     `python -m lib.assets <verb>` — see "Asset Sourcing" section below
- Preview:    `python -m lib.preview_beats projects/<slug>` — render one frame per editorial beat (run during Phase 5 assembly, not just at the end)
- Edit plan:  `python -m lib.edit_plan {validate,compile,summary,parity}` — compile edit-plan.json into timeline.json deterministically

Vendored component libraries (check before building anything new):
- `remotion/src/components/effects/clippkit/` — clippkit (MIT). BarWaveform, CircularWaveform, GlitchText, TypingText, ToastCard. See `clippkit/NOTICE.md`.
- `lib/feature_mockups/presets.json` — 12 pre-built FeatureMockup configs (sandboxing, credentials, checkpointing, tracing, monitoring, scaling, integration, performance, automation, permissions, encryption, search). `from lib.feature_mockups import preset`.

Installed npm packages with ready-made wrappers (check these before building custom components):
- `@remotion/paths` → `AnnotationCircle` (ellipse + underline draw-on). Also: `import { evolvePath } from "@remotion/paths"` for one-off SVG path animations.
- `@remotion/motion-blur` → `LogoOverlay trail={true} bounce={true}` for hook logo trail effect. Also: `import { Trail } from "@remotion/motion-blur"` for other animated elements.
- `@remotion/lottie` + `lottie-web` → `LottieOverlay` for animated brand logos (Lottie JSON). Source from LottieFiles.com or brand resources pages. Place JSON in `remotion/public/brands/`.
- `remotion-animate-text` → `CharKeyword` for single-word character-level explosion (presets: explode / rise / cascade). More punchy than `KeywordFadeIn` for 1-3 word hook emphasis.
- `@remotion/light-leaks` → `LightLeakOverlay` for cinematic scene transitions. Use inside `TransitionSeries.Overlay`. `hueShift` matches brand color. Max 1 per reel (same flash budget as FlashReset).

## Asset Sourcing (lib.assets)

Free, programmatic asset sourcing across the pipeline. Every fetched asset is
tracked in `projects/<slug>/assets/sourced/catalog.json` with provenance
(source, query, license, attribution requirements).

### Sources

| Source | Type | License | API key | Best for |
|---|---|---|---|---|
| **lobehub** | AI/LLM brand SVGs (300+ brands) | MIT | none | Anthropic, Claude, OpenAI, Gemini, Notion, etc. — extracted from `@lobehub/icons` npm package |
| **simpleicons** | SaaS brand SVGs (3,400+ brands) | CC0 | none | Notion, Asana, Slack, Rakuten, Atlassian, GitHub, etc. via `cdn.simpleicons.org` |
| **pexels** | Stock video + image API | Pexels License (no attribution) | `PEXELS_API_KEY` | Generic tech b-roll, AI footage |
| **pixabay** | Stock video + image API | Pixabay License (no attribution) | `PIXABAY_API_KEY` | Generic tech b-roll, alt to Pexels |
| **coverr** | Cinematic stock video API | Commercial, **attribution required** | `COVERR_API_KEY` | Cinematic AI/abstract b-roll |
| **youtube** | Source video + transcript + frames via yt-dlp | Source-dependent (always attribute) | none | Official product demo videos, source research |

### CLI

```bash
# Brand logos — no API key needed
python -m lib.assets brand notion --color 000000 --project <slug>
python -m lib.assets brands Notion Asana Rakuten --project <slug>      # SaaS via Simple Icons
python -m lib.assets ai-brand Anthropic --project <slug>               # AI via LobeHub
python -m lib.assets ai-brands                                          # list all available

# YouTube source — no API key needed (yt-dlp + ffmpeg)
python -m lib.assets youtube fetch <url> --project <slug> --frames-every 5
python -m lib.assets youtube transcript <url> --out transcript.txt

# Stock footage — needs API keys in .env
python -m lib.assets pexels search "ai data center" --orientation portrait --download --project <slug>
python -m lib.assets pixabay search "code terminal" --download --project <slug>
python -m lib.assets coverr search "ai abstract" --download --project <slug>

# Catalog
python -m lib.assets catalog projects/<slug>          # summary + full asset list
python -m lib.assets attribution projects/<slug>      # only assets requiring credits
```

### Required setup

**For LobeHub** (AI brand SVG extraction):
```
cd remotion && npm install @lobehub/icons
```

**For YouTube** (source video download):
```
python -m pip install -U yt-dlp
```

**For Pexels / Pixabay / Coverr** (free API keys):
- Pexels: https://www.pexels.com/api/  → set `PEXELS_API_KEY` in `.env`
- Pixabay: https://pixabay.com/api/docs/  → set `PIXABAY_API_KEY` in `.env`
- Coverr: https://coverr.co/developers  → set `COVERR_API_KEY` in `.env`

See `.env.example` for the full template.

### When to use lib.assets in the workflow

| Phase | Use case |
|---|---|
| **0 source-brief** | If source URL is YouTube → `python -m lib.assets youtube fetch <url> --project <slug>` for transcript + frames |
| **1b broll-pipeline** | Alternative to NotebookLM cinematic — search Pexels/Pixabay/Coverr for relevant b-roll |
| **4 capture-demo** | Pre-fetch tool/brand logos via `brand` / `ai-brand` before scraping favicons |
| **4b-i visual assignment** | Reference `python -m lib.assets catalog <slug>` when assigning visuals to beats |
| **Pre-publish** | Run `python -m lib.assets attribution <slug>` to gather credit lines for the description / pinned comment |

### Provenance + attribution

All fetched assets are recorded in `projects/<slug>/assets/sourced/catalog.json`
with: source, query, license, attribution_required, attribution_text, timestamp,
metadata. Before publishing a reel, run `attribution` to list every asset that
requires credit (Coverr videos, YouTube source clips) and add them to the post
description or pinned comment. Failing to credit attribution-required assets is
a publishing-readiness blocker, not just a courtesy.

---

## Content Scope

One main idea, up to three support points, one clear takeaway. Reduce scope before generating assets.

## Beat Intents

hook, setup, proof, demo, mechanism, trust, recap, CTA. Do not invent unnecessary types.

## Editing Philosophy

- Hook lands in first 1-3 seconds; proof before or during explanation
- Avoid long flat demo sections; use punch-ins, crops, overlays for momentum
- SFX supports emphasis, not distraction; avatar supports, not dominates
- Do not hide important UI behind captions; do not use b-roll as fake proof
- CTA should feel earned

---

## Style Profiles

Set `style` in `project.json`: `cinematic-presenter` (default), `editorial-authority`, or `proof-escalation-editorial`.
See `.claude/rules/style-profiles.md` for the selector and `styles/` for full specs.

## Renderer

Remotion. Preview: `cd remotion && npx remotion studio`. Render: `cd remotion && npx remotion render ReelComposition --output out/reel.mp4`

- `ReelComposition` = **GenericReelComposition** (default) — data-driven from timeline.json
- `LegacyReel` = old hardcoded composition — use only for projects with custom inline components
- Pre-render check: `python -m lib.preflight_render projects/<slug>`
- GPU-friendly only: transform, opacity, clipPath. No blur.
- All OffthreadVideo must be muted
- Load remotion-best-practices rules before any Remotion code change
- Read component `.tsx` source before using it in composition
- Overlay registry in GenericReelComposition.tsx — add new overlay types there

## Claude Behavior

- Prefer simplest robust V1 path; avoid overengineering
- Keep files explicit and traceable; preserve human review points
- Never skip validation; stop at phase gates
- Summarize what was created, checked, and still blocked before moving on
