---
name: script-reconcile
description: Diff the approved script against actual spoken audio transcript word-by-word, flag changes that affect captions, overlays, and proof beats, and produce a reconciliation report that locks the source of truth for all downstream phases.
---

# Script Reconcile Skill

Use this skill when:
- voice ingest (Phase 2) has produced a transcript (`audio/voice.json`)
- the approved script (`script.md`) exists
- the reel needs to reconcile what was WRITTEN vs what was SPOKEN

This is **Phase 2b** — script reconciliation.
It runs immediately after voice ingest (Phase 2) and before beat mapping (Phase 3).

This phase exists because HeyGen and ElevenLabs do not always produce exactly what the script says. Words get dropped, swapped, mispronounced, or rephrased. If these differences go unnoticed, downstream phases build on false assumptions:
- Captions show words the narrator didn't say
- Overlays reference features that were dropped
- Beat text doesn't match the audio timing
- QA catches mismatches that should have been caught here

---

## Primary Goal

Produce `audio/reconciliation.md` that:
- documents every difference between the approved script and the actual transcript
- classifies each difference by severity
- declares which version wins for downstream use
- flags critical changes for user decision
- locks the source of truth for captions, beat text, and overlays

**After this phase, the transcript wins.** All downstream references must match what was ACTUALLY spoken, not what was written.

---

## When to Trigger

Use this skill when:
- `audio/voice.json` or a transcript exists from Phase 2
- `script.md` exists and was approved
- the reel needs to verify script vs audio alignment before beat mapping

