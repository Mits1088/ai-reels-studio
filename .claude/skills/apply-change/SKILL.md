---
name: apply-change
description: Apply post-assembly changes by classifying the change type and re-entering the pipeline at the correct phase.
disable-model-invocation: true
---

# Apply Change Skill

Use this skill when the user requests a change to an assembled reel — ANY modification after Phase 5 assembly is complete.

This skill exists because direct ad-hoc edits to `ReelComposition.tsx` or `timeline.json` without re-entering the pipeline cause cascading bugs: wrong positioning, face covered, white gaps, z-index conflicts, double rendering.

**This skill is mandatory.** Do not edit Remotion code or timeline JSON in response to a user change request without invoking this skill first.

---

## When to Trigger

Use this skill when the user says ANY of:
- "make this bigger/smaller/centred/bold"
- "move this"
- "add a logo/image/b-roll/overlay"
- "change the position of..."
- "the gap/spacing is wrong"
- "this covers the face"
- "swap this clip"
- "change the timing"
- "add text/keyword/badge"
- "remove this"
- or any other post-assembly visual, timing, or content change

**If assembly (Phase 5) has been completed and the user asks for a modification, invoke this skill.**

Do not use this skill for:
- Initial assembly (use `assemble-reel`)
- Pre-assembly planning (use `shot-list`, `motion-intent`)
- QA (use `qa-reel`)

---

## Primary Goal

Implement the user's requested change correctly on the first attempt by:
1. Understanding exactly what they asked for
2. Classifying the change type
3. Reading the relevant component source code
4. Making the change with full knowledge of how the components work
5. Verifying the change matches what was asked

---

## Step 1 — Re-read the user's request (mandatory)

Before doing anything, re-read the user's exact words. Write down:
- **What element** is being changed (which overlay, which clip, which logo, which layout)
- **What property** is changing (position, size, color, timing, visibility)
- **What the target state is** (centred, bigger, removed, swapped)

**Rule:** If the user says "centre this" — the target is CENTRING. Not removing. Not replacing. Not repositioning to a different corner. Centring.

---

## Step 2 — Classify the change

| Change type | Re-entry phase | Required reading |
|---|---|---|
| **New visual asset** (logo, b-roll, screenshot added to reel) | 4b-i (shot-list visual assignment) | Shot list → component mapping → assembly |
| **Overlay text change** (position, size, color, font) | 5 (assembly) | Target component `.tsx` source |
| **Overlay add/remove** | 5 (assembly) | Target component `.tsx` source |
| **Split-screen layout change** (sizing, gap, positioning) | 5 (assembly) | `AvatarVideo.tsx` + target component `.tsx` |
| **Asset swap** (different clip for same beat) | 4d (asset prep) | Encode new asset → update `clipStartTime` |
| **Timing change** (beat boundaries, clip trim) | 3 (beat map) | Beat map → captions → shot list → assembly |
| **Script change** | 2b (reconcile) | Full pipeline restart |
| **Display mode change** (split → center-full, etc.) | 5 (assembly) | `BRollVideo.tsx` + `AvatarVideo.tsx` |
| **Background change** | 5 (assembly) | Background component source |

---

## Step 3 — Read component source (mandatory, no exceptions)

Before writing ANY JSX or modifying ANY timeline entry:

### 3a — Read the target component

Open and read the `.tsx` file for every component involved in the change:

```
Read remotion/src/components/effects/KeywordFadeIn.tsx
Read remotion/src/components/effects/BadgePopup.tsx
Read remotion/src/components/effects/OverlayKeyword.tsx
Read remotion/src/components/media/AvatarVideo.tsx
Read remotion/src/components/media/BRollVideo.tsx
Read remotion/src/components/media/FramedImage.tsx
```

Only read the ones relevant to the change. But ALWAYS read them.

### 3b — Extract key information

For each component, note:
- **Props interface** — exact prop names and types (not guessed)
- **Positioning** — does it position itself (`position: absolute`) or rely on parent?
- **z-index** — where does it stack?
- **Container sizing** — does it constrain its own height/width?
- **Internal padding/margins** — does it add spacing that affects layout?

