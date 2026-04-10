---
description: Rules for audio-visual timing synchronization
globs: ["**/beat-map.json", "**/captions.json", "**/timeline.json", "**/voice.json"]
---

# Timing and Sync Rules

## Source of Truth

Actual narration timing is the source of truth.

Priority order:
1. source narration audio
2. extracted audio from final HeyGen avatar video
3. only if neither exists, temporary estimate for planning only

Estimated timing may help draft a script, but may not be used for final edit assembly.

## Beat Rules

Beat map requirements:
- phrase or thought-group level timing
- each beat needs a unique ID
- each beat should have one primary intent
- each beat should map to a visual plan

Recommended beat intents:
- hook
- setup
- demo
- proof
- comparison
- transition
- CTA

## Caption Rules

- captions must be time-bound
- captions should align to phrase boundaries where possible
- avoid captions that are too dense for short-form viewing
- split long phrases into readable chunks

## Visual Sync Rules

- demo action should appear when it is being referenced
- visual proof should appear during or immediately after the claim it supports
- do not let captions or overlays obscure the key interaction being described

## Silence and Gaps

Acceptable pauses must feel intentional.

Flag:
- dead air without visual purpose
- extended stillness without emphasis
- empty beats with no supporting motion or visual meaning

## Transition Timing

Transitions should not delay comprehension.

Use transitions:
- between scene changes
- for emphasis shifts
- for perspective changes

Avoid transitions:
- during critical UI interactions
- when a simple cut is clearer
- when multiple effects compete in a short span
