# Input Quality Guide: Starting a Reel

How the quality of your starting input cascades through the entire pipeline — and what to include at each tier.

The first thing you give the system — a URL, a topic, a brief — determines the ceiling for every phase downstream. A weak input doesn't just produce a weak brief. It produces a weak script, which produces a generic hook, which produces low retention, which produces a reel nobody watches.

---

## The Cascade Effect

```
INPUT QUALITY → Brief → Script → Audio → Beat Map → Captions → Shot List → Motion → Assembly → QA → Render
     ↓            ↓        ↓        ↓         ↓          ↓          ↓          ↓         ↓        ↓       ↓
  Excellent    Focused   Sharp    Clean    Precise    Punchy     Clear      Tight     Fast     Pass   Great reel
  Great        Clear     Solid    Clean    Good       Good       Workable   Good      1 round  Pass   Good reel
  Good         Broad     Okay     Clean    Decent     Fine       Gaps       Messy     2 rounds Pass*  Okay reel
  Bad          Vague     Generic  Clean    Loose      Flat       Blocked    Broken    Stalls   Fail   Re-scope
```

Audio quality stays "Clean" regardless — HeyGen/ElevenLabs always produces clean audio. The quality gap shows up in **what** is said, not **how** it sounds. A perfectly voiced generic script is still a generic reel.

---

## The Four Tiers

---

### EXCELLENT Input

An excellent input gives the system everything it needs to make strong editorial decisions without guessing. Zero ambiguity about what the reel is about, who it's for, and what the viewer should see.

**What it includes:**

| Element | What it does | Example |
|---|---|---|
| **URL with visible proof** | Source-brief extracts claims, screenshots, and proof | Product launch blog, feature page with embedded demos |
| **Specific angle** | Locks the hook direction — no "pick from 3 options" round-trip | "Focus on the fact that it's free and builds websites from one prompt" |
| **Named audience** | Script speaks to a real person, not "everyone" | "For people who pay for Figma or Canva" |
| **Duration target** | Constrains scope — prevents feature-stuffing | "30-35 seconds" |
| **Style choice** | Determines pacing, transitions, visual language upfront | "editorial-authority, fast cuts" |
| **Scope boundaries** | Prevents coverage creep — what NOT to include | "Don't cover voice commands, MCP, or the design agent" |
| **Hook direction** | The first 3 seconds are decided before scripting | "Start with the fact that it's free — that's the scroll stopper" |
| **Proof method per claim** | Each claim maps to a specific visual proof | Table: "Multi-screen gen → screen recording; Code export → panel screenshot" |

**Real example — google-stitch (rendered cleanly):**
```
URL: https://blog.google/innovation-and-ai/models-and-research/google-labs/stitch-ai-ui-design/

"Make a reel about Google Stitch — it's a free AI design tool that builds
websites from a single prompt.

Focus on the speed and the fact that it's free.
Target audience: people who pay for Figma/Canva.
Style: editorial-authority. 30-35s.

Don't cover voice commands, MCP, or design agent — keep scope tight.
The hook should lead with 'free' — that's the scroll-stopper.

3 support points:
1. Multi-screen generation (one prompt → 5 connected screens)
2. Real code export (React, Tailwind, Flutter, SwiftUI)
3. Completely free — 350 generations/month, no credit card

Trust beat: Google-backed, free tier is generous, exportable code.

If Figma's stock chart is available, use it as credibility proof."
```

**What the brief looked like downstream:**

The brief that came out of this input had:
- Hook direction locked: "Google just released a FREE tool that's killing Figma"
- Capture priorities ranked 1-4 with fallback plans
- "Script Notes" section with 7 specific constraints
- Zero ambiguity at any phase gate

**Downstream result:**
- Source-brief: extracted 8+ proof points, 5+ screenshots, 3 hook directions → user picked in 1 round
- Script: specific, proof-led, hook landed in first 2 seconds
- Shot-list: clear visual assignments, zero MISSING fitness scores
- Assembly: 1 round
- QA: passed structural checks (style compliance flagged minor items)

