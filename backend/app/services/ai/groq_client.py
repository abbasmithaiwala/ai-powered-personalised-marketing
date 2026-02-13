"""Groq API client for LLM interactions."""
import asyncio
import logging
from typing import List, Optional, Dict, Any

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class GroqError(Exception):
    """Base exception for Groq API errors."""
    pass


class GroqAPIKeyError(GroqError):
    """Raised when API key is missing or invalid."""
    pass


class GroqRateLimitError(GroqError):
    """Raised when rate limit is exceeded."""
    pass


class GroqServerError(GroqError):
    """Raised when server returns 5xx errors."""
    pass


class GroqClient:
    """
    Production-ready Groq API client with retry logic.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        timeout: float = 30.0,
    ):
        """
        Initialize Groq client.

        Args:
            api_key: Groq API key (defaults to settings.GROQ_API_KEY)
            model: Model ID (defaults to settings.GROQ_MODEL)
            base_url: API base URL (defaults to settings.GROQ_BASE_URL)
            max_retries: Maximum number of retries for failed requests
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self.base_url = (base_url or settings.GROQ_BASE_URL).rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout

        if not self.api_key:
            logger.warning(
                "GROQ_API_KEY is not set. "
                "LLM calls will fail at runtime. "
                "Set GROQ_API_KEY in your environment."
            )

        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        response_format: Optional[dict] = None,
        model: Optional[str] = None,
    ) -> str:
        """
        Generate a completion using Groq API.

        Args:
            messages: List of message dicts in OpenAI format
                     [{"role": "system", "content": "..."}, ...]
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            response_format: Optional response format, e.g., {"type": "json_object"}
            model: Optional model override

        Returns:
            Generated text content

        Raises:
            GroqAPIKeyError: If API key is missing
            GroqRateLimitError: If rate limit exceeded after retries
            GroqServerError: If server error persists after retries
            GroqError: For other API errors
        """
        if not self.api_key:
            raise GroqAPIKeyError(
                "GROQ_API_KEY is not set. "
                "Cannot make LLM API calls without an API key."
            )

        # Validate messages
        if not messages:
            raise ValueError("messages list cannot be empty")

        # Build request payload
        payload: Dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            payload["response_format"] = response_format

        # Retry loop
        last_exception: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                client = await self._get_client()
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                )

                # Handle rate limit errors
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 1))
                    wait_time = min(retry_after, 2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Rate limit hit (attempt {attempt + 1}/{self.max_retries}). "
                        f"Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                    last_exception = GroqRateLimitError(
                        f"Rate limit exceeded: {response.text}"
                    )
                    continue

                # Handle server errors (5xx)
                if response.status_code >= 500:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        f"Server error {response.status_code} "
                        f"(attempt {attempt + 1}/{self.max_retries}). "
                        f"Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                    last_exception = GroqServerError(
                        f"Server error {response.status_code}: {response.text}"
                    )
                    continue

                # Handle other client errors (4xx except 429)
                if 400 <= response.status_code < 500:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("error", {}).get("message", error_detail)
                    except Exception:
                        pass

                    raise GroqError(
                        f"API request failed with status {response.status_code}: {error_detail}"
                    )

                # Success
                response.raise_for_status()
                result = response.json()

                # Extract content from response
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                if not content:
                    raise GroqError("Empty response from API")

                logger.debug(
                    f"LLM completion successful. "
                    f"Model: {result.get('model', 'unknown')}, "
                    f"Tokens: {result.get('usage', {}).get('total_tokens', 'unknown')}"
                )

                return content

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                wait_time = 2 ** attempt
                logger.warning(
                    f"Connection error (attempt {attempt + 1}/{self.max_retries}): {e}. "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
                last_exception = GroqError(f"Connection error: {e}")
                continue

            except GroqError:
                # Don't retry on client errors (4xx except 429)
                raise

        # All retries exhausted
        if last_exception:
            raise last_exception

        raise GroqError("Failed to complete request after all retries")
