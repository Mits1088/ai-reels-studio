# Changelog

All notable changes to the AI Reels Studio pipeline.

---

## [2026-04-05b] — Programmatic Pipeline Enforcement

Turned documented rules into running code. Gate enforcement, validation, QA, and learning capture now have real CLI-callable modules instead of relying solely on Claude reading markdown.

### Added

**`lib/constants.py` — Shared enum source of truth**
- Single import for all modules: 17 phases, 7 statuses, 2 styles, 11 gate IDs, gate order
- Prevents enum drift between validate.py, gates.py, and runner.py

**`lib/gates.py` — Programmatic gate enforcement (from ruflo's DeterministicToolGateway)**
- `check <project> <skill>` — verifies gates + files before a skill can run
- `set <project> <gate-id>` — marks a gate as passed
- `reset <project> <gate-id>` — cascading reset: removes gate + all downstream gates
- `status <project>` — shows `[x]`/`[ ]` checklist for all 11 gates
- Full skill-to-gate mapping coded as data (18 skills including sub-phase variants)
- Claude calls these commands during skill execution — operator doesn't run them manually

**8 new QA checks in `lib/qa/checks.py` (10 → 18 total)**
- `check_avatar_absence` — flags gaps >12s (cinematic) or >8s (editorial), style-aware
- `check_center_full_streak` — flags >4 consecutive center-full entries
- `check_sfx_coverage` — validates SFX count against duration-based minimums per style
- `check_video_encoding` — ffprobe validation: h264, 30fps, yuv420p, audio track
- `check_screenshot_hold` — flags static images >2s without zoom_moments
- `check_flash_budget` — enforces per-style punch/flash accent limits
- `check_style_compliance` — editorial-authority specific checks (proof-protected, no kenBurns)
- `check_overlay_positioning` — ensures overlays centered, fontSize >= 64

**`lib/learn.py` — Reel learning capture (from ruflo's SONA self-learning)**
- `capture <project>` — auto-generates `output/learnings.md` from project artifacts
- `compare <project>` — finds similar completed projects and shows their learnings
- Computes: duration, beat count, SFX count, screenshot count, avatar %, visual frequency
- Leaves `(fill in)` placeholders for subjective assessment
- First learnings.md ever generated: `google-stitch-vibe-design`

**`lib/migrate.py` — Project migration tool**
- Normalizes all 14 existing projects to current schema
- Fixes: old phase names (numeric, compound strings), old status values, missing fields
- Infers `gates_passed` from file existence (conservative — only infers what files prove)
- `--dry-run` mode for safe preview before applying

### Changed

**`lib/validate.py` — Synced with actual schema**
- Phase enum: 7 → 17 (was missing: init, source-brief, theme, reconcile, beat-map, captions, capture, shot-list, motion-intent, asset-prep, preview, render)
- Status enum: 6 old values → 7 current values (was: initialized/voice_ready/assets_ready/assembled/qa_passed/qa_failed → now: initialized/in_progress/awaiting_approval/approved/blocked/completed/failed)
- Beat ID regex: now allows sub-beats (`beat-01a`, `beat-03b`)
- New validations: `style` field, `gates_passed` array (valid IDs only), theme consistency (theme_set gate requires non-null theme fields), color hex format

**`lib/qa/runner.py` — Expanded and corrected**
- Gate registry expanded from 3-param to 6-param signature (adds project, style, video probes)
- `_probe_videos()` — runs ffprobe on all videos in remotion/public/
- QA pass now auto-sets `qa_passed` in `gates_passed` (was: only set old status value)
- QA fail now removes `qa_passed` from `gates_passed` and sets status to `failed`
- Status values corrected: `qa_passed` → `completed`, `qa_failed` → `failed`

**`RUNBOOK.md` — Full rewrite**
- Added: all missing phases (2b, 3b, 3c, 4c, 4d, 5b)
- Added: Gate Enforcement section with 11-gate table and CLI commands
- Added: Reel Learning section
- Added: Project Migration section
- Added: gate/migration/encoding troubleshooting
- Updated: CLI Reference with all new commands
- Updated: File Reference with learnings.md, reconciliation.md, motion-intent.md

**`templates/example-project/project.json` — Fixed old status**
- `"status": "qa_passed"` → `"status": "completed"`

### Test Results
- 88 tests passing (38 contract + 50 QA)
- 8 new test cases for gates, style, theme, color, sub-beat validation
- All test fixtures updated from old to current enum values

### Updated Files
- `lib/constants.py` — new file
- `lib/validate.py` — enum sync, new validations
- `lib/test_contracts.py` — fixture fixes, new tests
- `lib/gates.py` — new file
- `lib/qa/checks.py` — 8 new checks
- `lib/qa/runner.py` — expanded signature, gate setting, video probing
- `lib/qa/test_qa.py` — fixture fixes
- `lib/learn.py` — new file
- `lib/migrate.py` — new file
- `RUNBOOK.md` — full rewrite
- `templates/example-project/project.json` — status fix

---

## [2026-04-05] — 5 New Skills, Parallelization, Automated Vision, Pipeline Hardening

### Added

**5 New Skills (15 total — every phase now has skill backing)**
- `shot-list` (Phase 4b) — orchestrates visual assignment, component mapping, asset fitness audit, and technical planning into a single approved document with 3 internal approval gates
- `motion-intent` (Phase 4c) — beat-by-beat motion direction with exact Remotion preset mapping, gap ownership, background seam transitions, flash budget enforcement
- `caption-polish` (Phase 3b) — product name spelling correction, chunk splitting for mobile readability, emphasis word tagging, ElevenLabs `--` artifact stripping
- `script-reconcile` (Phase 2b) — word-by-word diff of approved script vs actual transcript, severity classification (Low/Medium/High/Critical), locks source of truth for all downstream phases
- `asset-prep` (Phase 4d) — browser chrome cropping, video re-encoding to Remotion spec (libx264/yuv420p/30fps/-g 1/faststart), playback rate calculation, ffprobe validation, frame extraction and visual verification

**Input Quality Diagnostic (in new-reel skill)**
- Scores user input on 8 elements (source, angle, audience, duration, style, scope boundaries, hook, proof methods)
- Classifies as Excellent (6-8) / Great (4-5) / Good (2-3) / Bad (1)
- Blocks bad inputs from initializing full projects — helps user narrow first
- Records `input_quality` in project.json

**Input Quality Guide**
- `training/input-quality-guide.md` — comprehensive reference with real project examples
- Cascade effect analysis showing how input quality multiplies through 11 phases
- Excellent/Great/Good/Bad examples drawn from google-stitch, chatgpt-secret-codes, claude-cowork, google-little-language-lessons
- The 8-element checklist, decision tree, and proof test

**URL Type Classification (in source-brief skill)**
- YouTube: transcript extraction from captions, chapter markers as beat boundaries, thumbnail as hook visual, key frame extraction
- Research papers: abstract, figures/tables, benchmark charts, citation as credibility proof
- Social posts: treated as signal not source, follow linked URLs, post as credibility screenshot
- Blog posts, product pages, GitHub repos, newsletters: standard handling with specific extraction strategies

**Automated Vision Analysis**
- shot-list Phase 4b-ii: reads each asset image via Read tool, visually verifies content matches narration, scores fitness based on actual image contents (not filename)
- shot-list Phase 4b-iii: reads each screenshot, identifies focal UI element, estimates x%/y% position, applies letterbox formula, writes zoom coordinates automatically
- asset-prep Phase 4d: extracts frame from every processed video, reads it via Read tool, checks for personal data, browser chrome, narrative mismatch

**4 Parallel Execution Windows**
- Window 1: Phase 0 (source-brief) + Phase 0b (theme-factory)
- Window 2: Phase 1b (b-roll classify) + Phase 2 (voice ingest)
- Window 3: Phase 3b (caption polish) + Phase 3c (demo config) + Phase 4 (capture)
- Window 4: Phase 4c (motion intent) + Phase 4d (asset prep)

### Changed

**Approval Gates: 8 → 11**
- Added: Phase 0 (brief approved), Phase 0b (theme mandatory), Phase 2b (reconciliation resolved), Phase 4b-iii (technical planning approved)
- Both CLAUDE.md and reel-workflow.md now list identical 11-gate sequence with phase numbers
- Theme selection changed from "if applicable" to mandatory — cannot proceed to reel-script without theme fields populated

**Schema Updates**
- `project.schema.json`: added `input_quality` field with enum (excellent/great/good/bad)
- `project.schema.json`: theme field documented as mandatory-by-workflow-gate

**Component References Fixed**
- `StackedImageReveal`: flagged as NOT YET BUILT in visual-style.md, component-mapping.md, assemble-reel SKILL.md — workaround: multiple FramedImage entries in rapid sequence
- `ImageMontage`: flagged as NOT YET BUILT in component-mapping.md — same workaround

**Gate Harmonization**
- CLAUDE.md and reel-workflow.md now use identical language for all 11 gates
- Quick preview gate (Phase 5b) added to CLAUDE.md (was only in reel-workflow.md)
- Brief approval gate added to reel-workflow.md (was only in CLAUDE.md)

### Updated Files
- `CLAUDE.md` — workflow order with parallel windows, 15-skill table, 11 gates, project structure tree
- `.claude/rules/reel-workflow.md` — skill references for 2b/3b/4b-i/4c/4d, 11-gate list, parallel notation
- `.claude/rules/component-mapping.md` — ImageMontage and StackedImageReveal flagged as unbuilt
- `.claude/rules/visual-style.md` — StackedImageReveal flagged as unbuilt with workaround
- `.claude/skills/new-reel/SKILL.md` — input quality diagnostic, link to training guide
- `.claude/skills/source-brief/SKILL.md` — URL type classification (YouTube, papers, social, etc.)
- `.claude/skills/shot-list/SKILL.md` — automated vision for fitness audit and zoom coordinates
- `.claude/skills/assemble-reel/SKILL.md` — StackedImageReveal flagged as unbuilt
- `.claude/skills/asset-prep/SKILL.md` — new skill (Phase 4d)
- `.claude/skills/script-reconcile/SKILL.md` — new skill (Phase 2b)
- `.claude/skills/motion-intent/SKILL.md` — new skill (Phase 4c)
- `.claude/skills/caption-polish/SKILL.md` — new skill (Phase 3b)
- `lib/schemas/project.schema.json` — input_quality field, theme documentation
- `training/input-quality-guide.md` — comprehensive input quality reference

**Patterns Extracted from ruflo (ruvnet/ruflo)**

Two architectural patterns adapted from ruflo's enterprise AI orchestration platform, sized for single-operator reel pipeline:

- `.claude/rules/gate-enforcement.md` — Deterministic gate checks (adapted from ruflo's DeterministicToolGateway). Every skill validates preconditions against `gates_passed` array in project.json before starting. Prevents out-of-order execution, tracks gate completion across sessions, handles parallel phase join points.
- `.claude/rules/reel-learning.md` — Post-render learning capture (adapted from ruflo's SONA self-learning). After successful render, captures what worked (hook pattern, proof strategy, pacing, technical patterns) in `output/learnings.md`. Future reels check similar completed projects for reusable patterns.
- `project.schema.json` updated: `phase` enum expanded from 7 to 17 granular phases, `status` enum expanded to track in_progress/awaiting_approval/approved/blocked, new `gates_passed` array tracks cleared gates
- Rule hierarchy updated: gate-enforcement at position 2 (high priority), reel-learning at position 10

### Evaluated & Rejected External Repos
- `supercent-io/skills-template` (remotion-video-production) — already installed at remotion/.agents/skills/remotion-best-practices/
- `inferen-sh/skills` (remotion-render) — cloud CPU rendering slower than local GPU, adds cost, same rule files already present
- `jina-ai/reader` — marginal text extraction improvement, doesn't solve YouTube transcripts
- `ruvnet/ruflo` — enterprise 100+ agent orchestration platform; too heavy to install, but 2 patterns extracted (gate enforcement, reel learning)

### NotebookLM Cinematic B-Roll Integration
- Installed `notebooklm-py` v0.3.4 — Python library for programmatic NotebookLM access
- `broll-pipeline` skill rewritten with proper YAML frontmatter and new Phase 0: cinematic video generation
- B-roll decision gate added — system must ASK user before generating b-roll (never assume)
- Auto-generated customization prompt from `brief.md` (topic, proof promise, support points, audience, scope boundaries)
- NotebookLM cinematic styles supported: classic, whiteboard, anime, retro, watercolor, auto
- Two source options: Option A (generate via notebooklm-py from URL) or Option B (user-provided footage)
- Generation takes 5-30 minutes — designed to run in background during parallel window 2
- `reel-workflow.md` Phase 1b updated to reference notebooklm-py and the decision gate
- Risk documented: reverse-engineered API, may break if Google changes endpoints

### Post-Audit Fixes
- `gate-enforcement.md` wired into pipeline via `reel-workflow.md` (no longer orphaned — all 10 skills that read reel-workflow.md now inherit gate enforcement)
- `remotion-skill-required.md` wired into `assemble-reel` Global Rule References (no longer orphaned)
- `project.schema.json`: removed unused `brand` and `template` fields; documented writer/reader for every remaining field; `voice_file` and `duration_s` documented with downstream consumers
- `beat_map.schema.json`: `visual_intent` changed from required to optional (ingest-voice may not produce it for ambient/silence beats)
- `gate-enforcement.md`: added `frontend-design` to skill-to-gate mapping table
- All 15 skills verified in CLAUDE.md skill table
- broll lane confirmed as intentionally optional in timeline schema (not every reel uses b-roll)

---

## [2026-04-03] — Dual Style System + Component Mapping Pipeline

### Added

**Style System**
- Dual style profiles: `cinematic-presenter` (default) and `editorial-authority` (new)
- `.claude/rules/style-profiles.md` — master style selector
- `styles/cinematic-presenter.md` — documented existing style as named profile
- `styles/editorial-authority.md` — full spec for fast-paced editorial style
- `styles/editorial-authority-components.md` — component build spec
- `style` field in `project.schema.json` — selectable per project

**New Remotion Components (8)**
- `HeroTextCard` — giant center-weighted text on solid background (P0)
- `FlashReset` — 2-3 frame white flash section divider (P0)
- `OverlayKeyword` — large text overlaid on avatar with optional strikethrough (P1)
- `ComparisonGrid` — side-by-side screenshots with VS divider (P1)
- `CursorClick` — cursor arrow with click ripple animation (P1)
- `AnnotationCircle` — hand-drawn SVG circle for UI callouts (P2)
- `ChapterDivider` — logo + wordmark on solid background (P2)
- `ScrollingIconGrid` — rotated multi-row grid of app logo cards, scrolls diagonally (hook backgrounds)

**New Transition Presets (4)**
- `hard-cut` — instant appear/disappear (0 frames)
- `scale-pop-overshoot` — 0.85 → 1.03 → 1.0 spring settle
- `flash-reset` — pairs with FlashReset component
- `slide-stack` — translateX + rotation for card stacking

**Component Mapping System (Phase 4b-ii)**
- `.claude/rules/component-mapping.md` — narration-to-component decision guide
- Narration classification system (15 types: keyword, claim, name reveal, etc.)
- Style-specific component selection tables
- Asset fitness audit (MATCH/PARTIAL/MISMATCH/MISSING scoring)
- Flow validation checklist

**Theme Factory Integration (Phase 0b)**
- Theme selection now a formal workflow phase after source-brief
- `theme`, `theme_primary`, `theme_secondary` fields in project.schema.json
- Theme values drive component colors during assembly
- QA audits theme consistency

**Frontend Design Integration**
- Wired into component-mapping Step 2 (design quality check)
- Wired into assemble-reel (pause if component looks generic)
- Wired into qa-reel (visual distinctiveness audit)

**B-Roll Pipeline Hand-off**
- Phase 4b-i now explicitly reads `broll_scenes/scene_list.json` classification data
- Match by editorial intent, not just visual similarity

### Changed

**Workflow Phases**
- Phase 4b split into 4b-i (visual assignment), 4b-ii (component mapping + asset fitness), 4b-iii (technical planning)
- Phase 0b added (theme selection)
- New approval gates: visual assignment → component mapping → technical planning
- MISMATCH or MISSING asset fitness = blocker

**CardStack Component**
- Added `variant` prop: `"cinematic"` (default) or `"editorial"` (white bg, number badges, rotation)

**TransitionWrapper**
- Added enter cases: hard-cut, scale-pop-overshoot, flash-reset, slide-stack
- Added exit case: hard-cut

**types.ts**
- TransitionPreset union extended with new preset types

**timeline.schema.json**
- Enter/exit preset enums extended

**Editorial-Authority Style (Lindsay.ai Reference)**
- Avatar on-screen target raised from 30-45% to 45-55%
- Text overlays ON avatar instead of replacing avatar (OverlayKeyword, not HeroTextCard)
- Hook uses split-screen: ScrollingIconGrid top + avatar bottom
- Split-screen IS used in editorial-authority (hook, proof with narration)
- Warm light-leak transition near CTA
- Avatar absence limit reduced from 18s to 12s

### Updated Files
- `CLAUDE.md` — workflow order, rule hierarchy, component inventory, style profiles section
- `.claude/rules/reel-workflow.md` — Phase 0b, 4b-ii, 4b-iii, broll hand-off
- `.claude/rules/visual-style.md` — style profiles header
- `.claude/rules/qa-gates.md` — style-aware thresholds table
- `.claude/skills/new-reel/SKILL.md` — style selection, theme fields, shot-list template
- `.claude/skills/reel-script/SKILL.md` — style-aware scripting guidance
- `.claude/skills/assemble-reel/SKILL.md` — style defaults table, component mapping precondition, design quality reference, theme reference
- `.claude/skills/qa-reel/SKILL.md` — style-aware thresholds, design quality audit, theme consistency audit
- `lib/schemas/project.schema.json` — style and theme fields
- `lib/schemas/timeline.schema.json` — new transition presets

### Test Project
- `projects/google-turboquant` — switched to editorial-authority style, fully assembled with new components

---

## [2026-03-24] — ChatGPT Secret Codes Reel

### Completed
- 48s listicle reel on 4 ChatGPT codes
- Code-only typing demo approach
- Rendered successfully

---

## [2026-03-19] — Google Little Language Lessons Reel

### Completed
- v9 rendered
- Claude-driven b-roll pipeline
- Center-full demos
- Layout flow pattern documented

---

## [Pre-2026-03-19] — Initial Pipeline

### Built
- Full reel production pipeline: source-brief → reel-script → ingest-voice → capture-demo → shot-list → assemble-reel → qa-reel → render
- Remotion composition engine (ReelComposition.tsx)
- 30+ Remotion components
- Beat map, caption, timeline schemas
- SFX library
- Demo capture 3-stage fallback chain
- QA gate system
