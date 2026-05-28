"""
Database bootstrap — SQLAlchemy engine, session factory and declarative base.

This module belongs to the **outbound adapter** layer in the Ports and
Adapters architecture.  It provides infrastructure plumbing that the ORM
models and repository implementations depend on, but the domain and port
layers never import from here directly.

Usage
-----
* ORM models inherit from ``Base``.
* The repository adapter receives a ``Session`` via dependency injection
  (FastAPI's ``Depends(get_db)``).
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from core.config.settings import get_settings

# ── Engine ───────────────────────────────────────────────────────────────

_settings = get_settings()

engine = create_engine(
    _settings.database.url,
    pool_pre_ping=True,
    echo=_settings.server.debug,
)

# ── Session factory ──────────────────────────────────────────────────────

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# ── Declarative base ────────────────────────────────────────────────────

Base = declarative_base()
"""All ORM models must inherit from this ``Base`` so that Alembic's
``target_metadata = Base.metadata`` picks up every table automatically."""


# ── Dependency injection helper ──────────────────────────────────────────


def get_db() -> Session:  # type: ignore[misc]
    """FastAPI-compatible dependency that yields a scoped ``Session``.

    The session is committed on success and closed (returned to the pool)
    in the ``finally`` block, regardless of outcome.

    Example
    -------
    .. code-block:: python

        @router.post("/candidates")
        def create_candidate(db: Session = Depends(get_db)):
            repo = PostgresCandidateRepository(db)
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
