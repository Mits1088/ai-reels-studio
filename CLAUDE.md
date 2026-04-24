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

## Creative Direction (read before style rules)

Before applying any style-profile defaults, visual-style rules, motion-intent choices, or component mapping, read these five files in order:

1. `docs/creative-direction.md` — authorship identity, hook philosophy, anti-patterns, what premium/boring/too-much-zoom means
2. `memory/creative-feedback.json` — accumulated human taste signal: hard rules, soft preferences, component guidance
3. `training/derived/taste-rules.json` — third-person patterns extracted from liked reference reels; hook archetypes, proof ordering, body patterns, anti-patterns. Check `_confidence` — LOW confidence is suggestive only; `creative-feedback.json` wins when they conflict unless confidence is HIGH.
4. `.claude/rules/hook-grammar.md` — the fixed hook identity (what stays stable across all reels in the first 2–3 seconds)
5. `.claude/rules/body-grammar.md` — post-hook variety rules (min variety, repetition limits, pattern interrupts, motion language)

Files 1–3 define *what to make*. Files 4–5 define *how the structure enforces creative consistency vs. variety*. Technical rules below define *how to implement it*.

When taste conflicts with a rule: **favor taste over style defaults** (component defaults, visual-style defaults, motion-intent presets, body-grammar limits) — document the override in the shot list. Do NOT override timing-sync, gate enforcement, QA safety, or asset-validity rules — those have production consequences that creative intent cannot compensate for. See `docs/creative-direction.md` → "On the Relationship Between Rules and Taste" for the full scope.

**When reading `memory/creative-feedback.json` before a planning phase**, extract:
- `hard_rules` — non-negotiable constraints that block component/motion choices without override
- `soft_preferences` — defaults that can be overridden with a documented justification in the shot list
- `components_to_use_more` / `components_to_use_less` — these have real weight in component scoring, not just advisory guidance
- Recent `feedback_log` entries (last 3-5) — recent taste evolution may have shifted preferences since earlier entries were written
- Also read `projects/<slug>/output/review-feedback.md` if it exists — project-specific signals from this project's earlier review rounds

**When reading `training/derived/taste-rules.json` before scripting, shot-listing, or motion-intent**, check:
- `hook_patterns` — before writing the hook or selecting a hook archetype
- `proof_patterns` — before ordering proof segments in the shot list
- `body_patterns` and `motion_patterns` — before motion-intent and component mapping
- `anti_patterns` — before finalizing any section to confirm you're not repeating a documented failure mode
- `_confidence` — if LOW, treat as inspiration only; if HIGH, treat as validated guidance on par with `soft_preferences`

**Confidence constraints (read `_usage_constraints` in the file for the full rules):**
- LOW confidence: these rules may influence candidate ranking and suggest hook angle alternatives — they must not override `creative-feedback.json` entries, establish a default hook or body template, or block a choice that `creative-feedback.json` permits
- MEDIUM confidence: may also inform soft preference defaults when `creative-feedback.json` is silent on the topic
- HIGH confidence: treated on par with `soft_preferences` in `creative-feedback.json` where not contradicted

**Per-rule provenance**: every entry in `taste-rules.json` carries `evidence_type` (human_annotation / machine_inferred / mixed), `source_example`, and `reference_strength`. Prefer entries with `evidence_type: "human_annotation"` and `reference_strength: "strong"` over machine-inferred entries when making planning decisions. `machine_inferred` entries are structural guesses, not confirmed taste.

When presenting a plan, briefly note 1-2 ways it applies prior feedback. Do not narrate the full memory read — the signal that feedback is being used should be visible in the choices.

**After any major human review round**, suggest running `feedback-capture` to classify and store the reviewer's comments. Use the review template at `projects/_shared/review-feedback-template.md` to structure the session if the reviewer wants prompts.

---

## Creative Intent Summary

**Required before:** reel-script, shot-list (Phase 4b-i), motion-intent, and assembly when the timeline structure materially changes (new beat layout, major component revision, new proof method).

Before beginning any of these phases, produce a 6-field Creative Intent Summary and wait for user confirmation before proceeding. This forces synthesis before execution and creates a reviewable planning layer — the summary must demonstrate that Claude understands the specific creative problem before producing anything.

### Template

- **Creative problem:** What specific tension or gap does this work need to resolve?
- **Stability to preserve:** What must not change — hook identity, validated body patterns, confirmed feedback choices
- **Change to pursue:** The specific targeted change, and why it improves the reel
- **Main risk:** Which past mistake, feedback entry, or known failure mode is most likely to recur here
- **Key signals:** Confirmed feedback entries (hard_rules / soft_preferences) most relevant; taste-rules named as tie-breaks only (never blockers)
- **Success criteria:** What QA would flag if this goes wrong; what the reviewer would say if it goes right

### Anti-fluff rule

Every field must name something specific: a component, a beat ID or range, a feedback entry, a visual role type. Any line that could describe any reel fails the test and must be rewritten before proceeding.

| Bad (too vague — do not write this) | Good (specific — write this instead) |
|---|---|
| "Make it more engaging." | "Replace beats 04–06 text-emphasis streak with AnnotationCircle + center-full demo. Breaks 5-consecutive role run." |
| "Apply creative feedback." | "`creative-feedback.json` hard_rule: OverlayKeyword max 3 uses. Currently at 4 — beat-06 overlay must become a proof visual." |
| "Keep the hook strong." | "Preserve Split-Proof archetype A: LogoOverlay + FramedImage + AvatarVideo split. Product screenshot stays unchanged." |

