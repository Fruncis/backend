"""
Candidates router — REST endpoints for CV upload and candidate retrieval.

This module defines the inbound HTTP adapter for the Candidates bounded
context.  It translates HTTP requests into use-case calls and domain-port
calls, and maps domain objects / exceptions back to HTTP responses.

Dependency injection
--------------------
``ProcessCVUseCase`` and ``CandidateRepository`` are injected via FastAPI's
``Depends()`` mechanism.  The dependency factories are defined in the
application factory (``app.py``) and ensure that each request gets a **fresh
SQLAlchemy session** — avoiding stale identity-map bugs.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from adapters.inbound.fastapi.schemas import CandidateResponse, from_domain
from core.domain.exceptions import AIServiceError, CVParsingError
from core.ports.candidate_repository import CandidateRepository
from core.usecases.process_cv import ProcessCVUseCase

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Dependency Stubs (overridden in app.py) ──────────────────────────────


def stub_get_use_case() -> ProcessCVUseCase:
    raise NotImplementedError


def stub_get_repo() -> CandidateRepository:
    raise NotImplementedError


# ── POST /candidates ─────────────────────────────────────────────────────


@router.post(
    "/candidates",
    response_model=CandidateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a CV and create a Candidate",
)
async def create_candidate(
    cv_file: UploadFile,
    use_case: ProcessCVUseCase = Depends(stub_get_use_case),
) -> CandidateResponse:
    """Accept a PDF CV, extract structured data via AI, and persist.

    Returns the newly created ``Candidate`` with a 201 status code.

    Error responses
    ---------------
    * **422** — the file is not a PDF or the CV could not be parsed.
    * **503** — the AI service is unavailable.
    * **500** — an unexpected internal error.
    """
    logger.debug(
        "POST /candidates | filename=%s | content_type=%s",
        cv_file.filename,
        cv_file.content_type,
    )

    # Guard: content-type must be application/pdf
    if cv_file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid content type '{cv_file.content_type}'. "
                f"Only application/pdf is accepted."
            ),
        )

    file_bytes: bytes = await cv_file.read()
    logger.debug("File bytes read | size=%d", len(file_bytes))

    try:
        candidate = use_case.execute(file_bytes)
    except CVParsingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error in POST /candidates")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal error occurred. Check server logs for details.",
        ) from exc

    logger.info("Candidate created | id=%s", candidate.id)
    return from_domain(candidate)


# ── GET /candidates ──────────────────────────────────────────────────────


@router.get(
    "/candidates",
    response_model=list[CandidateResponse],
    status_code=status.HTTP_200_OK,
    summary="List all candidates",
)
async def list_candidates(
    repo: CandidateRepository = Depends(stub_get_repo),
) -> list[CandidateResponse]:
    """Return every ``Candidate`` currently stored.

    Returns an empty list ``[]`` when no candidates exist — never 404.
    """
    logger.debug("GET /candidates")

    candidates = repo.get_all()
    logger.debug("GET /candidates | count=%d", len(candidates))

    return [from_domain(c) for c in candidates]