**Total revision rounds: 1-2 across the entire pipeline.**

---

### What makes Excellent different from everything else

The single biggest quality signal is **scope boundaries** — saying what NOT to cover.

Google Stitch brief said: "Don't cover voice commands, MCP, or design agent — keep scope tight."

That one sentence prevented:
- The script from trying to cover 6 features in 35 seconds
- Demo capture from recording 4 extra product screens
- Shot-list from having 12 beats instead of 8
- Assembly from being bloated and rushed
- QA from flagging "too much content, pacing feels rushed"

**Without scope boundaries, every phase expands by default.** The system will always try to include more because it has no signal to stop. "Don't cover X" is more valuable than "Do cover Y."

---

### GREAT Input

A great input has a clear topic and enough specificity for strong editorial direction, but may leave one or two decisions for the system to propose.

**What it includes:**

| Element | Present? | Notes |
|---|---|---|
| URL or specific topic | Yes | Clear what the reel is about |
| Specific angle | Yes | Clear which feature or claim to lead with |
| Audience | Sometimes | May be implied by topic |
| Duration | Sometimes | May default to 30-45s |
| Style | Sometimes | May default to cinematic-presenter |
| Scope boundaries | Partial | May not say what to skip |
| Hook direction | Implied | May not specify exact first 3 seconds |
| Proof method per claim | Partial | May list features without mapping each to a visual |

**What's missing vs. Excellent:**
- May not specify the exact hook angle (system proposes 2-3 options → 1 round-trip)
- May not have pre-recorded demo footage (capture-demo handles it — adds time)
- May not specify scope boundaries (system may try to cover too much → needs script revision)

**Real example — chatgpt-secret-codes (rendered, completed):**
```
"Make a reel about 4 ChatGPT hidden codes that most people don't know.
Source: Instagram reel by @mavgpt — transcript provided.
Listicle style, 35 seconds, editorial-authority.

The 4 codes:
| Code       | What it does                                    |
|------------|-------------------------------------------------|
| /human     | Humanizes output — sounds natural, not robotic   |
| X10 think  | Forces deeper reasoning before answering         |
| kill critic| Stops sycophancy — pushes back honestly          |
| alt 3      | Returns 3 distinct answer variations             |

CTA: Follow and comment LIST — I'll send you hundreds more codes."
```

**Why this is Great, not Excellent:**
- No explicit scope boundary ("Don't cover X")
- No capture priority ranking (all 4 codes treated equally — but should code 1 get more screen time?)
- No audience named (implied: "ChatGPT users who feel outputs are average" — but not stated)

**But the table structure carried it.** Each code mapped to a specific behavior = each code maps to a specific demo. The scriptwriter couldn't vaguely say "show the codes working." Each had its proof method baked into the table.

**Downstream result:**
- Brief: 1 round to confirm
- Script: specific because the listicle structure gave built-in beats
- Shot-list: some PARTIAL fitness (needed demo recordings of each code working)
- Assembly: 1-2 rounds
- QA: passed

**Total revision rounds: 2-3 across the pipeline.**

---

**Real example — claude-cowork (QA passed, completed):**
```
Feature: Claude Cowork mode
"Show that it works with actual files on your computer —
not just in the browser like ChatGPT.

Two demo flows:
1. Receipts → Excel expense report (show it reading files + saving output)
2. Creates a presentation from notes

Hook: show the finished output cold (expense report or presentation)
for 1-2 seconds before explaining.

Unlike browser chatbots, Cowork touches your actual files. That's the line that lands.
Tone: Impressed but grounded. 'Look what this actually does.'
40-50 seconds."
```

**Why this worked well:** The brief identified the DIFFERENTIATOR ("touches your actual files — that's the line that lands") and the PROOF METHOD ("show the finished output cold for 1-2 seconds before explaining"). The script could be written in one pass because the editorial strategy was decided at input time.

