---
name: caption-polish
description: Polish auto-generated captions by correcting product spelling, splitting chunks for mobile readability, tagging emphasis words, and stripping ElevenLabs artifacts, producing edit-ready captions.json.
---

# Caption Polish Skill

Use this skill when:
- `audio/captions.json` exists from auto-transcription
- the captions need cleanup before assembly
- the user says "polish captions", "fix captions", "caption cleanup", or similar

This is **Phase 3b** — caption polish.
It runs after beat-map creation (Phase 3) and before demo capture (Phase 4).

Captions are not just transcription. They are a retention tool. Bad captions make viewers scroll away. Good captions make the spoken words land harder.

---

## Primary Goal

Transform auto-generated captions into edit-ready caption chunks that are:
- correctly spelled (especially product and tool names)
- properly chunked for mobile readability
- tagged with emphasis words
- free of transcription artifacts
- timed to phrase boundaries

The result should make assembly and QA easier — not require caption fixes at render time.

---

## When to Trigger

Use this skill when:
- auto-generated captions exist in `audio/captions.json`
- the user wants to review or improve caption quality
- assembly is approaching and captions haven't been polished
- QA flagged caption issues and captions need a dedicated pass

Do not use this skill for:
- generating captions from scratch (use `ingest-voice`)
- writing the script (use `reel-script`)
- assembling the timeline (use `assemble-reel`)

---

## Global Rule References

This skill must follow these global rule files:

- `.claude/rules/timing-sync.md` — caption timing authority
- `.claude/rules/reel-workflow.md` — phase order

### Rule precedence

1. **Timing rules** — caption sync and phrase boundary alignment
2. **Workflow rules** — phase order
3. **This skill** — editorial caption polish decisions

---

## Workflow Alignment

This skill runs in **Phase 3b — caption polish**.

Before starting:
- `audio/captions.json` exists (from `ingest-voice` Phase 2)
- `audio/voice.json` transcript exists (for reference)
- script reconciliation (Phase 2b) is complete — the transcript is the source of truth, not the script

After this skill completes:
- captions are ready for assembly (Phase 5)
- no further caption corrections should be needed at QA

---

## Required Inputs

- `audio/captions.json` — auto-generated caption chunks with start/end timing
- `audio/voice.json` — transcript with word-level timestamps (reference)
- `script.md` — for product/tool name spelling reference (but transcript wins for wording)
- `project.json` — for product context

---

## Responsibilities

- correct product and tool name spelling
- split long chunks into mobile-readable segments
- tag emphasis words
- strip ElevenLabs artifacts (`--` pause markers, filler sounds)
- ensure timing aligns to phrase boundaries
- verify no chunk is too long or too short
- produce polished `audio/captions.json`

---

## Core Principle

**Captions must match what was ACTUALLY spoken, not what was scripted.**

After script reconciliation (Phase 2b), the transcript is the source of truth. If the narrator said "ChatGPT" but the script said "GPT-4", the caption must say "ChatGPT".

---

## Polish Steps

Follow these steps in order.

### Step 1 — Strip artifacts

Remove or replace these transcription artifacts:

| Artifact | Source | Action |
|---|---|---|
| `--` | ElevenLabs pause markers | Remove entirely — they render as visible text |
| `...` (literal) | Transcription hesitation | Replace with clean phrase break (split into separate chunk) |
| `[inaudible]` | Whisper uncertainty | Listen again or use script.md to infer the correct word |
| `uh`, `um`, `ah` | Filler sounds | Remove unless they serve deliberate pacing |
| Double spaces | Formatting artifacts | Replace with single space |

### Step 2 — Correct product names

Cross-reference with `script.md` and known product names. Common corrections:

| Wrong | Correct |
|---|---|
| chat GPT, chatgpt | ChatGPT |
| chat gpt 4, GPT 4 | GPT-4 |
| claud, claude ai | Claude |
| gemeni, jemini | Gemini |
| eleven labs | ElevenLabs |
| hey gen, haygen | HeyGen |
| remotion | Remotion |
| perplexity ai | Perplexity |
| mid journey | Midjourney |
| dall-e, dolly | DALL-E |
| github copilot | GitHub Copilot |
| vs code | VS Code |
| notebooklm | NotebookLM |
| google stitch | Google Stitch |
| lm arena | LMArena |

**Rule:** If a product name appears in the reel and is not in this list, check the source URL or brief for the correct capitalization. Never guess.

### Step 3 — Split long chunks

Caption chunks must be readable on mobile at reel speed.

**Maximum chunk length:** 8 words OR 2.0 seconds — whichever is shorter.

**Preferred chunk length:** 3-6 words, 0.6-1.2 seconds.

Split at natural phrase boundaries:
- after commas
- after conjunctions (and, but, so, because)
- before prepositions that start a new thought
- after the subject before a long predicate
- at breath pauses in the audio

**Bad split:**
```
"If you're paying for AI tools you need to see this"  (11 words, one chunk)
```

**Good split:**
```
"If you're paying for AI tools"  (chunk 1 — 7 words)
"you need to see this"            (chunk 2 — 5 words)
```

