# YouTube Script Sub-skill

**Invoked by:** `/youtube script`

Write a full-length, retention-engineered YouTube video script from the project's approved source brief, a top-performing reference video, and the creator's demo flow notes.

This is a long-form YouTube script (8-20 minutes), not a reel script. It uses a different structure, pacing, and production language.

---

## Primary Goal

Produce a complete YouTube video script that:
- matches the structure of what performs on the channel topic (informed by reference video)
- incorporates the creator's planned demo flow precisely
- includes production cues throughout so the editor knows exactly what to show on screen
- is structured to retain viewers with pattern interrupts every 60-90 seconds
- includes chapter timestamps, a mid-CTA, a retention re-hook, and a strong outro
- is written for spoken delivery — every sentence sounds natural when said out loud

---

## Gate Check

Before starting, verify:
- `brief_approved` is in `gates_passed` in `project.json`
- `projects/<slug>/brief.md` exists
- `projects/<slug>/youtube/demo-flow.md` exists (from `/youtube demo-ingest`)

If `demo-flow.md` is missing, stop and run `/youtube demo-ingest` first.

---

## Load Reference Guides

Read all five before writing:
- `.claude/skills/youtube/references/algorithm-guide.md`
- `.claude/skills/youtube/references/retention-guide.md`
- `.claude/skills/youtube/references/voice-profile.md`
- `.claude/skills/youtube/references/jack-roberts-techniques.md`
- `.claude/skills/youtube/references/script-structure.md`

These inform: hook structure, pattern interrupt placement, CTA timing, retention drop-off strategy, the creator's spoken delivery style, jargon translation patterns, three-phase demo mechanics, Mits-specific catchphrases and vocabulary rules, and chapter templates with exact text.

---

## Required Inputs

1. **`projects/<slug>/brief.md`** — source brief from the reel pipeline
2. **Top-performing video URL** — user-provided YouTube URL to benchmark against
3. **`projects/<slug>/youtube/demo-flow.md`** — creator's demo steps

Ask the user for the top-performing video URL if they haven't provided it.

---

## Step 0 — Clarify Audience Level

Before writing anything, determine the technical level of the target audience.

Read `brief.md` for an audience definition. Then apply this rule:

- If `brief.md` defines a **technical audience explicitly** (e.g. "developers using the Claude API", "engineers evaluating infrastructure tools") → write at that level
- If `brief.md` is ambiguous OR defines a general/business audience → **default to beginner-friendly**

**Beginner-friendly means:**
- Explain concepts by showing what they replace, not by defining them abstractly
- Do not assume familiarity with APIs, YAML, credential management, or infrastructure concepts
- Use scenario framing ("imagine you have a support team...") to create relevance before introducing the product
- Technical viewers will still watch a beginner-friendly video — beginners will not watch a technical one

Document the audience level decision at the top of `script.md` before writing.

---

## Step 1 — Analyze the Top-Performing Reference Video

Extract the reference video's transcript and metadata:

```bash
python -m lib.assets youtube transcript <url> --out projects/<slug>/youtube/reference-transcript.txt
python -m lib.assets youtube fetch <url> --project <slug> --frames-every 30
```

From the transcript and metadata, extract:

**Structure analysis:**
- Hook type (first 30 seconds — what psychological mechanism does it use?)
- Chapter names and positions (from description or transcript breaks)
- Intro approach (does it promise, show credentials, or jump straight in?)
- Pattern interrupt types used (b-roll cues, graphics, camera changes, verbal pivots)
- Mid-video CTA placement (what percentage in?)
- Re-hook language at the 60% mark
- Outro structure (hard CTA + end-screen cue + next-video tease?)

**Content analysis:**
- Primary claim the video makes
- Proof strategy (demos, screenshots, data, testimonials?)
- Key tools or products named
- Claims that could be borrowed, improved, or countered
- Angles this video did NOT cover (gaps our video can own)

**Performance signals:**
- Video duration vs view count / like ratio suggests whether long or short works better for this topic
- Chapter timestamps indicate which sections viewers skip to (high-value sections)

Write a concise analysis to `projects/<slug>/youtube/reference-analysis.md` covering these points before writing the script.

---

## Step 2 — Define the Video's Core Promise

From `brief.md` and the reference video analysis, distill:

1. **Primary claim** — what is the single most valuable thing the video proves?
2. **Proof strategy** — which demo sections from `demo-flow.md` prove the claim most directly?
3. **Angle** — what does this video do that the reference video does NOT do?

The promise drives the hook, the chapter structure, and the outro CTA.

---

## Step 3 — Select the Hook Type

**Default to Problem-Agitation for beginner or general audiences.** Leading with a relatable problem creates relevance before introducing the product — the viewer understands why they should care before they're told what to care about. Announcement-first hooks work for audiences already following the product; problem-first works for everyone.

