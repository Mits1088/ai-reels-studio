---
description: Post-render learning capture — records what worked and what didn't from completed reels to improve future projects
globs: ["**/learnings.md", "**/qa_report.json"]
---

# Reel Learning

Adapted from ruflo's self-learning pattern. After a reel renders successfully, capture what worked so future reels start stronger.

---

## Three Memory Systems — How They Differ

The pipeline uses three distinct memory mechanisms. Each answers a different question at a different time.

| System | File | When written | What it captures | Who uses it |
|---|---|---|---|---|
| **Global taste memory** | `memory/creative-feedback.json` | After 2+ signals from independent review rounds confirm a pattern | Aesthetic preferences: hard rules, soft preferences, component guidance, motion notes — generalizable across all future reels | Claude reads before every planning phase (script, shot-list, motion-intent, assembly) |
| **Project review feedback** | `projects/<slug>/output/review-feedback.md` | After any review round (hook preview, QA review, final render) — managed by `feedback-capture` skill | Per-round taste signals for the current project: what worked, what felt plain, what to change | Claude reads before revision rounds and before continuing any phase within the same project |
| **Post-render learning** | `projects/<slug>/output/learnings.md` | After Phase 7 render completes successfully — managed by this file | Structural outcomes: hook patterns that worked, proof methods, pacing numbers, encoding issues, revision count | Claude reads at start of similar new projects (same product type, same style, same audience) |

**Global taste memory** is global and permanent once promoted. **Project review feedback** is project-scoped and can inform global memory via the `feedback-capture` promotion process. **Post-render learning** is project-scoped and structural — it never automatically becomes a global rule.

If feedback from a review session is clearly one-off (product-specific, unique to this reel): write to project review feedback only. If the same feedback appears across 2+ projects: the `feedback-capture` skill will propose promoting it to global taste memory.

---

## When to Capture Post-Render Learnings

After Phase 7 (render) completes successfully — and only then. Do not capture learnings from failed or abandoned reels (they teach different lessons that should be captured as feedback memories via `feedback-capture`, not as render learnings).

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
