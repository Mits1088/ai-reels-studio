---
name: source-brief
description: Research a source URL for reel-worthy claims, visible proof, trust moments, assets, and hook direction, then produce markdown documents that drive the full retention-first reel pipeline.
---

# Source Brief Skill

Use this skill when the user provides a URL as the starting point for a new reel.

This is **Phase 0**.  
It runs before `reel-script` and feeds everything downstream.

This phase is not just research.  
It is **editorial source analysis**.

The goal is to decide whether the source can support a strong reel and to turn that source into:
- a clear reel direction
- a proof-led brief
- a capture-aware handoff
- copy-paste-ready markdown documents

---

## Primary Goal

Turn a source URL into a retention-first reel foundation.

The source brief should answer:

- what is the strongest claim here?
- what is the clearest visible proof?
- what is the best hook direction?
- what type of reel does this naturally want to become?
- what trust/control angle matters?
- what can be used directly from the page?
- what still needs to be captured later?

If the source does not support a compelling reel, say so clearly.

---

## When to Trigger

Use this skill when:

- the user shares a URL and wants to make a reel from it
- the user shares a product page, feature page, release note, demo page, changelog, or launch post
- a new reel needs to start and no approved `brief.md` exists yet
- the source material is external and must be analyzed before scripting

Do not use this skill for:
- writing the final reel script
- capturing new live demo footage
- assembling the timeline
- doing QA

Those happen later.

---

## Responsibilities

1. fetch and read the URL content
2. inspect the page structure and identify reel-worthy sections
3. capture screenshots of key sections and visible proof moments
4. identify downloadable screenshots, videos, thumbnails, or embedded media
5. extract structured source intelligence:
   - features
   - claims
   - proof moments
   - demo steps
   - outputs
   - trust/control language
   - tone
   - audience
6. evaluate the source for reel strength
7. rank the strongest hook directions
8. identify the best support points
9. determine the most natural CTA angle
10. identify capture gaps for later phases
11. produce markdown documents that are easy to copy and paste downstream

---

## Core Editorial Principle

Do not just summarize the page.

Interrogate it like an editor.

That means asking:
- what can I actually show on screen?
- what claim has proof?
- what proof is strongest in under 1 second?
- what output/result would make the viewer care?
- what objection or trust concern needs to be addressed?
- what does this page make possible for a reel?

The source brief must feed the reel system, not just document the source.

---

## Required Inputs

Before starting, gather:

- source URL
- project slug or project name
- optional user angle if given
- optional platform/context if already known

If the user gives a preferred angle, use it as a constraint, but still evaluate whether the source can support it.

---

## URL Type Classification

Before fetching, classify the URL. Different source types require different extraction strategies.

### Classification table

| URL pattern | Source type | Primary extraction | Secondary extraction |
|---|---|---|---|
| `youtube.com/watch`, `youtu.be/` | **YouTube video** | Transcript (captions/subtitles) | Title, description, thumbnail, chapter markers, comments |
| `blog.google/`, `developers.googleblog.com/` | **Blog post** | Full page text + embedded images | Screenshots of demos, feature sections, proof visuals |
| `*.github.com/*/releases`, changelogs | **Release notes** | Release body text, feature list | Linked docs, demo gifs, comparison tables |
| `github.com/*/` (repo root) | **GitHub repo** | README content, feature description | Star count, recent commits, demo screenshots |
| `arxiv.org/abs/`, `*.pdf` | **Research paper** | Abstract, key findings, figures | Method summary, benchmark results, comparison tables |
| `twitter.com/`, `x.com/` | **Social post/thread** | Thread text, quoted media | Engagement metrics, linked resources |
| `*.substack.com/`, `medium.com/` | **Newsletter/article** | Full article text | Embedded images, pull quotes |
| Product homepage (`*/pricing`, `*/features`) | **Product page** | Feature list, pricing, demos | Embedded videos, comparison charts, testimonials |
| `*.ai/`, `*.dev/`, tool landing pages | **Tool page** | Hero claim, feature grid, demo section | Screenshots, embedded video, pricing |

### YouTube — special handling (required)

YouTube pages contain almost no useful text in the HTML body. The page is a video player.

**Step 1 — Extract the transcript:**
- Fetch the video page
- Look for available captions/subtitles (auto-generated or manual)
- Extract the full transcript with timestamps
- If no captions are available: note this as a capture gap — the user may need to provide a transcript or the video content manually

