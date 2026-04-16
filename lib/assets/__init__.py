"""lib.assets — unified asset sourcing pipeline.

Provides programmatic access to free asset libraries used during reel
production: brand logos (LobeHub, Simple Icons), stock footage (Pexels,
Pixabay, Coverr), and source video (YouTube via yt-dlp).

All fetched assets are tracked in a per-project catalog for provenance.
See `python -m lib.assets --help` for the CLI surface.
"""

__all__ = [
    "catalog",
    "youtube",
    "lobehub",
    "simpleicons",
    "pexels",
    "pixabay",
    "coverr",
]
