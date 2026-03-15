"""
CSV column header mappings and aliases.

Provides flexible column mapping to handle various POS export formats.
"""

from typing import Dict, List

# Header alias dictionary - maps canonical field names to possible variations
COLUMN_ALIASES: Dict[str, List[str]] = {
    # Required fields
    "order_id": [
        "order_id",
        "order id",
        "orderid",
        "id",
        "order_number",
        "order number",
        "ordernumber",
    ],
    "customer_email": [
        "customer_email",
        "customer email",
        "customeremail",
        "email",
        "customer_email_address",
        "email_address",
    ],
    "brand_name": [
        "brand_name",
        "brand name",
        "brandname",
        "brand",
        "restaurant",
        "restaurant_name",
        "restaurant name",
        "location",
    ],
    "item_name": [
        "item_name",
        "item name",
        "itemname",
        "item",
        "dish",
        "dish_name",
        "product",
        "product_name",
        "menu_item",
    ],
    "quantity": [
        "quantity",
        "qty",
        "qnty",
        "amount",
        "count",
    ],
    "unit_price": [
        "unit_price",
        "unit price",
        "unitprice",
        "price",
        "item_price",
        "item price",
        "itemprice",
        "cost",
    ],
    "order_date": [
        "order_date",
        "order date",
        "orderdate",
        "date",
        "order_time",
        "order time",
        "datetime",
        "timestamp",
        "created_at",
    ],
    # Optional fields
    "customer_id": [
        "customer_id",
        "customer id",
        "customerid",
        "cust_id",
        "custid",
        "external_customer_id",
    ],
    "customer_name": [
        "customer_name",
        "customer name",
        "customername",
        "name",
        "full_name",
        "fullname",
    ],
    "customer_first_name": [
        "customer_first_name",
        "first_name",
        "firstname",
        "fname",
    ],
    "customer_last_name": [
        "customer_last_name",
        "last_name",
        "lastname",
        "lname",
        "surname",
    ],
    "customer_phone": [
        "customer_phone",
        "phone",
        "phone_number",
        "mobile",
        "telephone",
        "contact",
    ],
    "customer_city": [
        "customer_city",
        "city",
        "location",
        "delivery_city",
    ],
    "category": [
        "category",
        "item_category",
        "item category",
        "product_category",
        "type",
    ],
    "cuisine_type": [
        "cuisine_type",
        "cuisine type",
        "cuisinetype",
        "cuisine",
        "food_type",
        "food type",
    ],
    "order_total": [
        "order_total",
        "order total",
        "ordertotal",
        "total",
        "total_amount",
        "grand_total",
    ],
    "order_channel": [
        "order_channel",
        "channel",
        "source",
        "order_source",
        "platform",
    ],
}


def normalize_header(header: str) -> str:
    """
    Normalize a CSV header for fuzzy matching.

    Converts to lowercase, removes extra spaces, underscores, and special chars.

    Args:
        header: Raw CSV header string

    Returns:
        Normalized header string
    """
    # Convert to lowercase
    normalized = header.lower()

    # Replace underscores and hyphens with spaces
    normalized = normalized.replace("_", " ").replace("-", " ")

    # Strip leading/trailing whitespace
    normalized = normalized.strip()

    # Collapse multiple spaces to single space
    normalized = " ".join(normalized.split())

    return normalized


def get_canonical_field_name(header: str) -> str | None:
    """
    Map a CSV header to its canonical field name.

    Args:
        header: Raw CSV header string

    Returns:
        Canonical field name if match found, None otherwise
    """
    normalized = normalize_header(header)

    # Try exact match first
    for canonical, aliases in COLUMN_ALIASES.items():
        if normalized in [normalize_header(alias) for alias in aliases]:
            return canonical

    return None


# Required fields that must be present in CSV
REQUIRED_FIELDS = [
    "order_id",
    "customer_email",
    "brand_name",
    "item_name",
    "quantity",
    "unit_price",
    "order_date",
]


# Optional fields that enhance data quality if present
OPTIONAL_FIELDS = [
    "customer_id",
    "customer_name",
    "customer_first_name",
    "customer_last_name",
    "customer_phone",
    "customer_city",
    "category",
    "cuisine_type",
    "order_total",
    "order_channel",
]
