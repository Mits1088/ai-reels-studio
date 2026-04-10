---
description: Quality gates that must pass before a reel is exported
globs: ["**/qa-report.md", "**/qa_report.json", "**/timeline.json"]
---

# QA Gates

A reel is only ready when all blocking checks pass.

## Style-Aware Thresholds

Some QA thresholds vary by the project's `style` field in `project.json`. Read the style before applying thresholds.

| Threshold | `cinematic-presenter` | `editorial-authority` |
|---|---|---|
| Avatar absence (preferred) | 12s (relaxed with matched b-roll) | 8s |
| Avatar absence (hard max) | 15s | 12s — only ONE >8s block, proof-protected only |
| Consecutive center-full (preferred) | 4 | 4 |
| Consecutive center-full (conditional max) | — | 5, only if 3+ entries are different sub-classes |
| Flash accent max | 1 per reel | 2 for <35s, 3 for 35s+ |
| SFX target (30-40s) | 6-8 | 5-9 purposeful entries |
| SFX target (40-55s) | 8-12 | 7-12 purposeful entries |
| Dead hold tolerance | 0.5s (15 frames) | 0 (no dead holds) |
| Proof frame hold limit | N/A | 60 frames (2s) max unchanged |
| Claim-to-proof latency | N/A | 45 frames (1.5s) max |
| Visual variety minimum | 6-8 distinct states | 10-15 distinct states |
| Ken Burns required | yes on static content | no (not used) |
| Ambient motion | yes (breathe, drift) | no (stillness is fine) |
| Split-screen spacing check | required | required (hook + proof splits) |
| Proof-protected enforcement | N/A | required — verify proof beats use real source assets |

If the `style` field is missing or unrecognized, use `cinematic-presenter` thresholds.

---

## Blocking Checks

### Timing
- narration and timeline are aligned
- beat map timing matches actual transcript timing
- captions are synced and readable
- no accidental dead air

### Visuals
- captions stay within safe zones
- important UI is not covered
- demo steps are visually understandable
- scene order makes sense
- no continuous avatar absence longer than 15 seconds — flag if the face disappears for longer without a split-screen return or strong overlay compensation. When matched cinematic b-roll (e.g. NotebookLM) directly illustrates the narration, longer absence is acceptable.
- no more than 4 consecutive `center-full` entries without a face return or split-screen beat between them
- split-screen image spacing is visually balanced: image must be centered in the top 40% zone with equal margin above the image and between the image and avatar (enforced by `FramedImage.tsx` — if it looks top-anchored or unbalanced, the padding was changed and must be restored to `alignItems: center, padding: 32px 24px`)
- **split-screen gap check (BLOCKER)**: content container height must be exactly `40%` to match `AvatarVideo.tsx` split-screen boundary (`bottom: 0, height: 60%`). Any visible white gap between content bottom edge and avatar top edge means the container height is wrong. Read `AvatarVideo.tsx` to confirm the boundary before changing container sizing.
- **overlay positioning check**: all text overlays (KeywordFadeIn, BadgePopup, OverlayKeyword) must be horizontally centred and sized for mobile readability. Default: `position="center"`, `fontSize >= 64`. Overlays placed in corners (top-left, top-right) are a WARNING unless there is a documented design reason.
- **overlay face obstruction check**: no overlay or image card should cover the avatar's eyes or face during full-screen avatar beats. If an overlay must appear during avatar full-screen, it must sit above or below the face, not over it.

### Assets
- all referenced assets exist
- assets are linked to beat or scene purpose
- no orphaned critical references in timeline

### Render Layer Overlap
- no two center-full entries across demo and broll lanes overlap in time — if they do, one is invisible (BLOCKER)
- verify the JSX render order in ReelComposition.tsx matches the intended visual stacking (demo renders before broll, so broll appears on top)
- if an overlap is intentional (broll wipes over demo), verify the transition makes this visually clean

### Video Encoding
- all videos in remotion/public/ are encoded with libx264, yuv420p, 30fps
- all videos have `-g 1` keyframe interval (no jerky seeking)
- all videos have `-movflags +faststart` (no browser loading errors)
- all videos have an audio track (even if muted) — Remotion may throw HTMLVideoElement errors on videos without audio streams
- videos at non-standard fps (25fps, 24fps) have been converted to 30fps

