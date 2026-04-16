---
description: Fixed hook identity rules — what stays stable across all Mits reels in the first 2–3 seconds
globs: ["**/shot-list.md", "**/motion-intent.md", "**/timeline.json"]
---

# Hook Grammar

The hook is a **brand signature**. Viewers who watch multiple reels should recognize the opening without needing to read the account name. That recognition is earned by consistency in structure — not by identical execution. The hook has stable DNA and elastic execution.

**Stable DNA:** the structural elements that define every Mits hook — logo presence, real product UI, split-screen avatar, continuous motion, SFX on entry.
**Elastic execution:** which product, which screenshot, which logo, which caption text, which SFX character — these change every reel.

This file governs the first 2–3 seconds of every reel regardless of style profile. Creative variation belongs in the body.

---

## The Signature Elements (non-negotiable)

Every hook must have all of the following from frame 0:

| Element | Requirement |
|---|---|
| **Real product UI** | Screenshot or video clip of actual product UI (Claude Console, Notion workspace, ChatGPT interface). NOT stock footage. NOT abstract gradients. NOT a warm-beige background. |
| **Continuously animating element** | At least one element in continuous motion throughout the entire hook: bouncing logo, Ken Burns zoom on a screenshot, scrolling icon grid, cycling demo screenshots |
| **Recognizable brand logo** | SVG logo of the primary product or brand — visible by second 1–2 via `LogoOverlay` |
| **Avatar in split-screen** | Talking head always present but never full-screen in the hook — always paired with at least one other visual element |
| **Value claim caption** | First spoken phrase readable as a caption from frame 0 |
| **SFX on entry** | Whoosh, impact, or pop fires on frame 0 to mark the reel start |
| **≥4 simultaneous visual elements** | Count motion elements active in any single frame of the first 3 seconds — must reach 4 or more |

If any element is missing, the hook fails the Phase 4b-i self-test and must be redesigned.

---

## Approved Hook Archetypes

The hook must be built from one of these three archetypes. Do not invent a new hook structure unless explicitly requested. All creative energy goes into the body — the hook is the consistent handshake.

Each archetype defines its **DNA** (what must be present), **allowed variations** (what changes freely), and **forbidden sameness** (what must not repeat identically across consecutive reels). The archetypes are stable but elastic — same structure, different execution.

---

### Archetype A — Split-Proof Hook *(default)*

The standard hook for most reels. Product UI anchors the top, avatar anchors the bottom.

**Layout:**
- Top 40%: `FramedImage` (real product screenshot) with Ken Burns zoom toward the focal point
- Bottom 60%: `AvatarVideo` (split-screen)

**Logo:**
- `LogoOverlay` with `bounce: true, bounceAmplitude: 28–32, bounceFrequency: 2.4–3.0 Hz` at top-left or top-center
- Optional: secondary `LogoOverlay` at `position: center-bottom` on the avatar for brand comparisons — one per named brand, appearing sequentially on entry

**Caption:** Value claim at bottom safe zone (standard caption)

**SFX:** Impact or whoosh on entry + pop per logo entry

**Best for:** Single-product demos, feature reveals, capability showcases, cinematic-presenter and proof-escalation-editorial styles

**Required invariants (DNA — must be present):**
- FramedImage showing real product UI (not stock, not AI art)
- AvatarVideo in split-screen bottom position
- LogoOverlay with `bounce: true` as the continuous motion element
- SFX firing on frame 0
- Value claim caption readable from frame 0
- Ken Burns zoom active on the screenshot from frame 0

