---
description: Post-assembly change classification and re-entry pipeline
globs: ["remotion/**", "**/timeline.json", "**/assembly-notes.md"]
---

# Change Pipeline

When changes are requested AFTER assembly (Phase 5) is complete, do NOT edit the composition directly. Follow this pipeline to avoid cascading errors.

## Step 1 — Classify the change

| Change type | Re-entry phase | What to update |
|---|---|---|
| **New visual asset** (logo, b-roll, screenshot) | 4b-i (visual assignment) | Shot list → component mapping → technical planning → motion intent → assembly |
| **Overlay/text change** (position, size, color) | 5 (assembly) | Read component source → update composition → verify |
| **Asset swap** (different clip for same beat) | 4d (asset prep) | Encode → update timeline clipStartTime → verify |
| **Timing change** (beat boundaries) | 3 (beat map) | Beat map → captions → shot list → motion intent → assembly |
| **Script change** | 2b (reconcile) | Full pipeline restart from reconciliation |
| **Layout change** (split-screen sizing, avatar position) | 5 (assembly) | Read AvatarVideo.tsx + target component source → update composition → verify |

## Step 2 — Invoke required skills BEFORE writing code

Every change that touches Remotion code requires:

1. **Invoke `remotion-best-practices`** — load the relevant rule files for the change category
2. **Read the target component's source file** — understand its props, positioning, z-index, and internal styling
3. **Read `AvatarVideo.tsx`** if the change affects split-screen layout — confirm boundary percentages

This is not optional. Mid-session changes require the same skill invocation as initial assembly. Loading skills earlier in the session does not count — load them again before each code change.

## Step 3 — Read before writing

Before modifying how a component is used in `ReelComposition.tsx`:

1. **Read the component's `.tsx` file** — note its props interface
2. **Note its internal positioning** — how does it position itself? What CSS does it use?
3. **Note its z-index** — where does it sit in the stacking order?
4. **Note its container sizing** — does it constrain its own height/width, or does the parent?
5. **Cross-reference with AvatarVideo** — if this is split-screen content, does the container height match the avatar's boundary?
6. **THEN write the JSX**

### Critical measurements to verify before split-screen changes

Read `AvatarVideo.tsx` and note:
- Split-screen avatar: `bottom: 0, height: "60%"` — avatar occupies bottom 60%
- Content must fill top 40% — container height must be `"40%"` to meet the avatar boundary
- Any mismatch creates a visible white gap between content and avatar

## Step 4 — Choose your edit mode

Before writing any code, choose the edit mode based on how much of the file is changing:

| Change scope | Mode | Tool |
|---|---|---|
| **< 30% of file** — fix one constant, rename one prop, reposition one element | **Targeted** | `Edit` with `old_string` / `new_string` |
| **> 50% of file** — major feature addition, full component rewrite, large refactor | **Full replacement** | `Write` with complete new file content |
| **30–50%** | Choose based on which is safer — default to targeted | Either |

**Targeted edit rules:**
- `old_string` must be unique in the file — add surrounding context to disambiguate if needed
- Change ONLY what was asked — no reformatting, no restructuring adjacent code
- Verify the edit did not shift indentation or affect adjacent blocks

**Full replacement rules:**
- Read the current file first — never overwrite without understanding the existing code
- Preserve all existing prop interfaces (no silent prop removals)
- All constants, imports, and exports must be carried forward

## Step 5 — Verify after every change

After implementing a change:

1. **Compile check** — `cd remotion && npx tsc --noEmit`
   - If errors → run `python -m lib.compile_fix --prompt` for a formatted fix prompt with line context
   - Fix errors before rendering — never render with TypeScript errors
2. **Render the affected frames** — extract stills at the exact timestamps where the change applies
3. **Inspect visually** — don't just check "did it compile" — look at the actual rendered frame
4. **Compare against what the user asked for** — re-read the user's request and verify the output matches their words, not your interpretation

### Error correction loop

When `tsc --noEmit` fails:

```bash
# Get a formatted fix prompt with file:line context for every error
python -m lib.compile_fix --prompt
```

The output includes:
- File path and line number for each error
- Surrounding code context with an arrow at the error line  
- Reminder of reserved names that must never be shadowed
- Ready-to-use prompt format

Paste the output as your next message to get targeted fixes. After applying fixes, re-run `python -m lib.compile_fix` to verify clean compilation.

## Rule: Never remove what the user asks to fix

- If the user says "centre this" → centre it. Do not delete it.
- If the user says "make this bigger" → make it bigger. Do not replace it with something different.
- If the user says "move this" → move it. Do not remove it and add something new.

Fix what exists. Do not take the path of least resistance by removing the element.

## Rule: One change at a time, verified

When multiple changes are requested:
1. Implement the first change
2. Render and verify it works
3. Implement the next change
4. Render and verify

Do not batch multiple visual changes and hope they all work. Each change affects layout, z-index, and positioning — they interact.

## Common mid-pipeline mistakes to avoid

| Mistake | Why it happens | What to do instead |
|---|---|---|
| Guessing container height | Not reading AvatarVideo.tsx | Read the component, note the boundary |
| Wrong component props | Not reading the component source | Read the `.tsx` file, check the interface |
| Content covering avatar face | Not understanding z-index stacking | Read both components' z-index values |
| White gap between content and avatar | Container height doesn't match avatar boundary | Container = 40%, Avatar = bottom 60% |
| Double rendering (ghost images) | Layering static + video at same position | Use one approach, not both |
| Removing user's requested element | Taking path of least resistance | Fix the element, don't delete it |
