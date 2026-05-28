"""
Pydantic response schemas for the Candidates REST API.

These models define the HTTP response shape and handle serialisation of
domain entities into JSON.  They live in the **inbound adapter** layer and
are allowed to import from ``core/domain/`` (dependency arrows point inward).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from core.domain.entities import Candidate


class CandidateResponse(BaseModel):
    """JSON representation of a ``Candidate`` returned by the API."""

    id: UUID
    first_name: str
    last_name: str
    email: str
    phone: str | None
    linkedin_url: str | None
    github_url: str | None
    experience_summary: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


def from_domain(candidate: Candidate) -> CandidateResponse:
    """Convert a domain ``Candidate`` dataclass to a ``CandidateResponse``.

    Using an explicit mapper keeps the boundary between domain and transport
    layers visible and testable.
    """
    return CandidateResponse(
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
