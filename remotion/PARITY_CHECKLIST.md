# Renderer Parity Checklist

Use this when comparing `GenericReel` against `ReelComposition` in Remotion studio.

Open both compositions side-by-side, scrub to the same frames, and check each item.

## Pre-check
- [ ] Both compositions use the same timeline.json
- [ ] Both compositions show the same total duration
- [ ] Remotion studio loads both without errors

## Audio
- [ ] Narration audio plays at correct timing
- [ ] SFX fire at correct moments
- [ ] SFX volume levels match

## Avatar
- [ ] Avatar visible in correct layout (split-screen vs full-screen) at each beat
- [ ] Avatar hidden during center-full ranges
- [ ] Avatar transitions between layouts look correct
- [ ] No white gap between avatar and content in split-screen

## Backgrounds
- [ ] Dark background during full-screen avatar beats
- [ ] Light/white background during split-screen beats
- [ ] Neutral background during center-full content
- [ ] Background transitions are smooth (no hard flash)

## Demo Images (split-screen)
- [ ] Images appear at correct timing
- [ ] Images positioned in top 40% zone
- [ ] Zoom moments trigger at correct times
- [ ] Zoom targets correct regions of the image

## B-roll Videos (center-full)
- [ ] Videos play at correct timing
- [ ] Videos fill frame appropriately (contain, not crop)
- [ ] Videos are muted
- [ ] playbackRate applied if specified

## Overlays
- [ ] OverlayKeyword: text, color, fontSize, position match
- [ ] BadgePopup: text, color, size match, positioned correctly
- [ ] KeywordFadeIn: words, color, stagger timing match
- [ ] NumberPopup: number, label, color match
- [ ] No unsupported overlay types in console warnings

## Captions
- [ ] Caption text matches timeline
- [ ] Caption timing matches audio
- [ ] Captions in mobile-safe zone

## Acceptable Differences
These are known differences in the D1 spike that do NOT block parity:

- **Custom inline components**: The old renderer may have project-specific inline JSX
  (e.g. ScrollingBenchmark, HighlightRing in gemma-4). GenericReel renders the asset
  directly without the custom behavior. This is expected — custom components migrate
  to the registry in D3/D4.
- **Background subtlety**: GenericReel uses a simpler dark/light/neutral mapping.
  The old renderer may use specific hex values or Aurora/GradientMesh components.
  Color-exact parity is a D4 goal.
- **Transition animations**: GenericReel uses hard cuts as default. The old renderer
  may have specific enter/exit animations. Transition support is a D4 goal.

## Test Projects

| Project | Style | Overlays | Key test |
|---|---|---|---|
| gemma-4 | editorial-authority | OverlayKeyword, BadgePopup | Avatar layout switching, center-full broll |
| google-stitch-vibe-design | cinematic-presenter | KeywordFadeIn, BadgePopup | Demo zoom, split-screen, overlay variety |
| claude-3-setup-tips | (default) | NumberPopup, BadgePopup | Numbered list overlays, multiple overlay types |
