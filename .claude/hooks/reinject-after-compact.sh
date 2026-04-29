#!/bin/bash
# reinject-after-compact.sh — SessionStart hook (compact matcher)
# Re-injects critical project state after context compaction.
# stdout is added to Claude's context as a system reminder.

cat << 'CONTEXT'
CRITICAL CONTEXT (re-injected after compaction):

This is a reel production workspace. Key rules:
- Actual audio timing is the source of truth for all visual decisions
- QA must pass before render — never export until all blockers are cleared
- Every skill must pass gate checks before starting: run `python -m lib.phase check <skill> <project-dir>`
- project.json tracks gates_passed — check it before and update it after every phase
- All Remotion code changes require loading remotion-best-practices skill rules first
- Read component .tsx source before using any component in ReelComposition.tsx

Pipeline tools:
- Preflight:  python -m lib.phase check <skill> projects/<slug>
- Postflight: python -m lib.phase post <skill> projects/<slug>
- Health:     python -m lib.phase status projects/<slug>
- Validate:   python -m lib.validate projects/<slug>
- Gates:      python -m lib.gates status projects/<slug>
- Components: python -m lib.components check <Name>
CONTEXT

# ── Brain status after compaction ─────────────────────────────────────────
# Find the most recently active project and show its current state.
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

PROJECT_DIR=$(python -c "
import os, glob
from pathlib import Path
candidates = glob.glob('projects/*/project.json')
if not candidates:
    exit(1)
# Exclude _shared and _template
candidates = [p for p in candidates if not Path(p).parent.name.startswith('_')]
if not candidates:
    exit(1)
candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
print(str(Path(candidates[0]).parent))
" 2>/dev/null)

[ -z "$PROJECT_DIR" ] && exit 0

DIAG=$(python -m lib.brain diagnose "$PROJECT_DIR" --json 2>/dev/null)
[ -z "$DIAG" ] && exit 0

python -c "
import sys, json
d = json.load(sys.stdin)
g = d.get('gates', {})
a = d.get('autonomy', {})
stale = [r for r in d.get('artifacts', {}).get('staleness_results', []) if r.get('confidence') == 'high']
qa = d.get('qa', {})
slug = d.get('slug', '?')
phase = d.get('phase', '?')
gates_str = f\"{len(g.get('passed', []))}/{g.get('total', 11)}\"
healthy = '✓' if d.get('healthy') else '✗'
print(f'Active project: {slug}')
print(f'  Phase: {phase}  |  Gates: {gates_str}  |  Healthy: {healthy}  |  QA: {qa.get(\"verdict\",\"not_run\")}')
if a.get('human_required'):
    print(f'  ⏸  Waiting for approval: {a.get(\"human_required_reason\",\"\")}')
elif a.get('can_continue_autonomously'):
    print(f'  ▶  Next: {a.get(\"next_action\",\"\")}')
else:
    print(f'  ✗  Blocked — run: PYTHONPATH=. python -m lib.validate $PROJECT_DIR')
if stale:
    print(f'  ⚠  {len(stale)} high-confidence staleness signal(s) detected')
" <<< "$DIAG" 2>/dev/null

exit 0
