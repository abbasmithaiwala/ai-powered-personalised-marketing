"""
Brand repository for database operations.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand import Brand


class BrandRepository:
    """Repository for brand database operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize brand repository.

        Args:
            session: Async database session
        """
        self.session = session

    async def get_by_id(self, brand_id: UUID) -> Optional[Brand]:
        """
        Get brand by ID.

        Args:
            brand_id: Brand UUID

        Returns:
            Brand if found, None otherwise
        """
        result = await self.session.execute(
            select(Brand).where(Brand.id == brand_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Brand]:
        """
        Get brand by name (case-insensitive).

        Args:
            name: Brand name

        Returns:
            Brand if found, None otherwise
        """
        result = await self.session.execute(
            select(Brand).where(Brand.name.ilike(name))
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, **kwargs) -> Brand:
        """
        Create a new brand.

        Args:
            name: Brand name
            **kwargs: Additional brand attributes (slug, cuisine_type, is_active)

        Returns:
            Created brand
        """
        brand = Brand(name=name, **kwargs)
        self.session.add(brand)
        await self.session.flush()
        await self.session.refresh(brand)
        return brand

    async def get_or_create(self, name: str, **kwargs) -> tuple[Brand, bool]:
        """
        Get existing brand by name or create new one.

        Args:
            name: Brand name
            **kwargs: Additional brand attributes for creation

        Returns:
            Tuple of (brand, created) where created is True if brand was created
        """
        # Try to find existing brand (case-insensitive)
        brand = await self.get_by_name(name)

        if brand:
            return brand, False

        # Create new brand
        brand = await self.create(name=name, **kwargs)
        return brand, True
