# Orchestrator Test Fixtures

Fixtures are synthetic project directories created by `conftest.py` into `pytest`'s `tmp_path` for each test.
They are never committed to the repository — they exist only during the test run.

## Fixture Registry

| Fixture | Orchestration State | Gates Set | Key Files | Supports Scenarios |
|---|---|---|---|---|
| `fresh_project` | `created` | (none) | `project.json` | C (illegal phase), safety tests |
| `brief_ready_project` | `brief_ready` | `brief_approved` | `project.json`, `brief.md` | state derivation |
| `theme_ready_project` | `theme_ready` | `brief_approved`, `theme_set` | + `brief.md` | D (Claude pause at reel-script) |
| `script_ready_project` | `script_ready` | + `script_approved` | + `script.md` | E (Human pause at ingest-voice) |
| `reconciled_project` | `reconciled` | + `reconciliation_resolved` | + `audio/beat-map.json`, `audio/reconciliation.md` | H (invalidation cascade) |
| `shot_list_ready_project` | `shot_list_ready` | through `technical_planning_approved` | + `shot-list.md` | D (code phase asset-prep skipped) |
| `assembled_project` | `assembled` | through `assets_validated` + `timeline.json` exists | + `output/timeline.json`, `output/motion-intent.md` | E (Human pause at preview) |
| `preview_passed_project` | `preview_approved` | + `preview_passed` | same as assembled | F (parity before qa-reel) |
| `qa_passed_project` | `qa_passed` | all 11 gates | + `output/qa-report.md` | B (code phase render), F (parity before render) |

## What Each Fixture Intentionally Lacks

| Fixture | Missing intentionally | Why |
|---|---|---|
| `fresh_project` | `brief.md`, all gates | Test illegal phase rejection without clutter |
| `theme_ready_project` | `audio/`, `shot-list.md` | Only needs enough for reel-script gate check |
| `script_ready_project` | `audio/beat-map.json` | State: script_ready means audio not yet generated |
| `qa_passed_project` | Remotion `out/reel.mp4` | Render artifact absence distinguishes qa_passed from rendered |

## Fixture Design Principles

1. **Minimal** — each fixture contains only the files needed for its target scenarios
2. **Valid** — `project.json` always has required fields: `slug`, `gates_passed`, `style`, `theme`, `theme_primary`
3. **Isolated** — all fixtures are in `tmp_path` — parallel test runs cannot interfere
4. **Stable** — fixture content is not sensitive to the active reel project; no cross-project file references

## Adding New Fixtures

Add to `conftest.py` using `make_project()`:

```python
@pytest.fixture
def my_new_state_project(tmp_path: Path) -> Path:
    return make_project(
        tmp_path,
        "test-my-state",
        gates=["brief_approved", "theme_set", "script_approved"],
        extra_files={
            "brief.md": "# Brief\n",
            "script.md": "# Script\n\n## ElevenLabs Script\n\nHello.\n",
        },
    )
```

Gates must reflect the actual `lib/constants.py::GATE_ORDER` values exactly.
