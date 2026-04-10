---
name: new-reel
description: Initialize a new reel project with valid project.json, folder structure, and starter documents.
disable-model-invocation: true
---

# New Reel Skill

Use this skill when starting a new reel project.

This is the project initialization phase.  
Its job is not just to make folders.  
Its job is to create a clean, phase-ready reel workspace that supports the full retention-first pipeline.

That means the project should be ready for:
- source analysis
- briefing
- script writing
- voice ingest
- demo capture
- timeline assembly
- QA
- final render handoff

---

## Primary Goal

Create a new reel project that is:
- clearly named
- structurally complete
- easy to navigate
- ready for markdown-based handoff between phases
- ready for retention-first production

A good initialization should make the next step obvious and reduce setup mistakes later.

---

## Global Rule References

This skill must follow these global rule files in addition to its local instructions:

- `.claude/rules/reel-workflow.md`

### Rule precedence

When rules overlap, use this order:

1. **Workflow rules** — phase order and approval gates
2. **This skill** — project setup, folder structure, starter docs, and metadata decisions inside that workflow

---

## Workflow Alignment

This skill runs at the very start of the reel pipeline.

It should initialize the workspace so the next phase is clear and compliant with the required sequence:

1. new project
2. source brief or topic brief
3. script approval
4. voice ingest
5. demo capture
6. shot list approval
7. assembly
8. QA
9. render

### Important workflow rule
Initialization must not skip ahead.

Do not:
- auto-generate a full script unless explicitly requested
- jump straight into voice ingest
- start capture or assembly from project setup
- blur the difference between entry path selection and later production phases

---

## Responsibilities

- create a new project folder under `projects/`
- create the required phase folders
- create the required markdown starter files
- initialize `project.json`
- initialize empty asset/audio/output structures
- record what is known vs unknown
- define the project entry path
- make the next phase obvious
- stop after setup

---

## Core Principle

Initialize for the full workflow, not just the first file.

A new reel project should already be structured to support:
- source-first workflows
- topic-first workflows
- script-first workflows
- markdown handoffs
- editorial phase tracking
- clean asset registration later

Do not create a vague or incomplete shell.

---

## When to Trigger

Use this skill when:
- a new reel project is being started
- the user has a new topic, URL, or concept
- no project folder exists yet for the reel
- a clean workspace is needed before briefing or scripting

Do not use this skill for:
- rewriting an existing project
- scripting
- source research
- audio ingest
- asset capture
- timeline assembly
- QA

---

## Input Quality Diagnostic

Before initializing, assess the user's starting input. This directly determines pipeline speed and output quality.

**Full reference:** See `training/input-quality-guide.md` for detailed examples, real project comparisons, cascade effects, and the 8-element checklist with Excellent/Great/Good/Bad classifications.

### Run this check on every new project

Count how many of these the user has provided:

| # | Element | Provided? | Impact if missing |
|---|---|---|---|
| 1 | **Source** (URL or specific topic) | ? | Cannot start without this |
| 2 | **Angle** (which feature/claim to focus on) | ? | System proposes 3+ options → +1 round-trip |
| 3 | **Audience** (who cares and why) | ? | Script speaks to nobody → generic CTA |
| 4 | **Duration** (target length) | ? | Scope unconstrained → feature stuffing |
| 5 | **Style** (cinematic-presenter / editorial-authority) | ? | Defaults to cinematic-presenter |
| 6 | **Scope boundaries** (what NOT to cover) | ? | System covers everything → scope creep |
| 7 | **Hook direction** (first 1-3 seconds) | ? | System must research + propose → +1 round-trip |
| 8 | **Proof method per claim** (what visual proves each claim) | ? | Shot-list gets MISSING scores → blocks assembly |

### Score the input

| Elements provided | Quality | Expected pipeline |
|---|---|---|
| 6-8 | **Excellent** — minimal revisions, fast pipeline | 1-2 rounds total |
| 4-5 | **Great** — 1-2 extra decision points | 2-3 rounds total |
| 2-3 | **Good** — system makes assumptions, needs more approvals | 4-6 rounds total |
| 1 | **Bad** — cascading problems at every phase | 5x+ effort or restart |

### What to do with the score

**Excellent/Great (4+ elements):** Initialize and proceed. Record what was provided.

**Good (2-3 elements):** Initialize, but before proceeding to source-brief or reel-script, ask the user:
- "What specific angle should this reel focus on?"
- "Who is the audience — what do they currently do or pay for?"
- "How long should this be?"
- "Anything we should NOT cover?"

