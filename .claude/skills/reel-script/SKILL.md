---
name: reel-script
description: Write retention-first, ElevenLabs-ready Instagram Reel scripts from a brief, topic, or approved source research, optimized for proof-led editing and avatar-led delivery.
---

# Reel Script Skill

Produce a single ElevenLabs-ready script block for an Instagram Reel avatar voiceover.

The output must be a **markdown document** that is easy to copy and paste.  
The spoken script must read naturally when spoken aloud and cut cleanly into a high-retention reel.

This skill is not just for writing.  
It is for writing scripts that support:
- hook reveals
- proof packets
- split-screen presenter moments
- trust beats
- recap flashes
- earned CTAs

---

## Primary Goal

Write a script that is:

- spoken naturally
- immediately clear
- proof-led
- easy to cut visually
- high-retention
- CTA-aligned
- ready for ElevenLabs
- formatted as a markdown document for easy copy/paste

The reel should feel like:
- a person showing something useful
- not a brand explainer
- not a feature list
- not a generic AI ad

---

## When to Trigger

Use this skill when:
- the user asks to write or rewrite a reel script
- a topic, hook, brief, or source research is ready
- the user wants an avatar script
- the user wants an ElevenLabs-ready voiceover
- the user wants an existing script improved for retention

Do NOT use this skill for:
- URL analysis
- source research
- asset capture
- video assembly
- QA

Those belong to other phases.

---

## Preconditions

At least one of the following must exist:
- approved `brief.md`
- approved `source-research.md`
- user-supplied topic with enough context
- existing script that needs rewriting

If a `brief.md` exists, use it as the main constraint set.

---

## Outputs

| File | Contents |
|---|---|
| `projects/<slug>/script.md` | Final markdown document containing metadata, ElevenLabs-ready script block, and timing reference |

The output must always be delivered as a **markdown document** that the user can copy and paste directly.

The metadata header should include:
- hook category
- style
- engagement trigger
- estimated duration
- CTA angle
- proof promise
- whether trust beat is required

---

## Core Writing Principle

Write for the edit.

That means the script must help the editor clearly identify:
- what the hook shows
- where proof lands
- what the outcome is
- when the avatar should anchor
- where the trust beat belongs
- what should be recapped before the CTA

A good script should make the visual structure obvious.

---

## Relationship to the Reel System

This script must support the retention-first pipeline used by:
- `capture-demo`
- `assemble-reel`
- `qa-reel`

So the script should naturally create:
- early proof
- short clear beat units
- visible outcomes
- proof packets
- trust language where needed
- specific CTA payoff

If the script cannot be cut into a compelling reel, it is not finished.

---

## Script Production Workflow

Follow these steps in order.

### Step 1 — Read the Brief or Topic

If `brief.md` exists, read it first.

Use the brief’s guidance for:
- strongest hook direction
- support points
- CTA angle
- recommended style
- demo concept
- required capture notes

Do not re-derive the whole concept unless the brief is clearly weak.

If the user provides a topic directly:
- identify the single clearest promise
- identify the single clearest proof
- decide whether trust / control / safety matters
- choose a style that fits short-form retention

---

## Step 1b — Verify Product Claims

Before writing, verify that the product features described in the brief or topic actually exist and work the way the script will claim.

This is not optional. Scripts that sound confident but describe features incorrectly lose credibility on camera and in comments.

### What to verify

1. **Feature names and hierarchy** — does the product use the exact terms the script will use? If the product calls something a "plugin" that bundles "skills" and "connectors," the script must not treat plugins, skills, and connectors as three parallel features at the same level. Understand how concepts nest before structuring the script around them.

2. **Integration and app names** — if the script names specific apps (Gmail, Slack, Notion, Canva, Google Drive), verify which ones are officially supported. Do not name integrations that don't exist. Use the ones the product's own documentation explicitly references.

3. **Capability boundaries** — verify what the feature can and cannot do. If the product requires the app to be open, or only works on certain platforms, or has usage limits, note these. The script does not need to mention every limitation, but the writer must know them to avoid claims that are misleading.

4. **Terminology consistency** — if the product uses specific terms (e.g. "skills" not "workflows," "connectors" not "integrations"), the script should match. Mixing casual synonyms with official terms confuses the viewer and undermines trust.

