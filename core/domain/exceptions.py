"""
Domain exceptions — custom exception hierarchy for the business layer.

These exceptions live in core/domain/ and are pure Python: no framework or
infrastructure imports.  Use-case and adapter layers catch or raise them to
communicate domain-level failures without leaking infrastructure details.
"""


class AIServiceError(Exception):
    """Raised when the external AI service (e.g. Gemini) fails.

    Wraps lower-level transport, authentication, quota, and model errors
    so that upstream code can handle "AI unavailable" uniformly.
    """


class CVParsingError(Exception):
    """Raised when a CV / résumé cannot be parsed into structured data.

    This covers format issues (unreadable PDF, empty text) as well as
    semantic failures (the AI returned data that doesn't match the
    expected schema).
    """


class CandidateNotFoundError(Exception):
    """Raised when a requested Candidate does not exist in the repository."""
