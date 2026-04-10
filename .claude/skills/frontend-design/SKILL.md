---
name: frontend-design
description: Design principles for building distinctive Remotion components. Use when creating new visual components, refining existing ones, or when any component looks generic. Guides typography, color, motion, and spatial composition decisions for vertical reel content.
---

# Frontend Design Skill (Remotion Adaptation)

This skill guides creation of distinctive, production-grade Remotion components that avoid generic "AI slop" aesthetics. Every component should feel intentionally designed for 1080x1920 vertical mobile viewing.

Adapted from Anthropic's frontend-design skill for Remotion's frame-driven React video engine.

## When to Use

- Creating a new Remotion component (effects, overlays, backgrounds, mock UIs)
- Refining an existing component that looks generic or flat
- Deciding typography, color, or motion treatment for a reel scene
- Building animated mock UI components (TypingInput, SourceProofCard, etc.)

## Design Thinking for Reels

Before coding any component, answer:
- **Purpose**: What editorial job does this component serve? (proof, hook, trust, CTA support)
- **Tone**: What feeling should it create? (premium, urgent, clean, playful, authoritative)
- **Mobile-first**: Will this read clearly at 1080x1920 on a phone? (minimum touch-readable text: 18px)
- **Differentiation**: What makes this feel designed, not default?

## Typography Rules for Reels

### DO:
- Use **system-ui** as the base — it renders natively on every device
- Use **weight contrast** for hierarchy: 900 for hero words, 400 for context
- Use **size contrast** for emphasis: hero word 3-4x larger than supporting text
- Use **Inter** for clean UI text (inputs, badges, labels)
- Use **Georgia** or **serif** for editorial emphasis moments

### DON'T:
- Use exotic web fonts that might not load in Remotion renders
- Use fonts below 16px — unreadable on mobile
- Use more than 2 font families per reel
- Use identical weight/size for everything — creates visual monotony

### Kinetic typography (from reference analysis):
- Hero word fills center of frame (48-72px, weight 900)
- Context words sit above/below at 18-24px, weight 400
- Words appear with spring animation, not static placement

## Color Rules for Reels

### Product-aligned palettes:
When showing a product, use its brand colors as accent:
- **Claude**: `#D97757` (coral), `#E8B88A` (gold), `#FAF9F5` (cream bg)
- **Google**: `#4285F4` (blue), `#34A853` (green), `#FBBC04` (yellow), `#EA4335` (red)
- **ChatGPT**: `#10A37F` (green), `#343541` (dark bg)

### Scene color rules:
- Demo scenes: white/light backgrounds (`#FFFFFF`, `#FAFAFA`, `#F5F5F5`)
- Source proof cards: dark backgrounds (`#1A1A1A`, `#0A0A0A`)
- CTA/outro: dark gradient mesh backgrounds
- Never use purple gradients on white — the most generic AI aesthetic

### Contrast requirements:
- Text on light bg: minimum `#333333` (not gray, not light)
- Text on dark bg: `#FFFFFF` or `#F0F0F0`
- Accent elements: use the product's primary brand color

## Motion Rules for Remotion

### ALWAYS frame-driven:
```tsx
const frame = useCurrentFrame();
const { fps } = useVideoConfig();
// Use interpolate() and spring() — NEVER CSS keyframes or framer-motion
```

### Spring configs by intent:
| Intent | damping | stiffness | mass | Feel |
|---|---|---|---|---|
| Gentle settle | 14-18 | 120-160 | 0.8 | Smooth arrival |
| Pop/punch | 8-12 | 200-300 | 0.6 | Snappy entrance |
| Soft float | 20-30 | 80-100 | 1.0 | Ambient drift |
| Heavy land | 16-20 | 180-220 | 1.2 | Weighty impact |

### Motion hierarchy (from motion-intent rules):
- 1 hero motion per beat (the primary visual event)
- 1 support motion (secondary reinforcement)
- 1 accent (micro-event tied to emphasis word)
- Never exceed 3 simultaneous motion elements

### Staggered entrances:
When multiple elements enter (icons, cards, list items):
```tsx
const staggeredScale = spring({
  frame: Math.max(0, frame - (index * staggerDelay)),
  fps,
  config: { damping: 12, stiffness: 180, mass: 0.8 },
});
```
Delay: 2-4 frames between elements. Never all-at-once.

## Spatial Composition for 1080x1920

### Layout zones:
```
┌──────────────────┐
│    Top safe       │ ← 80px from top (platform UI)
│                   │
│   Content zone    │ ← Primary visual area
│    (center)       │
│                   │
│   Avatar zone     │ ← Bottom 60% when split-screen
│                   │
│  Caption zone     │ ← Bottom 200px (safe for captions)
│  Bottom safe      │ ← 100px from bottom (platform UI)
└──────────────────┘
```

### Key dimensions:
- Full width: 1080px
- Full height: 1920px
- Split-screen divider: 40% top / 60% bottom (768px / 1152px)
- Caption safe zone: y > 1620px
- Top badge safe zone: y < 160px
- Horizontal padding: 24-40px from edges

## Article Screenshot Highlight Technique

When a reel shows an article, research page, or headline screenshot and specific words need visual emphasis:

1. **OCR positioning**: Use `tesseract <image> output --psm 6 tsv` to extract word bounding boxes. Convert pixel positions to percentages for responsive overlay placement.
2. **Highlight wipe**: Use Remotion's spring-based `scaleX` wipe (NOT rough.js or CSS). Highlight bar renders behind text at `zIndex: 0`, text at `zIndex: 1`. See `remotion/.agents/skills/remotion-best-practices/rules/assets/text-animations-word-highlight.tsx` for the reference implementation.
3. **Subtle 3D Ken Burns**: `transform: perspective(1200px) scale() rotateY() rotateX()` driven by `interpolate()`. Keep total rotation ~15deg per axis. Makes the article feel examined, not spinning.
4. **Reveal**: Use `opacity` fade-in (0→1 over 1s). NOT blur — blur kills GPU performance.
5. **Multiple highlights**: Stagger start frames (e.g. 1.5s apart) so each phrase wipes independently.

Full technique reference with code examples: `templates/article-highlight-technique.md`

## Component Quality Checklist

Before shipping any Remotion component:
- [ ] Uses `useCurrentFrame()` + `interpolate()` / `spring()` — no CSS animations
- [ ] Readable at 1080x1920 on mobile (text ≥ 16px)
- [ ] Has entrance animation (spring or interpolate)
- [ ] Has exit animation (opacity fade or scale)
- [ ] Uses product-aligned colors when applicable
- [ ] Does not use `filter: blur()` (GPU performance)
- [ ] Uses `transform` and `opacity` only for animations (GPU-friendly)
- [ ] Has TypeScript props interface with sensible defaults
- [ ] Works within Remotion's `<Sequence>` timing system
