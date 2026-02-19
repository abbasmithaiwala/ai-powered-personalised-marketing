"""PDF menu parser — orchestrates OCR extraction and JSON validation."""
import json
import logging
import re
from typing import Optional

from app.schemas.pdf_import import ParsedMenuItem
from app.services.ai.ocr_client import OCRClient

logger = logging.getLogger(__name__)

# Maximum PDF size allowed (20 MB)
MAX_PDF_SIZE_BYTES = 20 * 1024 * 1024

MENU_EXTRACTION_PROMPT = """Extract all menu items from this PDF menu.

Return ONLY a valid JSON array (no markdown, no explanation). Each object must have:
- "name" (string, required) — item name
- "description" (string or null) — item description
- "category" (string or null) — menu section, e.g. "Starters", "Mains", "Desserts"
- "cuisine_type" (string or null) — cuisine style, e.g. "Italian", "Indian"
- "price" (number or null) — numeric price, no currency symbols
- "dietary_tags" (array of strings) — e.g. ["vegan", "gluten-free"]
- "flavor_tags" (array of strings) — e.g. ["spicy", "sweet", "smoky"]

Example output:
[
  {
    "name": "Margherita Pizza",
    "description": "Classic tomato base with fresh mozzarella",
    "category": "Pizzas",
    "cuisine_type": "Italian",
    "price": 12.99,
    "dietary_tags": ["vegetarian"],
    "flavor_tags": ["cheesy", "savory"]
  }
]

If no menu items are found, return an empty array: []
Do NOT wrap the response in markdown code fences."""


class PDFParseError(Exception):
    """Raised when PDF parsing fails at the service level."""
    pass


class PDFParserService:
    """
    Orchestrates PDF menu parsing via an OCR-capable vision model.

    Responsibilities:
    - Validate PDF size
    - Delegate OCR extraction to OCRClient (configurable model)
    - Parse and validate the JSON response into ParsedMenuItem list
    - Tolerate noisy OCR output (skip invalid items, never fail whole parse)
    """

    def __init__(self, ocr_model: str = OCRClient.DEFAULT_MODEL):
        """
        Args:
            ocr_model: OpenRouter model ID to use for OCR.
                       Defaults to google/gemini-2.0-flash-001 (free). The mistral-ocr
                       plugin handles PDF extraction; the model just processes the text.
        """
        self.ocr_client = OCRClient(model=ocr_model)

    async def parse_menu_pdf(
        self,
        pdf_bytes: bytes,
        max_size_bytes: int = MAX_PDF_SIZE_BYTES,
    ) -> list[ParsedMenuItem]:
        """
        Parse a PDF menu and return a list of extracted menu items.

        Args:
            pdf_bytes: Raw PDF file content
            max_size_bytes: Maximum allowed file size in bytes

        Returns:
            List of ParsedMenuItem objects (validated, ready for review)

        Raises:
            PDFParseError: If the file is too large or OCR completely fails
        """
        if len(pdf_bytes) > max_size_bytes:
            max_mb = max_size_bytes // (1024 * 1024)
            raise PDFParseError(f"PDF is too large. Maximum allowed size is {max_mb}MB.")

        async with self.ocr_client as client:
            try:
                raw_response = await client.extract_text_from_pdf(
                    pdf_bytes=pdf_bytes,
                    prompt=MENU_EXTRACTION_PROMPT,
                )
            except Exception as e:
                logger.error("ocr_extraction_failed: %s", str(e))
                raise PDFParseError(f"OCR extraction failed: {e}") from e

        return self._parse_and_validate(raw_response)

    def _parse_and_validate(self, raw_response: str) -> list[ParsedMenuItem]:
        """
        Parse OCR response text into a validated list of ParsedMenuItem.

        Tolerant parsing strategy:
        1. Strip markdown code fences (```json ... ```)
        2. Extract first JSON array [ ... ] if full parse fails
        3. Skip items missing a name (log warning, don't fail whole list)
        4. Return empty list if nothing can be extracted (graceful degradation)

        Args:
            raw_response: Raw text returned by the OCR model

        Returns:
            List of validated ParsedMenuItem (may be empty)
        """
        cleaned = self._strip_code_fences(raw_response.strip())

        # Attempt 1: direct JSON parse
        data = self._try_json_parse(cleaned)

        # Attempt 2: extract first [...] array substring
        if data is None:
            extracted = self._extract_json_array(cleaned)
            if extracted:
                data = self._try_json_parse(extracted)

        if data is None:
            logger.warning("pdf_parser_json_parse_failed raw_length=%d", len(raw_response))
            return []

        if not isinstance(data, list):
            logger.warning("pdf_parser_unexpected_structure type=%s", type(data).__name__)
            return []

        items: list[ParsedMenuItem] = []
        for idx, raw_item in enumerate(data):
            if not isinstance(raw_item, dict):
                logger.debug("pdf_parser_skipping_non_dict index=%d", idx)
                continue

            name = raw_item.get("name")
            if not name or not str(name).strip():
                logger.debug("pdf_parser_skipping_nameless_item index=%d", idx)
                continue

            try:
                item = ParsedMenuItem.model_validate(raw_item)
                items.append(item)
            except Exception as e:
                logger.warning(
                    "pdf_parser_item_validation_failed index=%d name=%s error=%s",
                    idx, str(name)[:50], str(e),
                )

        logger.info("pdf_parser_complete total_extracted=%d", len(items))
        return items

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        """Remove ```json ... ``` or ``` ... ``` markdown code fences."""
        # Remove opening fence with optional language tag
        text = re.sub(r"^```(?:json)?\s*\n?", "", text, flags=re.IGNORECASE)
        # Remove closing fence
        text = re.sub(r"\n?```\s*$", "", text)
        return text.strip()

    @staticmethod
    def _try_json_parse(text: str) -> Optional[object]:
        """Attempt to JSON-parse text; return None on failure."""
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return None

    @staticmethod
    def _extract_json_array(text: str) -> Optional[str]:
        """
        Find and return the first top-level [...] JSON array substring.
        Useful when the model wraps the array in prose.
        """
        start = text.find("[")
        if start == -1:
            return None
        # Walk to find matching closing bracket
        depth = 0
        for i, ch in enumerate(text[start:], start=start):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        return None
