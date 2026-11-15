
"""
NASA FLAME — Gemini LLM Provider

Server-side Google Gemini REST API client.

Features:
- Environment-based API credentials
- Structured JSON responses
- Response validation
- Detection of Gemini formatting conflicts
- Retry handling for temporary API failures
- Connection timeout protection
- Safe error reporting
"""

from typing import Dict, Any, Optional, Set
import os
import json
import logging
import urllib.request
import urllib.error
import time
import random


logger = logging.getLogger("flame.rag.llm")

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_OUTPUT_TOKENS = 2048


class GeminiProvider:
    """Google Gemini REST API provider for NASA FLAME."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
        max_retries: int = 3,
        initial_backoff: float = 0.5,
        backoff_multiplier: float = 2.0,
        max_backoff: float = 4.0,
    ):
        self.api_key = (
            api_key
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
        )

        self.model_name = (
            model_name
            or os.environ.get("GEMINI_MODEL")
            or DEFAULT_GEMINI_MODEL
        )

        self.timeout = timeout
        self.max_output_tokens = max_output_tokens
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.backoff_multiplier = backoff_multiplier
        self.max_backoff = max_backoff

    @property
    def is_configured(self) -> bool:
        """Check whether Gemini credentials are available."""
        return bool(self.api_key and self.api_key.strip())

    def _failure(
        self,
        message: str,
        status_code: int,
        attempt: int,
    ) -> Dict[str, Any]:
        """Return a standardized failure response."""
        return {
            "success": False,
            "error": message,
            "status_code": status_code,
            "raw_text": None,
            "retries_attempted": attempt,
        }

    def _validate_response(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """
        Validate Gemini's structured response.

        This provider uses application/json.

        A valid API response must contain parseable JSON.
        Error objects and instruction-conflict messages are rejected.
        """

        if not isinstance(text, str) or not text.strip():
            raise ValueError(
                "Gemini returned an empty response."
            )

        text = text.strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Gemini returned invalid JSON."
            ) from exc

        if not isinstance(parsed, (dict, list)):
            raise ValueError(
                "Gemini returned an unsupported JSON structure."
            )

        # Reject API/model-generated error objects.
        if isinstance(parsed, dict):
            if "error" in parsed and "answer" not in parsed:
                raise ValueError(
                    "Gemini returned an error object instead of a response."
                )

        if isinstance(parsed, list):
            if not parsed:
                raise ValueError(
                    "Gemini returned an empty JSON array."
                )

            if all(
                isinstance(item, dict)
                and "error" in item
                for item in parsed
            ):
                raise ValueError(
                    "Gemini returned an error array instead of a response."
                )

        # Detect formatting-conflict messages in generated prose.
        conflict_patterns = (
            "conflict between developer",
            "conflict between system",
            "conflicting instructions",
            "conflicting constraints",
            "return ordinary markdown prose, never",
            "system prompt strictly commands",
            "system instruction requires",
            "system instructions override",
            "cannot output json",
            "cannot return json",
            "overarching system instruction",
            "strict negative constraint",
        )

        # Inspect textual values, including nested error structures.
        def collect_text(value: Any) -> list[str]:
            if isinstance(value, str):
                return [value]

            if isinstance(value, dict):
                collected = []
                for item in value.values():
                    collected.extend(collect_text(item))
                return collected

            if isinstance(value, list):
                collected = []
                for item in value:
                    collected.extend(collect_text(item))
                return collected

            return []

        combined_text = " ".join(collect_text(parsed)).lower()

        if any(
            pattern in combined_text
            for pattern in conflict_patterns
        ):
            raise ValueError(
                "Gemini generated a response-format instruction conflict."
            )

        return parsed

    def _retry_delay(
        self,
        attempt: int,
        retry_after: Optional[str] = None,
    ) -> float:
        """Calculate bounded exponential backoff with jitter."""

        backoff = min(
            self.max_backoff,
            self.initial_backoff
            * (self.backoff_multiplier ** attempt),
        )

        if retry_after:
            try:
                backoff = min(
                    self.max_backoff,
                    max(0.0, float(retry_after)),
                )
            except (ValueError, TypeError):
                pass

        return backoff * random.uniform(0.8, 1.2)

    def generate(
        self,
        system_instruction: str,
        user_prompt: str,
    ) -> Dict[str, Any]:
        """
        Execute a Gemini generateContent request.

        Retries transient network/server failures.
        Rejects malformed JSON and formatting-conflict responses.
        Preserves the existing provider response contract.
        """

        if not self.is_configured:
            return self._failure(
                "GEMINI_API_KEY not configured",
                401,
                0,
            )

        endpoint = (
            "https://generativelanguage.googleapis.com"
            f"/v1beta/models/{self.model_name}:generateContent"
        )

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": user_prompt}
                    ],
                }
            ],
            "systemInstruction": {
                "parts": [
                    {"text": system_instruction}
                ]
            },
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": self.max_output_tokens,
                "responseMimeType": "application/json",
            },
        }

        req_data = json.dumps(payload).encode("utf-8")

        transient_codes: Set[int] = {
            429, 500, 502, 503, 504
        }

        permanent_codes: Set[int] = {
            400, 401, 403, 404
        }

        last_error = None
        last_status_code = 503

        for attempt in range(self.max_retries + 1):
            try:
                request = urllib.request.Request(
                    endpoint,
                    data=req_data,
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": self.api_key,
                    },
                    method="POST",
                )

                with urllib.request.urlopen(
                    request,
                    timeout=self.timeout,
                ) as resp:

                    status_code = resp.status

                    body = json.loads(
                        resp.read().decode("utf-8")
                    )

                    candidates = body.get("candidates", [])

                    if not candidates:
                        return self._failure(
                            "No candidates returned from Gemini API.",
                            status_code,
                            attempt,
                        )

                    candidate = candidates[0]

                    parts = (
                        candidate.get("content", {})
                        .get("parts", [])
                    )

                    text = "".join(
                        part.get("text", "")
                        for part in parts
                        if isinstance(part, dict)
                        and isinstance(part.get("text"), str)
                    ).strip()

                    finish_reason = candidate.get(
                        "finishReason", ""
                    )

                    if finish_reason not in (
                        "",
                        "STOP",
                    ):
                        logger.warning(
                            "Gemini stopped generation: %s",
                            finish_reason,
                        )

                        return self._failure(
                            f"Gemini generation stopped: {finish_reason}",
                            status_code,
                            attempt,
                        )

                    try:
                        self._validate_response(text)

                    except ValueError as exc:
                        logger.warning(
                            "Gemini response validation failed: %s",
                            exc,
                        )

                        return self._failure(
                            str(exc),
                            status_code,
                            attempt,
                        )

                    return {
                        "success": True,
                        "raw_text": text,
                        "status_code": status_code,
                        "model": self.model_name,
                        "retries_attempted": attempt,
                    }

            except urllib.error.HTTPError as exc:

                status_code = exc.code
                last_status_code = status_code

                last_error = (
                    f"Gemini API returned HTTP {status_code}: "
                    f"{exc.reason}"
                )

                logger.warning(
                    "Gemini API HTTP %d (attempt %d/%d)",
                    status_code,
                    attempt + 1,
                    self.max_retries + 1,
                )

                if (
                    status_code in permanent_codes
                    or status_code not in transient_codes
                    or attempt == self.max_retries
                ):
                    return self._failure(
                        last_error,
                        status_code,
                        attempt,
                    )

                retry_after = (
                    exc.headers.get("Retry-After")
                    if exc.headers
                    else None
                )

                delay = self._retry_delay(
                    attempt,
                    retry_after,
                )

                logger.info(
                    "Retrying Gemini in %.2f seconds...",
                    delay,
                )

                time.sleep(delay)

            except (urllib.error.URLError, TimeoutError) as exc:

                is_timeout = (
                    isinstance(exc, TimeoutError)
                    or "timed out" in str(exc).lower()
                )

                status_code = 504 if is_timeout else 503

                last_status_code = status_code

                last_error = (
                    f"Gemini connection timeout ({self.timeout}s)"
                    if is_timeout
                    else "Gemini network connection failed."
                )

                logger.warning(
                    "Gemini network failure "
                    "(attempt %d/%d): %s",
                    attempt + 1,
                    self.max_retries + 1,
                    last_error,
                )

                if attempt == self.max_retries:
                    return self._failure(
                        last_error,
                        status_code,
                        attempt,
                    )

                delay = self._retry_delay(attempt)

                time.sleep(delay)

            except Exception as exc:

                logger.exception(
                    "Unexpected Gemini provider error: %s",
                    type(exc).__name__,
                )

                return self._failure(
                    "Unexpected error during Gemini request.",
                    500,
                    attempt,
                )

        return self._failure(
            last_error or "Gemini retry budget exhausted.",
            last_status_code,
            self.max_retries,
        )
