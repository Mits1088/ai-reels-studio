# YouTube SEO Sub-skill

**Invoked by:** `/youtube seo`

Generate a complete, copy-paste-ready YouTube SEO metadata package: 3 title variants, full description, tags, chapters, hashtags, and VideoObject schema markup.

---

## Load Reference Guide

Read `.claude/skills/youtube/references/seo-playbook.md` before writing.

---

## Required Input

- `projects/<slug>/youtube/script.md` — for primary claim, chapter map, and topic
- `projects/<slug>/youtube/hooks.md` — for the selected hook title direction

---

## Step 1 — Keyword Research

Before writing titles, identify the primary keyword and 3-5 secondary keywords.

**Primary keyword:** the exact phrase viewers searching for this video would type. Extract from:
- The script's primary claim
- The reference video's title (what keyword made it rank)
- The topic's most natural search form

Check the primary keyword fits this pattern:
- It fits naturally in the first 40 characters of a title
- It is specific enough to have search intent, not so broad it has no ranking chance
- It is the phrase a viewer would type AFTER having the problem, not before

**Secondary keywords:** related phrases that should appear naturally in the description body and tags.

---

## Step 2 — Generate 3 Title Variants

Each title must:
- Be 60-100 characters total
- Contain the primary keyword within the first 40 characters
- Use a different psychological mechanism (curiosity gap, result-first, authority/number)
- Sound like something a real person would click, not manufactured SEO

**Title variant types:**

**Variant A — Result-First (strongest for search)**
Format: `[Primary keyword] — [Specific result or transformation]`
Example: `Claude Projects Tutorial — How I Cut My Workflow Time in Half`

**Variant B — Curiosity Gap (strongest for Browse/Suggested)**
Format: `[Primary keyword] + [what most people don't know / the hidden part]`
Example: `The Claude Feature Nobody Talks About (Projects Deep Dive)`

**Variant C — Number + Authority (strongest for credibility-first topics)**
Format: `[Number] [Things/Ways/Steps] to [Primary keyword result]`
Example: `5 Claude Projects Features You're Not Using (Full Walkthrough)`

**Title rules:**
- No ALL CAPS beyond one word
- No consecutive exclamation marks
- No "You Won't Believe" or similar clickbait patterns — YouTube's 2025 AI policy penalises thumbnails/titles that mislead
- Every title must be supported by the actual video content — no exaggeration
- The title and thumbnail must add different information (not repeat each other)

---

## Step 3 — Write the Full Description

**Structure:**

```
[First 150 characters — visible before "Show more"]
The value hook. Must contain primary keyword AND a compelling reason to watch.
This is what appears in Google search results and YouTube SERP snippets.

[150-500 characters — above the fold on mobile]
1-2 sentences expanding the promise.
What will the viewer know or be able to do after watching?

[500-2000 characters — body after Show more]
2-4 paragraphs.
Natural integration of primary keyword (2-4 times total across full description).
Integration of 2-3 secondary keywords.
Reference specific chapter topics to signal depth to the algorithm.
Brief credibility or context line.

[Chapters — always include]
00:00 [Chapter 1 title]
01:30 [Chapter 2 title]
...

[Links — if applicable]
🔗 [Named link, not raw URL]

[3-5 hashtags at the very end]
#tag1 #tag2 #tag3
```

**Description rules:**
- First 150 characters are critical — do not waste them on channel name or generic openers
- Keyword density: 2-4 natural mentions of primary keyword across full description (not stuffed)
- Chapters MUST start at 0:00 and include at minimum 3 entries
- Hashtags go at the very end — YouTube ignores all hashtags if you use more than 15
- Do not add irrelevant hashtags — relevance matters more than volume

---

## Step 4 — Generate Tags

Produce 10-15 tags. Total character count must stay under 500 characters.

