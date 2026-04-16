"""
URL ingestion CLI — drop any URL, get text + frames + assets.

Detects URL type (YouTube / Twitter/X / PDF / webpage) and runs the
appropriate extractor. Outputs ingestion.json and source-research.md
to the project directory.

Usage:
  python -m lib.ingest.url <url> --project <slug>

Examples:
  python -m lib.ingest.url https://youtube.com/watch?v=xxx --project my-reel
  python -m lib.ingest.url https://anthropic.com/claude   --project my-reel
  python -m lib.ingest.url https://x.com/user/status/123  --project my-reel
  python -m lib.ingest.url https://arxiv.org/pdf/2501.xyz.pdf --project my-reel

Options:
  --project SLUG      Reel project slug  (required)
  --frames-every N    Seconds between extracted frames for video (default: 5)
  --no-write          Dry-run: parse and report without writing files
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="URL ingestion layer — extract text, frames, and assets from any URL",
        prog="python -m lib.ingest.url",
    )
    parser.add_argument("url", help="URL to ingest")
    parser.add_argument(
        "--project", required=True, metavar="SLUG",
        help="Reel project slug (e.g. my-reel). Creates projects/<slug>/ if needed.",
    )
    parser.add_argument(
        "--frames-every", type=float, default=5.0, metavar="N",
        help="For video URLs: seconds between extracted frames (default: 5)",
    )
    parser.add_argument(
        "--no-write", action="store_true",
        help="Do not write output files (dry-run)",
    )

    args = parser.parse_args()

    # Resolve project directory relative to the repo root
    root = Path(__file__).resolve().parents[2]  # D:/Reel generation/
    project_dir = root / "projects" / args.project

    print(f"\nURL Ingestion Layer")
    print(f"{'─' * 50}")
    print(f"  URL     : {args.url}")
    print(f"  Project : {args.project}")
    print(f"  Output  : {project_dir}")
    print()

    from .url_router import ingest_url, detect_url_type

    url_type = detect_url_type(args.url)
    print(f"  Type detected: {url_type}")
    print()

    try:
        result = ingest_url(
            args.url,
            project_dir,
            frames_every=args.frames_every,
            write_output=not args.no_write,
        )
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'═' * 50}")
    print(f"  Ingestion complete")
    print(f"{'─' * 50}")
    print(f"  Type     : {result.source_type}")
    print(f"  Title    : {result.title[:70]}")
    print(f"  Text     : {len(result.text_content.split())} words")
    print(f"  Claims   : {len(result.key_claims)}")
    print(f"  Frames   : {len(result.frames)}")
    print(f"  Assets   : {len(result.assets)}")

    if result.key_claims:
        print(f"\n  Top claims:")
        for c in result.key_claims[:5]:
            print(f"    • {c[:90]}")
        if len(result.key_claims) > 5:
            print(f"    … and {len(result.key_claims) - 5} more")

    if result.frames:
        print(f"\n  Sample frames:")
        for f in result.frames[:4]:
            print(f"    {f}")
        if len(result.frames) > 4:
            print(f"    … and {len(result.frames) - 4} more")

    if not args.no_write:
        print(f"\n  Files written:")
        print(f"    {project_dir / 'ingestion.json'}")
        if result.source_type != "webpage":
            # webpage extractor writes its own source-research.md via source-brief.js
            print(f"    {project_dir / 'source-research.md'}")
        print(f"    {project_dir / 'assets/'}")

    print(f"\n  Next steps:")
    print(f"    1. Read {project_dir / 'source-research.md'}")
    print(f"    2. Run /source-brief to propose brief direction")
    print(f"    3. Approve brief → proceed to /reel-script")


if __name__ == "__main__":
    main()