### Zone rule

The summary must distinguish hook scope from body scope. Changes to the hook require explicit justification for altering the brand signature. Body zone changes do not require hook justification — but must name the beat range affected.

### Example — body revision after QA flags text-emphasis streak

**Creative problem:** 5 consecutive text-emphasis beats (04–08) — QA blocked on `text-emphasis-domination` gate. Fake variety: 5 different component names, 1 visual role.
**Stability to preserve:** Split-Proof hook (archetype A) unchanged. Avatar layout sequence (split → full → split) approved at Phase 4b-i — do not alter. CTA structure validated.
**Change to pursue:** Replace beat-06 OverlayKeyword with AnnotationCircle on benchmark screenshot. Replace beat-07 KeywordFadeIn with FramedImage center-full. Net: text-emphasis drops to 37% of body beats; `proof-display` and `annotation-focus` each gain one beat.
**Main risk:** Repeating text-only proof. `creative-feedback.json` soft_preference: image-dominant proof beats preferred over text-only whenever evidence exists. Beat-06 already has a benchmark screenshot — another overlay is a regression.
**Key signals:** [hard_rule] OverlayKeyword max 3 uses — beat-05 is use 3, beat-06 must change. [soft_preference] Annotation when narrator names a specific element. [taste-rule LOW] Benchmark charts read better with zoom — used as zoom coordinate direction only, not a design blocker.
**Success criteria:** QA `text-emphasis-domination` gate passes (consecutive streak ≤ 2). Reviewer finds visible evidence per claim in the middle section. AnnotationCircle on benchmark gives viewer a specific element to track.

---

## Rule Hierarchy

1. `docs/creative-direction.md` ← **read first — authorship identity**
2. `memory/creative-feedback.json` ← **read second — accumulated taste signal**
3. `training/derived/taste-rules.json` ← **read third — patterns from liked reference reels (check `_confidence`)**
4. `.claude/rules/hook-grammar.md` ← **hook structure — what stays stable**
5. `.claude/rules/body-grammar.md` ← **body structure — variety rules and motion language**
6. `.claude/rules/reel-workflow.md`
7. `.claude/rules/gate-enforcement.md`
8. `.claude/rules/change-pipeline.md`
9. `.claude/rules/timing-sync.md`
10. `.claude/rules/qa-gates.md`
11. `.claude/rules/visual-style.md`
12. `.claude/rules/style-profiles.md`
13. `.claude/rules/component-mapping.md` (candidate sets) + `.claude/rules/component-selection-scoring.md` (scoring criteria)
14. `.claude/rules/motion-grammar.md` — motion modes, anti-patterns, stillness doctrine (read before Phase 4c)
15. `.claude/rules/demo-capture-strategy.md`
16. `.claude/rules/remotion-skill-required.md`
17. `.claude/rules/reel-learning.md` — post-render learning (see also: `feedback-capture` skill for in-production review feedback)
18. `.claude/rules/template-grammar.md` (when style is `proof-escalation-editorial`)
19. `.claude/skills/*/SKILL.md`
20. `CLAUDE.md`

`visual-style.md` provides rendering defaults (display modes, backgrounds, zoom coords). `hook-grammar.md` governs the first 2–3s. `body-grammar.md` governs everything after. `assemble-reel` may override display choices by beat intent when retention or presenter anchoring is stronger.

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

Phases: 0 source-brief → 0b theme-factory → 1 reel-script → 2 ingest-voice → 2b script-reconcile → 3 beat-map → 3b caption-polish → 4 capture-demo → 4b shot-list (i/ii/iii) → 4c motion-intent → 4d asset-prep → 5 assemble-reel → **5b quick preview [→ feedback-capture]** → 6 qa-reel **[→ feedback-capture]** → 7 render **[→ feedback-capture + reel-learning]** → **7b publish-prep** (Instagram caption + posting checklist — mandatory after every render)

11 approval gates. See `.claude/rules/gate-enforcement.md` for the full gate-to-skill mapping.

**Feedback capture triggers** — suggest running `feedback-capture` after:
- Phase 5b (quick preview): user's first impressions of the assembled cut
- Phase 6 (QA review): any editorial observations beyond technical blockers
- Phase 7 (render): final impressions before publishing
- Any revision round: user watches the revised cut and comments on whether it improved

See `.claude/skills/feedback-capture/SKILL.md` for the full classification and memory update process. Use `projects/_shared/review-feedback-template.md` to prompt structured feedback from the reviewer.

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

Set `style` in `project.json`: `cinematic-presenter` (default), `editorial-authority`, `proof-escalation-editorial`, or `image-showcase`.
See `.claude/rules/style-profiles.md` for the selector and `styles/` for full specs.

**`image-showcase`** — use when the creator has 8+ output images and the images ARE the proof (AI image models, design tools, visual capability showcases). Overrides avatar-led defaults: ≤25% avatar presence, gallery-dominant layout, VIDEO-FIRST suspended for gallery beats, neutral white backgrounds.

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
