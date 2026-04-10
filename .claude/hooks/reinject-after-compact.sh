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
