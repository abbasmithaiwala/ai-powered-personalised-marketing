"""Generic OCR client for extracting text from documents via OpenRouter vision models."""
import asyncio
import base64
import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class OCRClientError(Exception):
    """Base exception for OCR client errors."""
    pass


class OCRRateLimitError(OCRClientError):
    """Raised when rate limit is exceeded."""
    pass


class OCRServerError(OCRClientError):
    """Raised when the server returns 5xx errors."""
    pass


class OCRAPIKeyError(OCRClientError):
    """Raised when API key is missing or invalid."""
    pass


class OCRClient:
    """
    Generic OCR client that uses any vision-capable model via OpenRouter.

    Defaults to mistral/mistral-ocr-latest but is fully configurable,
    allowing easy model swaps without changing call sites.

    Features:
    - Model-agnostic: pass any OpenRouter vision model ID
    - Automatic retry on rate limits (429) and server errors (5xx)
    - Exponential backoff: 1s → 2s → 4s
    - Lazy HTTP client initialization
    - Async context manager support
    - 60s timeout (OCR is slower than standard completions)
    """

    # The file-parser plugin (mistral-ocr engine) handles PDF extraction independently of the
    # model. The model only needs to process the extracted text, so any free model works.
    DEFAULT_MODEL = "google/gemini-2.0-flash-001"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        timeout: float = 60.0,
        use_mistral_ocr_plugin: bool = True,
    ):
        """
        Initialize the OCR client.

        Args:
            model: OpenRouter model ID to use for OCR (defaults to google/gemini-2.0-flash-001)
            api_key: OpenRouter API key (defaults to settings.OPENROUTER_API_KEY)
            base_url: API base URL (defaults to settings.OPENROUTER_BASE_URL)
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds (60s default for OCR workloads)
            use_mistral_ocr_plugin: When True, adds the file-parser plugin with
                                    mistral-ocr engine for best OCR quality on PDFs
        """
        self.model = model
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.base_url = (base_url or settings.OPENROUTER_BASE_URL).rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout
        self.use_mistral_ocr_plugin = use_mistral_ocr_plugin
        self._client: Optional[httpx.AsyncClient] = None

        if not self.api_key:
            logger.warning(
                "OPENROUTER_API_KEY is not set. "
                "OCR calls will fail at runtime. "
                "Set OPENROUTER_API_KEY in your environment."
            )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or lazily create the underlying HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        """Close and release the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "OCRClient":
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        await self.close()

    async def extract_text_from_pdf(self, pdf_bytes: bytes, prompt: str) -> str:
        """
        Extract text/structured data from a PDF using a vision model via OpenRouter.

        Encodes the PDF as a base64 data URL and sends it as multimodal message content
        alongside the caller-supplied prompt. The model choice (set at init) determines
        which OCR capabilities are applied.

        Args:
            pdf_bytes: Raw bytes of the PDF file
            prompt: Instruction prompt telling the model what to extract and how to format it

        Returns:
            Raw text response from the model (typically JSON, but depends on the prompt)

        Raises:
            OCRAPIKeyError: If the API key is missing
            OCRRateLimitError: If rate limit is exceeded after all retries
            OCRServerError: If a server error persists after all retries
            OCRClientError: For other API errors
        """
        if not self.api_key:
            raise OCRAPIKeyError(
                "OPENROUTER_API_KEY is not set. Cannot make OCR API calls without an API key."
            )

        # Encode PDF as base64 data URL using OpenRouter's file content type
        b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        file_data_url = f"data:application/pdf;base64,{b64_pdf}"

        payload: dict = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "file",
                            "file": {
                                "filename": "menu.pdf",
                                "file_data": file_data_url,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        }

        # Add Mistral OCR plugin for best PDF extraction quality
        if self.use_mistral_ocr_plugin:
            payload["plugins"] = [
                {
                    "id": "file-parser",
                    "pdf": {
                        "engine": "mistral-ocr",
                    },
                }
            ]

        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                client = await self._get_client()
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                )

                # Rate limit — retry with backoff
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 1))
                    wait_time = min(retry_after, 2 ** attempt)
                    logger.warning(
                        "ocr_rate_limit attempt=%d/%d wait=%ds",
                        attempt + 1, self.max_retries, wait_time,
                    )
                    await asyncio.sleep(wait_time)
                    last_exception = OCRRateLimitError(
                        f"Rate limit exceeded: {response.text}"
                    )
                    continue

                # Server error — retry with backoff
                if response.status_code >= 500:
                    wait_time = 2 ** attempt
                    logger.warning(
                        "ocr_server_error status=%d attempt=%d/%d wait=%ds",
                        response.status_code, attempt + 1, self.max_retries, wait_time,
                    )
                    await asyncio.sleep(wait_time)
                    last_exception = OCRServerError(
                        f"Server error {response.status_code}: {response.text}"
                    )
                    continue

                # Client error (4xx except 429) — do not retry
                if 400 <= response.status_code < 500:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("error", {}).get("message", error_detail)
                    except Exception:
                        pass
                    raise OCRClientError(
                        f"OCR API request failed with status {response.status_code}: {error_detail}"
                    )

                response.raise_for_status()
                result = response.json()

                content = (
                    result.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )

                if not content:
                    raise OCRClientError("Empty response from OCR API")

                logger.debug(
                    "ocr_extraction_successful model=%s tokens=%s",
                    result.get("model", self.model),
                    result.get("usage", {}).get("total_tokens", "unknown"),
                )

                return content

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                wait_time = 2 ** attempt
                logger.warning(
                    "ocr_connection_error error=%s attempt=%d/%d wait=%ds",
                    str(e), attempt + 1, self.max_retries, wait_time,
                )
                await asyncio.sleep(wait_time)
                last_exception = OCRClientError(f"Connection error: {e}")
                continue

            except OCRClientError:
                # Don't retry on explicit client errors (4xx)
                raise

        # All retries exhausted
        if last_exception:
            raise last_exception

        raise OCRClientError("OCR request failed after all retries")
