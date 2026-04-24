# Claude Code Hooks

Six shell hooks automate pipeline safety checks and context injection. Hooks are configured in `.claude/settings.json` and run in response to Claude tool use events.

---

## Hook Architecture

```
SessionStart
├── reinject-after-compact.sh     ← compact matcher: re-injects critical rules + active project
└── portfolio-sweep.sh            ← compact matcher: shows portfolio health summary (read-only)

PreToolUse
├── Edit|Write → protect-generated-artifacts.sh
└── Bash       → prevent-unsafe-render.sh

PostToolUse
├── Edit|Write → validate-project-json.sh
│            → brain-status.sh
└── Bash      → qa-analytics-ingest.sh
```

Hooks are **non-blocking by default** (exit 0). Only `prevent-unsafe-render.sh` may hard-block (exit 2), and only when the project is confirmed and the gate is definitively unset.

---

## Hook Reference

### 1. `portfolio-sweep.sh`

**Trigger:** `SessionStart` — matcher: `compact`
**Purpose:** Show portfolio health summary after compact recovery, giving Claude situational awareness of all active projects without requiring manual inspection.

**What it outputs (to Claude context):**
```
AI Reels Brain portfolio status:
  Projects: 17
  Blocked: 2
  Human approval needed: 3
  Can continue: 5
Top attention:
  1. claude-cowork — QA fail — run: python -m lib.brain repair projects/claude-cowork
  2. gemma-4 — awaiting approval — run: python -m lib.brain repair projects/gemma-4
  3. google-stitch — 1 stale signal(s) — run: python -m lib.brain repair projects/google-stitch
```

**Attention tier logic:**
- Tier 0 (blocked): unhealthy, not human-required, not can-continue
- Tier 1 (human-required): waiting for approval gate
- Tier 2 (stale/degraded): unhealthy or has high-confidence staleness signals
- Tier 3 (healthy): fully healthy — omitted from attention list

**Fail-safe:** Checks for `lib/brain/__init__.py` and `projects/` before running — silent exit if not in this repo. Silent on any Python failure. Exits 0 always.

**Read-only guarantee:** Never edits files, never resets gates, never applies memory. Runs `python -m lib.brain sweep projects/ --json` only.

---

### 2. `reinject-after-compact.sh`

**Trigger:** `SessionStart` — matcher: `compact`
**Purpose:** Re-inject critical project context after Claude's context is compacted.

**What it outputs (to Claude context):**
1. `CRITICAL CONTEXT` heredoc with pipeline key rules and tool commands
2. Brain status of the most recently modified project (active project summary)

**Brain status output format:**
```
Active project: claude-managed-agents
  Phase: render  |  Gates: 11/11  |  Healthy: ✓  |  QA: pass
  ▶  Next: run_render
```

**Fail-safe:** If no project exists or brain is unavailable, outputs only the CONTEXT block — no errors. Exit 0 always.

---

### 3. `protect-generated-artifacts.sh`

**Trigger:** `PreToolUse` — matcher: `Edit|Write`
**Purpose:** Prevent Claude from overwriting generated artifact files that are expensive to regenerate (audio, rendered video, etc.).

**Protected paths:** `audio/`, `remotion/out/`, any `.mp4` in the project output folder.

**Fail-safe:** Warns and allows if the protection check cannot be evaluated. Only blocks when the path is clearly in a protected zone.

---

### 4. `prevent-unsafe-render.sh`

**Trigger:** `PreToolUse` — matcher: `Bash`
**Purpose:** Block `npx remotion render` commands when the `qa_passed` gate is not set.

**Early-exit guard:** Only activates when the Bash command contains `"remotion render"`. All other Bash commands pass through immediately (exit 0, no output).

**Project detection:**
1. Extracts `projects/<slug>` from the render command via regex
2. Falls back to the most recently modified `project.json` if no slug found

**Gate check:** Reads brain diagnosis JSON and checks `qa_passed` in `gates.passed`.

**When blocked (exit 2):**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RENDER BLOCKED — qa_passed gate not set

  Project:    claude-managed-agents
  Gates:      10/11
  QA verdict: not_run

  Run QA first:
    PYTHONPATH=. python -m lib.qa.cli projects/claude-managed-agents

  Then check gates:
    PYTHONPATH=. python -m lib.gates status projects/claude-managed-agents
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**When allowed (exit 0):**
```
render-guard: qa_passed confirmed for claude-managed-agents (QA: pass, 11/11 gates). Render allowed.
```

**Fail-safe:** If project cannot be determined or brain is unavailable, outputs a warning to stderr and exits 0 (allows the render with a manual verification reminder).

---

### 5. `validate-project-json.sh`

**Trigger:** `PostToolUse` — matcher: `Edit|Write`
**Purpose:** Validate `project.json` structure after every edit to catch schema violations immediately.

