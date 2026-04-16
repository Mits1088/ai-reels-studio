"""Abstract base class for all URL extractors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..url_router import IngestionResult


class BaseExtractor(ABC):
    """Every extractor must implement extract() and return an IngestionResult."""

    @abstractmethod
    def extract(
        self,
        url: str,
        project_dir: Path,
        *,
        frames_every: float = 5.0,
        **kwargs,
    ) -> IngestionResult:
        """
        Extract all useful content from a URL.

        Args:
            url:          The source URL.
            project_dir:  Project directory — all outputs go here.
            frames_every: For video sources, seconds between extracted frames.

        Returns:
            IngestionResult with text, frames, assets, and metadata populated.
        """
        ...
