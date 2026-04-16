# Feedback Annotation Guide

How to add a `taste_annotation` block to a training example so it contributes to `taste-rules.json`.

---

## Why Annotate

The structural data in a training example (templates, timing, caption suppression) tells the pipeline *what* a reference reel did. Taste annotation tells it *why it worked*. Without the why, the pipeline learns to copy the pattern without understanding when to apply it.

`taste-rules.json` is only as good as the annotations that feed it. A well-annotated example produces generalizable principles. A structural-only example produces nothing for taste.

---

## Reference-Only vs System-Worthy — The Critical Distinction

Not every reference reel should become a planning default. Some reels are worth studying because they inspire a mood, demonstrate a principle, or show what a certain style looks like in practice — but they should not become templates that Claude applies by default.

| Role | What it means | `reference_strength` | Contributes to |
|---|---|---|---|
| **System-worthy** | Patterns from this reel are broadly applicable — they transfer to other products, audiences, and topics without modification | `"strong"` | All positive pattern lists + anti-patterns |
| **Inspiration-only** | The reel demonstrates something interesting but is too product-specific, too niche, or too dependent on creator personality to generalize | `"unrated"` | Anti-patterns only (once annotated) |
| **Anti-pattern reference** | Included specifically because it shows what NOT to do | `"weak"` | Anti-patterns only |

**The derivation logic enforces this automatically.** `derive_taste_rules()` only pulls `hook_patterns`, `proof_patterns`, `body_patterns`, `motion_patterns`, `caption_patterns`, and `creative_principles` from examples with `reference_strength == "strong"`. Examples marked `"weak"` or `"unrated"` contribute only to `anti_patterns`.

### How to decide: strong vs unrated vs weak

**Mark `reference_strength: "strong"` when:**
- The patterns work because of something structural (proof escalation, caption suppression, rhythm) — not because of the creator's charisma or the product's novelty
- You can imagine the same pattern working on a completely different product
- You would want to apply this approach on the next reel regardless of topic

**Mark `reference_strength: "unrated"` (default) when:**
- You're not sure yet — you haven't watched it carefully enough to judge
- The approach seemed to work but you can't articulate why
- The reel is interesting but you can't separate creator personality from structural pattern

**Mark `reference_strength: "weak"` when:**
- The reel is included specifically for contrast: "don't do this"
- The approach clearly didn't work (low retention signals, poor engagement pattern)
- The patterns are so product-specific or creator-specific they cannot transfer
- You want to document failure modes, not success patterns

### Why this matters for the pipeline

If every reference reel becomes a positive pattern source regardless of quality, the taste rules will average out to the mean of what you've watched — which is not the same as the best of what you've watched. `reference_strength` is the filter that preserves signal quality as the training set grows.

One strong, deeply-annotated example is more valuable than five unrated, lightly-processed ones.

---

## When You Have Enough to Annotate

You can annotate any reference reel that you:

1. **Watched fully** — not just extracted frames from
2. **Reacted to positively** — you noticed something working, not just that it was "well-made"
3. **Can explain why** — not just "it felt premium" but what *mechanism* created that feeling

If you watched a reel and can't say what made it hold attention, mark `reference_strength: "unrated"` and come back later.

---

## What Each Field Means

### `annotation_source`

Who produced this annotation:
- `"human"` — you wrote this yourself, watching the reel
- `"machine-draft"` — Claude drafted it from structural data (needs human review before it can be trusted)
- `"mixed"` — you edited a machine draft

### `annotation_completeness`

- `"complete"` — all fields present and specific. The annotation has real insight in every field.
- `"partial"` — `why_it_works` and at least some patterns are present. Missing a few fields.
- `"minimal"` — stub only. Doesn't yet contribute meaningfully to taste derivation.

Only `complete` and `partial` annotations are used by `derive_taste_rules()`.

---

## The Most Important Field: `why_it_works`

This is the single most valuable field. One or two sentences explaining the **mechanism** — not what the reel did, but what psychological or attention effect it created and why.

**Bad (describes what happened):**
> "The reel opens with a news hook and then shows screenshots and then ends with a CTA."

**Bad (generic praise):**
> "The editing was tight and the proof felt convincing."

**Good (identifies the mechanism):**
> "The reel creates a forward pull by treating each proof type as the answer to the question raised by the previous one — existence proof creates 'how much?', breadth creates 'how does it work?', and so on. The viewer is never ahead of the narration."

**Good (identifies a specific tension):**
> "The hook uses brand recognition (Claude) as an interrupt — anyone who knows Claude will stop because the claim contradicts their existing model of it. The logo confirms this is real, not speculation."

The test: if you swapped the product name, would the principle still apply to a different reel? If yes, it's a generalizable mechanism and worth capturing.

---

## `hook_strength_reason`

What specifically made the first 2-3 seconds effective. Reference the exact element:

- "The logo appeared before the narration, which confirmed this was official before the claim landed"
- "The scrolling icon grid created immediate context — the viewer recognized multiple tools at once"
- "The news-event framing ('just launched') created urgency before any product feature was shown"