### 3c — Cross-reference with AvatarVideo (if split-screen)

If the change affects anything in split-screen layout:
- Read `AvatarVideo.tsx`
- Note the split-screen boundary: `bottom: 0, height: "60%"` (avatar occupies bottom 60%)
- Content container MUST be `height: "40%"` to match
- Any mismatch = visible white gap

### 3d — Invoke remotion-best-practices (if writing Remotion code)

If the change requires modifying `.tsx` files:
- Invoke the `remotion-best-practices` skill
- Load the relevant rule files (videos, sequencing, timing, etc.)
- Only then proceed to implementation

---

## Step 4 — Implement the change

With component APIs understood, implement the change:

### Rules during implementation

1. **Use the correct prop names** — from the component source, not from memory
2. **Match container boundaries** — split-screen content = 40%, avatar = bottom 60%
3. **Use `objectFit: "cover"`** for gap-free split-screen video/image rendering
4. **Centre overlays by default** — `position="center"` for KeywordFadeIn, `AbsoluteFill` with `justifyContent: "center"` for BadgePopup
5. **Size overlays for mobile** — `fontSize >= 64` for all text overlays
6. **Never remove what the user asked to fix** — fix the element in place
7. **One change at a time** — don't batch visual changes

### For split-screen content (video/image in top zone)

```tsx
// CORRECT — matches avatar boundary, fills completely
<div style={{
  position: "absolute", top: 0, left: 0, right: 0,
  height: "40%",  // MUST match AvatarVideo split-screen boundary
  overflow: "hidden", zIndex: 10,
}}>
  <OffthreadVideo
    src={staticFile("clip.mp4")}
    muted
    style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center" }}
  />
</div>
```

### For centred overlays

```tsx
// KeywordFadeIn — use position="center", large fontSize
<KeywordFadeIn
  words="Tool Name"          // prop is "words" not "text"
  durationInFrames={toFrame(1.5)}
  color="#4285F4"
  withGlow
  position="center"          // "center" | "top" | "bottom" — NOT "top-center"
  fontSize={80}              // minimum 64 for mobile
/>

// BadgePopup — no position prop, wrap in centred container
<AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center", zIndex: 20 }}>
  <BadgePopup
    text="Badge Text"
    durationInFrames={toFrame(1.5)}
    color="#34A853"
    size="large"              // "small" | "medium" | "large"
  />
</AbsoluteFill>
```

---

## Step 5 — Verify the change (mandatory)

After implementing:

1. **Compile check** — `npx tsc --noEmit`
2. **Render the affected frame** — `npx remotion still <Composition> --frame=<N> --output=<path>`
3. **Visually inspect the rendered frame** — read the PNG file and look at it
4. **Compare against the user's request** — re-read their words. Does the output match what they asked for?
5. **Check for side effects** — did the change break anything adjacent? (gaps, overlaps, z-index conflicts)

If the rendered frame does not match the user's request, go back to Step 3 and re-read the component source. Do not guess at a fix.

---

## Common mistakes this skill prevents

| Mistake | How this skill prevents it |
|---|---|
| Wrong prop names | Step 3a: read component source, note exact interface |
| White gap between content and avatar | Step 3c: read AvatarVideo.tsx, confirm 40%/60% boundary |
| Overlay in corner instead of centred | Step 4: default centre rule, correct container pattern |
| Element covering avatar face | Step 3b: check z-index and positioning |
| Removing element user asked to fix | Step 1: re-read exact words, note target state |
| Double rendering (ghost images) | Step 3b: understand component's own rendering before adding layers |
| Change breaks adjacent layout | Step 5: check for side effects |

---

## Relationship to other skills

**assemble-reel** — handles initial assembly. This skill handles post-assembly changes.

**remotion-best-practices** — invoked by this skill when code changes are needed (Step 3d).

**qa-reel** — runs after changes to verify the full reel still passes. This skill handles individual change verification (Step 5).

**shot-list** — re-entered by this skill when new visual assets are added (Step 2 classification).

---

## Stop condition

Stop after:
- The change is implemented
- The affected frame is rendered and visually verified
- The output matches what the user asked for

Present the rendered frame to the user for confirmation before moving on.
