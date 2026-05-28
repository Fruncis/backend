"""
AIService port — abstract interface for AI-powered document analysis.

This is a *driven port* (outbound) in the Ports and Adapters architecture.
Use-case code depends only on this abstraction; the concrete implementation
(e.g. ``GeminiService``) is injected at runtime.

**Architectural constraint**: this module lives in ``core/ports/`` and MUST
NOT import from ``adapters/``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class AIService(ABC):
    """Contract for an AI service capable of parsing CV / résumé text.

    Implementations are expected to call a remote LLM and return a dict
    whose keys map to the fields of the ``Candidate`` domain entity.
    """

    @abstractmethod
    def parse_cv(self, text: str) -> dict:
        """Takes raw CV text and returns a dict with extracted candidate fields.

        Parameters
        ----------
        text:
            The full plain-text content extracted from a CV document.

        Returns
        -------
        dict
            A mapping of candidate field names (``first_name``, ``last_name``,
            ``email``, etc.) to their extracted values.

        Raises
        ------
        core.domain.exceptions.AIServiceError
            If the underlying AI service call fails for any reason.
        """
        ...
