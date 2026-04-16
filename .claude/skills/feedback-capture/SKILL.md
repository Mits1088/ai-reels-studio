---
name: feedback-capture
description: Capture human review comments after any review round, classify by category and scope, write project review notes, and propose controlled updates to global taste memory.
---

# Feedback Capture Skill

Run after any major human review round: after a hook preview, after QA review, after watching a rendered or exported cut. Can run multiple times per project.

This skill handles human taste signals — what the reviewer noticed watching the reel, what felt premium, what felt plain, what should change. It is separate from QA (which handles technical correctness) and separate from post-render learning (which records structural outcomes after completion).

---

## When to Run

| Review trigger | When to suggest running |
|---|---|
| After Phase 5b (quick preview) | User watches the first rough cut and gives impressions |
| After Phase 6 (QA review) | User watches the QA cut and adds editorial notes beyond the QA blockers |
| After Phase 7 (render) | User watches the final export before publishing |
| After any revision round | User reviews a changed cut and gives feedback on whether it improved |

The QA skill generates technical findings. This skill processes human observations — what the reviewer felt watching it.

---

## Inputs

1. **Review comments** — free text from the human reviewer. Can be structured or prose. Examples: "the hook feels right but the body drags in the middle", "that proof section felt premium", "too much motion on the screenshot beats", "the CTA felt generic".
2. **Project slug** — which project the feedback applies to.
3. **Review round label** — `hook-preview`, `qa-review`, `final-render`, or a custom label like `revision-2`.

---

## Process

### Step 1 — Before reading comments: load memory context

Read `memory/creative-feedback.json` first. This gives you:
- The current hard_rules and soft_preferences — so you can recognize when feedback aligns with or contradicts them
- The feedback_log — so you can spot repeated signals across projects
- The components to use more / use less — so you can recognize when feedback reinforces or revises these

Read `projects/<slug>/output/review-feedback.md` if it exists — earlier review rounds may have already flagged related signals.

### Step 2 — Parse and classify each comment

For each comment (or each distinct point within a longer comment), identify:

**Category** — which aspect of the reel does this comment address? (See category table below.)

**Direction:**
- `positive` — this worked, felt strong, do more of this
- `negative` — this didn't work, felt weak, avoid this
- `suggestion` — change X to Y specifically

**Scope:**
- `project-specific` — applies only to this reel (product-specific, one-off observation)
- `potentially-global` — a repeatable pattern generalizable across future reels

**Strength:**
- `observation` — noticed something, low conviction; store locally, don't promote
- `soft-preference-candidate` — consistent preference that guides choices; promote after 2 independent signals (see definition below)
- `hard-rule-candidate` — feels strongly or recurs 3+ times; promote after 3 independent signals or explicit request

**Signal match check:**
- Does this align with an existing `memory/creative-feedback.json` entry? → **Reinforces existing**
- Does this contradict an existing entry? → **Contradicts existing** — flag and do not change silently
- Is this new? → **New signal** — project-local by default

A single prose comment may produce multiple classified entries — break it apart.

### Step 3 — Write project review notes

Always write to `projects/<slug>/output/review-feedback.md`. Create the file if it doesn't exist. Append a new dated section if the file already exists.

**Format:**

The file has two parts: a **maintained summary block** at the top (updated on every run) and an **append-only log** of dated review sessions below it. The summary block is what Claude reads first during revision rounds — it gives the state at a glance without reading every log entry.

```markdown
# Review Feedback: <slug>

## Summary (updated each run)

**Confirmed improvements:** [things the reviewer explicitly said got better since a prior round]
**Unresolved issues:** [negatives or suggestions that have not yet been addressed in the timeline]
**Candidate global learnings:** [potentially-global signals that have appeared 2+ times — ready to propose for promotion]
**Project-only notes:** [signals that are specific to this reel and should not become global rules]

---

## Log

### <date> — <review-round>

#### <Category>
**Comment:** [exact or close paraphrase of what the reviewer said]
**Direction:** positive | negative | suggestion
**Scope:** project-specific | potentially-global
**Strength:** observation | soft-preference-candidate | hard-rule-candidate
**Signal match:** reinforces [existing entry] | contradicts [existing entry] | new signal
**Status:** [project-local only] | [proposed for global memory — see below]
```

