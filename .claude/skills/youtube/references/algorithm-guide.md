# YouTube Algorithm Guide

Reference for the `youtube` skill suite. Read before writing any YouTube script or planning content strategy.

---

## Three Distribution Systems

YouTube's algorithm operates as three separate systems. Content that performs in one does not automatically perform in others.

### 1. Search Feed
- Triggered by: specific keyword queries
- Primary signals: title match, description relevance, watch time percentage, click-through rate
- Best content type: how-to, tutorials, specific tool breakdowns
- Keyword placement: first 40 characters of title, first 150 characters of description

### 2. Browse / Home Feed
- Triggered by: viewer history, subscriptions, recent watch patterns
- Primary signals: click-through rate (CTR), absolute watch time
- Best content type: engaging hooks, emotionally resonant thumbnails, pattern-interrupting titles
- Keyword placement: less critical — thumbnail and title emotion matter more

### 3. Suggested / Recommended
- Triggered by: session continuation — appears alongside similar videos
- Primary signals: viewer overlap with other channels, session watch time
- Best content type: deeper dives on topics viewers just watched
- Keyword placement: topic coherence matters more than exact keyword match

**Write scripts knowing which feed is the primary target.** A how-to tutorial should be written differently from a trend commentary piece.

---

## Watch Time Hierarchy

YouTube's internal ranking (from public documentation and creator research):

1. **Average View Duration (%)** — Most important. What percentage of the video do viewers watch?
2. **Absolute Watch Time (minutes)** — Total minutes watched across all viewers
3. **Click-Through Rate (CTR)** — Of impressions shown, what percentage clicked?
4. **Re-watches and shares** — Strong positive signals
5. **Likes, comments** — Moderate positive signals
6. **Dislikes and leaves** — Negative signals

**Rule:** A 50% average view duration is the threshold between "being pushed" and "being suppressed." Below 50% = algorithm reduces distribution. Above 50% = algorithm tests wider audiences.

---

## CTR Dynamics

- **Impression CTR** directly controls initial distribution burst
- Typical mature video CTR: 4-8% (varies by niche)
- CTR spikes in first 24-48 hours (warm subscriber audience — highest CTR)
- CTR stabilizes lower as video reaches cold Browse audiences
- A video with high CTR + high AVD gets promoted aggressively

**For new videos:** CTR in first 24 hours determines whether YouTube shows it to cold audiences at all.

---

## The First 24-48 Hour Window

YouTube uses the first 24-48 hours as a testing period:
1. Video is shown to subscribers and viewers with similar history
2. If CTR and AVD are strong → shown to progressively colder audiences
3. If CTR and AVD are weak → distribution caps early

**Implication for scripts:** The hook and first 30 seconds determine whether the video gets a second chance with wider audiences.

---

## Freshness and Decay

**Long-form videos:** Decay is gradual. A well-performing video can rank and surface for months or years (evergreen). YouTube doesn't heavily penalize age for search-intent content.

**Shorts:** Freshness decay is aggressive — distribution drops significantly after 28-30 days (as of Sept 2025). Less relevant for YouTube long-form strategy.

---

## 2024-2025 Algorithm Changes

- **LLM topic classification:** YouTube now uses LLMs to understand video topic, not just title/tag keywords. This means tag stuffing is less effective; actual content coherence matters more.
- **Clickbait penalty:** YouTube's AI compares title/thumbnail claims to actual content. Videos where the title promises something the video doesn't deliver are penalized in sustained distribution.
- **Chapter navigation:** Videos with chapters see up to 50% increase in average view duration — viewers skip to relevant sections rather than abandoning.
- **AI narration retention gap:** Videos with AI/synthetic narration consistently show 15-25% lower average view duration compared to human narrators on equivalent content.

---

## Pattern Interrupt Science

Average drop-off happens at predictable moments:
- **0:00-0:30:** Highest drop-off — viewer decides if the video is for them
- **Every 60-90 seconds:** Secondary drop-off without a retention anchor
- **~50-60% mark:** Major drop-off event — "I've gotten enough value" check

**Pattern interrupts reset the drop-off clock.** Each interrupt buys another 60-90 seconds of attention. Interrupts include: B-roll cuts, camera angle changes, graphics/text cards, verbal pivots ("But here's the thing..."), music shifts.

---

## Recommended Content Length (AI/Tech niche)

| Content type | Optimal length | Why |
|---|---|---|
| Tool tutorial / deep dive | 8-15 min | Enough time for substantial demo; high watch time ceiling |
| Feature breakdown | 5-10 min | Specific audience, focused search intent |
| Comparison video | 10-18 min | Viewer wants comprehensive coverage |
| Opinion/commentary | 6-12 min | Shorter if point is clear; longer if developing nuanced argument |

Longer is NOT always better. The goal is: fill every minute with value that keeps the viewer in the video. Dead air, padding, and slow setup kill AVD.
