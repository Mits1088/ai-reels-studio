# project.json Lifecycle

Canonical reference for project state across the pipeline.
This document is the source of truth — schema, constants, and validation must match it.

## Schema Version

Current: `2`

Version history:
- `1` (implicit) — original schema, reel-only, no project_type, limited fields
- `2` — adds project_type, schema_version, reel metadata fields, youtube fields

## Project Types

### `reel` (default)

Instagram vertical reel. Full 15-phase pipeline with 11 gates.

### `youtube`

YouTube horizontal video with overlay annotations. Lightweight 2-phase pipeline with 2 gates.

## Field Inventory

### Required at creation (both types)

| Field | Type | Set by | Notes |
|-------|------|--------|-------|
| `schema_version` | integer | new-reel / youtube-ingest | Always `2` for new projects |
| `project_type` | string | new-reel / youtube-ingest | `"reel"` or `"youtube"` |
| `slug` | string | new-reel / youtube-ingest | URL-safe, matches directory name |
| `title` | string | new-reel / youtube-ingest | Human-readable project name |
| `phase` | string | new-reel / youtube-ingest | Current pipeline phase |
| `status` | string | new-reel / youtube-ingest | Status within current phase |
| `gates_passed` | array | new-reel / youtube-ingest | Always `[]` at creation |
| `created` | string | new-reel / youtube-ingest | ISO 8601 datetime |
| `updated` | string | new-reel / youtube-ingest | ISO 8601 datetime |

### Reel-only fields (set at creation with placeholders)

| Field | Type | Set by | Default |
|-------|------|--------|---------|
| `style` | string | new-reel | `"cinematic-presenter"` |
| `topic` | string | new-reel | From user input |
| `source_url` | string/null | new-reel | URL if source-first |
| `audience` | string | new-reel | From user input |
| `target_duration` | string | new-reel | e.g. `"30s"` |
| `hook_direction` | string | new-reel | From user input |
| `cta_direction` | string | new-reel | From user input |
| `content_type` | string | new-reel | e.g. "product-launch", "listicle" |
| `entry_path` | string | new-reel | "source-first", "topic-first", "script-first", "revision" |
| `series` | string/null | new-reel | null if not part of series |
| `trust_beat_likely` | boolean | new-reel | Whether trust beat is relevant |
| `input_quality` | string/null | new-reel | "excellent"/"great"/"good"/"bad"/null |
| `theme` | string/null | theme-factory | null until theme-factory runs |
| `theme_primary` | string/null | theme-factory | null until theme-factory runs |
| `theme_secondary` | string/null | theme-factory | null until theme-factory runs |

### Reel-only fields (set by later phases)

| Field | Type | Set by | Notes |
|-------|------|--------|-------|
| `voice_file` | string/null | ingest-voice | Path to audio relative to project dir |
| `duration_s` | number/null | ingest-voice | Actual duration in seconds |
| `avatar_file` | string/null | ingest-voice | Path to avatar video if HeyGen |
| `avatar_format` | string/null | asset-prep | e.g. "1080x1920 portrait" |
| `canonical_audio` | string/null | ingest-voice | e.g. "audio/source.wav" |

### YouTube-only fields (set at creation)

| Field | Type | Set by | Notes |
|-------|------|--------|-------|
| `duration` | number | youtube-ingest | Video duration in seconds |
| `fps` | integer | youtube-ingest | Video frame rate |
| `width` | integer | youtube-ingest | Output width (1920) |
| `height` | integer | youtube-ingest | Output height (1080) |
| `source_width` | integer/null | youtube-ingest | Original video width |
| `source_height` | integer/null | youtube-ingest | Original video height |
| `video_file` | string | youtube-ingest | Video filename in remotion/public/ |

## Valid Phases

### Reel phases
init, source-brief, theme, script, voice, reconcile, beat-map, captions,
capture, shot-list, motion-intent, asset-prep, assembly, preview, qa, render, done

### YouTube phases
init, ingest, overlay-plan, assembly, qa, render, done

## Valid Statuses (shared)

initialized, in_progress, awaiting_approval, approved, blocked, completed, failed

## Valid Gates

### Reel gates (11)
brief_approved, theme_set, script_approved, reconciliation_resolved,
visual_assignment_approved, asset_fitness_passed, technical_planning_approved,
motion_intent_reviewed, assets_validated, preview_passed, qa_passed

### YouTube gates (2)
video_ingested, overlay_plan_approved

## Migration

Projects with missing `schema_version` are version 1. Run `python -m lib.migrate`
to normalize to version 2. Migration adds missing required fields, normalizes
phase/status values, and infers gates from file evidence.