### SFX and Transitions
- all SFX files referenced in timeline exist and are non-empty (>1KB, >0.1s)
- SFX are audible during playback — not drowned by narration or silent
- every scene/layout change has at least one SFX or transition (no silent hard cuts between sections)
- SFX volume levels are set per entry (not relying on defaults)
- transitions render visibly — check at least 1 frame during enter and 1 during exit for each visual entry
- no more than 2 consecutive visual entries share the same enter transition type
- transition durations are appropriate (enterDur 3–10 frames, exitDur 2–4 frames)

### Scene Backgrounds
- demo scenes (split-screen, responsive, center-full) use white/light backgrounds (AuroraBackground, BackgroundBeams)
- avatar full-screen scenes use dark backgrounds (GradientMesh + atmosphere)
- no single background runs for the entire composition — each is scoped to its time range via `<Sequence>`
- BRollVideo containers use transparent backgrounds — no opaque dark containers hiding the scene background
- background transitions at layout boundaries are clean (no flash of wrong color)

### Short Clip Safety
- clips shorter than 30 frames must use proportional fade durations: `fadeIn = Math.min(15, Math.floor(durationInFrames * 0.3))` — fixed fade durations on short clips cause `inputRange must be strictly monotonically increasing` errors in Remotion's `interpolate()`
- center-full broll entries must not be filtered out by `isHiddenByAvatar` — the filter must allow center-full entries even during avatar full-screen ranges
- Root.tsx timeline JSON imports must use `as unknown as Timeline` cast to fix display type inference

### Privacy and Personal Data
- no personal names, emails, or account info visible in demo clips unless the user explicitly approves it (e.g. their own brand name "Mits" is fine — personal bookmarks, Gmail links, third-party account names are not)
- no browser chrome, bookmarks bar, Windows taskbar, or desktop wallpaper visible in any demo clip
- no cursor artifacts from screen recording tools unless they serve the demo narrative
- if personal data is found: BLOCKER — re-crop, re-capture with mock, or blur before render

### Narrative Match
- every demo clip's visible content must match what the narrator is saying at that moment
- if the narrator says "automatic" but the visual shows a manual action — BLOCKER
- if the narrator references a specific UI element but the visual shows a different part of the interface — BLOCKER
- demo clips showing creation steps must not be used for "it works automatically" narration and vice versa

### Motion Budget
- no beat has more than 3 motion elements (1 hero, 1 support, 1 accent) — if a beat has 4+ simultaneous treatments (shimmer + glow + flash + vignette), strip the decorative ones
- flash/punch accents: maximum 1 per reel — if more than one flash accent exists across all beats, reduce to one and use opacity shifts or grade changes for the others
- no static hold longer than 0.5s (15 frames) without ambient motion — flag if a beat has zero visual movement during its hold phase

### Edit Quality
- transition use is controlled
- SFX do not overpower narration
- music sits below the voice properly
- hook lands quickly
- ending feels deliberate

### Content Quality
- claims are not obviously unresolved placeholders
- feature names are consistent
- comparisons are clear
- CTA matches the reel's topic

## Warning Checks

Warnings should be raised for:
- pacing that feels slightly rushed
- support visuals that add little value
- avatar overuse
- too much on-screen text
- weak proof for a stated claim

## Frame-by-Frame Visual Inspection

QA must include frame extraction and visual inspection of every beat:

1. Extract a representative frame from each beat at its midpoint
2. For demo beats: also extract the first and last visible frames to verify trim points
3. Inspect each frame for: personal data, browser chrome, narrative mismatch, visual clarity on mobile
4. Cross-reference the b-roll scene library — identify any scenes that could enhance understanding for beats that feel visually weak
5. Document any b-roll enhancement suggestions in the QA report (these are suggestions, not blockers)

## B-Roll Enhancement Review

During QA, re-examine the b-roll library against the assembled reel:
- For each avatar-only beat: would a b-roll insert improve the viewer's understanding of the concept?
- For each bridge/gap: would a brief b-roll flash add anticipation or visual texture?
- Only suggest b-roll that adds comprehension value — not decoration
- Document suggestions with specific beat, scene ID, display mode, and rationale

## Performance QA

Beyond technical correctness, QA must check whether the reel performs like a reel — not just whether it renders correctly.

### First-second impact
- Does the first frame stop the scroll? Is there immediate visual interest?
- Does the hook land within the first 1–3 seconds?
- Is the first visual static or does it have motion/entrance energy?