Do NOT write: "The hook was strong and grabbed attention immediately."

---

## `body_variation_reason`

How the body achieved variety without feeling chaotic. Name the specific dimensions that varied:

- Shot families (split vs full vs hidden avatar)
- Component types (card carousel vs proof screenshot vs avatar-overlay)
- Proof methods (static screenshot → demo video → scrolling document)
- Rhythm (fast card sequence → slow fullscreen warm → mid-pace avatar return)

Do NOT write: "There was good variety in the visuals."

---

## `repeatable_patterns` — How to Write Them

This is the most actionable field. Write patterns as **transferable instructions**, not as observations about this specific reel.

**Format:** "When X, do Y" or "For Z content, approach W works because..."

**Bad (observation about this reel):**
> "The reel used a card carousel to show multiple plugins at once"

**Good (transferable instruction):**
> "When proving breadth (many items), use card-carousel rather than sequential screenshots. Cards create a visual metaphor for quantity — the viewer feels the scale, not just hears it."

**Bad (too generic):**
> "Use real product UI instead of stock footage"

**Good (specific trigger):**
> "When naming a brand in the hook, show the brand's actual UI at that exact moment — not a logo card or generic product image. The UI is more credible than the brand identity."

Each pattern should be something you could hand to a different editor for a different reel and they would know exactly what to do.

---

## `avoid_patterns` — How to Write Them

Same format — transferable instructions. Write what the reel specifically did NOT do, and why that choice was correct.

**Bad:**
> "The reel didn't use too many transitions"

**Good:**
> "Avoid adding Ken Burns drift to proof screenshots. Movement shifts the key stat out of frame while the narrator is reading it — the viewer can't track both."

**Bad:**
> "The reel avoided using b-roll as proof"

**Good:**
> "Don't substitute cinematic b-roll for a missing proof screenshot. If the narrator says 'it built a full marketing plan', the visual must show the plan — not abstract footage of a person typing."

---

## `creative_takeaways` — Principles vs Recipes

This field is for editorial principles that apply beyond this specific format.

The difference:
- **Recipe** (don't put here): "Open with a news hook, show card carousel, use warm beige for output proof"
- **Principle** (put here): "Proof escalation is a narrative arc that keeps the viewer asking the next question. Each proof type should feel like it answers the question raised by the previous one."

Ask: if someone read this takeaway without knowing the reel, would they learn something that would make their next edit better? If yes, write it. If it only makes sense with the specific reel in context, it's a recipe, not a principle.

---

## Reference Strength — When to Mark Strong

Set `reference_strength: "strong"` only when:

1. You watched the full reel and it **held your attention** throughout
2. The patterns feel **repeatable** — not just right for this one product or moment
3. You can **name specific mechanisms** in the annotation, not just say it worked

Set `reference_strength: "weak"` when:
- The reel has anti-patterns you want to document
- It's included for contrast, not as a positive model
- Some sections work well but others don't
- You want to document what NOT to do

Set `reference_strength: "unrated"` until you've watched it carefully enough to annotate it.

**Important:** Weak examples still have value — they teach what to avoid. But `derive_taste_rules()` will only pull `repeatable_patterns` from them (marked as anti-patterns), not `creative_takeaways`.

---

## Annotation Status Workflow

1. `not-started` — `preprocess-reel.py` hasn't been run yet. No frames exist.
2. `skeleton-only` — Structural data exists (templates, timing) but `taste_annotation` is empty.
3. `needs-annotation` — Structural data is complete, but `taste_annotation` hasn't been filled.
4. `annotated` — `taste_annotation` is complete and `annotation_completeness` is set.

Update `annotation_status` in `training-index.json` when you change the status.

---

## Minimum Viable Annotation

If you're short on time, fill these three fields and mark `annotation_completeness: "partial"`:

1. `why_it_works` — one to two sentences on the mechanism
2. `repeatable_patterns` — three to five transferable instructions
3. `avoid_patterns` — two to three things this reel deliberately did NOT do

This is enough for `derive_taste_rules()` to produce meaningful output at LOW confidence.

---

## How to Avoid Machine-Draft Problems

If Claude drafted this annotation from structural data, it can only see what happened, not why it worked. Before marking `annotation_source: "mixed"`, verify:

- Every `why_it_works` sentence identifies a mechanism, not just an action
- Every `repeatable_pattern` starts with "When" or "For" — not "The reel did..."
- At least one `creative_takeaway` is a principle that would apply to a completely different product category

If all three pass, the draft is trustworthy enough to mark as mixed. If any fail, rewrite those fields.

---

## Running Derivation After Annotation

After updating one or more `taste_annotation` blocks:

```bash
python training/derive_style_pack.py --only taste-rules
```

Check the output for:
- `_confidence` level — target `medium` or `high` for taste rules to influence planning
- `_sparse_data_warning` — present if fewer than 3 annotated examples
- Pattern counts per category — if any category is 0, the annotations didn't classify into it

Re-run the full derivation before a major planning phase if you've added new annotations:

```bash
python training/derive_style_pack.py
```
