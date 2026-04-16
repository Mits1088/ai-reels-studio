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
| Ambient motion default | opt-in (not assumed — body beats default to `still`) | none (stillness is fine) |
| Motivated zoom requirement | coordinates pre-defined in Phase 4b-iii | N/A |
| Max consecutive ambient-mode body beats | 2 (3rd only with documented escalation) | 0 |
| Stacked Motion check | fail if zoom-in entry + ambient hold on same beat | N/A |
| Split-screen spacing check | required | required (hook + proof splits) |
| Proof-protected enforcement | N/A | required — verify proof beats use real source assets |

If the `style` field is missing or unrecognized, use `cinematic-presenter` thresholds.

---

## Hook QA vs Body QA

The hook and the body are judged by different standards. Do not apply body freshness checks to the hook zone (first ~3 seconds). Do not apply hook consistency requirements to the body.

### Hook QA — clean execution of the brand signature

The hook is designed to be consistent across reels. Consistency IS the hook's job. Hook QA checks whether the signature is well-executed, not whether it is fresh.

- [ ] **Brand signature intact:** logo visible by second 1–2, real product UI in frame 0, avatar in split-screen
- [ ] **Value claim readable from frame 0** — caption or OverlayKeyword present and legible
- [ ] **At least 4 simultaneous visual elements** in any frame of the first 3 seconds
- [ ] **Continuous motion element** active throughout the full hook duration (bounce, Ken Burns, scroll, or clip motion)
- [ ] **SFX fires on entry** — silence on frame 0 is not acceptable
- [ ] **Clean execution** — no colliding overlays, no face obscured, no motion competing with the logo bounce

Hook verdict: **recognizable and clean** / **unclear signature** / **execution issue — [name element]**

The hook should NOT be penalized for repeating the same structural pattern from previous reels. It should be penalized if any of the six signature elements above is missing or broken.

### Body QA — authored variety

The body is judged for variety, escalation, proof coverage, and reset quality. These are different criteria from the hook. A body section that looks like the hook (continuous drift, bounce animations, stacked motion) is a motion quality failure (Hook energy infecting body, already in the Motion Quality section).

The Creative Freshness section below is the body-specific QA.

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
- static holds are allowed — `still` mode is valid and often preferred for body beats. A beat with no hold motion is not a failure; a beat with *unmotivated* hold motion may be.

### Motion Quality

Check for named motion anti-patterns from `.claude/rules/motion-grammar.md`. Any of these is a blocking issue:

- **Stacked Motion (BLOCKER):** Any body beat uses `zoom-in` entry preset AND ambient drift hold simultaneously. The viewer cannot settle. Fix: if entry is `zoom-in`, hold must be `still`; if hold has a zoom_moment, entry must be a non-zoom preset.
- **Zoom Reflex (BLOCKER):** A motivated zoom fires on a beat where the narrator does not name a specific element, OR where zoom coordinates were not pre-defined in Phase 4b-iii. Fix: remove the zoom_moment and assign `still` or `ambient` mode.
- **Proof Smear (BLOCKER):** A motivated zoom targets a generic region (center, top of screen) rather than the specific stat or UI element the narrator names. Fix: define target coordinates pointing at the named element.
- **Ambient overrun (WARNING):** More than 2 consecutive body beats with ambient motion active (3rd only with documented escalation in the motion intent). Fix: insert at least one `still` or `transition-led` beat. Screenshot-heavy proof sections: flag even 2 consecutive ambient beats — still or annotation-led is preferred when the viewer needs to read on-screen content.
- **Drift Without Purpose (WARNING):** Ambient motion assigned to a hold shorter than 1.5s. The drift cannot register as intentional at that duration. Fix: assign `still` mode.
- **Hook energy infecting body (WARNING):** Body beats use Ken Burns or bounce animations that read as hook signature motion rather than earned editorial motion. The first body beat should typically be `still` or `transition-led` to signal the substance section has begun.
- **Motion as Rescue (WARNING):** A beat's motion treatment appears to compensate for a weak component or asset choice. If removing the motion would reveal the composition is mismatched with the narration, the motion is rescue-motion. Fix: return to component mapping.

**Motion density check:** If the reel has high motion density (>60% of body beats using ambient or motivated mode) AND low proof/layout variation (fewer than 4 unique visual states), flag as likely over-animated. Motion variety does not substitute for compositional variety.

**Hook vs body motion check:** Verify the hook zone and the body zone use different motion registers. If body beats look identical to hook-zone motion style (continuous drift, bounce, stacked elements), flag as hook energy bleed.

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

For structured body-level freshness warnings and blockers — visual role domination, proof coverage, text-emphasis streaks, mode alternation, motion density, and assembled vs authored heuristics — see the Creative Freshness section below.

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

## Creative Freshness

These checks address reels that are technically valid but feel repetitive, plain, or over-patterned. A reel can pass every timing, encoding, and asset check and still fail as editorial design. Run these after all blocking checks pass.

