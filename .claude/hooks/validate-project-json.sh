#!/bin/bash
# validate-project-json.sh — PostToolUse hook
# Runs after any Edit/Write. Checks if the file was project.json,
# and if so, validates the project contract.
# stdout/stderr fed back to Claude as context.

INPUT=$(cat)
FILE_PATH=$(python -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" <<< "$INPUT" 2>/dev/null)

# Only validate project.json files
case "$FILE_PATH" in
  */project.json) ;;
  *) exit 0 ;;
esac

# Find the project directory (parent of project.json)
PROJECT_DIR=$(dirname "$FILE_PATH")

# Run validation
cd "$CLAUDE_PROJECT_DIR" || exit 0
RESULT=$(python -m lib.validate "$PROJECT_DIR" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  echo "project.json validation FAILED after edit:" >&2
  echo "$RESULT" >&2
  exit 2
fi

exit 0
