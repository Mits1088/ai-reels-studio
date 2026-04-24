# Agent Roles

Specialist sub-agents for the reel production pipeline. Each agent is invoked by the main agent when a task matches its specific domain.

---

## Agent Index

| Agent | File | Pipeline phase | When to use |
|---|---|---|---|
| `qa-runner` | `.claude/agents/qa-runner.md` | Phase 6 (QA) | After assembly — run full automated + editorial QA |
| `asset-auditor` | `.claude/agents/asset-auditor.md` | Phase 4d (asset-prep) | Before assembly — verify encoding, presence, privacy |
| `timeline-critic` | `.claude/agents/timeline-critic.md` | Phase 5 (assembly) | After assembly — verify structural integrity of timeline.json |
| `render-doctor` | `.claude/agents/render-doctor.md` | Any — on failure | When render, tsc, or visual frame output is broken |
| `retention-critic` | `.claude/agents/retention-critic.md` | Phase 5b (quick preview) | Editorial review — hook strength, pacing, variety |
| `data-analyst` | `.claude/agents/data-analyst.md` | Any — on demand | Portfolio-level pattern questions against analytics DB |
| `memory-curator` | `.claude/agents/memory-curator.md` | Post-render / between projects | Audit accumulated taste signal for conflicts and stale entries |

---

## Agent Descriptions

### qa-runner

**Scope:** Technical and editorial QA on a single project after assembly.  
**Reads:** `output/qa-report.md`, `output/qa_report.json`, `output/timeline.json`, `audio/beat-map.json`, `project.json`  
**Runs:** `python -m lib.qa.cli <project-dir>`  
**Returns:** PASS / PASS_WITH_WARNINGS / FAIL verdict with blockers and fix hints  
**Use when:** Assembly is complete (`preview_passed` gate is set) and the project needs QA before render.  
**Do not use when:** You want creative/editorial feedback (use `retention-critic`) or when assembly hasn't started yet.

---

### asset-auditor

**Scope:** Per-asset encoding compliance and presence check before assembly.  
**Reads:** `assets/sourced/catalog.json`, `output/timeline.json` (if present), `remotion/public/` directory  
**Runs:** `ffprobe` on each video asset  
**Returns:** Per-asset table (encoded / audio / present / issues) with re-encode commands for broken assets  
**Use when:** Phase 4d (asset-prep) is complete and you want to confirm every asset is Remotion-ready before writing the timeline.  
**Do not use when:** You want QA after assembly (use `qa-runner`) or when you have render errors (use `render-doctor`).

---

### timeline-critic

**Scope:** Structural integrity of `output/timeline.json`.  
**Reads:** `output/timeline.json`, `audio/beat-map.json`, `project.json`  
**Returns:** Lane-by-lane structural verdict — overlap conflicts, missing beat IDs, gap ownership failures, broken asset references  
**Use when:** Assembly is complete but before running `qa-runner` — catching structural bugs early prevents wasted QA cycles.  
**Do not use when:** You want editorial/creative critique (use `retention-critic`) or encoding validation (use `asset-auditor`).

---

### render-doctor

**Scope:** Root-cause diagnosis of render failures, TypeScript errors, and visual frame defects.  
**Reads:** `remotion/src/ReelComposition.tsx`, `remotion/src/components/*.tsx`, error output, QA frame images  
**Runs:** `tsc --noEmit`, `python -m lib.compile_fix --prompt`, `ffprobe` on specific assets  
**Returns:** Root cause with file:line precision and a specific recommended edit  
**Use when:** `npx remotion render`, `npx remotion studio`, or `tsc --noEmit` fails — or when extracted QA frames show a visual defect (white gap, wrong z-index, missing element).  
**Do not use when:** The reel renders correctly and you want editorial feedback (use `retention-critic`) or QA (use `qa-runner`).

---

### retention-critic

