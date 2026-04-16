# Orchestration System Specification

## Purpose

This document defines the orchestration architecture for AI Reels Studio.

It is the source of truth for:
- workflow control
- phase transitions
- human approval interrupts
- artifact validation
- invalidation rules
- feedback and benchmark triggers
- memory and training integration
- division of responsibility between code and Claude

This document does **not** replace:
- creative direction
- creative feedback memory
- taste rules
- hook grammar
- body grammar
- motion grammar
- component mapping
- QA gates

Instead, it defines **how those systems are coordinated**.

---

## Core Principle

**Code controls the machine. Claude controls the creative judgment.**

### Code should own
- workflow state
- legal transitions
- gate enforcement
- artifact existence checks
- schema validation
- invalidation rules
- trigger logic
- retries
- event logging
- parity checks
- benchmark scheduling
- feedback-capture prompting
- memory-promotion proposal routing

### Claude should own
- script writing
- hook archetype choice within grammar
- shot-list planning
- component selection
- motion-intent planning
- revision strategy
- creative tradeoffs
- benchmark interpretation
- feedback interpretation
- memory update proposals

---

## Operating Model

The orchestration layer is a coded state machine.

Claude is a planning worker inside that machine.

The orchestrator decides:
- what phase the project is in
- what can run next
- what is blocked
- what inputs are required
- whether code should run directly
- whether Claude should be called
- whether human approval is required
- what downstream phases become invalid if something changes

Claude does **not** decide workflow order.

---

## Workflow Type

This is a **human-in-the-loop creative workflow**.

That means:
- some steps are deterministic and coded
- some steps are creative and require Claude
- some steps require human review or approval
- the workflow must pause and resume safely
- the workflow must preserve state and event history

This is not a fully autonomous pipeline.
It is a supervised orchestration system.

---

## Sources of Truth

### Creative sources of truth
1. `docs/creative-direction.md`
2. `memory/creative-feedback.json`
3. `training/derived/taste-rules.json`
4. `.claude/rules/hook-grammar.md`
5. `.claude/rules/body-grammar.md`
6. `.claude/rules/motion-grammar.md`

### Workflow sources of truth
1. `project.json` (`gates_passed` + `phase` + `status`)
2. `lib/orchestrator/spec.py` (phase definitions, invalidation rules)
3. `lib/parity.py` (style threshold parity checks)
4. `.claude/rules/qa-gates.md` (QA validation rules)
5. `projects/<slug>/output/orchestration-log.jsonl` (event history)
6. `projects/<slug>/output/review-feedback.md` (project-local review signals)

If these conflict:
- technical safety / schema / QA / parity rules are non-negotiable
- style defaults must yield to creative direction and approved grammar
- low-confidence taste rules may guide tie-breaks only

---

## Implementation

### Module: `lib/orchestrator/`

| Module | Purpose |
|---|---|
| `spec.py` | Phase definitions, state model, invalidation rules — pure data |
| `state.py` | State derivation from `project.json`; backward-compatible |
| `transitions.py` | Legal next action computation from current state |
| `validators.py` | Artifact existence checks + parity enforcement |
| `invalidation.py` | Downstream invalidation via `lib.gates.reset_gate` |
| `events.py` | Event logging to `orchestration-log.jsonl` |
| `cli.py` | CLI commands |

### CLI

```bash
python -m lib.orchestrator status    projects/<slug>          # quick state summary
python -m lib.orchestrator next      projects/<slug>          # legal next actions
python -m lib.orchestrator diagnose  projects/<slug>          # full diagnostic
python -m lib.orchestrator approve   projects/<slug> <gate>   # set a gate
python -m lib.orchestrator reject    projects/<slug> <phase>  # flag for revision
python -m lib.orchestrator resume    projects/<slug>          # what to do to resume
python -m lib.orchestrator invalidate projects/<slug> <file>  # cascade-invalidate
python -m lib.orchestrator history   projects/<slug>          # event log
```

---

## Project State Model

State is derived from `project.json` (`gates_passed` + artifact existence).
No migration required for existing projects.

