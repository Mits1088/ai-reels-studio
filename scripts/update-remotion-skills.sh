#!/bin/bash
# update-remotion-skills.sh
#
# Fetches the official Remotion Claude Code skills from github.com/remotion-dev/skills
# and installs them into .claude/skills/remotion/.
#
# Run this whenever you want to pull the latest Remotion API guidance:
#   bash scripts/update-remotion-skills.sh
#
# How the two skills coexist:
#   .claude/skills/remotion/           ← Official Remotion skill (this script updates it)
#     SKILL.md                           40+ domain files: animations, audio, video,
#     animations.md                      lottie, fonts, transitions, etc.
#     ...
#
#   .claude/skills/remotion-best-practices/  ← Project-specific skill (hand-maintained)
#     SKILL.md                           Split-screen contract, SFX CDN rules, encoding
#                                        requirements, GuidedDemo protocol, edit modes.
#                                        PROJECT RULES TAKE PRECEDENCE over the official
#                                        skill when they conflict (e.g. OffthreadVideo
#                                        over <Video>, @sfx/ shorthand, -g 1 encoding).
#
# Update cadence: when Remotion releases a major version, run this script and check
# the diff for new rules or changed APIs worth incorporating into the project skill.

set -e

SKILLS_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude/skills/remotion"
REPO_URL="https://github.com/remotion-dev/skills"
VERSION_FILE="$SKILLS_DIR/.version"
TMP_DIR=$(mktemp -d)

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Updating Remotion Claude Code skills"
echo "  Source: $REPO_URL"
echo "  Target: $SKILLS_DIR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── Check git is available ─────────────────────────────────────────────────
if ! command -v git &>/dev/null; then
  echo "ERROR: git is required but not found."
  exit 1
fi

# ── Clone the skills repo into a temp directory ────────────────────────────
echo "Fetching from GitHub..."
git clone --quiet --depth 1 "$REPO_URL" "$TMP_DIR/skills" 2>&1

if [ $? -ne 0 ]; then
  echo "ERROR: Failed to clone $REPO_URL"
  echo "  Check network access and verify the repo exists."
  rm -rf "$TMP_DIR"
  exit 1
fi

# ── Find the remotion skill files ──────────────────────────────────────────
# The repo may have skills in a subdirectory (skills/remotion/) or at root
SKILL_SOURCE=""
if [ -d "$TMP_DIR/skills/remotion" ]; then
  SKILL_SOURCE="$TMP_DIR/skills/remotion"
elif [ -f "$TMP_DIR/skills/SKILL.md" ]; then
  SKILL_SOURCE="$TMP_DIR/skills"
else
  # Try to find any SKILL.md
  SKILL_SOURCE=$(find "$TMP_DIR/skills" -name "SKILL.md" -printf "%h\n" | head -1)
fi

if [ -z "$SKILL_SOURCE" ] || [ ! -d "$SKILL_SOURCE" ]; then
  echo "ERROR: Could not find Remotion skill files in cloned repo."
  echo "  Repo structure:"
  ls "$TMP_DIR/skills/" 2>/dev/null || echo "  (empty)"
  rm -rf "$TMP_DIR"
  exit 1
fi

# ── Record what we're replacing ────────────────────────────────────────────
PREVIOUS_VERSION="(not installed)"
if [ -f "$VERSION_FILE" ]; then
  PREVIOUS_VERSION=$(cat "$VERSION_FILE")
fi

CURRENT_COMMIT=$(git -C "$TMP_DIR/skills" rev-parse HEAD 2>/dev/null || echo "unknown")
CURRENT_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || python -c "from datetime import datetime,timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))")

# ── Install: copy skill files to target ───────────────────────────────────
mkdir -p "$SKILLS_DIR"

# Count files before
FILES_BEFORE=$(ls "$SKILLS_DIR"/*.md 2>/dev/null | wc -l || echo 0)

# Copy all .md files from the skill source
cp "$SKILL_SOURCE"/*.md "$SKILLS_DIR/" 2>/dev/null || true

# Copy any subdirectory structure if it exists
if ls "$SKILL_SOURCE"/*/ &>/dev/null 2>&1; then
  cp -r "$SKILL_SOURCE"/*/  "$SKILLS_DIR/" 2>/dev/null || true
fi

# Count files after
FILES_AFTER=$(ls "$SKILLS_DIR"/*.md 2>/dev/null | wc -l || echo 0)

# ── Write version record ───────────────────────────────────────────────────
cat > "$VERSION_FILE" << EOF
commit: $CURRENT_COMMIT
updated: $CURRENT_DATE
source: $REPO_URL
previous: $PREVIOUS_VERSION
EOF

# ── Write a precedence note at the bottom of SKILL.md ─────────────────────
# Only add if not already present
if [ -f "$SKILLS_DIR/SKILL.md" ] && ! grep -q "Project Override Note" "$SKILLS_DIR/SKILL.md"; then
  cat >> "$SKILLS_DIR/SKILL.md" << 'EOF'

---

## Project Override Note

This is the official Remotion skill (auto-updated from remotion-dev/skills).

For this project, also load `.claude/skills/remotion-best-practices/SKILL.md` which contains
project-specific rules. When rules conflict, the project skill takes precedence:

| Topic | This skill | Project skill (wins) |
|---|---|---|
| Video component | `<Video>` from @remotion/media | `<OffthreadVideo>` — frame-accurate |
| SFX | Local file approach | `@sfx/` CDN shorthand |
| Video encoding | General guidance | `-g 1` keyframe + faststart + yuv420p required |
| Math.random() | May not cover | Banned — use `random('seed')` from remotion |
| interpolate() | May vary | Both extrapolateLeft AND extrapolateRight: "clamp" |
EOF
fi

# ── Cleanup ─────────────────────────────────────────────────────────────────
rm -rf "$TMP_DIR"

# ── Summary ────────────────────────────────────────────────────────────────
echo "Done."
echo ""
echo "  Skill files: $FILES_AFTER .md files in $SKILLS_DIR"
echo "  Commit:      $CURRENT_COMMIT"
echo "  Updated:     $CURRENT_DATE"
echo ""

if [ "$CURRENT_COMMIT" != "$(echo "$PREVIOUS_VERSION" | grep 'commit:' | cut -d' ' -f2)" ]; then
  echo "  CHANGED from previous version."
  echo "  Review the diff and check for new rules to incorporate:"
  echo "    cat $SKILLS_DIR/SKILL.md"
  echo ""
  echo "  Key things to check after an update:"
  echo "    - New packages or APIs added to Remotion"
  echo "    - Deprecated patterns (e.g. <Video> → OffthreadVideo changes)"
  echo "    - New animation primitives or hooks"
  echo "    - Changes to interpolate/spring behavior"
else
  echo "  No change — already at latest commit."
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