**Step 2 — Extract video metadata:**
- Title, description, channel name
- Chapter markers (timestamps in description) — these often map to beat structure
- Thumbnail (download as potential hook visual)
- Duration (for pacing reference)
- Key comments if accessible (social proof, corrections, additional context)

**Step 3 — Analyze frames (when possible):**
- If the video shows product UI, tools, or demos, extract key frames at chapter markers or at regular intervals (every 15-30 seconds)
- These frames become potential source assets for the reel
- Note which frames show: product UI, results, comparisons, proof moments

**Step 4 — Treat the transcript as the source text:**
- Apply the same editorial analysis (claims, proof, hook ranking) to the transcript as you would to a blog post
- Chapter markers often correspond to natural beat boundaries
- Speaker emphasis and pacing in the transcript may suggest which moments matter most

**YouTube-specific rules:**
- The transcript IS the source content — do not just describe "it's a YouTube video about X"
- If the video is a product demo, frame timestamps become capture gap references ("need screenshot at 2:34 showing the export panel")
- If the video is an explainer/opinion, extract the claims and check if they can be supported with independent proof (screenshots from the actual product)
- Videos by creators (@lindsey.ai, @mavgpt, etc.) can be source reference but the reel must be original — adapt the angle, do not copy the script

### Research papers — special handling

- Extract abstract, key claim, methodology summary (one sentence), and headline result
- Extract figures and tables — these are often the strongest proof visuals
- Look for benchmark comparisons and charts — these are ready-made proof screenshots
- Note: academic language needs translation to conversational language at script phase
- The paper itself is credibility proof ("peer-reviewed at ICLR 2026")

### Social posts — special handling

- A tweet or thread is usually a SIGNAL, not a SOURCE. It tells you something is worth covering.
- Follow linked URLs from the post to find the actual product page or announcement
- The social post itself can be a credibility/trust screenshot ("even [person] says...")
- Thread structure may map to reel beat structure (each tweet = one beat)

#### X/Twitter video demos (Stage 0 capture source)

When a source URL is an X post — or when researching a topic reveals X posts with demo videos:
- **Flag the tweet URL** in the `## Demo Sources (X/Twitter)` section of `source-research.md`
- Note: product account (@GoogleLabs, @OpenAI, @AnthropicAI) or credible reviewer?
- Note: does the video show real product UI in action? (not just a promo graphic)
- Note: approximate duration and what product state it shows
- These URLs feed directly into `capture-x-video.js` at Phase 4 (demo capture)
- An authenticated X session is available via `.env` (AUTH_TOKEN, CT0) for automated download

**Always check for X demo videos** when the product has an official X account. Official product demos on X are often the highest-quality real footage available — better than anything we could mock or screen-record.

### Blog posts and product pages — standard handling

These are the default case. Follow the standard extraction process below.

---

## Script / Tool Entry Point