### Evidence Weighting

The severity of creative freshness findings depends on the source behind the check.

| Evidence source | Severity cap | Example |
|---|---|---|
| Structural rules (`body-grammar.md` repetition limits, `component-mapping.md` maximums) | BLOCKER | Same component type 4+ consecutive beats |
| `creative-feedback.json` hard_rules | BLOCKER | A component or motion pattern explicitly banned |
| `creative-feedback.json` soft_preferences | WARNING | A pattern running against stated preferences |
| `training/derived/taste-rules.json` (any confidence) | Observation only — listed in Creative Freshness Summary, never a standalone BLOCKER | Pattern absent from taste-derived preferences |

Taste rules at LOW confidence may influence candidate ranking but must not create new blockers. If a taste-rule observation coincides with a structural rule violation, the structural rule sets the severity — not the taste rule.

### Body Variation

**Visual role distribution (BLOCKER):**
Map every body beat to its primary visual role using the taxonomy from `component-mapping.md` (text-emphasis, proof-display, annotation-focus, avatar-anchor, comparison, list-structure, reset-interrupt, credibility-signal). If any single visual role exceeds 50% of body beats: BLOCKER — the reel is one-dimensional regardless of component name variety.

Flag: "Visual role `[role]` accounts for `[N]` of `[total]` body beats (`[%]%`). Maximum 50%."

**Layout role distribution (WARNING):**
Map every body beat to its layout role (text-on-avatar, split-content, center-full, full-frame-card, annotation-overlay, full-screen-avatar, corner-micro, side-by-side). If any single layout role exceeds 60% of body beats: WARNING — the frame does not change and the eye stops seeking variety.

Flag: "Layout role `[role]` used in `[N]` of `[total]` body beats (`[%]%`). Consider breaking monotony."

**Component family variety (BLOCKER):**
Count distinct component families in the body (text-dominant, image-dominant, motion-dominant, avatar-dominant, card/badge, annotation). Reels >25s must have at least 3 different families. See `body-grammar.md` → Minimum Variety Rules.

Flag: "Only `[N]` component families represented. Minimum 3 for reels longer than 25s."

### Proof Cadence

**Proof coverage minimum (BLOCKER):**
Count `proof-display` + `annotation-focus` beats in the body. Required minimums: 25–35s reel → 3; 35–50s → 5; 50s+ → 7. Below minimum: BLOCKER — the viewer is told but not shown.

Flag: "Only `[N]` proof-display/annotation-focus beats in a `[duration]`s reel. Minimum `[required]`."

**Proof method variety (BLOCKER):**
Count distinct proof methods used (screenshot-at-rest, demo-video, annotated-screenshot, data-chart, animated-component, side-by-side). Reels >25s must use at least 2 methods. Only one method across all proof beats: BLOCKER.

Flag: "Only 1 proof method (`[method]`) used across all proof beats."

**Claim-to-proof gap (WARNING):**
For each explicit claim beat (narration classification: number+proof, trust/credibility): does a supporting proof visual appear within 2 beats or 3 seconds? If not: WARNING — narrator states something the viewer cannot verify at the moment of hearing it.

Flag: "Beat `[id]`: claim at `[time]`s, nearest proof visual not until `[time+N]`s."

### Reset / Pattern Interrupt Cadence

**Reset beat requirement (WARNING for 35–45s, BLOCKER for 45s+):**
Count `reset-interrupt` beats in the body (FlashReset, ChapterDivider, LightLeakOverlay, HeroTextCard as section label). A 35–45s reel with 0 reset beats: WARNING. A 45s+ reel with 0 reset beats: BLOCKER.

Flag: "No editorial reset in `[duration]`s reel. At least 1 pattern interrupt required for reels 35s+."

**Mode alternation (WARNING):**
Classify each body beat as presenter-mode (avatar-anchor, text-on-avatar, text-emphasis words-only) or proof-mode (proof-display, annotation-focus, comparison, list-structure). Flag if 4+ consecutive beats stay in the same mode.

- 4+ consecutive presenter-mode beats: WARNING — reel feels like a podcast
- 4+ consecutive proof-mode beats: WARNING — reel loses its human anchor

Flag: "Run of `[N]` consecutive `[mode]`-mode beats at `[id_start]`–`[id_end]`."

### Motion Freshness

**Motion density (WARNING):**
If >60% of body beats use ambient or motivated motion mode AND the reel has fewer than 4 unique visual states: WARNING — motion variety does not substitute for compositional variety.

Flag: "`[N]%` of body beats use ambient/motivated mode with only `[K]` distinct visual states."

**Still mode distribution (WARNING):**
If fewer than 30% of body beats use `still` mode: WARNING — body beats default to still, and a reel where every beat moves reads as over-animated.

Flag: "Only `[N]%` of body beats use still mode. Target at least 30%."

