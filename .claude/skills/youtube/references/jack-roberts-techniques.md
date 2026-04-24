# Jack Roberts Techniques (Adapted for Mits)

Jack Roberts is a YouTuber Mits admires. These are the specific techniques from his channel that we're adopting, adapted for Mits's voice and audience.

## 1. The translation layer

Never assume the viewer understands technical terminology. When introducing a technical term, immediately define it simply using a plain-English explanation or a relatable analogy.

### Translation pattern

Technical term [comma] plain-English definition [full stop]. Analogy if the concept is abstract.

### Examples of good translation

- **RAG** → "a fancy word for AI memory. Think of it as a librarian who fetches the exact paragraph you need instead of making you read the whole book."
- **API** → "the way different apps talk to each other. Think of it as the hands an AI uses to reach into another service."
- **MCP** → "Model Context Protocol. It's basically the standard way for agents to connect to outside tools like Notion or Slack."
- **OAuth** → "a secure way to connect two apps without sharing your password."
- **Vault** → "a secure locker where your passwords and API keys get stored, so the agent can use them without ever actually seeing them."
- **Session** → "one complete run of your agent from start to finish, with everything it did logged."

### Apply this rule to any technical term

The rule is: define it in plain English the first time it appears, using a metaphor if the concept is abstract. If Mits wouldn't use the term naturally in conversation, don't use it at all. Replace it with a description of what the thing actually does.

### Preferred metaphor styles for Mits

Use metaphors that are:
- **Business-focused**: hiring a digital employee, having a virtual assistant, a team member who works 24/7
- **Everyday life-based**: a librarian, an assistant, a personal organiser, a filing cabinet
- **Sports or fitness-based**: warming up, training, drills, match day

Avoid:
- Sci-fi or superhero references ("Iron Man suit")
- Overly dramatic comparisons
- Anything that feels too clever

## 2. On-screen mechanics

The three phases of every demo section.

### Phase A: Setup (before the action)

Before typing a single line of code or prompt, explain what you're about to do and why it matters for a business. Never just start clicking.

Template:
"What we're about to do is [specific action]. This matters because [business reason]. Watch what happens."

### Phase B: Void-filler (during the action)

AI takes time. Never leave dead air. Fill the loading time with one of these:

**Explain the why**
"While this loads, here's what's actually happening behind the scenes. The system is [technical detail, translated]..."

**Contrast with the old way**
"Normally, you'd have to [old approach with specific steps]. That used to take days of engineering work. Now it's happening automatically."

**Drop a quick hack**
"Little tip by the way. If you [keyboard shortcut or setting], you can [save time or avoid a common mistake]."

**Build community connection**
"If you're finding this useful, subscribe. I break down AI tools every week for people actually building things."

**Bridge to the next concept**
"While that runs, let me tell you what comes next. After this, we'll [next step]."

### Phase C: Review (after the action)

Once the AI finishes, immediately review the output on screen. Two reactions in sequence:

1. **Positive reaction**: "How good is that." / "Check this out." / "That's amazing."
2. **Critical review**: "Let me just check what it actually did here. [Point out one thing that works well, one thing to watch out for]."

This dual reaction (enthusiasm + critical eye) builds trust. It shows the viewer you're not just a cheerleader for the tool.

## 3. Dictating prompts aloud

Read prompts aloud exactly as you type or dictate them. Start conversationally, like you're talking to a person.

### Prompt style examples

Bad (too formal):
"Please analyse the attached sales script and generate tasks in ClickUp."

Good (conversational, Mits's voice):
"Hey, I'd like you to read through this sales script. Find any tasks embedded in the text, like follow-ups or contract prep. Then create those tasks in ClickUp with sensible deadlines. Check this out, let me run it."

This proves to viewers that they don't need complex prompt engineering to get results.

## 4. Embracing mistakes

Leave errors in videos. Do not edit them out. When something fails:

1. Read the error aloud, calmly. "Ah, we've got an error here. It says [error message]."
2. Show the exact prompt used to ask the AI to fix it. "Let me just ask it to sort this out."
3. Walk through the troubleshooting process on camera.

This demystifies the process. It shows the viewer what to actually do when things break in their own setup. It builds trust by showing the messy reality rather than a polished fake demo.

## 5. Visualising the output

Don't just show the code or config. Always run it and show the final result. Prove that the simple prompts actually work.

- If you built an agent, run the agent.
- If you created tasks, open ClickUp and show them.
- If you sent an email, open the inbox.
- If you configured a platform, show the live dashboard.

## 6. Structuring for digestion

Break tutorials into numbered, logical steps. Use simple frameworks where possible. Give viewers a roadmap at the start.

Examples of roadmap language:
- "Today we're doing three things. One, [X]. Two, [Y]. Three, [Z]. Let's go straight in."
- "Here's the simple 4-step flow. [List the four steps]. That's it."

Simple numbered structures make the video feel digestible and give viewers a mental checkpoint throughout.

## 7. The "done-for-you" approach

Remove friction for viewers. Pre-build complex assets and give them away free in the video description.

For every video, provide in the description:
- Exact prompts used (copy-paste ready)
- Template files (YAML, JSON, Markdown, etc.)
- URL links to all tools and platforms mentioned
- Any custom configs or skills built during the video

When introducing a free resource on camera:
"I've done all the work for you. All you need to do is grab [the thing]. Link in the description, you can just copy and paste it."

## 8. Business value anchor

Never explain a tool just for the technology. Tie every technical demonstration to a real-world, high-ROI business outcome.

### Real examples to use for Mits's channel

- "This agent can do the work of a £40k salary employee for less than £50 a month."
- "These are deliverables clients pay thousands of pounds for."
- "For a physio clinic, this means reactivating past clients while you're asleep."
- "For a med spa, this means never missing a follow-up again."
- "For a local service business, this replaces hiring an admin assistant."

### Anchor rule

Every tool demo should include at least one business value anchor. Use Mits's actual client base where possible: physiotherapy clinics, medical spas, wellness businesses, local service businesses.

## 9. Hook construction

Jack's hook formula (adapted for Mits):

1. **The big promise**, a massive opportunity and a common mistake.
   - "Managed agents are one of the most powerful tools you can use right now, but most people aren't using them yet, or they're using them wrong."

2. **The credibility anchor** (when used), kept to one sentence.
   - "My name is Mits. I run a GHL agency helping wellness businesses scale, and I test AI tools on real business problems every week."

3. **The transition**, "Let's go straight in."

Remember: credibility anchor is used occasionally, not every video. When the video doesn't directly connect to business automation, skip it and go straight from hook to intro.

## 10. Visual pacing tactics

- **Split screen where possible**: Keep context visible (file tree, interface) while focusing on the active area.
- **Dictation over typing**: Speaking is 4x faster than typing. If Mits has a dictation tool, use it for long prompts to keep momentum high.
- **Command visual flair**: When building anything visual, ask the AI for "delightful" elements (animations, confetti, smooth transitions) to prove the code works in a fun, visual way.
- **Avoid black terminal**: Prefer IDEs or platforms with visual interfaces. A visual environment keeps viewers engaged longer than a bare terminal.
