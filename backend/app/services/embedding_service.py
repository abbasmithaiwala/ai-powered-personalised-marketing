"""
Embedding service for generating text embeddings using local sentence-transformers.

Always uses the local all-MiniLM-L6-v2 model (384-dim) which matches the Qdrant
collection vector size. OpenRouter is for LLM chat only, not embeddings.
"""

import asyncio
from functools import partial
from typing import List

import structlog

from app.core.constants import VECTOR_DIMENSION

logger = structlog.get_logger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings using local sentence-transformers.

    encode() is CPU-bound and synchronous, so all calls are offloaded to a
    thread pool executor to avoid blocking the event loop.
    """

    def __init__(self):
        self._model = None
        self._initialize_local_model()

    def _initialize_local_model(self):
        """Initialize the local sentence-transformers model."""
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer("all-MiniLM-L6-v2")
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
            logger.error("local_embedding_model_failed", error=str(e))

    def _assert_model_ready(self):
        if self._model is None:
            raise ValueError(
                "Local embedding model not initialized. "
                "Install sentence-transformers: pip install sentence-transformers"
            )

    async def embed(self, text: str) -> List[float]:
        """
        Generate an embedding vector for the given text.

        The underlying encode() call is CPU-bound and runs in a thread pool
        so the event loop is never blocked.

        Raises:
            ValueError: If text is empty or embedding generation fails.
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        self._assert_model_ready()

        loop = asyncio.get_event_loop()
        try:
            encode_fn = partial(self._model.encode, text, convert_to_numpy=True)
            embedding = await loop.run_in_executor(None, encode_fn)
            embedding_list: List[float] = embedding.tolist()
            logger.debug(
                "local_embedding_generated",
                text_length=len(text),
                vector_dimension=len(embedding_list),
            )
            return embedding_list
        except Exception as e:
            logger.error("local_embedding_error", error=str(e))
            raise ValueError(f"Failed to generate local embedding: {e}")

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a single batched encode call.

        Uses the model's native batch encoding (faster than one-by-one) and
        offloads the whole batch to a thread pool executor.

        Items that fail validation are skipped and logged; the returned list
        may therefore be shorter than the input list.
        """
        valid_texts = [t for t in texts if t and t.strip()]
        skipped = len(texts) - len(valid_texts)
        if skipped:
            logger.warning("embed_batch_skipped_empty", count=skipped)

        if not valid_texts:
            return []

        self._assert_model_ready()

        loop = asyncio.get_event_loop()
        try:
            encode_fn = partial(
                self._model.encode,
                valid_texts,
                convert_to_numpy=True,
                batch_size=32,
                show_progress_bar=False,
            )
            embeddings = await loop.run_in_executor(None, encode_fn)
            result: List[List[float]] = [e.tolist() for e in embeddings]
            logger.debug(
                "local_batch_embedding_generated",
                count=len(result),
            )
            return result
        except Exception as e:
            logger.error("batch_embedding_failed", error=str(e))
            raise ValueError(f"Failed to generate batch embeddings: {e}")


# Singleton instance
embedding_service = EmbeddingService()
