"""
PostgresCandidateRepository — concrete outbound adapter for candidate
persistence backed by PostgreSQL via SQLAlchemy.

In the Ports and Adapters architecture this class is an **outbound adapter**
(also called a *driven adapter*).  It implements the
``CandidateRepository`` port defined in the core and translates between
pure-domain ``Candidate`` dataclasses and SQLAlchemy ``CandidateORM`` rows.

The domain layer never imports this module directly; the adapter is wired
in at the composition root (e.g. FastAPI dependency injection) and injected
as a ``CandidateRepository`` abstraction.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from adapters.outbound.postgres.candidate_orm import CandidateORM
from core.domain.entities import Candidate
from core.ports.candidate_repository import CandidateRepository


class PostgresCandidateRepository(CandidateRepository):
    """Repository adapter that persists ``Candidate`` entities in PostgreSQL.

    Parameters
    ----------
    session:
        A SQLAlchemy ``Session`` instance, typically provided via
        ``Depends(get_db)`` in the FastAPI layer.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── public interface (port contract) ─────────────────────────────

    def save(self, candidate: Candidate) -> Candidate:
        """Persist a ``Candidate`` (insert or update).

        Uses ``Session.merge`` so that both new and existing candidates
        are handled transparently.

        Returns
        -------
        Candidate
            The domain entity reflecting the persisted state (including
            any server-generated defaults such as ``created_at``).
        """
        orm_obj = self._to_orm(candidate)
        merged: CandidateORM = self._session.merge(orm_obj)
        self._session.commit()
        self._session.refresh(merged)
        return self._to_domain(merged)

    def get_all(self) -> list[Candidate]:
        """Return every ``Candidate`` currently stored in the database."""
        rows: list[CandidateORM] = (
            self._session.query(CandidateORM).all()
        )
        return [self._to_domain(row) for row in rows]

    # ── private mappers ──────────────────────────────────────────────

    @staticmethod
    def _to_domain(orm_obj: CandidateORM) -> Candidate:
        """Map a ``CandidateORM`` row to a domain ``Candidate`` dataclass."""
        return Candidate(
            id=orm_obj.id,
            first_name=orm_obj.first_name,
            last_name=orm_obj.last_name,
            email=orm_obj.email,
            phone=orm_obj.phone,
            linkedin_url=orm_obj.linkedin_url,
            github_url=orm_obj.github_url,
            experience_summary=orm_obj.experience_summary,
            created_at=orm_obj.created_at,
        )

    @staticmethod
    def _to_orm(candidate: Candidate) -> CandidateORM:
        """Map a domain ``Candidate`` dataclass to a ``CandidateORM`` row."""
        return CandidateORM(
            id=candidate.id,
            first_name=candidate.first_name,
            last_name=candidate.last_name,
            email=candidate.email,
            phone=candidate.phone,
            linkedin_url=candidate.linkedin_url,
            github_url=candidate.github_url,
            experience_summary=candidate.experience_summary,
            created_at=candidate.created_at,
        )