Frame these as quick decisions, not a questionnaire. One sentence each is enough.

**Bad (1 element):** Do NOT initialize a full project yet. Instead, help the user narrow their input:
- "Which ONE feature of [tool] should this reel focus on?"
- "What's the one claim that would make someone stop scrolling?"
- "Who specifically would watch this and why?"

A bad input initialized into a full project folder creates false momentum — the team thinks production has started, but the brief will stall.

### Important rule

**Never skip this diagnostic.** Even if the user is eager to start, a 30-second input quality check prevents days of downstream revision. Record the input quality score in project.json as `input_quality`.

---

## Required Inputs

When available, gather:

- project name
- reel topic
- audience
- target duration
- hook direction
- CTA direction
- content type
- source URL if one exists
- whether this is part of a series
- whether trust/control is likely relevant
- visual style preference (`cinematic-presenter` or `editorial-authority`)

If some inputs are missing, initialize the project anyway and mark unknown fields clearly.

### Style Selection

Ask the user which visual style to use:

| Style | ID | Best for |
|---|---|---|
| Cinematic Presenter | `cinematic-presenter` | Feature demos, tutorials, single-tool deep-dives |
| Editorial Authority | `editorial-authority` | Listicles, comparisons, claim-and-prove, tool roundups |

If the user doesn't specify, default to `cinematic-presenter`.
Set the `style` field in `project.json`. This drives all downstream defaults.

---

## Entry Path Classification

Each project should be classified into one of these entry paths:

### 1. Source-first
Use when the project begins from a URL, product page, release note, changelog, or launch page.

**Next phase:** `source-brief`

### 2. Topic-first
Use when the user has a concept or topic but no source URL yet.

**Next phase:** `brief` creation or `reel-script`, depending on context

### 3. Script-first
Use when the user already has an approved script or wants to start directly from scripting.

**Next phase:** `reel-script`

### 4. Revision
Use when the project is a rework of an older reel concept.

**Next phase:** depends on what is missing, but still initialize with clear metadata

The chosen entry path must be written into `project.json`.

---

## Required Folder Structure

A new project should include at minimum:

