---
description: Motion modes, anti-patterns, stillness doctrine, and beat-level examples — motion as editorial language, not default polish
globs: ["**/motion-intent.md", "**/shot-list.md", "**/timeline.json"]
---

# Motion Grammar

Read during Phase 4c (motion-intent) and Phase 4b-iii (technical planning). Defines when motion is appropriate, when stillness is preferred, and what over-animation looks like.

Read alongside `.claude/rules/body-grammar.md` (component variety rules) and `.claude/skills/motion-intent/SKILL.md` (per-beat assignment). This file governs the **motion dimension** of body beats; SKILL.md implements it.

**Supersedes** the Ken Burns / ambient motion mandates in `body-grammar.md` → Hold Behavior Rule and Four Beat Categories. Where those rules say motion is required, this file governs instead.

---

## The Doctrine

**Motion is signal, not polish.**

When every beat drifts, no beat drifts with meaning. When most beats are still, a motivated zoom communicates: *look specifically here*. The viewer's attention system is directional — movement draws the eye, and if movement is always present, the eye stops following it.

Calm, settled framing is not lazy. It is confident. Stillness says: this composition is strong enough to hold attention without movement. Continuous drift says: we are not sure this image is interesting on its own.

**Hook motion is signature. Body motion is earned.**

The hook uses stylized, recognizable motion as brand identity. That energy does not carry into the body. Each body beat starts from stillness and earns its motion by having a specific reason for it.

---

## The Four Motion Modes

Every beat must be assigned exactly **one primary motion mode** before a preset is selected. This decision comes before the enter/exit preset — it governs what happens during the hold, which is where most motion fatigue originates.

| Mode | Definition | Use when |
|---|---|---|
| `still` | No camera motion during the hold. The composition rests. | Short beats (<1.5s). Beats where proof IS the composition. Annotation beats. Return beats. Any beat where the entry was already punchy. |
| `ambient` | Slow scale push (1.0 → 1.015–1.02) or very slow pan toward the focal point. Barely perceptible. | Long holds (>2.0s) with a specific focal point to drift toward. No other motion event fires during the hold. The preceding beat was relatively still. |
| `motivated` | Camera move tied to a specific narration event — a stat named, a UI element highlighted, a proof moment peaks. | Narrator names a specific element. Zoom coordinates pre-defined in Phase 4b-iii technical planning. There is a zoom *target*, not just a zoom reflex. |
| `transition-led` | Motion energy lives in the scene transition (wipe, punch, scale-pop), not in the hold. Hold is still. | Short beats (<2s) where the entry animation creates the momentum. After a high-energy edit point. When the reel has been ambient-heavy. |

### How to select a mode — decision order

1. Is this beat short (<1.5s)? → `still` or `transition-led`
2. Does the narrator name a specific element to look at, AND were zoom coordinates pre-defined in Phase 4b-iii? → `motivated`
3. Is the hold long (>2.0s), is there a clear focal point, and no other motion fires? → `ambient` (opt-in)
4. Does the entry transition carry enough energy that the hold needs nothing? → `transition-led`
5. Default → `still`

**`ambient` is opt-in, not the default for static content.** When in doubt, use `still`.

---

## When Stillness Is Preferred

Stillness is the premium default for body beats. Use it:

**Short beats (<1.5s):** Not enough screen time for drift to register as intentional — the image just looks slightly unstable.

**Annotation beats:** `AnnotationCircle` draw-on animation is already the motion event. Adding Ken Burns on top competes with the annotation and splits the viewer's attention.

**Strong proof moments:** When a screenshot contains a specific stat, chart bar, or UI result the viewer must read, drift moves it away from them. Still lets them process it.

**Emotional emphasis:** Avatar beats delivering a payoff line. Natural speech motion is sufficient — the face is the anchor, not a surface to animate.

**Return beats after proof sections:** The scale settle IS the energy reset. Adding drift dilutes the feeling of re-entry.

**Any beat where the entry was punchy (punch, scale-pop-overshoot, zoom-in):** The entry communicated kinetic energy. The hold should settle. Entry-into-drift is motion stacking.

**After 2+ consecutive ambient beats:** Stillness provides the viewer with a visual anchor. Without it, the camera reads as always searching.

---

## When Ambient Motion Is Allowed

Ambient motion must be earned. Allow it when ALL of the following are true:

1. The hold is **at least 2.0 seconds** (60 frames) — too short to read as intentional otherwise
2. There is a **specific focal point** to drift toward: a UI element, a key figure, a chart region — not "drift toward center"
3. **No other motion event fires** during the hold (no zoom_moment, no annotation draw-on, no overlay entry animation)
4. The **preceding beat was relatively still** — ambient-on-ambient streaks feel automatic, not editorial

**Cap:** No more than **2 consecutive body beats** with ambient motion active. After 2, at least one still or transition-led beat must follow. A third consecutive ambient beat is only allowed if there is a documented escalation reason (e.g. a single long explanation hold that spans a natural breath point) — this exception must be written in the motion intent document.

