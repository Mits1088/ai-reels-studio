"""
lib/parity.py — Source-of-truth drift detector.

Checks that shared numeric thresholds in markdown rule/skill files stay in sync
with the canonical Python source: STYLE_THRESHOLDS in lib.qa.checks.

Usage:
    python -m lib.parity           # check all files, exit 0/1
    python lib/parity.py           # same
    python -m lib.parity --verbose # show passes too

Designed for CI integration. Returns exit code 1 if any check fails.
"""

from __future__ import annotations

import re
import sys
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# Import canonical thresholds
# ---------------------------------------------------------------------------

try:
    from lib.qa.checks import STYLE_THRESHOLDS
except ImportError:
    # Fallback: run from repo root with plain python lib/parity.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from lib.qa.checks import STYLE_THRESHOLDS


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class ParityCheck:
    """A single pattern assertion against a markdown file."""
    file: str                     # relative path from repo root
    description: str              # human-readable name
    pattern: str                  # regex pattern that must (or must NOT) match
    must_match: bool              # True = required, False = forbidden
    reason: str                   # why this check exists
    fix_hint: str                 # what to do if it fails


@dataclass
class CheckResult:
    check: ParityCheck
    passed: bool
    detail: str


# ---------------------------------------------------------------------------
# Build check list from STYLE_THRESHOLDS
# ---------------------------------------------------------------------------

