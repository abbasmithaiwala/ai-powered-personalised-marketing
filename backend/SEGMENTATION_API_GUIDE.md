# Customer Segmentation API Guide

## Overview

The Customer Segmentation API provides powerful filtering and search capabilities for targeting specific customer groups in marketing campaigns. This guide covers the segmentation endpoints, filter options, and usage patterns.

## Endpoints

### 1. Search Customers

**Endpoint:** `POST /api/v1/customers/search`

Search customers matching specific criteria with pagination support.

**Request Body:**
```json
{
  "filters": {
    "last_order_after": "2024-01-01T00:00:00Z",
    "last_order_before": "2024-12-31T23:59:59Z",
    "total_spend_min": 50.0,
    "total_spend_max": 500.0,
    "total_orders_min": 3,
    "favorite_cuisine": "italian",
    "dietary_flag": "vegetarian",
    "city": "London",
    "order_frequency": "weekly",
    "brand_id": "uuid-here"
  },
  "page": 1,
  "page_size": 25
}
```

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "external_id": "cust_123",
      "email": "customer@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "city": "London",
      "total_orders": 15,
      "total_spend": 250.50,
      "first_order_at": "2024-01-15T12:00:00Z",
      "last_order_at": "2024-02-10T18:30:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 25,
  "pages": 2
}
```

### 2. Count Segment Size

**Endpoint:** `POST /api/v1/customers/segment-count`

Fast count of customers matching filters. Optimized for real-time audience size estimation.

**Request Body:**
```json
{
  "filters": {
    "total_spend_min": 100.0,
    "favorite_cuisine": "thai",
    "order_frequency": "weekly"
  }
}
```

**Response:**
```json
{
  "count": 87
}
```

**Performance:** Target response time <200ms for MVP scale.

## Filter Options

All filters are **optional** and combine with **AND logic**. Empty filters return all customers.

### Order History Filters

| Filter | Type | Description | Example |
|--------|------|-------------|---------|
| `last_order_after` | datetime | Customers who ordered after this date (inclusive) | `"2024-01-01T00:00:00Z"` |
| `last_order_before` | datetime | Customers who ordered before this date (inclusive) | `"2024-12-31T23:59:59Z"` |
| `total_spend_min` | float | Minimum total lifetime spend | `50.0` |
| `total_spend_max` | float | Maximum total lifetime spend | `500.0` |
| `total_orders_min` | int | Minimum number of orders placed | `3` |

### Preference Filters

These filters use the computed customer preference profiles.

| Filter | Type | Description | Allowed Values |
|--------|------|-------------|----------------|
| `favorite_cuisine` | string | Filter by top cuisine preference | Any cuisine (e.g., `"italian"`, `"thai"`, `"indian"`) |
| `dietary_flag` | string | Filter by dietary restriction | `"vegetarian"`, `"vegan"`, `"halal"`, `"gluten_free"` |
| `order_frequency` | string | Filter by ordering pattern | `"daily"`, `"weekly"`, `"monthly"`, `"occasional"` |

### Geographic Filters

| Filter | Type | Description | Example |
|--------|------|-------------|---------|
| `city` | string | Case-insensitive partial match on customer city | `"london"` matches "London", "LONDON", etc. |

### Brand Filters

| Filter | Type | Description | Example |
|--------|------|-------------|---------|
| `brand_id` | UUID | Customers who have ordered from specific brand | `"550e8400-e29b-41d4-a716-446655440000"` |

## Usage Examples

### Example 1: High-Value Italian Food Lovers in London

```python
import httpx

response = httpx.post(
    "http://localhost:8000/api/v1/customers/search",
    json={
        "filters": {
            "city": "London",
            "favorite_cuisine": "italian",
            "total_spend_min": 100.0,
            "order_frequency": "weekly"
        },
        "page": 1,
        "page_size": 50
    }
)

data = response.json()
print(f"Found {data['total']} customers")
for customer in data['items']:
    print(f"- {customer['email']}: ₹{customer['total_spend']}")