**On every run:**
1. Append a new dated section to the log
2. Rewrite the Summary block to reflect the current state — move resolved issues out of "Unresolved", add newly confirmed improvements, update candidate global learnings

Multiple comments from the same session → all in one dated section with separate entries per comment.

### Step 4 — Propose global memory updates

After writing the project notes, scan for entries that qualify for global promotion:

**Qualify when ANY of these are true:**
- `potentially-global` scope AND the same pattern already appears in `feedback_log` from a different project → propose as `soft_preferences`
- `hard-rule-candidate` AND the same signal has appeared 3+ times total → propose as `hard_rules`
- The reviewer explicitly says "remember this for all reels" or "this is always wrong" → propose as appropriate strength

**Do NOT propose when:**
- Scope is `project-specific`
- The comment contradicts an existing hard rule
- It's a single observation with no prior history
- The comment is product-specific (a brand's colors, a specific UI pattern from one product)

**Show the proposed diff before applying — never update silently:**

```markdown
## Proposed global memory updates

### Add to `soft_preferences`:
> "Proof sections should default to still or annotation-led motion — ambient drift on proof screenshots moves stats out of frame while the narrator is reading them."

**Promotion reason:** Flagged in gemma-4 review and again here. Two independent signals from different projects.
**Target key in creative-feedback.json:** `soft_preferences`

Apply? Confirm to update global memory, or decline to keep this project-local only.
```

**If multiple changes are proposed, list all of them before asking for confirmation.** Do not ask for confirmation per item — show everything, then ask once.

### Step 5 — Apply on confirmation

When the user confirms (or invokes with `--apply-global`):
1. Add new string entries to the appropriate array in `creative-feedback.json`
2. Append a dated entry to `feedback_log` with `source: "review-feedback"` and which entries changed
3. **Never remove or modify existing entries** unless explicitly instructed
4. **Never downgrade a hard_rule to soft_preferences** without explicit instruction
5. Show a brief summary: "Added 2 entries to `soft_preferences`, 1 to `feedback_log`."

---

## Categories

| Category | What it covers | JSON key target |
|---|---|---|
| `hook` | First 2-3 seconds: energy, logo, split-screen, first frame, scroll-stop power | `hook_notes` |
| `body_variation` | Component variety, shot families, pattern interrupts, layout changes | `soft_preferences`, `likes`, `dislikes` |
| `motion` | Ambient/motivated/still choices, zoom usage, drift on screenshots | `motion_notes` |
| `transitions` | Entry/exit presets, cut rhythm, SFX on cuts, seams | `soft_preferences`, `likes`, `dislikes` |
| `proof` | Evidence clarity, screenshot quality, fitness of visuals to narration | `soft_preferences`, `likes`, `dislikes` |
| `captions` | Readability, chunk size, suppression, emphasis, overlap with overlays | `caption_notes` |
| `component_usage` | Specific component choices, overuse patterns, underused components | `components_to_use_more`, `components_to_use_less` |
| `pacing` | Beat density, visual change frequency, holds, dragging sections | `soft_preferences`, `likes`, `dislikes` |
| `cta` | CTA feel, dwell time, connection to proof, generic vs. earned | `soft_preferences`, `likes`, `dislikes` |
| `overall_feel` | General premium/plain/brand-aligned impression | `likes`, `dislikes`, `soft_preferences` |

---

## Scope Rules

**Mark as `project-specific` when:**
- The feedback is about a product's specific colors, UI, or brand elements
- The feedback contradicts patterns that have worked well in other reels
- It's a one-off observation: "this particular b-roll clip felt off"
- The product is unique and the lesson doesn't generalize

**Mark as `potentially-global` when:**
- The feedback is about a repeatable pattern (zoom behavior, caption suppression, component overuse)
- It's phrased in general terms: "screenshot sections always feel static", "hooks are usually too clean"
- It matches a pattern already flagged during a different project

**Default is `project-specific`.** Only promote when there's clear evidence of a generalizable pattern.

---

## Strength Classification

Signal words to watch for:

| Strength | Indicators | Treatment |
|---|---|---|
| `observation` | "I noticed", "it felt like", "not sure if", "maybe" | Store in review notes; do not promote globally yet |
| `soft-preference-candidate` | "I prefer", "this feels better", "generally", "usually", "I like when" | After 2 **independent** signals → add to `soft_preferences` |
| `hard-rule-candidate` | "always", "never", "every time", "I hate when this happens", "this is wrong", "fix this permanently" | After 3 **independent** signals or explicit escalation → add to `hard_rules` |

When in doubt, classify lower (observation) rather than higher — a single session is not sufficient to create a permanent rule.

### What counts as an independent signal

A signal is independent when it comes from one of these three sources — and only when it could not be a paraphrase of a signal already counted:

| Source | Counts as independent when |
|---|---|
| **Separate review round** | A different session (different date, different cut) — not two comments in the same sitting |
| **Separate project** | The same pattern flagged on a different reel slug entirely |
| **Clearly distinct statement** | A new formulation that adds different framing, not a restatement of the same observation ("the zoom felt unnecessary" + "I prefer still frames on proof beats" = 2 independent; "the zoom felt unnecessary" + "the zoom was too much" = 1 signal, different words) |

**What does NOT count as independent:**
- Two comments from the same review session, even if worded differently
- A later comment that paraphrases a comment from the same project's earlier session (e.g., "still too much motion on screenshots" said at QA after saying "the screenshot zooms felt noisy" at preview)
- The reviewer elaborating on the same observation in the same message

**How to check:** Before counting a signal as independent, ask — "could this be the same underlying preference expressed twice?" If yes, merge them into one signal.

---

## Contradiction Handling

If new feedback contradicts an existing entry in `creative-feedback.json`:

1. **Flag explicitly**: "This contradicts the existing `hard_rule`: [existing entry]"
2. **Do not silently remove or modify** the existing entry
3. **Show both and ask** which should stand
4. If the user wants to override an existing hard_rule: confirm explicitly, then move the old entry to a `deprecated_rules` key (keep the history) before adding the new one

A reviewer's current preference does not automatically override a rule that was set from accumulated evidence. Surface the conflict; let the human decide.

---

## How Claude Uses Feedback During Planning

Before proposing a script, shot-list, component mapping, motion-intent, or assembly plan, Claude must:

1. **Read `memory/creative-feedback.json`** and identify:
   - Hard rules that constrain choices for this reel (non-negotiable)
   - Soft preferences that should inform defaults (override with documented justification)
   - Recent `feedback_log` entries (last 3-5) to see recent taste evolution
   - Components to use more vs. use less — these have real weight in component scoring

2. **Read `projects/<slug>/output/review-feedback.md`** if it exists and identify:
   - Signals from earlier review rounds in this project
   - Patterns flagged during earlier phases (e.g. "hook preview noted the body needs more variety")

3. **When presenting a plan**, briefly note 1-2 specific ways it applies prior feedback:
   - "I kept all screenshot proof beats in `still` mode per your gemma-4 feedback on ambient drift"
   - "I'm using AnnotationCircle on beats 5, 8, 11 since you flagged static proof sections as plain"
   - "I avoided using KeywordFadeIn as the primary overlay — you flagged it as overused"

Do not narrate the full memory read. One or two specific applications is enough. The signal that feedback is being used should be visible in the choices, not in a paragraph recap.

---

## One-Off vs. Durable Changes

Not every review comment should change the global memory. Use this heuristic:

| Signal type | Action |
|---|---|
| "This beat specifically felt wrong" | Fix the beat; store in project review notes; not global |
| "This section dragged for me" | Fix the pacing; store in project review notes; note as observation |
| "Screenshot sections always feel static in your reels" | Fix + store as potentially-global soft-preference-candidate |
| "I hate when the hook opens with just the avatar" | Fix + store as hard-rule-candidate (already in global memory) |
| "Remember this for all future reels" | Explicit promotion instruction — propose as hard_rule after user confirms |

---

## Output Files

| File | Written | When |
|---|---|---|
| `projects/<slug>/output/review-feedback.md` | Always | Every run — append new dated section |
| `memory/creative-feedback.json` | Only on confirmation | When global update proposed and user confirms |
