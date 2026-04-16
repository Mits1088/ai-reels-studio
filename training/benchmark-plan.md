# Benchmark Plan — Reel Quality Evaluation

## Purpose

This benchmark system answers a concrete question: **is the output of the current creative operating system getting closer to the reels we actually like?**

It is used for:
- evaluating generated reel quality against liked reference reels
- tracking whether rule changes produce measurable output improvements
- identifying which parts of the operating system still need tuning
- grounding future rule and feedback decisions in observable output patterns

It is NOT for:
- copying reference reels shot-for-shot
- freezing one creator's execution style into a mandatory template
- overfitting to a small number of liked examples
- replacing the QA gate (benchmarks are editorial; QA gates are technical)

---

## The Overfitting Guard

The training set is small (3 reference reels, 1 annotated). Benchmark comparisons must operate at the **principle level**, not the execution level.

| Principle check (correct) | Execution check (overfitting) |
|---|---|
| "Does the hook create a forward pull into the body?" | "Does the hook use a scrolling icon grid?" |
| "Is there a proof escalation arc?" | "Does the reel follow existence → breadth → process → output → authority?" |
| "Does motion feel motivated rather than ambient?" | "Are hard cuts used instead of fades?" |
| "Does proof arrive before the explanation?" | "Is the card carousel placed in the 5–9s window?" |

Every benchmark dimension in this document is phrased as a principle that would apply to any well-made reel, not as a fingerprint of any one creator.

When a reference reel is used for comparison, extract the principle it demonstrates — then evaluate whether the generated reel satisfies that principle in its own way. A generated reel can satisfy every benchmark dimension without resembling the reference reel at all.

---

## Comparison Dimensions