```

### Example 2: Vegetarian Customers Who Haven't Ordered Recently

```python
from datetime import datetime, timedelta

cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()

response = httpx.post(
    "http://localhost:8000/api/v1/customers/search",
    json={
        "filters": {
            "dietary_flag": "vegetarian",
            "last_order_before": cutoff_date
        },
        "page": 1,
        "page_size": 100
    }
)

# Use these customers for a re-engagement campaign
customers = response.json()['items']
```

### Example 3: Count Audience Before Creating Campaign

```python
# First, check how many customers match your criteria
count_response = httpx.post(
    "http://localhost:8000/api/v1/customers/segment-count",
    json={
        "filters": {
            "total_orders_min": 5,
            "favorite_cuisine": "thai",
            "city": "Manchester"
        }
    }
)

audience_size = count_response.json()['count']
print(f"Campaign will reach {audience_size} customers")

# If size is acceptable, use same filters to create campaign
if audience_size > 10:
    campaign_response = httpx.post(
        "http://localhost:8000/api/v1/campaigns",
        json={
            "name": "Thai Food Lovers - Manchester",
            "purpose": "Promote new Thai menu items",
            "segment_filters": {
                "total_orders_min": 5,
                "favorite_cuisine": "thai",
                "city": "Manchester"
            }
        }
    )
```

### Example 4: Brand-Specific Re-Engagement

```python
# Find customers of a specific brand who haven't ordered in 60 days
brand_id = "uuid-of-brand"
sixty_days_ago = (datetime.now() - timedelta(days=60)).isoformat()

response = httpx.post(
    "http://localhost:8000/api/v1/customers/search",
    json={
        "filters": {
            "brand_id": brand_id,
            "last_order_before": sixty_days_ago
        }
    }
)
```

## Integration with Campaigns

The segmentation API is designed to work seamlessly with the Campaign API:

1. **Preview Audience Size**: Use `/segment-count` to check how many customers match your criteria
2. **Create Campaign**: Use the same `SegmentFilters` in the campaign `segment_filters` field
3. **Execute Campaign**: The campaign service uses the segmentation service internally to find recipients
4. **Monitor Results**: Track campaign performance by recipient demographics

## Filter Logic

### AND Combination

All filters combine with AND logic:

```json
{
  "filters": {
    "city": "London",
    "total_spend_min": 100.0,
    "favorite_cuisine": "italian"
  }
}
```

This finds customers who are:
- In London **AND**
- Spent at least ₹100 **AND**
- Have Italian as a favorite cuisine

### Empty Filters

An empty filter object returns **all customers**:

```json
{
  "filters": {}
}
```

## Performance Considerations

### Count Queries

The `/segment-count` endpoint is optimized for speed:
- Uses COUNT(*) with indexed filters
- No data loading or serialization overhead
- Target: <200ms response time

Use this for real-time UI updates (e.g., showing audience size as filters change).

### Search Queries

The `/search` endpoint includes data loading:
- Loads customer records with eager-loaded preferences
- Serializes to JSON
- Supports pagination for large result sets

For large audiences (>1000), use pagination with reasonable page sizes (25-100).

## Error Handling

### Invalid Filter Values

```json
{
  "detail": "dietary_flag must be one of {'vegetarian', 'vegan', 'halal', 'gluten_free'}"
}
```

### Invalid Pagination

```json
{
  "detail": "page must be >= 1"
}
```

## Testing

Run segmentation tests:

```bash
# Service layer tests
pytest tests/services/test_segmentation_service.py -v

# API endpoint tests
pytest tests/api/test_customers.py -v
```

All tests should pass with <2s total runtime.

## Next Steps

- **Campaign Integration**: Use segments to create targeted campaigns (see [CAMPAIGN_API_GUIDE.md](CAMPAIGN_API_GUIDE.md))
- **Message Generation**: Combine segmentation with personalized messaging (TASK-014)
- **Analytics**: Track campaign performance by segment characteristics
