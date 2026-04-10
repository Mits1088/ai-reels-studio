"""
CLI entrypoint for voice ingestion.

Usage:
  # Extract audio only (no transcription needed):
  python -m lib.ingest.cli extract avatar.mp4 projects/my-reel/

  # Full pipeline with mock transcription:
  python -m lib.ingest.cli full narration.wav projects/my-reel/ --provider mock

  # Full pipeline with Whisper:
  python -m lib.ingest.cli full narration.wav projects/my-reel/ --provider whisper --api-key KEY

Backward-compatible (no subcommand = full pipeline with mock):
  python -m lib.ingest.cli narration.wav projects/my-reel/
"""

import argparse
import sys
from pathlib import Path

from .pipeline import ingest, extract_only, IngestError
from .transcribe import MockProvider, WhisperAPIProvider, LocalWhisperProvider


def _run_extract(args):
    """Extract audio only — for manual beat-map/captions workflow."""
    try:
        result = extract_only(args.input, args.project_dir)
    except IngestError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Audio extracted.")
    print(f"  Output:   {result.audio_path}")
    if result.total_duration:
        print(f"  Duration: {result.total_duration}s")
    print()
    print(f"Next steps:")
    print(f"  1. Create {args.project_dir / 'audio' / 'beat-map.json'} (manually or with AI)")
    print(f"  2. Create {args.project_dir / 'audio' / 'captions.json'} (manually or with AI)")
    print(f"  3. Run: python lib/validate.py {args.project_dir}")


def _resolve_provider(args):
    """Resolve transcription provider from args + env. Fail fast if misconfigured."""
    import os

    if args.provider == "mock":
        print("WARNING: Using mock transcription (dev only). Pass --provider whisper or local for real output.",
              file=sys.stderr)
        return MockProvider()

    if args.provider == "whisper":
        api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("ERROR: Whisper API provider requires OPENAI_API_KEY.\n"
                  "  Set it in .env or pass --api-key <key>\n"
                  "  See .env.example for details.", file=sys.stderr)
            sys.exit(1)
        return WhisperAPIProvider(api_key=api_key)

    if args.provider == "local":
        try:
            import whisper  # noqa: F401
        except ImportError:
            print("ERROR: Local Whisper provider requires 'openai-whisper' package.\n"
                  "  Install: pip install openai-whisper\n"
                  "  Or use --provider whisper for the API instead.", file=sys.stderr)
            sys.exit(1)
        return LocalWhisperProvider(model=args.whisper_model)

    # No provider specified — check env for auto-detection
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        print("Auto-detected OPENAI_API_KEY — using Whisper API provider.", file=sys.stderr)
        return WhisperAPIProvider(api_key=api_key)

    # Try local whisper
    try:
        import whisper  # noqa: F401
        print("Auto-detected local whisper — using local provider.", file=sys.stderr)
        return LocalWhisperProvider(model=args.whisper_model)
    except ImportError:
        pass

    # Nothing available
    print("ERROR: No transcription provider configured.\n"
          "  Options:\n"
          "    1. Set OPENAI_API_KEY in .env (Whisper API)\n"
          "    2. pip install openai-whisper (local Whisper)\n"
          "    3. Pass --provider mock (dev only, fake output)\n"
          "  See .env.example for details.", file=sys.stderr)
    sys.exit(1)


def _run_full(args):
    """Full pipeline — extract + transcribe + beats + captions."""
    provider = _resolve_provider(args)

    try:
        result = ingest(args.input, args.project_dir, provider)
    except IngestError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Voice ingestion complete.")
    print(f"  Duration: {result.total_duration}s")
    print(f"  Beats:    {result.beat_count}")
    print(f"  Captions: {len(result.captions)}")
    print(f"  Audio:    {result.audio_path}")
    print(f"  Outputs:  {result.project_dir / 'audio/'}")


def main():
    parser = argparse.ArgumentParser(
        description="Voice ingestion pipeline",
        prog="python -m lib.ingest.cli",
    )
    subparsers = parser.add_subparsers(dest="command")

    # ── extract subcommand ───────────────────────────────────────────
    p_extract = subparsers.add_parser(
        "extract",
        help="Extract audio from video (no transcription). "
             "Output: projects/<slug>/audio/source.wav",
    )
    p_extract.add_argument("input", type=Path,
                           help="HeyGen avatar MP4 or any video/audio file")
    p_extract.add_argument("project_dir", type=Path,
                           help="Project directory")
    p_extract.set_defaults(func=_run_extract)

    # ── full subcommand ──────────────────────────────────────────────
    p_full = subparsers.add_parser(
        "full",
        help="Full pipeline: extract + transcribe + beats + captions",
    )
    p_full.add_argument("input", type=Path,
                        help="Audio file or HeyGen video")
    p_full.add_argument("project_dir", type=Path,
                        help="Project directory")
    p_full.add_argument(
        "--provider", choices=["whisper", "local", "mock"], default=None,
        help="Transcription provider. Auto-detects from env if omitted. "
             "Mock requires explicit --provider mock.",
    )
    p_full.add_argument("--api-key", type=str, default=None,
                        help="OpenAI API key for Whisper API provider")
    p_full.add_argument("--whisper-model", type=str, default="base",
                        help="Local Whisper model size (default: base)")
    p_full.set_defaults(func=_run_full)

    args = parser.parse_args()

    # ── Backward compatibility: no subcommand = full pipeline ────────
    if args.command is None:
        # Check if old-style positional args were given
        if len(sys.argv) >= 3 and not sys.argv[1].startswith("-"):
            # Reparse with full subcommand prepended
            sys.argv.insert(1, "full")
            args = parser.parse_args()
        else:
            parser.print_help()
            sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
