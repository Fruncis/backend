"""
CandidateORM — SQLAlchemy table-mapped model for the ``candidates`` table.

In the Ports and Adapters pattern, ORM models live in the **outbound adapter**
layer.  They mirror the domain entity's attributes but add persistence
concerns (column types, constraints, default generation).  The domain layer
is unaware of this class; mapping between ``Candidate`` (domain) and
``CandidateORM`` (infrastructure) is handled by the repository adapter.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from adapters.outbound.postgres.database import Base


class CandidateORM(Base):
    """SQLAlchemy model mapped to the ``candidates`` PostgreSQL table.

    Each column corresponds to a field on the domain ``Candidate`` dataclass.
    The table uses a server-side UUID primary key and records a ``created_at``
    timestamp defaulting to the current UTC time.
    """

    __tablename__ = "candidates"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String(320), nullable=False, unique=True)
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(2048), nullable=True)
    github_url = Column(String(2048), nullable=True)
    experience_summary = Column(Text, nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<CandidateORM(id={self.id!r}, email={self.email!r})>"
        )