```text
projects/<slug>/
  brief.md
  script.md
  assets-needed.md
  project.json
  source-research.md
  shot-list.md
  qa-notes.md
  audio/
  assets/
    source/
  output/

  Inside audio/

Prepare for:

source.wav
voice.json
beat-map.json
captions.json
ingest-report.md
timing-notes.md
Inside assets/

Prepare for:

catalog.json
source/
later demo captures
support visuals
SFX/music references
Inside output/

Prepare for:

timeline.json
assembly-notes.md
qa_report.json
qa-report.md
Required Starter Files
brief.md

Starter markdown document for the creative brief.

script.md

Starter markdown document for the final spoken script.

source-research.md

Starter markdown document for source analysis when relevant.

assets-needed.md

Starter markdown checklist of what still needs to be captured or sourced.

shot-list.md

Starter markdown document for beat-to-visual planning later.

qa-notes.md

Starter markdown document for manual QA notes if needed.

project.json

Canonical metadata file for status, entry path, and downstream phases.

assets/catalog.json

Initialize as an empty valid catalog structure if possible.

Markdown-First Requirement

All starter docs must be markdown documents that are easy to copy and paste.

The project should be initialized in a way that supports clean handoff between:

source-brief
reel-script
ingest-voice
capture-demo
assemble-reel
qa-reel

Do not create vague placeholder files with no structure.

Starter File Templates
brief.md
# Brief: [Project Slug]

**Topic:** [Unknown or provided]  
**Audience:** [Unknown or provided]  
**Target duration:** [Unknown or provided]  
**Content type:** [Unknown or provided]  
**Entry path:** [Source-first / Topic-first / Script-first / Revision]  
**Trust beat likely:** [Yes / No / Unknown]

---

## Hook Direction
[TBD]

## Proof Promise
[TBD]

## Strongest Visible Proof
[TBD]

## Support Points
1. [TBD]
2. [TBD]
3. [TBD]

## CTA Angle
[TBD]

## Capture Gaps
- [ ] [TBD]

## Notes
[TBD]
script.md
# Script: [Project Slug]

**Hook category:** [TBD]  
**Style:** [TBD]  
**Visual style:** [cinematic-presenter / editorial-authority]  
**Engagement trigger:** [TBD]  
**Estimated duration:** [TBD]  
**CTA angle:** [TBD]  
**Proof promise:** [TBD]  
**Trust beat required:** [TBD]

---

## ElevenLabs Script

[TBD]

---

## Timing Reference

(00:00–00:00) [TBD]
source-research.md
# Source Research: [Project Slug]

**URL:** [Unknown or provided]  
**Source type:** [TBD]  
**Reel suitability:** [TBD]  
**Audience:** [TBD]  
**Tone:** [TBD]  
**Trust beat recommended:** [TBD]

---

## Core Source Promise
[TBD]

## Strongest Visible Proof
[TBD]

## Hook Direction Ranking
1. [TBD]
2. [TBD]
3. [TBD]

## Ranked Proof Moments
1. [TBD]
2. [TBD]
3. [TBD]

## Claims and Evidence
[TBD]

## Trust / Control Signals
[TBD]

## Recommended Support Points
1. [TBD]
2. [TBD]
3. [TBD]

## Recommended CTA Angle
[TBD]

## Recommended Style
[TBD]

## Source Assets Captured
[TBD]

## Capture Gaps
- [ ] [TBD]

## Notes for Reel Script
[TBD]

## Notes for Capture Demo
[TBD]
assets-needed.md
# Assets Needed: [Project Slug]

## Source Assets
- [ ] [TBD]

## Demo Captures
- [ ] [TBD]

## Result-State Screenshots
- [ ] [TBD]

## Trust / Permission Assets
- [ ] [TBD]

## Recap / CTA Support Assets
- [ ] [TBD]

## SFX / Music
- [ ] [TBD]
shot-list.md
# Shot List: [Project Slug]

**Style:** [cinematic-presenter / editorial-authority]

## Phase 4b-i — Visual Assignment

| Beat | Time | Narration | Visual Type | Asset | Notes |
|---|---|---|---|---|---|
| beat-01 | 0.00–0.00 | TBD | TBD | TBD | TBD |

## Phase 4b-ii — Component Mapping + Asset Fitness

### Component Mapping

| Beat | Narration Classification | Component | Avatar Layout | Content Zone | Notes |
|---|---|---|---|---|---|
| beat-01 | TBD | TBD | TBD | TBD | TBD |

### Asset Fitness Audit

| Beat | Narration | Must SEE | Available Assets | Best Match | Fitness | Action |
|---|---|---|---|---|---|---|
| beat-01 | TBD | TBD | TBD | TBD | TBD | TBD |

### Flow Validation

- [ ] Component variety ≥ 6 for 35s+ reel
- [ ] No same-component streak > 3
- [ ] No same-layout streak > 3
- [ ] Dense sections < 8s without face return
- [ ] Sparse sections < 5s without visual support

## Phase 4b-iii — Technical Planning

| Beat | Background | SFX | Transition | Notes |
|---|---|---|---|---|
| beat-01 | TBD | TBD | TBD | TBD |
qa-notes.md
# QA Notes: [Project Slug]

## Blocking Issues
- None yet

## Warnings
- None yet

## Notes
- Project initialized
project.json Requirements

**Schema version:** All new projects must use schema version 2.

Initialize project.json with ALL of these fields. Every field must be present — no omissions.

### Required fields (contract v2)

| Field | Type | Rule |
|-------|------|------|
| `schema_version` | integer | Always `2` |
| `project_type` | string | Always `"reel"` for this skill |
| `slug` | string | URL-safe kebab-case, matches directory name |
| `title` | string | Human-readable project name |
| `phase` | string | Set based on entry path (see below) |
| `status` | string | `"initialized"` |
| `gates_passed` | array | Always `[]` at creation |
| `created` | string | ISO 8601 datetime (e.g. `"2026-04-07T12:00:00Z"`) |
| `updated` | string | ISO 8601 datetime (same as created) |

### Reel metadata fields (all must be present)

| Field | Type | Rule |
|-------|------|------|
| `style` | string | `"cinematic-presenter"` or `"editorial-authority"` |
| `entry_path` | string | `"source-first"`, `"topic-first"`, `"script-first"`, or `"revision"` |
| `topic` | string/null | From user input, null if unknown |
| `source_url` | string/null | URL if source-first, null otherwise |
| `audience` | string/null | From user input, null if unknown |
| `target_duration` | string/null | e.g. `"30s"`, null if unknown |
| `hook_direction` | string/null | From user input, null if unknown |
| `cta_direction` | string/null | From user input, null if unknown |
| `content_type` | string/null | e.g. "product-launch", "listicle", null if unknown |
| `series` | string/null | Series name or null |
| `trust_beat_likely` | boolean/null | From diagnostic, null if unknown |
| `input_quality` | string/null | "excellent", "great", "good", "bad", or null |
| `theme` | null | Always null — set later by theme-factory |
| `theme_primary` | null | Always null — set later by theme-factory |
| `theme_secondary` | null | Always null — set later by theme-factory |
| `voice_file` | null | Always null — set later by ingest-voice |
| `duration_s` | null | Always null — set later by ingest-voice |
| `avatar_file` | null | Always null — set later by ingest-voice |
| `avatar_format` | null | Always null — set later by asset-prep |
| `canonical_audio` | null | Always null — set later by ingest-voice |

### Example shape (v2)

```json
{
  "schema_version": 2,
  "project_type": "reel",
  "slug": "claude-cowork-reel",
  "title": "Claude Cowork Reel",
  "phase": "source-brief",
  "status": "initialized",
  "gates_passed": [],
  "style": "cinematic-presenter",
  "entry_path": "source-first",
  "topic": "Claude Cowork feature",
  "source_url": "https://example.com/launch",
  "audience": "Creators and AI-curious professionals",
  "target_duration": "30s",
  "hook_direction": null,
  "cta_direction": null,
  "content_type": "feature",
  "series": null,
  "trust_beat_likely": true,
  "input_quality": "great",
  "theme": null,
  "theme_primary": null,
  "theme_secondary": null,
  "voice_file": null,
  "duration_s": null,
  "avatar_file": null,
  "avatar_format": null,
  "canonical_audio": null,
  "created": "2026-04-07T12:00:00Z",
  "updated": "2026-04-07T12:00:00Z"
}
```

**Important:** Use `title` (not `name`), `created` (not `created_at`), and `phase` (not `current_phase`). These are the schema v2 field names.

If values are unknown, use `null` — not empty strings, not `"TBD"`, not omission.

### Validation

After creating project.json, it must pass: `python -m lib.validate projects/<slug>`

Project Status Rules

At the end of initialization:

set status → initialized
set phase appropriately
Default phase by entry path
source-first → source-brief
topic-first → source-brief
script-first → script
revision → whichever phase is actually needed first

Do not advance beyond initialization automatically.

Initialization Workflow
Step 1

Create the project slug and folder.

Step 2

Create the base folder structure:

root docs
audio/
assets/
assets/source/
output/
Step 3

Create starter markdown docs with useful structure.

Step 4

Create project.json with known metadata and clear unknowns.

Step 5

Initialize empty asset/output readiness:

assets/catalog.json
audio folder readiness
output folder readiness
Step 6

Determine the entry path and current phase.

Step 7

Summarize what was created and what still needs human or upstream input.

Validation Checklist

Before finishing, verify:

Structure
 project folder exists
 required subfolders exist
 required markdown docs exist
 project.json exists
 file names are clear and consistent
Metadata
 slug is usable
 entry path is set
 current phase is set
 known inputs are recorded
 unknown inputs are marked clearly
Workflow readiness
 next phase is obvious
 markdown handoff docs are usable
 project can continue without structural confusion
Output Expectations

At the end:

confirm folder structure
confirm created files
confirm project.json setup
summarize what is still unknown
state the correct next phase

The initialization should make the next step obvious and reduce ambiguity.

Important Rules
do not skip source-research.md even if it will be unused at first
do not leave the project without project.json
do not create empty files with no structure
do not auto-generate a full brief or script unless the user asked for it
do not move into voice ingest automatically
initialize for the full pipeline, not just the first creative step
Relationship to Other Skills
source-brief

Uses the initialized project when starting from a URL.

reel-script

Uses brief.md, project.json, and the initialized structure.

ingest-voice

Uses the prepared audio/ folder and metadata.

capture-demo

Uses assets-needed.md, project.json, and later the script/shot list.

assemble-reel

Uses shot-list.md, audio/, assets/, and output/.

qa-reel

Uses the finished project structure and output folder later.

This skill should make every later phase cleaner.

Stop Condition

Stop after:

the project structure is created
starter markdown files are created
project.json is initialized
the next phase is clearly identified

Do not proceed into briefing, scripting, voice ingest, capture, assembly, or QA automatically.