"""
Customer resolver service.

Handles finding or creating customer records from CSV data.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.repositories.customer import CustomerRepository
from app.schemas.csv_schemas import OrderCSVRow


class CustomerResolver:
    """
    Service for resolving customers from CSV data.

    Finds existing customers or creates new ones based on external_id and email.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize customer resolver.

        Args:
            session: Async database session
        """
        self.session = session
        self.repository = CustomerRepository(session)

    async def resolve(self, csv_row: OrderCSVRow) -> Customer:
        """
        Resolve customer from CSV row.

        Lookup strategy:
        1. Try external_id if provided
        2. Fall back to email

        Args:
            csv_row: Validated CSV row

        Returns:
            Customer instance
        """
        # Prepare customer data
        email = csv_row.customer_email.strip().lower()
        external_id = csv_row.customer_id.strip() if csv_row.customer_id else None

        # Prepare optional fields
        first_name = None
        last_name = None

        # Use provided first/last name if available
        if csv_row.customer_first_name:
            first_name = csv_row.customer_first_name.strip()
        if csv_row.customer_last_name:
            last_name = csv_row.customer_last_name.strip()

        # Prepare other optional fields
        phone = csv_row.customer_phone.strip() if csv_row.customer_phone else None
        city = csv_row.customer_city.strip() if csv_row.customer_city else None

        # Get or create customer
        customer, created = await self.repository.get_or_create(
            email=email,
            external_id=external_id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            city=city,
        )

        return customer
