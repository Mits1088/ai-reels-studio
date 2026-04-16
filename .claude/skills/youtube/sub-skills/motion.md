# YouTube Motion Sub-skill

**Invoked by:** `/youtube motion`

Plan and build the Remotion motion graphics package for a YouTube video. This skill does two things:

1. **Reel asset export** — identify which elements from the reel's Remotion composition can be exported as standalone video clips for reuse in the YouTube edit
2. **YouTube composition** — build a new 1920×1080 Remotion composition that generates lower thirds, chapter title cards, and hook graphics for the YouTube video

---

## Mandatory: Load Remotion Rules Before Writing Any Code

Before writing or modifying ANY Remotion code, invoke the `remotion-best-practices` skill.

This is not optional. Even if Remotion skills were loaded earlier in this session, load them again before each code change.

---

## Required Inputs

- `projects/<slug>/youtube/script.md` — for chapter names, tool mentions, lower third labels
- `projects/<slug>/output/timeline.json` — reel timeline for identifying reusable elements
- `projects/<slug>/project.json` — theme colors, slug, style
- `remotion/public/brands/` — brand SVGs already prepared for the reel

---

## Part 1 — Reel Asset Export Plan

### Step 1: Audit the Reel Timeline

Read `output/timeline.json`. Identify every entry that produces a self-contained visual element useful in a YouTube edit:

**Always reusable from any reel:**
- `LogoOverlay` entries — brand logo animations (product logos with bounce/trail)
- `HeroTextCard` entries — bold text cards on solid backgrounds (chapter titles, key claims)
- `KeywordFadeIn` / `CharKeyword` entries — animated keyword reveals
- `BadgePopup` entries — small pill badges (tool names, labels)
- `NumberPopup` entries — numbered list items
- `AnnotationCircle` entries — draw-on annotation overlays

**Conditionally reusable:**
- `FramedImage` entries with relevant proof screenshots (if the YouTube video covers the same proof)
- `ChapterDivider` entries — section title cards (reusable if chapter names match)

### Step 2: Build Export List

For each reusable element, document:

```markdown
| Entry ID | Type | Content | Duration | YouTube use case | Export name |
|---|---|---|---|---|---|
| logo-01 | LogoOverlay | Anthropic SVG | 90 frames | Hook brand reveal (0:00-0:03) | youtube-logo-anthropic.mp4 |
| hero-02 | HeroTextCard | "5x Faster" | 60 frames | Chapter 2 title card | youtube-title-5x.mp4 |
```

### Step 3: Render Instructions

For each element to export, provide the render command using Remotion's `renderMedia` with a time range:

```bash
cd remotion
npx remotion render ReelComposition --output out/youtube-assets/[export-name].mp4 \
  --frames [startFrame]-[endFrame] \
  --background-color transparent
```

Use `--background-color transparent` for overlays (LogoOverlay, KeywordFadeIn, BadgePopup) so they can be composited in video editors.

Use `--background-color #FFFFFF` for standalone cards (HeroTextCard, ChapterDivider).

List all export commands in the motion package document so the creator can run them after the reel is rendered.

---

## Part 2 — YouTube Remotion Composition Plan

Plan the new YouTube-specific Remotion composition at 1920×1080, 30fps.

### Components needed

Based on `youtube/script.md` chapter map and tool mentions, identify which of these are needed:

| Component | When to build | Notes |
|---|---|---|
| `YoutubeLowerThird` | When script has `[LOWER THIRD: ...]` cues | Tool name cards, chapter labels |
| `YoutubeChapterCard` | When video has 3+ chapters | Full-screen chapter title animation |
| `YoutubeHookGraphic` | For the hook section | Animated stat or bold claim card |
| `YoutubeEndCard` | For outro section | Subscribe CTA + video suggestion layout |

### Design constraints (non-negotiable)

- **Resolution:** 1920×1080, 30fps — NEVER render YouTube assets at 1080×1920
- **Safe zone:** 10% on all sides for platform UI elements (title bar, subscribe button)
- **Text legibility:** Minimum 48pt for body, minimum 72pt for titles — tested on 1080p monitors AND mobile
- **Background:** Use `theme_primary` from `project.json` as the base brand color
- **Typography:** Match the font choices from the reel's Remotion components (check existing `HeroTextCard.tsx` or `KeywordFadeIn.tsx` for font imports)
- **Duration:** Lower thirds: 3-5 seconds. Chapter cards: 2-3 seconds. End card: 20 seconds.

### YoutubeLowerThird Component Spec

When the script has `[LOWER THIRD: tool name]` cues, a lower third animates in from the left, holds, and exits.

