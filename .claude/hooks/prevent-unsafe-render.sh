#!/bin/bash
# prevent-unsafe-render.sh — PreToolUse hook for Bash
#
# Blocks any `remotion render` command if the active project's qa_passed
# gate is not set. Silent on all other Bash commands.
# Fails safely (warns but allows) if the project cannot be determined.

INPUT=$(cat)

# Extract the bash command
COMMAND=$(python -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('command', ''))
except Exception:
    print('')
" <<< "$INPUT" 2>/dev/null)

[ -z "$COMMAND" ] && exit 0

# Only intercept render commands — ignore everything else
case "$COMMAND" in
  *"remotion render"*)
    ;;
  *)
    exit 0
    ;;
esac

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

# ── Find the active project ────────────────────────────────────────────────
# 1. Check if the command names a project dir explicitly
# 2. Fall back to most recently modified project.json

PROJECT_DIR=$(python -c "
import os, glob, re, sys
from pathlib import Path

# Try to extract a project slug from the command
cmd = '''$COMMAND'''
m = re.search(r'projects/([\w-]+)', cmd)
if m:
    candidate = Path('projects') / m.group(1)
    if (candidate / 'project.json').exists():
        print(str(candidate))
        sys.exit(0)

# Fall back to most recently modified project.json
candidates = glob.glob('projects/*/project.json')
if not candidates:
    sys.exit(1)
candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
print(str(Path(candidates[0]).parent))
" 2>/dev/null)

if [ -z "$PROJECT_DIR" ]; then
  echo "" >&2
  echo "render-guard: Could not determine active project." >&2
  echo "  Manually verify qa_passed is set before rendering:" >&2
  echo "  PYTHONPATH=. python -m lib.gates status projects/<slug>" >&2
  echo "" >&2
  # Warn but allow — fail safe, do not block on unknown project
  exit 0
fi

# ── Run brain diagnosis ────────────────────────────────────────────────────
DIAG=$(python -m lib.brain diagnose "$PROJECT_DIR" --json 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$DIAG" ]; then
  echo "" >&2
  echo "render-guard: Brain diagnosis unavailable for $PROJECT_DIR." >&2
  echo "  Manually verify before rendering:" >&2
  echo "  PYTHONPATH=. python -m lib.gates status $PROJECT_DIR" >&2
  echo "" >&2
  # Warn but allow — do not block on diagnosis failure
  exit 0
fi

# ── Check qa_passed gate ───────────────────────────────────────────────────
read -r SLUG QA_PASSED QA_VERDICT GATES_PASSED GATES_TOTAL <<< "$(python -c "
import sys, json
d = json.load(sys.stdin)
g = d.get('gates', {})
passed = g.get('passed', [])
print(
    d.get('slug', '?'),
    '1' if 'qa_passed' in passed else '0',
    d.get('qa', {}).get('verdict', 'not_run'),
    len(passed),
    g.get('total', 11),
)
" <<< "$DIAG" 2>/dev/null)"

if [ "$QA_PASSED" = "0" ]; then
  # ── BLOCK ─────────────────────────────────────────────────────────────────
  echo "" >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  echo "  RENDER BLOCKED — qa_passed gate not set" >&2
  echo "" >&2
  echo "  Project:    $SLUG" >&2
  echo "  Gates:      ${GATES_PASSED}/${GATES_TOTAL}" >&2
  echo "  QA verdict: $QA_VERDICT" >&2
  echo "" >&2
  echo "  Run QA first:" >&2
  echo "    PYTHONPATH=. python -m lib.qa.cli $PROJECT_DIR" >&2
  echo "" >&2
  echo "  Then check gates:" >&2
  echo "    PYTHONPATH=. python -m lib.gates status $PROJECT_DIR" >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  exit 2
fi

# ── QA passed — allow render, confirm in stderr ────────────────────────────
echo "render-guard: qa_passed confirmed for $SLUG (QA: $QA_VERDICT, ${GATES_PASSED}/${GATES_TOTAL} gates). Render allowed." >&2
exit 0
