# Brain Design — Phase 1: Read-Only Diagnostic Surface

**Module:** `lib/brain/`
**Phase:** 1 of 6 (diagnostic surface only)
**Constraint:** Read-only. Never mutates project.json or any artifact.

---

## Purpose

`lib.brain` is a self-diagnosing layer that reads all available signals about a project and returns a single structured `Diagnosis` object. It answers:

- What phase is this project in?
- Which gates have been passed, which are missing?
- What key artifacts exist or are absent?
- Are any artifact–gate combinations suspicious (gate set but file missing)?
- Are any downstream artifacts potentially stale?
- What does the last QA run say (if any)?
- What does the critic say (if any)?
- What is the next action, and who should take it?
- Can Claude continue autonomously, or does a human need to act?

---

## Diagnosis Contract

```
Diagnosis
├── slug, title, project_dir
├── project_json_found: bool
├── schema_version: int | None
├── schema_ok: bool
├── phase, status, style, theme, theme_primary
├── validation_errors: list[str]
│
├── gates: GateInventory
│   ├── passed: list[str]       gates in project.json AND in GATE_ORDER
│   ├── missing: list[str]      gates in GATE_ORDER not yet passed
│   ├── next_required: str|None lowest unpassed gate
│   ├── unknown_gates: list[str] in project.json but not in GATE_ORDER
│   └── total: int              canonical gate count (11 for reel)
│
├── artifacts: ArtifactInventory
│   ├── entries: list[ArtifactEntry]           key pipeline files + their presence
│   ├── gate_artifact_mismatches: list[str]    gate set but expected file missing
│   └── stale_hints: list[str]                 upstream newer than downstream
│
├── qa: QAStatus
│   ├── available: bool         qa_report.json exists
│   ├── verdict: str            PASS / PASS_WITH_WARNINGS / FAIL / not_run
│   ├── blockers: int
│   ├── warnings: int
│   ├── top_blockers: list[str] up to 3 human-readable messages
│   └── report_timestamp: str
│
├── critic: CriticStatus
│   ├── available: bool         critic-report.json exists
│   ├── status: str             critic_passed / critic_warnings / critic_blocked / not_run
│   ├── findings_count: int
│   ├── highest_severity: str   block / warn / suggest / none
│   └── top_findings: list[str] up to 3 human-readable messages
│
├── autonomy: AutonomyVerdict
│   ├── can_continue_autonomously: bool
│   ├── human_required: bool
│   ├── human_required_reason: str
│   ├── next_action: str         human-readable description
│   ├── next_action_actor: str   code / claude / human / human+claude / unknown
│   ├── next_action_command: str concrete shell or conversation command
│   └── confidence: str          high / medium / low
│
├── healthy: bool               computed: no validation errors, no mismatches, QA not FAIL
└── diagnosis_timestamp: str    ISO 8601
```

---

## Autonomy Decision Rules

The `autonomy` verdict is the brain's key output. The rules are explicit and deterministic:

| Condition | can_continue_autonomously | human_required |
|---|---|---|
| project.json missing | False | False |
| validation_errors present | False | False |
| All 11 gates passed, QA PASS | True | False |
| All 11 gates passed, QA FAIL | False | False |
| Next gate is in AUTO_GATES | True | False |
| Next gate is in HUMAN_GATES | False | True |

**AUTO_GATES** (Claude/code can set these without human review):
- `theme_set` — set by theme-factory skill
- `reconciliation_resolved` — set by script-reconcile
- `asset_fitness_passed` — set by shot-list 4b-ii auto check
- `assets_validated` — set by asset-prep
- `qa_passed` — set by lib.qa.runner

**HUMAN_GATES** (require explicit human approval):
- `brief_approved`
- `script_approved`
- `visual_assignment_approved`
- `technical_planning_approved`
- `motion_intent_reviewed`
- `preview_passed`

---

## Signal Sources

The brain reads these sources in order. All reads are defensive (missing file = skip, not crash):

| Source | Used for |
|---|---|
| `project.json` | Phase, status, gates, theme, style, schema |
| `lib.validate.validate_project()` | JSON contract errors |
| Filesystem (key artifact paths) | Presence and size |
| File mtimes (upstream/downstream pairs) | Stale hints |
| `output/qa_report.json` | QA verdict and blockers |
| `output/qa-report.md` | QA presence signal when JSON absent |
| `output/critic-report.json` | Critic status and findings |

The brain does **not** re-run QA or the critic. It reads the last written reports.

---

## Key Artifacts Checked

These files are always checked regardless of gate state:

```
brief.md
script.md
audio/beat-map.json
audio/captions.json
audio/source.wav
audio/reconciliation.md
shot-list.md
output/motion-intent.md
output/timeline.json
output/qa-report.md
output/qa_report.json
output/critic-report.json
output/edit-plan.json
```

---

## Gate–Artifact Mapping

A "gate–artifact mismatch" is flagged when a gate is marked as passed in `gates_passed`
but its expected artifact does not exist on disk. These are suspicious because they suggest
the gate was set manually or the artifact was deleted after the gate was passed.

