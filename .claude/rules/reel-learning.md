---
description: Post-render learning capture — records what worked and what didn't from completed reels to improve future projects
globs: ["**/learnings.md", "**/qa_report.json"]
---

# Reel Learning

Adapted from ruflo's self-learning pattern. After a reel renders successfully, capture what worked so future reels start stronger.

## When to Capture

After Phase 7 (render) completes successfully — and only then. Do not capture learnings from failed or abandoned reels (they teach different lessons that should be captured as feedback memories, not reel learnings).

## What to Capture

For every completed reel, record these in `projects/<slug>/output/learnings.md`:

### 1. Input Quality Assessment
- What was the starting input? (URL, topic, brief)
- What was the `input_quality` score?
- Did the input quality prediction match the actual pipeline experience?
- How many revision rounds happened? (brief, script, shot-list, assembly)

### 2. Hook Performance
- What hook pattern was used? (cost tension, secret knowledge, result-first, number + outcome)
- What was the first frame?
- Did the hook require revision? If so, what changed?
- Note: "This hook style worked for [product type] aimed at [audience]"

### 3. Proof Strategy
- How many unique screenshots were used?
- How many demo videos?
- What proof method per claim worked? (screen recording, mock HTML, screenshot + zoom, animated component)
- Were there MISMATCH/MISSING fitness scores at shot-list? What was the resolution?

### 4. Pacing & Structure
- Final duration
- Beat count
- Style used (cinematic-presenter / editorial-authority)
- Visual change frequency (average seconds between visual state changes)
- Avatar on-screen percentage
- Were there any QA flags for pacing?

### 5. Technical Patterns
- What playback rates were used? (any sped-up videos)
- What zoom coordinate approach worked? (auto from Stage 3, manual, vision-estimated)
- What transition types dominated?
- Were there encoding issues?
- What SFX count was used?

### 6. What Would Be Done Differently
- One sentence on what would improve the reel if made again
- One sentence on what should be repeated

## learnings.md Structure

```markdown
# Reel Learnings: [project-slug]

**Rendered:** [date]
**Duration:** [seconds]
**Style:** [cinematic-presenter / editorial-authority]
**Input quality:** [excellent / great / good / bad]
**Revision rounds:** [count]

## Hook
- Pattern: [cost tension / secret knowledge / result-first / number + outcome]
- First frame: [description]
- Revised: [yes/no — if yes, what changed]

## Proof
- Screenshots: [count]
- Demo videos: [count]
- Fitness blockers resolved: [count]
- Strongest proof moment: [description]

## Pacing
- Beats: [count]
- Visual changes: every [X]s average
- Avatar on-screen: [X]%
- QA pacing flags: [none / list]

## Technical
- Encoding issues: [none / list]
- Zoom approach: [auto / manual / vision-estimated]
- SFX count: [X]

## Repeat
[What worked well and should be repeated]

## Improve
[What would be done differently next time]
```

## How Future Reels Use This

When starting a new reel with similar characteristics (same product type, same style, same audience), read previous learnings:

1. `new-reel` skill checks if similar completed projects exist
2. If found, read their `output/learnings.md`
3. Apply: hook patterns that worked, proof methods that resolved fitness, pacing that passed QA
4. Avoid: patterns that caused revision cycles, encoding issues, QA failures

This is not a database or vector search — it's simple markdown file comparison. Check 2-3 most recent completed projects before starting a new one.

## Important Constraint

Do not over-optimize from a small sample. With 13 projects, patterns are suggestive, not definitive. Use learnings as starting points, not rules. The brief and shot-list approval gates remain the real quality controls.