def _build_checks() -> list[ParityCheck]:
    cp = STYLE_THRESHOLDS["cinematic-presenter"]
    ea = STYLE_THRESHOLDS["editorial-authority"]

    # Convenience aliases
    cp_abs_warn  = int(cp["avatar_absence_warn"])   # 12
    cp_abs_block = int(cp["avatar_absence_block"])  # 15
    cp_cf_max    = cp["center_full_max"]            # 4
    cp_flash     = cp["flash_max"]                  # 1

    ea_abs_warn  = int(ea["avatar_absence_warn"])   # 8
    ea_abs_block = int(ea["avatar_absence_block"])  # 12
    ea_cf_max    = ea["center_full_max"]            # 4
    ea_flash_s   = ea["flash_max_short"]            # 2
    ea_flash_l   = ea["flash_max_long"]             # 3

    ASSEMBLE = ".claude/skills/assemble-reel/SKILL.md"
    CINEMATIC = "styles/cinematic-presenter.md"
    QA_GATES  = ".claude/rules/qa-gates.md"

    checks: list[ParityCheck] = []

    # ── cinematic-presenter thresholds in assemble-reel ────────────────────

    checks.append(ParityCheck(
        file=ASSEMBLE,
        description="cinematic-presenter: avatar absence warn threshold (12s preferred)",
        pattern=r"12s preferred",
        must_match=True,
        reason="STYLE_THRESHOLDS cinematic-presenter avatar_absence_warn=12.0",
        fix_hint=f"Update avatar absence row to '{cp_abs_warn}s preferred — {cp_abs_block}s hard max'",
    ))

    checks.append(ParityCheck(
        file=ASSEMBLE,
        description="cinematic-presenter: avatar absence block threshold (15s hard max)",
        pattern=r"15s hard max",
        must_match=True,
        reason="STYLE_THRESHOLDS cinematic-presenter avatar_absence_block=15.0",
        fix_hint=f"Update avatar absence row to include '{cp_abs_block}s hard max'",
    ))

    checks.append(ParityCheck(
        file=ASSEMBLE,
        description="editorial-authority: avatar absence warn threshold (8s preferred)",
        pattern=r"8s preferred",
        must_match=True,
        reason="STYLE_THRESHOLDS editorial-authority avatar_absence_warn=8.0",
        fix_hint=f"Update editorial-authority avatar absence row to '{ea_abs_warn}s preferred — {ea_abs_block}s hard max'",
    ))

    checks.append(ParityCheck(
        file=ASSEMBLE,
        description="editorial-authority: avatar absence block threshold (12s hard max)",
        pattern=r"12s hard max",
        must_match=True,
        reason="STYLE_THRESHOLDS editorial-authority avatar_absence_block=12.0",
        fix_hint=f"Update editorial-authority avatar absence row to include '{ea_abs_block}s hard max'",
    ))

    checks.append(ParityCheck(
        file=ASSEMBLE,
        description="cinematic-presenter: center-full max (4 preferred)",
        pattern=r"4 preferred",
        must_match=True,
        reason="STYLE_THRESHOLDS cinematic-presenter center_full_max=4",
        fix_hint="Update Max consecutive center-full row to '4 preferred'",
    ))

    checks.append(ParityCheck(
        file=ASSEMBLE,
        description="cinematic-presenter: ambient motion defaults to still",
        pattern=r"body beats default to [`']?still[`']?",
        must_match=True,
        reason="motion-grammar.md + qa-gates.md: body beats default to still; ambient is opt-in",
        fix_hint="Ambient motion row must state 'body beats default to still — ambient opt-in only'",
    ))

    # ── Forbidden historical wrong values in assemble-reel ─────────────────

    checks.append(ParityCheck(
        file=ASSEMBLE,
        description="FORBIDDEN: old avatar absence warn (8s with b-roll) for cinematic-presenter",
        pattern=r"\|\s*Avatar absence limit\s*\|[^\n]*8s \(12s with b-roll\)",
        must_match=False,
        reason="This was the wrong old value — cinematic-presenter warn is 12s, not 8s",
        fix_hint="Replace stale '8s (12s with b-roll)' with '12s preferred — 15s hard max'",
    ))

    checks.append(ParityCheck(
        file=ASSEMBLE,
        description="FORBIDDEN: old editorial-authority avatar absence (18s)",
        pattern=r"\|\s*Avatar absence limit\s*\|[^\n]*18s",
        must_match=False,
        reason="Editorial-authority hard max is 12s, not 18s — 18s was a stale wrong value",
        fix_hint="Remove '18s' from editorial-authority column; correct value is '12s hard max'",
    ))

    checks.append(ParityCheck(
        file=ASSEMBLE,
        description="FORBIDDEN: old center-full max of 2 for cinematic-presenter",
        pattern=r"\|\s*Max consecutive center.full\s*\|\s*2\b",
        must_match=False,
        reason="cinematic-presenter center_full_max is 4, not 2",
        fix_hint="Replace '2' in Max consecutive center-full row with '4 preferred'",
    ))

    checks.append(ParityCheck(
        file=ASSEMBLE,
        description="FORBIDDEN: old editorial-authority center-full max of 8",
        pattern=r"\|\s*Max consecutive center.full\s*\|[^\n]*8 \(full.frame",
        must_match=False,
        reason="editorial-authority center_full_max is 4 (5 conditional), not 8",
        fix_hint="Replace '8 (full-frame is the default)' with '4 preferred (5 conditional)'",
    ))

    checks.append(ParityCheck(
        file=ASSEMBLE,
        description="FORBIDDEN: old Ken Burns mandate (yes on static content)",
        pattern=r"Ken Burns.*yes on static content",
        must_match=False,
        reason="Body beats default to still; Ken Burns is opt-in, not 'yes on static content'",
        fix_hint="Replace Ken Burns row with Ambient motion row reflecting stillness doctrine",
    ))

    # ── qa-gates.md threshold consistency ──────────────────────────────────

    checks.append(ParityCheck(
        file=QA_GATES,
        description="qa-gates: cinematic-presenter avatar absence preferred (12s)",
        pattern=r"12s \(relaxed with matched b-roll\)",
        must_match=True,
        reason="STYLE_THRESHOLDS cinematic-presenter avatar_absence_warn=12.0",
        fix_hint="qa-gates.md threshold table: cinematic-presenter avatar absence preferred = '12s (relaxed with matched b-roll)'",
    ))

    checks.append(ParityCheck(
        file=QA_GATES,
        description="qa-gates: editorial-authority avatar absence preferred (8s)",
        pattern=r"Avatar absence \(preferred\)[^\n]*8s",
        must_match=True,
        reason="STYLE_THRESHOLDS editorial-authority avatar_absence_warn=8.0",
        fix_hint="qa-gates.md threshold table: editorial-authority avatar absence = 8s",
    ))

    checks.append(ParityCheck(
        file=QA_GATES,
        description="qa-gates: cinematic-presenter flash max (1 per reel)",
        pattern=r"Flash accent max[^\n]*1 per reel",
        must_match=True,
        reason="STYLE_THRESHOLDS cinematic-presenter flash_max=1",
        fix_hint="qa-gates.md: cinematic-presenter flash accent max = 1 per reel",
    ))

    checks.append(ParityCheck(
        file=QA_GATES,
        description="qa-gates: editorial-authority flash max short (2 for <35s)",
        pattern=r"2 for <35s",
        must_match=True,
        reason="STYLE_THRESHOLDS editorial-authority flash_max_short=2",
        fix_hint="qa-gates.md: editorial-authority flash = '2 for <35s, 3 for 35s+'",
    ))

    checks.append(ParityCheck(
        file=QA_GATES,
        description="qa-gates: ambient motion defaults to still (body beats opt-in)",
        pattern=r"opt-in \(not assumed.*body beats default to [`']?still[`']?\)",
        must_match=True,
        reason="motion-grammar.md stillness doctrine: body beats default to still",
        fix_hint="qa-gates.md: ambient motion row for cinematic-presenter should say 'opt-in (not assumed — body beats default to still)'",
    ))

    checks.append(ParityCheck(
        file=QA_GATES,
        description="qa-gates: Stacked Motion check (zoom-in + ambient hold = BLOCKER)",
        pattern=r"Stacked Motion.*BLOCKER",
        must_match=True,
        reason="motion-grammar.md: Stacked Motion is a named anti-pattern, BLOCKER severity",
        fix_hint="qa-gates.md Motion Quality section must include 'Stacked Motion (BLOCKER)' check",
    ))

    checks.append(ParityCheck(
        file=QA_GATES,
        description="qa-gates: Zoom Reflex check (BLOCKER)",
        pattern=r"Zoom Reflex.*BLOCKER",
        must_match=True,
        reason="motion-grammar.md: Zoom Reflex is a named anti-pattern, BLOCKER severity",
        fix_hint="qa-gates.md Motion Quality section must include 'Zoom Reflex (BLOCKER)' check",
    ))

    # ── cinematic-presenter.md threshold consistency ────────────────────────

    checks.append(ParityCheck(
        file=CINEMATIC,
        description="cinematic-presenter.md: avatar absence warn (12s)",
        pattern=r"12[s\s]",
        must_match=True,
        reason="STYLE_THRESHOLDS cinematic-presenter avatar_absence_warn=12.0 must appear in the style spec",
        fix_hint="styles/cinematic-presenter.md: confirm avatar absence threshold is 12s preferred",
    ))

    checks.append(ParityCheck(
        file=CINEMATIC,
        description="cinematic-presenter.md: center-full max (4)",
        pattern=r"\b4\b.*center.full|center.full.*\b4\b",
        must_match=True,
        reason="STYLE_THRESHOLDS cinematic-presenter center_full_max=4",
        fix_hint="styles/cinematic-presenter.md: center-full max should be 4",
    ))

    return checks


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _repo_root() -> Path:
    """Find the repo root (directory containing CLAUDE.md)."""
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "CLAUDE.md").exists():
            return parent
    # Fallback: cwd
    return Path.cwd()


