"""
Unit tests for the embedding builder service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.intelligence.embedding_builder import EmbeddingBuilder
from app.models.menu_item import MenuItem
from app.models.brand import Brand


@pytest.fixture
def mock_session():
    """Create a mock async database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_brand():
    """Create a mock brand."""
    brand = Brand(
        id=uuid4(),
        name="Test Restaurant",
        slug="test-restaurant",
        cuisine_type="Italian",
        is_active=True,
    )
    return brand


@pytest.fixture
def sample_menu_item(mock_brand):
    """Create a sample menu item for testing."""
    return MenuItem(
        id=uuid4(),
        brand_id=mock_brand.id,
        name="Margherita Pizza",
        description="Classic pizza with tomato, mozzarella, and fresh basil",
        category="Mains",
        cuisine_type="Italian",
        price=12.50,
        dietary_tags=["vegetarian"],
        flavor_tags=["savory", "cheesy", "herby"],
        is_available=True,
        embedding_id=None,
    )


@pytest.fixture
def minimal_menu_item(mock_brand):
    """Create a minimal menu item with only required fields."""
    return MenuItem(
        id=uuid4(),
        brand_id=mock_brand.id,
        name="Simple Dish",
        description=None,
        category=None,
        cuisine_type=None,
        price=None,
        dietary_tags=None,
        flavor_tags=None,
        is_available=True,
        embedding_id=None,
    )


