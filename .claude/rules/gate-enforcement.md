---
description: Deterministic gate checks that prevent skills from running with incomplete preconditions
globs: ["projects/**"]
---

# Gate Enforcement

Adapted from ruflo's DeterministicToolGateway pattern. Every skill must validate its preconditions before starting work — not with a polite "please check" in markdown, but with a deterministic file/field check.

## How It Works

Before any skill begins work, it must:

1. Read `project.json`
2. Check `gates_passed` array for required gates
3. Check that required files exist on disk
4. If any check fails → report the specific failure and stop

This is not optional. A skill that skips gate checks may produce output that downstream skills cannot use.

## The 11 Gates

| Gate ID | Set by | Required before | File check | Field check |
|---|---|---|---|---|
| `brief_approved` | User approval after source-brief | reel-script | `brief.md` exists and is not TBD-only | — |
| `theme_set` | theme-factory | reel-script | — | `project.json` has non-null `theme`, `theme_primary`, `theme_secondary` |
| `script_approved` | User approval after reel-script | ingest-voice, broll-pipeline | `script.md` exists with ElevenLabs script section | — |
| `reconciliation_resolved` | script-reconcile | beat-map creation | `audio/reconciliation.md` exists | Result is not "Needs Re-Record" |
| `visual_assignment_approved` | User approval after shot-list 4b-i | shot-list 4b-ii | `shot-list.md` has Phase 4b-i section | — |
| `asset_fitness_passed` | shot-list 4b-ii auto-check | shot-list 4b-iii | `shot-list.md` has Phase 4b-ii section | Zero MISMATCH or MISSING scores |
| `technical_planning_approved` | User approval after shot-list 4b-iii | motion-intent | `shot-list.md` has Phase 4b-iii section | — |
| `motion_intent_reviewed` | User review after motion-intent | assemble-reel | `output/motion-intent.md` exists | — |
| `assets_validated` | asset-prep | assemble-reel | All assets in `remotion/public/` pass ffprobe | Validation report exists |
| `preview_passed` | Quick preview after assembly | qa-reel | `output/timeline.json` exists | Remotion renders without errors |
| `qa_passed` | qa-reel | render | `output/qa-report.md` exists | No blocking issues |

## Skill-to-Gate Mapping

Every skill must check these gates before starting:

| Skill | Required gates in `gates_passed` | Required files on disk |
|---|---|---|
| **source-brief** | (none — entry point) | URL provided |
| **theme-factory** | (none — can run from product name alone) | `project.json` exists |
| **reel-script** | `brief_approved`, `theme_set` | `brief.md`, `project.json` with theme fields |
| **broll-pipeline** | `script_approved` | B-roll footage exists |
| **ingest-voice** | `script_approved` | `script.md`, audio file provided |
| **script-reconcile** | (runs immediately after ingest-voice) | `audio/voice.json`, `script.md` |
| **caption-polish** | `reconciliation_resolved` | `audio/captions.json`, `audio/beat-map.json` |
| **capture-demo** | `reconciliation_resolved` | `audio/beat-map.json` |
| **shot-list** (4b-i) | `reconciliation_resolved` | `audio/beat-map.json`, `assets/catalog.json` |
| **shot-list** (4b-ii) | `visual_assignment_approved` | `shot-list.md` with 4b-i section |
| **shot-list** (4b-iii) | `asset_fitness_passed` | `shot-list.md` with 4b-ii section |
| **motion-intent** | `technical_planning_approved` | `shot-list.md` complete |
| **asset-prep** | `technical_planning_approved` | Raw assets exist |
| **assemble-reel** | `motion_intent_reviewed`, `assets_validated` | `output/motion-intent.md`, assets in `remotion/public/` |
| **qa-reel** | `preview_passed` | `output/timeline.json` |
| **render** | `qa_passed` | QA report with no blockers |
| **frontend-design** | (none — cross-phase reference skill) | Invoked during shot-list 4b-ii and assembly |

## Gate Check Procedure

At the start of every skill, run this check:

```
1. Read project.json
2. For each required gate:
   - Is gate_id in gates_passed array?
   - If NO → report: "BLOCKED: Gate '{gate_id}' not passed. Run {skill_that_sets_it} first."
3. For each required file:
   - Does file exist on disk?
   - If NO → report: "BLOCKED: Required file '{path}' not found."
4. If all checks pass → proceed with skill
5. If any check fails → list ALL failures (not just the first one) and stop
```

## Setting Gates

When a gate is cleared, the skill that owns it must:

1. Add the gate ID to `gates_passed` array in `project.json`
2. Update `phase` to the current phase
3. Update `status` to `approved` or `completed`
4. Update `updated` timestamp

Example after script approval:
```json
{
  "phase": "script",
  "status": "approved",
  "gates_passed": ["brief_approved", "theme_set", "script_approved"],
  "updated": "2026-04-05T14:30:00Z"
}
```

## Parallel Phase Handling

When two phases run in parallel (e.g., motion-intent + asset-prep):
- Both check the same prerequisite gate (`technical_planning_approved`)
- Each sets its own gate independently (`motion_intent_reviewed`, `assets_validated`)
- The downstream phase (assemble-reel) requires BOTH gates

This naturally enforces the join point — assembly cannot start until both parallel phases complete.

## Reset Behavior

If a gate needs to be re-run (e.g., user changes the script after approval):
- Remove the invalidated gate AND all downstream gates from `gates_passed`
- Set `status` to `in_progress` on the current phase
- This cascades: removing `script_approved` invalidates everything downstream

## Why This Matters

Without deterministic gates, the pipeline relies on skills politely checking preconditions. This fails when:
- A skill is invoked out of order
- A user restarts mid-pipeline and forgets what was completed
- An approval happened in a previous session and there's no record
- Parallel phases complete at different times

With `gates_passed` in project.json, every skill has a single source of truth for "what has been done and approved."
