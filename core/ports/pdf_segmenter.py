"""
PDFSegmenter port — abstract interface for PDF validation and text extraction.

This is a *driven port* (outbound) in the Ports and Adapters architecture.
Use-case code depends only on this abstraction; the concrete implementation
(e.g. the ``PDFSegmenter`` in ``adapters/utils/``) is injected at runtime.

**Architectural constraint**: this module lives in ``core/ports/`` and MUST
NOT import from ``adapters/``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class PDFSegmenterPort(ABC):
    """Abstract contract for PDF validation and text extraction.

    Every concrete adapter that handles PDF processing must implement this
    interface so the domain / use-case layer can remain infrastructure-agnostic.
    """

    @abstractmethod
    def is_valid_pdf(self, file_bytes: bytes) -> bool:
        """Return ``True`` if *file_bytes* appears to be a valid PDF."""
        ...

    @abstractmethod
    def extract_text(self, file_bytes: bytes) -> str:
        """Extract all text from a PDF, returning an empty string on failure."""
        ...
