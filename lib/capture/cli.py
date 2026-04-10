"""
CLI entrypoint for asset registration.

Usage:
  python -m lib.capture.cli register <source-file> <project-dir> --type <type> --role <role> --beats <beat-01,beat-02> --desc "description"
  python -m lib.capture.cli demo <source-file> <project-dir> --beats <beat-03> --desc "deploy button click"
  python -m lib.capture.cli validate <project-dir>
  python -m lib.capture.cli finalize <project-dir>
"""

import argparse
import json
import sys
from pathlib import Path

from .register import register_asset, register_demo, finalize_assets, RegisterError
from .catalog import load_catalog
from .validate_catalog import validate_catalog


def main():
    parser = argparse.ArgumentParser(
        description="Asset capture and registration",
        prog="python -m lib.capture.cli",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── register ─────────────────────────────────────────────────────────
    reg = sub.add_parser("register", help="Register any asset")
    reg.add_argument("source", type=Path, help="Source file to import")
    reg.add_argument("project_dir", type=Path, help="Project directory")
    reg.add_argument("--type", required=True, dest="asset_type",
                     help="Asset type (video, image, logo, chart, icon, overlay, sfx, music)")
    reg.add_argument("--role", required=True,
                     help="Timeline role (avatar, demo, support, background, sfx, music)")
    reg.add_argument("--beats", required=True,
                     help="Comma-separated beat IDs (e.g., beat-01,beat-02)")
    reg.add_argument("--desc", required=True, help="What this asset shows and why")
    reg.add_argument("--scene", type=int, default=None, help="Scene number (optional)")
    reg.add_argument("--id", default=None, help="Custom asset ID (optional)")
    reg.add_argument("--source-method", default="import",
                     help="How obtained: capture, import, generate, brand-kit")

    # ── demo ─────────────────────────────────────────────────────────────
    demo = sub.add_parser("demo", help="Register a demo capture (shorthand)")
    demo.add_argument("source", type=Path, help="Screen recording file")
    demo.add_argument("project_dir", type=Path, help="Project directory")
    demo.add_argument("--beats", required=True, help="Comma-separated beat IDs")
    demo.add_argument("--desc", required=True, help="What the demo shows")
    demo.add_argument("--scene", type=int, default=None)
    demo.add_argument("--id", default=None)

    # ── validate ─────────────────────────────────────────────────────────
    val = sub.add_parser("validate", help="Validate catalog against beat map")
    val.add_argument("project_dir", type=Path, help="Project directory")

    # ── finalize ─────────────────────────────────────────────────────────
    fin = sub.add_parser("finalize", help="Mark project as assets_ready")
    fin.add_argument("project_dir", type=Path, help="Project directory")

    args = parser.parse_args()

    try:
        if args.command == "register":
            entry = register_asset(
                args.source, args.project_dir,
                asset_type=args.asset_type,
                role=args.role,
                linked_beats=[b.strip() for b in args.beats.split(",")],
                description=args.desc,
                scene=args.scene,
                asset_id=args.id,
                source=args.source_method,
            )
            print(f"Registered: {entry.id}")
            print(f"  File:  assets/{entry.filename}")
            print(f"  Type:  {entry.type} / {entry.role}")
            print(f"  Beats: {', '.join(entry.linked_beats)}")

        elif args.command == "demo":
            entry = register_demo(
                args.source, args.project_dir,
                linked_beats=[b.strip() for b in args.beats.split(",")],
                description=args.desc,
                scene=args.scene,
                asset_id=args.id,
            )
            print(f"Registered demo: {entry.id}")
            print(f"  File:  assets/{entry.filename}")
            print(f"  Beats: {', '.join(entry.linked_beats)}")

        elif args.command == "validate":
            assets_dir = args.project_dir / "assets"
            catalog = load_catalog(assets_dir / "catalog.json")

            # Load beat IDs if beat-map exists
            beat_ids = None
            bm_path = args.project_dir / "audio" / "beat-map.json"
            if bm_path.exists():
                with open(bm_path) as f:
                    bm = json.load(f)
                beat_ids = {b["id"] for b in bm.get("beats", [])}

            errs = validate_catalog(catalog, assets_dir=assets_dir, beat_ids=beat_ids)
            if errs:
                print(f"FAILED — {len(errs)} error(s):")
                for e in errs:
                    print(f"  {e}")
                sys.exit(1)
            else:
                print(f"PASSED — {len(catalog.assets)} asset(s) valid.")

        elif args.command == "finalize":
            finalize_assets(args.project_dir)
            print("Project marked as assets_ready.")

    except RegisterError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