| Hook type | When to use | Opening feel |
|---|---|---|
| **Problem-Agitation** *(default)* | Viewer has a real pain this video solves | "If you're still doing Y manually, this video is for you" |
| **Shock/Contradiction** | Counter-intuitive claim the viewer won't expect | "Most people are using X completely wrong" |
| **Story Open** | Begin mid-action, viewer joins in progress | "Three weeks ago I tried to X. Here's what happened." |
| **Curiosity Gap** | Withhold the answer to create pull | "There's a feature inside X that almost nobody knows about" |
| **Social Proof** | Lead with credibility and stakes | "X million people use this tool. 90% miss the part that matters." |

Choose the type that best fits the brief's strongest hook direction AND that differs enough from the reference video's hook to stand out.

---

## Step 4 — Plan Chapter Structure

Map the video into chapters before writing. Every chapter needs:
- a keyword-rich title (for YouTube chapter navigation and SEO)
- an estimated duration
- the primary demo section from `demo-flow.md` that it covers (if any)
- a pattern interrupt at or before the 90-second mark within it

**Default structure for beginner-friendly educational AI videos:**

| Chapter | Position | What it covers |
|---|---|---|
| Hook | 0:00-0:30 | Problem framing — relatable scenario, not announcement |
| Intro / Promise | 0:30-1:30 | What you'll learn, two examples previewed, pricing or outcome teased |
| The Problem | 1:30-3:30 | Two concrete scenarios, why it was hard before, what changed |
| Platform Orientation | 3:30-4:00 | Brief tour of where the demo happens — orient before demoing |
| [Demo Section 1 name] | 4:00-6:30 | First proof block with live demo + narration layer |
| [Demo Section 2 name] | 6:30-9:00 | Second proof block, goes deeper |
| Pricing / Reality Check | 9:00-10:00 | Frame cost as surprisingly affordable |
| Outro + CTA | 10:00-11:00 | Restate the core shift, hard CTA, next video tease |

Adjust chapter count and timing to match the demo-flow sections and target video length. Follow the actual user journey in demo order — the reference video informs structure, not demo order.

---

## Step 5 — Write the Script

Write the full script following this structure:

### Hook (0:00-0:30)
- Deliver the chosen hook type
- Lead with the problem, not the product
- 3 ingredients: recognizable situation + unexpected contrast + concrete payoff
- Under 75 words spoken at ~150 wpm
- End with a promise: "In this video I'm going to show you exactly how to..."
- No "Hey guys" or generic opening — value from word one

### Intro / Promise (0:30-1:30)
- Who this is for (audience identity line — use "you" heavily)
- What they'll be able to do after watching
- Two concrete examples or outcomes previewed
- Brief credibility signal (optional — only if genuinely earned)
- Forward tease: "By the end of this, you'll see exactly how [specific result]"

### The Problem (before any demo)
Before demoing anything, establish the problem clearly:
- Two concrete scenarios the viewer can picture themselves in
- Why this was hard before — list what was required, not just that it was hard
- What changed — one clear statement of the shift
- Only then transition to the demo

### Platform Orientation (before every new demo platform)
Before demoing any tool or platform, orient the viewer:
- "This is what [platform name] looks like"
- Brief tour of where things are — don't assume familiarity
- Only then start the demo sequence

### Content / Demo Blocks

Each content block covers one demo section from `demo-flow.md`. Follow the actual demo steps in user journey order. Structure every block:

```
[CHAPTER TITLE CARD: Chapter name]

Setup line — why this matters before showing it
Transition into demo — "let me show you exactly what this looks like"

[DEMO: Specific step from demo-flow — what's on screen, what action happens]
Narration explaining why this works this way AND what would have been required before.
Do not describe what the viewer can already see. Explain the "why" and the contrast.

[DEMO: Next action]
Narration — what changed, what the result means, what this enables.

[DEMO: Key result moment]
Spoken payoff — "and this is the moment that matters because..."

Pattern interrupt (no later than 90 seconds into the block):
[GRAPHIC: Stat or key claim visual]
OR [B-ROLL: Context footage]
OR [CAMERA CHANGE]

Micro-summary before transitioning: "So what just happened there was..."
Forward hook into next block: "But here's where it gets even more interesting..."
```