**Tag order (priority order matters for YouTube processing):**
1. Primary keyword (exact match)
2. Primary keyword with one modifier (broad + specific)
3. Tool/product name alone
4. Tool/product name + use case
5. Secondary keywords
6. Related topic keywords
7. Broad category tags last

**Tag rules:**
- No tags over 30 characters
- Mix single-word and multi-word tags
- Include misspellings only if widely used (e.g., "chat gpt" alongside "chatgpt")
- Do not include competitor channel names

---

## Step 5 — Chapter Timestamps

Pull chapter timestamps from `youtube/script.md` chapter map.

**Chapter rules:**
- Must start at 0:00
- Minimum 3 chapters (fewer chapters = YouTube doesn't display them)
- Chapter titles should be keyword-rich but natural-sounding
- Chapter title max ~28 characters for clean display on all devices
- Chapters increase viewer retention up to 50% by letting viewers navigate — always include them

---

## Step 6 — Hashtags

Select 3-5 hashtags. These appear above the title and next to it in some interfaces.

**Hashtag selection rules:**
- First 3 hashtags appear in the title row — choose the most relevant
- Do not repeat the video title verbatim
- Mix a broad hashtag (high volume), a mid-tier hashtag (medium volume), and a niche hashtag (low competition)
- YouTube displays the first 3 above the title — make the first one your strongest keyword hashtag

---

## Step 7 — VideoObject Schema Markup

Generate JSON-LD schema for the video's web presence (for channel website, blog post, or pinned comment context):

```json
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "[Selected title]",
  "description": "[First 300 characters of description]",
  "thumbnailUrl": "[To be filled after thumbnail is uploaded]",
  "uploadDate": "[YYYY-MM-DD — to be filled at publish]",
  "duration": "PT[X]M[Y]S",
  "publisher": {
    "@type": "Organization",
    "name": "[Channel name]",
    "logo": {
      "@type": "ImageObject",
      "url": "[Channel logo URL]"
    }
  },
  "contentUrl": "[YouTube URL — to be filled at publish]",
  "embedUrl": "[YouTube embed URL — to be filled at publish]"
}
```

Mark placeholder fields clearly. The creator fills them at publish time.

---

## Output

Produce `projects/<slug>/youtube/seo-package.md`:

```markdown
# YouTube SEO Package: [Project Slug]

**Primary keyword:** [keyword]
**Secondary keywords:** [keyword 1], [keyword 2], [keyword 3]
**Target CTR:** [X%] (benchmark from seo-playbook for this niche)

---

## Title Variants

**Variant A (Result-First — recommended for search):**
[Title — character count]

**Variant B (Curiosity Gap — recommended for Browse/Suggested):**
[Title — character count]

**Variant C (Number + Authority):**
[Title — character count]

**Recommended title:** Variant [X] — [one sentence reason]

---

## Full Description

[Complete description — copy-paste ready, with chapters, links placeholder, and hashtags]

---

## Tags

[tag1], [tag2], [tag3], ... (total: [X] chars)

---

## Chapters

00:00 [Chapter 1]
01:30 [Chapter 2]
...

---

## Hashtags

#tag1 #tag2 #tag3 #tag4 #tag5

---

## VideoObject Schema

[JSON-LD block with placeholders marked]

---

## Pre-Publish Checklist

- [ ] Primary keyword appears in first 40 characters of selected title
- [ ] First 150 chars of description contain keyword + compelling reason to watch
- [ ] Chapters start at 0:00 and have minimum 3 entries
- [ ] Tag count between 10-15, total under 500 characters
- [ ] Hashtag count between 3-5
- [ ] Title and thumbnail show different information (no text duplication)
- [ ] No misleading claims in title that the video doesn't support
- [ ] VideoObject schema placeholders filled before publish
```

---

## Stop Condition

Deliver `seo-package.md`. Present it for review.

Do not proceed to `/youtube thumbnail` until the preferred title variant is confirmed — the thumbnail brief depends on the selected title.
