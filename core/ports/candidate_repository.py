"""
CandidateRepository port — the abstract interface for candidate persistence.

In the Ports and Adapters architecture this module lives in the **core/ports**
package and defines a *driven port* (also called an *outbound port*).  The
domain and use-case layers depend only on this abstraction; the concrete
implementation (e.g. ``PostgresCandidateRepository``) is injected at runtime,
keeping the core free of infrastructure concerns.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.domain.entities import Candidate


class CandidateRepository(ABC):
    """Abstract contract for persisting and retrieving ``Candidate`` entities.

    Every concrete adapter that stores candidates (PostgreSQL, in-memory,
    file-based, etc.) must implement this interface so the domain layer
    can remain infrastructure-agnostic.
    """

    @abstractmethod
    def save(self, candidate: Candidate) -> Candidate:
        """Persist a ``Candidate`` (insert or update) and return the saved entity."""
        ...

    @abstractmethod
    def get_all(self) -> list[Candidate]:
        """Return every ``Candidate`` currently stored."""
        ...