```tsx
// Props interface to implement:
interface YoutubeLowerThirdProps {
  name: string;           // Primary label (tool name, chapter name)
  subtitle?: string;      // Optional secondary label
  brandColor: string;     // Hex color — from project.json theme_primary
  logoSrc?: string;       // Optional SVG path from remotion/public/brands/
  position: "bottom-left" | "bottom-center";
  durationInFrames: number;
}
```

Animation: slide in from left (transform translateX) over 8 frames, hold, slide out over 6 frames. No CSS animations — use `useCurrentFrame()` and `interpolate()` only.

### YoutubeChapterCard Component Spec

Full-screen chapter transition card. Appears for 2-3 seconds between major sections.

```tsx
interface YoutubeChapterCardProps {
  chapterNumber: number;  // e.g., 1, 2, 3
  title: string;          // Chapter title from script chapter map
  brandColor: string;     // from project.json theme_primary
  durationInFrames: number;
}
```

Animation: title scales in from 0.9 to 1.0 with spring, chapter number fades in 6 frames ahead of title.

### YoutubeHookGraphic Component Spec

For the hook section — an animated bold claim or stat card.

```tsx
interface YoutubeHookGraphicProps {
  headline: string;       // The bold claim (max 6 words)
  subtext?: string;       // Optional supporting line
  brandColor: string;     // from project.json theme_primary
  durationInFrames: number;
}
```

### YoutubeEndCard Component Spec

20-second end card with subscribe CTA and next-video placeholder.

```tsx
interface YoutubeEndCardProps {
  channelName: string;
  nextVideoTitle: string;
  brandColor: string;
  durationInFrames: number; // 600 frames (20 seconds)
}
```

---

## Part 3 — YouTube Composition File

The YouTube motion package generates a `YoutubeComposition.tsx` file.

This composition renders all YouTube motion elements as a single timeline. The creator exports individual sections as separate clips using Remotion's frame-range render.

### Root.tsx Registration

The new composition must be registered in `remotion/src/Root.tsx`:

```tsx
<Composition
  id="YoutubeAssets"
  component={YoutubeComposition}
  durationInFrames={totalYoutubeDuration}
  fps={30}
  width={1920}
  height={1080}
/>
```

**Do not modify the existing `ReelComposition` registration** — YouTube assets are a separate composition entirely.

---

## Output Document

Produce `projects/<slug>/youtube/motion-package.md`:

```markdown
# YouTube Motion Package: [Project Slug]

---

## Part 1 — Reel Asset Exports

### Reusable Elements from Reel Timeline

| Entry | Type | Content | Duration | YouTube Use | Export Command |
|---|---|---|---|---|---|
[table]

### Export Commands
[Shell commands to run after reel render — one per asset]

---

## Part 2 — YouTube Composition Plan

### Components to Build
- [ ] YoutubeLowerThird — for [X] `[LOWER THIRD]` cues in script
- [ ] YoutubeChapterCard — for [X] chapters
- [ ] YoutubeHookGraphic — for hook section at 0:00
- [ ] YoutubeEndCard — for 20-second outro

### Chapter Card Schedule
| Frame | Chapter | Title |
|---|---|---|
[table from script chapter map]

### Lower Third Schedule
| Timestamp | Label | Logo | Brand color |
|---|---|---|---|
[table from script [LOWER THIRD] cues]

### Brand Color Applied
- theme_primary: [hex from project.json]
- theme_secondary: [hex from project.json]

---

## Part 3 — Implementation Steps

1. Invoke `remotion-best-practices` skill
2. Read existing component source files (HeroTextCard.tsx, KeywordFadeIn.tsx) for font/style reference
3. Create `remotion/src/YoutubeComposition.tsx`
4. Create components: [list]
5. Register `YoutubeAssets` composition in `remotion/src/Root.tsx`
6. Compile check: `cd remotion && npx tsc --noEmit`
7. Preview: `cd remotion && npx remotion studio` → scrub through YoutubeAssets
8. Export individual clips using frame-range render commands above
```

---

## Implementation Gate

**Do not write any Remotion code until:**
1. The motion package plan is reviewed and approved
2. `remotion-best-practices` skill has been loaded
3. Existing component `.tsx` source files have been read

---

## Stop Condition

Phase 1: Deliver `motion-package.md` with the full plan. Present for approval.

Phase 2 (after approval): Invoke `remotion-best-practices`, read existing component sources, then implement the YouTube composition and components.

Phase 3: Compile check → preview in Remotion studio → run export commands → verify clips.
