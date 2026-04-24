#!/bin/bash
# qa-analytics-ingest.sh — PostToolUse hook for Bash
#
# After a successful QA run (python -m lib.qa.cli), ingests the project
# into data/analytics.db if the analytics layer exists.
# Silent on all other Bash commands. Silent if analytics DB is absent.
# Fails safe — analytics ingest is best-effort and non-blocking.

INPUT=$(cat)

# Extract command
COMMAND=$(python -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('command', ''))
except Exception:
    print('')
" <<< "$INPUT" 2>/dev/null)

[ -z "$COMMAND" ] && exit 0

# Only trigger after QA CLI runs
case "$COMMAND" in
  *"lib.qa.cli"*) ;;
  *) exit 0 ;;
esac

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

# Analytics DB must exist — this feature is entirely opt-in
[ ! -f "data/analytics.db" ] && exit 0

# Extract project dir from the command
# Format: python -m lib.qa.cli projects/<slug> [options]
PROJECT_DIR=$(python -c "
import sys, re
from pathlib import Path
cmd = '''$COMMAND'''
m = re.search(r'(projects/[\w-]+)', cmd)
if m:
    p = Path(m.group(1))
    if p.is_dir() and (p / 'project.json').exists():
        print(str(p))
" 2>/dev/null)

[ -z "$PROJECT_DIR" ] && exit 0

# Ingest — output goes to stdout so Claude sees it as context
RESULT=$(python -m lib.analytics ingest "$PROJECT_DIR" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "analytics: ingested $PROJECT_DIR — $RESULT"
fi
# Silently ignore ingest errors — analytics is non-critical
exit 0