### How to verify

- Search the product's official docs, help center, or support site
- Check the product's changelog or release notes if the feature is new
- If `source-research.md` exists and was produced by `source-brief`, use its verified claims
- If the user provided a URL, check that URL
- If no official source is available, flag unverified claims explicitly

### What to do with findings

- Adjust feature language to match verified terminology
- Remove or rephrase integrations/apps that are not officially supported
- Note any limitations that affect the trust beat or could invite correction in comments
- If a claim cannot be verified, mark it in the script metadata as a positioning line (see Claim Transparency below)

Do not let this step block scripting entirely. If some claims are unverifiable, write the script but flag them. The goal is awareness, not paralysis.

---

## Series Format Rule

If `project.json` contains a `"series"` field, this reel is part of a series.

Apply these rules:

1. The spoken opener must be the series title + part number.
2. Format: `"[Series title] -- Part [number]."`
3. Speak the number as a word, not a digit.
4. The hook must still land quickly after the series opener.

Example:
`Things you didn't know you could do with Claude--Part one`

The series opener should not delay the actual value too long.

---

## Demo-Specificity Rule

The script must reference the actual demo that will be shown.

Do not write vague tool language if the visuals are concrete.

### Required behavior
- name the actual subject if the demo is specific
- name the actual output if the output is specific
- name the tool clearly
- match what the viewer will literally see on screen

### Good
- `Say you want to learn human anatomy -- Claude builds a diagram that actually makes it make sense`
- `Drop in your receipt photos -- Claude builds the expense report for you`

### Bad
- `You can use this for basically anything`
- `The tool does stuff automatically`

Generic claims can appear later, but the primary proof lines must match the actual demo.

---

## Step 2 — Decide the Reel Promise

Before writing, define the reel’s main promise in one sentence.

### The promise must answer:
- what useful thing happens?
- why does it matter?
- what is surprising about it?

Examples:
- `Claude doesn't just answer -- it builds the actual deliverable`
- `This feature turns a messy manual task into a finished output`
- `Most people use the app like chat and miss the part that does real work`

This promise should shape:
- the hook
- the proof beats
- the CTA

---

## Step 3 — Select the Style

Choose the style based on what creates the strongest retention shape.

### Check the visual style first

Read `project.json` for the `style` field. The visual style affects scripting decisions:

| Visual style | Script impact |
|---|---|
| `cinematic-presenter` | Moderate word density (140-160 wpm), longer beats, setup-then-proof flow, trust beats more common |
| `editorial-authority` | High word density (160-190 wpm), shorter beats, claim-then-proof-then-cut flow, every sentence must be visually confirmable |