| State | Description |
|---|---|
| `created` | No gates passed |
| `brief_ready` | `brief_approved` set |
| `theme_ready` | `brief_approved` + `theme_set` |
| `script_ready` | `script_approved` — awaiting voice generation |
| `voice_ingested` | `script_approved` + `audio/beat-map.json` exists |
| `reconciled` | `reconciliation_resolved` |
| `shot_list_visual_done` | `visual_assignment_approved` |
| `shot_list_fitness_done` | `asset_fitness_passed` |
| `shot_list_ready` | `technical_planning_approved` |
| `motion_done_awaiting_assets` | `motion_intent_reviewed` but not `assets_validated` |
| `assets_done_awaiting_motion` | `assets_validated` but not `motion_intent_reviewed` |
| `assets_ready` | Both parallel phases complete |
| `assembled` | `output/timeline.json` exists + both parallel gates |
| `preview_approved` | `preview_passed` |
| `qa_passed` | `qa_passed` |
| `rendered` | `qa_passed` + render artifact exists |

---

## Invalidation Rules

When an upstream artifact changes, remove the corresponding gate
(and all downstream gates) from `project.json`:

| Changed artifact | Reset from gate | Downstream effect |
|---|---|---|
| `script.md` | `reconciliation_resolved` | All downstream phases stale |
| `audio/beat-map.json` | `visual_assignment_approved` | Shot list, motion, assembly stale |
| `shot-list.md` | `technical_planning_approved` | Motion intent, assembly, preview, QA stale |
| `output/motion-intent.md` | `assets_validated` | Assembly, preview, QA stale |
| `output/timeline.json` | `preview_passed` | Preview, QA stale |

Run: `python -m lib.orchestrator invalidate projects/<slug> <artifact>`

---

## Human Approval Interrupts

Phases requiring explicit human approval before the workflow continues:

| Phase | Approval command |
|---|---|
| Brief direction | `python -m lib.orchestrator approve <slug> brief_approved` |
| Theme | `python -m lib.orchestrator approve <slug> theme_set` |
| Script | `python -m lib.orchestrator approve <slug> script_approved` |
| Script reconciliation | `python -m lib.orchestrator approve <slug> reconciliation_resolved` |
| Visual assignment | `python -m lib.orchestrator approve <slug> visual_assignment_approved` |
| Asset fitness | `python -m lib.orchestrator approve <slug> asset_fitness_passed` |
| Technical planning | `python -m lib.orchestrator approve <slug> technical_planning_approved` |
| Motion intent | `python -m lib.orchestrator approve <slug> motion_intent_reviewed` |
| Asset validation | `python -m lib.orchestrator approve <slug> assets_validated` |
| Preview | `python -m lib.orchestrator approve <slug> preview_passed` |
| QA | `python -m lib.orchestrator approve <slug> qa_passed` |

---

## Creative Intent Summary Gate

Required before major creative phases (not a gates_passed entry):
- script generation or major revision
- shot-list creation (4b-i)
- motion-intent planning
- structural assembly changes
- revision rounds

Claude produces the summary and waits for user confirmation before proceeding.
Managed in conversation — not tracked in `project.json`.

---

## Parity Enforcement

Parity checks (`python lib/parity.py`) run automatically before:
- `assemble-reel`
- `qa-reel`
- `render`

Parity failures are blockers. They detect source-of-truth drift between
`lib/qa/checks.py` (STYLE_THRESHOLDS) and markdown rule/skill files.

---

## Feedback Integration

| Trigger | Action |
|---|---|
| After preview review | Suggest `/feedback-capture` in conversation |
| After QA failure or weak review | Suggest `/feedback-capture` |
| After render | Suggest `/feedback-capture` |
| After benchmark | Suggest promoting to `creative-feedback.json` if 2+ signal |

Project-local signals → `projects/<slug>/output/review-feedback.md`
Global signals → proposed via `feedback-capture` → `memory/creative-feedback.json` (human approves)

---

## Benchmark Integration

Trigger benchmark review after:
- Major rule changes (e.g., Changes 7–9)
- Designated test reels
- Weak review rounds
- Every ~5 completed reels

Scorecard: `training/benchmark-scorecard.md`
Template: `projects/_shared/benchmark-review-template.md`

---

## Policy: Code vs Claude

| Decision | Owner |
|---|---|
| What can run next | Code |
| What is blocked | Code |
| What is invalid | Code |
| What must be rerun | Code |
| What parity checks must pass | Code |
| What logs are written | Code |
| What creative strategy best fits this phase | Claude |
| Which components fit best | Claude |
| How to revise weak sections | Claude |
| Whether creative direction feels right | Human |
| Whether approvals are granted | Human |
| Whether a global memory update is promoted | Human |
| Whether a benchmark insight deserves annotation | Human |
