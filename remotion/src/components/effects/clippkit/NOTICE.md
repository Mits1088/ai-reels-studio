# clippkit (vendored)

The components in this directory are adapted from **clippkit** — a free,
open-source collection of Remotion video components and effects by the
team at [reactvideoeditor.com](https://www.reactvideoeditor.com).

- Source: https://github.com/reactvideoeditor/clippkit
- License: MIT
- Path in upstream repo: `apps/docs/registry/default/components/`

## Vendored components

| File | Upstream source |
|---|---|
| `BarWaveform.tsx` | `bar-waveform.tsx` |
| `CircularWaveform.tsx` | `circular-waveform.tsx` |
| `GlitchText.tsx` | `glitch-text.tsx` |
| `TypingText.tsx` | `typing-text.tsx` |
| `ToastCard.tsx` | `toast-card.tsx` |

## Adaptations made

Each vendored file has the following changes from upstream:

1. **Named export** instead of `export default function` — matches our
   project convention so `OVERLAY_REGISTRY` lookups work.
2. **Theme defaults** — replaced `var(--foreground)` / `var(--card)` /
   `var(--border)` CSS variables with explicit Claude theme colors
   (`#D97757` coral, `#FAF9F5` warm beige, `#1A1A1A` dark, `#FFFFFF`
   white) so they render correctly without a CSS variable provider.
3. **AbsoluteFill wrapping** — every component now wraps its output in
   an `AbsoluteFill` so it self-positions when used as an overlay entry
   in the `OVERLAY_REGISTRY` (which renders each overlay inside an
   AbsoluteFill with `zIndex: 20`).
4. **Determinism fix in GlitchText** — replaced `Math.random()` with
   Remotion's `random()` (seeded by frame) so renders are reproducible.
5. **`durationInFrames` derivation in ToastCard** — when the OVERLAY_REGISTRY
   passes a single `durationInFrames`, the ToastCard now auto-derives
   entry / visible / exit durations from it as 20% / 65% / 15%.
6. **Position props** — added optional `position: "top" | "center" | "bottom"`
   and `paddingY` to BarWaveform and TypingText so they can sit at any
   vertical position without external positioning wrappers.

## Components NOT vendored (yet)

The following clippkit components were intentionally not vendored — they
either duplicate existing project components or are lower priority for
the AI Reels Studio pipeline:

- `popping-text.tsx` — duplicates `OverlayKeyword`
- `sliding-text.tsx` — duplicates `KeywordFadeIn`
- `floating-card.tsx` — could replace `HeroTextCard` for some uses
- `card-flip.tsx` — niche, useful for proof reveal moments
- `linear-waveform.tsx` — third waveform style; bar + circular cover most cases
- `bar-loader.tsx`, `circular-loader.tsx`, `screen-loader.tsx` — useful for
  "agent processing" mockups but currently no beat needs them

To vendor any of these later, fetch from
`https://raw.githubusercontent.com/reactvideoeditor/clippkit/main/apps/docs/registry/default/components/<filename>`
and adapt following the same 6-step process above. Update this NOTICE.

## Attribution

Per the MIT license, no public attribution is required when using these
components in rendered output. The original authors note in their file
headers: *"Credit appreciated but not required."*

If you publish a reel that prominently uses one of these components and
want to credit the original authors, mention `clippkit` and link to
[reactvideoeditor.com](https://www.reactvideoeditor.com) in the post
description.
