"""
PDF segmentation utility for the CV processing pipeline.

Why segment PDFs before sending them to an AI model?

1. **Token limits** — Large language models impose a maximum context window.
   A 15-page academic CV can easily exceed that limit.  Splitting the
   document into manageable chunks ensures every piece of content can be
   processed without silent truncation.

2. **Error isolation** — If a single page is corrupt, garbled by OCR, or
   contains only images (no extractable text), segmentation lets the
   pipeline skip or retry that segment instead of failing the entire
   document.

3. **Layout handling** — CVs come in wildly different layouts (single-column
   American résumés, two-column European Europass, multi-section academic
   CVs).  Page-level and paragraph-level splitting gives downstream
   components a consistent unit of work regardless of the original format.
"""

from __future__ import annotations

import io
import logging
from typing import List

from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError

from core.ports.pdf_segmenter import PDFSegmenterPort

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────

_PAGE_SEPARATOR_TEMPLATE = "\n--- PAGE {n} ---\n"
_PDF_MAGIC = b"%PDF-"


class PDFSegmenter(PDFSegmenterPort):
    """Extract, validate, and chunk text from PDF files.

    Implements :class:`~core.ports.pdf_segmenter.PDFSegmenterPort` so that
    the use-case layer can depend on the abstract interface while this
    concrete class provides the real PDF-handling behaviour.

    All methods are stateless and operate on raw ``bytes`` so the caller
    does not need to manage file handles or temporary files.
    """

    # ── public API ───────────────────────────────────────────────────

    def extract_text(self, file_bytes: bytes) -> str:
        """Extract all text from a PDF, concatenating pages with separators.

        Parameters
        ----------
        file_bytes:
            Raw bytes of the PDF file.

        Returns
        -------
        str
            The full extracted text with pages delimited by
            ``--- PAGE {n} ---`` markers, or an empty string if
            extraction fails for any reason.
        """
        try:
            reader = self._build_reader(file_bytes)
            pages: List[str] = []

            for idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                pages.append(
                    _PAGE_SEPARATOR_TEMPLATE.format(n=idx) + text
                )

            full_text = "".join(pages)
            total_chars = len(full_text)

            logger.debug(
                "PDF text extracted | pages=%d | total_chars=%d",
                len(reader.pages),
                total_chars,
            )

            if not full_text.strip():
                logger.warning(
                    "PDF text extraction produced an empty result — "
                    "the file may contain only scanned images with no "
                    "embedded text layer."
                )
                return ""

            return full_text

        except ValueError:
            # Re-raise ValueErrors we created (e.g. encrypted PDF).
            raise
        except PdfReadError as exc:
            logger.warning(
                "Failed to read PDF (file may be corrupt): %s", exc
            )
            return ""
        except Exception:
            logger.error(
                "Unexpected error during PDF text extraction",
                exc_info=True,
            )
            return ""

    def extract_pages(self, file_bytes: bytes) -> List[str]:
        """Return a list of per-page text, excluding empty pages.

        Parameters
        ----------
        file_bytes:
            Raw bytes of the PDF file.

        Returns
        -------
        list[str]
            One string per non-empty page, in document order.
        """
        reader = self._build_reader(file_bytes)
        pages: List[str] = []

        for page in reader.pages:
            text = (page.extract_text() or "").strip()
            if text:
                pages.append(text)

        return pages

    def extract_and_chunk(
        self,
        file_bytes: bytes,
        max_chars: int = 4000,
    ) -> List[str]:
        """Extract text from a PDF and split it into chunks.

        Chunking strategy (in priority order):

        1. Break at double newlines (paragraph boundaries).
        2. Fall back to single newlines.
        3. Last resort: hard cut at ``max_chars``, breaking at the last
           space before the limit so words are never split mid-token.

        Parameters
        ----------
        file_bytes:
            Raw bytes of the PDF file.
        max_chars:
            Maximum number of characters per chunk (default 4 000).

        Returns
        -------
        list[str]
            Non-empty text chunks, each at most *max_chars* characters.
        """
        full_text = self.extract_text(file_bytes)
        if not full_text:
            return []

        chunks = self._split_into_chunks(full_text, max_chars)

        sizes = [len(c) for c in chunks]
        logger.debug(
            "PDF chunked | num_chunks=%d | sizes=%s",
            len(chunks),
            sizes,
        )

        return chunks

    def is_valid_pdf(self, file_bytes: bytes) -> bool:
        """Check whether *file_bytes* starts with the PDF magic number.

        Parameters
        ----------
        file_bytes:
            Raw bytes to inspect.

        Returns
        -------
        bool
            ``True`` if the bytes begin with ``%PDF-``.
        """
        result = file_bytes[:5] == _PDF_MAGIC
        logger.debug(
            "PDF magic-number check | valid=%s | first_bytes=%r",
            result,
            file_bytes[:16],
        )
        return result

    # ── private helpers ──────────────────────────────────────────────

    @staticmethod
    def _build_reader(file_bytes: bytes) -> PdfReader:
        """Construct a ``PdfReader`` from raw bytes.

        Raises
        ------
        ValueError
            If the PDF is encrypted / password-protected.
        """
        reader = PdfReader(io.BytesIO(file_bytes))

        if reader.is_encrypted:
            raise ValueError(
                "The uploaded PDF is password-protected and cannot be "
                "read. Please upload an unencrypted version of the CV."
            )

        return reader

    @staticmethod
    def _split_into_chunks(text: str, max_chars: int) -> List[str]:
        """Split *text* into chunks of at most *max_chars* characters.

        Strategy
        --------
        1. Try to break at a double-newline (paragraph boundary).
        2. Fall back to a single newline.
        3. Last resort: find the last space before *max_chars*.
        4. Absolute last resort: hard cut at *max_chars* (only when the
           text contains no whitespace at all in the window).
        """
        chunks: List[str] = []
        remaining = text

        while remaining:
            # If what's left fits in one chunk we're done.
            if len(remaining) <= max_chars:
                stripped = remaining.strip()
                if stripped:
                    chunks.append(stripped)
                break

            window = remaining[:max_chars]

            # 1. Try double-newline (paragraph boundary).
            split_pos = window.rfind("\n\n")

            # 2. Fall back to single newline.
            if split_pos == -1:
                split_pos = window.rfind("\n")

            # 3. Fall back to last space (never cut mid-word).
            if split_pos == -1:
                split_pos = window.rfind(" ")

            # 4. Absolute last resort: hard cut.
            if split_pos == -1:
                split_pos = max_chars

            chunk = remaining[:split_pos].strip()
            if chunk:
                chunks.append(chunk)

            # Advance past the split point (skip the delimiter character).
            remaining = remaining[split_pos:].lstrip("\n")

        return chunks
