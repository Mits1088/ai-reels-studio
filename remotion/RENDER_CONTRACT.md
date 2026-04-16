# Render Contract

The minimum stable `timeline.json` contract that `GenericReelComposition.tsx` can consume.
This is the handoff between the planning pipeline and the renderer.

## Required top-level fields

| Field | Type | Source |
|---|---|---|
| `total_duration` | number (seconds) | ingest-voice |
| `audio` | string (filename in public/) | ingest-voice |
| `avatar_file` | string (filename in public/) | asset-prep |
| `lanes` | object | assemble-reel |

## Required lanes

| Lane | Entries | Drives |
|---|---|---|
| `avatar` | TimelineEntry[] | Avatar video visibility, layout switching |
| `demo` | TimelineEntry[] | Static images in split-screen with zoom |
| `broll` | TimelineEntry[] | Video clips, center-full or split |
| `captions` | TimelineEntry[] | Bottom caption text |
| `sfx` | TimelineEntry[] | Sound effect audio clips |
| `overlays` | OverlayEntry[] | Text overlays, badges, keywords |

## Optional lanes

| Lane | Entries | Drives |
|---|---|---|
| `support` | TimelineEntry[] | Additional images/videos |
| `music` | TimelineEntry[] | Background music |

## TimelineEntry (visual lanes: avatar, demo, broll, support)

| Field | Required | Type | Notes |
|---|---|---|---|
| `start` | yes | number | Seconds |
| `end` | yes | number | Seconds |
| `beat_id` | yes | string | Links to beat-map |
| `asset` | for demo/broll/support | string | Filename in public/ |
| `layout` | for avatar | string | `"full-screen"` or `"split-screen"` |
| `display` | no | string | `"center-full"` or omit for split-screen default |
| `transition_preset` | no | object | `{ enter, exit, enterDur, exitDur }` |
| `zoom_moments` | no | array | `[{ at, x, y, scale, holdFor }]` |
| `playbackRate` | no | number | Speed multiplier for video |
| `clipStartTime` | no | number | Trim start in seconds |
| `notes` | no | string | Editorial notes (ignored by renderer) |

## TimelineEntry — editorial planning fields (Phase C)

These fields are written by the edit-plan compiler (`lib/edit_plan/compile.py`)
so the rendered timeline carries its template + proof + caption-mode context.
**Phase C update:** they are now formally enumerated in
`lib/schemas/timeline.schema.json` (under `$defs.visual_lane.properties`)
alongside the existing render-hint fields. The compiler attaches them only
when invoked with `attach_planning_fields=True`. `GenericReelComposition`
still does not consume them at runtime — they are pure metadata for
downstream tooling (critic in Phase E, learning in Phase F, retrieval).

| Field | Type | Source | Notes |
|---|---|---|---|
| `template_id` | string | edit-plan | Layout template id from `training/derived/template-registry.json` |
| `proof_class` | string | edit-plan | One of: `existence`, `breadth`, `process`, `output`, `integration`, `authority`, `cta` |
| `avatar_mode` | string | edit-plan | Free-form descriptor (`"full-screen, clean"`, `"visible, bottom 35%"`, ...) |
| `splitRatio` | string | edit-plan | E.g. `"40/60"`, `"65/35"`, `"100/0"`, `"50/50"`, `"0/100"` |
| `captionMode` | string | edit-plan | One of: `standard`, `headline`, `suppressed`, `section-label`, `badge-overlay` |
| `proof_protected` | boolean | edit-plan | `true` for beats whose proof asset must not be substituted with b-roll (already read by `lib/qa/checks.py:check_style_compliance`) |

The `lib/grammar/` package is the runtime source of truth for the
`proof_class` and `captionMode` enums. `lib/test_contracts.py` enforces
drift detection between the Python grammar, the new
`lib/schemas/edit_plan.schema.json`, and this contract.

## OverlayEntry (overlays lane)

| Field | Required | Type | Notes |
|---|---|---|---|
| `start` | yes | number | Seconds |
| `end` | yes | number | Seconds |
| `type` | yes | string | Component name: `"OverlayKeyword"`, `"BadgePopup"`, etc. |
| `beat_id` | no | string | Links to beat-map |
| `props` | no | object | Passed directly to the component |
| `notes` | no | string | Ignored by renderer |

## Background determination

Backgrounds are derived from avatar layout at each moment:
- `full-screen` avatar → dark background (`#1A1A2E`)
- `split-screen` avatar → light background (`#FFFFFF`)
- No avatar (center-full content) → neutral background (`#F5F5F5`)

Style overrides (from `project.json` style field) can modify these defaults.

## Center-full ranges

Computed from `broll` and `demo` entries with `display: "center-full"`.
Avatar hides during these ranges.

## Supported overlay components (D1 spike)

| Type | Props |
|---|---|
| `OverlayKeyword` | text, color, fontSize, position, shadowStrength |
| `BadgePopup` | text, color, size |

Additional components added incrementally in D3.

## Fallback behavior

- Missing `audio` → use `"source.wav"`
- Missing `avatar_file` → use `"avatar.mp4"`
- Missing `overlays` lane → no overlays rendered
- Missing `broll` lane → no broll rendered
- Missing `transition_preset` → hard cut (no transition)
- Missing `zoom_moments` → no zoom, static display
- Missing `playbackRate` → 1.0
- Missing `display` → split-screen default
