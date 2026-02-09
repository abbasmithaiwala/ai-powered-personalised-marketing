"""
Brand resolver service.

Handles finding or creating brand records from CSV data.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand import Brand
from app.repositories.brand import BrandRepository
from app.schemas.csv_schemas import OrderCSVRow


class BrandResolver:
    """
    Service for resolving brands from CSV data.

    Finds existing brands or creates new ones based on brand name.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize brand resolver.

        Args:
            session: Async database session
        """
        self.session = session
        self.repository = BrandRepository(session)

    async def resolve(self, csv_row: OrderCSVRow) -> Brand:
        """
        Resolve brand from CSV row.

        Finds existing brand by name (case-insensitive) or creates new one.

        Args:
            csv_row: Validated CSV row

        Returns:
            Brand instance
        """
        # Normalize brand name
        brand_name = csv_row.brand_name.strip()

        # Get or create brand
        brand, created = await self.repository.get_or_create(
            name=brand_name,
            is_active=True,
        )

        return brand
