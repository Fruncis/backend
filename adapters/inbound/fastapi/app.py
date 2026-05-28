"""
FastAPI application factory — the composition root for the HTTP layer.

This is the **only** place where concrete adapters (PostgreSQL, Gemini, PDF
segmenter) are instantiated and wired into use cases via FastAPI's dependency
injection system.

CRITICAL — session management
------------------------------
Each HTTP request receives a **fresh** SQLAlchemy ``Session`` via
``Depends(get_db)``.  Never create a shared session at startup — doing so
caches a stale identity map and causes GET to return ``[]`` after POST
creates rows in a different session.
"""

from __future__ import annotations

import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from adapters.inbound.fastapi.routers.candidates_router import router as candidates_router
from adapters.outbound.gemini.gemini_service import GeminiService
from adapters.outbound.postgres.candidate_repository import PostgresCandidateRepository
from adapters.outbound.postgres.database import get_db
from adapters.utils.pdf_segmenter import PDFSegmenter
from core.config.settings import Settings, get_settings
from core.ports.ai_service import AIService
from core.ports.candidate_repository import CandidateRepository
from core.ports.pdf_segmenter import PDFSegmenterPort
from core.usecases.process_cv import ProcessCVUseCase

logger = logging.getLogger(__name__)


# ── Dependency factories (one fresh session per request) ─────────────────


def get_candidate_repository(
    db: Session = Depends(get_db),
) -> CandidateRepository:
    """Create a ``PostgresCandidateRepository`` bound to the request session."""
    return PostgresCandidateRepository(db)


def get_ai_service() -> AIService:
    """Create a ``GeminiService`` — stateless, safe to construct per request."""
    return GeminiService(get_settings())


def get_pdf_segmenter() -> PDFSegmenterPort:
    """Create a ``PDFSegmenter`` — stateless, safe to construct per request."""
    return PDFSegmenter()


def get_process_cv_use_case(
    ai: AIService = Depends(get_ai_service),
    repo: CandidateRepository = Depends(get_candidate_repository),
    segmenter: PDFSegmenterPort = Depends(get_pdf_segmenter),
) -> ProcessCVUseCase:
    """Assemble the ``ProcessCVUseCase`` with all its dependencies."""
    return ProcessCVUseCase(ai, repo, segmenter)


# ── Application factory ─────────────────────────────────────────────────


def create_app(settings: Settings) -> FastAPI:
    """Build and configure the FastAPI application.

    Parameters
    ----------
    settings:
        Application settings (server, database, AI config).

    Returns
    -------
    FastAPI
        A fully configured application instance with middleware, dependency
        overrides, and mounted routers.
    """
    app = FastAPI(
        title="CV Processor API",
        description="Upload CVs as PDF, extract structured data via AI, and persist candidates.",
        version="1.0.0",
        debug=settings.server.debug,
    )

    # ── CORS ─────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Dependency overrides ─────────────────────────────────────────
    # Wire abstract types used in Depends() to concrete factories.
    from adapters.inbound.fastapi.routers.candidates_router import stub_get_use_case, stub_get_repo
    app.dependency_overrides[stub_get_use_case] = get_process_cv_use_case
    app.dependency_overrides[stub_get_repo] = get_candidate_repository

    # ── Routes ───────────────────────────────────────────────────────
    app.include_router(
        candidates_router,
        prefix="/api/v1",
        tags=["candidates"],
    )

    @app.get("/health", tags=["health"])
    async def health_check() -> dict:
        """Simple liveness probe."""
        return {"status": "ok"}

    logger.info(
        "FastAPI app created | debug=%s | routes=%d",
        settings.server.debug,
        len(app.routes),
    )

    return app
