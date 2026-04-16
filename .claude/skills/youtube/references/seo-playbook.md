# YouTube SEO Playbook

Reference for the `youtube` skill suite. Read before generating any SEO metadata package.

---

## Title Optimization

### Length
- **Optimal range: 60-100 characters total**
- Titles 70-100 characters outperform shorter titles by 10-14% in sustained impressions
- Under 60 characters: leaves keyword opportunity unused
- Over 100 characters: truncated in most surfaces, second half never seen

### Keyword Placement
- **Primary keyword must appear in the first 40 characters**
- YouTube's LLM processes title weight from left to right — first 40 characters get the highest semantic weight
- The primary keyword is the phrase a viewer would type after having the problem

### Power Words That Increase CTR
- "How to", "Complete", "Guide", "Ultimate", "Step by Step", "In [Year]"
- Numbers: "5 Ways", "7 Things", specific stats
- Urgency: "Before It's Too Late", "Right Now"
- Contrast: "Nobody Talks About", "Most People Miss", "The Hidden"

### 2025 Anti-Clickbait Policy
YouTube's AI compares title/thumbnail claims to actual video content. Penalised patterns:
- Titles that promise something not in the video
- Emotion-first titles with no specific claim ("This Changed My Life")
- Titles that exaggerate results beyond what the video shows
- Excessive use of ALL CAPS more than one word

---

## Description Strategy

### The First 150 Characters (critical)
- Displayed before "Show more" in most YouTube surfaces
- Used as the snippet in Google search results
- Must contain: primary keyword + compelling reason to watch
- Must NOT open with the channel name, generic welcome, or "In this video..."
- Write this line as if it must stand alone and still make someone click

### Description Body (150-2000 characters)
- **2-4 natural mentions** of the primary keyword across the full description
- **2-3 secondary keyword mentions** — naturally integrated, not stuffed
- Reference specific chapter topics by name — signals content depth to algorithm
- Include one credibility or context sentence if relevant
- Do not copy-paste the script — the description adds context, not repetition

### What NOT to do
- Do not start with "In this video I will..." (wastes prime real estate)
- Do not list 20+ unrelated keywords at the bottom — treated as spam
- Do not use the same keyword more than 4 times — triggers over-optimization flag

---

## Chapter Optimization

### Why chapters matter
- Chapters increase average view duration by up to **50%** — viewers navigate rather than abandon
- Each chapter creates a separate SEO entry point in Google's video search
- YouTube's chapter titles appear in the SERP preview with individual timestamps
- Chapters signal high-value, organized content to the algorithm

### Requirements
- Must start at **0:00**
- Must have a minimum of **3 chapters** for YouTube to display them
- Chapter titles should be keyword-rich but natural (not stuffed)
- **Maximum ~28 characters per chapter title** for clean display on all devices
- Chapters must be in the description body (not just the chapters feature)

### Chapter title examples
- Bad: "Part 1 — Introduction" (no keyword value)
- Good: "Claude Projects Setup (0:00)" (keyword + context)
- Good: "Live Demo: Workflow Automation (3:30)" (keyword + content signal)

---

## Tag Strategy (Post-2024)

Tags have significantly less impact since YouTube's LLM topic detection replaced keyword-matching for content classification. However:
- Tags still help for niche disambiguation (same-name topics in different industries)
- Tags help with long-tail discovery at the edges of YouTube's LLM confidence
- **10-15 tags, total under 500 characters**

### Tag priority order
1. Exact primary keyword match
2. Primary keyword + main modifier
3. Tool/product name alone
4. Tool/product name + primary use case
5. Secondary topic keywords
6. Broad category tags (lowest priority, add last)

### Tag rules
- No tags over 30 characters
- No competitor channel names
- No irrelevant broad tags (e.g., "AI", "tutorial" on every video regardless of topic)
- Misspellings only if the misspelling has documented search volume

---

## Hashtag Rules

- **3-5 hashtags maximum** — YouTube displays the first 3 above the title
- More than 15 hashtags → YouTube ignores ALL hashtags on that video
- The first hashtag is the most important — it appears first in the title display
- Hashtags should add classification value, not repeat the title
- Use: one broad hashtag (category), one mid-tier (topic), one niche-specific

---

## VideoObject JSON-LD Schema

For any channel website, blog post, or external page embedding a YouTube video, include VideoObject schema:

```json
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "[Video title]",
  "description": "[First 300 characters of description]",
  "thumbnailUrl": "[Thumbnail URL from YouTube CDN]",
  "uploadDate": "[ISO 8601 date]",
  "duration": "[ISO 8601 duration, e.g. PT12M30S]",
  "contentUrl": "[Full YouTube watch URL]",
  "embedUrl": "[https://www.youtube.com/embed/VIDEO_ID]"
}
```

**Why it matters:** 29.5% of Google AI Overviews cite YouTube videos. Properly marked-up videos rank more frequently in AI Overview citations.

---

## SEO Benchmarks by Niche (AI/Tech)

| Metric | Average | Strong performer |
|---|---|---|
| CTR (Search) | 4-6% | 8%+ |
| CTR (Browse) | 6-10% | 12%+ |
| Average View Duration | 28-35% | 45%+ |
| Click-to-subscribe conversion | 0.5-1% | 2%+ |

---

## Pre-Publish SEO Checklist

- [ ] Primary keyword in first 40 characters of title
- [ ] Title 60-100 characters
- [ ] First 150 characters of description contain keyword + hook
- [ ] Description body has 2-4 keyword mentions (not stuffed)
- [ ] Chapters start at 0:00, minimum 3 entries, titles under 28 characters
- [ ] Tags: 10-15, under 500 characters total, priority order followed
- [ ] Hashtags: 3-5 only
- [ ] VideoObject schema prepared for website/blog use
- [ ] Thumbnail text does not repeat title text verbatim
