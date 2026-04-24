# Parallel Agent Playbook

When to use a single subagent, when to use agent teams, and how to run both safely in this repo.

---

## The Core Distinction

| Pattern | What it is | When it applies |
|---|---|---|
| **Subagent** | One specialist reads files and returns a structured finding | Diagnosis, auditing, analysis — one domain, one answer |
| **Agent team** | Multiple agents work in parallel on independent subtasks, results merged before any edits land | Large changes where parallel investigation genuinely saves time and the subtasks do not overlap |

**Default to subagents.** Agent teams add coordination overhead and file-collision risk. They are warranted only when the task is genuinely parallel and the cost of serializing it is real.

---

## When to Use Subagents

Invoke a single specialist subagent for any of the following. These tasks have clear inputs, bounded scope, and return structured findings — no parallelism needed.

| Task | Agent | Invoke at |
|---|---|---|
| **Asset audit** | `asset-auditor` | Phase 4d — before assembly begins |
| **QA review** | `qa-runner` | Phase 6 — after timeline is assembled |
| **Timeline critique** | `timeline-critic` | Phase 5 or after any timeline edit |
| **Render risk review** | `render-doctor` | After `tsc --noEmit` fails or render crashes |
| **Data analysis** | `data-analyst` | Any time — read-only SQL against analytics.db |
| **Memory promotion review** | `memory-curator` | After any review round before promoting to global memory |

These agents are **read-only and single-invocation**. They return findings; they do not edit files or set gates. See `.claude/agents/` for each agent's full specification and `docs/AGENT_ROLES.md` for the decision tree.

---

## When to Use Agent Teams

Agent teams are appropriate only when **all four conditions hold**:

1. The task has genuinely independent subtasks (no shared files, no sequential dependencies)
2. Serializing the subtasks would meaningfully slow the work (each subtask >10 min estimated)
3. The scope is investigative or architectural — not direct file editing
4. A plan has been reviewed and approved before any agent touches a file

**Do not enable agent teams by default.** Spinning up teammates for tasks that a single focused session would handle faster is overhead, not leverage.

### Warranted use cases

| Scenario | Why teams help |
|---|---|
| **Large architecture change** | Separate agents can own separate layers (lib/, remotion/, skills/) and their findings merged before edits begin |
| **Cross-layer refactor** | When a refactor touches Python lib, TypeScript components, and skill SKILL.md files simultaneously, independent review of each layer catches cross-layer regressions |
| **Competing diagnosis hypotheses** | Two agents independently diagnose the same failure — they cannot bias each other's findings. Agreement = high confidence. Divergence = the real signal |
| **Parallel code review before major merge** | Multiple reviewers catch different classes of issues faster than one sequential pass |

---

## Agent Team Rules

These are non-negotiable constraints for all agent team sessions.

### 1. Maximum 3 teammates (default)

The default cap is **3 agents running in parallel**. Increase beyond 3 only when the task has more than 3 genuinely independent subtasks — meaning each subtask touches completely non-overlapping files and produces a self-contained output.

When in doubt, use 2. Coordination cost scales with team size; findings quality rarely does.

### 2. Plan approval before any agent edits files

Agent teams are for **investigation first**. The flow is always:

```
Define subtasks → Assign owners → Run in parallel (read-only) → Merge findings → Review plan → Edit files
```

No agent edits a file until:
- All investigative agents have reported back
- The findings have been merged into a single coherent plan
- The plan has been reviewed and approved (by Mits for human gates, by brain diagnosis for auto gates)

### 3. No two agents edit the same file

Before the editing phase begins, list every file each agent will modify. If any file appears on two lists, one agent takes full ownership of that file and the other defers. Enforce this before starting — not after a collision.

### 4. Agents are not enabled by default

Agent team mode requires explicit invocation. A normal session with subagents does not become a team automatically. State clearly in the task prompt that you are forming a team and name each agent's scope.

---

## Example Prompts

### Example 1 — Parallel code review with 3 teammates

Use before merging a large assembly change that touches the Remotion composition, the timeline schema, and the QA gates simultaneously.

```
Form a 3-agent review team. Run all three in parallel. Each reviews only their assigned scope.
Do not edit any files. Return findings only.

Teammate A — Remotion composition review:
  Read remotion/src/ReelComposition.tsx and remotion/src/Root.tsx.
  Check: TypeScript correctness (run tsc --noEmit), lane ordering matches timeline.json
  lanes, avatar hideRanges cover all center-full entries, no two center-full entries
  overlap in time. Return a structured PASS/FAIL per check with file:line citations.

Teammate B — Timeline schema review:
  Read projects/<slug>/output/timeline.json and lib/schemas/timeline.schema.json.
  Check: all required fields present, beat_id references resolve against beat-map.json,
  durationInFrames values are positive integers, caption coverage ≥60% of total duration,
  no gap >9 frames without coverage. Return PASS/FAIL per check with beat_id citations.

Teammate C — QA gate review:
  Read projects/<slug>/project.json.
  Run: PYTHONPATH=. python -m lib.brain diagnose projects/<slug> --json
  Check: gates_passed count matches expected phase, no validation_errors, healthy=true,
  staleness_results with confidence=high. Return a gate status table and list any
  high-confidence staleness signals by artifact name.

After all three report back: merge findings into a single READY / NOT READY verdict
with a prioritized fix list before proceeding to render.
```

