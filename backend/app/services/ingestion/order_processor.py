"""
Order ingestion processor.

Main pipeline orchestrator that transforms validated CSV rows into database records.
"""

import logging
from decimal import Decimal
from typing import List, Set
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.repositories.customer import CustomerRepository
from app.repositories.order import OrderRepository
from app.schemas.csv_schemas import OrderCSVRow
from app.services.ingestion.brand_resolver import BrandResolver
from app.services.ingestion.customer_resolver import CustomerResolver
from app.services.ingestion.menu_item_resolver import MenuItemResolver

logger = logging.getLogger(__name__)


class RowProcessingError(Exception):
    """Exception for row-level processing errors."""

    def __init__(self, row_number: int, error_message: str):
        self.row_number = row_number
        self.error_message = error_message
        super().__init__(f"Row {row_number}: {error_message}")


class OrderProcessingResult:
    """Result of processing CSV rows."""

    def __init__(self):
        self.total_rows = 0
        self.processed_rows = 0
        self.skipped_rows = 0
        self.failed_rows = 0
        self.errors: List[dict] = []
        self.affected_customer_ids: Set[UUID] = set()

    def add_error(self, row_number: int, error: str) -> None:
        """Add a processing error."""
        self.errors.append({
            "row": row_number,
            "error": error,
        })
        self.failed_rows += 1

    def to_dict(self) -> dict:
        """Convert result to dictionary."""
        return {
            "total_rows": self.total_rows,
            "processed_rows": self.processed_rows,
            "skipped_rows": self.skipped_rows,
            "failed_rows": self.failed_rows,
            "errors": self.errors,
            "affected_customer_count": len(self.affected_customer_ids),
        }


class OrderProcessor:
    """
    Main order ingestion pipeline orchestrator.

    Processes validated CSV rows and creates database records for:
    - Brands
    - Customers
    - Menu items
    - Orders
    - Order items

    Also updates customer aggregate statistics.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize order processor.

        Args:
            session: Async database session
        """
        self.session = session
        self.brand_resolver = BrandResolver(session)
        self.customer_resolver = CustomerResolver(session)
        self.menu_item_resolver = MenuItemResolver(session)
        self.order_repository = OrderRepository(session)
        self.customer_repository = CustomerRepository(session)

    async def process_rows(
        self,
        rows: List[OrderCSVRow],
    ) -> OrderProcessingResult:
        """
        Process a batch of validated CSV rows.

        Pipeline steps (per row):
        1. Normalize fields
        2. Resolve brand (find or create)
        3. Resolve customer (find or create)
        4. Resolve menu item (find or create)
        5. Skip if order.external_id already exists (idempotency)
        6. Insert order + order_item in one transaction
        7. Update customer aggregate stats

        Row-level errors are caught and logged; processing continues.

        Args:
            rows: List of validated OrderCSVRow objects

        Returns:
            OrderProcessingResult with summary
        """
        result = OrderProcessingResult()
        result.total_rows = len(rows)

        for csv_row in rows:
            try:
                await self._process_single_row(csv_row, result)
            except Exception as e:
                # Log error and continue processing
                error_msg = str(e)
                logger.warning(
                    f"Error processing row {csv_row.row_number}: {error_msg}",
                    exc_info=True
                )
                result.add_error(csv_row.row_number, error_msg)

        return result

    async def _process_single_row(
        self,
        csv_row: OrderCSVRow,
        result: OrderProcessingResult,
    ) -> None:
        """
        Process a single CSV row.

        Args:
            csv_row: Validated CSV row
            result: Result accumulator
        """
        # Step 1: Normalize order_id
        order_external_id = csv_row.order_id.strip()

        # Step 2: Check if order already exists (idempotency)
        if await self.order_repository.exists_by_external_id(order_external_id):
            logger.debug(f"Order {order_external_id} already exists, skipping")
            result.skipped_rows += 1
            return

        # Step 3: Resolve brand
        brand = await self.brand_resolver.resolve(csv_row)

        # Step 4: Resolve customer
        customer = await self.customer_resolver.resolve(csv_row)

        # Step 5: Resolve menu item
        menu_item = await self.menu_item_resolver.resolve(csv_row, brand.id)

        # Step 6: Calculate order total
        # Use order_total from CSV if available, otherwise calculate from line item
        if csv_row.order_total:
            order_total = csv_row.order_total
        else:
            # Calculate from quantity * unit_price
            order_total = csv_row.quantity * csv_row.unit_price

        # Calculate subtotal for line item
        subtotal = csv_row.quantity * csv_row.unit_price

        # Step 7: Create order with order items
        order_items = [
            {
                "item_name": menu_item.name,
                "quantity": csv_row.quantity,
                "unit_price": csv_row.unit_price,
                "subtotal": subtotal,
                "menu_item_id": menu_item.id,
            }
        ]

        order = await self.order_repository.create_with_items(
            customer_id=customer.id,
            brand_id=brand.id,
            order_date=csv_row.order_date,
            items=order_items,
            external_id=order_external_id,
            total_amount=order_total,
            channel=csv_row.order_channel,
        )

        # Step 8: Update customer aggregate statistics
        await self.customer_repository.update_order_stats(
            customer_id=customer.id,
            order_total=order_total,
            order_date=csv_row.order_date,
        )

        # Track affected customer for preference computation
        result.affected_customer_ids.add(customer.id)

        result.processed_rows += 1
        logger.debug(f"Processed order {order_external_id} for customer {customer.email}")
