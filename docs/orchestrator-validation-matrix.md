# Orchestrator Validation Matrix

Source of truth for orchestration execution behavior. Each row defines a scenario, the command that validates it, and the criteria for pass/fail.

**Test status legend:** ✅ implemented · ⚠ partial · 🔲 deferred

---

## Scenario Matrix

### A. Healthy Deterministic Execution

| Scenario | Command | Initial State | Expected Status | Expected State Effect | Log Behavior | Notes |
|---|---|---|---|---|---|---|
| **1. run_advances_deterministic_phase** ✅ | `Runner().run(project_dir)` | `shot_list_ready` | `SKIPPED` or `PAUSED_FOR_CLAUDE` | No gate regression | Event logged | `asset-prep` has no task → SKIPPED; `motion-intent` → PAUSED |
| **2. run_phase_succeeds_on_legal_phase** ✅ | `Runner().run_phase(project_dir, "render")` (mocked) | `qa_passed` | `SUCCESS` | No gate regression | Event logged | Task mocked; parity mocked to pass |

---

### B. Legal Single-Phase Execution

| Scenario | Command | Initial State | Expected Status | Gate Effect | Notes |
|---|---|---|---|---|---|
| Code phase no-task → SKIPPED | `run_phase(project_dir, "asset-prep")` | `shot_list_ready` | `SKIPPED` | None | Normal code path for phases without registered task |
| Claude phase → WorkOrder | `run_phase(project_dir, "reel-script")` | `theme_ready` | `PAUSED_FOR_CLAUDE` | None | WorkOrder must have purpose, memory, rules, approval_command |
| Human phase → HumanAction | `run_phase(project_dir, "ingest-voice")` | `script_ready` | `PAUSED_FOR_HUMAN` | None | HumanAction must have numbered steps |

---

### C. Illegal Phase Rejection

| Scenario | Command | Initial State | Expected Status | Expected Gate Effect | Notes |
|---|---|---|---|---|---|
| **3. run_phase_fails_on_illegal_phase** ✅ | `Runner().run_phase(project_dir, "reel-script")` | `created` | `BLOCKED` | No change | Missing `brief_approved`, `theme_set` gates |
| Unknown phase key | `Runner().run_phase(project_dir, "nonexistent-xyz")` | any | `FAILED` | No change | Unknown key not in PHASES registry |
| Has gate, missing required file | `Runner().run_phase(project_dir, "render")` | `qa_passed` + no `output/qa-report.md` | `BLOCKED` | No change | Validators catch missing file before execution |

---

### D. Claude Pause Behavior

| Scenario | Command | Initial State | Expected Status | WorkOrder Fields | CIS Required? | Notes |
|---|---|---|---|---|---|---|
| **4. run_pauses_for_claude_phase** ✅ | `Runner().run(project_dir)` | `theme_ready` | `PAUSED_FOR_CLAUDE` | phase_key, purpose, memory_to_read, rules_to_apply, approval_command | Yes (reel-script) | WorkOrder must be non-None |
| Claude phase with no CIS | `run_phase(project_dir, "assemble-reel")` | `assets_ready` | `PAUSED_FOR_CLAUDE` | same | No | assemble-reel doesn't require CIS |
| run() stops after first Claude pause | `Runner().run(project_dir)` | `theme_ready` | `PAUSED_FOR_CLAUDE` | — | — | phases_succeeded must be 0 |

---

### E. Human Approval Pause Behavior

| Scenario | Command | Initial State | Expected Status | HumanAction Fields | Notes |
|---|---|---|---|---|---|
| **5. run_pauses_for_human_approval** ✅ | `Runner().run(project_dir)` | `script_ready` | `PAUSED_FOR_HUMAN` | steps, approval_command, rejection_command | ingest-voice requires human action |
| Assembled project waits for preview | `Runner().run(project_dir)` | `assembled` | `PAUSED_FOR_HUMAN` | same | `preview` is a human phase |

---

### F. Parity-Blocked Execution

