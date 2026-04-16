#!/usr/bin/env bash
# scripts/validate-orchestrator.sh — Run orchestrator validation suite
#
# Usage:
#   bash scripts/validate-orchestrator.sh           # quiet summary
#   bash scripts/validate-orchestrator.sh -v        # verbose
#   bash scripts/validate-orchestrator.sh --runner  # test_runner.py only
#   bash scripts/validate-orchestrator.sh --cli     # test_cli.py only

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

VERBOSE=""
FILTER="tests/orchestrator"

for arg in "$@"; do
  case "$arg" in
    -v|--verbose) VERBOSE="-v" ;;
    --runner)     FILTER="tests/orchestrator/test_runner.py" ;;
    --cli)        FILTER="tests/orchestrator/test_cli.py" ;;
  esac
done

echo "═══════════════════════════════════════════════════════"
echo "  Orchestrator Validation Suite"
echo "  Target: $FILTER"
echo "═══════════════════════════════════════════════════════"
echo ""

python -m pytest "$FILTER" $VERBOSE --tb=short 2>&1

EXIT_CODE=$?
echo ""
if [ $EXIT_CODE -eq 0 ]; then
  echo "  ✓  All orchestrator tests passed."
else
  echo "  ✗  Some tests failed. See output above."
fi
echo "═══════════════════════════════════════════════════════"
exit $EXIT_CODE
