"""CLI entry point for lib.assets.

Run with: python -m lib.assets <verb> [args...]

Verbs:
  brand <name> [--color HEX] [--out DIR] [--project SLUG]
      Fetch a SaaS brand SVG via Simple Icons CDN.

  ai-brand <name> [--out DIR] [--project SLUG]
      Extract an AI/LLM brand SVG from @lobehub/icons (must be installed
      in remotion/node_modules).

  ai-brands
      List all AI/LLM brands available in the installed @lobehub/icons.

  brands <name1> <name2> ... [--color HEX] [--out DIR] [--project SLUG]
      Batch-fetch multiple SaaS brand logos via Simple Icons.

  youtube fetch <url> [--out DIR] [--project SLUG] [--frames-every SECONDS]
      Download a YouTube video, transcript, and (optionally) extract frames.

  youtube transcript <url> [--out FILE]
      Download only the transcript / captions for a YouTube video.

  pexels search <query> [--limit N] [--orientation portrait|landscape]
      [--download DIR] [--project SLUG]
      Search and optionally download Pexels stock videos. Needs PEXELS_API_KEY.

  pixabay search <query> [--limit N] [--download DIR] [--project SLUG]
      Search and optionally download Pixabay stock videos. Needs PIXABAY_API_KEY.

  coverr search <query> [--limit N] [--download DIR] [--project SLUG]
      Search and optionally download Coverr stock videos. Needs COVERR_API_KEY.

  catalog <project-dir>
      Print a summary of the project's sourced asset catalog.

  attribution <project-dir>
      List all assets in the catalog that require attribution credits.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import catalog, coverr, lobehub, pexels, pixabay, simpleicons, youtube


def _project_assets_dir(project_slug: str | None, sub: str) -> Path | None:
    if project_slug is None:
        return None
    base = Path("projects") / project_slug / "assets" / "sourced" / sub
    return base


def _resolve_out(args, sub: str) -> tuple[Path, Path | None]:
    """Resolve out_dir and project_dir from args.

    Priority:
      1. --out is explicit -> use it; project_dir = projects/<slug> if --project given
      2. --project given without --out -> projects/<slug>/assets/sourced/<sub>
      3. neither -> error
    """
    project_dir = Path("projects") / args.project if args.project else None
    if args.out:
        return Path(args.out), project_dir
    if args.project:
        return _project_assets_dir(args.project, sub), project_dir  # type: ignore
    raise SystemExit("Either --out DIR or --project SLUG is required")


def cmd_brand(args) -> int:
    out_dir, project_dir = _resolve_out(args, "brands")
    try:
        path = simpleicons.fetch(
            args.name, out_dir, color=args.color, project_dir=project_dir
        )
        print(f"  ✓ {args.name} → {path}")
        return 0
    except Exception as e:
        print(f"  ! failed: {e}", file=sys.stderr)
        return 1


def cmd_brands(args) -> int:
    out_dir, project_dir = _resolve_out(args, "brands")
    paths = simpleicons.fetch_many(
        args.names, out_dir, color=args.color, project_dir=project_dir
    )
    print(f"  ✓ fetched {len(paths)}/{len(args.names)} brand logos")
    for p in paths:
        print(f"    - {p}")
    return 0 if len(paths) == len(args.names) else 1


def cmd_ai_brand(args) -> int:
    out_dir, project_dir = _resolve_out(args, "ai-brands")
    try:
        path = lobehub.fetch(args.name, out_dir, project_dir=project_dir)
        print(f"  ✓ {args.name} → {path}")
        return 0
    except Exception as e:
        print(f"  ! failed: {e}", file=sys.stderr)
        return 1


def cmd_ai_brands(args) -> int:
    try:
        brands = lobehub.list_brands()
        for b in brands:
            print(b)
        print(f"\n{len(brands)} brands available", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"  ! failed: {e}", file=sys.stderr)
        return 1


def cmd_youtube_fetch(args) -> int:
    out_dir, project_dir = _resolve_out(args, "youtube")
    try:
        result = youtube.download(args.url, out_dir, project_dir=project_dir)
        print(f"  ✓ {result['title']}")
        print(f"    channel : {result['channel']}")
        print(f"    duration: {result['duration_s']:.1f}s")
        print(f"    video   : {result['video_path']}")
        if result["subs_path"]:
            print(f"    subs    : {result['subs_path']}")
            text_path = Path(result["subs_path"]).with_suffix(".txt")
            text_path.write_text(
                youtube.vtt_to_text(Path(result["subs_path"])), encoding="utf-8"
            )
            print(f"    text    : {text_path}")
        if args.frames_every:
            frames = youtube.extract_frames(
                Path(result["video_path"]),
                Path(out_dir) / "frames",
                every_seconds=args.frames_every,
                project_dir=project_dir,
                attribution_text=f"{result['channel']} via YouTube",
            )
            print(f"    frames  : {len(frames)} extracted ({args.frames_every}s interval)")
        return 0
    except Exception as e:
        print(f"  ! failed: {e}", file=sys.stderr)
        return 1


def cmd_youtube_transcript(args) -> int:
    try:
        result = youtube.download(
            args.url,
            Path(args.out or ".").parent if args.out else Path("."),
            write_subs=True,
            write_auto_subs=True,
        )
        if not result["subs_path"]:
            print("  ! no transcript available", file=sys.stderr)
            return 1
        text = youtube.vtt_to_text(Path(result["subs_path"]))
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
            print(f"  ✓ transcript → {args.out}")
        else:
            print(text)
        return 0
    except Exception as e:
        print(f"  ! failed: {e}", file=sys.stderr)
        return 1


def cmd_pexels_search(args) -> int:
    if args.download:
        out_dir, project_dir = _resolve_out(args, "pexels")
        paths = pexels.search_and_download_videos(
            args.query,
            out_dir,
            project_dir=project_dir,
            limit=args.limit,
            orientation=args.orientation,
        )
        print(f"  ✓ downloaded {len(paths)} videos")
        return 0 if paths else 1
    results = pexels.search_videos(
        args.query, per_page=args.limit, orientation=args.orientation
    )
    print(json.dumps(results, indent=2))
    return 0


def cmd_pixabay_search(args) -> int:
    if args.download:
        out_dir, project_dir = _resolve_out(args, "pixabay")
        paths = pixabay.search_and_download_videos(
            args.query, out_dir, project_dir=project_dir, limit=args.limit
        )
        print(f"  ✓ downloaded {len(paths)} videos")
        return 0 if paths else 1
    results = pixabay.search_videos(args.query, per_page=args.limit)
    print(json.dumps(results, indent=2))
    return 0


def cmd_coverr_search(args) -> int:
    if args.download:
        out_dir, project_dir = _resolve_out(args, "coverr")
        paths = coverr.search_and_download_videos(
            args.query, out_dir, project_dir=project_dir, limit=args.limit
        )
        print(f"  ✓ downloaded {len(paths)} videos")
        return 0 if paths else 1
    results = coverr.search_videos(args.query, per_page=args.limit)
    print(json.dumps(results, indent=2))
    return 0


def cmd_catalog(args) -> int:
    project_dir = Path(args.project_dir)
    if not project_dir.exists():
        print(f"  ! project not found: {project_dir}", file=sys.stderr)
        return 1
    summary = catalog.summarize(project_dir)
    print(json.dumps(summary, indent=2))
    print()
    for asset in catalog.load(project_dir):
        attr = " [ATTRIB REQ]" if asset.attribution_required else ""
        print(f"  {asset.source:12s} {asset.asset_type:10s} {asset.local_path}{attr}")
    return 0


def cmd_attribution(args) -> int:
    project_dir = Path(args.project_dir)
    if not project_dir.exists():
        print(f"  ! project not found: {project_dir}", file=sys.stderr)
        return 1
    items = catalog.list_attribution(project_dir)
    if not items:
        print("  ✓ no assets require attribution")
        return 0
    print(f"  Assets requiring attribution ({len(items)}):\n")
    for a in items:
        print(f"  - {a.local_path}")
        print(f"    {a.attribution_text or '(no attribution text recorded)'}")
        print()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m lib.assets")
    sub = parser.add_subparsers(dest="verb", required=True)

    p = sub.add_parser("brand", help="Fetch a SaaS brand logo via Simple Icons")
    p.add_argument("name")
    p.add_argument("--color", default=None)
    p.add_argument("--out", default=None)
    p.add_argument("--project", default=None)
    p.set_defaults(func=cmd_brand)

    p = sub.add_parser("brands", help="Batch fetch multiple brand logos")
    p.add_argument("names", nargs="+")
    p.add_argument("--color", default=None)
    p.add_argument("--out", default=None)
    p.add_argument("--project", default=None)
    p.set_defaults(func=cmd_brands)

    p = sub.add_parser("ai-brand", help="Extract an AI/LLM brand SVG from LobeHub")
    p.add_argument("name")
    p.add_argument("--out", default=None)
    p.add_argument("--project", default=None)
    p.set_defaults(func=cmd_ai_brand)

    p = sub.add_parser("ai-brands", help="List available AI/LLM brands in LobeHub")
    p.set_defaults(func=cmd_ai_brands)

    yt = sub.add_parser("youtube", help="YouTube source utilities")
    yt_sub = yt.add_subparsers(dest="yt_verb", required=True)

    p = yt_sub.add_parser("fetch", help="Download a YouTube video + transcript")
    p.add_argument("url")
    p.add_argument("--out", default=None)
    p.add_argument("--project", default=None)
    p.add_argument("--frames-every", type=float, default=None,
                   help="Extract frames every N seconds")
    p.set_defaults(func=cmd_youtube_fetch)

    p = yt_sub.add_parser("transcript", help="Download a transcript only")
    p.add_argument("url")
    p.add_argument("--out", default=None)
    p.set_defaults(func=cmd_youtube_transcript)

    px = sub.add_parser("pexels", help="Pexels stock video search")
    px_sub = px.add_subparsers(dest="px_verb", required=True)
    p = px_sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--orientation", choices=["portrait", "landscape", "square"], default="portrait")
    p.add_argument("--download", action="store_true",
                   help="Download top results to --out / --project")
    p.add_argument("--out", default=None)
    p.add_argument("--project", default=None)
    p.set_defaults(func=cmd_pexels_search)

    pb = sub.add_parser("pixabay", help="Pixabay stock video search")
    pb_sub = pb.add_subparsers(dest="pb_verb", required=True)
    p = pb_sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--download", action="store_true")
    p.add_argument("--out", default=None)
    p.add_argument("--project", default=None)
    p.set_defaults(func=cmd_pixabay_search)

    cv = sub.add_parser("coverr", help="Coverr stock video search")
    cv_sub = cv.add_subparsers(dest="cv_verb", required=True)
    p = cv_sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--download", action="store_true")
    p.add_argument("--out", default=None)
    p.add_argument("--project", default=None)
    p.set_defaults(func=cmd_coverr_search)

    p = sub.add_parser("catalog", help="Show project sourced asset catalog")
    p.add_argument("project_dir")
    p.set_defaults(func=cmd_catalog)

    p = sub.add_parser("attribution", help="List assets requiring attribution")
    p.add_argument("project_dir")
    p.set_defaults(func=cmd_attribution)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