def run_checks(verbose: bool = False) -> list[CheckResult]:
    root = _repo_root()
    checks = _build_checks()
    results: list[CheckResult] = []

    for check in checks:
        path = root / check.file
        if not path.exists():
            results.append(CheckResult(
                check=check,
                passed=False,
                detail=f"File not found: {check.file}",
            ))
            continue

        text = path.read_text(encoding="utf-8")
        match = re.search(check.pattern, text, re.IGNORECASE | re.DOTALL)
        matched = match is not None

        if check.must_match:
            passed = matched
            detail = "pattern found" if passed else f"pattern not found: {check.pattern!r}"
        else:
            passed = not matched
            detail = "forbidden pattern absent" if passed else f"forbidden pattern found: {match.group()!r}"

        results.append(CheckResult(check=check, passed=passed, detail=detail))

    return results


def _print_results(results: list[CheckResult], verbose: bool) -> int:
    failures = [r for r in results if not r.passed]
    passes   = [r for r in results if r.passed]

    if verbose:
        for r in passes:
            print(f"  \033[32m✓\033[0m  {r.check.description}")

    if failures:
        print(f"\n\033[31m{len(failures)} parity check(s) FAILED\033[0m  ({len(passes)} passed)\n")
        for r in failures:
            label = "REQUIRED" if r.check.must_match else "FORBIDDEN"
            print(f"  \033[31m✗  [{label}] {r.check.description}\033[0m")
            print(f"     File   : {r.check.file}")
            print(f"     Reason : {r.check.reason}")
            print(f"     Detail : {r.detail}")
            print(f"     Fix    : {r.check.fix_hint}")
            print()
        return 1
    else:
        print(f"\033[32m✓  All {len(passes)} parity checks passed\033[0m")
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Parity checker — detects source-of-truth drift across rule/skill markdown files."
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show passing checks too")
    args = parser.parse_args(argv)

    results = run_checks(verbose=args.verbose)
    return _print_results(results, verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())