**If `editorial-authority`:**
- Write in micro-claims: one statement → one proof → next statement
- Every sentence should create an obvious hard-cut point
- Favor bold contradictions (“WRONG”, “stop paying”, “you don't need”)
- Write for giant text overlays — key emotional words should stand alone as title cards
- The script should alternate between talking-head lines and proof lines
- Duration target is shorter: 25-35 seconds preferred
- Lists are stronger than deep dives (use numbered framing: “Number one...”, “Number two...”)

**If `cinematic-presenter`:**
- Write in flowing proof packets: input → action → result → save
- Allow longer setup before proof
- Trust beats and mechanism beats have room to breathe
- Duration target: 30-50 seconds

### Preferred styles for most AI / workflow reels
1. Breakdown
2. Case Study
3. Problem & Solution
4. Listicle
5. Rapid Tutorial

### Use style based on content behavior
- use **Breakdown** when explaining why a feature matters
- use **Case Study** when the result is the hook
- use **Problem & Solution** when the viewer has a clear frustration
- use **Listicle** only when multiple distinct points genuinely exist — **strongly preferred for editorial-authority style**
- use **Rapid Tutorial** for quick “do this” use cases

Do not force a listicle when the reel is really about one powerful workflow.

---

## Step 4 — Select the Hook

The hook should deliver:
- identity
- tension or pain
- curiosity
- early value

But it must also be easy to support visually.

### Hook rules
- the viewer should understand the claim quickly
- the hook should strongly imply proof
- avoid hypey mystery hooks with no payoff
- avoid hooks that require too much setup before visuals can support them
- the hook should cut cleanly with the first demo reveal
- **every hook promise must be paid off in the body** — if the hook makes a comparison ("makes X feel like a search bar"), the script must explicitly explain why within the next 5–8 seconds. If the hook makes a bold claim, the first proof packet must directly support it. A hook that sets up an expectation the body never addresses is worse than a weaker hook that the body delivers on

### Hook construction formula

A strong hook has up to three ingredients in one sentence:

1. **Big brand or anchor** — name the company or product ("Google", "Claude", "OpenAI")
2. **Unexpected contrast or surprise** — the thing that makes them think "wait, how?"
3. **Everyday payoff** — what it means for the viewer personally

Not every hook needs all three, but the best ones combine at least two.

### Hook word order: benefit-first, contrast-second

The everyday payoff should come BEFORE the surprising contrast. The benefit is what the viewer can immediately picture. The contrast is what makes them stay.

**Benefit-first (stronger):**
`Google just dropped an AI model you can run on your phone--and it competes with models twenty times bigger`

**Contrast-first (weaker on first listen):**
`Google just dropped an AI model that competes with models twenty times bigger--and you can run it on your phone`

The benefit-first version works because "run it on your phone" is instantly graspable. The contrast "twenty times bigger" then creates the curiosity gap: *wait, how is that possible?*

### Hook word economy

Every word in the hook must earn its place. Conversational phrasing beats grammatically precise phrasing in spoken delivery.

| Tighter (use this) | Looser (avoid) |
|---|---|
| "twenty times bigger" | "twenty times its size" |
| "runs on your phone" | "is capable of running on your mobile device" |
| "just dropped" | "just released" or "has announced" |
| "and somehow" | "and what's interesting is that it" |

If a hook sentence has more than ~18 words, it's probably trying to do too much. Split it or trim.

### Preferred hook types
- direct problem / payoff
- comparison
- myth correction
- result-first statement
- viewer callout tied to a real use case
- **benefit + contrast combo** — everyday payoff paired with unexpected capability

### Strong examples
- `Google just dropped an AI model you can run on your phone--and it competes with models twenty times bigger`
- `I typed one sentence--and Claude built the whole presentation`
- `Most people use Claude like chat--this is the part that actually does the work`
- `If you're still turning receipts into reports by hand--watch this`
- `This free tool just replaced three apps I was paying for`

### Weak examples
- `You won't BELIEVE this hidden feature`
- `This AI trick is insane`
- `Nobody is ready for this`
- `Google just released an AI model that beats ones twenty times its size and you can run it on your phone` (too long, contrast-first, "its size" is stiff)

### Hook self-test

After writing a hook, ask:
1. Can a viewer picture the benefit in under 1 second?
2. Does the contrast create a "wait, how?" reaction?
3. Is it under 18 words?
4. Does it sound like something a person would actually say?
5. Read it aloud once — if you stumble, it's too long or too stiff

---

## Step 5 — Build the Retention Structure

Use this default beat logic unless the style clearly requires another flow.

### Retention-first 7-part structure
1. **Hook** — claim + curiosity + visible value
2. **Fast setup** — what the feature/tool is
3. **Proof packet 1** — first real use case
4. **Proof packet 2 / mechanism** — why it works or second proof
5. **Trust beat** — control, approval, safety, or reassurance if relevant
6. **Recap / reframe** — what the viewer should now understand
7. **CTA** — specific ask tied to value

### Important
Do not let the script become:
- hook
- long explanation
- generic CTA

The middle must contain visible payoffs.

### Argument Sequence Check

The beat structure defines *what goes where*. The argument sequence defines *whether the ideas build on each other*.

A script can have all 7 beats in the right order and still fail if the idea progression is flat. Check the argument sequence before writing.

**Strong sequences:**
- hook → contrast → proof → concrete examples → recap
- hook → problem → mechanism → result → reframe
- hook → claim → evidence → second evidence → payoff

**Weak sequences:**
- hook → feature list → more features → recap
- hook → explanation → explanation → CTA
- hook → abstract concept → abstract concept → abstract concept → CTA

The difference: strong sequences **build an argument**. Each beat raises the stakes or adds evidence. Weak sequences **list information** — the viewer learns facts but never feels momentum.

### How to check

After outlining the beats, read only the first line of each beat aloud in order. Ask:
1. Does each beat raise the stakes or add evidence? Or does it just add another item?
2. If beat 3 was removed, would the script still make sense? If yes, beat 3 is probably filler.
3. Does the final beat feel earned by everything before it? Or could it follow any script?

If the sequence is flat, restructure before writing the full script.

### Pillar balance rule

When a script has multiple support points (e.g. three features, three use cases), each pillar must receive roughly equal development. If one pillar gets setup + explanation + example, and another gets a single noun, the reel will feel lopsided.

Each pillar needs at minimum:
- one concrete example or visible action (not just a name)
- enough spoken time for the viewer to form a mental image

If a pillar cannot support a concrete example, it is either too abstract for a reel or should be folded into another pillar.

---

## Step 6 — Write in Proof Packets

This is a major rule.

Whenever the script describes a workflow, write it in mini-payoffs that can each be cut visually.

### Preferred proof packet structure
- input
- action
- result
- save/output
- reframe

Not every packet needs all five parts, but the script should give the editor clear moments.

### Example
Weak:
`It can read files and make reports for you automatically`

Strong:
`Drop in your receipt photos -- Claude reads them -- builds the expense report -- and saves the Excel file for you`

That creates obvious cut points:
- drop in files
- reads them
- builds report
- saves file

That is what we want.

---

## Step 7 — Value Before Explanation

Always state the value first.

### Rule
Benefit first.  
Mechanism second.

### Bad
`This feature has access to files on your computer so it can help with tasks`

### Better
`It can build the actual file for you -- Cowork has access to the files on your computer so it can do the task instead of just describing it`

The viewer should feel the payoff before the explanation expands it.

---

## Step 7b — Kill Vague Payoff Lines

Every payoff line must create a mental image. If the viewer cannot picture what happens next, the line is too vague.

### The test
Read the payoff line and ask: can I see this happening? If the answer is "sort of" or "conceptually," rewrite it.

### Bad (vague)
- `so the work goes somewhere useful`
- `so you can do more with it`
- `so it actually helps`

### Good (visual and concrete)
- `so the work goes straight into the tools you already use`
- `so Claude drops the draft right into your Gmail`
- `so the report lands in Notion before your morning coffee`

The stronger version always names where the result ends up or what physically changes. Abstract payoffs ("somewhere useful", "helps you work better") don't stick in a 30-second avatar reel.

---

## Step 7c — Defeat Catalog Energy

Listing features at the same energy level creates "product tour" pacing — the #1 middle-section retention killer in avatar reels.

### The problem
`It can do content creation, SEO audits, campaign plans, and competitive analysis`

That is a catalog. Every item lands at the same weight. The viewer zones out by item 3.

### Three fixes

**1. Escalation words** — use "even" or "or even" to make later items feel like a reveal:
- `Claude can run a full workflow like content creation--SEO audits--or even campaign planning`

The word "even" tells the viewer each item is bigger than the last. Without it, they are just a list.

**2. One sharp example** — pick the single most concrete example and make the viewer feel it:
- `say you need an SEO audit--type slash--pick the command--done`

One vivid example proves more than three named features.

**3. Contrast framing** — set up what the viewer expects, then break it:
- `instead of just getting ideas--Claude runs a full workflow`

The "instead of" creates a before/after in one sentence.

### When listing is acceptable
When each item is a tool name the viewer already knows (Gmail, Notion, Slack) — these are recognition anchors, not features. The viewer doesn't need to understand them, just recognize them. But even tool lists benefit from escalation: `Gmail--Notion--Slack--or even Canva`.

---

## Step 7d — Discovery Over Onboarding

Avatar scripts must feel like the viewer is discovering something, not being taught how to use it.

### The difference
- **Onboarding:** "Step one, go to settings. Step two, click connectors. Step three, browse the list."
- **Discovery:** "Then connect it to Gmail, Notion, Slack — so the work goes straight into the tools you already use."

Onboarding scripts describe *how to navigate*. Discovery scripts describe *what changes for the viewer*.

### Rules
- Do not describe UI navigation steps unless the step IS the proof (e.g. "type slash--pick the command--done")
- Frame features as things the viewer gets, not things they must configure
- Use "you get" and "it can" more than "go to" and "click on"
- The viewer should feel lucky to have found this, not instructed to set it up

### When onboarding language is acceptable
Only when the navigation step itself is surprisingly simple and that simplicity is the payoff:
- `click Cowork--add a plugin--done` (the ease IS the point)

---

## Step 7e — Audience-Aware Language (Jargon Translation)

Technical claims must be translated for the target audience. A benchmark number means nothing if the viewer cannot picture why it matters to them.

### The rule

**Every technical claim must answer: "what does this mean for me?"**

If the audience is developers, technical language is fine. If the audience is general or AI-curious, every stat, benchmark, and technical term must be rewritten as a benefit the viewer can feel.

### Translation patterns

| Technical (developer audience) | Translated (general audience) |
|---|---|
| "31 billion parameter version ranks #3 on Arena AI" | "competes with models twenty times its size" |
| "86.4% on t2-bench agentic tool use" | "thirteen times better at doing tasks for you" |
| "Apache 2.0 license" | "fully open source--anyone can use it--build on it--own it" |
| "MoE with 3.8B active parameters" | "only uses a fraction of its power at a time so it runs fast" |
| "128K context window" | "it can read entire documents in one go" |
| "native function-calling and structured JSON output" | "it can actually use tools and apps on its own" |

### Structure: accessibility before stats

For general audiences, lead with **what it means for you** before proving it with numbers:

**Bad order (stats-first):**
`Ranks number three in the world--four times better at math--thirteen times better at tool use--and it runs on your phone`

**Good order (meaning-first):**
`You don't need massive servers for powerful AI anymore--laptop--phone--even a Raspberry Pi--and it's not watered down either--thirteen times better at doing tasks for you`

The meaning-first order tells the viewer why to care, then proves it's real. The stats-first order asks the viewer to trust numbers they can't evaluate.

### Defeat the assumption before the proof

When a product is smaller, cheaper, free, or open-source, viewers assume it's weaker. Name and defeat this assumption before delivering the stats:

- "And it's not a watered down version either--" (defeats "small = weak")
- "This isn't the free tier--" (defeats "open source = inferior")
- "Even though it's a fraction of the size--" (defeats "bigger = better")

Without the defeat line, the stats land on skeptical ground.

### Credibility calibration

Choose claim strength based on audience trust level:

| Audience | Claim style | Example |
|---|---|---|
| Developer | Precise, bold | "beats models 20x its size" |
| AI-curious general | Confident but hedged | "competes with models twenty times its size" |
| Skeptical / new to AI | Understated, let proof speak | "performs as well as models much bigger than it" |

"Competes with" is safer than "beats" for general audiences — it's still impressive but doesn't invite "well actually" comments.

### One hero stat, group the rest

For general audiences, three or more stats in a row is benchmark overload. The viewer can absorb one impressive number. After that, they zone out.

**Bad (stat overload):**
`it's thirteen times better at doing tasks--four times better at math--and nearly three times better at code`

**Good (one hero + grouped rest):**
`it's thirteen times better at handling real tasks for you--with big improvements in maths and coding too`

Rules:
- Pick the single most impressive stat as the hero number
- Group the remaining stats into a general claim ("big improvements in X and Y")
- The hero stat should be the one that best answers "why should I care?"
- For developers, you can keep 2-3 specific stats. For general audiences, one is the maximum

### Safer claim language

General audiences trust understated confidence more than bold assertions. Overselling invites skepticism and "well actually" comments.

| Bolder (developer audience) | Safer (general audience) |
|---|---|
| "beats models 20x its size" | "competes with models twenty times bigger" |
| "own what you create" | "customize it freely" |
| "crushes the competition" | "outperforms much bigger models" |
| "400 million downloads and counting" | "over four hundred million downloads already" |
| "best open model in the world" | "one of the most powerful open models available" |

**"And counting"** sounds hype-driven. **"Already"** sounds earned.
**"Beats"** invites debate. **"Competes with"** is still impressive but defensible.
**"Own"** oversimplifies licensing. **"Customize freely"** is accurate and still strong.

### When to keep technical language

- When the technical term IS the product name (Gemma 4, Apache 2.0, Ollama)
- When the audience already knows the term (developers know "context window")
- When the term is the proof (benchmark names matter to developers)
- When simplifying would be misleading

### Checklist

Before finalizing a script for a general audience:
- [ ] No benchmark names (Arena AI, MMLU, t2-bench) unless the audience knows them
- [ ] No parameter counts unless framed as a comparison ("a fraction of the size")
- [ ] Every stat is followed by or preceded by what it means for the viewer
- [ ] Technical terms are either translated or are recognizable product names
- [ ] The script leads with meaning/benefit, not with numbers
- [ ] Assumptions about "smaller/free = weaker" are defeated before stats land

---

## Step 8 — Use Avatar-Friendly Spoken Language

The script must sound like a human creator speaking directly.

### Use
- short spoken chunks
- direct phrasing
- concrete nouns
- spoken rhythm
- real observations
- simple phrasing with sharp verbs
- one clear thought per beat

### Avoid
- corporate wording
- startup pitch language
- vague abstraction
- overexplaining
- stacked clauses
- filler transitions before strong lines
- written-grammar phrasing that sounds unnatural in TTS

### Good voice style
- `And here's what I like most`
- `What makes this different is this`
- `Most people miss this part`
- `That’s the bit that matters`

### Avoid
- `Leverage this capability to optimize`
- `This revolutionizes productivity`
- `Allow me to show you`

---

## Step 9 — Trust Beat Rule

If the workflow implies autonomy, access, sensitive actions, or approval, include a trust beat.

This matters especially for:
- file access
- computer actions
- sending or saving things
- permissions
- anything that might make the viewer wonder if the tool acts without them

### Trust beat goals
- remove fear
- show the user stays in control
- make the feature feel safe, not reckless

### Good trust lines
- `Whenever it hits something sensitive -- it asks before taking action`
- `It doesn't just do random things in the background -- you approve the step first`
- `You stay in control the whole time`

Do not skip this if it is one of the product’s strongest objections to solve.

---

## Step 10 — Reframe Before the CTA

Before the ask, help the viewer understand why the feature matters.

Examples:
- `Most people downloading Claude don't even know this part exists`
- `That’s the difference between chat and actual workflow help`
- `This is why using it like a chatbot misses the point`

This gives the CTA more weight.

---

## Step 11 — Write the CTA to Match the Reel

The CTA should fit the actual value delivered.

### CTA rules
- be specific
- reference the type of payoff shown
- avoid a generic “follow for more tips” unless the reel is broad
- prefer workflows, use cases, hidden features, or missed capabilities if those are the true value

### Better CTA examples
- `Follow for more Claude workflows people miss`
- `Follow for more AI tools that actually do the work`
- `Follow if you want the useful part -- not just the hype`

### Weaker CTA examples
- `Follow for more tips`
- `Comment YES`
- `Don’t forget to like and subscribe`

If a comment CTA is used, it should still feel native and specific.

---

## ElevenLabs Script Rules

These rules are mandatory.

Write for **speech**, not written grammar.

### Core Rules
- default to **one paragraph**
- avoid full stops unless a **hard stop** is intentionally needed
- use `--` as the default pause marker for softer, more natural pacing — written with **no spaces** either side (e.g. `word--word`, not `word -- word`)
- minimize commas because they often cause exaggerated pauses and overacted delivery
- keep ideas in short spoken chunks with one clear thought per beat
- prefer conversational phrasing over formal sentence structure
- maintain forward momentum so the script rolls from one idea to the next without constant vocal resets
- use capitalization sparingly for emphasis
- use simple transitions and repeated phrasing patterns to stabilize rhythm
- always proof spacing carefully because merged words or missing spaces can hurt TTS pronunciation
- optimize every line for how it sounds aloud, not how it looks on the page

### Default Rhythm Preference
Prefer:
- short phrases
- flowing thought chains
- clean spoken pivots
- natural continuation

Avoid:
- frequent full-stop resets
- comma-heavy phrasing
- formal sentence balance
- visually elegant writing that sounds stiff aloud

### Spoken Example
Better:
`I typed one sentence--Claude built the whole presentation--then it planned the structure--built the slides--and asked before doing anything sensitive`

Worse:
`I typed one sentence, and Claude built the whole presentation. Then it planned the structure, built the slides, and asked before doing anything sensitive.`

---

## Spoken Formatting Rules

These control ElevenLabs output and delivery flow.

### Single-Block Format
No line breaks inside the script body.  
The spoken script must be one continuous paragraph.

### Default Pause Marker
Use `--` as the default pause marker. Write it with **no spaces** either side — `word--word` not `word -- word`. Spaces around `--` create unnatural gaps in ElevenLabs delivery.

### Full Stops
Avoid full stops unless a hard stop is intentionally needed for emphasis or separation.

### Commas
Minimize commas.  
Only use them when clarity truly requires them.

### Semantic Punching
Capitalise only the most emotionally important words.  
Max 3–4 per script.

### Phonetic Spelling
Use phonetic alternatives if needed for pronunciation.

### Spacing
Proof every line carefully for spacing errors that could harm TTS pronunciation.

### No Filler Transitions Before Strong Statements
Do not weaken strong lines with unnecessary setup words.

Bad:
`Look -- unlike regular chat -- Cowork has access to your files`

Better:
`Unlike regular chat -- Cowork has access to your files`

---

## Transition Phrase Rules

Transition phrases should help flow, not create clutter.

### Rules
- never repeat the same transition within one script unless repeated phrasing is intentionally used for rhythm
- avoid repeating recent transitions across consecutive scripts
- use fewer transitions in high-density scripts
- do not insert transitions where the phrase already works without one
- prefer simple spoken pivots over formal connectors

### Best use cases
- contrast
- reveal
- reframe
- pivot to proof
- pivot to trust
- pivot to CTA

---

## Engagement Trigger Rule

At least one engagement trigger must be included.

Choose the one that best fits the reel:
- identity
- opinion
- status
- FOMO
- save
- comment

But do not force a trigger if it damages clarity.

### Best practice
Use the engagement trigger as part of the message, not as an obvious gimmick.

Better:
`Most people downloading Claude don't even open this feature`

Weaker:
`Comment WOW if you agree`

---

## Duration and Density Rules

### Target duration
- 15–40 seconds allowed
- 25–35 seconds preferred for most proof-led reels

### Density rules
- value should start early
- do not let setup drag
- keep the middle moving
- leave enough space for proof moments to breathe
- if a line forces too many visuals into too little time, rewrite it

A strong script gives the edit room to land proof.

---

## Editorial Writing Rules

These are non-negotiable.

### Rule 1
Write what can actually be shown.

### Rule 2
Do not promise proof the visuals cannot support.

### Rule 3
If the reel claims a result, mention the result explicitly.

### Rule 4
If the reel claims an output, mention the output explicitly.

### Rule 5
If the reel solves an objection, say so clearly.

### Rule 6
If a beat can be split visually, write it in a way that makes the split obvious.

### Rule 7
Write in a way that sounds strong out loud even if it looks less formal on the page.

---

## Metadata Requirements

The output header should include:
- hook category
- style
- engagement trigger
- estimated duration
- CTA angle
- proof promise
- trust beat required: yes/no

Optional:
- best demo subject
- strongest proof packet
- best recap line

---

## Quality Gate

Run every script through these checks before delivering.

### Must-pass
- [ ] Hook lands quickly
- [ ] Hook can be supported visually
- [ ] Hook promise is explicitly paid off in the body (not just implied)
- [ ] Value is stated before explanation
- [ ] Script references actual demo content
- [ ] Script contains visible proof moments
- [ ] Middle includes at least one clear proof packet
- [ ] Argument sequence builds momentum (not a flat feature list)
- [ ] Each support pillar has at least one concrete example
- [ ] Product feature names match verified official terminology
- [ ] Named integrations/apps are officially supported by the product
- [ ] Trust beat is present when relevant
- [ ] Known limitations are not contradicted by script claims
- [ ] CTA matches the actual reel value
- [ ] Script sounds conversational
- [ ] Script is one continuous paragraph
- [ ] Script follows ElevenLabs speech rules
- [ ] No corporate or hype language
- [ ] No filler transitions before strong lines
- [ ] Feature names land cleanly
- [ ] Script gives the editor obvious beat points
- [ ] Reframe exists before CTA when needed
- [ ] Spacing is proofread carefully
- [ ] No vague payoff lines — every payoff creates a mental image
- [ ] No catalog energy — feature lists use escalation words or contrast framing
- [ ] Script feels like discovery, not onboarding — describes what changes, not how to navigate

### Red flags requiring revision
- hook is interesting but visually vague
- hook makes a comparison or bold claim that the body never addresses
- setup is longer than the payoff
- script sounds like an explainer instead of a reel
- idea progression is flat — beats add information but don't build an argument
- one support pillar is developed with examples while another is just a noun
- proof is implied but not named
- no save/output/result language where that is the claim
- feature terms don't match the product's official naming
- script names an integration/app the product doesn't officially support
- CTA is generic relative to the reel
- trust concern exists but is not addressed
- script contradicts a known product limitation
- too many clauses for natural avatar delivery
- punctuation is too formal for TTS delivery
- comma use is causing overacted pacing
- new product terms introduced mid-script without setup (viewer has to decode)
- payoff line is abstract or vague ("somewhere useful", "helps you work better", "do more with it") — must be visual and concrete
- middle section lists 3+ features at the same energy level without escalation words or contrast — catalog energy kills retention
- script reads like a product walkthrough or onboarding guide — must feel like discovery
- feature list has no "even" or "instead of" or contrast — items land at flat equal weight

---

## Output Format

Deliver `script.md` with this structure:

```markdown
# Script: [Project Slug]

**Hook category:** [e.g., Result-first]  
**Style:** [e.g., Breakdown]  
**Visual style:** [cinematic-presenter / editorial-authority]  
**Engagement trigger:** [e.g., FOMO]  
**Estimated duration:** [e.g., 29s]  
**CTA angle:** [e.g., Hidden workflows]  
**Proof promise:** [e.g., Claude builds the finished deliverable, not just the answer]  
**Trust beat required:** [Yes / No]

---

## ElevenLabs Script

[Single-paragraph script text -- no line breaks inside the script body -- copy-paste ready.]

---

## Timing Reference

(00:00–00:03) [Hook]  
(00:03–00:06) [Setup]  
(00:06–00:12) [Proof packet 1]  
(00:12–00:19) [Proof packet 2 / mechanism]  
(00:19–00:24) [Trust beat]  
(00:24–00:28) [Reframe]  
(00:28–00:32) [CTA]


The ElevenLabs Script block must be directly usable without cleanup.
The entire output must be a markdown document that the user can copy and paste.

## Claim Transparency

After the timing reference, include a short section that separates verified claims from creative positioning. This helps the user make an informed decision about risk before recording.

```markdown
## Claim Check

### Verified (from official docs/sources)
- [Feature X does Y — source: product help center]
- [Integrations: A, B, C are officially listed]

### Creative positioning (not from official sources)
- [Comparison line "makes X feel like Y" — editorial choice, not a product claim]
- [Phrasing "the actual deliverable" — simplification of what the feature produces]

### Known limitations
- [Feature only works when app is open]
- [Integration Z is not officially listed — replaced with verified alternative]
```

This section is for the user's reference only. It does not appear in the ElevenLabs script block.

The goal is not to weaken the script. It is to make sure the user knows which lines are product truth and which are creative framing, so they can decide what level of boldness they are comfortable with before recording.

Example Output Logic

A good script should read like this structurally:

strong hook
fast orientation
first visible proof
second visible proof or explanation
trust reassurance
reframe
CTA tied to the exact payoff

It should never read like:

hook
feature explanation
more explanation
generic CTA
Relationship to Other Skills
source-brief

Runs first and defines the concept.

capture-demo

Uses this script to know what proof moments must be captured.

assemble-reel

Uses this script to map beats, presenter moments, proof packets, trust beat, and CTA.

qa-reel

Uses this script as part of checking whether the reel actually delivered the promised proof and structure.

This means the script must be clear enough to drive all later stages.

Stop Condition

Deliver the completed script.md markdown document and present it for approval.

Do not proceed to audio generation, demo capture, timeline assembly, or QA until the script is approved.
