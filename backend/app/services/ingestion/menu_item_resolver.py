"""
Menu item resolver service.

Handles finding or creating menu item records from CSV data.
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.menu_item import MenuItem
from app.repositories.menu_item import MenuItemRepository
from app.schemas.csv_schemas import OrderCSVRow
from app.services.intelligence.embedding_builder import EmbeddingBuilder
from app.db.vector_store import vector_store


class MenuItemResolver:
    """
    Service for resolving menu items from CSV data.

    Finds existing items or creates new ones based on item name and brand.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize menu item resolver.

        Args:
            session: Async database session
        """
        self.session = session
        self.repository = MenuItemRepository(session)

    async def resolve(self, csv_row: OrderCSVRow, brand_id: UUID) -> MenuItem:
        """
        Resolve menu item from CSV row.

        Finds existing item by name and brand (case-insensitive) or creates new one.
        For new items, generates embedding for taste profile support.

        Args:
            csv_row: Validated CSV row
            brand_id: Brand UUID

        Returns:
            MenuItem instance
        """
        import structlog

        logger = structlog.get_logger(__name__)

        item_name = csv_row.item_name.strip()

        category = csv_row.category.strip() if csv_row.category else None

        price: Optional[float] = None
        if csv_row.unit_price:
            price = float(csv_row.unit_price)

        menu_item, created = await self.repository.get_or_create(
            name=item_name,
            brand_id=brand_id,
            category=category,
            price=price,
            is_available=True,
        )

        if created:
            logger.info(
                "menu_item_created",
                item_id=str(menu_item.id),
                item_name=item_name,
            )

            if vector_store.is_connected:
                try:
                    embedding_builder = EmbeddingBuilder(self.session)
                    success = await embedding_builder.upsert_item_embedding_no_commit(
                        menu_item
                    )
                    if success:
                        logger.info(
                            "menu_item_embedding_created",
                            item_id=str(menu_item.id),
                            item_name=item_name,
                        )
                    else:
                        logger.warning(
                            "menu_item_embedding_failed",
                            item_id=str(menu_item.id),
                            item_name=item_name,
                        )
                except Exception as e:
                    logger.warning(
                        "menu_item_embedding_error",
                        item_id=str(menu_item.id),
                        item_name=item_name,
                        error=str(e),
                    )
            else:
                logger.warning(
                    "vector_store_not_connected",
                    operation="menu_item_embedding",
                    item_id=str(menu_item.id),
                )

        return menu_item