---

### GOOD Input

A good input has a real topic but lacks specificity. The system can work with it, but makes more assumptions and needs more approval rounds.

**What it includes:**

| Element | Present? | Notes |
|---|---|---|
| URL or topic | Yes | Something concrete exists |
| Specific angle | No | System must research and propose multiple angles |
| Audience | No | System guesses |
| Duration | No | Defaults to 30-45s |
| Style | No | Defaults to cinematic-presenter |
| Scope boundaries | No | System covers everything it finds |
| Hook direction | No | System proposes 3+ options |
| Proof method per claim | No | System must figure out what to capture |

**What it looks like:**

```
URL: https://developers.googleblog.com/en/how-its-made-little-language-lessons/
"Make a reel about this."
```

Or:

```
"Make a reel about Claude Code."
```

Or:

```
"I want to do something about this new Google tool, here's the link."
```

**What happens downstream — the real cost:**

| Phase | What goes wrong | Extra rounds |
|---|---|---|
| **Source-brief** | Finds 3-5 possible angles. Proposes all of them. User must pick. | +1 round-trip |
| **Brief** | Tries to cover everything it found. Too many support points. No scope limit. | +1 revision to narrow |
| **Script** | Hook is broad ("Google just launched an amazing new AI tool..."). Proof is scattered across 5 features. | +1 revision to tighten |
| **Demo capture** | Unclear what to capture. Multiple UI states needed. Which one matters most? | +2-3 capture decisions |
| **Shot-list** | Multiple MISSING fitness scores. Assets don't exist for half the beats. | +1-3 blockers to resolve |
| **Assembly** | Pacing feels rushed (too much in 30s) or flat (nothing lands hard enough). | +1-2 revision cycles |
| **QA** | Weak hook, low proof density, generic CTA. | May fail → revise → re-QA |

**Real example — google-little-language-lessons (reached render but with problems):**

The project rendered, but:
- No `brief.md` was ever created — the source-research document ends with "Claude — Action Required: produce a hook, 3 support points, CTA" but no user confirmation ever happened
- The three language experiments (Tiny Lesson, Slang Hang, Word Cam) were never prioritized — which one is the hook? Which is cut if time is tight?
- The project.json has minimal metadata

**The lesson:** A URL alone gives the system something to research, but it doesn't give it an OPINION. And opinion is what makes a reel specific.

**Real example — claude-cowork-basics (stalled, restart-pending):**

The brief tried to cover skills + connectors + plugins + scheduled tasks — 4 distinct features for ~25 seconds. That's 6 seconds per feature. The capture list had 6 checkboxes. No scope boundary said "focus on skills only, cut the rest."

Result: `"current_phase": "restart-pending"` — the project stalled because production couldn't fit everything in.

**Total revision rounds: 4-6 across the pipeline. May stall completely.**

---

### BAD Input

A bad input creates cascading problems that compound at every phase.

**What it looks like:**

```
"Make a reel about AI."
```

```
"Here's a cool article, turn it into a reel."
[link to a 3000-word think piece with no visuals, no product, no specific claim]
```

```
"Make a reel comparing all the AI tools."
[scope: 8 tools, 15 features, no audience, no angle]
```

```
"I want something about machine learning for my Instagram."
```

**Why it's bad — the specific failures:**

| Input problem | Phase that breaks | What happens |
|---|---|---|
| **No specific product** | Source-brief | Can't research a product page — finds opinions instead of proof |
| **No specific claim** | Script | No hook. "AI is changing everything" makes 80% of viewers scroll past |
| **No visible proof** | Shot-list | Every beat scores MISSING — nothing to show the viewer |
| **Scope too wide** | Script + Assembly | Tries to cover 8 things in 30 seconds — every feature gets 3.7 seconds. Nothing lands. |
| **No audience** | Script + CTA | CTA is "follow for more" — no conversion. Not speaking TO anyone. |
| **Think piece, not product** | Capture-demo | No UI to capture. Mock HTML can fake 1 product, not 8. |
| **"Make something"** | Brief | System must invent the entire creative direction. The reel reflects the system's taste, not yours. |

