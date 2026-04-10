---
name: component-reference
description: Remotion component inventory, Remotion best-practices rule file lookup, pipeline skill-to-phase table, and SFX catalog reference. Use when planning visuals, selecting components, or looking up which Remotion rule to load.
disable-model-invocation: true
---

# Component & Pipeline Reference

## Remotion Component Inventory

All components live in `remotion/src/components/`. Prefer existing components over creating new ones.
Run `python -m lib.components check <Name>` to verify a component exists before using it.

### Backgrounds
GradientMesh, SmokeWisp, FocusVignette, AuroraBackground, BackgroundBeams, ImageAutoSlider

### Media
AvatarVideo, BRollVideo, FramedImage, ImageLayer

### Text & Overlays
Caption, NumberPopup, KeywordFadeIn, BadgePopup, OverlayKeyword, HeroTextCard

### Animated Mock UI
TypingInput, IconOrbit, SourceProofCard, StrikethroughSwap

### Decorative / Transitions
SceneBreak, AnimatedDivider, ShimmerBar, GlowBorder, NoiseOverlay, PunchInZoom, TransitionWrapper

### Editorial Authority
FlashReset, ComparisonGrid, CursorClick, AnnotationCircle, ChapterDivider, ScrollingIconGrid, CardStack

### Not Yet Built (use workaround)
- **StackedImageReveal** — use multiple FramedImage entries in rapid sequence (3-5 frames each)
- **ImageMontage** — same workaround as StackedImageReveal

---

## Remotion Best-Practices Rule Files

Located at `remotion/.agents/skills/remotion-best-practices/rules/`. Load the relevant file before writing Remotion code.

| Rule file | When to use |
|---|---|
| sfx.md | Adding sound effects |
| transitions.md | Scene transitions |
| audio.md | Audio import, trimming, volume, pitch |
| subtitles.md | Caption/subtitle handling |
| animations.md | interpolate, spring, easing curves |
| sequencing.md | Sequence, Series, nesting, premounting |
| timing.md | Timing curves and spring behavior |
| videos.md | Embedding and trimming video |
| text-animations.md | Text motion and typography animation |
| light-leaks.md | Light leak overlays |

---

## Pipeline Skills

| Skill | Phase | Stage |
|---|---|---|
| new-reel | init | Initialize project + input quality diagnostic |
| source-brief | 0 | Research URL → source-research.md + brief.md |
| theme-factory | 0b | Apply product-aligned color themes |
| reel-script | 1 | Write ElevenLabs-ready voiceover script |
| broll-pipeline | 1b | Split, classify, match, cut cinematic b-roll |
| ingest-voice | 2 | Import and analyze narration / avatar audio |
| script-reconcile | 2b | Diff script vs transcript, lock source of truth |
| caption-polish | 3b | Polish captions: spelling, chunking, emphasis |
| capture-demo | 4 | Capture screen/demo footage and support assets |
| shot-list | 4b | Visual assignment, component mapping, technical planning |
| motion-intent | 4c | Beat-by-beat motion direction with preset mapping |
| asset-prep | 4d | Crop, encode, validate assets for Remotion |
| assemble-reel | 5 | Compose final reel from approved artifacts |
| apply-change | 5+ | Post-assembly changes via pipeline re-entry |
| qa-reel | 6 | Validate reel before export |
| frontend-design | any | Design principles for Remotion components |

---

## SFX Catalog

The shared SFX library lives at `SFX/` with an index at `SFX/catalog.json`.

Quick reference by type:
- **pop**: pop-01
- **click**: click-01, click-02
- **notification**: notification-01, notification-02
- **whoosh**: whoosh-cinematic, whoosh-short, whoosh-fast
- **zoom**: zoom-01
- **impact**: impact-mega, impact-bass
- **riser**: riser-01
- **transition**: transition-subtle, transition-needle
- **slide**: slide-paper, slide-sword
- **ambient**: ambient-hum, ambient-spacecraft, ambient-space, ambient-low-hum

Read `SFX/catalog.json` for full details including filenames and recommended uses.
