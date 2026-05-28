"""
GeminiService — outbound adapter that implements ``AIService`` via Google Gemini.

This module uses the **new** ``google-genai`` SDK (the ``google-generativeai``
package is deprecated).  The client is initialised with an API key read from
the environment, and the model name and prompt template path are taken from
the application ``Settings``.

Dependency direction (correct for Ports & Adapters):
    adapters/outbound/gemini  →  core/ports  →  core/domain
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from google import genai
from google.genai import types

from core.config.settings import Settings
from core.domain.exceptions import AIServiceError
from core.ports.ai_service import AIService

logger = logging.getLogger(__name__)

# ── Prompt / CV separator ────────────────────────────────────────────────
_CV_DELIMITER = "\n\n--- CV TEXT ---\n\n"


class GeminiService(AIService):
    """Concrete ``AIService`` backed by Google Gemini.

    Parameters
    ----------
    settings:
        The application ``Settings`` instance (injected by the composition
        root).  The adapter reads ``settings.ai.*`` for model name, prompt
        file path, and the name of the environment variable that holds the
        API key.
    """

    # ── construction ─────────────────────────────────────────────────

    def __init__(self, settings: Settings) -> None:
        # 1. Resolve the API key from the environment
        api_key = os.environ.get(settings.ai.api_key_env, "").strip()
        if not api_key:
            raise ValueError(
                f"Gemini API key not found. Set the environment variable "
                f"'{settings.ai.api_key_env}' before starting the server. "
                f"Example: export {settings.ai.api_key_env}=your_key_here"
            )

        # 2. Instantiate the google-genai client (new SDK)
        self.client = genai.Client(api_key=api_key)

        # 3. Store the model name for later API calls
        self.model_name: str = settings.ai.model_name

        # 4. Load the prompt template from disk
        prompt_path = Path(settings.ai.prompts_file_path)
        if not prompt_path.is_file():
            raise FileNotFoundError(
                f"Prompt template not found at '{prompt_path.resolve()}'. "
                f"Ensure the file exists or update 'ai.prompts_file_path' "
                f"in config.yaml."
            )
        self._prompt_template: str = prompt_path.read_text(encoding="utf-8")

        logger.info(
            "GeminiService initialised | model=%s | prompt_file=%s",
            self.model_name,
            prompt_path,
        )

    # ── public API ───────────────────────────────────────────────────

    def parse_cv(self, text: str) -> dict:
        """Send CV text to Gemini and return a dict of candidate fields.

        Raises
        ------
        AIServiceError
            Wraps any Gemini SDK or network error with a descriptive message.
        ValueError
            If the model response is not valid JSON.
        """
        full_prompt = self._prompt_template + _CV_DELIMITER + text

        logger.debug(
            "Calling Gemini API | model=%s | input_chars=%d",
            self.model_name,
            len(text),
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
        except Exception as exc:
            msg = self._describe_api_error(exc)
            raise AIServiceError(msg) from exc

        raw: str = response.text
        logger.debug("Gemini raw response: %s", raw)

        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error("JSON parse failure — raw response: %s", raw)
            raise ValueError(
                f"Could not parse Gemini response as JSON: {raw}"
            ) from exc

    # ── private helpers ──────────────────────────────────────────────

    @staticmethod
    def _describe_api_error(exc: Exception) -> str:
        """Return a human-friendly message for common Gemini SDK errors."""
        exc_type = type(exc).__name__
        exc_text = str(exc).lower()

        if "auth" in exc_text or "api key" in exc_text or "401" in exc_text:
            return (
                f"Gemini authentication failed — check that your API key "
                f"is valid and has not been revoked. ({exc_type}: {exc})"
            )

        if "quota" in exc_text or "rate" in exc_text or "429" in exc_text:
            return (
                f"Gemini rate-limit / quota exceeded — wait and retry or "
                f"upgrade your plan. ({exc_type}: {exc})"
            )

        if "not found" in exc_text or "404" in exc_text:
            return (
                f"Gemini model not found — verify 'ai.model_name' in "
                f"config.yaml. ({exc_type}: {exc})"
            )

        if "permission" in exc_text or "403" in exc_text:
            return (
                f"Gemini permission denied — your API key may lack access "
                f"to this model. ({exc_type}: {exc})"
            )

        if "deadline" in exc_text or "timeout" in exc_text:
            return (
                f"Gemini request timed out — the service may be temporarily "
                f"unavailable. ({exc_type}: {exc})"
            )

        return (
            f"Gemini API call failed with an unexpected error. "
            f"({exc_type}: {exc})"
        )