**The fundamental issue:** A bad input asks the system to be creative AND strategic AND editorial AND technical simultaneously. Each of those is a separate decision that should be locked BEFORE production begins.

**What happens downstream:**
- Source-brief returns "Weak / Not Reel-Ready" suitability score
- Brief requires 2-3 rounds of scope reduction
- Script is generic — hook doesn't stop the scroll
- Demo capture has no clear targets
- Shot-list is mostly MISSING
- Assembly can't start
- **The reel either stalls or gets re-scoped from scratch**

**Total cost: 5x+ the effort of an Excellent input, or a full restart.**

---

## The Multiplier Table

| Input quality | Brief rounds | Script rounds | Capture gaps | Shot-list blockers | Assembly rounds | QA result | Total effort |
|---|---|---|---|---|---|---|---|
| **Excellent** | 0-1 | 0-1 | 0 | 0 | 1 | Pass | 1x |
| **Great** | 1 | 1 | 0-2 | 0-1 | 1-2 | Pass | 1.5x |
| **Good** | 1-2 | 1-2 | 2-4 | 1-3 | 2-3 | Pass (2nd attempt) | 2.5-3x |
| **Bad** | 2-3+ | 2-3+ | 5+ | 3+ | Stalls | Fail → re-scope | 5x+ or restart |

---

## What to Include — The Complete Checklist

### The 8 Elements

Every starting input should try to include these. The more you provide, the less the system guesses, and the fewer approval rounds you need.

---

#### 1. Source (URL or Topic)

**What it is:** The thing the reel is about.

**Excellent:**
```
URL: https://blog.google/innovation-and-ai/models-and-research/google-labs/stitch-ai-ui-design/
```
A specific product page with visible demos, screenshots, and claims on the page.

**Great:**
```
"4 ChatGPT hidden codes that most people don't know: /human, X10 think, kill critic, alt 3"
```
A specific topic with defined scope even without a URL.

**Good:**
```
URL: https://developers.googleblog.com/en/how-its-made-little-language-lessons/
```
A real URL but no guidance on what to focus on.

**Bad:**
```
"Something about AI tools"
```
No product, no feature, no claim.

**The proof test:** Can you screenshot something from this source that proves a specific claim?
- Yes, multiple things → Excellent source
- Yes, one or two things → Great source
- Maybe → Good source
- No → Bad source (all text, opinions, no product UI)

---

#### 2. Angle

**What it is:** Which specific aspect of the product to focus on. Not "what it does" but "why it matters."

**Excellent:**
```
"Focus on the fact that it's free and builds websites from one prompt.
The angle is: this replaces Figma for most people."
```
One clear value proposition that immediately creates tension.

**Great:**
```
"Show that it can build working apps inside the conversation."
```
Clear enough to drive scripting, but doesn't name the tension or competitor.

**Good:**
```
(not provided — system infers from URL)
```
System proposes 3 angles. You pick one. Adds 1 round-trip.

**Bad:**
```
"Just cover what it does."
```
Feature-list energy. No editorial point of view.

**Why this matters:** The angle determines the HOOK. A reel without an angle gets a hook like "Check out this AI tool" — which has an 80%+ skip rate. A reel with an angle gets "If you're paying for design tools, you need to see this" — which creates immediate tension.

---

#### 3. Audience

**What it is:** Who specifically watches this reel and what pain point they have.

**Excellent:**
```
"For people who pay for Figma or Canva and feel like AI tools
should be cheaper or free by now."
```
Names a specific behavior (paying for design tools) AND a feeling (should be cheaper).

**Great:**
```
"Everyday ChatGPT users who feel like they're getting average outputs."
```
Names a group and a frustration.

**Good:**
```
(not provided — system infers "AI enthusiasts" or "tech-curious viewers")
```
Generic audience = generic CTA = no conversion.