**Motion as rescue (BLOCKER — per motion-grammar.md):**
If any beat's motion treatment appears to compensate for a mismatched component or asset, identify by: motion intensity higher than surrounding beats, component doesn't match narration classification, asset fitness was PARTIAL or lower. See Motion as Rescue in `motion-grammar.md`.

Flag: "Beat `[id]`: motion may be rescue-motion — component/asset fitness does not match narration."

### Text-Emphasis Domination

**50% cap (BLOCKER):**
Count all `text-emphasis` visual role beats in the body (OverlayKeyword, KeywordFadeIn, CharKeyword, HeroTextCard as emphasis, GlitchText). If they exceed 50% of total body beats: BLOCKER.

Flag: "`[N]` of `[total]` body beats (`[%]%`) use text-emphasis role. Maximum 50%."

**Three consecutive text-emphasis (BLOCKER):**
If 3 or more consecutive body beats all carry text-emphasis as their primary visual role: BLOCKER — a role streak of 3 is fake variety regardless of component name differences.

Flag: "Beats `[id]`–`[id]`: 3 consecutive text-emphasis beats. Same visual function across different component names."

**Text-only proof section (BLOCKER):**
If any beat with a proof-class narration (number+proof, trust/credibility, explanation over visual) uses only text-emphasis components with no screenshot, demo video, or annotation: BLOCKER — narration without evidence is assertion, not proof.

Flag: "Beat `[id]`: narration is a proof claim but visual is text-only. Must show evidence."

### Assembled vs Authored

These are qualitative heuristics requiring editorial judgment. QA must answer each explicitly.

- [ ] **Predictable cycle (WARNING):** Does the body cycle through a short repeating template (e.g. avatar → screenshot → overlay → avatar) without variation? A reel that can be described by a repeating pattern is assembled, not authored.
- [ ] **First body beat energy drop (WARNING):** Does the first body beat look like the hook — continuous drift, bounce, stacked motion? The first body beat should feel deliberately different from the hook register, signaling that substance has begun.
- [ ] **Proof feels decorative (WARNING):** Does any proof visual feel added because a proof beat was required, rather than because it genuinely supports the narrator's claim? Decorative proof is worse than none — it signals the creator did not find real evidence.
- [ ] **Avatar beats as filler (WARNING):** Are avatar full-screen beats each doing distinct editorial work (pivot, reframe, direct address, CTA energy) — or do they all look the same? If avatar beats are interchangeable, they are filler.
- [ ] **CTA feels arrived at (pass/fail):** Does the ending feel earned — did the viewer go somewhere, and the CTA is the conclusion? Or does the CTA feel appended?
- [ ] **Hook contract honored (pass/fail):** After the hook, does the reel immediately demonstrate what it promised? A hook that promises a revelation but delays evidence for more than 5 seconds has broken the hook contract.

---

## QA Output Format

Every QA report should return:
- blocking issues
- warnings
- suggested fixes
- b-roll enhancement suggestions (if any)
- creative freshness summary (see format below)
- final recommendation: pass / revise

### Creative Freshness Summary (required for all reels)

Include this section in every QA report after structural checks complete. Use the role taxonomy from `component-mapping.md` for role labeling.

```markdown
## Creative Freshness Summary

**Visual role distribution:** [list each role with beat count and %]
**Dominant role:** [role name] — [N]% of body beats — [PASS / BLOCKER if >50%]
**Component families:** [list families present] — [N] distinct — [PASS / BLOCKER if <3 for reels >25s]
**Proof coverage:** [N] proof-display/annotation-focus beats — [PASS / BLOCKER vs minimum]
**Proof methods:** [list methods used] — [PASS / BLOCKER if only 1]
**Reset beats:** [N] reset-interrupt beats — [PASS / WARNING / BLOCKER]
**Mode alternation:** longest presenter-mode run [N] beats, longest proof-mode run [N] beats — [PASS / WARNING if 4+]
**Text-emphasis:** [N]% of body beats — [PASS / BLOCKER if >50%]; longest consecutive run [N] — [PASS / BLOCKER if 3+]
**Still mode:** [N]% of body beats — [PASS / WARNING if <30%]
**Motion density:** [N]% ambient/motivated — [PASS / WARNING if >60% with <4 visual states]

**Assembled vs Authored:**
- [ ] Predictable cycle: [yes — WARNING / no — pass]
- [ ] First body beat energy drop: [yes — WARNING / no — pass]
- [ ] Proof feels decorative: [yes — WARNING / no — pass]
- [ ] Avatar beats as filler: [yes — WARNING / no — pass]
- [ ] CTA feels arrived at: [yes — pass / no — FAIL]
- [ ] Hook contract honored: [yes — pass / no — FAIL]

**Taste-rule observations (if any):** [list observations from taste-rules.json — these are never blockers]

**Overall freshness verdict:** [authored / assembled / borderline — one sentence explaining why]
```

---

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
