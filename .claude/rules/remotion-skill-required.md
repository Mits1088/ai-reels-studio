---
description: Mandatory rule — load remotion-best-practices before any Remotion code change
globs: ["remotion/**"]
---

# Remotion Best Practices Skill — Mandatory

## Rule

Before writing or modifying ANY Remotion code, the `remotion-best-practices` skill MUST be invoked and the relevant rule files loaded.

This is non-negotiable. No exceptions.

## When this applies

- Creating or editing components in `remotion/src/components/`
- Updating `ReelComposition.tsx`
- Updating `Root.tsx`
- Building or modifying `timeline.json`
- Adding new dependencies to the Remotion project
- Debugging Remotion rendering issues
- Any work that touches files inside `remotion/`
- **Mid-session changes** — even if skills were loaded earlier in the session, load them again before each code change. Context from an earlier invocation does not carry forward reliably.

## Read component source before using

Before modifying how a component is used in `ReelComposition.tsx`:

1. **Read the component's `.tsx` file** — note its props interface (what it accepts, what types)
2. **Note its internal positioning** — does it position itself, or does the parent?
3. **Note its z-index** — where does it sit in the stacking order?
4. **Note its container sizing** — does it use internal padding, aspect ratio constraints, or borders?
5. **Cross-reference with AvatarVideo.tsx** — if split-screen content, confirm the container height matches the avatar's boundary (`bottom: 0, height: 60%` → content must be `height: 40%`)
6. **THEN write the JSX**

Failure to read component source causes: wrong prop names (TypeScript errors), wrong positioning (visual bugs), wrong container sizing (white gaps), and wrong z-index stacking (elements covering each other).

## How to comply

1. Invoke the `remotion-best-practices` skill via the Skill tool
2. Read the SKILL.md index to identify which rule files are relevant
3. Load the specific rule files for the work being done
4. Only then begin writing or modifying code

## Minimum rule files per task

| Task | Required rule files |
|---|---|
| Assembly (Phase 5) | sequencing, animations, transitions, sfx, audio, images, videos, timing |
| New component | animations, timing, text-animations, fonts |
| Caption work | subtitles, display-captions |
| Video embedding | videos, trimming |
| Audio/SFX | audio, sfx |
| Debugging | animations, sequencing, can-decode |
| Charts/data viz | charts, animations |

## Why

The Remotion rule files contain patterns, restrictions, and best practices that prevent common bugs:
- CSS animations are FORBIDDEN in Remotion (must use useCurrentFrame)
- Images must use `<Img>` from remotion, not native `<img>`
- Videos must use `<Video>` from @remotion/media
- Sequences must use `premountFor` for smooth rendering
- Spring configs affect timing behavior

Skipping these rules leads to rendering failures, flickering, and anti-patterns that are hard to debug later.
