---
name: qa-reel
description: Review a reel project for retention, timing, captions, assets, pacing, safe zones, proof clarity, implementation quality, and render readiness before export.
---

# QA Reel Skill

Use this skill after timeline assembly and before final render or delivery.

This QA pass is not only technical.  
It is also editorial.

The reel must be:
- understandable
- visually engaging
- retention-safe
- proof-led
- implementation-safe
- platform-ready

QA should catch both:
- **technical blockers**
- **editorial weaknesses that will reduce watch time**

---

## Primary Goal

Determine whether the reel is ready to render and publish by checking:

- timing accuracy
- visual continuity
- caption readability
- safe zones
- asset validity
- audio clarity
- retention structure
- proof visibility
- trust/objection handling
- CTA effectiveness
- transition implementation
- scene background correctness
- short-clip safety
- render/export blockers

QA is a **gate**, not a formality.

---

## Style-Aware QA

Read `project.json` for the `style` field before running QA. Thresholds change by style.

### Style-conditional thresholds

| Check | `cinematic-presenter` | `editorial-authority` |
|---|---|---|
| Visual change frequency | every 3-5s | every 1-3s |
| Avatar on-screen % | 60-70% | 30-45% |
| Max consecutive center-full | 2 (before face return) | 8 (full-frame is default) |
| Avatar absence limit | 8s (12s with b-roll) | 18s |
| SFX minimum (30-40s reel) | 6 | 8 |
| SFX minimum (40-55s reel) | 8 | 12 |
| Visual variety (distinct states) | 6-8 | 10-15 |
| Dead air tolerance | 0.5s | 0 (none) |
| Flash accent limit | 1 per reel | 3 per reel (flash resets are structural) |
| Split-screen spacing check | required | N/A (no split-screen) |
| Ken Burns check | required on static content | N/A (no Ken Burns) |
| Background type | Aurora/Beams for demos | Solid colors for all scenes |
| Transition variety rule | max 2 same enter in a row | hard-cut is exempt; max 3 flash-resets per reel |

