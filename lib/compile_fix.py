#!/usr/bin/env python3
"""
compile_fix — Error correction loop for Remotion TypeScript.

Runs `npx tsc --noEmit` in remotion/, parses the errors, reads the surrounding
code context, and formats everything as a self-contained Claude fix prompt.

Usage:
    python -m lib.compile_fix              # run tsc, print structured errors
    python -m lib.compile_fix --prompt     # print as a ready-to-paste Claude prompt
    python -m lib.compile_fix --watch N    # run up to N times, stopping when clean

Workflow:
    1.  Run after any Remotion code change
    2.  If clean → done
    3.  If errors → run with --prompt to get a formatted fix prompt
    4.  Paste the prompt into Claude to get targeted fixes
    5.  Apply fixes, then re-run to verify

Integration with change-pipeline:
    Step 4 of change-pipeline.md requires `npx tsc --noEmit` after every change.
    This tool replaces that manual step with a structured, actionable output.
"""

import subprocess
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
REMOTION_DIR = ROOT / "remotion"
CONTEXT_LINES = 4   # lines of code shown above and below each error


def _npx() -> str:
    """Return the correct npx executable name for the current platform."""
    import platform
    return "npx.cmd" if platform.system() == "Windows" else "npx"


def run_tsc() -> tuple[int, str]:
    """Run tsc and return (returncode, combined output)."""
    result = subprocess.run(
        [_npx(), "tsc", "--noEmit"],
        capture_output=True,
        text=True,
        cwd=REMOTION_DIR,
    )
    return result.returncode, result.stdout + result.stderr


def parse_errors(output: str) -> list[dict]:
    """Parse tsc error output into structured error dicts.

    Handles both relative and absolute file paths as emitted by tsc.
    """
    errors = []
    pattern = re.compile(
        r"^(.+?)\((\d+),(\d+)\):\s+error\s+(TS\d+):\s+(.+)$",
        re.MULTILINE,
    )
    for m in pattern.finditer(output):
        raw_file, line, col, code, message = m.groups()
        errors.append({
            "file": raw_file.strip(),
            "line": int(line),
            "col": int(col),
            "code": code,
            "message": message.strip(),
        })
    return errors


def read_context(file_ref: str, error_line: int) -> str:
    """Return CONTEXT_LINES of code surrounding error_line with an arrow marker."""
    candidates = [
        REMOTION_DIR / file_ref,
        Path(file_ref),
        ROOT / file_ref,
    ]
    src = None
    for path in candidates:
        try:
            if path.exists():
                src = path.read_text(encoding="utf-8")
                break
        except OSError:
            continue

    if src is None:
        return f"(could not read file: {file_ref})"

    lines = src.splitlines()
    start = max(0, error_line - 1 - CONTEXT_LINES)
    end = min(len(lines), error_line + CONTEXT_LINES)
    chunks = []
    for i, text in enumerate(lines[start:end], start=start + 1):
        marker = ">>>" if i == error_line else "   "
        chunks.append(f"{i:5d} {marker}  {text}")
    return "\n".join(chunks)


# ── Reserved names that must never be shadowed ────────────────────────────────
RESERVED = [
    "spring", "interpolate", "useCurrentFrame", "useVideoConfig",
    "AbsoluteFill", "Sequence", "fps", "width", "height",
]
RESERVED_SET = set(RESERVED)


def check_reserved(errors: list[dict]) -> list[str]:
    """Warn if any error message looks like a reserved-name shadow."""
    warnings = []
    for e in errors:
        for name in RESERVED_SET:
            if name in e["message"] and "shadow" in e["message"].lower():
                warnings.append(
                    f"WARNING: '{name}' appears in a shadowing error — "
                    f"never redefine Remotion built-ins as local variables."
                )
    return warnings


def format_prompt(errors: list[dict]) -> str:
    """Return a self-contained Claude fix prompt."""
    if not errors:
        return "✓  TypeScript compilation clean — no errors."

    reserved_warnings = check_reserved(errors)

    lines = [
        f"Fix {len(errors)} TypeScript compilation error(s) in the Remotion project.",
        "",
        "Rules (non-negotiable):",
        "  1. Fix exactly the errors listed — do NOT change component behavior.",
        "  2. Do NOT rename or redefine Remotion reserved names:",
        f"     {', '.join(RESERVED)}",
        "  3. Do NOT add or remove props that aren't mentioned in the errors.",
        "  4. After applying all fixes, verify with:",
        "     cd remotion && npx tsc --noEmit",
        "     or: python -m lib.compile_fix",
    ]

    if reserved_warnings:
        lines.append("")
        lines.extend(reserved_warnings)

    lines += ["", "=" * 60, "ERRORS", "=" * 60]

    for i, e in enumerate(errors, 1):
        lines += [
            "",
            f"--- Error {i} of {len(errors)} ---",
            f"File:    {e['file']}",
            f"Line:    {e['line']}, Col {e['col']}",
            f"Code:    {e['code']}",
            f"Message: {e['message']}",
            "",
            "Context:",
            read_context(e["file"], e["line"]),
        ]

    return "\n".join(lines)


def format_summary(errors: list[dict]) -> str:
    """Return a compact summary listing each error on one line."""
    if not errors:
        return "✓  TypeScript compilation clean."
    lines = [f"Found {len(errors)} error(s):\n"]
    for e in errors:
        lines.append(f"  {e['file']}:{e['line']}:{e['col']}  [{e['code']}]  {e['message']}")
    lines.append(
        "\nRun with --prompt to get a formatted fix prompt for Claude."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]

    as_prompt = "--prompt" in args

    watch_max = 1
    if "--watch" in args:
        idx = args.index("--watch")
        try:
            watch_max = int(args[idx + 1])
        except (IndexError, ValueError):
            watch_max = 3  # default iterations

    for attempt in range(watch_max):
        if watch_max > 1:
            print(f"\n[compile_fix] Attempt {attempt + 1} / {watch_max} ...", flush=True)

        returncode, output = run_tsc()

        if returncode == 0:
            print("✓  TypeScript compilation clean.")
            return 0

        errors = parse_errors(output)
        if not errors and returncode != 0:
            # tsc returned non-zero but we couldn't parse structured errors
            print("tsc exited with errors but output could not be parsed:\n")
            print(output)
            return 1

        if as_prompt:
            print(format_prompt(errors))
        else:
            print(format_summary(errors))

        if attempt < watch_max - 1:
            print("\n[Waiting for external fix... re-running on next iteration]")
        else:
            return 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