---

### Example 2 — Brain architecture refactor with separate owners

Use when refactoring `lib/brain/` in a way that changes the `Diagnosis` schema, the staleness checker, and the autonomy engine — three independent modules.

```
This refactor changes three independent modules in lib/brain/. Assign separate owners.
Do not edit files yet — investigation phase only.

Owner A — Diagnosis schema changes (lib/brain/diagnosis.py, lib/brain/__init__.py):
  Read the current Diagnosis dataclass and all callers (grep for 'Diagnosis(' across lib/).
  Identify: which fields are being renamed or added, which callers will break,
  what the migration surface is. Return a caller inventory with impact per change.

Owner B — Staleness checker changes (lib/brain/staleness.py):
  Read staleness.py and the current staleness_results schema in Diagnosis.
  Identify: which staleness rules are changing, what the new confidence thresholds are,
  whether the output structure is backwards-compatible with hooks that parse staleness_results.
  Read .claude/hooks/brain-status.sh and reinject-after-compact.sh — do they parse
  staleness fields directly? Return a compatibility report.

Owner C — Autonomy engine changes (lib/brain/autonomy.py):
  Read autonomy.py and the autonomy block structure (can_continue_autonomously,
  human_required, next_action). Read .claude/skills/autonomous-reel/SKILL.md Step 2
  decision tree — it branches on these fields. Identify whether the field names or
  semantics are changing and what SKILL.md Step 2 would need to be updated to match.
  Return a field-level compatibility table.

After all three report: produce a single unified migration plan with ordered steps.
Owner assignment for the editing phase: A owns diagnosis.py + __init__.py, B owns
staleness.py, C owns autonomy.py. No file is touched by more than one owner.
Plan requires approval before any editing begins.
```

---

### Example 3 — Debugging render failure with competing hypotheses

Use when a render crash has multiple plausible root causes and you want independent diagnosis to avoid confirmation bias.

```
A render failure needs diagnosis. Run two independent agents — they must not see each
other's reasoning. Competing hypotheses prevent bias. Compare conclusions after both report.

Hypothesis Agent 1 — encoding / asset hypothesis:
  Assume the failure is caused by a bad asset. Do not read the TypeScript source first.
  Run: PYTHONPATH=. python -m lib.preflight_render projects/<slug>
  Run ffprobe on every video in remotion/public/ — check codec (must be h264),
  pix_fmt (must be yuv420p), r_frame_rate (must be 30/1), audio stream presence.
  Check for filenames with spaces. Check for zero-byte or corrupted files.
  Return: ROOT_CAUSE_FOUND with specific file + ffprobe output, or RULED_OUT
  with evidence that all assets are clean.

Hypothesis Agent 2 — TypeScript / composition hypothesis:
  Assume the failure is caused by a code error. Do not check assets first.
  Run: cd remotion && npx tsc --noEmit 2>&1
  Run: PYTHONPATH=. python -m lib.compile_fix --prompt
  Read remotion/src/ReelComposition.tsx — check for exitDur:0 in any Sequence
  (crashes interpolate), check for OffthreadVideo without muted prop, check for
  missing premountFor on long sequences.
  Return: ROOT_CAUSE_FOUND with file:line + error text, or RULED_OUT with tsc output.

After both report: if both found a root cause — fix both (they are independent bugs).
If only one found a root cause — apply that fix and re-run the other agent to confirm.
If neither found a root cause — escalate to render-doctor for deeper diagnosis.
```

---

## Decision Flowchart

```
Task arrives
    │
    ▼
Is this a single-domain diagnostic task?
(audit / QA / critique / analysis / memory review)
    │
    ├── YES → Use the matching specialist subagent from AGENT_ROLES.md
    │
    └── NO → Is this a large change with genuinely independent subtasks?
                │
                ├── NO → Single focused session (no team needed)
                │
                └── YES → Do the subtasks touch different files?
                              │
                              ├── NO → Serialize them (sequential subagents)
                              │
                              └── YES → Agent team (max 3)
                                            │
                                            ├── Investigation phase first (read-only)
                                            ├── Merge findings → get plan approval
                                            └── Editing phase with single-file ownership
```

---

## What Agent Teams Are Not

- **Not a speed hack for small tasks.** Forming a team for a 20-minute task costs more in coordination than it saves.
- **Not a way to skip plan review.** Teams investigate; Mits (or brain diagnosis) approves; then files are edited.
- **Not autonomous by default.** Each agent in a team reports findings — they do not chain into each other's outputs without a merge step.
- **Not a substitute for the existing specialist agents.** If `qa-runner` or `timeline-critic` covers the scope, use them directly — do not wrap them in a team structure.
