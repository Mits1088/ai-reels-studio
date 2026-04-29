---
name: autonomous-reel
description: Continue a reel project autonomously until the next human approval gate or hard blocker. Diagnoses project state via lib.brain, resolves auto-gates without human input, stops cleanly at human gates, creates repair plans for blockers, and never renders without QA. Invoke when the user says "continue", "keep going", "what's next", or "finish this autonomously".
---

# Autonomous Reel Skill

`lib.brain` is the single coordination surface. Read its output, follow the tree below, act once, verify, repeat.

---

## Decision Tree

### 0. project_type check (before anything else)

Read `project_type` from the diagnosis JSON (`project_type` field) or directly from `project.json`.

If `project_type` is not `"reel"`:
→ Stop immediately. Do not diagnose, repair, or advance.
→ Report:
```
⛔ Not a reel project
project_type: <value>
This project is not eligible for autonomous-reel.
For YouTube projects: use the /youtube skill suite.
For unknown project_type: set project_type in project.json first.
```

---

### 1. Diagnose (always first)

```bash
PYTHONPATH=. python -m lib.brain diagnose projects/<slug> --json
```

Hold: `healthy`, `validation_errors`, `autonomy.*`, `gates.*`, `qa.*`, `artifacts.staleness_results`, `project_type`.

---

### 2. Route — first matching condition wins

**Project not found / project.json missing**
→ Report and stop. Ask Mits for the correct slug.

**`validation_errors` non-empty**
→ Run `PYTHONPATH=. python -m lib.brain repair projects/<slug>`.
→ If the repair plan contains a **code-actor** migration step (`lib.migrate`), run it immediately — it is code-safe and requires no human judgment:
```bash
PYTHONPATH=. python -m lib.migrate projects/<slug>
```
Re-diagnose after migration. If validation errors persist (non-migrate errors remain), present the repair plan and stop.
→ If NO code-actor steps: present the plan and stop.

**`autonomy.human_required: true`**
→ Stop. Present:
```
⏸  WAITING FOR MITS
Gate:   <gates.next_required>
Reason: <autonomy.human_required_reason>
Run:    <autonomy.next_action_command>
```
Never proceed past a human gate.

**`can_continue_autonomously: false` AND `human_required: false`** (blocked)
→ Run `PYTHONPATH=. python -m lib.brain repair projects/<slug>`, present the plan verbatim, stop. Invoke specialist agents listed in the plan before asking Mits to act.

**`qa.verdict == "FAIL"`**
→ Invoke `qa-runner` agent. Present blockers. Do not render. Ask Mits whether to repair or escalate.

**`gates.next_required == "assets_validated"`**
→ Invoke `asset-auditor` agent first, then proceed to Step 3.

**`gates.next_required == "preview_passed"`**
→ Invoke `timeline-critic` agent first, then proceed to Step 3.

**`can_continue_autonomously: true` AND `autonomy.next_action_actor == "code"`**
→ Dry-run:
```bash
PYTHONPATH=. python -m lib.brain advance projects/<slug>
```
If the dry-run looks correct, ask Mits before executing:
```bash
PYTHONPATH=. python -m lib.brain advance projects/<slug> --execute
```
After execution re-diagnose and loop.

**`can_continue_autonomously: true` AND actor is `claude`**
→ Invoke the matching skill (see Claude-actor table below). Run preflight first:
```bash
PYTHONPATH=. python -m lib.phase check <skill-name> projects/<slug>
```

**All 11 gates passed AND `qa_passed` in `gates.passed`** (render requested)
→ See Render section below.

---

## Claude-actor Gates

| Gate | Skill to invoke |
|---|---|
| `theme_set` | theme-factory |
| `reconciliation_resolved` | script-reconcile |
| `asset_fitness_passed` | shot-list Phase 4b-ii |
| `assets_validated` | asset-prep |

Run preflight before every claude-actor skill. If preflight fails, report and stop.

---

## Render

Pre-render checks (both must pass):
```bash
PYTHONPATH=. python -m lib.preflight_render projects/<slug>
cd remotion && npx tsc --noEmit
```

If either fails: invoke `render-doctor` agent. Do not render until both pass.

```bash
cd remotion && npx remotion render ReelComposition --output out/reel.mp4
```

After render: suggest `publish-prep` and `feedback-capture`.

**Hard rule:** `qa_passed` must be in `gates.passed` (the array) — not just `qa.verdict`. Check both.

---

## Critic Advisory

When `critic.available: true` AND `critic.status` is `critic_warnings` or `critic_blocked`, surface findings **before** advancing — even in advisory mode:

```
ℹ  Critic findings (advisory — not blocking):
Status: <critic.status>
Findings: <critic.findings_count> (<critic.highest_severity> highest)
Top: <top_findings[0..2]>
```

Critic findings are **never blocking** unless `--critic-hard-mode` was explicitly passed to the diagnose command. Do not stop for advisory findings — surface them and continue if the gate path is otherwise clear.

If `diagnosis.critic_hard_blocked: true` (requires explicit opt-in to hard mode), treat as a blocker: run repair, present plan, stop.

---

## Staleness

For any `artifacts.staleness_results` entry with `confidence: "high"`:
```
⚠  <upstream> → <downstream>: stale by <delta>s
Action: <recommended_action>
```
Warn and let Mits decide. If the stale artifact is what the current action would produce, treat as a soft blocker and ask before proceeding.

---

## Sub-agents

| When | Agent |
|---|---|
| QA failed | `qa-runner` |
| Next gate is `assets_validated` | `asset-auditor` |
| Next gate is `preview_passed` | `timeline-critic` |
| Render or tsc error | `render-doctor` |
| repair plan recommends one | whichever is named |

Invoke with the slug and a specific question. Summarise their verdict — do not pass raw output to Mits.

---

## After Each Action

1. Re-run diagnose `--json`
2. Verify the completed gate is in `gates.passed`
3. If the gate did not advance: treat as a blocker, stop
4. Max 3 consecutive auto-gates per run — then surface progress to Mits before continuing

---

## Final Report

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Autonomous Run: <slug>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gates before/after: N/11 → N/11
Actions taken:      ✓ <gate> | (none)
Stop reason:        ⏸ human gate | 🔧 blocker | ✓ complete
Staleness:          [none] | [high: upstream → downstream]
Next for Mits:      <command or repair plan>
```

---

## Hard Stops

1. Never render unless `qa_passed` is in `gates.passed`
2. Never bypass a human gate
3. Never edit `memory/creative-feedback.json` directly — proposals only
4. Never set a gate manually
5. Never render with TypeScript errors
6. Never loop more than 3 consecutive auto-gates without reporting to Mits
