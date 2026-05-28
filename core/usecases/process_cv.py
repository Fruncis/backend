"""
ProcessCV use case — orchestrates the end-to-end CV ingestion pipeline.

In the Ports and Adapters (Hexagonal) architecture this module sits in the
**application / use-case ring**.  It coordinates domain entities and outbound
ports to implement a single business workflow:

    raw PDF bytes  →  validate  →  extract text  →  AI parse  →  persist Candidate

All dependencies are constructor-injected as **abstract interfaces** defined
in ``core/ports/``.  This keeps the use case fully testable with simple
in-memory fakes and completely decoupled from infrastructure concerns
(FastAPI, SQLAlchemy, google-genai, PyPDF2, etc.).

**Architectural constraint** — this module lives in ``core/usecases/`` and
MUST import only from:

* ``core/domain/`` (entities, exceptions)
* ``core/ports/`` (abstract interfaces — never concrete implementations)
* Python standard library (``uuid``, ``datetime``, ``logging``)
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import uuid4

from core.domain.entities import Candidate
from core.domain.exceptions import CVParsingError
from core.ports.ai_service import AIService
from core.ports.candidate_repository import CandidateRepository
from core.ports.pdf_segmenter import PDFSegmenterPort

logger = logging.getLogger(__name__)


class ProcessCVUseCase:
    """Receive raw CV bytes, extract structured data, and persist a Candidate.

    This is the primary *driving* use case for CV ingestion.  It validates
    the incoming file, delegates text extraction and AI parsing to the
    appropriate outbound ports, maps the result to a ``Candidate`` domain
    entity, and writes it to the repository.

    Parameters
    ----------
    ai_service:
        An implementation of :class:`~core.ports.ai_service.AIService`.
    candidate_repository:
        An implementation of :class:`~core.ports.candidate_repository.CandidateRepository`.
    pdf_segmenter:
        An implementation of :class:`~core.ports.pdf_segmenter.PDFSegmenterPort`.
    """

    def __init__(
        self,
        ai_service: AIService,
        candidate_repository: CandidateRepository,
        pdf_segmenter: PDFSegmenterPort,
    ) -> None:
        self._ai_service = ai_service
        self._candidate_repository = candidate_repository
        self._pdf_segmenter = pdf_segmenter

    # ── public API ───────────────────────────────────────────────────

    def execute(self, file_bytes: bytes) -> Candidate:
        """Process a CV file from raw bytes to a persisted ``Candidate``.

        Parameters
        ----------
        file_bytes:
            The raw content of the uploaded PDF file.

        Returns
        -------
        Candidate
            The saved ``Candidate`` entity (as returned by the repository,
            which may have refreshed fields from the database).

        Raises
        ------
        CVParsingError
            If the file is not a valid PDF, contains no extractable text,
            or the AI cannot extract the candidate's name.
        AIServiceError
            Propagated as-is from the AI service if the remote call fails.
        """
        logger.info("ProcessCVUseCase.execute() started")

        # 1. Validate that the file is a genuine PDF.
        if not self._pdf_segmenter.is_valid_pdf(file_bytes):
            raise CVParsingError(
                f"The uploaded file does not appear to be a valid PDF "
                f"(size: {len(file_bytes)} bytes). Only PDF files are accepted."
            )
        logger.debug("PDF validation passed")

        # 2. Extract text from the PDF.
        extracted_text: str = self._pdf_segmenter.extract_text(file_bytes)

        if not extracted_text or not extracted_text.strip():
            raise CVParsingError(
                "Could not extract any text from the uploaded PDF. "
                "The file may be scanned/image-based without OCR, or "
                "corrupted. Please upload a text-selectable PDF."
            )
        logger.debug("Text extracted | chars=%d", len(extracted_text))

        # 3. Send extracted text to the AI service for structured parsing.
        logger.debug(
            "Calling AI service | text_preview=%s", extracted_text[:200]
        )
        raw_data: dict = self._ai_service.parse_cv(extracted_text)
        # AIServiceError is intentionally NOT caught — it already carries
        # a descriptive message and should propagate to the caller.
        logger.debug("AI service returned | keys=%s", list(raw_data.keys()))

        # 4. Map raw_data to a Candidate domain entity.
        candidate = Candidate(
            first_name=(raw_data.get("first_name") or "").strip(),
            last_name=(raw_data.get("last_name") or "").strip(),
            email=(raw_data.get("email") or "").strip().lower(),
            phone=raw_data.get("phone"),
            linkedin_url=raw_data.get("linkedin_url"),
            github_url=raw_data.get("github_url"),
            experience_summary=raw_data.get("experience_summary"),
            id=uuid4(),
            created_at=datetime.utcnow(),
        )
        logger.debug(
            "Candidate mapped | first_name=%s last_name=%s email=%s",
            candidate.first_name,
            candidate.last_name,
            candidate.email,
        )

        # 5. Validate that the AI extracted a usable name.
        if not candidate.first_name or not candidate.last_name:
            raise CVParsingError(
                f"Could not extract candidate name from the CV. "
                f"AI returned: first_name={raw_data.get('first_name')!r}, "
                f"last_name={raw_data.get('last_name')!r}. "
                f"The CV may be in an unsupported format or language."
            )

        # 6. Persist the candidate via the repository.
        #    CRITICAL: capture the return value — the repository may refresh
        #    fields from the database (e.g. server-generated timestamps).
        saved = self._candidate_repository.save(candidate)
        logger.info("Candidate saved | id=%s", saved.id)

        # 7. Return the repository's version, not the local variable.
        return saved
