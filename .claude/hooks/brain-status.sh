#!/bin/bash
# brain-status.sh — PostToolUse hook for Edit/Write
#
# Fires after editing a key pipeline state file inside a projects/ directory.
# Outputs a compact brain status so Claude stays oriented after making changes.
# Silent on unrelated edits.

INPUT=$(cat)

# Extract file path from tool input JSON
FILE_PATH=$(python -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('file_path', ''))
except Exception:
    print('')
" <<< "$INPUT" 2>/dev/null)

[ -z "$FILE_PATH" ] && exit 0

# Only trigger on key pipeline state files — ignore everything else
case "$FILE_PATH" in
  */project.json | \
  */output/timeline.json | \
  */output/qa_report.json | \
  */output/qa-report.md | \
  */output/motion-intent.md | \
  */shot-list.md | \
  */audio/beat-map.json | \
  */audio/captions.json)
    ;;
  *)
    exit 0
    ;;
esac

# Must be inside a projects/ directory
case "$FILE_PATH" in
  */projects/*) ;;
  *) exit 0 ;;
esac

# Walk up the path to find the project root (directory containing project.json)
PROJECT_DIR=$(python -c "
import sys, os
from pathlib import Path
p = Path('''$FILE_PATH''')
for candidate in [p.parent] + list(p.parents):
    if (candidate / 'project.json').exists():
        print(str(candidate))
        break
" 2>/dev/null)

[ -z "$PROJECT_DIR" ] && exit 0

# Change to workspace root before running brain
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

# Run brain diagnosis — fail silently if unavailable
DIAG=$(python -m lib.brain diagnose "$PROJECT_DIR" --json 2>/dev/null)
[ $? -ne 0 ] && exit 0
[ -z "$DIAG" ] && exit 0

# Extract fields
read -r SLUG PHASE GATES_PASSED GATES_TOTAL HEALTHY CAN_CONTINUE HUMAN_REQUIRED NEXT_ACTION STALE_HIGH QA_VERDICT <<< "$(python -c "
import sys, json
d = json.load(sys.stdin)
g = d.get('gates', {})
a = d.get('autonomy', {})
stale = [r for r in d.get('artifacts', {}).get('staleness_results', []) if r.get('confidence') == 'high']
qa = d.get('qa', {})
print(
    d.get('slug', '?'),
    d.get('phase', '?'),
    len(g.get('passed', [])),
    g.get('total', 11),
    '1' if d.get('healthy') else '0',
    '1' if a.get('can_continue_autonomously') else '0',
    '1' if a.get('human_required') else '0',
    a.get('next_action', '').replace(' ', '_'),
    len(stale),
    qa.get('verdict', 'not_run'),
)
" <<< "$DIAG" 2>/dev/null)"

[ -z "$SLUG" ] && exit 0

# ── Output compact status ──────────────────────────────────────────────────
NEXT_ACTION_READABLE=$(echo "$NEXT_ACTION" | tr '_' ' ')

echo "Brain status — $SLUG"
echo "  Phase: $PHASE  |  Gates: ${GATES_PASSED}/${GATES_TOTAL}  |  QA: $QA_VERDICT"

if [ "$HUMAN_REQUIRED" = "1" ]; then
  REASON=$(python -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('autonomy', {}).get('human_required_reason', ''))
" <<< "$DIAG" 2>/dev/null)
  echo "  ⏸  Waiting for Mits: $REASON"
elif [ "$CAN_CONTINUE" = "1" ]; then
  echo "  ▶  Safe to continue: $NEXT_ACTION_READABLE"
else
  echo "  ✗  Blocked: $NEXT_ACTION_READABLE"
  echo "     Run: PYTHONPATH=. python -m lib.validate $PROJECT_DIR"
fi

if [ "$STALE_HIGH" -gt "0" ] 2>/dev/null; then
  echo "  ⚠  ${STALE_HIGH} high-confidence staleness signal(s)"
  echo "     Run: PYTHONPATH=. python -m lib.brain diagnose $PROJECT_DIR for details"
fi

exit 0
