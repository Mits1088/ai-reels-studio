# Cinematic Presenter

**Style ID:** `cinematic-presenter`
**Status:** Default — all existing projects use this style.

## Feel

Smooth, premium, avatar-anchored. The presenter is the throughline. Demos and proof moments punctuate the delivery. Transitions are invisible. Motion is restrained.

## When to Use

- Feature deep-dives where the avatar walks through a product
- Tutorial-style demos showing step-by-step workflows
- Single-tool showcases with extended screen recordings
- Reels where presenter trust and connection matter

## Pacing

- **Visual change frequency:** every 3-5 seconds
- **Typical duration:** 30-55 seconds
- **Beat density:** 8-14 beats
- **Word density:** moderate (140-160 wpm spoken)
- **Hold time:** up to 3s; ambient drift only when the hold is >2.0s and has a named focal point

## Avatar Behavior

- Avatar is the anchor — visible 60-70% of the reel
- Split-screen is the primary layout (avatar bottom 60%, content top 40%)
- Center-full moments hide the avatar briefly for key demos
- Avatar re-entry is deliberate (scale settle 1.05 → 1.00)
- No more than 4 consecutive center-full entries without face return

## Transition Defaults

| Context | Enter | Exit | Duration |
|---|---|---|---|
| Demo entry | `wipe-up` | `fade` | enterDur: 5, exitDur: 3 |
| Avatar beat | `fade` | `fade` | enterDur: 3, exitDur: 2 |
| B-roll | `fade` or `zoom-in` | `fade` | enterDur: 4, exitDur: 3 |
| Overlay | `scale-pop` | `fade` | enterDur: 4, exitDur: 2 |
| CTA | `punch` | hold | enterDur: 4 |

**Variety rule:** max 2 consecutive entries with same enter preset.
**Consistency rule:** max 3 transition types per reel.

## Typography

- Caption: Inter/system-ui, bottom safe zone, rounded gray boxes
- KeywordFadeIn: staggered word fade, product brand color, top zone
- NumberPopup: colored badge with spring pop-in, 1.0-1.5s hold
- All text stays below hero typography scale (max ~48px for overlays)

## Background Mapping

| Scene type | Background |
|---|---|
| Hook split-screen | AuroraBackground (white) |
| Split-screen demo | AuroraBackground (white) |
| Center-full demo/broll | AuroraBackground + BackgroundBeams (white #FAFAFA) |
| Avatar CTA/outro | GradientMesh + SmokeWisp + FocusVignette (dark) |

**Rule:** white backgrounds for demos, dark only for CTA/outro.

## Motion Language

Motion grammar rules: see `.claude/rules/motion-grammar.md` for the full doctrine, four motion modes, anti-patterns, and beat-level examples.

- **1 hero + 1 support + 1 accent per beat** (strict)
- **Stillness is the default for body beats** — calm, confident framing. Not every beat needs drift.
- **Ambient motion is opt-in**, not assumed. Apply only when hold >2.0s, there is a named focal point, and no other motion fires.
- **Motivated zoom** requires pre-defined coordinates from Phase 4b-iii. Zoom reflex (zooming because the shot is static) is an anti-pattern.
- **Do not stack** `zoom-in` entry preset + ambient drift hold on the same beat.
- **Scale settle** on avatar re-entry
- **Hook motion** may be stylized (bouncing logo, Ken Burns push toward hero element) — body beats do not inherit hook energy
- **Flash accent:** max 1 per reel
- **Gap ownership:** required for all speech pauses
- **Background seams:** 8-12 frame opacity crossfade

## SFX Behavior

- Subtle, supportive, never dominant
- Soft clicks and slides preferred over sharp pops
- Every layout change must have SFX
- Minimum 6-8 SFX entries per reel
- Volume levels explicit per entry

## Display Modes

| Mode | When |
|---|---|
| Split-screen (default) | Standard presenter + screenshot |
| Responsive | Hook opening with landscape content |
| Center-full | Key demo video or cinematic b-roll |
| Full-screen | Avatar-only direct address |

## Component Decision Guide

See `.claude/rules/component-mapping.md` for the full universal guide.

### Core principle

**The avatar is the anchor.** Content shares the frame with the face via split-screen. Full-screen content is reserved for short proof bursts only (3-5 seconds max before face return).

### Component preference order

| Narration type | First choice | Second choice | Avoid |
|---|---|---|---|
| Emotional keyword | KeywordFadeIn (split-screen top zone) | NumberPopup | HeroTextCard (too aggressive for this style) |
| Staccato claim | KeywordFadeIn or BadgePopup | — | Full-screen text cards |
| Name reveal | KeywordFadeIn with glow | BadgePopup | HeroTextCard |
| Number + proof | Split FramedImage + NumberPopup | — | Full-screen chart without avatar |
| Explanation + visual | Split FramedImage + avatar | — | Center-full without face |
| Direct address | AvatarVideo full-screen | — | — |
| Trust/credibility | Split FramedImage + BadgePopup | — | — |
| Contradiction | StrikethroughSwap | — | OverlayKeyword (too editorial) |
| Hook opening | Hook-reveal (avatar springs down, visual reveals above) | Responsive split | Solid color cards |
| CTA | AvatarVideo full-screen (dark bg) | — | Text overlay on face (too editorial) |
| Demo video | Center-full BRollVideo (short burst) | Split-screen | Long unbroken center-full runs |

## Existing Components (all available)

GradientMesh, SmokeWisp, FocusVignette, AuroraBackground, BackgroundBeams,
AvatarVideo, BRollVideo, FramedImage, ImageLayer, Caption, NumberPopup,
KeywordFadeIn, BadgePopup, PunchInZoom, CardStack, StrikethroughSwap,
TypingInput, IconOrbit, SourceProofCard, SceneBreak, AnimatedDivider,
ShimmerBar, GlowBorder, NoiseOverlay, StackedImageReveal, TransitionWrapper