Score each dimension on a 1–5 scale (or N/A if genuinely not applicable to this reel's format).

Use the scorecard template in `training/benchmark-scorecard.md` to record results.

---

### 1. Hook Recognisability

**What good looks like:** The hook has a stable brand identity — real product UI in frame 0, at least one brand logo, avatar in split-screen, continuous motion element (bounce/scroll/zoom), value claim readable from the first frame, SFX on entry. A viewer who has seen multiple reels from this account would recognise the opening even without seeing the account name.

**What weak looks like:** Generic opener, no logo visible in the first 2 seconds, avatar full-screen alone, warm background with no product UI, no motion in the first 3 seconds, caption fades in after the hook moment passes.

**Watch for:** Hook varies its execution (screenshot, caption, SFX character) but keeps its structural DNA. A hook that is identical in execution to the previous reel on the same product is failing at the elastic dimension.

---

### 2. Hook Execution Quality

**What good looks like:** The value claim is specific and creates curiosity. The product UI shown matches the hook narration. The motion element is continuous and purposeful (logo bounce, Ken Burns with a named focal point, scroll with a clear destination). At least 4 simultaneous visual elements in the first 3 seconds.

**What weak looks like:** Vague value claim ("AI is changing everything"). Product UI visible but unrelated to what the hook narration claims. Motion feels decorative, not purposeful. Fewer than 4 visual elements active simultaneously.

**Watch for:** Hook execution quality degrades when the hook is treated as a template slot to fill rather than a creative problem to solve each time.

---

### 3. Body Variation

**What good looks like:** The body uses at least 3 component families. No single visual role exceeds 40% of body beats. Layout changes at least once every 4 beats. The reel cannot be described by a simple repeating pattern (avatar → screenshot → overlay → avatar → repeat). The viewer's eye encounters genuine variety in how the frame is divided and what occupies it.

**What weak looks like:** Repeating 3-beat cycle throughout. Fake variety: 5 different component names, 1 visual role (all text-emphasis). Avatar layout stays the same for 4+ consecutive beats. The middle section feels like a slideshow with captions.

**Watch for:** Role distribution hiding behind component name variety. Run the role-sequence check from `component-selection-scoring.md` mentally — does the visual role sequence reveal a streak that component names masked?

---

### 4. Proof Cadence and Strength

**What good looks like:** At least one proof visual arrives within the first 5 beats of the body. Proof beats use evidence that matches what the narrator claims — the viewer sees the stat, the UI, the output, the result. Multiple proof methods are used (not just screenshots). Claims are not left floating for more than 2–3 seconds before proof appears. The viewer ends the reel feeling like they witnessed the evidence, not just heard about it.

**What weak looks like:** Proof arrives late (halfway through the body). Proof is decorative — a screenshot unrelated to what the narrator is saying at that moment. Only one proof method used across the full reel (all screenshots or all text overlays). The strongest claim has no visual support.

**Watch for:** The claim-to-proof gap. Does the proof beat follow the claim beat closely, or does the viewer have to trust the narrator for 5+ seconds before seeing anything? Does the proof beat show what the narrator specifically says, or does it show something adjacent?

---

### 5. Motion Quality

**What good looks like:** Most body beats use `still` mode. When a zoom fires, there is a named target. No beat stacks `zoom-in` entry + ambient drift hold. After proof sections, the avatar re-entry uses stronger settle energy. The viewer is never in a state where everything is always drifting — motion marks specific moments of attention direction.

**What weak looks like:** Ken Burns on every screenshot regardless of whether a focal point was named. Entry preset + ambient drift on the same beat (Stacked Motion). First body beat still has hook-level energy — the transition from hook to body substance never lands. Motion feels automated, not authored.

**Watch for:** The Ambient Overrun check — more than 2 consecutive body beats with ambient motion. The Zoom Reflex check — zoom coordinates pointing at the center of an image rather than a named element.

---

### 6. Caption Handling

**What good looks like:** Captions are chunk-sized for mobile (max ~8 words per chunk, max ~2s). Product and tool names are spelled correctly (Claude, not "claud"; ChatGPT, not "chat G.P.T."). Emphasis words are tagged. Caption timing matches phrase boundaries, not arbitrary word boundaries. Captions don't render over important UI elements. No ElevenLabs `--` pause markers visible on screen.

**What weak looks like:** Long run-on caption chunks that are unreadable at mobile size. Product name misspellings. Captions placed in unsafe zones (too close to edges). Captions covering the critical UI element that the proof beat is meant to show.

**Watch for:** Caption polish regression — did the caption-polish phase run, and did it catch the product spelling and chunk length issues?

---

### 7. Component Library Usage

**What good looks like:** The reel uses components that match the narration class for each beat (not just the first available option). Underused components (AnnotationCircle, ToastCard, StrikethroughSwap) are used where they would be strongest. Brand logos appear at the moment a brand is named. No component is used just to add visual interest — each one is there because it is the correct choice for that beat's narration type.

**What weak looks like:** KeywordFadeIn dominance — same component for 5+ beats despite different narration types. OverlayKeyword used when the beat needs a proof visual. Missing brand logo at the moment the product is named. AnnotationCircle and StrikethroughSwap never used even when the beat is a perfect fit.

**Watch for:** The stale mapping patterns from `component-mapping.md` — KeywordFadeIn chain, OverlayKeyword dominance, text-only proof section, same entry preset throughout.

---

### 8. Reset / Pattern Interrupt Quality

**What good looks like:** For reels 35s+, at least one editorial reset separates the proof section from the conclusion. The reset feels timed to a natural content boundary, not inserted at random. After the reset, the energy genuinely changes — the viewer has a brief recalibration moment before the next section.

**What weak looks like:** No reset in a 45s+ reel. Reset exists but is inserted at an arbitrary beat with no connection to the content structure. Multiple resets stacked together (more than the reel duration warrants).

**Watch for:** Does the reset beat feel earned, or does it feel like a technical requirement was met?

---

### 9. Overall — Authored vs Assembled

**What good looks like:** The reel has an editorial point of view. Each beat feels chosen, not filled. The proof arc creates a sense of progression — the viewer is led through a sequence that builds conviction, not just shown a series of facts. The CTA feels like a conclusion to something, not a bolted-on ending.

**What weak looks like:** Predictable 3-beat cycle throughout (assembled). Every section looks interchangeable (no editorial arc). The CTA arrives but nothing led to it. The viewer could have shuffled the middle beats in any order and the reel would have felt the same.

**Watch for:** Can the middle section be described by a repeating pattern? If yes, it was assembled. Does each section have a distinct visual character from the others? If not, variety is cosmetic.

---

## Scoring Model

Use these values when completing the scorecard:

| Score | Label | What it means |
|---|---|---|
| **5** | Excellent | Clearly meets the benchmark — this is what good looks like |
| **4** | Strong | Meets the benchmark with minor gaps |
| **3** | Acceptable | Meets minimum bar but doesn't stand out — room for improvement |
| **2** | Below target | Doesn't meet the benchmark — identifiable gap to address |
| **1** | Weak | Clear failure on this dimension |
| **N/A** | Not applicable | Dimension genuinely doesn't apply to this format |

A reel with all 5s is not the goal — it means the scoring is too easy. The purpose is to identify the weakest 2–3 dimensions per reel and drive focused improvement.

---

## Benchmark Review Questions

Use these when watching the generated reel before scoring:

**Hook:**
- Does the first frame stop the scroll? Does it look like one of our reels?
- Is the value claim specific and immediately credible?
- Are there at least 4 visual elements active in the first 3 seconds?

**Body:**
- Does the body avoid the stale patterns (KeywordFadeIn chain, text-only proof, layout monotony)?
- After watching 2–3 beats, can you predict the rest of the structure? (Bad sign if yes.)
- Does proof arrive before the viewer has time to doubt the claim?

**Motion:**
- Are most body beat holds still? Does motion feel motivated when it fires?
- Does the first body beat feel different from the hook energy (substance, not signature)?
- Is there any obvious Stacked Motion or Zoom Reflex?

**Overall:**
- What single section of the reel is strongest?
- What single section is weakest?
- If you had to improve one dimension to get this closer to the liked references, which dimension is it?
- Does the reel feel authored or assembled?

---

## Learning from Reference Reels Without Cloning Them

### What to extract

When using a liked reference reel for comparison, extract:
- **The persuasion arc** — what sequence of proof types did it use?
- **The rhythm pattern** — how did it oscillate between presenter and proof?
- **The specific attention mechanism** — what kept the viewer watching at the hardest moment (usually 15–25s)?
- **The proof method** — how did it make claims feel credible, specifically?

### What NOT to extract

- The exact shot sequence
- The background colors or visual aesthetic
- The specific components used (unless they were used because of a principle, not habit)
- The creator's verbal style or persona

### The test

After extracting a principle from a reference reel, ask: "Would this principle still apply to a reel on a completely different product by a different creator?" If yes, it's a generalizable principle worth adding to taste-rules.json. If no, it's execution-specific and should stay as a case study in the nicholas-puru-grammar.md file.

---

## When to Run a Benchmark

| Trigger | What to compare |
|---|---|
| After a major rule change (e.g. Change 7, Change 8) | Compare a reel generated before and after the rule change |
| After generating a new test reel | Compare against the closest reference reel by topic/style |
| After a failed QA round or weak review | Identify which benchmark dimensions the failure maps to |
| Before promoting a taste pattern into creative-feedback.json | Confirm the pattern produces higher benchmark scores when applied |
| Every ~5 completed reels | Spot check — is quality trending up, down, or flat? |

---

## Connecting Benchmark Findings to the Feedback Loop

Benchmark findings are inputs, not conclusions. They must flow somewhere:

1. **Immediately:** record in `projects/<slug>/output/review-feedback.md` with the dimension score and observation.

2. **If the same weakness appears in 2+ reel benchmarks:** run `feedback-capture` to propose promoting it to `memory/creative-feedback.json`. Weak proof cadence appearing in 3 reels is a signal that a rule is missing or underspecified, not that 3 individual projects went wrong.

3. **If a liked reference reel demonstrates the missing pattern:** annotate the reference reel's training example with the principle (`README-feedback-annotation.md` has the workflow), then run `python training/derive_style_pack.py --only taste-rules` to promote it into `training/derived/taste-rules.json`.

4. **If a system rule is confirmed to be working** (a dimension scores 4–5 consistently across multiple reels): note it in a feedback memory as a validated rule — not to change it, but to resist future drift or "simplification" that would remove it.

The benchmark is the beginning of the feedback loop, not the end. A score without a next action is not useful.

---

## Benchmark Cadence — Keeping It Lightweight

A full benchmark should take under 15 minutes for a reviewer who has watched the reel. The goal is a score per dimension plus 1–2 sentences of observation, not an essay. The review template in `projects/_shared/benchmark-review-template.md` provides a fill-in format designed for this pace.

Rules for keeping it fast:
- Score each dimension in one pass — do not re-watch the whole reel for each dimension
- Write one sentence per dimension: what was strong, what was weak
- Flag the single worst dimension explicitly — that is the action item
- Do not score dimensions that genuinely don't apply (use N/A freely)
- The benchmark is not a comprehensive editorial review — it is a calibration tool

If a benchmark review is taking more than 20 minutes, the format is getting too heavy. Cut dimensions or consolidate.