**Bad split (mid-phrase):**
```
"If you're paying"          (breaks before the object)
"for AI tools you need"     (bridges two thoughts)
"to see this"               (orphaned)
```

**Good split (phrase boundaries):**
```
"If you're paying for AI tools"  (complete thought)
"you need to see this"            (complete thought)
```

### Step 4 — Adjust timing

After splitting, redistribute timing:

1. Use word-level timestamps from `audio/voice.json` to place split boundaries precisely
2. Each chunk's `start` should align to the first word in that chunk
3. Each chunk's `end` should align to the last word in that chunk (plus ~0.1s buffer)
4. Chunks should not overlap
5. Small gaps between chunks (< 0.15s) are fine — they give the eye a micro-rest

### Step 5 — Tag emphasis words

Mark words that should be visually emphasized in the caption display.

**Emphasis candidates:**
- Product names (ChatGPT, Claude, Gemini)
- Action verbs that carry proof (built, saved, generated, created, asked)
- Outcome nouns (deck, report, file, website, prototype)
- Numbers and stats (6x, 14%, free, zero)
- Negation words that set up contradiction (wrong, never, can't, won't)
- CTA action words (follow, comment, try)

**Emphasis format:** Add an `emphasis` array to each chunk listing the words to highlight:

```json
{
  "text": "ChatGPT built the entire deck",
  "start": 5.20,
  "end": 7.10,
  "emphasis": ["ChatGPT", "built", "deck"]
}
```

**Rule:** Maximum 3 emphasis words per chunk. If everything is emphasized, nothing is.

### Step 6 — Verify platform safety

Final checks:
- No chunk longer than 8 words
- No chunk longer than 2.0 seconds
- No chunk shorter than 0.3 seconds (too fast to read)
- No single-word chunks unless the word IS the emphasis (e.g. "FREE." or "WRONG.")
- All chunks fit within caption safe zones (bottom 15-25% of screen)
- No profanity or unintended words from transcription errors

---

## Validation Checklist

Before saving the polished captions, verify:

### Spelling
- [ ] All product names correctly capitalized
- [ ] No transcription misspellings remain
- [ ] Acronyms correct (AI, ML, API, LLM, UI)

### Chunking
- [ ] No chunk exceeds 8 words
- [ ] No chunk exceeds 2.0 seconds
- [ ] No chunk shorter than 0.3 seconds (except single-emphasis-word chunks)
- [ ] Splits happen at phrase boundaries, not mid-phrase
- [ ] Preferred chunk length: 3-6 words

### Artifacts
- [ ] No `--` pause markers remain
- [ ] No `...` literal strings remain
- [ ] No `[inaudible]` markers remain
- [ ] No filler sounds (uh, um) remain
- [ ] No double spaces

### Timing
- [ ] Chunk timing uses word-level timestamps from voice.json
- [ ] No overlapping chunks
- [ ] Gaps between chunks are < 0.15s

### Emphasis
- [ ] Emphasis words tagged per chunk
- [ ] Maximum 3 emphasis words per chunk
- [ ] Product names are always emphasized
- [ ] CTA action word is emphasized

### Content accuracy
- [ ] Captions match the TRANSCRIPT (what was spoken), not the SCRIPT (what was written)
- [ ] If script reconciliation flagged changes, captions reflect the spoken version

---

## Output

This skill produces a single file:

**`audio/captions.json`** — polished version replaces the auto-generated version.

The structure must match the existing schema:
```json
[
  {
    "text": "If you're paying for AI tools",
    "start": 0.00,
    "end": 1.48,
    "emphasis": ["AI tools"]
  },
  {
    "text": "you need to see this",
    "start": 1.50,
    "end": 2.95,
    "emphasis": ["see"]
  }
]
```

### Optional: caption-polish-report.md

If significant corrections were made, produce a short report:

```markdown
# Caption Polish Report: [project-slug]

## Changes Made
- Corrected [X] product name spellings
- Split [Y] long chunks
- Removed [Z] ElevenLabs artifacts
- Tagged [W] emphasis words

## Notable Corrections
- "chat gpt" → "ChatGPT" (5 instances)
- Removed "--" pause markers (3 instances)
- Split 2.8s chunk at beat-04 into two phrases

## Timing Adjustments
- [list any chunks where timing was shifted]
```

---

## Relationship to Other Skills

**ingest-voice**
Produces the raw `audio/captions.json` and `audio/voice.json` that this skill reads.

**reel-script**
Provides spelling reference for product names (but transcript wins for wording).

**assemble-reel**
Uses the polished captions directly in the caption lane of `output/timeline.json`.

**qa-reel**
Checks caption readability, safe zones, and sync — fewer QA issues when captions are pre-polished.

This skill should eliminate caption corrections at assembly and QA time.

---

## Stop Condition

Stop after:
- `audio/captions.json` is polished and saved
- validation checklist passes
- any significant corrections are noted

Do not proceed to demo capture or shot list automatically.
Caption polish is a cleanup step, not a gate — but it should be done before assembly begins.
