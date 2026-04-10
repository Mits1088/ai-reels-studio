---
name: ingest-voice
description: Ingest narration audio or avatar video, extract and validate audio, generate transcript, beat map, captions, and speech timing notes, then produce markdown handoff documents for the retention-first reel pipeline.
---

# Ingest Voice Skill

Use this skill when:
- the script is approved
- real narration audio exists, or
- a HeyGen/avatar MP4 exists and must be used as the source of truth

This phase is not just file extraction.  
It is the point where the reel switches from estimated timing to **real spoken timing**.

That timing will drive:
- shot timing
- beat timing
- caption timing
- proof packet pacing
- transition timing
- SFX timing
- final editorial rhythm

---

## Primary Goal

Turn approved narration into a validated timing package for the reel.

That means producing:
- clean source audio
- transcript data
- beat map
- captions
- speech timing notes
- markdown handoff documents

The result should make downstream editing easier, not harder.

---

## Global Rule References

This skill must follow these global rule files in addition to its local instructions:

- `.claude/rules/reel-workflow.md`
- `.claude/rules/timing-sync.md`

### Rule precedence

When rules overlap, use this order:

1. **Workflow rules** — phase order and approval gates
2. **Timing rules** — actual narration timing and sync authority
3. **This skill** — ingestion, transcript, beat map, caption, and reporting decisions inside those constraints

---

## Workflow Alignment

This skill runs after:
- source/brief direction is approved
- script is approved

This skill must complete before:
- final shot-list approval
- timeline assembly
- QA
- render

### Important workflow rule
Once real narration exists, it becomes the pacing authority for downstream stages.

Do not allow:
- script-estimated timing
- guessed narration duration
- stale beat maps from an older audio export

to remain the working timing source after real audio exists.

---

## Core Principle

**Actual audio timing is the source of truth.**

Do not use script-estimated timing once real audio exists.  
Do not continue building the reel from guessed timing if real narration is available.

This skill establishes the real spoken structure.

---

## When to Trigger

Use this skill when:
- the user has approved the script
- the user has exported a HeyGen/avatar video
- the user has recorded narration separately
- the reel needs real beat timing before capture, assembly, or QA

Do not use this skill for:
- writing the script
- researching the source
- capturing product demos
- assembling the reel
- final QA

---

## Ingestion Paths

### Path A — Extract Only
Recommended when:
- the source is a HeyGen/avatar MP4
- the operator wants manual beat and caption control
- TTS phrasing needs human editorial timing

Outputs:
- `audio/source.wav`
- `audio/ingest-report.md`
- updated `project.json`

### Path B — Full Timing Pipeline
Recommended when:
- narration quality is clean enough
- transcription is reliable
- automated beats and captions will save time
- the team wants a draft timing package to refine

Outputs:
- `audio/source.wav`
- `audio/voice.json`
- `audio/beat-map.json`
- `audio/captions.json`
- `audio/ingest-report.md`
- optional `audio/timing-notes.md`
- updated `project.json`

### Path C — Hybrid
Recommended when:
- auto transcript is useful
- but beats/captions still need editorial correction
- or HeyGen/TTS delivery needs manual chunking refinement

Outputs:
- same as Path B, but mark `beat-map.json` and/or `captions.json` as draft-quality in the report

---

## Accepted Inputs

Voice source may be any of:

- raw narration WAV / MP3 / M4A
- avatar MP4
- HeyGen export MP4
- separate VO file plus avatar video
- revised voiceover re-export

