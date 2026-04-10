---
description: Style profile selector — cinematic-presenter vs editorial-authority defaults and overrides
globs: ["**/project.json", "**/shot-list.md", "**/motion-intent.md"]
---

# Style Profiles

## Purpose

Every reel project selects a **style profile** that controls motion language, transition defaults, typography scale, background treatment, and pacing density. The style is set in `project.json` and read by every downstream phase.

## Available Styles

| Style | ID | Feel | Best for |
|---|---|---|---|
| Cinematic Presenter | `cinematic-presenter` | Smooth, premium, avatar-led | Feature demos, product deep-dives, tutorials |
| Editorial Authority | `editorial-authority` | Fast, punchy, proof-led | Listicles, comparisons, news, claim-and-prove |
| Proof Escalation Editorial | `proof-escalation-editorial` | Template-driven, proof-escalation arc | Product launches, capability showcases, feature announcements |

## How to Select

Set the `style` field in `project.json`:

```json
{
  "slug": "my-reel",
  "style": "editorial-authority",
  ...
}
```

If `style` is omitted, the default is `cinematic-presenter` (backward compatible with all existing projects).

## Where Style Affects the Pipeline

| Phase | What changes |
|---|---|
| reel-script | Hook style, pacing target, word density |
| shot-list | Display mode defaults, visual assignment patterns |
| motion-intent | Preset vocabulary, transition defaults, timing |
| assembly | Default transitions, background mapping, overlay behavior |
| QA | Pacing density thresholds, visual variety minimums |

## Style Profile Docs

Full specs live in `styles/`:

- `styles/cinematic-presenter.md` — current default style
- `styles/editorial-authority.md` — fast editorial style
- `styles/proof-escalation-editorial.md` — template-driven proof escalation style

## Rule Interaction

Style profiles provide **defaults** for `cinematic-presenter`. For `editorial-authority`, the style file is an **explicit override mode** — see `styles/editorial-authority.md` for its precedence block.

### cinematic-presenter (default)

Does not override baseline rules. Works within them:
1. Beat-intent overrides from `assemble-reel` skill (these still win)
2. Explicit per-entry `transition_preset` values in timeline.json
3. QA blocking rules (these apply to all styles)

### editorial-authority (override mode)

When active, `styles/editorial-authority.md` **overrides** baseline visual-style, QA thresholds, and motion defaults where they conflict. See the precedence block in that file.

### proof-escalation-editorial (template-driven mode)

When active, this style uses **layout templates** instead of per-component selection. The template registry (`training/derived/template-registry.json`) is the source of truth for avatar mode, split ratio, background, and caption behavior. Shot-list emits `template_id` per beat; assembly maps it to `captionMode` and `splitRatio`; QA validates against `training/derived/rhythm-bounds.json`. See `styles/proof-escalation-editorial.md` and `.claude/rules/template-grammar.md`.

### What all style profiles override (regardless of mode)

- Default transition type when no preset is specified
- Default background mapping
- Default typography scale for overlays
- Pacing density expectations
- Motion budget interpretation

## Style Activation Contract

When a style is selected, these declarations are required throughout the pipeline:

| Artifact | Required |
|---|---|
| `project.json` | `"style": "<style-id>"` |
| `shot-list.md` | Every beat tagged with broad intent + style-specific sub-class |
| `output/motion-intent.md` | Must declare `style_profile: <style-id>` at the top |
| `output/timeline.json` | Proof beats must include `"proof_protected": true/false` |
| `output/qa-report.md` | Must include a style compliance section |

If any declaration is missing, QA must flag it as a blocker.

## Adding a New Style

1. Create `styles/<style-id>.md` with the full profile spec
2. Add the ID to the `style` enum in `lib/schemas/project.schema.json`
3. Add it to the table in this file
4. Build any new components it requires in `remotion/src/components/`
5. Test on one reel before using in production
