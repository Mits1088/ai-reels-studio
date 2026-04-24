# Publish Prep Skill

Use this skill when:
- A reel has just been rendered (Phase 7 complete)
- The user asks for an Instagram caption, post copy, or hashtags
- The user says "publish prep", "caption", "post copy", or similar

This is **Phase 7b** — the final publishing step.
It runs after render (Phase 7) and produces everything needed to post the reel.

---

## Primary Goal

Produce `projects/<slug>/output/instagram-caption.md` containing:
1. A primary caption (hook line + body + CTA)
2. An alt caption (shorter variant)
3. Hashtag block (15 tags, mix of broad + niche)
4. First comment suggestion (engagement prompt)
5. Posting notes (link in bio, timing, attribution)

The caption must match the reel's energy and hook — it is the written version of what the viewer just watched.

---

## When to Trigger

Run after every render, without exception. If the caption file already exists, check whether the script has changed and update accordingly.

Do NOT use this skill for:
- Writing the voiceover script (use `reel-script`)
- QA of the rendered video (use `qa-reel`)
- Anything before the render is complete

---

## Required Inputs

- `projects/<slug>/script.md` — spoken content, hook, CTA
- `projects/<slug>/brief.md` — topic, audience, proof promise
- `projects/<slug>/project.json` — product, brand, duration
- `remotion/out/<slug>.mp4` — rendered file (confirms render is done)

---

## Caption Writing Rules

### Hook line
- Must match the reel's hook verbatim or very closely
- First sentence stops the scroll — same job as frame 0 of the reel
- No emojis in the first line (Instagram hides text after 3 lines; save emojis for below the fold)
- Under 12 words

### Body
- 3–5 short paragraphs, each one idea
- Mirror the reel's beat structure: hook → proof → secret/differentiator → CTA
- Named product + URL always appear (e.g. "claude.ai/design")
- Outcome language, not feature language: "design to working product" not "has an export function"
- No more than one emoji per paragraph

### CTA
- One specific action: Follow, Comment, or Save
- Tie it to the reel's CTA angle from script.md
- Include ↓ or 👇 to signal there's more below the fold

### Hashtags
- 15 tags total: 5 broad (>500k posts), 5 niche (<100k posts), 5 product-specific
- Always include the product's brand hashtag and the company hashtag
- No banned/flagged hashtags
- Place as a separate block after the caption body — never inline

### First comment
- Post immediately after publishing — boosts early engagement signal
- A question that invites a response related to the reel's topic
- Under 15 words

### Alt caption
- Shorter version (under 150 characters) for Stories or cross-posting
- Hook line + product name + one outcome claim

---

## Posting Notes to Include

- **Link in bio:** which URL should be in bio at time of posting
- **Tag:** whether to tag @anthropic, @openai, etc. (only if the account follows them or they're directly relevant)
- **Timing:** best posting window based on AI/tech audience (weekday mornings 8–10am or evenings 6–8pm)
- **Attribution:** run `python -m lib.assets attribution projects/<slug>` and list any assets requiring credit in the caption or pinned comment. If none, state "No attribution required."

---

## Output Format

Save to `projects/<slug>/output/instagram-caption.md`:

```markdown
# Instagram Caption — [project-slug]

**Project:** [slug]
**Rendered:** [date]
**Reel duration:** [Xs]

---

## Caption (copy-paste ready)

[hook line]

[body — 3–5 paragraphs]

[CTA line] ↓

---

## Hashtags

#Tag1 #Tag2 ... (15 total)

---

## Alt caption (shorter, hook-first)

[Under 150 chars]

---

## First comment (post immediately after)

[Question to drive engagement]

---

## Posting Notes
- Link in bio: [URL]
- Tag: [accounts if relevant, or "none"]
- Best posting window: [timing]
- Attribution: [asset credits or "No attribution required"]
```

---

## Quality Check Before Saving

- [ ] Hook line under 12 words, no emoji
- [ ] Product name and URL appear in body
- [ ] CTA matches reel's CTA angle from script.md
- [ ] Exactly 15 hashtags
- [ ] First comment is a question
- [ ] Attribution check run via `python -m lib.assets attribution`
- [ ] Alt caption under 150 characters

---

## Relationship to Other Skills

**render** — must complete before publish-prep runs (output file must exist)
**reel-learning** — runs alongside publish-prep after render; both are post-render steps
**feedback-capture** — if the user reviews the caption and gives feedback, capture it
**source-brief** — provides the original topic and proof claims that the caption should echo
