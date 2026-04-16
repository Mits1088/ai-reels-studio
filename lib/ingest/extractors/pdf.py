"""PDF URL extractor.

Downloads a PDF from a URL and extracts its text content.

Requirements:
  pip install pdfplumber requests
  (gracefully degrades if pdfplumber is not installed)
"""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

from .base import BaseExtractor
from ..url_router import IngestionResult


class PDFExtractor(BaseExtractor):
    """Download a PDF and extract its text."""

    def extract(
        self,
        url: str,
        project_dir: Path,
        *,
        frames_every: float = 5.0,
        **kwargs,
    ) -> IngestionResult:
        assets_dir = project_dir / "assets" / "sourced"
        assets_dir.mkdir(parents=True, exist_ok=True)

        # Derive a filename from the URL
        url_stem = url.rstrip("/").split("/")[-1].split("?")[0]
        if not url_stem.lower().endswith(".pdf"):
            url_stem += ".pdf"
        pdf_path = assets_dir / url_stem

        print(f"  → Downloading PDF: {url_stem} …")

        # ── Download ─────────────────────────────────────────────────────────
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; reel-pipeline/1.0)"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                pdf_path.write_bytes(resp.read())
            print(f"  ✓ Downloaded {pdf_path.stat().st_size // 1024}KB")
        except Exception as e:
            print(f"  ✗ Download failed: {e}")
            return IngestionResult(
                source_url=url,
                source_type="pdf",
                title="(download failed)",
                text_content="",
                key_claims=[],
                frames=[],
                assets=[],
                metadata={"error": str(e)},
            )

        # ── Extract text ──────────────────────────────────────────────────────
        text_content = ""
        title = url_stem.replace(".pdf", "").replace("-", " ").replace("_", " ").title()

        try:
            import pdfplumber
            with pdfplumber.open(str(pdf_path)) as pdf:
                pages: list[str] = []
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        pages.append(t.strip())
                text_content = "\n\n".join(pages)

            # Try to find a title from the first non-empty lines
            first_lines = [ln.strip() for ln in text_content.splitlines() if ln.strip()]
            if first_lines:
                title = first_lines[0][:120]

            print(f"  ✓ Text extracted: {len(text_content.split())} words, {len(pages)} pages")

        except ImportError:
            print("  ⚠  pdfplumber not installed — text extraction skipped")
            print("     Install: pip install pdfplumber")
        except Exception as e:
            print(f"  ⚠  Text extraction failed: {e}")

        key_claims = _claims_from_pdf_text(text_content)

        try:
            rel_path = str(pdf_path.relative_to(project_dir))
        except ValueError:
            rel_path = str(pdf_path)

        return IngestionResult(
            source_url=url,
            source_type="pdf",
            title=title,
            text_content=text_content,
            key_claims=key_claims,
            frames=[],
            assets=[rel_path],
            metadata={
                "filename": url_stem,
                "has_text": bool(text_content),
                "word_count": len(text_content.split()) if text_content else 0,
            },
        )


def _claims_from_pdf_text(text: str, max_claims: int = 20) -> list[str]:
    """Extract notable sentences from PDF text."""
    if not text:
        return []

    # Split on sentence boundaries
    sentences = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
    claims = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 25:
            continue
        score = 0
        if re.search(r"\d+[x%]|\d+\s*(times|percent|faster|better|more|less)", sent, re.I):
            score += 3
        if re.search(r"\b(finding|result|show|demonstrate|improve|outperform|achieve)\b", sent, re.I):
            score += 2
        if re.search(r"\b(propose|introduce|present|novel|first|state-of-the-art)\b", sent, re.I):
            score += 2
        if score > 0:
            claims.append(sent)
        if len(claims) >= max_claims:
            break

    return claims or [s.strip() for s in sentences[:max_claims] if len(s.strip()) > 25]