**Screenshot-heavy and proof sections:** Apply a stricter default. When 3 or more consecutive beats are screenshot-based proof beats, assign `still` or annotation-led motion as the default. Ambient drift is not the answer for proof sections — it moves the image away from the stat the viewer needs to read. Use `motivated` mode if there is a specific element to zoom to, `still` otherwise. Reserve ambient for proof sections only when the hold is extremely long (>3.5s) and the focal point is named.

**Note on b-roll:** If the b-roll clip has its own internal motion (camera movement, action, particles), assign `still` — the clip handles hold motion. Only add ambient Ken Burns to nearly-static b-roll clips.

---

## When Motivated Zoom Is Appropriate

A motivated zoom is a zoom_moment (defined in Phase 4b-iii technical planning) tied to a specific narration reference.

**Appropriate when:**
- Narrator explicitly names or points to an element ("look at this number", "this field right here")
- A key stat appears on screen and the narrator references it by value
- A UI walkthrough names sequential elements (prompt field → model selector → run button)

**Not appropriate:**
- Zooming for visual interest when no specific element is being named
- Zooming every screenshot because static shots "feel boring" — fix the screenshot, not the motion
- Applying zoom to screenshots without a strong focal point

**Hard rule:** Motivated zoom requires pre-defined coordinates in the technical planning table. If no zoom target coordinates exist in the shot list's Phase 4b-iii section, no motivated zoom may be assigned during motion intent. No improvised zoom targets at this phase.

---

## When Transition-Led Mode Is Appropriate

Use `transition-led` mode when:

- The entry transition (wipe-up, punch, zoom-in) is already the beat's motion event — adding hold drift stacks two events
- The beat is brief (<2s) and the entry animation will still be settling when most of the narration fires
- The reel needs rhythmic editing energy, not continuous drift
- After a high-density motion section, `transition-led` + still hold provides the breathing space

In `transition-led` mode: the hold is still, the exit is a clean fade. The edit is the motion.

---

## Over-Animation and Named Anti-Patterns

A beat is over-animated when removing any motion element still leaves the beat reading correctly. If the beat only makes sense *with* all three layers, it is probably the wrong composition — not a motion problem.

These patterns are named so they can be identified and flagged by name during motion review and QA.

### Zoom Reflex
Applying a motivated zoom or Ken Burns to a screenshot because the shot "feels static" — not because there is a specific narration target. The symptom: zoom coordinates are "center of image" or vague, not a named element.

**Fix:** No zoom without a named target. Use `still` mode, or replace the screenshot with one that has a clearer focal point.

### Stacked Motion
Combining `zoom-in` entry preset + ambient drift during the hold on the same beat. Three zoom events: entry scale-down, continuous drift, and sometimes a zoom_moment mid-hold. The viewer's eye cannot settle on any of them.

**Fix:** Choose one zoom event per beat maximum. If the entry preset is `zoom-in`, the hold must be `still`. If there is a zoom_moment (motivated), the entry should be a non-zoom preset (`wipe-up`, `fade`, `slide-up`).

### Drift Without Purpose
Applying slow Ken Burns to a hold shorter than 1.5s. There is not enough screen time for the drift to register as intentional — it just makes the image look unstable.

**Fix:** Holds under 1.5s use `still` or `transition-led` mode. Ambient drift requires at least 2.0s.

### Proof Smear
Using a motivated zoom on a proof screenshot but zooming away from the stat or element the narrator is describing — toward generic UI or empty space. The zoom obscures the proof instead of directing attention to it.

**Fix:** Zoom coordinates in the technical planning table must name their target element explicitly. "center" is not a valid target. If the target cannot be named, the zoom should be removed.

### Transition-and-Hold Conflict
Using a punchy entry (punch, scale-pop-overshoot, zoom-in) and then adding ambient drift during the hold. The entry communicates kinetic energy; the drift communicates slow contemplation. They fight each other and the viewer reads neither.

**Fix:** Punchy entries → `still` holds. Gentle entries (fade, smooth-push) → ambient holds are permitted if the shot is long enough.

### Camera Always Searching
Multiple consecutive beats using ambient drift in different directions — slow zoom-in, then pan right, then slow zoom-out. The camera never settles, which reads as editorial anxiety rather than confidence.

**Fix:** After 2 consecutive ambient beats, insert a still beat. Variety of drift directions does not solve ambient overuse — the cap applies regardless of direction.

### Motion as Rescue
Adding zoom or drift to a composition that is mismatched with the narration, hoping movement will cover the weak component choice. Motion cannot rescue a semantic mismatch — it makes a confusing beat more energetic.

**Fix:** If motion is being added to "compensate" for a weak visual, return to component mapping and select the correct component for the beat.

---

## Hook Motion vs Body Motion

### Hook motion
The hook is signature territory. Its motion is stylized and recognizable — it establishes visual identity:
- Bouncing logo (continuous energy, brand signature)
- Ken Burns push toward the hero UI element (establishes proof setup from frame 0)
- SFX hit on frame 0
- Avatar split-screen with natural speech energy

These are properties of the hook zone specifically. They are **not inherited** by body beats.

