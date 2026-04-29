#!/bin/bash
# post-render-advance.sh — PostToolUse hook for Bash
#
# After a successful `npx remotion render` command (exit code 0), this hook:
#   1. Finds the active project
#   2. Sets phase=render, status=completed, rendered_at in project.json
#   3. Copies the rendered file reference into project.json (render_output)
#   4. Runs `python -m lib.brain repair` to advance the brain
#   5. Scaffolds output/learnings.md if it doesn't already exist
#   6. Prints a reminder to run feedback-capture and publish-prep
#
# Silent on all other Bash commands. Fails safe — all steps are best-effort.

INPUT=$(cat)

# Extract command and exit code
COMMAND=$(python -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('command', ''))
except Exception:
    print('')
" <<< "$INPUT" 2>/dev/null)

EXIT_CODE_FROM_HOOK=$(python -c "
import sys, json
try:
    d = json.load(sys.stdin)
    # PostToolUse result contains tool_response with exit_code
    resp = d.get('tool_response', {})
    # Claude Code puts exit code as integer in the response
    print(resp.get('exit_code', -1))
except Exception:
    print(-1)
" <<< "$INPUT" 2>/dev/null)

[ -z "$COMMAND" ] && exit 0

# Only trigger after remotion render commands
case "$COMMAND" in
  *"remotion render"*) ;;
  *) exit 0 ;;
esac

# Only act on success
if [ "$EXIT_CODE_FROM_HOOK" != "0" ]; then
  # Render failed — do not advance
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

# ── Find the active project ────────────────────────────────────────────────
PROJECT_DIR=$(python -c "
import os, glob, re, sys
from pathlib import Path

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

[ -z "$PROJECT_DIR" ] && exit 0

SLUG=$(basename "$PROJECT_DIR")

# ── Extract render output path from command ────────────────────────────────
RENDER_OUTPUT=$(python -c "
import re, sys
cmd = '''$COMMAND'''
m = re.search(r'--output\s+([\S]+)', cmd)
if m:
    out = m.group(1)
    # Strip remotion/ prefix if present, store as relative from project root
    import re as re2
    out = re2.sub(r'^remotion/', '', out)
    print(out)
else:
    print('out/reel.mp4')
" 2>/dev/null)

# ── Advance project.json ────────────────────────────────────────────────────
python -c "
import json, sys
from datetime import datetime, timezone
from pathlib import Path

pj_path = Path('$PROJECT_DIR/project.json')
try:
    pj = json.loads(pj_path.read_text(encoding='utf-8'))
except Exception as e:
    print(f'post-render: Could not read project.json: {e}', file=sys.stderr)
    sys.exit(0)

now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
changed = False

if pj.get('phase') != 'render':
    pj['phase'] = 'render'
    changed = True
if pj.get('status') != 'completed':
    pj['status'] = 'completed'
    changed = True
if 'rendered_at' not in pj:
    pj['rendered_at'] = now
    changed = True
if 'render_output' not in pj:
    pj['render_output'] = 'output/reel.mp4'
    changed = True
if changed:
    pj['updated'] = now
    pj_path.write_text(json.dumps(pj, indent=2), encoding='utf-8')
    print(f'post-render: project.json advanced to phase=render, status=completed')
else:
    print(f'post-render: project.json already at render/completed — no change needed')
" 2>/dev/null

# ── Run brain repair ───────────────────────────────────────────────────────
BRAIN_OUT=$(python -m lib.brain repair "$PROJECT_DIR" 2>&1)
BRAIN_EXIT=$?
if [ $BRAIN_EXIT -eq 0 ]; then
  echo "post-render: brain repair complete — $SLUG"
else
  echo "post-render: brain repair had warnings for $SLUG (check manually)"
fi

# ── Scaffold learnings.md if absent ────────────────────────────────────────
LEARNINGS_PATH="$PROJECT_DIR/output/learnings.md"
if [ ! -f "$LEARNINGS_PATH" ]; then
  DURATION=$(python -c "
import json
from pathlib import Path
try:
    pj = json.loads(Path('$PROJECT_DIR/project.json').read_text())
    print(pj.get('duration_s', '?'))
except:
    print('?')
" 2>/dev/null)
  STYLE=$(python -c "
import json
from pathlib import Path
try:
    pj = json.loads(Path('$PROJECT_DIR/project.json').read_text())
    print(pj.get('style', 'cinematic-presenter'))
except:
    print('cinematic-presenter')
" 2>/dev/null)
  TODAY=$(date +%Y-%m-%d 2>/dev/null || python -c "from datetime import date; print(date.today())")

  cat > "$LEARNINGS_PATH" << EOF
# Reel Learnings: $SLUG

**Rendered:** $TODAY
**Duration:** ${DURATION}s
**Style:** $STYLE
**Input quality:** [excellent / great / good / bad]
**Revision rounds:** [count]

---

## Hook

- Pattern: [cost tension / secret knowledge / result-first / number + outcome]
- First frame: [description]
- Revised: [yes/no — if yes, what changed]

---

## Proof

- Screenshots: [count]
- Demo videos: [count]
- Fitness blockers resolved: [count]
- Strongest proof moment: [description]

---

## Pacing

- Beats: [count]
- Visual changes: every [X]s average
- Avatar on-screen: [X]%
- QA pacing flags: [none / list]

---

## Technical

- Encoding issues: [none / list]
- Zoom approach: [auto / manual / vision-estimated]
- SFX count: [X]

---

## Repeat

[What worked well and should be repeated]

---

## Improve

[What would be done differently next time]
EOF
  echo "post-render: scaffolded $LEARNINGS_PATH — fill in details while fresh"
fi

# ── Reminder ───────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Render complete — $SLUG"
echo ""
echo "  Next steps (Phase 7b):"
echo "    1. Run publish-prep to generate Instagram caption"
echo "       (already done if caption.md exists in output/)"
echo "    2. Fill in output/learnings.md while details are fresh"
echo "    3. Watch the reel and run feedback-capture:"
echo "       python -m lib.brain feedback $PROJECT_DIR"
echo "    4. Upload output/reel.mp4 to Google Drive"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exit 0