```bash
node lib/capture/source-brief.js --url <URL> --project <slug>



The automation may produce initial outputs, but the skill must still review, improve, and validate them.

Do not trust raw extraction alone.

What to Capture From the Source
Page captures
full-page screenshot
screenshots of each major feature section
screenshots of visible result/output states
screenshots of any trust/permission/control UI
screenshots of feature labels or names if important to the hook
Embedded media
downloadable screenshots
downloadable images
embedded videos or poster frames
thumbnails
gifs or motion demos
product visuals that can work as support proof
Structured text
headings
subheads
claims
proof language
output/result language
permission/control language
audience positioning
CTA language on page if useful
Source Evaluation Framework

Every source must be evaluated across these dimensions:

1. Claim Strength

Is there a clear interesting claim?

Examples:

a tool does real work, not just chat
a workflow is faster, smarter, safer, or more complete
a feature changes how a common task is done
2. Proof Strength

Can the source visibly prove the claim?

Examples:

generated deck shown
saved file shown
before/after shown
result UI shown
actual workflow steps shown
3. Hook Potential

Can this source support a strong opening?

Examples:

visible end result
surprising capability
hidden feature
strong pain/solution contrast
4. Trust / Objection Potential

Does the source show:

approval
permissions
user control
safety
reliability
real-world usefulness
5. Capture Sufficiency

Can enough visuals be sourced directly from the URL, or will later capture be required?

6. Reel Suitability

Does this feel like:

a reel with momentum
a static product page summary
a feature announcement with no usable proof
something that needs a live demo later to work
Reel Suitability Decision

At the end of source analysis, classify the source as one of:

Strong

The page provides enough proof, visuals, and claim clarity to drive a compelling reel.

Usable with Capture Gaps

The source has a strong concept, but later live capture or additional assets will be needed.

Weak

The source contains interesting information but lacks clear visible proof or usable visual moments.

Not Reel-Ready

The page is too vague, too text-heavy, too repetitive, or too unsupported to justify scripting yet.

This judgment must be explicit.

Proof Extraction Rules

This is a major v2 requirement.

For every meaningful claim, extract:

the claim itself
where it appears
what visible proof supports it
whether the proof is strong enough for a hook
whether the proof is strong enough for a middle-beat payoff
whether the proof is strong enough for recap
Examples of proof types
result shown
file shown
generated output shown
workflow step shown
save/output shown
permission dialog shown
transformation shown
comparison shown

If a claim has no visible proof, flag it.

Do not treat every feature equally.
Rank the strongest proof first.

Trust / Control Extraction Rules

If the source mentions or shows:

permissions
review before action
user approval
privacy
control
safety
access boundaries

then extract that explicitly.

Required output

The source brief must state:

whether a trust beat is recommended
what the trust concern is
what source evidence supports it
whether later capture is needed to show it clearly

This is critical for tools that act on files, computer actions, approvals, or other sensitive steps.

Hook Direction Ranking

The brief should not only identify one hook direction.
It should rank the top options.

Provide:
Primary Hook Direction
Secondary Hook Direction
Backup Hook Direction

Each direction should be:

a claim or surprise
not a fully written script line
easy to support visually
tied to proof, not just wording
Example

Primary:

Claude builds the finished deliverable, not just the answer

Secondary:

Most people use Claude like chat and miss the workflow feature

Backup:

The real difference is that it can act on actual files

The final script skill will convert the chosen direction into wording.

Support Point Selection

Select up to 3 support points only.

These should not just be random features.
They should help build the reel.

Best support point types
first proof workflow
second proof workflow or mechanism
trust/control proof
clear user benefit
output/result differentiation

Avoid weak support points such as:

minor interface details
broad marketing language
feature names with no proof value
CTA Angle Selection

Choose the CTA angle that feels most natural for the source.

Good CTA angle types
hidden feature people miss
more workflows like this
more use cases
more tool breakdowns
template / prompt / system follow-up
part two if the source is rich enough for a series

The CTA angle should reflect what the source actually delivers, not generic engagement bait.

Style Selection

The brief must include a Recommended Style field.

Choose the style based on:

source shape
proof behavior
pacing potential
how naturally it fits a short-form reel
Recommended styles
Breakdown
Case Study
Problem & Solution
Rapid Tutorial
Listicle
Long Tutorial
Day In The Life
Personal Update
Simple Tip
Style rules
prefer the style that best supports visible proof
do not force a listicle unless the source genuinely has multiple strong items
if one workflow is the star, prefer Breakdown, Case Study, or Problem & Solution
if two styles are equally viable, list both and explain why
Capture Gaps Analysis

This section must be stronger than before.

For every source, identify what still needs to be captured later.

Categories
live demo needed
avatar video needed
trust prompt not visible enough
output/save state not visible enough
hook-ready result not visible enough
recap-ready flashes missing
SFX/music still needed
brand assets missing
better crops/screenshots needed
Rules

Be specific.

Bad:

Need more visuals

Better:

Need a live capture of the saved Excel file moment because the page only implies the output
Need a cleaner permission prompt capture because the source only references approval in text
Need 2–3 recap-ready screenshots of the final deck
Output Documents

This skill must produce markdown documents that are easy to copy and paste.

Required files
File	Contents
projects/<slug>/source-research.md	Full structured source analysis
projects/<slug>/brief.md	Condensed creative brief for downstream scripting
projects/<slug>/assets/source/	Downloaded and captured source visuals
projects/<slug>/assets/catalog.json	Registered source assets
lib/capture/demo-config.json	Pre-populated when prompts/responses are discoverable

All written outputs must be markdown-first and copy-paste ready.

source-research.md Required Structure

Deliver a markdown document with this structure:

# Source Research: [Project Slug]

**URL:** [Source URL]  
**Source type:** [Product page / release note / demo page / changelog / etc.]  
**Reel suitability:** [Strong / Usable with Capture Gaps / Weak / Not Reel-Ready]  
**Audience:** [Who this seems aimed at]  
**Tone:** [How the page communicates]  
**Trust beat recommended:** [Yes / No]

---

## Core Source Promise
[One sentence describing the strongest overall promise from the page.]

## Strongest Visible Proof
[The clearest proof moment or result visible on the page.]

## Hook Direction Ranking
1. [Primary hook direction]
2. [Secondary hook direction]
3. [Backup hook direction]

## Ranked Proof Moments
1. [Proof moment + why it matters]
2. [Proof moment + why it matters]
3. [Proof moment + why it matters]

## Claims and Evidence
### Claim 1
- Claim:
- Source evidence:
- Visible proof:
- Reel value:
- Hook-worthy: [Yes / No]

### Claim 2
- Claim:
- Source evidence:
- Visible proof:
- Reel value:
- Hook-worthy: [Yes / No]

## Trust / Control Signals
- [Any permission, approval, safety, or control evidence]
- [Whether later capture is still needed]

## Recommended Support Points
1. [Support point]
2. [Support point]
3. [Support point]

## Recommended CTA Angle
[Best CTA direction based on the source.]

## Recommended Style
[Primary style]
[Optional secondary style + reason]

## Source Assets Captured
- [Asset list or summary]

## Capture Gaps
- [ ] [Specific missing proof or assets]
- [ ] [Specific missing trust or save/output coverage]
- [ ] [Any needed live demo or additional visuals]

## Notes for Reel Script
[What the writer should lean into.]

## Notes for Capture Demo
[What later live capture must prioritize.]
brief.md Required Structure

Deliver a markdown document with this structure:

# Brief: [Project Slug]

**Source URL:** [URL]  
**Reel suitability:** [Strong / Usable with Capture Gaps / Weak / Not Reel-Ready]  
**Recommended style:** [Primary style]  
**Trust beat required:** [Yes / No]

---

## Hook Direction
[The single strongest hook direction for scripting.]

## Proof Promise
[What the reel will prove.]

## Strongest Visible Proof
[The best visual payoff available from the source.]

## Support Points
1. [Support point]
2. [Support point]
3. [Support point]

## CTA Angle
[The clearest CTA direction for this source.]

## Capture Gaps
- [ ] [Specific missing asset or proof]
- [ ] [Specific missing trust or output coverage]

## Script Notes
- [Keep this concrete]
- [Prioritize this proof]
- [Avoid this weaker angle]

## Capture Notes
- [Capture this output moment]
- [Capture this trust moment]
- [Capture recap-ready flashes]

The brief must be short, clear, and directly usable by reel-script.

Review Workflow
Step 1 — Fetch and inspect the URL

Read the full page and identify major sections.

Step 2 — Capture source visuals

Take screenshots of sections and download usable visuals.

Step 3 — Extract source intelligence

Claims, proof, outputs, trust signals, demo steps, audience, tone.

Step 4 — Rank editorial value

Determine:

best hook direction
best proof
best support points
best CTA angle
best style
Step 5 — Judge reel suitability

Explicitly decide whether this source is strong enough.

Step 6 — Write markdown outputs

Produce:

source-research.md
brief.md
Step 7 — Present the brief for approval

Do not move to scripting until the brief is approved.

Important Rules
never invent claims not present in the source
never inflate weak proof into strong proof
if the page is paywalled or blocked, ask for screenshots or screen recording instead
if embedded media exists, note timestamps or sections worth using later
if the source contains good visuals but weak proof, say so
extracted screenshots go into assets/source/
any downloaded source media must be registered in assets/catalog.json
prefer result-first thinking over feature-list thinking
if the source supports only one strong workflow, do not pretend it supports a listicle
Relationship to Other Skills
reel-script

Uses brief.md to write the final spoken script.

capture-demo

Uses source findings to know what later live capture still needs to show.

assemble-reel

Uses the brief’s hook direction, proof promise, and structure assumptions.

qa-reel

Uses the source promise to check whether the final reel actually delivered what the source claimed.

This skill should make the next phases easier, not harder.

Stop Condition

Stop after:

source-research.md is produced
brief.md is produced
reel suitability is stated clearly
capture gaps are listed explicitly
the brief is presented for approval

Do not proceed to reel-script until the user approves the brief direction.
