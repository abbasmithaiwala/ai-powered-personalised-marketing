"""
Menu item repository for database operations.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.menu_item import MenuItem


class MenuItemRepository:
    """Repository for menu item database operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize menu item repository.

        Args:
            session: Async database session
        """
        self.session = session

    async def get_by_id(self, menu_item_id: UUID) -> Optional[MenuItem]:
        """
        Get menu item by ID.

        Args:
            menu_item_id: Menu item UUID

        Returns:
            MenuItem if found, None otherwise
        """
        result = await self.session.execute(
            select(MenuItem).where(MenuItem.id == menu_item_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name_and_brand(
        self,
        name: str,
        brand_id: UUID
    ) -> Optional[MenuItem]:
        """
        Get menu item by name and brand (case-insensitive).

        Args:
            name: Item name
            brand_id: Brand UUID

        Returns:
            MenuItem if found, None otherwise
        """
        result = await self.session.execute(
            select(MenuItem).where(
                and_(
                    MenuItem.name.ilike(name),
                    MenuItem.brand_id == brand_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        name: str,
        brand_id: UUID,
        category: Optional[str] = None,
        price: Optional[float] = None,
        **kwargs
    ) -> MenuItem:
        """
        Create a new menu item.

        Args:
            name: Item name
            brand_id: Brand UUID
            category: Item category
            price: Item price
            **kwargs: Additional menu item attributes

        Returns:
            Created menu item
        """
        menu_item = MenuItem(
            name=name,
            brand_id=brand_id,
            category=category,
            price=price,
            **kwargs
        )
        self.session.add(menu_item)
        await self.session.flush()
        await self.session.refresh(menu_item)
        return menu_item

    async def get_or_create(
        self,
        name: str,
        brand_id: UUID,
        category: Optional[str] = None,
        price: Optional[float] = None,
        **kwargs
    ) -> tuple[MenuItem, bool]:
        """
        Get existing menu item or create new one.

        Args:
            name: Item name
            brand_id: Brand UUID
            category: Item category
            price: Item price
            **kwargs: Additional menu item attributes

        Returns:
            Tuple of (menu_item, created) where created is True if item was created
        """
        # Try to find existing item by name and brand
        menu_item = await self.get_by_name_and_brand(name, brand_id)

        if menu_item:
            return menu_item, False

        # Create new item
        menu_item = await self.create(
            name=name,
            brand_id=brand_id,
            category=category,
            price=price,
            **kwargs
        )
        return menu_item, True
