from __future__ import annotations

import logging
from typing import Any, Literal, Protocol

from google import genai
from google.genai import types

from core.config import Settings

logger = logging.getLogger(__name__)


class AIServiceError(RuntimeError):
    """A safe, user-facing error from the Gemini service."""


class GeminiClient(Protocol):
    models: Any


class GeminiService:
    def __init__(self, settings: Settings, client: GeminiClient | None = None) -> None:
        self.settings = settings
        self._client = client

    def _get_client(self) -> GeminiClient:
        if self._client is not None:
            return self._client
        if not self.settings.api_key:
            raise AIServiceError(
                "Gemini is not configured. Add GEMINI_API_KEY to your local .env file or Streamlit secrets, "
                "then restart the app."
            )
        self._client = genai.Client(api_key=self.settings.api_key)
        return self._client

    @staticmethod
    def _safe_error(exc: Exception) -> AIServiceError:
        error_type = type(exc).__name__.casefold()
        details = str(exc).casefold()
        logger.warning("Gemini request failed (%s).", type(exc).__name__)
        if any(word in error_type + details for word in ("quota", "resourceexhausted", "rate limit", "429")):
            message = "Gemini's request quota or rate limit was reached. Wait a little and try again."
        elif any(word in error_type + details for word in ("unauthenticated", "permissiondenied", "401", "403", "api key")):
            message = "Gemini could not authenticate this request. Check that GEMINI_API_KEY is valid."
        elif any(word in error_type + details for word in ("notfound", "404", "model not found")):
            message = "The configured Gemini model is unavailable. Check GEMINI_MODEL or GEMINI_EMBEDDING_MODEL."
        elif any(word in error_type for word in ("connection", "timeout")):
            message = "Gemini could not be reached. Check your internet connection and try again."
        else:
            message = "Gemini could not complete the request. Check the configured model, network, and API quota."
        return AIServiceError(message)

    def generate_json(self, prompt: str, system_instruction: str | None = None) -> str:
        try:
            response = self._get_client().models.generate_content(
                model=self.settings.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    system_instruction=system_instruction,
                ),
            )
        except AIServiceError:
            raise
        except Exception as exc:
            raise self._safe_error(exc) from exc
        text = response.text
        if not text or not text.strip():
            raise AIServiceError("Gemini returned an empty response. Please try again.")
        return text.strip()

    def embed_texts(
        self,
        texts: list[str],
        task_type: Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"] = "RETRIEVAL_DOCUMENT",
    ) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = self._get_client().models.embed_content(
                model=self.settings.embedding_model,
                contents=texts,
                config=types.EmbedContentConfig(task_type=task_type),
            )
        except AIServiceError:
            raise
        except Exception as exc:
            raise self._safe_error(exc) from exc
        embeddings = response.embeddings
        if embeddings is None or len(embeddings) != len(texts):
            raise AIServiceError("Gemini returned an incomplete embedding response. Please retry.")
        vectors = [list(embedding.values or []) for embedding in embeddings]
        if any(not vector or any(not isinstance(value, (int, float)) for value in vector) for vector in vectors):
            raise AIServiceError("Gemini returned invalid document embeddings. Please retry.")
        return [[float(value) for value in vector] for vector in vectors]
