# YouTube Demo Ingest Sub-skill

**Invoked by:** `/youtube demo-ingest`

Transcribe the creator's voice recording about their planned demo flow into a structured document for use by the YouTube script skill.

This recording is **not** the final script. It is the creator's rough informal notes — spoken naturally — about what they plan to show on screen during the video. It might be 2-5 minutes of unscripted talk: "I'm going to start by opening the tool here, then I'll type this prompt in, then show how it builds the output, then cut to the results page..."

---

## Primary Goal

Turn the voice recording into:
- an ordered list of demo steps with screen state descriptions
- named demo sections that map to video chapter positions
- key emphasis moments the creator highlighted
- production notes the creator mentioned (what to cut, what to slow down, what's the payoff)

This document drives the `[DEMO: ...]` production cues in the YouTube script.

---

## Required Inputs

- Audio file path (WAV, M4A, MP3, or MP4 with audio track)
- Project slug

Typical location: `projects/<slug>/youtube/demo-recording.wav`

Ask the user for the file path if they haven't provided it.

---

## Step 1 — Extract Audio

If the source is a video file, extract audio first:
```bash
ffmpeg -i input.mp4 -ac 1 -ar 16000 -c:a pcm_s16le output.wav
```

---

## Step 2 — Transcribe

Use the project's Whisper transcription pipeline:
```bash
python -m lib.voice.transcribe projects/<slug>/youtube/demo-recording.wav --out projects/<slug>/youtube/demo-flow-raw.json
```

If `lib.voice.transcribe` is unavailable, fall back to Whisper CLI:
```bash
whisper projects/<slug>/youtube/demo-recording.wav --model base --output_format json --output_dir projects/<slug>/youtube/
```

---

## Step 3 — Structure the Transcript

After transcription, parse the raw transcript into structured demo flow:

**Find demo step markers** — phrases that indicate screen actions:
- "I'll show...", "then I...", "click on...", "open...", "this is where...", "you can see...", "now type..."

**Find screen state cues** — what specific UI, tool, or content must be visible:
- Tool names, page names, input fields, output states, result screens

**Find timing signals** — relative duration cues:
- "this takes about...", "then briefly...", "the main thing to show is...", "spend a bit more time here..."

**Find section breaks** — when the creator shifts to a new topic or area:
- "then for the second part...", "moving on to...", "the next thing is..."

**Find emphasis moments** — things the creator repeated or stressed:
- Repeated phrases, "this is the important bit", "make sure to show this clearly"

---

## Output

Produce `projects/<slug>/youtube/demo-flow.md`:

```markdown
# Demo Flow: [Project Slug]

**Recording source:** [filename]
**Recording duration:** [Xs]
**Transcription quality:** [Clear / Partial / Rough notes — note any unclear sections]

---

## Demo Sections

### Section 1: [Descriptive name]
**Estimated position in video:** [e.g., minutes 2-6, or "early demo", "main proof section"]
**Screen states required:**
- [What must be visible — specific tool, page, UI state]
- [What must be visible]

**Demo steps in order:**
1. [Action — specific enough for the camera operator to reproduce]
2. [Action]
3. [Action]

**Creator notes from recording:** [Any caveats, alternatives, or emphasis the creator mentioned]

---

### Section 2: [Descriptive name]
[Same structure]

---

## Key Emphasis Moments

Moments the creator clearly flagged as high-value — these become the script's proof beats:

1. **[Moment name]** — [What happens and why the creator emphasized it]
2. **[Moment name]** — [What happens and why]
3. **[Moment name]** — [What happens and why]

---

## Production Notes from Recording

- [Anything about what to emphasize on screen]
- [Pacing notes: "slow down here", "cut this fast"]
- [What the creator said the payoff moment is]
- [Any concerns or alternatives they mentioned]

---

## Open Questions

List anything that was unclear from the recording and needs creator confirmation before scripting:

- [ ] [Unclear step or ambiguous screen state]
- [ ] [Unclear section boundary]
```

---

## Quality Check

Before finalizing, verify:
- [ ] All sections have named screen states (not vague descriptions)
- [ ] Steps are specific enough to reproduce on screen
- [ ] Key emphasis moments are identified
- [ ] Any unclear items are listed as Open Questions

---

## Stop Condition

Stop after `demo-flow.md` is written. Present it to the user for a quick confirmation check — demo steps often need a clarification or two before scripting begins.

Do not proceed to `/youtube script` until the creator confirms the demo flow is correct.