When QAing an `editorial-authority` reel, do NOT flag:
- High avatar absence (up to 18s is expected)
- Many consecutive full-frame entries (up to 8 is expected)
- Lack of Ken Burns or ambient motion (static holds are fine in this style)
- Hard cuts everywhere (that's the baseline, not a problem)

When QAing an `editorial-authority` reel, DO flag:
- Any frame with no visual purpose (zero dead air tolerance)
- Visual change gap > 3 seconds
- Fewer than 10 visually distinct moments in a 30s+ reel
- Missing HeroTextCard on emotional keywords
- Missing FlashReset between major sections

---

## Global Rule References

This skill must follow these global rule files in addition to its local instructions:

- `.claude/rules/reel-workflow.md`
- `.claude/rules/timing-sync.md`
- `.claude/rules/qa-gates.md`
- `.claude/rules/visual-style.md`
- `.claude/rules/style-profiles.md`

### Rule precedence

When rules overlap, use this order:

1. **Workflow rules** — phase order and approval gates
2. **Timing rules** — actual narration timing and sync behavior
3. **QA gates** — hard export blockers
4. **Visual style rules** — layout, background, overlay, and display implementation
5. **Style profiles** — style-specific threshold overrides
6. **This skill** — editorial QA logic inside those constraints

---

## Workflow Alignment

This skill runs in **Phase 6 — QA**, after:
- source/brief approval
- script approval
- voice ingest
- beat map creation
- demo capture
- shot-list approval
- timeline assembly

### Important workflow rule
**QA always before render.**

Do not approve export until:
- assembly is complete
- the approved shot list has been respected
- all blocking QA gates pass

If required artifacts are missing, the reel cannot pass QA.

---

## Alignment With Assembly

This skill must validate that the final timeline follows the retention-first rules established in assembly.

That includes checking for:
- face-first social composition where appropriate
- proof before long explanation
- no flat middle
- regular visual refreshes
- visible outcomes
- strong trust moment treatment
- earned CTA
- safe implementation of display/background/transition logic

If the reel is technically correct but editorially weak, it should **not** pass cleanly.

---

## Responsibilities

- inspect timing consistency
- inspect narration-to-visual sync
- inspect captions and safe zones
- inspect asset references and existence
- inspect pacing and transition rhythm
- inspect presenter visibility and anchoring
- inspect proof density and clarity
- inspect overlay usefulness and overload
- inspect trust moment execution
- inspect CTA quality and payoff
- inspect display-mode correctness
- inspect scene background correctness
- inspect SFX existence and audibility
- inspect short-clip safety
- **inspect demo clips frame-by-frame** for personal data, browser chrome, and narrative mismatch
- **inspect motion budget** — verify no beat exceeds 1 hero / 1 support / 1 accent
- **inspect flash accent budget** — maximum 1 flash accent per reel
- **review b-roll library** for enhancement opportunities that would improve comprehension
- **audit visual design quality** — verify components look distinctive, not generic:
  - Typography has weight/size contrast (not flat same-weight throughout)
  - Colors align with project theme (`theme_primary`, `theme_secondary` from project.json)
  - Components feel designed for this specific reel, not default
  - If any component looks generic, flag for `frontend-design` review
- **audit theme consistency** — verify all accent colors, badge colors, and background palettes match the selected theme from project.json
- separate blockers from warnings
- write structured QA outputs (including b-roll enhancement suggestions)
- update project status

---

## Required Inputs

QA should read and reconcile:

- `output/timeline.json`
- `shot-list.md`
- `audio/source.wav`
- `audio/beat-map.json`
- `audio/captions.json`
- `assets/catalog.json`
- `project.json`

If available, also inspect:
- `audio/voice.json`
- `audio/ingest-report.md`
- `output/assembly-notes.md`
- render preview
- frame exports
- waveform or loudness summary
- overlay component usage

If timing conflicts exist, actual narration timing is the source of truth.

---

## Preconditions

QA may begin only when all of the following are true:

- `output/timeline.json` exists
- `shot-list.md` exists and was approved
- `output/motion-intent.md` exists and was reviewed
- `audio/source.wav` exists
- `audio/beat-map.json` exists
- `audio/captions.json` exists
- referenced assets exist or can be validated
- timeline assembly is complete enough to inspect

If these do not exist, QA should fail fast and report missing prerequisites.

---

## Frame-by-Frame Visual Inspection

QA must extract and inspect frames from every beat:

1. For each beat: extract a representative frame from the demo/broll clip at the midpoint of its visible time window
2. For demo beats: also extract the first and last visible frames to verify trim points show the right content
3. Inspect each frame for:
   - **Personal data:** names, emails, bookmarks, account info (BLOCKER if found)
   - **Browser chrome:** tabs, bookmarks bar, Windows taskbar, desktop wallpaper (BLOCKER if found)
   - **Narrative mismatch:** does the visible content match what the narrator is saying? (BLOCKER if mismatched)
   - **Visual clarity:** can the key UI element be read at mobile size?
   - **Motion budget:** count the simultaneous motion elements — flag if > 3

If a blocker is found, document the exact timestamp, the issue, and the fix (re-crop, re-capture with mock, or replace clip).

---

## B-Roll Enhancement Review

During QA, re-examine the b-roll scene library against the assembled reel:

1. For each avatar-only beat: would a b-roll insert improve the viewer's understanding of the concept being explained?
2. For each bridge/gap > 15 frames: would a brief b-roll flash add anticipation or visual texture?
3. Cross-reference the `broll_scenes/scene_list.json` classification data to find semantically relevant scenes
4. Only suggest b-roll that adds **comprehension value** — not decoration
5. Document suggestions in the QA report with: beat ID, scene ID, display mode, insert timing, and rationale

Note: B-roll should have been initially assigned during shot-list construction (Phase 4b). This QA review is the **second pass** — checking whether the assembled reel would benefit from additional b-roll that wasn't obvious at planning stage.

---

## Required Outputs

Each QA pass must produce:

- `blocking_issues`
- `warnings`
- `suggested_fixes`
- `pass_or_revise`
- `summary`

### Required files
- `output/qa_report.json`
- `output/qa-report.md`

### Project update
- `project.json` updated:
  - `status → qa_passed` if no blockers
  - `status → qa_failed` if blockers remain

Do not mark the reel ready if blockers remain unresolved.

---

## Markdown-First Requirement

This is a required handoff stage.

QA must produce a **markdown document** that is easy to copy and paste for review.

### Required markdown file
`output/qa-report.md`

This file should summarize:
- decision
- strongest blockers
- warnings
- exact fixes
- what is safe to keep
- what must change before render

The JSON report is for structured tooling.  
The markdown report is for human review.

---

## Severity Levels

### Blocker
A problem that makes the reel unpublishable, misleading, broken, or clearly low-quality.

### Warning
A problem that does not break delivery but is likely to reduce performance, polish, or retention.

### Pass
No blockers. Warnings may remain only if they are minor and explicitly noted.

---

## Blocking Issue Types

Treat these as blockers unless there is a documented reason not to.

### Timing / Sync
- narration noticeably out of sync with visuals
- beat boundaries do not match the spoken structure
- key proof visuals land too early or too late
- intro or CTA timing is broken
- transition timing obscures meaning
- beat map timing does not reflect actual audio timing
- dead air appears without visual purpose

### Assets / Timeline
- missing critical assets
- invalid timeline references
- broken file paths
- unresolved placeholders
- wrong asset assigned to a beat
- orphaned critical references
- duplicate or overlapping entries that break readability

### Captions / Readability
- unreadable captions
- captions outside safe zones
- captions covered by UI or overlays
- caption chunks too long to read in time
- emphasis styling obscures legibility
- captions are not properly time-bound

### Visual Clarity
- key UI is covered
- proof moments are impossible to see
- overlays block the actual point of the beat
- zoom targets miss the intended UI element
- important output/result is never clearly shown
- demo steps are not visually understandable
- scene order does not make sense

### Structural / Editorial
- hook fails to show or strongly imply proof
- middle becomes flat for too long
- trust beat is missing or unclear where required
- CTA is broken or disconnected from the reel
- ending cuts awkwardly or feels incomplete
- a major claim is not visually supported

### Audio
- narration unclear
- music competes with voice
- SFX overpower key lines
- audible clipping, corruption, or silence where action should land

### Implementation / Render Safety
- transition durations violate safe bounds
- transitions do not render visibly
- referenced SFX files are missing or silent
- short clips use unsafe fixed fade durations
- scene backgrounds are wrong for scene type
- BRollVideo containers are opaque when they must be transparent
- center-full entries are hidden incorrectly by avatar/full-screen logic
- render setup is likely to fail due to typing/import assumptions if that implementation still applies

---

## Warning Types

These do not always block export, but should be surfaced clearly.

### Pacing
- slightly rushed pacing
- too many similar transitions in a row
- too many support visuals
- proof moments move too quickly
- recap montage is slightly crowded

### Presenter Balance
- too much avatar presence during software-heavy proof
- too little avatar presence during explanation
- face disappears slightly too long
- split-screen ratio weakens presenter anchoring

### Graphics / Motion
- excessive effect usage
- unnecessary zoom punches
- overlays feel decorative rather than useful
- too many competing graphic elements
- repeated motion pattern feels mechanical

### Messaging
- weak CTA
- setup is slightly too long
- one proof packet could be clearer
- trust beat lands but could be stronger
- hidden-feature angle is not fully capitalized
- feature names could be more consistent

### Support Visual Value
- support visuals add little value
- b-roll is slightly too decorative
- repeated scene mood weakens variety

---

## Retention QA Standards

This is the core editorial layer.

### 1. Hook Check
The opening must create curiosity and show or imply value quickly.

Warn or fail if:
- the hook feels purely explanatory
- no meaningful proof is visible early
- the first seconds feel static
- the face is missing without a strong reason
- the opening visual does not match the spoken claim

### 2. Presenter Anchor Check
The presenter should remain the social anchor when appropriate.

Check:
- whether the face disappears too long
- whether full-screen demos run too long without face return
- whether split-screen keeps the presenter meaningfully visible
- whether the reel still feels like a creator reel, not a raw screen recording

Warn or fail if:
- the first 15 seconds stay away from the face too long
- long demo sections are not broken by presenter return, reaction, or major payoff
- the avatar is so small that it stops anchoring attention

### 3. Flat Middle Check
The middle of the reel must not become one long undifferentiated demo.

Check for:
- proof packets
- layout changes
- zoom emphasis
- result moments
- face return
- overlay variety
- pattern interrupts

Warn or fail if:
- 2+ consecutive beats feel visually identical
- the viewer mostly watches software operate with no new editorial reward
- the reel becomes a walkthrough instead of a payoff sequence

### 4. Proof Visibility Check
Every major claim should have visible proof.

Check:
- is the result shown?
- is the save/output shown?
- is the deck/report/result readable enough?
- does the viewer actually see the payoff?

Fail if:
- the narration promises something that the visuals never prove
- the proof moment is too small, too quick, or obscured

### 5. Trust Beat Check
If the reel makes an implicit promise of control, safety, or permission, that moment must land clearly.

Check:
- permission prompts
- approval requests
- confirmation dialogs
- visual isolation of sensitive actions

Warn or fail if:
- the trust beat is mentioned but not meaningfully shown
- the permission UI is too small or rushed
- the reel skips the objection-handling moment entirely

### 6. CTA Check
The CTA must feel earned.

Check:
- whether the CTA follows visible proof
- whether there is recap support before the ask
- whether the ask matches the reel’s actual value
- whether the ending feels complete

Warn if:
- CTA is too generic
- CTA does not reference the specific payoff
- ending relies only on “follow for more” without reinforcing what for

Fail if:
- CTA timing is broken
- end card is incomplete
- reel ends abruptly with no landing

---

## Timing and Sync Checks

Use actual narration timing as the authority.

### Required timing checks
- narration and timeline are aligned
- beat map timing matches actual transcript timing
- each beat still maps to a clear visual plan
- captions align to phrase boundaries where possible
- visual proof appears during or immediately after the claim it supports
- transitions do not delay comprehension

### Flag:
- dead air without visual purpose
- extended stillness without emphasis
- empty beats with no supporting motion or visual meaning

---

## Pattern Interrupt Check

QA must confirm the reel stays visually fresh.

### Check for visual refreshes such as:
- crop change
- zoom punch
- split/full layout change
- badge or overlay reveal
- cursor emphasis
- save/output confirmation
- recap flash
- face return

Warn if:
- the first 12–15 seconds go too long without meaningful visual refresh
- the middle relies on one visual mode for too long
- the reel feels rhythmically repetitive

Not every refresh must be flashy.  
It just must be editorially meaningful.

---

## Overlay QA

Check overlays for both usefulness and restraint.

### Pass criteria
- overlays reinforce the beat
- keyword emphasis is clear
- utility badges support proof
- progress chips help multi-step demos
- overlays do not cover the point of the screen

### Warn or fail if
- overlays are too sparse to support the explanation
- overlays are too dense and compete with captions
- overlay language is generic and adds no value
- more than two meaningful overlays compete at once

### Component-aware checks
Where relevant, confirm overlays match system intent:
- `NumberPopup` at number mentions
- `KeywordFadeIn` at key tool/feature mentions
- `BadgePopup` for concise labels/callouts

Do not fail a reel for not using a specific component unless the scene clearly needed it.

---

## Caption QA

Captions must be readable, intentional, and synced.

### Check
- timing sync
- chunk length
- safe zones
- contrast
- readability over all backgrounds
- keyword emphasis behavior

### Preferred standards
- short phrase chunks
- max 2 lines
- readable at mobile viewing size
- no collisions with badges or UI

### Block if
- captions are unreadable
- captions cover essential UI
- captions are mistimed enough to confuse meaning

---

## Safe Zone QA

Check the full reel for mobile-safe layout.

### Inspect
- top overlays
- bottom captions
- split-screen crops
- avatar framing
- badges near edges
- UI callouts near platform UI areas

Block if:
- essential content falls into unsafe regions
- captions or CTA are likely hidden by platform chrome
- top badges collide with app header zones

---

## Transition QA

Transitions should support rhythm, not call attention to themselves.

### Check
- variety
- appropriateness by beat
- readability through transitions
- no accidental confusion around beat changes

Warn if:
- the same transition repeats too often
- transitions feel decorative
- trust or CTA moments use overly flashy motion

Block if:
- a transition obscures the meaning of the shot
- key proof becomes unreadable during entry/exit

---

## SFX and Audio QA

Check all audio layers.

### Narration
- clear
- consistent level
- no clipping
- no distracting artifacts

### Music
- does not compete with narration
- supports pacing
- does not overpower proof beats

### SFX
- aligned to visible moments
- not random
- not too loud
- support proof, layout, or keyword moments

Warn if:
- there are too few editorial sound cues in proof-heavy reels
- SFX are repetitive
- trust moment lacks audio contrast it likely needs

Block if:
- voice intelligibility is compromised
- important moments are sonically confusing or broken

---

## Reward Moment Check

Certain moments deserve enough time to register.

### Check whether these moments breathe enough:
- deck reveal
- result appearance
- save/output confirmation
- permission prompt
- before/after comparison

Warn if:
- these moments are technically present but too rushed to land

Block if:
- the claimed payoff is effectively invisible because it passes too fast

---

## Hard QA Gates

These are hard blockers unless explicitly documented otherwise.

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

### Assets
- all referenced assets exist
- assets are linked to beat or scene purpose
- no orphaned critical references in timeline

### SFX and Transitions
- all SFX files referenced in timeline exist and are non-empty
- SFX are audible during playback
- every scene/layout change has at least one SFX or transition
- SFX volume levels are set per entry
- transitions render visibly
- no more than 2 consecutive visual entries share the same enter transition type
- transition durations stay within safe bounds:
  - `enterDur`: 3–10 frames
  - `exitDur`: 2–4 frames

### Scene Backgrounds
- demo scenes use white/light backgrounds
- avatar full-screen scenes use dark backgrounds only where appropriate
- no single background runs for the entire composition
- BRollVideo containers are transparent
- background transitions at layout boundaries are clean

### Short Clip Safety
- clips shorter than 30 frames use proportional fade durations:
  - `fadeIn = Math.min(15, Math.floor(durationInFrames * 0.3))`
- center-full entries are not incorrectly filtered out by avatar/full-screen hiding logic
- if the implementation requires it, timeline JSON typing/import assumptions are safe

### Edit Quality
- transition use is controlled
- SFX do not overpower narration
- music sits below the voice properly
- hook lands quickly
- ending feels deliberate

### Content Quality
- claims are not unresolved placeholders
- feature names are consistent
- comparisons are clear
- CTA matches the reel’s topic

---

## Visual Style Compliance

QA must confirm the composition respects the visual-style system.

### Check display behavior
- `center-full` is used when content truly needs full viewer attention
- split/default layouts preserve clarity
- responsive is not creating accidental crop or layout confusion
- center-full hides avatar correctly when intended

### Check backgrounds
- hook split-screen can use Aurora/white
- split-screen demo scenes use Aurora/light backgrounds
- center-full demo/b-roll scenes use Aurora + Beams or equivalent white/light treatment
- only CTA/outro/direct address uses dark GradientMesh-style backgrounds

### Check zoom usage
- punch-in zooms follow spoken references
- zoom targets point to real visible UI elements
- image-based zooms do not drift into empty space from bad coordinate mapping

---

## Beat-by-Beat QA Method

Review the reel beat by beat.

For each beat, verify:

- beat intent is clear
- narration and visuals align
- display mode is appropriate
- key proof is visible
- overlay support is appropriate
- captions are readable
- transitions help rather than hurt
- audio cueing makes sense
- the beat advances the reel

If a beat is doing too many jobs at once, flag it.

---

## Pass / Revise Decision Rules

### Pass
Use only if:
- there are no blockers
- the reel is technically sound
- the hook works
- the middle is not flat
- proof is visible
- trust beat is clear where needed
- CTA feels earned
- warnings are minor

### Revise
Use if:
- any blocker exists
- proof is weak or missing
- presenter anchor is broken
- timing harms clarity
- captions or safe zones fail
- ending is weak enough to reduce publish readiness
- implementation safety is not confirmed

---

## Suggested Fixes Guidance

Each issue must include:
- what is wrong
- where it happens
- why it matters
- the smallest effective fix

Good fixes are specific.

Examples:
- `Punch in 12 frames earlier on the saved file name`
- `Return avatar for 1.0–1.5s after the long center-full demo run`
- `Replace one repeated whip transition with fade`
- `Shorten caption chunk at beat-03 to 4–5 words`
- `Add recap flashes before CTA`
- `Use proportional fade on the 24-frame clip to avoid interpolation errors`
- `Switch the demo scene background to Aurora/Beams instead of dark GradientMesh`

Avoid vague notes like:
- `make it better`
- `improve pacing`
- `needs more energy`

---

## `output/qa_report.json` Required Structure

Write `output/qa_report.json` in this shape:

```json
{
  "decision": "revise",
  "summary": "Strong concept and clear proof, but the middle section becomes visually flat and the CTA is too generic.",
  "blocking_issues": [
    {
      "type": "proof_visibility",
      "beat_id": "beat-04",
      "issue": "The saved file moment is too brief to register clearly.",
      "why_it_matters": "This is the core payoff that proves the claim.",
      "suggested_fix": "Hold the saved file state 8–12 more frames and add a subtle punch-in."
    }
  ],
  "warnings": [
    {
      "type": "cta",
      "beat_id": "beat-07",
      "issue": "The CTA is broad relative to the reel's actual payoff.",
      "why_it_matters": "A more specific ask will convert better.",
      "suggested_fix": "Reference Claude workflows or hidden features instead of generic tips."
    }
  ],
  "checks": {
    "hook": "pass",
    "presenter_anchor": "warning",
    "proof_visibility": "warning",
    "captions": "pass",
    "safe_zones": "pass",
    "audio": "pass",
    "cta": "warning",
    "backgrounds": "pass",
    "sfx_transitions": "pass",
    "short_clip_safety": "pass"
  }
}


output/qa-report.md Required Structure

Write a markdown report using this structure:

# QA Report: [Project Slug]

**Decision:** [Pass / Revise]  
**Render Ready:** [Yes / No]

---

## Summary
[Short summary of overall readiness.]

## Blocking Issues
- [Type] [Beat/Scene] — [Issue] — [Smallest effective fix]

## Warnings
- [Type] [Beat/Scene] — [Issue] — [Suggested improvement]

## Retention Checks
- Hook: [Pass / Warning / Fail]
- Presenter anchor: [Pass / Warning / Fail]
- Proof visibility: [Pass / Warning / Fail]
- Trust beat: [Pass / Warning / Fail]
- CTA: [Pass / Warning / Fail]

## Technical Checks
- Timing sync: [Pass / Warning / Fail]
- Captions / safe zones: [Pass / Warning / Fail]
- Assets / timeline: [Pass / Warning / Fail]
- SFX / transitions: [Pass / Warning / Fail]
- Backgrounds / display: [Pass / Warning / Fail]
- Short clip safety: [Pass / Warning / Fail]

## Exact Fixes Before Render
1. [Highest priority fix]
2. [Next fix]
3. [Next fix]

## Notes
[Any final guidance for assembly revision or render handoff.]
QA Workflow
Step 1

Read:

output/timeline.json
shot-list.md
audio/beat-map.json
audio/captions.json
assets/catalog.json
project.json
Step 2

Validate technical integrity:

file references
lane integrity
timing continuity
caption presence
no placeholders
Step 3

Validate editorial structure:

hook
presenter anchor
proof packets
trust beat
CTA
Step 4

Inspect readability:

captions
overlays
safe zones
UI visibility
Step 5

Inspect rhythm:

transition repetition
flat sections
lack of refresh
overly dense effects
Step 6

Inspect audio:

voice clarity
music balance
SFX logic
Step 7

Inspect implementation safety:

backgrounds
display modes
short clips
center-full handling
visible transitions
Step 8

Write reports and decision:

blockers
warnings
fixes
pass/revise
Step 9

Update project.json

Validation Checklist

Before completing QA, verify:

Technical
 all referenced assets exist
 no invalid timeline entries
 no unresolved placeholders
 narration sync is acceptable
 captions exist and are readable
Editorial
 hook creates curiosity and shows value early
 presenter remains an anchor where needed
 middle does not go flat
 proof moments are clearly visible
 trust beat lands when relevant
 CTA feels earned and complete
Visual
 overlays help more than they distract
 captions stay within safe zones
 zooms hit the intended targets
 key UI is not covered
 transition usage is varied but controlled
 backgrounds match scene type
 display behavior is correct
Audio
 narration is clear
 music supports rather than competes
 SFX enhance proof and transitions
 no clipping or broken audio moments
Render safety
 short clips are fade-safe
 center-full scenes remain visible as intended
 no obvious implementation blockers remain
Stop Condition

Stop after:

output/qa_report.json is written
output/qa-report.md is written
project.json is updated
the decision is clearly stated

Do not claim the reel is final unless blockers are resolved.