**Bad:**
```
"Everyone" or "People interested in AI"
```
If your audience is everyone, your reel speaks to no one.

**Why this matters:** Audience determines:
- Script voice (technical vs. accessible)
- Proof framing (capability demo vs. "look how easy this is")
- CTA specificity ("Follow for more free AI tools" vs. "Follow for more")

---

#### 4. Duration

**What it is:** How long the reel should be.

**Excellent:** `"30-35 seconds"`
**Great:** `"Keep it under 40 seconds"`
**Good:** (not provided — defaults to 30-45s)
**Bad:** `"Make it comprehensive"` (= 90 seconds = nobody watches it)

**Why this matters:** Duration is a hard constraint on scope. A 30-second reel can cover:
- 1 main idea
- Up to 3 support points
- 1 CTA

If you don't set duration, the system tries to cover everything, and the reel feels rushed.

**Duration guidelines:**
| Duration | What fits | Best for |
|---|---|---|
| 20-25s | 1 claim + 1 proof + CTA | Single-feature reveals, "did you know" |
| 30-40s | 1 claim + 2-3 proofs + CTA | Standard feature demo, launch announcement |
| 40-55s | 1 claim + 3-4 proofs + trust beat + CTA | Deep feature demo, comparison, explainer |

---

#### 5. Style

**What it is:** The visual and editing language of the reel.

| Style | Feel | Best for |
|---|---|---|
| `cinematic-presenter` | Smooth, premium, avatar-led, split-screen | Feature demos, tutorials, product deep-dives |
| `editorial-authority` | Fast, punchy, hard cuts, proof-led, text cards | Listicles, comparisons, news, claim-and-prove |

