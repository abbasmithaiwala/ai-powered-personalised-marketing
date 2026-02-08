"""
Embedding service for generating text embeddings.

Uses OpenRouter API if configured, otherwise falls back to local sentence-transformers.
"""

import structlog
from typing import List, Optional
import httpx

from app.core.config import settings
from app.core.constants import VECTOR_DIMENSION

logger = structlog.get_logger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings.

    Tries OpenRouter API first, falls back to sentence-transformers if not configured.
    """

    def __init__(self):
        self._model = None
        self._use_openrouter = bool(settings.OPENROUTER_API_KEY)

        if not self._use_openrouter:
            logger.info("openrouter_not_configured_using_local_embeddings")
            self._initialize_local_model()

    def _initialize_local_model(self):
        """Initialize the local sentence-transformers model."""
        try:
            from sentence_transformers import SentenceTransformer

            # Using all-MiniLM-L6-v2 which produces 384-dimensional vectors
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info(
                "local_embedding_model_loaded",
                model="all-MiniLM-L6-v2",
                dimension=VECTOR_DIMENSION,
            )
        except ImportError:
            logger.warning(
                "sentence_transformers_not_installed",
                message="Install with: pip install sentence-transformers",
            )
        except Exception as e:
            logger.error(
                "local_embedding_model_failed",
                error=str(e),
            )

    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding vector for the given text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector

        Raises:
            ValueError: If embedding generation fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        if self._use_openrouter:
            return await self._embed_openrouter(text)
        else:
            return await self._embed_local(text)

    async def _embed_openrouter(self, text: str) -> List[float]:
        """
        Generate embedding using OpenRouter API.

        Args:
            text: Text to embed

        Returns:
            Embedding vector

        Raises:
            ValueError: If API call fails
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.OPENROUTER_BASE_URL}/embeddings",
                    headers={
                        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "text-embedding-3-small",  # 1536 dimensions
                        "input": text,
                    },
                )
                response.raise_for_status()
                data = response.json()

                embedding = data["data"][0]["embedding"]
                logger.debug(
                    "openrouter_embedding_generated",
                    text_length=len(text),
                    vector_dimension=len(embedding),
                )
                return embedding

        except httpx.HTTPStatusError as e:
            logger.error(
                "openrouter_embedding_failed",
                status_code=e.response.status_code,
                error=str(e),
            )
            raise ValueError(f"OpenRouter API error: {e}")
        except Exception as e:
            logger.error(
                "openrouter_embedding_error",
                error=str(e),
            )
            raise ValueError(f"Failed to generate embedding: {e}")

    async def _embed_local(self, text: str) -> List[float]:
        """
        Generate embedding using local sentence-transformers model.

        Args:
            text: Text to embed

        Returns:
            Embedding vector

        Raises:
            ValueError: If model not initialized or encoding fails
        """
        if self._model is None:
            raise ValueError(
                "Local embedding model not initialized. "
                "Install sentence-transformers or configure OPENROUTER_API_KEY."
            )

        try:
            # sentence-transformers encode is synchronous, but we're in an async context
            # For production, consider running in a thread pool executor
            embedding = self._model.encode(text, convert_to_numpy=True)
            embedding_list = embedding.tolist()

            logger.debug(
                "local_embedding_generated",
                text_length=len(text),
                vector_dimension=len(embedding_list),
            )
            return embedding_list

        except Exception as e:
            logger.error(
                "local_embedding_error",
                error=str(e),
            )
            raise ValueError(f"Failed to generate local embedding: {e}")

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            try:
                embedding = await self.embed(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(
                    "batch_embedding_item_failed",
                    text=text[:50],
                    error=str(e),
                )
                # Continue with other texts
                continue

        return embeddings


# Singleton instance
embedding_service = EmbeddingService()