### Body motion
Body beats earn their motion independently of the hook. A body beat does not get ambient drift because the hook was energetic. The question is always: what is *this specific beat's* motion doing?

**The hook-to-body transition should be perceptible.** The first body beat (typically a setup or direct-address beat) should usually be `still` or `transition-led` — it creates contrast with the hook's continuous motion and signals to the viewer: *the substance starts now*.

---

## Beat-Level Motion Mode Examples

### Screenshot with specific proof callout → `motivated`

```
Narration: "6x less memory"
Shot: benchmark screenshot (longbench.png)
Motion mode: motivated
Reason: narrator names a specific stat — zoom coordinates pre-defined at memory-comparison bar
Enter preset: wipe-up (not zoom-in — entry and hold should not both zoom)
Hold: motivated zoom fires at 0.4s → x:44, y:20, scale:1.9, holdFor:2.0
Notes: avoids Stacked Motion (wipe-up entry does not compete with motivated hold zoom)
```

### Avatar explanation beat → `still`

```
Narration: "Here's why that matters"
Shot: AvatarVideo full-screen (pivot line)
Motion mode: still
Reason: face IS the whole message. Natural speech motion is sufficient ambient presence.
Adding drift competes with eye contact and dilutes the authority of the statement.
Enter preset: fade (enterDur: 3)
Hold: still
```

### Stat card / HeroTextCard → `transition-led`

```
Narration: "Zero accuracy loss"
Shot: HeroTextCard
Motion mode: transition-led
Reason: scale-pop-overshoot entry IS the motion event. The spring entrance communicates
the impact of the stat. Hold should settle immediately to let the text read.
Enter preset: scale-pop-overshoot (enterDur: 5)
Hold: still (card settled, text legible)
```

### Long UI walkthrough → `motivated` (conditional)

```
Narration: "Type your prompt here, select a model, then hit run"
Shot: Demo video (product UI walkthrough)
Motion mode: motivated (if clip does not have its own cursor motion)
        still (if clip has cursor motion guiding the eye)
Reason: if the clip's cursor already follows the narration path, the clip handles
the motion event — add still mode. If it does not, define zoom_moments matching
each named element (prompt field → model dropdown → run button) pre-defined in Phase 4b-iii.
```

### Cinematic b-roll with rich internal motion → `still`

```
Shot: Abstract AI process footage (NotebookLM cinematic clip)
Motion mode: still
Reason: clip has its own internal motion (camera move, particles, abstract animation).
Adding Ken Burns on top creates Stacked Motion. still mode lets the clip breathe.
```

### Long product screenshot (>2.5s hold) → `ambient` (earned)

```
Narration: (extended explanation over a results dashboard)
Shot: FramedImage of results table
Motion mode: ambient
Reason: hold is 3.1s, specific focal point (top-left results cell), no other motion fires,
preceding beat was transition-led. All four ambient conditions satisfied.
Drift direction: toward top-left cell (focal point, not generic center drift)
Scale: 1.0 → 1.018 over 3.1s
```

---

## Motion Reflection Step

At the end of Phase 4c (motion-intent), before presenting the document for user review, write a brief reflection under the heading `## Motion Review`.

**Requirements:**
- Every entry must name a **specific beat ID** and a **specific reason tied to that beat's content**
- Generic phrases are banned: "the content required it", "felt right", "best fit", "natural choice", "to add energy" — these do not count
- If "motion doing real work" cannot be filled with specific beat IDs and specific narration references, the reel's motion needs review — it means all motion is ambient or decorative

**Format:**

```markdown
## Motion Review

**Still beats:** [name 2–3 beats with still mode — beat ID + one specific reason]
**Motion doing real work:** [name 1–2 beats where the mode improves comprehension or proof clarity — beat ID + what specifically the motion directs attention to]
**Motion reduced:** [name 1–2 beats where motion was downgraded from what old defaults would have produced — beat ID + what was removed and why]
```

**Bad example (too generic — do not write this):**

```
Still beats: beat-03, beat-07, beat-09 — all felt calmer without motion
Motion doing real work: beat-05 — the zoom helped with the screenshot
Motion reduced: beat-08 — removed because it was too much
```

**Good example (concrete — write this):**

```
Still beats: beat-02 (avatar pivot line — face is the whole message, drift would compete with eye contact); beat-07 (return beat after proof section — the scale settle IS the energy reset, adding drift dilutes it)
Motion doing real work: beat-05 (motivated zoom to the memory-comparison bars at x:44 y:20 — narrator names "6x less memory", zoom arrives at the exact bar); beat-09 (wipe-up entry carries the demo section's kinetic energy, hold settles immediately — transition-led mode)
Motion reduced: beat-03 (hold is 1.1s — ambient drift at this duration looks unstable, not intentional; assigned still); beat-06 (removed ambient from proof screenshot — drift would move the pricing row out of frame while narrator is reading it aloud)
```

This is not a QA checklist. It is editorial accounting that forces the question: does the motion in this reel communicate anything specific, or is it ambient polish?
