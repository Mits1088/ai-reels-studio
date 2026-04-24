---
name: youtube-script-creator
description: "Creates complete YouTube video packages for Mits's channel covering AI tools, agents, and business automation. Produces a full script in Mits's spoken voice plus all supporting assets needed to shoot the video, including exact prompts, template files, URLs, pre-production checklist, video description, and chapter timestamps. Use when the user asks to write a YouTube script, draft a video, plan a video, create video content, build a YouTube video package, or prepare a video about any AI tool, platform, or workflow demo. Unlike the /youtube skill suite, this skill is standalone — it does not require a reel project, brief.md, or pipeline gates."
metadata:
  author: Mits
  version: 1.1.0
  channel-focus: AI tools and business automation for beginners
---

# YouTube Script Creator

## What this skill does

Produces a complete, shoot-ready YouTube video package for Mits's channel. Every output includes the script AND all the assets needed to actually film the video without additional prep: exact prompts to type on screen, template files, URLs, a pre-production checklist, the video description, and chapter timestamps.

**Standalone use:** This skill does not require a reel project, `brief.md`, or any pipeline gates. It can be run directly from a topic, URL, or brief description.

**Pipeline integration:** If a reel project already exists (`brief.md` and `project.json` present), this skill can draw from them — but they are not required.

---

## Core principles (always apply)

1. **Write for the spoken word, not the page.** Every sentence must sound natural when read aloud. If a phrase wouldn't come up in casual conversation, replace it.

2. **Default to beginner-friendly.** Assume the viewer is curious about AI but hasn't built anything yet. Technical viewers will still watch accessible content; beginners will bounce from technical content.

3. **Lead with the problem, not the product.** Open with something the viewer relates to. Show why it was hard. Then show what changed. Then demo.

4. **Translate every piece of jargon** the first time it appears. Use a plain-English explanation or a real-world analogy. See `.claude/skills/youtube/references/jack-roberts-techniques.md` for the translation approach.

5. **Demo sections need narration layers.** Every loading, processing, or connecting moment must have pre-written filler narration. Never leave dead air. See `.claude/skills/youtube/references/script-structure.md`.

6. **Produce complete assets, not just a script.** A script alone is not enough. Every video package must include the full shoot checklist. See `references/asset-checklist.md`.

7. **Match Mits's voice exactly.** Use his confirmed catchphrases. Avoid rejected phrases. See `.claude/skills/youtube/references/voice-profile.md` for the full profile.

---

## Workflow

### Step 1: Clarify the video brief

Before writing anything, confirm with the user:

- **Topic and angle:** What tool or concept is this about? What's the unique angle versus other videos on this topic?
- **Primary demo:** What will be shown on screen? Walk through the user journey step by step.
- **Practical examples:** What real business scenarios will the video use? (Prefer examples that match Mits's actual client base: physiotherapy clinics, medical spas, wellness businesses, local service businesses.)
- **Target duration:** Usually 10 to 12 minutes.
- **Credibility anchor:** Should this video reference Mits's GHL agency background? Use sparingly, only when directly relevant.

If any of these are unclear, ask before drafting.

### Step 2: Plan the structure

Use the problem-first structure by default. Map out chapters with timestamps before writing prose. See `.claude/skills/youtube/references/script-structure.md` for the full template.

### Step 3: Draft the script

Write chapter by chapter, applying the voice profile and the demo narration rules. Pre-write filler narration for every loading or processing moment in demo sections. Use `assets/script-template.md` as the starting skeleton.

### Step 4: Build the asset package

Produce every required asset in `references/asset-checklist.md`. Do not skip any. The output is only complete when all assets are ready.

### Step 5: Final review

Before delivering, check:

- No em dashes anywhere in the output (Mits's explicit preference).
- UK English spellings throughout.
- No rejected phrases ("dude," "bro," "freaking cool," "grab that coffee and let's dive in").
- Every technical term is translated the first time it appears.
- Every demo section has filler narration, not just camera directions.
- Every prompt shown on screen is written out verbatim in a copy-paste block.
- All URLs, files, and resources are listed in the pre-production checklist.
- The description is written and includes chapter timestamps.

---

## Delivery format

Always deliver in this exact order:

1. **Video meta** (title, duration, primary claim, CTA)
2. **Pre-production checklist** (everything needed before hitting record)
3. **Full script** (chapter by chapter with narration and on-screen actions)
4. **Copy-paste assets** (all prompts, files, configs, sample data)
5. **URLs and links** (every link referenced in the video)
6. **Video description** (pre-written, with chapter timestamps)
7. **Claim check** (verified facts and editorial framing flagged)

---

## When to load additional references

- For voice and language questions, load `.claude/skills/youtube/references/voice-profile.md`.
- For script structure, chapter pacing, or demo narration templates, load `.claude/skills/youtube/references/script-structure.md`.
- For translation metaphors, on-screen mechanics, or hook construction, load `.claude/skills/youtube/references/jack-roberts-techniques.md`.
- For the full asset checklist, load `references/asset-checklist.md`.
- For templates, use the files in `assets/`.

---

## Critical rules (never break)

- No em dashes in final output. Use commas, full stops, or restructure the sentence.
- No "dude," "bro," or "freaking cool." Mits does not use these.
- No "grab that coffee and let's dive in." Use "Let's go straight in" instead.
- UK English only.
- Every demo step must have narration written for it.
- Every prompt shown on screen must appear verbatim in the copy-paste assets section.
- Every video package must include a pre-production checklist and a ready-to-paste description.