Do not use this skill for:
- writing the script (use `reel-script`)
- extracting audio (use `ingest-voice`)
- polishing captions (use `caption-polish`)
- building the beat map (that's Phase 3, after this)

---

## Global Rule References

This skill must follow:
- `.claude/rules/reel-workflow.md` — phase order, transcript authority
- `.claude/rules/timing-sync.md` — actual audio is source of truth

### Rule precedence

1. **Workflow rules** — transcript wins after reconciliation
2. **Timing rules** — actual narration timing authority
3. **This skill** — reconciliation decisions inside those constraints

---

## Workflow Alignment

This skill runs in **Phase 2b — script reconciliation**.

Before starting:
- `audio/source.wav` exists (from voice ingest)
- `audio/voice.json` transcript exists (from voice ingest)
- `script.md` exists and was approved

After this skill completes:
- Beat mapping (Phase 3) uses the RECONCILED transcript, not the original script
- Caption polish (Phase 3b) uses reconciled wording
- All downstream overlays, beat text, and proof references match actual spoken words

---

## Required Inputs

- `script.md` — the approved script (what was intended)
- `audio/voice.json` — the transcript with word-level timestamps (what was actually spoken)

---

## Reconciliation Process

### Step 1 — Extract comparable text

From `script.md`: extract the ElevenLabs script body (the spoken content, not metadata or stage directions).

From `audio/voice.json`: extract the full transcript text in reading order.

### Step 2 — Word-by-word diff

Compare the two texts word by word. For each difference, classify it:

| Classification | What happened | Severity | Example |
|---|---|---|---|
| **Exact match** | Word spoken as written | None | Script: "Claude" → Spoken: "Claude" |
| **Minor variation** | Contraction, filler, or natural speech adaptation | Low | Script: "it is" → Spoken: "it's" |
| **Word substitution** | Different word with same meaning | Medium | Script: "creates" → Spoken: "builds" |
| **Word addition** | Extra word not in script | Medium | Script: "really fast" → Spoken: "really really fast" |
| **Word deletion** | Word from script not spoken | Medium | Script: "completely free" → Spoken: "free" |
| **Tool name change** | Product or feature name changed | **High** | Script: "Claude Code" → Spoken: "Claude" |
| **Number/stat change** | Specific claim changed | **High** | Script: "6x faster" → Spoken: "much faster" |
| **Phrase dropped** | Entire phrase or sentence missing | **High** | Script: "And the best part — it asks permission first." → Not spoken |
| **CTA change** | Call to action wording changed | **High** | Script: "Comment AI" → Spoken: "Comment below" |
| **Meaning reversal** | Opposite meaning from script | **Critical** | Script: "it never accesses your files" → Spoken: "it accesses your files" |

### Step 3 — Flag high-severity changes

For every **High** or **Critical** change, document:
- What the script said
- What the narrator actually said
- Which beats are affected (by timestamp reference to beat-map timing)
- Whether downstream phases need adjustment
- Whether the change weakens or strengthens the reel
- **Recommendation:** accept the spoken version, or flag for re-record

### Step 4 — Check proof-critical content

For every beat that the shot list will tag as `proof`, `trust`, or `demo`:
- Is the specific claim still present in the spoken version?
- If the narrator says "it compresses data" but the script said "6x less memory" — the specific proof (the "6x" number) was lost
- Flag these specifically — they will cause MISMATCH scores at shot-list fitness audit if not caught here

### Step 5 — Check tool names

Every product or tool name mentioned in the script must appear correctly in the transcript:
- ChatGPT not "chat GPT"
- Claude Code not "Claude"
- Gemini not "Jemini"
- Specific feature names must match

If a tool name was dropped or mispronounced, flag it — it affects overlays, captions, and whether the audience knows what tool is being discussed.

### Step 6 — Lock the source of truth

After classification:
- **Low severity changes:** Accept the spoken version silently. No user action needed.
- **Medium severity changes:** Document them. Accept the spoken version unless the user overrides.
- **High severity changes:** Present to the user. Recommend accept or re-record.
- **Critical severity changes:** Block downstream progression until the user decides.

---

## Decision Rules

At the end of reconciliation, classify the result:

### Clean
- No high-severity changes
- Script and transcript are functionally identical
- Downstream phases can proceed without concern

### Accepted with Notes
- Some medium or high-severity changes documented
- All changes are acceptable (no meaning reversals, no critical proof lost)
- Downstream phases should use the transcript version
- Beat text, captions, and overlays must reference spoken wording

### Needs User Decision
- One or more high-severity changes that could weaken the reel
- User must decide: accept the spoken version, or re-record
- Do not proceed to beat mapping until the user decides

### Needs Re-Record
- Critical changes that reverse meaning or drop essential content
- The spoken audio does not support the reel's proof promise
- Re-recording is recommended before proceeding

---

## Output

### Required file

`audio/reconciliation.md`

### Required structure

```markdown
# Script Reconciliation: [project-slug]

**Script version:** script.md (approved)
**Transcript source:** audio/voice.json
**Result:** [Clean / Accepted with Notes / Needs User Decision / Needs Re-Record]

---

## Summary

- Total words in script: [count]
- Total words in transcript: [count]
- Exact matches: [count] ([percent]%)
- Minor variations: [count]
- Medium changes: [count]
- High-severity changes: [count]
- Critical changes: [count]

---

## High-Severity Changes

| # | Script said | Narrator said | Severity | Beats affected | Recommendation |
|---|---|---|---|---|---|
| 1 | "6x less memory" | "much less memory" | High — proof number lost | beat-05 (proof) | Accept but note: shot-list must not assign "6x" chart |
| 2 | "Comment AI" | "Comment below" | High — CTA changed | beat-12 (CTA) | Accept — "below" is fine for Instagram |

---

## Medium Changes

| # | Script said | Narrator said | Severity | Note |
|---|---|---|---|---|
| 1 | "creates" | "builds" | Medium — synonym | Accept |
| 2 | "completely free" | "free" | Medium — modifier dropped | Accept |

---

## Proof-Critical Check

| Beat (estimated) | Script claim | Spoken claim | Proof intact? |
|---|---|---|---|
| ~5-8s | "6x less memory" | "much less memory" | NO — specific number lost |
| ~15-18s | "peer-reviewed at ICLR" | "peer-reviewed at ICLR" | YES |

---

## Tool Name Check

| Tool | Script spelling | Transcript spelling | Match? |
|---|---|---|---|
| ChatGPT | ChatGPT | ChatGPT | YES |
| Claude Code | Claude Code | Claude | NO — "Code" dropped |

---

## Downstream Impact

- **Captions:** Must use transcript wording, not script wording
- **Overlays:** [list any overlay text that must change]
- **Beat text:** [list any beats whose text must be updated]
- **Shot-list impact:** [list any proof beats where the claim changed]

---

## Decision Required

[If Needs User Decision or Needs Re-Record, list the specific decisions needed]
```

---

## Relationship to Other Skills

**ingest-voice**
Produces the transcript (`audio/voice.json`) that this skill reads.

**reel-script**
Produces the approved script (`script.md`) that this skill compares against.

**caption-polish**
Uses reconciled wording — must not reference script wording if it differs from spoken.

**shot-list**
Uses reconciled beat text — asset fitness audit must match what was SPOKEN, not written.

**assemble-reel**
Uses reconciled overlay text and caption wording.

This skill prevents downstream phases from building on words that were never spoken.

---

## Stop Condition

Stop after:
- `audio/reconciliation.md` is produced
- all high-severity changes are documented
- result classification is stated (Clean / Accepted / Needs Decision / Needs Re-Record)
- if Needs User Decision: present the decisions and wait

Do not proceed to beat mapping until reconciliation is resolved.
The transcript is the source of truth for everything downstream.