**Allowed variations (elastic — change freely per reel):**
- Which product screenshot (any reel-specific product UI, any product state)
- Which logo(s) and brand(s) shown
- Caption text (always specific to this reel's proof)
- Ken Burns direction and focal point target
- Aurora background tint (follows `theme_primary`)
- SFX character (whoosh, impact, cinematic hit)
- Secondary logo entries at avatar chest position (0–3 brands)
- Logo bounce amplitude and frequency (within spec range)
- FramedImage aspect ratio (portrait screenshot, landscape screenshot, etc.)

**Forbidden sameness:**
- Same screenshot composition (same image, same crop, same Ken Burns direction) as the hook in the most recent reel on the same product
- Identical caption phrasing structure repeated across consecutive reels ("X just changed Y about Z")
- Same logo position + identical bounce parameters without any variation

---

### Archetype B — Icon-Grid Hook *(editorial-authority, multi-tool reels)*

The hook for comparison and listicle reels where multiple brands are named. The icon grid IS the product proof.

**Layout:**
- Top 45–50%: `ScrollingIconGrid` (brand logos scrolling diagonally)
- Bottom 50–55%: `AvatarVideo` (split-screen)

**Logo:** Individual `LogoOverlay` entries appearing sequentially over the grid (one per brand named in the hook)

**Overlay:** `OverlayKeyword` at the center of the grid zone for the value claim text — positioned above the avatar boundary

**Caption:** Minimal or absent (OverlayKeyword carries the text)

**SFX:** Stutter or whoosh on entry + pop per icon/logo entry

**Best for:** "3 tools that...", "ChatGPT vs X" comparisons, multi-brand listicles, editorial-authority style

**Required invariants (DNA — must be present):**
- ScrollingIconGrid present and actively scrolling from frame 0
- AvatarVideo in split-screen bottom position
- At least one LogoOverlay entry per brand named in the hook narration
- OverlayKeyword for value claim visible from frame 0 (or caption if OverlayKeyword is not used)
- SFX firing on frame 0

**Allowed variations (elastic — change freely per reel):**
- Which brands populate the grid (can vary from the brands in the overlay)
- Grid scroll speed and diagonal angle
- Value claim text (always specific to this reel)
- OverlayKeyword size, weight, and vertical position within the grid zone
- Number of sequential LogoOverlay entries (1–5 typical)
- SFX character and rhythm between logo entries
- Grid density and icon size

**Forbidden sameness:**
- Identical brand set + identical OverlayKeyword text across consecutive multi-brand reels
- Same logo entry sequence order (always same brand first) without any variation in rhythm or ordering

---

### Archetype C — B-Roll-Reveal Hook *(cinematic-presenter, abstract concepts)*

For reels where no product UI is ready at launch, or where cinematic footage is editorially stronger than a static screenshot.

**Layout:**
- Top portion: `BRollVideo` with `display: "responsive"` (b-roll fills its natural aspect ratio, avatar visible below)
- Bottom: `AvatarVideo` (visible below the b-roll)

**B-roll requirement:** Must be product-adjacent — official product footage, brand-produced cinematic content, or NotebookLM-generated abstract AI visuals. Never generic Pexels b-roll in the hook.

**Logo:** `LogoOverlay` with `bounce: true` above the b-roll zone

**Caption:** Value claim at bottom safe zone

**SFX:** Cinematic hit or whoosh on entry

**Best for:** Concept-driven reels, when source video provides strong opening footage, when the product itself is abstract (AI model research, infrastructure tools)

**Required invariants (DNA — must be present):**
- BRollVideo clip is product-adjacent (official footage, brand-produced, or NotebookLM cinematic)
- AvatarVideo visible below the b-roll
- LogoOverlay with `bounce: true` above the b-roll zone as the continuous motion element
- SFX firing on frame 0
- Value claim caption readable from frame 0

**Allowed variations (elastic — change freely per reel):**
- Which b-roll clip (any product-adjacent footage)
- Clip trim points and duration in the hook
- Logo position above the b-roll zone (top-left vs top-center)
- Caption text (always specific to this reel)
- SFX character

**Forbidden sameness:**
- Same b-roll clip in consecutive reels on the same topic
- Same opening frame composition (same clip + same trim point + same logo position)

---

## What Remains Stable Across All Archetypes

These never change regardless of which archetype is used or what the reel covers. They are the brand DNA:

1. **Avatar always in split-screen** — never full-screen in the hook
2. **Logo presence** — at least one brand SVG logo visible by second 1–2
3. **Continuous motion** — at least one element moving continuously through the full hook duration
4. **Real product UI or brand-relevant content** — no stock footage, no abstract gradients, no empty backgrounds in frame 0
5. **SFX on entry** — silence on frame 0 is not acceptable
6. **Value claim** — specific to this reel's proof, readable from frame 0
7. **≥4 simultaneous visual elements** — counted in any frame of the first 3 seconds

---

## What Changes Per Reel

These vary freely between reels:

- Which archetype (A, B, or C)
- Specific screenshot or b-roll content
- Logo(s) shown and their order
- Value claim text (always specific to this reel)
- SFX character (whoosh vs. impact vs. stutter)
- Color palette (follows `theme_primary` / `theme_secondary` from project.json)
- Brand count (one primary brand or multiple)
- Caption text

---

## Allowed Motion Families in the Hook

| Motion | Notes |
|---|---|
| Ken Burns zoom on product UI | Slow push (1.0 → 1.03 over hook duration), toward the focal product element |
| Logo bounce | `LogoOverlay bounce: true` — the signature continuous motion element |
| ScrollingIconGrid diagonal scroll | Built-in animation — do not add competing motion on top |
| B-roll internal motion | The clip's own motion handles the continuous element requirement |
| OverlayKeyword fade entry | Brief, clean fade-in over the grid |

**Not allowed in the hook:**
- FlashReset (belongs in body section dividers)
- GlitchText, StrikethroughSwap, complex card animations (belong in body beats)
- Full-screen avatar (hook is always split-screen)
- Center-full anything (hook requires avatar visible)
- Aggressive scale punches on the avatar or screenshot (hook energy is continuous, not impactful)

---

## Caption Behavior in the Hook

- Value claim caption must be visible from frame 0 — not fading in after a second
- For Archetype B (editorial-authority): OverlayKeyword carries the value claim instead of the standard caption component
- Caption must be readable against the background — ensure sufficient contrast on light Aurora backgrounds
- Do not suppress captions in the hook — the viewer is still deciding whether to keep watching

---

## Proof Behavior in the Hook

The hook proof is **visual and implicit** — the product UI itself is the proof setup.

- The screenshot or b-roll creates the question ("what is this? is this real?")
- The hook does not answer the question — that belongs in the body
- No explicit verbal proof claims in the hook narration ("it did X" belongs in beat 2 or later)
- Generic product imagery is not proof — the specific feature, result, or UI state being demonstrated must be visible

---

## Self-Test (Phase 4b-i gate)

Before approving the hook visual assignment, verify:

- [ ] First frame contains real product UI — not just an avatar, not a warm background
- [ ] At least one element is in continuous motion through the entire hook (bounce, zoom, scroll, or clip motion)
- [ ] At least one brand logo SVG is visible within seconds 1–2
- [ ] Caption (or OverlayKeyword) is readable in the first frame
- [ ] Total simultaneous visual elements in any frame of the first 3 seconds ≥ 4
- [ ] Avatar is in split-screen (not full-screen)
- [ ] SFX fires on entry
- [ ] Check the most recent reel with this product: is this hook meaningfully different in execution (different screenshot, different caption angle, different SFX) even if the archetype is the same?

---

## Banned Hook Patterns

- Avatar full-screen alone with no overlays in frame 0
- Single text card as the sole visual (no product UI, no avatar)
- Empty warm-beige or dark background while the avatar fades in
- "Clean minimalism" — minimalism belongs in body beats, not hooks
- Static screenshot with no Ken Burns or continuous motion
- Generic stock footage (hooded hacker imagery, abstract particles, glowing circuits) — these do not pass the "real product UI" requirement
- Fade-in from black — the hook starts at full energy, not building to it