### Pacing density
- Is there a visual change at least every 3–4 seconds?
- Are there any stretches where nothing visually changes for > 2 seconds?
- Does the middle section maintain momentum or flatten out?

### CTA dwell time
- Does the CTA have enough visual hold time to register? (minimum 2s)
- Is the CTA action word (e.g. "GUIDE") visually reinforced?
- Does the ending feel deliberate or abrupt?

### Named tool support
- Every time a tool is named in narration, is it visually supported? (logo, UI, demo, overlay)
- If the narrator says "Claude" or "ChatGPT" — is the product visible on screen at that moment?

### Beat overload check
- Does any single beat try to show too many things simultaneously? (> 3 visual elements competing)
- Are captions fighting with overlays or demo content?

### Visual variety score
- Count the number of distinct visual states across the reel
- A 45-55s reel should have at least 6-8 visually distinct moments
- If fewer than 6, flag as "visually monotonous"

## QA Output Format

Every QA report should return:
- blocking issues
- warnings
- suggested fixes
- b-roll enhancement suggestions (if any)
- final recommendation: pass / revise

### Editorial Authority Compliance (required when style is `editorial-authority`)

When the project uses `editorial-authority` style, QA must include an additional section:

```markdown
## Editorial Authority Compliance
- [ ] Style activation: project.json, shot-list, motion-intent, timeline all declare editorial-authority
- [ ] Proof-protected beats: all proof_protected entries use real source assets (no b-roll substitution)
- [ ] Avatar absence: no >8s blocks except one proof-protected run, hard max 12s
- [ ] Center-full streak: max 4 preferred, 5 only if 3+ different sub-classes
- [ ] Claim-to-proof latency: every number/tool/result claim has proof within 45 frames
- [ ] Proof hold limit: no unchanged proof frame >60 frames
- [ ] Dense/sparse rhythm: no >3 dense frames without sparse reset
- [ ] Flash budget: within limit for reel duration
- [ ] SFX: event-driven only, no quota-filler
- [ ] No ambient motion on static content
- [ ] Backgrounds: solid colors only (no Aurora/GradientMesh/Beams)
```

If any of these checks fail, flag as a style compliance blocker.

### Proof Escalation Editorial Compliance (required when style is `proof-escalation-editorial`)

When the project uses `proof-escalation-editorial` style, QA must include an additional section. Thresholds are read from `training/derived/rhythm-bounds.json` and validated against the assembled timeline.

```markdown
## Proof Escalation Editorial Compliance

### Template & Oscillation
- [ ] Every timeline entry has a `template_id` from the template registry
- [ ] Template class sequence (ANCHOR/PROOF) has no run longer than recommended_max from rhythm-bounds.json
- [ ] Longest avatar absence compensated by cursor/interaction motion if >8s

### Caption Suppression
- [ ] All `demo-fullscreen` entries have `captionMode: "suppressed"`
- [ ] All `card-carousel` entries have `captionMode: "suppressed"`
- [ ] No caption text renders during suppressed zones
- [ ] Caption suppression covers 24-36% of total reel duration (from rhythm-bounds.json)

### Proof Arc
- [ ] `proof_class` values progress forward (existence → breadth → process → output → authority → cta)
- [ ] No backward jumps in proof class (e.g., "output" then "existence")
- [ ] Every proof_class entry has matching visual proof on screen (zero-gap rule)

### Rhythm (from rhythm-bounds.json metric_bounds)
- [ ] Average visual change within bounds (2.6-3.8s)
- [ ] Avatar on-screen percentage within bounds (38-58%)
- [ ] Total visual states within bounds (14-22)
- [ ] Template types used within bounds (6-10)
- [ ] No static hold exceeds max_static_hold_s bound (2.5s)

### Split Ratios
- [ ] `splitRatio` set per entry matches template registry value
- [ ] No fixed 40/60 split used (this style uses flexible ratios)
- [ ] Proof-overlay-split entries use 65/35 (not 40/60)

### Backgrounds
- [ ] No Aurora, GradientMesh, or BackgroundBeams (this style uses solid/natural backgrounds)
- [ ] Template background values match: warm-beige=#F0EBE0, dark=#1A1A1A, natural=none
```

If any of these checks fail, flag as a style compliance blocker.