| Gate | Expected artifact(s) |
|---|---|
| `brief_approved` | `brief.md` |
| `script_approved` | `script.md` |
| `reconciliation_resolved` | `audio/reconciliation.md` |
| `visual_assignment_approved` | `shot-list.md` |
| `asset_fitness_passed` | `shot-list.md` |
| `technical_planning_approved` | `shot-list.md` |
| `motion_intent_reviewed` | `output/motion-intent.md` |
| `preview_passed` | `output/timeline.json` |
| `qa_passed` | `output/qa-report.md` |

---

## Artifact Dependency Map (Phase 2)

**Module:** `lib/brain/artifacts.py`

The dependency map is a directed graph of 13 upstream→downstream edges. Each
edge carries a `base_confidence` (high/medium/low), a human-readable `reason`,
and a `recommended_action`.

Staleness is detected in `lib/brain/staleness.py`. A pair is flagged when
`upstream.mtime > downstream.mtime + 2s`. Confidence is then scaled by the
size of the delta:

| Delta | Effect |
|---|---|
| < 30s | Confidence reduced one tier (same-session write) |
| 30s – 300s | High stays high; medium/low unchanged |
| > 300s | Base confidence kept (different pipeline session) |

### Dependency Edges

| Upstream | Downstream | Base confidence | Why |
|---|---|---|---|
| `brief.md` | `script.md` | medium | Script is written from the brief |
| `script.md` | `audio/reconciliation.md` | **high** | Reconciliation compares approved script against audio |
| `script.md` | `audio/beat-map.json` | medium | Audio may not match a revised script |
| `audio/source.wav` | `audio/beat-map.json` | **high** | Beat map is derived from source audio |
| `audio/beat-map.json` | `audio/captions.json` | **high** | Captions are polished from beat map timing |
| `audio/beat-map.json` | `shot-list.md` | medium | Shot list assigns visuals to beats |
| `shot-list.md` | `output/motion-intent.md` | **high** | Motion intent is derived from the shot list |
| `output/motion-intent.md` | `output/timeline.json` | **high** | Timeline is assembled from motion intent |
| `output/edit-plan.json` | `output/timeline.json` | **high** | Edit plan compiles into timeline |
| `audio/captions.json` | `output/timeline.json` | medium | Timeline embeds caption timing |
| `assets/sourced/catalog.json` | `output/timeline.json` | low | New assets may not be referenced in timeline |
| `output/timeline.json` | `output/qa_report.json` | **high** | QA runs against the timeline |
| `output/review-feedback.md` | `output/qa_report.json` | medium | Feedback captured after QA may need a re-run |

### StalenessResult fields

```
StalenessResult
├── downstream: str           relative path of the potentially-stale artifact
├── upstream: str             relative path of the artifact that changed
├── confidence: str           high / medium / low (after delta scaling)
├── reason: str               why downstream depends on upstream
├── recommended_action: str   concrete next step
└── age_delta_seconds: float  how many seconds newer the upstream is
```

`StalenessResult` objects are available at:
- `Diagnosis.artifacts.staleness_results` — structured list
- `Diagnosis.artifacts.stale_hints` — backward-compat human-readable summary strings

---

## CLI

```bash
# Human-readable report (exit 0 = healthy, exit 1 = issues found)
PYTHONPATH=. python -m lib.brain diagnose projects/<slug>

# Machine-readable JSON (includes staleness_results array)
PYTHONPATH=. python -m lib.brain diagnose projects/<slug> --json

# Write JSON to file
PYTHONPATH=. python -m lib.brain diagnose projects/<slug> --json --out output/diagnosis.json
```

The CLI exits 0 when `Diagnosis.healthy` is True, 1 otherwise.

---

## Smoke Tests

```bash
PYTHONPATH=. python lib/brain/smoke_test.py
```

Sixteen tests covering:
- **Phase 1 (8):** missing project, minimal project, all-gates-passed, JSON serialisation,
  human renderer, unknown gate detection, gate–artifact mismatch detection, real project
- **Phase 2 (8):** clean pipeline order, high-confidence staleness, below-tolerance not
  flagged, script change cascades, review-feedback signal, serialisation, missing
  downstream skipped, registry completeness

---

## What This Is NOT

Phases 1–2 are deliberately scoped:

- **Does not** re-run QA or the critic (reads existing reports only)
- **Does not** mutate project.json or any artifact
- **Does not** execute any pipeline phase
- **Does not** propose fixes (that is Phase 3)
- **Does not** cascade-invalidate gates (that is `lib.orchestrator.invalidation`)
- **Does not** reset gates automatically when staleness is detected

---

## Phase 3 Preview (Fix Proposal Engine)

The `Diagnosis` object (with staleness signals) is designed to feed Phase 3
(`lib/propose/`), which will:
- Read `staleness_results` → produce concrete regeneration proposals ranked by confidence
- Read `gate_artifact_mismatches` → map each to the skill that produces the missing file
- Read `qa.top_blockers` → map each to a repair strategy + target artifact
- Read `critic.top_findings` → map to `BeatPlan` patches where auto-safe
- Add `risk_level` and `requires_human` to each proposal

Phase 3 will import `diagnose_project` and `detect_staleness` from this module
without changes.
