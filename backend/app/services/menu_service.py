"""
Menu service for business logic related to brands and menu items.
"""

import math
import structlog
from typing import Optional
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand import Brand
from app.models.menu_item import MenuItem
from app.repositories.brand import BrandRepository
from app.repositories.menu_item import MenuItemRepository
from app.schemas.brand import BrandCreate, BrandUpdate, BrandListResponse, BrandResponse
from app.schemas.menu_item import MenuItemCreate, MenuItemUpdate, MenuItemListResponse, MenuItemResponse
from app.schemas.pdf_import import ParsedMenuItem, BulkCreateResponse
from app.services.intelligence.embedding_builder import EmbeddingBuilder

logger = structlog.get_logger(__name__)


class MenuService:
    """Service for managing brands and menu items."""

    def __init__(self, session: AsyncSession):
        """
        Initialize menu service.

        Args:
            session: Async database session
        """
        self.session = session
        self.brand_repo = BrandRepository(session)
        self.menu_item_repo = MenuItemRepository(session)
        self.embedding_builder = EmbeddingBuilder(session)

    # Brand operations
    async def list_brands(
        self,
        page: int = 1,
        page_size: int = 25,
    ) -> BrandListResponse:
        """
        List all brands with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Paginated brand list response
        """
        # Calculate offset
        offset = (page - 1) * page_size

        # Get total count
        count_result = await self.session.execute(
            select(func.count()).select_from(Brand)
        )
        total = count_result.scalar_one()

        # Get brands
        result = await self.session.execute(
            select(Brand)
            .order_by(Brand.name)
            .limit(page_size)
            .offset(offset)
        )
        brands = result.scalars().all()

        # Calculate total pages
        pages = math.ceil(total / page_size) if total > 0 else 1

        return BrandListResponse(
            items=[BrandResponse.model_validate(brand) for brand in brands],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_brand(self, brand_id: UUID) -> Optional[BrandResponse]:
        """
        Get brand by ID.

        Args:
            brand_id: Brand UUID

        Returns:
            Brand response or None if not found
        """
        brand = await self.brand_repo.get_by_id(brand_id)
        if brand:
            return BrandResponse.model_validate(brand)
        return None

    async def create_brand(self, data: BrandCreate) -> BrandResponse:
        """
        Create a new brand.

        Args:
            data: Brand creation data

        Returns:
            Created brand response
        """
        brand = await self.brand_repo.create(
            name=data.name,
            slug=data.slug,
            cuisine_type=data.cuisine_type,
            is_active=data.is_active,
        )
        await self.session.commit()
        return BrandResponse.model_validate(brand)

    async def update_brand(
        self,
        brand_id: UUID,
        data: BrandUpdate,
    ) -> Optional[BrandResponse]:
        """
        Update an existing brand.

        Args:
            brand_id: Brand UUID
            data: Brand update data

        Returns:
            Updated brand response or None if not found
        """
        brand = await self.brand_repo.get_by_id(brand_id)
        if not brand:
            return None

        # Update fields if provided
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(brand, field, value)

        await self.session.commit()
        await self.session.refresh(brand)
        return BrandResponse.model_validate(brand)

    async def delete_brand(self, brand_id: UUID) -> bool:
        """
        Soft delete a brand (set is_active to False).

        Args:
            brand_id: Brand UUID

        Returns:
            True if brand was deleted, False if not found
        """
        brand = await self.brand_repo.get_by_id(brand_id)
        if not brand:
            return False

        brand.is_active = False
        await self.session.commit()
        return True

    # Menu item operations
    async def list_menu_items(
        self,
        page: int = 1,
        page_size: int = 25,
        brand_id: Optional[UUID] = None,
        category: Optional[str] = None,
        cuisine: Optional[str] = None,
        dietary_tag: Optional[str] = None,
    ) -> MenuItemListResponse:
        """
        List menu items with pagination and filtering.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            brand_id: Filter by brand ID
            category: Filter by category
            cuisine: Filter by cuisine type
            dietary_tag: Filter by dietary tag

        Returns:
            Paginated menu item list response
        """
        # Build filters
        filters = []
        if brand_id:
            filters.append(MenuItem.brand_id == brand_id)
        if category:
            filters.append(MenuItem.category.ilike(f"%{category}%"))
        if cuisine:
            filters.append(MenuItem.cuisine_type.ilike(f"%{cuisine}%"))
        if dietary_tag:
            # Use any_ for PostgreSQL array contains check
            filters.append(MenuItem.dietary_tags.any(dietary_tag))

        # Calculate offset
        offset = (page - 1) * page_size

        # Build base query
        base_query = select(MenuItem)
        if filters:
            base_query = base_query.where(and_(*filters))

        # Get total count
        count_result = await self.session.execute(
            select(func.count()).select_from(MenuItem).where(and_(*filters)) if filters else select(func.count()).select_from(MenuItem)
        )
        total = count_result.scalar_one()

        # Get items
        result = await self.session.execute(
            base_query
            .order_by(MenuItem.name)
            .limit(page_size)
            .offset(offset)
        )
        items = result.scalars().all()

        # Calculate total pages
        pages = math.ceil(total / page_size) if total > 0 else 1

        return MenuItemListResponse(
            items=[MenuItemResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_menu_item(self, item_id: UUID) -> Optional[MenuItemResponse]:
        """
        Get menu item by ID.

        Args:
            item_id: Menu item UUID

        Returns:
            Menu item response or None if not found
        """
        item = await self.menu_item_repo.get_by_id(item_id)
        if item:
            return MenuItemResponse.model_validate(item)
        return None

    async def create_menu_item(self, data: MenuItemCreate) -> MenuItemResponse:
        """
        Create a new menu item.

        Args:
            data: Menu item creation data

        Returns:
            Created menu item response
        """
        # Verify brand exists
        brand = await self.brand_repo.get_by_id(data.brand_id)
        if not brand:
            raise ValueError(f"Brand with id {data.brand_id} not found")

        item = await self.menu_item_repo.create(
            name=data.name,
            brand_id=data.brand_id,
            description=data.description,
            category=data.category,
            cuisine_type=data.cuisine_type,
            price=data.price,
            dietary_tags=data.dietary_tags,
            flavor_tags=data.flavor_tags,
            is_available=data.is_available,
        )
        await self.session.commit()
        await self.session.refresh(item)

        # Trigger embedding generation (fire-and-forget, doesn't block response)
        # Run in background - errors logged but don't fail the create operation
        try:
            await self.embedding_builder.upsert_item_embedding(item)
        except Exception as e:
            # Log but don't fail the create operation
            import structlog
            logger = structlog.get_logger(__name__)
            logger.warning(
                "embedding_generation_failed_on_create",
                item_id=str(item.id),
                error=str(e),
            )

        return MenuItemResponse.model_validate(item)

    async def update_menu_item(
        self,
        item_id: UUID,
        data: MenuItemUpdate,
    ) -> Optional[MenuItemResponse]:
        """
        Update an existing menu item.

        Args:
            item_id: Menu item UUID
            data: Menu item update data

        Returns:
            Updated menu item response or None if not found
        """
        item = await self.menu_item_repo.get_by_id(item_id)
        if not item:
            return None

        # Track if content changed (for embedding regeneration)
        content_fields = {'name', 'description', 'cuisine_type', 'category', 'dietary_tags', 'flavor_tags'}
        update_data = data.model_dump(exclude_unset=True)
        content_changed = any(field in update_data for field in content_fields)

        # Update fields if provided
        for field, value in update_data.items():
            setattr(item, field, value)

        await self.session.commit()
        await self.session.refresh(item)

        # If content changed, trigger embedding regeneration (fire-and-forget)
        if content_changed:
            try:
                await self.embedding_builder.upsert_item_embedding(item)
            except Exception as e:
                # Log but don't fail the update operation
                import structlog
                logger = structlog.get_logger(__name__)
                logger.warning(
                    "embedding_regeneration_failed_on_update",
                    item_id=str(item_id),
                    error=str(e),
                )

        return MenuItemResponse.model_validate(item)

    async def delete_menu_item(self, item_id: UUID) -> bool:
        """
        Soft delete a menu item (set is_available to False).

        Args:
            item_id: Menu item UUID

        Returns:
            True if item was deleted, False if not found
        """
        item = await self.menu_item_repo.get_by_id(item_id)
        if not item:
            return False

        item.is_available = False
        await self.session.commit()
        return True

    async def bulk_create_menu_items(
        self,
        brand_id: UUID,
        items: list[ParsedMenuItem],
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> BulkCreateResponse:
        """
        Bulk create menu items from parsed PDF data.

        Strategy:
        - Verify brand exists once upfront
        - Loop and create each item, collecting successes and failures separately
        - Single db.commit() after all inserts (more efficient than per-item)
        - Fire-and-forget embedding generation per item after commit

        Args:
            brand_id: Brand to associate all items with
            items: List of ParsedMenuItem from the OCR/review stage

        Returns:
            BulkCreateResponse with created/failed counts and full item details

        Raises:
            ValueError: If brand does not exist
        """
        brand = await self.brand_repo.get_by_id(brand_id)
        if not brand:
            raise ValueError(f"Brand with id {brand_id} not found")

        created_items: list[MenuItem] = []
        failed_count = 0

        for parsed in items:
            try:
                item = await self.menu_item_repo.create(
                    name=parsed.name,
                    brand_id=brand_id,
                    description=parsed.description,
                    category=parsed.category,
                    cuisine_type=parsed.cuisine_type,
                    price=parsed.price,
                    dietary_tags=parsed.dietary_tags or [],
                    flavor_tags=parsed.flavor_tags or [],
                    is_available=True,
                )
                created_items.append(item)
            except Exception as e:
                logger.warning(
                    "bulk_create_item_failed",
                    name=parsed.name,
                    brand_id=str(brand_id),
                    error=str(e),
                )
                failed_count += 1

        # Single commit for all inserts
        await self.session.commit()

        # Refresh all items and build response immediately
        response_items: list[MenuItemResponse] = []
        for item in created_items:
            await self.session.refresh(item)
            response_items.append(MenuItemResponse.model_validate(item))

        # Schedule embeddings as a true background task so they don't block the response
        item_ids = [item.id for item in created_items]
        if background_tasks is not None:
            background_tasks.add_task(self._embed_items_background, item_ids)
        else:
            # Fallback: embed inline (e.g. called outside request context)
            for item in created_items:
                try:
                    await self.embedding_builder.upsert_item_embedding(item)
                except Exception as e:
                    logger.warning("bulk_embed_failed", item_id=str(item.id), error=str(e))

        return BulkCreateResponse(
            created=len(created_items),
            failed=failed_count,
            items=response_items,
        )

    @staticmethod
    async def _embed_items_background(item_ids: list) -> None:
        """Embed a list of menu items by ID. Runs after the HTTP response is sent.

        Opens its own DB session since the request-scoped session is closed by this point.
        """
        from app.db.session import AsyncSessionLocal
        from app.repositories.menu_item import MenuItemRepository

        async with AsyncSessionLocal() as session:
            repo = MenuItemRepository(session)
            builder = EmbeddingBuilder(session)
            for item_id in item_ids:
                try:
                    item = await repo.get_by_id(item_id)
                    if item:
                        await builder.upsert_item_embedding(item)
                except Exception as e:
                    logger.warning("bulk_embed_background_failed", item_id=str(item_id), error=str(e))