### Common location
```text
projects/<slug>/audio/avatar.mp4

Preferred extracted output
projects/<slug>/audio/source.wav
Required Outputs
Audio output
audio/source.wav — extracted or normalized source audio
Structured timing outputs
audio/voice.json — transcript with timestamps when available
audio/beat-map.json — beat-level timing structure
audio/captions.json — caption chunks with start/end times
Markdown outputs
audio/ingest-report.md — required
audio/timing-notes.md — recommended when editorial notes matter
Project update
project.json updated:
status → voice_ready when usable
status → voice_needs_revision when timing or clarity problems block progress
Required Markdown Handoff

This skill must produce a markdown document that is easy to copy and paste into later phases.

Required document

audio/ingest-report.md

This document must clearly state:

input source used
ingestion path used
whether timing is final or draft
whether beats/captions are safe to use downstream
any speech issues that affect editing
whether re-export or cleanup is recommended
Recommended second document

audio/timing-notes.md

Use this when the narration contains important editorial timing observations, such as:

long pauses
rushed proof lines
unnatural TTS emphasis
awkward resets
strong emphasis words
moments that need visual breathing room
Responsibilities
ingest the correct source file
extract audio cleanly
normalize or prepare audio if needed
generate transcript data when applicable
generate or validate beat structure
generate or validate captions
identify pacing and pronunciation issues
identify important emphasis moments
identify timing that affects proof visibility
document whether downstream stages can trust the timing package
write markdown handoff docs
Ingestion Priority Rules

Use this source priority order:

approved standalone narration audio
extracted avatar audio from final avatar video
alternate narration export
older audio only if nothing newer exists
Rules
prefer the most final spoken version
if a revised voice export exists, do not keep using old timing
if separate clean narration exists, prefer it over noisier embedded video audio
if the avatar MP4 is the only source, extract from it and validate quality before proceeding
Audio Extraction Rules

Use ffmpeg-python when possible.
Fallback to raw ffmpeg CLI if needed.

Extraction target

Always create:

audio/source.wav
Preferred audio format
WAV
mono or stereo acceptable if consistent
stable sample rate suitable for transcription and waveform handling
Rules
overwrite stale extracted audio only when the source has changed or is explicitly newer
do not leave multiple competing “final” audio files without noting which is canonical
extracted audio must be non-empty and decodable
Full Timing Pipeline Rules

When generating transcript and timing data:

Transcript

Produce audio/voice.json with:

full transcript
phrase or word timing when available
confidence metadata when available
source file reference
Beat map

Produce audio/beat-map.json with:

unique beat IDs
start/end times
spoken text for that beat
beat intent if derivable
duration
notes when a beat is unusually fast, slow, or proof-heavy
Captions

Produce audio/captions.json with:

short readable chunks
start and end times
phrase-based grouping
mobile-safe reading cadence
emphasis fields if supported by the schema
Important

Auto-generated beats and captions are a starting point unless clearly high quality.
Do not assume automatic timing is editorially good enough without inspection.

Timing Authority Rules

These rules come directly from the reel timing system.

Required timing behavior
estimated timing is for planning only
actual narration timing becomes authoritative once audio exists
beat timing should reflect the real spoken cadence
proof visuals later must appear during or immediately after the spoken claim they support
transition timing must not obscure the meaning of the spoken line
shot-list and assembly must use real beat timing, not script guesses
If timing artifacts conflict

Use this authority order:

audio/source.wav
actual transcript / voice timing derived from that audio
audio/beat-map.json
audio/captions.json
older script-estimated timing
Beat Map Standards

This is a major requirement.

The beat map should support the reel system, not just transcript segmentation.

Each beat should ideally map to one clear job:
hook
setup
proof
mechanism
trust
recap
CTA
Rules
beats should follow spoken meaning, not arbitrary transcript length
do not merge multiple proof steps into one large beat if they need separate editing
split when the spoken rhythm clearly shifts
keep beats clean enough for assemble-reel to assign visuals confidently
note any line that may need an internal split during assembly
Good beat behavior
one core thought per beat
visible edit points
proof moments separated cleanly
trust moment isolated if relevant
Caption Standards

Captions must support mobile viewing and spoken rhythm.

Rules
max 2 lines
prefer short spoken chunks
avoid large subtitle blocks
split on meaning, not only silence
use phrasing that reads naturally with TTS delivery
do not let caption chunks run too long without refresh
preserve important nouns and action words
break proof steps into readable chunks
Preferred caption behavior
0.6–1.2 second readable chunks when possible
short phrases
clean timing transitions
strong alignment to spoken emphasis
Watch for
commas causing awkward subtitle grouping
overlong chunks from formal script punctuation
merged phrases that make the reel feel slow
Speech Quality Review

Review the audio not just for transcription, but for editorial usability.

Check for:
unnatural pauses
rushed sections
overacted TTS commas
robotic emphasis spikes
flattened energy
pronunciation issues
swallowed words
merged words from script spacing errors
awkward hard stops
long dead air
clipped endings
Especially inspect:
hook delivery
proof lines
trust line
CTA line

If the speech quality weakens the reel materially, flag it.

HeyGen / Avatar-Specific Rules

When the source is an avatar video:

Check:
extracted audio clarity
whether the spoken pacing matches the intended edit
whether the avatar export inserted unnatural pauses
whether words sound fused because of script formatting
whether emphasis landed on the right words
whether the CTA sounds complete rather than truncated
If issues exist

Document whether the fix belongs in:

script rewrite
TTS punctuation rewrite
avatar re-export
caption correction only
beat remap only

Do not blame everything on assembly if the problem starts in the audio.

Editorial Timing Notes

Create audio/timing-notes.md when any of the following are true:

proof lines are fast and need breathing room
trust line needs visual isolate
hook lands with a strong emphasis word
there are long pauses that affect cut rhythm
one spoken line contains multiple editable proof steps
captions need special handling
CTA needs a hold before or after it lands
Good timing note examples
The phrase "builds the expense report" lands fast -- give the result visual extra hold
"asks before taking action" has a natural slow-down and should be isolated as the trust beat
The hook has a strong emphasis on "one sentence" and supports a text hit there
There is an unnatural pause before "Excel file" -- consider tightening the audio or splitting captions carefully
Validation Rules

Before completion, validate all outputs.

Audio validation
audio/source.wav exists
file is non-empty
file is decodable
audio duration is plausible
no obvious corruption or silence-only export
Transcript validation
transcript exists if Path B or C used
transcript broadly matches the script
no major dropped sections
obvious recognition errors are noted
Beat validation
beat IDs are unique
start/end times are sequential
no overlapping beats unless explicitly intended by schema
beat durations are plausible
proof and CTA beats are not lost inside giant segments
Caption validation
captions are time-bound
captions are readable
chunks are not excessively long
chunk boundaries roughly match speech meaning
Editorial validation
hook timing is clear
proof lines are identifiable
trust moment is identifiable when relevant
CTA timing is identifiable
downstream editor can use this without guessing the structure
Decision Rules

At the end of ingestion, classify the result as:

Ready

Audio and timing are good enough for downstream stages.

Ready with Notes

Usable, but editorial issues are documented and should be respected later.

Needs Revision

Problems in delivery, timing, or transcript quality are strong enough that downstream work would be weakened.

This decision must be written into audio/ingest-report.md.

audio/ingest-report.md Required Structure

Deliver this markdown document:

# Voice Ingest Report: [Project Slug]

**Input source:** [avatar.mp4 / voice.wav / etc.]  
**Ingestion path:** [Extract Only / Full Timing Pipeline / Hybrid]  
**Timing status:** [Ready / Ready with Notes / Needs Revision]  
**Source of truth:** [Which file is canonical]  
**Duration:** [e.g. 32.4s]

---

## Summary
[Short summary of whether the audio is usable and what downstream stages should know.]

## Files Produced
- `audio/source.wav`
- `audio/voice.json`
- `audio/beat-map.json`
- `audio/captions.json`
- `audio/timing-notes.md`

## Speech Quality Review
- [Observation]
- [Observation]
- [Observation]

## Hook Timing
[How the hook lands and whether it is clean.]

## Proof Timing
[Where major proof phrases land and whether they need support.]

## Trust Beat
[Whether a trust beat is present and how clearly it lands.]

## CTA Timing
[Whether the CTA lands clearly or needs adjustment.]

## Risks / Issues
- [ ] [Specific issue]
- [ ] [Specific issue]

## Downstream Guidance
- [Assembly note]
- [Caption note]
- [QA note]

Only list files that were actually produced.

audio/timing-notes.md Recommended Structure

Use this when needed:

# Timing Notes: [Project Slug]

## Strong Emphasis Moments
- [timestamp] [word/phrase] — [why it matters]

## Proof Packet Timing Notes
- [timestamp or beat] [note]

## Trust Timing Notes
- [timestamp or beat] [note]

## Caption Notes
- [note]

## Assembly Notes
- [note]
Workflow
Step 1

Identify the correct final source audio or avatar file.

Step 2

Extract audio/source.wav.

Step 3

Choose ingestion path:

Extract Only
Full Timing Pipeline
Hybrid
Step 4

Generate transcript, beat map, and captions as appropriate.

Step 5

Review speech quality and editorial timing.

Step 6

Validate outputs.

Step 7

Write markdown handoff documents.

Step 8

Update project.json.

Project Status Update Rules

Update project.json:

status → voice_ready when usable
status → voice_needs_revision when blocking issues exist

Optional metadata to include:

canonical audio source
ingest path
duration
transcript generated: yes/no
captions generated: yes/no
beat map generated: yes/no
Important Rules
do not finalize timing from script estimates once real audio exists
do not silently keep stale beat/caption files from an older export
if the audio changed, regenerate or explicitly invalidate downstream timing artifacts
if extract-only is used, clearly remind the operator that beat map and captions still need to be created
if auto-generated captions are weak, say so
if the script punctuation caused TTS problems, document it
if the hook, trust beat, or CTA sound weak, document it
do not proceed into assembly automatically
Relationship to Other Skills
reel-script

Provides the approved script that the audio should match.

capture-demo

May use timing notes to understand where proof moments need visual support.

assemble-reel

Uses the beat map, captions, and timing notes as the real pacing foundation.

qa-reel

Uses the ingest report to determine whether later issues came from source audio or from editing.

Stop Condition

Stop after:

source audio is extracted
transcript / beat / captions are generated or explicitly deferred
markdown handoff documents are written
project.json is updated

Do not move into asset planning, timeline assembly, or QA automatically.