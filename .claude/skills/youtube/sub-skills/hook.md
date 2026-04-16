# YouTube Hook Sub-skill

**Invoked by:** `/youtube hook`

Generate 5 distinct 30-second hook variants for the YouTube video, each using a different psychological retention mechanism. The creator picks one (or combines elements from several).

---

## Load Reference Guide

Read `.claude/skills/youtube/references/retention-guide.md` before writing.

---

## Required Input

- `projects/<slug>/youtube/script.md` — for the video's primary claim, angle, and audience
- If no script exists yet, ask the user for: topic, primary claim, target audience

---

## The Five Hook Types

Generate one variant for each type. Every hook is ~75 words, ~30 seconds spoken at 150 wpm.

---

### Hook 1: Shock / Contradiction

**Mechanism:** Opens with a counterintuitive claim that produces cognitive dissonance. The viewer's brain needs to resolve the contradiction, so they keep watching.

**Formula:** State something that contradicts the viewer's assumption → reveal the unexpected truth → make the payoff personal.

**Template:**
```
[Contradicts assumption they hold] — [unexpected truth about the topic] — [what it means for them personally].
In this video I'm going to show you [specific promise].
```

**Example for an AI tool video:**
```
You're probably using this AI tool the same way everyone else does — and that's exactly why you're getting the same mediocre results. There's a completely different way to use it that almost nobody talks about. One that turns it from a chatbot into something that actually does the work for you. I'm going to show you exactly what that looks like.
```

**Drop-off risk:** Low (contradiction creates immediate cognitive pull)
**Best for:** Topics where the viewer has existing habits or assumptions to break
**Optimal traffic source:** Browse feed (pattern breaks stop the scroll)

---

### Hook 2: Problem-Agitation

**Mechanism:** Names a specific pain the viewer feels, amplifies it briefly, then promises relief. Works because recognition is immediate — the viewer thinks "that's me."

**Formula:** Name the exact pain → agitate (make it feel bigger) → promise the specific solution → preview the video's proof.

**Template:**
```
If you're still [doing the painful thing], [agitated cost of continuing]. 
[The solution exists]. And in this video I'm going to show you [specific transformation].
```

**Example:**
```
If you're still spending hours building content manually — writing, formatting, researching one piece at a time — you're losing time you're never getting back. There's a better way to do this, and it doesn't require expensive tools or a big team. In this video I'll show you the exact workflow I use to do in 20 minutes what used to take me half a day.
```

**Drop-off risk:** Low-Medium (strong for pain-aware audiences, weaker for discovery audiences)
**Best for:** Tutorial and workflow videos targeting people with an existing frustration
**Optimal traffic source:** Search (pain-aware viewers searching for solutions)

---

### Hook 3: Story Open (In Medias Res)

**Mechanism:** Drops the viewer into the middle of an active situation. The narrative tension of "what happens next?" keeps them watching.

**Formula:** Begin at a specific moment of action → reveal the surprising outcome → connect it to what the viewer will learn.

**Template:**
```
[Specific scene, active tense, specific detail]. [What I discovered]. 
Here's what I want to show you.
```

**Example:**
```
Three weeks ago I gave an AI tool one sentence — and it built me a complete presentation deck, formatted and ready to send. I didn't type anything else. I just watched it work. I've been testing this approach every day since then and the results keep getting better. Here's everything I've learned.
```

**Drop-off risk:** Low-Medium (depends on how specific and relatable the story is)
**Best for:** Case study and "I tried this" formats
**Optimal traffic source:** Browse and Suggested (story energy stops scrollers)

---

### Hook 4: Curiosity Gap

**Mechanism:** Reveals the existence of something the viewer didn't know they were missing, without revealing what it is. The unresolved tension forces them to keep watching.

**Formula:** Hint at the hidden knowledge → qualify why the viewer hasn't found it → promise the reveal.

**Template:**
```
There's a [feature/method/technique] inside [tool/topic] that [almost nobody knows about / most people skip past / doesn't get covered in any tutorial].
[Why it matters]. And in this video I'm going to show you exactly what it is and how to use it.
```

**Example:**
```
There's a setting inside this AI tool that completely changes what it can do for you — and it's not in any tutorial I've ever seen. It's buried two menus deep and it's turned off by default. Once you find it, you'll wonder how you ever worked without it. I'm going to show you where it is and exactly what it unlocks.
```

**Drop-off risk:** Medium (depends on how specific the "gap" feels — vague gaps feel like clickbait)
**Best for:** Feature reveals, hidden capabilities, lesser-known tools
**Optimal traffic source:** Browse (curiosity stops scrollers; also works well for suggested)

---

### Hook 5: Social Proof

**Mechanism:** Opens with credibility and stakes — a number, a result, a recognized name, or an authority signal. Tells the viewer immediately that this is worth their time.

**Formula:** Lead with the scale or authority → connect it to the viewer's situation → promise the specific transfer of value.

**Template:**
```
[Credibility signal: number, result, or authority]. [What that proves]. 
[What you're going to show them].
```

**Example:**
```
Over four million people have downloaded this AI tool in the last 90 days. Most of them are using it like a search engine. The ones getting real results are using it completely differently — as a workflow engine that does the work rather than just answers questions. In this video I'll show you exactly what that workflow looks like.
```

**Drop-off risk:** Low for established audiences, Medium for cold audiences
**Best for:** Broad-topic educational videos, product overviews
**Optimal traffic source:** Search (authority signals work well for search-intent viewers)

---

## Evaluation Table

After writing all 5 hooks, produce this table:

```markdown
## Hook Comparison

| Hook | Type | Drop-off Risk | Best Traffic | Best for this video because... |
|---|---|---|---|---|
| Hook 1 | Shock/Contradiction | Low | Browse | [one sentence] |
| Hook 2 | Problem-Agitation | Low-Med | Search | [one sentence] |
| Hook 3 | Story Open | Low-Med | Browse/Suggested | [one sentence] |
| Hook 4 | Curiosity Gap | Medium | Browse | [one sentence] |
| Hook 5 | Social Proof | Low | Search | [one sentence] |

**Recommended:** Hook [X] — [reason it fits this specific video best]
```

Base the recommendation on: the primary claim, the angle vs the reference video, and which hook type the reference video did NOT use (differentiation opportunity).

---

## Output

Produce `projects/<slug>/youtube/hooks.md` with all 5 hooks and the evaluation table.

---

## Stop Condition

Deliver `hooks.md`. Present all 5 hooks and the recommendation.

The creator selects one (or asks to combine elements). That selected hook replaces the placeholder in `youtube/script.md` before proceeding.

Do not proceed to `/youtube seo` until a hook is selected.