**Excellent:** `"editorial-authority, fast cuts, Lindsay.ai energy"`
**Great:** `"editorial-authority"`
**Good:** (not provided — defaults to cinematic-presenter)
**Bad:** (doesn't affect the reel badly, but the wrong style for the content can weaken engagement)

**When to choose editorial-authority:**
- Listicles ("4 codes", "3 tools")
- Claim-and-prove ("This tool replaces Figma")
- News/comparison ("Google vs OpenAI")
- Fast pacing, hard cuts, text cards

**When to choose cinematic-presenter:**
- Feature walkthroughs ("Here's how Claude Cowork handles files")
- Product deep-dives (one tool, explored thoroughly)
- Trust-building (permission beats, safety moments)
- Smooth pacing, split-screen, avatar-anchored

---

#### 6. Scope Boundaries

**What it is:** What the reel should NOT cover.

This is the single most valuable thing you can add to any input. The system always expands scope unless told not to.

**Excellent:**
```
"Don't cover voice commands, MCP, or the design agent — keep scope tight.
Focus ONLY on: multi-screen generation, code export, and free pricing."
```

**Great:**
```
"Skip the history, go straight to features. Don't mention competitors."
```

**Good:**
```
(not provided — system covers everything it finds)
```

**Bad:**
```
"Cover everything" or "Be comprehensive"
```

**Real example of what happens without scope boundaries:**

Claude-cowork-basics brief tried to cover: skills, connectors, plugins, AND scheduled tasks. Four distinct features for 25 seconds. That's 6 seconds per feature. No feature got enough time to land. The project status: `restart-pending`.

If the input had said "Focus on skills and connectors only. Cut plugins and scheduled tasks." — the reel would have shipped.

---

#### 7. Hook Direction

**What it is:** What the first 1-3 seconds should say or show.

**Excellent:**
```
"Start with 'free' — that's the scroll-stopper.
Show the finished website in the first frame, then explain how it was made."
```
This is result-first + specific word + visual instruction.

**Great:**
```
"Lead with the result, not the setup."
```
Clear editorial direction but doesn't specify the exact word or visual.

**Good:**
```
(not provided — system proposes 3 hook options from research)
```
Adds 1 round-trip to select.

**Bad:**
```
"Start with an introduction to the tool."
```
Introductions kill retention. The hook must create tension or show a result. Never introduce.

**Hook patterns that work (from your completed reels):**

| Pattern | Example | Why it works |
|---|---|---|
| **Cost tension** | "If you're paying for design tools..." | Viewer immediately thinks "am I overpaying?" |
| **Secret knowledge** | "Here are 4 secret codes..." | Curiosity gap — viewer wants the list |
| **Result-first** | Show the finished expense report cold for 1-2 seconds | Proof before explanation — viewer wants to know how |
| **Number + outcome** | "6x less memory — and the stock market felt it" | Specific number + unexpected consequence |

**Hook patterns that fail:**

| Pattern | Example | Why it fails |
|---|---|---|
| **Introduction** | "Today I want to talk about..." | No reason to keep watching |
| **Definition** | "Stitch is an AI design tool by Google" | No tension, no curiosity |
| **Generic praise** | "This tool is amazing" | Everyone says this. Viewer scrolls. |
| **Question without stakes** | "Have you heard of Claude Code?" | If no → scroll. If yes → already know. |

---

#### 8. Proof Method Per Claim

**What it is:** For each claim the reel makes, what specific visual proves it.

**Excellent (table format):**
```
| Claim                    | Proof method                                    |
|--------------------------|-------------------------------------------------|
| Builds websites          | Screen recording of generation from prompt       |
| Exports real code        | Screenshot of code export panel (React, Flutter) |
| Free                     | Pricing page showing 350 gen/month, no card      |
| Figma replacement        | Figma stock chart drop (external credibility)    |
```

**Great (narrative format):**
```
"Show the expense report being built from receipts (screen recording).
Show the output Excel file saved to desktop."
```

**Good:**
```
"Show the tool working."
```
Vague — system must decide WHICH moment to capture and HOW to show it.

**Bad:**
```
(not provided — system guesses what to show based on script text)
```
Results in MISMATCH and MISSING scores at shot-list. Blocks assembly.

**Why this matters more than anything else:**

A reel about an AI tool making a website is worthless if the viewer never SEES the website being made. The proof method is the visual that makes the claim real. Without it:
- The narrator says "it builds websites" → the viewer sees the avatar talking
- The narrator says "it exports code" → the viewer sees a generic screenshot
- The narrator says "it's free" → the viewer sees nothing proving it

**Every claim without a mapped proof method becomes an avatar-only beat.** And avatar-only beats without visual support kill retention after 5 seconds.

---

## What NOT to Include

These actively hurt the pipeline:

### 1. "Be comprehensive"
Comprehensive = everything = nothing lands. A 30-second reel communicates ONE idea with up to 3 support points. "Be comprehensive" creates scope creep that stalls production.

### 2. "Cover all the features"
Same problem. Pick the 1-3 features that prove the angle. Skip the rest.

### 3. "Make it go viral"
Not actionable. Instead: "Hook with the result in the first frame. Use editorial-authority style. 30 seconds."

### 4. Conflicting instructions
"Keep it short but make sure to cover the history of the company AND all 6 features AND a comparison to 3 competitors." This is a 3-minute video crammed into 30 seconds. Pick one.

### 5. Other people's scripts verbatim
Adapting a competitor's structure is fine (chatgpt-secret-codes adapted from @mavgpt). Copying their script word-for-word is not — the reel-script skill writes ElevenLabs-optimized scripts with retention hooks that generic transcripts lack.

### 6. Vague emotional goals
"Make it exciting" or "Make it professional" — these aren't inputs, they're outcomes. Instead: "Editorial-authority style, hard cuts, 160+ wpm."

### 7. URLs to paywalled or login-required content
Source-brief can't read behind login walls. If the URL requires authentication, either:
- Copy the visible content into a document
- Provide screenshots
- Find a public version of the announcement

---

## The Input Checklist

Use this before starting any new reel. The more boxes you check, the faster the pipeline runs.

### Minimum viable input (enough to start)
- [ ] A URL to a product page, blog post, or launch announcement
- [ ] OR a specific topic with defined scope

### Good input (reduces 1-2 revision rounds)
- [ ] Everything above, plus:
- [ ] A specific angle or feature to focus on
- [ ] A target duration (e.g. "30-35 seconds")

### Great input (reduces 2-3 revision rounds)
- [ ] Everything above, plus:
- [ ] Named audience ("For people who...")
- [ ] Style preference (cinematic-presenter or editorial-authority)
- [ ] At least one scope boundary ("Don't cover X")

### Excellent input (minimal revisions, fastest pipeline)
- [ ] Everything above, plus:
- [ ] Hook direction ("Start with the result" or "Lead with 'free'")
- [ ] Proof method per claim (table or narrative mapping each claim to its visual proof)
- [ ] Capture priorities ranked (which demo matters most if time is limited)
- [ ] CTA direction ("Follow for more free AI tools" — specific to the reel's value)
- [ ] Any pre-recorded demo footage (MP4 files skips the entire capture phase)

---

## Quick Decision Tree

```
Do you have a URL to a product page with visible proof?
├── YES
│   ├── Can you state the ONE main claim in 10 words?
│   │   ├── YES → Add angle + audience + duration → EXCELLENT
│   │   └── NO → Add just the URL → GOOD (system will propose angles)
│   └── Does the page have screenshots/demos?
│       ├── YES → Capture phase will be fast
│       └── NO → Budget extra time for demo capture
├── NO, but I have a specific topic with defined features
│   ├── Can you list each feature + its proof method?
│   │   ├── YES → Provide the table → GREAT
│   │   └── NO → Provide the feature list → GOOD
│   └── Do you know who the audience is?
│       ├── YES → Add them → bumps quality up one tier
│       └── NO → System infers (may be generic)
├── NO, just a general topic
│   └── GOOD at best. Expect 2-3 extra scoping rounds.
│       → Try to narrow: "Which ONE feature?" "Who cares most?"
└── NO, just "make something about AI"
    └── BAD. Don't start yet. Pick:
        → One tool
        → One feature of that tool
        → One audience who needs it
        Then come back.
```

---

## Real Project Report Card

| Project | Input tier | What was provided | What was missing | Pipeline result |
|---|---|---|---|---|
| **google-stitch** | Excellent | URL + angle + audience + style + scope boundaries + hook + proof methods + capture priorities | Nothing material | QA phase, clean pipeline |
| **chatgpt-secret-codes** | Great | Topic + code table with proof methods + style + duration + CTA | Explicit audience, scope boundaries, capture priorities | Rendered, completed |
| **claude-cowork** | Great | Feature knowledge + 2 demo flows + differentiator + hook + tone | No URL (feature knowledge), no explicit scope boundary | QA passed, completed |
| **google-turboquant** | Great | URL + hard numbers + ranked proof moments + twist/payoff + scope limits | No demo recordings provided | Assembled, approaching QA |
| **google-little-language-lessons** | Good | URL only | Angle, audience, duration, style, scope, hook, proof methods, brief.md itself | Rendered but sparse metadata |
| **claude-cowork-basics** | Good→Bad | Topic + brief BUT scope creep (4 features for 25s) | Scope boundary, feature prioritization | Stalled: restart-pending |

---

## The Bottom Line

**The best input is a URL with visible proof + a specific angle + who it's for + what to skip.**

This sentence:

> "Make a 30-second editorial-authority reel about Google Stitch for people who pay for design tools. Focus on the fact that it builds websites from one prompt and it's free. Don't cover voice commands or the design agent."

...carries more value than any amount of downstream effort can compensate for.

The second most valuable thing you can provide is a **table mapping each claim to its visual proof.** That table becomes the shot-list backbone and prevents the most common pipeline stall: MISSING fitness scores at Phase 4b.

Everything downstream amplifies what you start with. Start specific.
