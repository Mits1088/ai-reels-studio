# Autonomy Policy

**Applies to:** `autonomous-reel` skill, any context where Claude advances the pipeline without per-step approval from Mits.

---

## What Autonomy Means Here

Autonomy is scoped, not unlimited. Claude may advance the pipeline through a defined set of AUTO_GATES without asking Mits. At every HUMAN_GATE, it stops unconditionally and waits for explicit approval. The gate system is the enforcement mechanism — not trust, not judgment, not context.

Autonomy does not mean "work until done." It means "work until the next decision that requires human taste or authority, then stop and surface it clearly."

---

## The Two Gate Classes

### AUTO_GATES — Claude executes without approval

These gates represent technical or deterministic work. The output is verifiable by code, not by taste.

| Gate | Who sets it | What it represents |
|---|---|---|
| `theme_set` | theme-factory | Brand colors committed to project.json |
| `reconciliation_resolved` | script-reconcile | Transcript-to-script delta resolved |
| `asset_fitness_passed` | shot-list 4b-ii | Zero MISMATCH/MISSING in fitness audit |
| `assets_validated` | asset-prep | Every asset encoded, present, and ffprobe-verified |
| `qa_passed` | lib.qa.runner | QA found no blockers |

Claude may run these skills and set these gates in a single autonomous run, up to 3 consecutive gates before reporting progress.

### HUMAN_GATES — Mits approves before continuing

These gates represent decisions that require human taste, editorial judgment, or authority sign-off. No amount of confidence in the diagnosis changes this.

| Gate | What Mits is approving |
|---|---|
| `brief_approved` | The topic, angle, hook direction, and scope |
| `script_approved` | The exact words that will be spoken |
| `visual_assignment_approved` | The creative/editorial visual plan per beat |
| `technical_planning_approved` | Zoom coordinates, SFX plan, background assignments |
| `motion_intent_reviewed` | The motion language and per-beat motion decisions |
| `preview_passed` | The assembled cut before QA — "does this look right?" |

---

## What Claude Decides Autonomously

Within an autonomous run, Claude may:

- Read any project file without asking
- Run `lib.brain diagnose` and interpret its output
- Run skill preflights and report failures
- Execute auto-gate skills (theme-factory, script-reconcile, asset-prep, QA)
- Invoke read-only sub-agents (asset-auditor, timeline-critic, retention-critic, data-analyst, render-doctor)
- Run `tsc --noEmit` and interpret compile errors
- Run `lib.qa.cli` and interpret QA findings
- Report staleness signals and ask whether to act
- Create repair plans and wait for approval
- Propose memory updates (as text, not file edits)

---

## What Claude Never Decides Autonomously

These actions require explicit instruction or approval from Mits:

| Action | Why |
|---|---|
| Set a HUMAN_GATE | Gate represents Mits's taste judgment, not a technical check |
| Run `npx remotion render` without `qa_passed` | Rendering without QA wastes time and may publish broken work |
| Edit `memory/creative-feedback.json` | Taste memory is Mits's record — proposals go through human review |
| Edit `training/derived/taste-rules.json` | Same reason |
| Push to any external service | Not within pipeline scope |
| Delete project files | Destructive, irreversible |
| Set or clear gates manually in `project.json` | Gates are set by skills + postflight scripts only |
| Run more than 3 consecutive auto-gates without reporting | Prevents silent runaway execution |

---

## How Staleness Affects Autonomy

Staleness signals from `lib.brain` are informational, not automatic blockers — with one exception.

**Default:** surface high-confidence staleness signals at the start of each run and let Mits decide whether to regenerate before continuing.

**Exception (soft blocker):** if the stale artifact is the direct input to the current action, treat it as a soft blocker. Example: `timeline.json` is stale before QA runs — the QA result will be against stale data. In this case, stop and ask before running QA.

Low and medium confidence staleness signals are observations only. Do not create blockers from them.

---

## Repair Plans

When the diagnosis shows `can_continue_autonomously: false` and `human_required: false` (validation errors, unknown state, or structural blocker):

1. Claude creates a repair plan — a specific ordered list of fixes
2. The plan is presented to Mits for approval before any fix is executed
3. Mits approves or modifies the plan
4. Claude executes the approved steps
5. Claude re-diagnoses to verify the repair worked

Claude never executes a repair plan unilaterally. A repair plan without human approval is a proposal, not a commitment.

---

## Memory Proposal Protocol

If during an autonomous run Claude observes a pattern that belongs in `memory/creative-feedback.json`:

1. Note the observation internally
2. Include it in the final report under "Memory Proposals" as structured text:
   ```
   Proposed addition to memory/creative-feedback.json:
     Field: soft_preferences
     Entry: "<proposed rule text>"
     Basis: <which project, which observation, why it generalises>
   ```
3. The proposal is applied only if Mits explicitly approves it
4. The `memory-curator` sub-agent may be used to check whether the proposal conflicts with existing rules before presenting it

---

## Iteration Limit

A single autonomous run may advance at most **3 consecutive auto-gates** without surfacing progress to Mits. After 3 gates, the run pauses and reports what was accomplished before asking to continue.

This limit exists to:
- Keep Mits informed of state changes
- Prevent Claude from advancing so far that a mid-run error requires rolling back multiple phases
- Preserve the human's mental model of where the project is

If Mits says "keep going", the 3-gate counter resets and another run begins.

---

## Confidence and Uncertainty

The brain diagnosis includes a `confidence` field on the autonomy verdict: `high`, `medium`, or `low`.

- `high` — proceed as described
- `medium` — proceed but note the uncertainty in the report
- `low` — stop and ask Mits to confirm the next action even if `can_continue_autonomously: true`

Claude should not override a `low` confidence verdict by reasoning that it "probably" knows what to do. The low confidence signal exists precisely for the cases where the brain cannot be certain — defer to Mits.

---

## Source of Truth Hierarchy

Within an autonomous run, these sources are read in this priority order:

1. `lib.brain diagnose` output — primary source for phase, gates, autonomy verdict
2. `project.json` gates_passed array — ground truth for gate state
3. `output/qa_report.json` — authoritative QA verdict
4. This policy document — governs what Claude may do with what the brain says
5. `.claude/rules/gate-enforcement.md` — gate definitions and skill mappings
6. `.claude/rules/reel-workflow.md` — phase order and phase-level rules

If these sources conflict (e.g. brain says `can_continue` but gate-enforcement says a prerequisite file is missing), stop and report the conflict. Do not resolve it autonomously.

---

## References

- Brain design: `docs/BRAIN_DESIGN.md`
- Gate enforcement: `.claude/rules/gate-enforcement.md`
- Autonomous reel skill: `.claude/skills/autonomous-reel/SKILL.md`
- Sub-agent roles: `docs/AGENT_ROLES.md`
- Analytics layer: `docs/DATA_LAYER.md`
