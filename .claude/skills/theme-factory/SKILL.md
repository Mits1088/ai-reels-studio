---
name: theme-factory
description: Apply consistent product-aligned color and typography themes to reels. Use when starting a new reel to set the visual palette, or when a reel's colors feel inconsistent. Provides pre-set themes for common AI products plus custom theme generation.
---

# Theme Factory Skill (Reel Adaptation)

Apply consistent, professional color and typography themes to Instagram reels. Each theme provides a cohesive palette that drives Aurora background colors, accent tones, overlay colors, and typography choices across the entire composition.

Adapted from Anthropic's theme-factory skill for Remotion reel production.

## When to Use

- Starting a new reel — select a theme during Phase 0 or Phase 1
- A reel's colors feel inconsistent across scenes
- Building components that need product-aligned styling
- The reel covers a specific product (Claude, Google, ChatGPT) and should match its brand

## Usage

1. Identify the reel's product/topic
2. Select the matching theme (or create a custom one)
3. Apply the theme's colors to: Aurora background blobs, accent borders, NumberPopup colors, badge colors, text highlights, background gradients
4. Use the theme's typography for overlays and kinetic text

## Pre-Set Reel Themes

### Claude / Anthropic
```
Primary: #D97757 (coral)
Secondary: #E8B88A (warm gold)
Background: #FAF9F5 (cream white)
Dark BG: #1A1A1A
Accent: #CC785C (deep coral)
Aurora blobs: rgba(204,120,92,0.08), rgba(232,184,138,0.06), rgba(245,230,216,0.09)
Beams: rgba(204,120,92,0.04)
Dark mesh: rgba(204,120,92,0.20), rgba(61,37,22,0.75), rgba(45,27,20,0.60)
Headers: system-ui, weight 700
Body: system-ui, weight 400
```

### Google / Workspace
```
Primary: #4285F4 (blue)
Secondary: #34A853 (green)
Tertiary: #FBBC04 (yellow)
Quaternary: #EA4335 (red)
Background: #FFFFFF
Dark BG: #1A1A2E
Aurora blobs: rgba(66,133,244,0.06), rgba(52,168,83,0.04), rgba(251,188,4,0.05), rgba(234,67,53,0.03)
Beams: rgba(66,133,244,0.04)
Headers: Google Sans / system-ui, weight 700
Body: system-ui, weight 400
```

### ChatGPT / OpenAI
```
Primary: #10A37F (green)
Secondary: #1A7F64 (dark green)
Background: #FFFFFF
Dark BG: #343541
Accent: #10A37F
Aurora blobs: rgba(16,163,127,0.06), rgba(26,127,100,0.04), rgba(255,255,255,0.08)
Beams: rgba(16,163,127,0.04)
Headers: system-ui, weight 700
Body: system-ui, weight 400
```

### Gemini / Google AI
```
Primary: #4285F4 (blue)
Secondary: #8E24AA (purple)
Tertiary: #1E88E5 (light blue)
Background: #FFFFFF
Dark BG: #1A1A2E
Aurora blobs: rgba(66,133,244,0.06), rgba(142,36,170,0.04), rgba(30,136,229,0.05)
Beams: rgba(66,133,244,0.04)
Headers: Google Sans / system-ui, weight 700
Body: system-ui, weight 400
```

### Tech Neutral (generic AI/tech topic)
```
Primary: #0066FF (electric blue)
Secondary: #00CCFF (cyan)
Background: #FAFAFA
Dark BG: #1E1E1E
Aurora blobs: rgba(0,102,255,0.05), rgba(0,204,255,0.04), rgba(255,255,255,0.08)
Beams: rgba(0,102,255,0.04)
Headers: system-ui, weight 700
Body: system-ui, weight 400
```

## How to Apply a Theme

During assembly (Phase 5), use the theme values in:

### ReelComposition.tsx backgrounds
```tsx
<AuroraBackground colors={theme.auroraBlobs} />
<BackgroundBeams color={theme.beamsColor} />
<GradientMesh colors={theme.darkMeshColors} />
```

### NumberPopup overlays
```tsx
<NumberPopup color={theme.primary} />
```

### BadgePopup overlays
```tsx
<BadgePopup color={theme.primary} />
```

### TypingInput components
```tsx
<TypingInput style="claude" /> // Uses Claude theme automatically
<TypingInput style="google" /> // Uses Google theme automatically
```

### SourceProofCard
```tsx
<SourceProofCard highlightColor={`${theme.primary}4D`} /> // 30% opacity highlight
```

## Creating a Custom Theme

If the reel covers a product not listed above:
1. Find the product's brand guidelines (primary color, secondary, background)
2. Generate Aurora blob colors at 4-8% opacity from the primary/secondary
3. Generate beams color at 4% opacity from the primary
4. Generate dark mesh colors from darkened versions of primary (20% opacity) + near-black
5. Document the theme in `themes/<product-name>.md`

## Theme in project.json

Record the selected theme in project.json:
```json
{
  "theme": "claude",
  "theme_primary": "#D97757",
  "theme_secondary": "#E8B88A"
}
```

This allows assembly and QA to verify color consistency.