| Scenario | Command | Initial State | Expected Status | Gate Effect | Notes |
|---|---|---|---|---|---|
| **6. run_blocks_on_parity_failure** ✅ | `Runner().run_phase(project_dir, "render")` (parity mocked to fail) | `qa_passed` | `BLOCKED` | No change | Parity checked in `validate_phase_preconditions` before execution |
| Parity blocked for qa-reel | `run_phase(project_dir, "qa-reel")` (parity mocked to fail) | `preview_passed` | `BLOCKED` | No change | Same mechanism |
| Parity blocked for assemble-reel | `run_phase(project_dir, "assemble-reel")` (parity mocked to fail) | `assets_ready` | `BLOCKED` | No change | All three parity-required phases behave identically |

---

### G. Validation-Blocked Execution

| Scenario | Command | Initial State | Expected Status | Notes |
|---|---|---|---|---|
| **7. run_blocks_on_missing_artifact** ✅ | `Runner().run_phase(project_dir, "render")` | `qa_passed` gates set + `output/qa-report.md` missing | `BLOCKED` | File check in `validate_phase_preconditions` |
| Missing beat-map blocks shot-list | `run_phase(project_dir, "shot-list-4b-i")` | `reconciliation_resolved` + no `audio/beat-map.json` | `BLOCKED` | Same mechanism |

---

### H. Invalidation Cascade

| Scenario | Command | Initial State | Gate Effect | Verification |
|---|---|---|---|---|
| **8. invalidate_marks_downstream_stale** ✅ | `invalidate_from_change(project_dir, "script.md")` | `reconciliation_resolved` set | Removes `reconciliation_resolved` + all downstream | Gates upstream of script.md (`brief_approved`, `theme_set`, `script_approved`) must survive |
| Invalidate beat-map | `invalidate_from_change(project_dir, "audio/beat-map.json")` | `visual_assignment_approved` set | Removes visual_assignment_approved + downstream | upstream survives |
| Invalidate timeline | `invalidate_from_change(project_dir, "output/timeline.json")` | `preview_passed` set | Removes preview_passed + downstream | upstream survives |
| Unknown artifact | `invalidate_from_change(project_dir, "unknown.json")` | any | No change | `result.reset_from_gate` must be `None` |
| After invalidation, run() respects stale state | `load_snapshot(project_dir)` after invalidation | any | State degraded | `orchestration_state` reflects removed gates |

**Invalidation rules (from `spec.py::INVALIDATION_MAP`):**

| Changed artifact | Gate reset from | Cascade effect |
|---|---|---|
| `script.md` | `reconciliation_resolved` | All downstream stale |
| `audio/beat-map.json` | `visual_assignment_approved` | Shot list, motion, assembly stale |
| `shot-list.md` | `technical_planning_approved` | Motion intent, assembly, preview, QA stale |
| `output/motion-intent.md` | `assets_validated` | Assembly, preview, QA stale |
| `output/timeline.json` | `preview_passed` | Preview, QA stale |

---

### I. History / Event Logging

| Scenario | Command | Expected Log Entry Fields | Notes |
|---|---|---|---|
| **9. history_records_execution_event** ✅ | `Runner().run_phase(project_dir, "reel-script")` | `timestamp`, `actor`, `action`, `result` | Written to `output/orchestration-log.jsonl` |
| Blocked phase | `run_phase(project_dir, "reel-script")` on `fresh_project` | `result`: `"blocked"` or `"failed"` | May not log depending on impl |
| Approve command | `python -m lib.orchestrator approve <slug> brief_approved` | `action`: `"approve brief_approved"`, `actor`: `"human"` | Always logged |
| Reject command | `python -m lib.orchestrator reject <slug> reel-script` | `result`: `"rejected"` | Always logged |
| Invalidation | `python -m lib.orchestrator invalidate <slug> script.md` | `result`: `"invalidated"` | Always logged |

---

### J. Resume Behavior