**Dead air rule:** Any time the demo involves loading, processing, or connecting (anything the viewer watches but doesn't read or interact with), the narration must fill that time. Assume 30-60 seconds of narration needed per loading/processing step. Use this time to:
- Explain what's happening behind the scenes
- Contrast with what this used to require
- Bridge to the next concept
- Reinforce key benefits
- Ask and answer a rhetorical question the viewer is likely thinking

### Mid-CTA (~25% of total runtime)
Soft, conversational ask — does not interrupt momentum:
```
"If this is useful so far, hit the subscribe button — I post [topic] breakdowns every week."
```
Tie it to the content naturally — don't make it feel like an interruption.

### Retention Re-Hook (~60% of total runtime)
Verbal pattern interrupt to re-engage viewers who are drifting:
```
"Now here's the part that most people miss — and honestly it's the reason I made this video..."
OR
"Before I show you the most important step, I want to quickly mention..."
```

### Pricing Section
Frame pricing as a relief, not a reveal:
- Lead with the number
- Immediately contrast it with what the viewer expected or what alternatives cost
- Reframe: "that's [everyday comparison] — not a monthly subscription, not a seat license"
- Make it feel like the viewer just got good news

### Recap + Reframe
- Briefly restate the core shift (not a feature list)
- Reframe: what does this mean for the viewer's work?
- "Here's what actually changed" — one clear sentence
- Do not summarize features — summarize the implication

### Outro + CTA (Hard)
```
CTA action: [Follow / Subscribe / Link in description / Comment]
Why to act now: [what they'll get next, what they'd miss]
End-screen cue: "Check out [related video title] next — it's right here"
Next-video tease: one sentence on what's coming — always include this
```

---

## Production Cue Standards

Use these exact bracket formats throughout the script. They are instructions to the editor, not spoken text.

| Cue | What it means |
|---|---|
| `[DEMO: description]` | Show specific screen state from demo-flow.md — state what's visible and what action happens |
| `[B-ROLL: description]` | Cut to context footage — be specific about what type of footage |
| `[GRAPHIC: description]` | Show a text card, stat visual, or animated graphic |
| `[CHAPTER TITLE CARD: name]` | Show chapter title animation at chapter boundary |
| `[CAMERA CHANGE]` | Switch to a different angle or framing |
| `[LOWER THIRD: name / label]` | Show a lower-third name card or tool label |
| `[ZOOM TO: element description]` | Punch into a specific part of the screen |
| `[PAUSE FOR EFFECT]` | Brief hold — let this land |

Every `[DEMO: ...]` cue must reference a specific step from `demo-flow.md`. Do not write generic `[DEMO: show the tool]` — write `[DEMO: open Claude Projects, type the prompt from Section 2 step 1, wait for response to generate]`.

Every `[DEMO: ...]` cue that involves loading or processing must be followed by narration that fills the wait time — never leave a loading state with nothing said.

---

## Pattern Interrupt Placement Rules

At minimum, one pattern interrupt per 90 seconds. Track cumulative time as you write. When approaching 90 seconds without an interrupt, force one in:

- A `[GRAPHIC]` with a key stat or visual claim
- A `[CAMERA CHANGE]`
- A verbal pivot: "But wait — here's the thing most people don't know..."
- A `[B-ROLL]` insert

Pattern interrupts are not decoration. They are retention anchors. The viewer who was about to scroll hears a gear-shift and stays.

---

## Spoken Delivery Check (run before finalizing)

Before outputting the final script, do a spoken delivery check on every section:

1. **Read it out loud** (mentally simulate — would a human say this naturally?)
2. **Flag any sentence that would sound stiff when spoken aloud** — rewrite it
3. **Check for jargon** against the demo-ingest notes: which technical terms did the creator use naturally in their own words? Only those terms are in scope. Everything else gets a plain-language replacement.
4. **Check "you" density** — if a paragraph has more "it", "one", or "they" than "you", rewrite it toward the viewer
5. **Check sentence rhythm** — every 3-5 longer sentences should be broken by a short punchy one

Apply the voice profile from `.claude/skills/youtube/references/voice-profile.md` throughout.

---

## Retention Risk Annotations

After the full script, include a section listing the 3-5 highest drop-off risk moments:

```markdown
## Retention Risk Annotations

| Timestamp | Risk | Mitigation |
|---|---|---|
| 2:30 | Long setup before first demo visual | Add [GRAPHIC] at 2:20 to bridge |
| 6:00 | Second demo runs 4 minutes without interrupt | Insert camera change at 4:00 mark |
| 9:30 | Technical explanation could lose non-dev viewers | Translate jargon — add analogy |
```

---

## Output

Produce two files:

**`projects/<slug>/youtube/reference-analysis.md`:**
The reference video breakdown (Step 1). See format in Step 1.

**`projects/<slug>/youtube/script.md`:**

```markdown
# YouTube Script: [Project Slug]

**Audience level:** [beginner-friendly / intermediate / technical — and why]
**Hook type:** [Problem-Agitation / Shock / Story / Curiosity Gap / Social Proof]
**Structure:** [problem-first / announcement-first — and why]
**Target duration:** [minutes]
**Primary claim:** [one sentence]
**Proof strategy:** [how the demos prove the claim]
**Key angle vs reference video:** [what this video does differently]
**CTA:** [action + what viewer gets]

---

## Chapter Map

| # | Chapter title | Start | Duration | Demo section |
|---|---|---|---|---|
| 1 | [title] | 0:00 | 1:30 | — (hook + intro) |
| 2 | [title] | 1:30 | 3:00 | Section 1 from demo-flow |
| ... | | | | |

---

## Full Script

[Hook 0:00]
[Written script text with production cues inline]

[Intro 0:30]
[Written script text with production cues inline]

[Chapter 1 title: name — 1:30]
[Written script text with production cues inline]

... [continue for all chapters]

[Outro]
[Written script text with hard CTA + end-screen cue + next-video tease]

---

## Retention Risk Annotations

[Table as specified above]

---

## Claim Check

### Verified (from brief.md source or reference video)
- [claim — source]

### Creative positioning
- [line that is editorial framing, not product claim]
```

---

## Stop Condition

Deliver both `reference-analysis.md` and `script.md`. Present the script for approval.

Do not proceed to `/youtube hook` or `/youtube seo` until the script structure and chapter map are approved.