**Scope:** Editorial and retention quality evaluation against accumulated taste signal.  
**Reads:** `memory/creative-feedback.json`, `audio/beat-map.json`, `output/timeline.json`, `shot-list.md`, `output/review-feedback.md`, `training/derived/taste-rules.json`  
**Returns:** Hook assessment, pacing density, visual variety score, hard rule violations, weakest beats with specific fix suggestions  
**Use when:** Phase 5b (quick preview) — the user has seen the assembled cut and wants to know if it will hold attention. Also use before writing the shot list if the user asks "is this creative direction strong?".  
**Do not use when:** You want structural checks (use `timeline-critic`) or technical QA (use `qa-runner`).

---

### data-analyst

**Scope:** Cross-project pattern analysis against the analytics database.  
**Reads:** `data/analytics.db` (read-only SQL queries)  
**Returns:** Ranked tables of patterns — gate failures, critic check recurrence, staleness signal frequency, projects needing attention  
**Use when:** The user asks portfolio-level questions: "what keeps failing?", "which projects need attention?", "what is the most common QA blocker?", "which gate has the lowest pass rate?"  
**Prerequisite:** `data/analytics.db` must exist. If not: `python -m lib.analytics ingest-all`.  
**Do not use when:** You want project-specific analysis (use the appropriate project-scoped agent) or when the question requires reading frame images (no agent handles that).

---

### memory-curator

**Scope:** Consistency and freshness audit of the global taste memory layer.  
**Reads:** `memory/creative-feedback.json`, `projects/*/output/review-feedback.md`, `training/derived/taste-rules.json`  
**Returns:** Proposed changes as structured text — conflicts, stale entries, promotion candidates. NEVER edits files directly.  
**Use when:** After multiple review rounds when feedback feels contradictory, before starting a new reel series, or when the user says "the rules feel off" or "I keep getting the same feedback".  
**Do not use when:** You want to evaluate a specific reel (use `retention-critic`) or answer analytics questions (use `data-analyst`).

---

## Invocation Decision Tree

```
Is there a render / compile error?
  └── YES → render-doctor

Is there a question about all projects or portfolio patterns?
  └── YES → data-analyst (requires analytics DB to be current)

Is the task "check memory/taste signal consistency"?
  └── YES → memory-curator

Is assembly complete?
  └── NO → asset-auditor (check assets are ready before writing timeline)
  └── YES →
        Did you just finish writing timeline.json?
          └── YES → timeline-critic first, then qa-runner
        Is this a creative/editorial review?
          └── YES → retention-critic
        Is this a full pre-render QA check?
          └── YES → qa-runner
```

---

## Return Format Contract

All agents return findings in this structure (field names vary slightly by agent):

```
VERDICT: [agent-specific verdict values]

[agent-specific sections]

BLOCKERS: [issues that must be resolved before proceeding]
WARNINGS: [issues worth addressing but not blocking]

EVIDENCE READ: [every file or data source the agent read]

RECOMMENDED NEXT ACTION: [specific, actionable instruction]
```

Blockers must be resolved before moving to the next pipeline phase. Warnings are actionable but not mandatory. Every agent stays within 60–80 lines — the main agent needs verdicts and actionable items, not essays.

---

## Overlap and Boundary Notes

These are the cases where two agents seem similar but are distinct:

| Scenario | Correct agent | Why NOT the other |
|---|---|---|
| "Are my assets ready to assemble?" | `asset-auditor` | `qa-runner` runs after assembly and won't check encoding |
| "Is my timeline structurally valid?" | `timeline-critic` | `qa-runner` covers structural issues too, but `timeline-critic` is faster and runs before QA |
| "Will viewers stay engaged?" | `retention-critic` | `qa-runner` checks technical QA thresholds, not editorial retention risk |
| "Why did my render fail?" | `render-doctor` | `qa-runner` finds issues in already-rendered output; `render-doctor` diagnoses failures before render completes |
| "What patterns repeat across all my reels?" | `data-analyst` | `retention-critic` evaluates one project; `data-analyst` queries the full portfolio |
| "Is my feedback memory still valid?" | `memory-curator` | `retention-critic` applies the memory to a specific reel; `memory-curator` audits the memory itself |
