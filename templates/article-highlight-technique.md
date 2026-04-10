# Article Screenshot Highlight Technique

Use this technique when a reel needs to show an article/research page screenshot with specific words or phrases visually highlighted — proving the claim by pointing the viewer's eye to the exact text.

## When to Use

- Trust beats showing official source pages with key claims highlighted
- Proof beats where a benchmark result or headline needs emphasis
- Any beat where an article screenshot is the visual and specific text must stand out

## Pipeline

### Step 1 — OCR for text positions

Use Tesseract CLI to extract bounding boxes from the screenshot:

```bash
tesseract input.png output --psm 6 tsv
```

Parse the TSV output to find the pixel coordinates of target words/phrases. Convert pixel positions to percentage-based coordinates for Remotion's responsive layout.

### Step 2 — Remotion composition

```
Use Remotion's useCurrentFrame() + interpolate() for ALL animations.
No CSS transitions. No framer-motion. No CSS keyframes.
```

**Load the image** and pad it generously on a white (#FFFFFF) background at 1080x1920 (or composition size).

**Subtle zoom + 3D rotation** (Ken Burns with perspective):
```tsx
const frame = useCurrentFrame();
const { fps } = useVideoConfig();

const scale = interpolate(frame, [0, 5 * fps], [1.0, 1.05], { extrapolateRight: "clamp" });
const rotateY = interpolate(frame, [0, 5 * fps], [-7, 8], { extrapolateRight: "clamp" });
const rotateX = interpolate(frame, [0, 5 * fps], [3, -3], { extrapolateRight: "clamp" });

// Apply via transform (GPU-friendly)
style={{
  transform: `perspective(1200px) scale(${scale}) rotateY(${rotateY}deg) rotateX(${rotateX}deg)`,
}}
```

Keep total rotation subtle (~15deg range across both axes over 5s). The article should feel like it's being examined, not spinning.

**Reveal entry** — use opacity fade-in (NOT blur):
```tsx
const opacity = interpolate(frame, [0, 1 * fps], [0, 1], { extrapolateRight: "clamp" });
```

Blur is forbidden in our pipeline (kills GPU performance, conflicts with visual-style.md). Opacity fade achieves the same "reveal" feeling.

**Highlighter wipe** — use Remotion's spring-based scaleX pattern:
```tsx
const highlightProgress = spring({
  fps,
  frame,
  config: { damping: 200 },
  delay: HIGHLIGHT_START_FRAME,
  durationInFrames: 18,
});

// Highlight bar behind text (zIndex: 0), text in front (zIndex: 1)
<span style={{
  position: "absolute",
  left: 0, right: 0,
  top: "50%",
  height: "1.05em",
  transform: `translateY(-50%) scaleX(${Math.min(1, highlightProgress)})`,
  transformOrigin: "left center",
  backgroundColor: "#FFE066", // yellow highlighter
  borderRadius: "0.18em",
  zIndex: 0,
}} />
```

Reference implementation: `remotion/.agents/skills/remotion-best-practices/rules/assets/text-animations-word-highlight.tsx`

### Step 3 — Multiple highlights with stagger

For multiple phrases, stagger the highlight start frames:
```tsx
const highlights = [
  { word: "6x reduction", delay: 1.5 * fps, color: "#FFE066" },
  { word: "zero accuracy loss", delay: 2.5 * fps, color: "#A7C7E7" },
];
```

Each highlight wipes left-to-right independently with its own delay.

## Positioning highlights on screenshots

When highlighting text on a screenshot (not rendered text), use the Tesseract bounding boxes to position absolute-positioned highlight bars over the image:

```tsx
<div style={{ position: "relative" }}>
  <Img src={staticFile("article.png")} style={{ width: "100%" }} />
  {highlights.map((h) => (
    <div
      key={h.word}
      style={{
        position: "absolute",
        left: `${h.x}%`,
        top: `${h.y}%`,
        width: `${h.width}%`,
        height: `${h.height}%`,
        backgroundColor: h.color,
        opacity: 0.4,
        transform: `scaleX(${highlightProgress})`,
        transformOrigin: "left center",
        borderRadius: 4,
      }}
    />
  ))}
</div>
```

The highlight renders as a semi-transparent overlay at the exact text position, appearing behind the text visually because the screenshot's text is already baked into the image.

## Rules

- ALL animation via `useCurrentFrame()` — no CSS animations, no rough.js, no framer-motion
- No blur effects — use opacity for reveals
- GPU-friendly only: `transform`, `opacity`, `clipPath`
- Keep 3D rotation subtle (max ~15deg per axis over the full duration)
- Highlight colors should match the reel's brand palette
- Spring-based wipe looks more natural than linear interpolation
- Reference: `remotion/.agents/skills/remotion-best-practices/rules/text-animations.md`

## Original Prompt (for reference)

> Import the image into the project. Use Tesseract CLI to do OCR and find the positions of the text. In Remotion, make a new composition where you load the image and pad the article generously on a white full HD background. While the composition runs for 5 seconds, slowly and subtly zoom into it and slightly rotate the article in 3D from left to right. The overall rotation should be around 15deg for each axis. At the beginning, fade in the composition over 1 second. After the fade, evolve a highlighter from left to right over the target words. Make sure the marker appears behind the text.

Adapted from the original which used blur (replaced with opacity) and rough.js (replaced with Remotion spring wipe).
