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

    async def resolve(
        self,
        csv_row: OrderCSVRow,
        brand_id: UUID
    ) -> MenuItem:
        """
        Resolve menu item from CSV row.

        Finds existing item by name and brand (case-insensitive) or creates new one.

        Args:
            csv_row: Validated CSV row
            brand_id: Brand UUID

        Returns:
            MenuItem instance
        """
        # Normalize item name
        item_name = csv_row.item_name.strip()

        # Prepare optional fields
        category = csv_row.category.strip() if csv_row.category else None

        # Use unit_price as the item price
        price: Optional[float] = None
        if csv_row.unit_price:
            price = float(csv_row.unit_price)

        # Get or create menu item
        menu_item, created = await self.repository.get_or_create(
            name=item_name,
            brand_id=brand_id,
            category=category,
            price=price,
            is_available=True,
        )

        return menu_item