**What it checks:** Required fields, gate ID validity, phase value, JSON syntax.

**Fail-safe:** Silent on non-project.json edits. Exits 0 always (warns but doesn't block after the fact).

---

### 6. `brain-status.sh`

**Trigger:** `PostToolUse` — matcher: `Edit|Write`
**Purpose:** Show compact pipeline status after editing key project state files, so Claude stays oriented after making changes.

**Early-exit guard:** Only activates for these specific files:
- `project.json`
- `output/timeline.json`
- `output/qa_report.json`
- `output/qa-report.md`
- `output/motion-intent.md`
- `shot-list.md`
- `audio/beat-map.json`
- `audio/captions.json`

Also requires the file to be inside a `projects/` directory.

**Output format:**
```
Brain status — claude-managed-agents
  Phase: assemble  |  Gates: 8/11  |  QA: not_run
  ▶  Safe to continue: run_qa_reel
```

Or when blocked:
```
Brain status — claude-managed-agents
  Phase: assemble  |  Gates: 8/11  |  QA: not_run
  ✗  Blocked: resolve_asset_fitness
     Run: PYTHONPATH=. python -m lib.validate projects/claude-managed-agents
```

Or when waiting for human:
```
Brain status — claude-managed-agents
  Phase: shot-list  |  Gates: 5/11  |  QA: not_run
  ⏸  Waiting for Mits: visual_assignment_approved requires human review
```

**Staleness signal:**
```
  ⚠  2 high-confidence staleness signal(s)
     Run: PYTHONPATH=. python -m lib.brain diagnose projects/<slug> for details
```

**Fail-safe:** Silent on any error. Project root discovery walks up from the edited file path. Exits 0 always.

---

### 7. `qa-analytics-ingest.sh`

**Trigger:** `PostToolUse` — matcher: `Bash`
**Purpose:** After a QA run completes, automatically ingest the project into the analytics database.

**Early-exit guard:** Only activates when the Bash command contains `"lib.qa.cli"`. All other Bash commands exit immediately.

**Additional guard:** Only runs if `data/analytics.db` exists (analytics is entirely opt-in — the file must be initialized via `python -m lib.analytics init` before any ingest runs).

**What it does:**
1. Extracts the project slug from the QA command (`projects/<slug>`)
2. Runs `python -m lib.analytics ingest projects/<slug>`
3. Outputs a one-line success message to stdout (becomes Claude context)

**Success output:**
```
analytics: ingested projects/claude-managed-agents — ok
```

**Fail-safe:** Silently ignores all errors. Analytics is a derived index — failures here never affect the pipeline. Exits 0 always.

---

## Settings Configuration

All hooks are registered in `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [
          {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/reinject-after-compact.sh\""},
          {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/portfolio-sweep.sh\""}
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/protect-generated-artifacts.sh\""}]
      },
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/prevent-unsafe-render.sh\""}]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/validate-project-json.sh\""},
          {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/brain-status.sh\""}
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/qa-analytics-ingest.sh\""}]
      }
    ]
  }
}
```

---

## Fail-Safe Policy

Every hook follows this contract:

| Situation | Behavior |
|---|---|
| Project cannot be found | Exit 0, print warning to stderr |
| `lib.brain` unavailable or crashes | Exit 0, print warning to stderr |
| File edit is unrelated to the hook's scope | Exit 0, no output |
| Bash command is unrelated to the hook's scope | Exit 0, no output |
| Analytics DB does not exist | Exit 0, no output |
| Hook output would be noisy with no value | Exit 0, no output |
| Gate is definitively not set AND project is confirmed | Exit 2 (block) — only `prevent-unsafe-render.sh` |

Hooks **never** edit project files, reset gates, or modify memory. They are read-only diagnostic signals.

---

## Extending Hooks

To add a new hook:

1. Create the script in `.claude/hooks/` — always include an early-exit guard at the top
2. Make it executable: `chmod +x .claude/hooks/new-hook.sh`
3. Add to `.claude/settings.json` with the appropriate event and matcher
4. Document it in this file

**Hook script template:**

```bash
#!/bin/bash
# new-hook.sh — [Event] hook for [Matcher]
# [One-sentence purpose.]
# Silent on all other [events/commands]. Fails safe.

INPUT=$(cat)

# [Extract relevant field]
RELEVANT=$(python -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('relevant_field', ''))
except Exception:
    print('')
" <<< "$INPUT" 2>/dev/null)

[ -z "$RELEVANT" ] && exit 0

# [Early-exit: check if this hook should fire]
case "$RELEVANT" in
  *"trigger_pattern"*) ;;
  *) exit 0 ;;
esac

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

# [Main logic — fail safe on every step]
RESULT=$(python -m lib.some_module "$RELEVANT" 2>/dev/null)
[ -z "$RESULT" ] && exit 0

echo "$RESULT"
exit 0
```
