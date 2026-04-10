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
