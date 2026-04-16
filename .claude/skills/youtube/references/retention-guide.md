# YouTube Retention Scripting Guide

Reference for the `youtube` skill suite. Read before writing any YouTube script or hook variants.

---

## The Drop-Off Anatomy

Average viewer behavior across YouTube long-form content:
- **55% of viewers leave within the first 60 seconds** if the hook doesn't deliver
- **Average view duration across all content: 23-27%** of total runtime
- **Strong channels target: 40-55%** average view duration
- **Algorithm promotion threshold: 50%** — below this, distribution is suppressed

**What this means for scripting:** The first 60 seconds are not the opening — they are the audition. The video either earns the next 10 minutes there or it doesn't.

---

## Drop-Off Curve Types

Understanding which curve a video tends to produce helps diagnose retention problems:

| Curve type | Pattern | Cause | Fix |
|---|---|---|---|
| **Cliff** | Steep immediate drop in first 30s | Hook didn't match the audience expectation | Rewrite hook, be more specific about who this is for |
| **Valley** | Drop after intro before stabilizing | Intro runs too long, delays value delivery | Cut intro, jump to first proof faster |
| **Steady decline** | Gradual consistent downward slope | Content is working, just long | Acceptable. Consider shorter cut of the same video |
| **Sawtooth** | Sharp drops followed by recoveries | Pattern interrupts are working but chapters aren't | Add more chapters so viewers can skip |
| **Suspension bridge** | Hold, big drop at midpoint, recovery | Mid-video content is weak or tangential | Identify the weak section and cut or replace it |

---

## The Hook Formula (First 30 Seconds)

The hook must complete three jobs in 30 seconds or fewer:

**Job 1: Grab (0:00-0:05)**
Create an immediate reason to stay. Options:
- A bold claim that contradicts what the viewer expects
- A specific result being shown on screen (pattern interrupt for a tutorial)
- An open loop: "By the end of this video, you'll know exactly how to X"
- A problem statement that makes the viewer think "that's me"

**Job 2: Promise (0:05-0:15)**
Tell the viewer explicitly what they will get from watching. Be specific.
- Bad: "In this video I'm going to show you some really cool AI tips"
- Good: "In the next 12 minutes I'm going to show you exactly how to set up Claude Projects to run your workflows automatically — no coding required"

**Job 3: Stakes (0:15-0:30)**
Answer: "Why does this matter? Why now?" Options:
- The cost of NOT knowing this
- The competitive advantage of knowing it first
- The size of the result possible
- The contrast between current behavior and new behavior

---

## Pattern Interrupt Rules

**Frequency:** Every 60-90 seconds mandatory. No exceptions.

**What counts as a pattern interrupt:**
- Cut to B-roll, product screenshot, or graphic (any visual change)
- Camera angle change
- Verbal pivot: "But here's what most people miss..." / "Now this is where it gets interesting..."
- Sound effect or music shift
- Text overlay appearing on screen
- Quick cut to a different section and back

**What does NOT count:**
- Saying "so let's continue" and continuing the same visual
- Adding a graphic that's on screen for less than 1 second
- Verbal transitions with no visual change

**Tracking rule:** As you write the script, track elapsed time since the last pattern interrupt. When approaching 90 seconds, force one in even if it's a simple camera change cue.

---

## CTA Timing Science

Two CTAs are standard in educational YouTube content:

**Mid-CTA (~25% of total runtime)**
- Goal: capture early-dropoff subscribers
- Tone: soft, conversational, no urgency
- Format: "If this is useful, subscribe — I post [topic] breakdowns every [frequency]"
- Key rule: must not interrupt the value delivery — place it at a natural pause

**Re-hook (~60% of total runtime)**
- Goal: reactivate viewers who are drifting toward clicking away
- Not a CTA — it's a retention anchor disguised as new information
- Format: "Now here's the part most people skip past..." or "This is actually what I wanted to show you all along..."
- The re-hook works by creating a new open loop at the point where the viewer might otherwise decide they've "gotten enough"

**Final CTA (last 60 seconds)**
- Hard ask: subscribe, follow link, comment
- Specificity wins: "Click subscribe if you want the second part of this" beats "subscribe for more content"
- Always include: end screen verbal cue, next-video tease, reason to act now

---

## Content Block Architecture

Each major content block (demo section, concept section) should be structured:

```
Setup: Why does this section matter? (15-30 seconds)
Demo/Proof: Show it — specific, visual, narrated (2-4 minutes)
Pattern interrupt: Visual change or verbal pivot (5-10 seconds)
Payoff: What does this mean for the viewer? (15-30 seconds)
Forward hook: Why they should stay for the next section (5-10 seconds)
```

Never end a section without a forward hook into the next one.

---

## Intro Length Rules

The intro should be as short as possible while completing its job.

| Channel stage | Intro length |
|---|---|
| New / small channel | 15-30 seconds max — viewer doesn't know you yet, earn attention fast |
| Growing channel | 30-60 seconds — earned slightly more patience, but still ruthless |
| Established channel | Up to 90 seconds — but only if the hook was strong enough to earn it |

**Banned intro patterns:**
- "Hey guys, welcome back to the channel" — kills retention immediately
- Long backstory before the value starts
- Showing the full outline before any payoff
- Asking for a subscribe before delivering any value

---

## Outro Architecture

The last 60 seconds of a YouTube video are underused by most creators.

**Optimal outro structure:**
1. **Payoff recap** (10s): One sentence restatement of the main thing they learned
2. **Stakes elevation** (10s): Why this matters more than they might think
3. **CTA** (15s): Specific action with specific reason — not generic
4. **End screen** (20s): Dedicated 20-second end card for YouTube's end screen feature
5. **Next-video tease** (5s): One sentence about the next video — this keeps viewers in the session

The end screen 20 seconds must be kept clean of important spoken content — viewers are clicking cards during this window.

---

## Human vs AI Narration

**Key data point:** Videos with human voice narration consistently outperform AI/synthetic narration by 15-25% in average view duration on equivalent content.

**Why it matters for scripting:**
- If the creator is recording their own voice, the script can include more nuanced delivery cues (pause, emphasis, tone shift) that a human can execute
- If using synthetic voice (e.g., ElevenLabs), write in shorter sentences with more explicit pace markers
- The YouTube algorithm's LLM content analysis may penalize synthetic narration for AI-related topics where the viewer expects authentic experience

**Recommendation:** For AI tool tutorials, human narration creates stronger authenticity signal and better retention. Prioritize recorded human voice over synthetic if possible.
