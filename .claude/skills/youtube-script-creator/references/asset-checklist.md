# Asset Checklist

A script alone is not enough. Every video package must include ALL of the following assets. Do not deliver the video package until every item on this list is complete.

## 1. Video meta

- Title (hook-style, problem-first, not product-first)
- Target duration
- Primary claim (what the viewer will walk away believing)
- Proof strategy (how the claim is demonstrated)
- CTA (subscribe plus the platform URL)

## 2. Pre-production checklist

Everything needed before hitting record. Format as a checklist Mits can tick off.

Include:
- Accounts to be logged in (with the exact login URL)
- Browser tabs to pre-open (in the order they'll appear in the video)
- Files to have ready on the desktop (template files, sample data)
- Extensions or software to install before shooting
- Sample data prepared (example sales scripts, customer queries, test inputs)
- Any API keys or credentials needed, with a secure handling note (never type them on camera)
- Camera angle reminders if relevant (split screen, zoom plans)

Example format:

```
PRE-PRODUCTION CHECKLIST

Accounts to log in:
[ ] platform.claude.com (using your Anthropic account)
[ ] clickup.com (your ClickUp workspace)

Browser tabs in order:
[ ] Tab 1: platform.claude.com/quickstart
[ ] Tab 2: platform.claude.com/agents
[ ] Tab 3: clickup.com dashboard

Files to have ready on desktop:
[ ] sample-sales-script.md (see Copy-Paste Assets section)
[ ] agent-config.yaml (pre-filled template)

Software installed:
[ ] None required

Sample data:
[ ] Sales script for a fake client "Sarah at Wellness Studio London"
```

## 3. Full script

Chapter by chapter with timestamps. Every chapter includes:
- Spoken narration (written for Mits's voice)
- On-screen actions in square brackets `[CLICK: Quickstart tab]`
- Demo filler narration pre-written for every loading or processing moment
- Every prompt typed on screen appears verbatim, marked clearly: `[TYPE: exact prompt here]`

## 4. Copy-paste assets

All prompts, files, and configs needed during the shoot. Every item must be copy-paste ready, with no placeholders left for Mits to figure out on camera.

Include:
- Every prompt used in the video, written out in full in a copy-paste block
- Any YAML, JSON, or Markdown files Mits needs to show or upload (complete contents, not snippets)
- Sample data used in demos (example sales scripts, customer queries, test inputs, complete with realistic details)
- Any code snippets shown on screen

Example format:

```
COPY-PASTE ASSETS

Prompt 1 (used at 4:45 in the video):
---
Hey, I'd like you to create a sales task agent. When I feed you a 
sales script from a closed deal, read through it, find any tasks 
embedded in the text (follow-ups, contract prep, onboarding steps), 
and create them in my ClickUp workspace. Assign each task to the 
right person based on context, set reasonable deadlines, and include 
a brief description pulled from the sales script.
---

Sample sales script (to demonstrate the agent at 8:45):
---
[full realistic sales script here, 300 to 500 words]
---

YAML template (shown on screen at 5:00):
---
[complete YAML file here]
---
```

## 5. URLs and links

Every link referenced in the video, in one list. These feed into the video description.

Include:
- The main product URL
- Documentation links
- Any tool or extension URLs mentioned
- Any proof-point source links (company case studies referenced)
- Mits's own social or signup links if relevant

## 6. Video description

Pre-written, ready to paste into YouTube Studio. Include:

- Hook sentence at the top (repeats or riffs on the video's promise)
- Two to three paragraph description of what the video covers
- Chapter timestamps (matching the script exactly)
- "Resources mentioned in this video" section with all URLs
- "Free resources" section if Mits is giving away prompts or templates
- Subscribe CTA
- Any affiliate disclosures if relevant

Example format:

```
VIDEO DESCRIPTION

Most people building AI agents never ship them, because the 
infrastructure around the agent is harder than the agent itself. 
In this video I show you what's changed, how to build a support 
agent and a sales agent in minutes, and exactly what it costs.

Everything you see in this video, including the exact prompts and 
templates, is linked below.

CHAPTERS
0:00 The problem nobody explains
0:30 What you'll learn today
1:30 Why building agents used to be so hard
3:30 What actually changed
4:00 The Claude platform
...

RESOURCES MENTIONED
Claude platform: https://platform.claude.com
Managed agents docs: [URL]

FREE RESOURCES
Sales agent prompt: [link to pastebin or GitHub gist]
YAML template: [link]

Subscribe for weekly AI tool breakdowns for people actually 
building things.
```

## 7. Claim check

Every factual claim in the script must be flagged as either verified or creative framing.

Format:

```
CLAIM CHECK

Verified facts (with sources):
- Rakuten deployed four enterprise agents in one week (source: Anthropic engineering blog)
- Pricing is £X per session hour (source: pricing page URL)
- Beta header required: managed-agents-2026-04-01 (source: docs URL)

Creative framing (not direct claims, make sure these feel editorial not literal):
- "Two to three months" for the old infrastructure timeline (editorial estimate)
- "Glass box" metaphor for the session debug view (my phrasing, not the product's)

Needs fact-checking before publish:
- [Anything Mits needs to verify himself before shooting]
```

## Quality gate

Before delivering the package, verify:

- [ ] Every demo moment has filler narration written for it
- [ ] Every prompt typed on screen appears in Copy-Paste Assets
- [ ] Every URL mentioned appears in URLs and Links
- [ ] The pre-production checklist covers every account, file, and tab needed
- [ ] The description is ready to paste with chapter timestamps
- [ ] The claim check flags anything that needs verification
- [ ] No em dashes anywhere in the output
- [ ] No rejected phrases ("dude," "bro," "freaking cool," "grab that coffee")
- [ ] UK English throughout
