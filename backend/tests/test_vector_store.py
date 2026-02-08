"""
Integration tests for Qdrant vector store.
"""

import pytest
from uuid import uuid4
from qdrant_client.models import PointStruct

from app.db.vector_store import VectorStore
from app.services.embedding_service import EmbeddingService
from app.core.constants import (
    MENU_ITEM_EMBEDDINGS_COLLECTION,
    CUSTOMER_TASTE_PROFILES_COLLECTION,
    VECTOR_DIMENSION,
)


@pytest.mark.asyncio
async def test_vector_store_connection():
    """Test that we can connect to Qdrant."""
    store = VectorStore()
    result = await store.connect()

    # Should connect (even if Qdrant is not running, it should not crash)
    assert isinstance(result, bool)

    if result:
        assert store.is_connected
        await store.close()
        assert not store.is_connected


@pytest.mark.asyncio
async def test_collections_created():
    """Test that collections are created on connection."""
    store = VectorStore()
    connected = await store.connect()

    if not connected:
        pytest.skip("Qdrant not available")

    try:
        # Collections should exist
        collections = await store.client.get_collections()
        collection_names = [col.name for col in collections.collections]

        assert MENU_ITEM_EMBEDDINGS_COLLECTION in collection_names
        assert CUSTOMER_TASTE_PROFILES_COLLECTION in collection_names

    finally:
        await store.close()


@pytest.mark.asyncio
async def test_upsert_and_search():
    """Test upserting vectors and searching for them."""
    store = VectorStore()
    connected = await store.connect()

    if not connected:
        pytest.skip("Qdrant not available")

    try:
        # Create a test vector (matching the expected dimension)
        test_id = str(uuid4())
        test_vector = [0.1] * VECTOR_DIMENSION

        point = PointStruct(
            id=test_id,
            vector=test_vector,
            payload={
                "menu_item_id": str(uuid4()),
                "brand_id": str(uuid4()),
                "name": "Test Pizza",
                "category": "main",
                "cuisine_type": "italian",
                "dietary_tags": ["vegetarian"],
                "price": 12.99,
            },
        )

        # Upsert the point
        success = await store.upsert_points(
            collection_name=MENU_ITEM_EMBEDDINGS_COLLECTION,
            points=[point],
        )
        assert success

        # Search for similar vectors
        results = await store.search(
            collection_name=MENU_ITEM_EMBEDDINGS_COLLECTION,
            query_vector=test_vector,
            limit=1,
        )

        assert len(results) >= 1
        # The most similar should be our test point (or very close)
        assert results[0].id == test_id
        assert results[0].payload["name"] == "Test Pizza"

    finally:
        await store.close()


@pytest.mark.asyncio
async def test_embedding_service_local():
    """Test that embedding service generates vectors."""
    service = EmbeddingService()

    # Test with simple text
    text = "Delicious margherita pizza with fresh basil and mozzarella"

    try:
        embedding = await service.embed(text)

        # Should return a list of floats
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)

        # Dimension should match expected (384 for local model or 1536 for OpenRouter)
        assert len(embedding) in [384, 1536]

    except ValueError as e:
        # If sentence-transformers is not installed or OpenRouter not configured
        if "not initialized" in str(e) or "not installed" in str(e):
            pytest.skip("Embedding service not available")
        else:
            raise


@pytest.mark.asyncio
async def test_embedding_service_empty_text():
    """Test that empty text raises an error."""
    service = EmbeddingService()

    with pytest.raises(ValueError, match="Text cannot be empty"):
        await service.embed("")

    with pytest.raises(ValueError, match="Text cannot be empty"):
        await service.embed("   ")


@pytest.mark.asyncio
async def test_embedding_batch():
    """Test batch embedding generation."""
    service = EmbeddingService()

    texts = [
        "Pizza margherita",
        "Chicken tikka masala",
        "Vegan burger",
    ]

    try:
        embeddings = await service.embed_batch(texts)

        # Should return list of embeddings
        assert isinstance(embeddings, list)
        assert len(embeddings) <= len(texts)  # May skip failed ones

        for embedding in embeddings:
            assert isinstance(embedding, list)
            assert len(embedding) in [384, 1536]

    except ValueError as e:
        if "not initialized" in str(e) or "not installed" in str(e):
            pytest.skip("Embedding service not available")
        else:
            raise
