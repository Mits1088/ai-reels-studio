#!/bin/bash
# portfolio-sweep.sh — SessionStart hook (compact matcher)
# Shows portfolio health summary after compact recovery.
#
# READ-ONLY: never edits files, never resets gates, never applies memory.
# Fails softly if projects/ is absent, lib.brain is unavailable, or Python errors.

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

# ── Repo guard ─────────────────────────────────────────────────────────────────
# Only run inside the AI Reels Studio workspace.
# Prevents noise when the hook fires in an unrelated repository.
[ -f "lib/brain/__init__.py" ] || exit 0
[ -d "projects" ] || exit 0

# ── Portfolio sweep (read-only) ────────────────────────────────────────────────
# Note: sweep exits 1 when any project is unhealthy — check for empty output,
# not exit code, so we show the summary exactly when projects need attention.
SWEEP_JSON=$(PYTHONPATH=. python -m lib.brain sweep projects/ --json 2>/dev/null)
[ -z "$SWEEP_JSON" ] && exit 0

# ── Render compact summary ─────────────────────────────────────────────────────
python -c '
import sys, json

try:
    summaries = json.load(sys.stdin)
except Exception:
    sys.exit(0)

if not summaries:
    print("AI Reels Brain: no projects found.")
    sys.exit(0)

total     = len(summaries)
blocked   = sum(
    1 for s in summaries
    if not s["healthy"] and not s["human_required"] and not s["can_continue"]
)
human_req = sum(1 for s in summaries if s["human_required"])
can_cont  = sum(1 for s in summaries if s["can_continue"])

print("AI Reels Brain portfolio status:")
print(f"  Projects: {total}")
print(f"  Blocked: {blocked}")
print(f"  Human approval needed: {human_req}")
print(f"  Can continue: {can_cont}")


def _tier(s):
    is_blocked = (
        not s["healthy"]
        and not s["human_required"]
        and not s["can_continue"]
    )
    if is_blocked:
        return 0
    if s["human_required"]:
        return 1
    if not s["healthy"] or s.get("stale_count", 0) > 0:
        return 2
    return 3


def _reason(s):
    if not s["healthy"] and not s["human_required"] and not s["can_continue"]:
        qa = s.get("qa_status", "not_run")
        return "QA fail" if qa in ("FAIL", "fail") else "blocked"
    if s["human_required"]:
        return "awaiting approval"
    if s.get("stale_count", 0) > 0:
        n = s["stale_count"]
        return f"{n} stale signal(s)"
    if s["can_continue"]:
        return "ready to advance"
    act = s.get("recommended_action", "check status")
    return (act[:40] + "...") if len(act) > 40 else act


# Top 5 needing attention (tier 0–2 only; tier 3 = fully healthy, skip)
attention = sorted(
    [s for s in summaries if _tier(s) < 3],
    key=_tier,
)[:5]

if attention:
    print("Top attention:")
    for i, s in enumerate(attention, 1):
        slug   = s["slug"]
        reason = _reason(s)
        print(
            f"  {i}. {slug} — {reason}"
            f" — run: python -m lib.brain repair projects/{slug}"
        )
' <<< "$SWEEP_JSON" 2>/dev/null

exit 0
