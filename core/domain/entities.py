"""
Domain Entities — pure Python dataclasses.

In Ports and Adapters (Hexagonal Architecture) the domain layer sits at the
very centre of the application.  Entities defined here carry **no** framework
or infrastructure dependencies (no SQLAlchemy, no Pydantic, no FastAPI).
They express the core business concepts and rules, and all other layers point
inward toward them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Candidate:
    """A person who has submitted (or been submitted for) a job position.

    This is the **aggregate root** of the Candidate bounded context.
    All persistence and transport details live outside this class — the
    ORM model maps *to* and *from* this dataclass via dedicated mappers in
    the outbound adapter.

    Field ordering note
    -------------------
    Python dataclasses require all fields *without* defaults to precede
    fields *with* defaults.  ``first_name``, ``last_name`` and ``email``
    are mandatory and therefore come first.
    """

    # ── required fields ──────────────────────────────────────────────
    first_name: str
    last_name: str
    email: str

    # ── optional fields ──────────────────────────────────────────────
    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    experience_summary: str | None = None

    # ── identity / auditing ──────────────────────────────────────────
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