class TestEmbeddingBuilder:
    """Test suite for EmbeddingBuilder service."""

    def test_build_item_text_full_data(self, mock_session, sample_menu_item):
        """Test text construction with all fields populated."""
        builder = EmbeddingBuilder(mock_session)
        text = builder.build_item_text(sample_menu_item)

        # Check that all components are present
        assert "Margherita Pizza" in text
        assert "Italian" in text
        assert "Mains" in text
        assert "Classic pizza with tomato" in text
        assert "flavors: savory, cheesy, herby" in text
        assert "dietary: vegetarian" in text

        # Check separator is used
        assert "|" in text

    def test_build_item_text_minimal_data(self, mock_session, minimal_menu_item):
        """Test text construction with only name (minimal)."""
        builder = EmbeddingBuilder(mock_session)
        text = builder.build_item_text(minimal_menu_item)

        # Should at least have the name
        assert "Simple Dish" in text
        assert text.strip() == "Simple Dish"

    def test_build_item_text_no_tags(self, mock_session, mock_brand):
        """Test text construction when tags are empty lists."""
        item = MenuItem(
            id=uuid4(),
            brand_id=mock_brand.id,
            name="Test Item",
            description="A test description",
            category="Starters",
            cuisine_type="Mexican",
            price=8.50,
            dietary_tags=[],
            flavor_tags=[],
            is_available=True,
        )

        builder = EmbeddingBuilder(mock_session)
        text = builder.build_item_text(item)

        # Should not include empty tag sections
        assert "flavors:" not in text
        assert "dietary:" not in text
        assert "Test Item" in text
        assert "Mexican" in text
        assert "Starters" in text

    def test_build_item_text_partial_data(self, mock_session, mock_brand):
        """Test text construction with some fields populated."""
        item = MenuItem(
            id=uuid4(),
            brand_id=mock_brand.id,
            name="Spicy Curry",
            description=None,
            category="Mains",
            cuisine_type="Indian",
            price=14.00,
            dietary_tags=["vegan", "gluten-free"],
            flavor_tags=None,
            is_available=True,
        )

        builder = EmbeddingBuilder(mock_session)
        text = builder.build_item_text(item)

        assert "Spicy Curry" in text
        assert "Indian" in text
        assert "Mains" in text
        assert "dietary: vegan, gluten-free" in text
        assert "flavors:" not in text

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, mock_session, sample_menu_item):
        """Test successful embedding generation."""
        builder = EmbeddingBuilder(mock_session)

        # Mock the embedding service
        mock_embedding = [0.1] * 384  # 384-dimensional vector
        with patch("app.services.intelligence.embedding_builder.embedding_service.embed") as mock_embed:
            mock_embed.return_value = mock_embedding

            result = await builder.generate_embedding(sample_menu_item)

            # Check that embedding was generated
            assert result == mock_embedding
            assert len(result) == 384

            # Check that embed was called with correct text
            mock_embed.assert_called_once()
            call_args = mock_embed.call_args[0][0]
            assert "Margherita Pizza" in call_args

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self, mock_session, mock_brand):
        """Test embedding generation with empty text (edge case)."""
        # Create item with all fields empty/None
        item = MenuItem(
            id=uuid4(),
            brand_id=mock_brand.id,
            name="",  # Empty name
            description=None,
            category=None,
            cuisine_type=None,
            price=None,
            dietary_tags=None,
            flavor_tags=None,
            is_available=True,
        )

        builder = EmbeddingBuilder(mock_session)
        result = await builder.generate_embedding(item)

        # Should return None for empty text
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_embedding_service_failure(self, mock_session, sample_menu_item):
        """Test handling of embedding service failure."""
        builder = EmbeddingBuilder(mock_session)

        # Mock the embedding service to raise an error
        with patch("app.services.intelligence.embedding_builder.embedding_service.embed") as mock_embed:
            mock_embed.side_effect = ValueError("API error")

            result = await builder.generate_embedding(sample_menu_item)

            # Should return None on failure
            assert result is None

    @pytest.mark.asyncio
    async def test_upsert_item_embedding_success(self, mock_session, sample_menu_item):
        """Test successful upsert of item embedding to Qdrant."""
        builder = EmbeddingBuilder(mock_session)

        mock_embedding = [0.1] * 384

        with patch("app.services.intelligence.embedding_builder.embedding_service.embed") as mock_embed, \
             patch("app.services.intelligence.embedding_builder.vector_store") as mock_vector_store:

            mock_embed.return_value = mock_embedding
            mock_vector_store.is_connected = True
            mock_vector_store.upsert_points = AsyncMock(return_value=True)

            result = await builder.upsert_item_embedding(sample_menu_item)

            # Check success
            assert result is True

            # Check that upsert was called
            mock_vector_store.upsert_points.assert_called_once()

            # Check the payload structure
            call_args = mock_vector_store.upsert_points.call_args
            points = call_args[1]["points"]
            assert len(points) == 1

            point = points[0]
            assert point.id == str(sample_menu_item.id)
            assert point.vector == mock_embedding
            assert point.payload["name"] == "Margherita Pizza"
            assert point.payload["cuisine_type"] == "Italian"
            assert point.payload["category"] == "Mains"
            assert "vegetarian" in point.payload["dietary_tags"]
            assert point.payload["price"] == 12.50

            # Check that embedding_id was updated
            assert sample_menu_item.embedding_id == str(sample_menu_item.id)
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_item_embedding_vector_store_disconnected(self, mock_session, sample_menu_item):
        """Test upsert when vector store is not connected."""
        builder = EmbeddingBuilder(mock_session)

        with patch("app.services.intelligence.embedding_builder.vector_store") as mock_vector_store:
            mock_vector_store.is_connected = False

            result = await builder.upsert_item_embedding(sample_menu_item)

            # Should return False when not connected
            assert result is False

    @pytest.mark.asyncio
    async def test_upsert_item_embedding_generation_failure(self, mock_session, sample_menu_item):
        """Test upsert when embedding generation fails."""
        builder = EmbeddingBuilder(mock_session)

        with patch("app.services.intelligence.embedding_builder.embedding_service.embed") as mock_embed, \
             patch("app.services.intelligence.embedding_builder.vector_store") as mock_vector_store:

            mock_embed.side_effect = ValueError("Embedding failed")
            mock_vector_store.is_connected = True

            result = await builder.upsert_item_embedding(sample_menu_item)

            # Should return False when embedding generation fails
            assert result is False

    @pytest.mark.asyncio
    async def test_embed_all_items_success(self, mock_session, mock_brand):
        """Test batch embedding of all items."""
        # Create sample items
        items = [
            MenuItem(
                id=uuid4(),
                brand_id=mock_brand.id,
                name=f"Item {i}",
                description=f"Description {i}",
                category="Mains",
                cuisine_type="Italian",
                price=10.0 + i,
                dietary_tags=["vegetarian"],
                flavor_tags=["savory"],
                is_available=True,
                embedding_id=None,
            )
            for i in range(3)
        ]

        # Mock the query result
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = items
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        builder = EmbeddingBuilder(mock_session)

        # Mock embedding and vector store
        with patch("app.services.intelligence.embedding_builder.embedding_service.embed") as mock_embed, \
             patch("app.services.intelligence.embedding_builder.vector_store") as mock_vector_store:

            mock_embed.return_value = [0.1] * 384
            mock_vector_store.is_connected = True
            mock_vector_store.upsert_points = AsyncMock(return_value=True)

            result = await builder.embed_all_items()

            # Check results
            assert result["total"] == 3
            assert result["successful"] == 3
            assert result["failed"] == 0
            assert result["skipped"] == 0

            # Check that upsert was called for each item
            assert mock_vector_store.upsert_points.call_count == 3

    @pytest.mark.asyncio
    async def test_embed_all_items_with_brand_filter(self, mock_session, mock_brand):
        """Test batch embedding with brand filter."""
        builder = EmbeddingBuilder(mock_session)

        # Mock empty result
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await builder.embed_all_items(brand_id=mock_brand.id)

        # Check that query was executed (with brand filter)
        assert mock_session.execute.called
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_embed_all_items_skip_unavailable(self, mock_session, mock_brand):
        """Test that unavailable items are skipped during batch embedding."""
        # Create mix of available and unavailable items
        items = [
            MenuItem(
                id=uuid4(),
                brand_id=mock_brand.id,
                name="Available Item",
                is_available=True,
            ),
            MenuItem(
                id=uuid4(),
                brand_id=mock_brand.id,
                name="Unavailable Item",
                is_available=False,
            ),
        ]

        # Mock the query result
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = items
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        builder = EmbeddingBuilder(mock_session)

        with patch("app.services.intelligence.embedding_builder.embedding_service.embed") as mock_embed, \
             patch("app.services.intelligence.embedding_builder.vector_store") as mock_vector_store:

            mock_embed.return_value = [0.1] * 384
            mock_vector_store.is_connected = True
            mock_vector_store.upsert_points = AsyncMock(return_value=True)

            result = await builder.embed_all_items()

            # Check that unavailable item was skipped
            assert result["total"] == 2
            assert result["successful"] == 1
            assert result["failed"] == 0
            assert result["skipped"] == 1

    @pytest.mark.asyncio
    async def test_embed_all_items_partial_failure(self, mock_session, mock_brand):
        """Test batch embedding with some items failing."""
        items = [
            MenuItem(id=uuid4(), brand_id=mock_brand.id, name="Item 1", is_available=True),
            MenuItem(id=uuid4(), brand_id=mock_brand.id, name="Item 2", is_available=True),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = items
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        builder = EmbeddingBuilder(mock_session)

        with patch("app.services.intelligence.embedding_builder.embedding_service.embed") as mock_embed, \
             patch("app.services.intelligence.embedding_builder.vector_store") as mock_vector_store:

            # First item succeeds, second fails
            mock_embed.side_effect = [
                [0.1] * 384,
                ValueError("Embedding failed"),
            ]
            mock_vector_store.is_connected = True
            mock_vector_store.upsert_points = AsyncMock(return_value=True)

            result = await builder.embed_all_items()

            # Check mixed results
            assert result["total"] == 2
            assert result["successful"] == 1
            assert result["failed"] == 1
            assert result["skipped"] == 0

    @pytest.mark.asyncio
    async def test_delete_item_embedding_success(self, mock_session):
        """Test successful deletion of item embedding."""
        builder = EmbeddingBuilder(mock_session)
        item_id = uuid4()

        with patch("app.services.intelligence.embedding_builder.vector_store") as mock_vector_store:
            mock_vector_store.is_connected = True
            mock_vector_store.delete_points = AsyncMock(return_value=True)

            result = await builder.delete_item_embedding(item_id)

            assert result is True
            mock_vector_store.delete_points.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_item_embedding_not_connected(self, mock_session):
        """Test deletion when vector store is not connected."""
        builder = EmbeddingBuilder(mock_session)
        item_id = uuid4()

        with patch("app.services.intelligence.embedding_builder.vector_store") as mock_vector_store:
            mock_vector_store.is_connected = False

            result = await builder.delete_item_embedding(item_id)

            assert result is False