| Scenario | Command | Precondition | Expected Output | Notes |
|---|---|---|---|---|
| **10. resume_after_pause_surfaces_correct_next_step** ✅ | `main(["resume", project_dir])` | After `run()` pauses at `reel-script` | Output contains `reel-script` | Reads `compute_next_actions(snap)` |
| Pause state in project.json | `load_json(project_dir / "project.json")` | After `Runner().run()` pauses | `_paused_at` field present | Set by `runner._save_pause_state()` |
| Clear pause state on success | `Runner().run_phase(...)` succeeds | Project had `_paused_at` set | `_paused_at` removed from project.json | Set by `runner._clear_pause_state()` |

---

## Summary Table

| # | Scenario | Status | Test Location |
|---|---|---|---|
| 1 | run_advances_deterministic_phase | ✅ implemented | `test_runner.py::TestCodePhaseExecution::test_run_advances_through_skipped_phases` |
| 2 | run_phase_succeeds_on_legal_phase | ✅ implemented | `test_runner.py::TestCodePhaseExecution::test_render_succeeds_with_mocked_task` |
| 3 | run_phase_fails_on_illegal_phase | ✅ implemented | `test_runner.py::TestIllegalPhaseRejection::test_run_phase_fails_on_missing_gates` |
| 4 | run_pauses_for_claude_phase | ✅ implemented | `test_runner.py::TestClaudePauseBehavior::test_run_phase_pauses_for_claude` |
| 5 | run_pauses_for_human_approval | ✅ implemented | `test_runner.py::TestHumanPauseBehavior::test_run_phase_pauses_for_human` |
| 6 | run_blocks_on_parity_failure | ✅ implemented | `test_runner.py::TestParityBlockedExecution::test_parity_failure_blocks_render` |
| 7 | run_blocks_on_missing_artifact | ✅ implemented | `test_runner.py::TestIllegalPhaseRejection::test_render_blocked_when_missing_required_file` |
| 8 | invalidate_marks_downstream_stale | ✅ implemented | `test_runner.py::TestInvalidationCascade::test_invalidate_script_removes_downstream_gates` |
| 9 | history_records_execution_event | ✅ implemented | `test_runner.py::TestEventLogging::test_run_phase_creates_event_log` |
| 10 | resume_after_pause_surfaces_correct_next_step | ✅ implemented | `test_runner.py::TestResumeBehavior::test_pause_state_preserved_for_resume` + `test_cli.py::TestResumeCommand::test_resume_after_pause_shows_correct_next` |

**Total: 10 scenarios · 10 implemented · 0 partial · 0 deferred**

---

## Running the Validation Suite

```bash
# Full orchestrator test suite
pytest tests/orchestrator -v

# Quiet mode with counts
pytest tests/orchestrator -q

# Run via convenience script
bash scripts/validate-orchestrator.sh

# One category at a time
pytest tests/orchestrator/test_runner.py -v
pytest tests/orchestrator/test_cli.py -v

# Single scenario
pytest tests/orchestrator -k "test_run_pauses_for_claude_phase" -v
```

---

## Required Behavior Assertions (summary)

### Result model
- `SUCCESS` → no error, gate set if spec defines one
- `PAUSED_FOR_CLAUDE` → `work_order` is not None; `human_action` is None
- `PAUSED_FOR_HUMAN` → `human_action` is not None; `work_order` is None
- `BLOCKED` → `error` has a human-readable explanation; no state mutation
- `FAILED` → `error` has a human-readable explanation; no gate removal

### Safety
- Illegal phases **never** mutate `gates_passed`
- Missing artifacts **never** advance workflow
- Parity failures **never** allow assembly/QA/render to proceed

### Workflow
- Code phases that have no task return `SKIPPED` (not `FAILED`)
- Claude phases always return `PAUSED_FOR_CLAUDE`
- Human phases always return `PAUSED_FOR_HUMAN`
- `run()` stops at the first pause/failure and does not continue
- Invalidation cascade respects `INVALIDATION_MAP` exactly
- Event log (`output/orchestration-log.jsonl`) is always written after execution
