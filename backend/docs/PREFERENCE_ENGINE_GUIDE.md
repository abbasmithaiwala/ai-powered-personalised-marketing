# Preference Engine Usage Guide

## Overview

The Preference Engine analyzes customer order history to compute personalized preference signals that drive recommendations and marketing campaigns.

## Quick Start

### 1. Automatic Computation

Preferences are **automatically computed** after CSV ingestion for all affected customers.

```bash
# Upload CSV via API
curl -X POST http://localhost:8000/api/v1/ingestion/upload \
  -F "file=@orders.csv" \
  -F "csv_type=orders"
```

### 2. Manual Recomputation

Trigger preference computation for a specific customer:

```bash
curl -X POST http://localhost:8000/api/v1/customers/{customer_id}/recompute-preferences
```

### 3. Programmatic Usage

```python
from app.db.session import AsyncSessionLocal
from app.services.intelligence import PreferenceEngine

async def compute_preferences(customer_id):
    async with AsyncSessionLocal() as db:
        engine = PreferenceEngine(db)
        preference = await engine.compute_preferences(customer_id)
        print(f"Computed preferences version {preference.version}")
```

## Preference Signals

### Favorite Cuisines
- **Top 5** cuisines ranked by frequency and recency
- **Score Range:** 0-1 (normalized)
- **Recency Weights:**
  - Last 30 days: 1.0x
  - 30-90 days: 0.7x
  - 90-180 days: 0.3x

Example:
```json
{
  "italian": 1.0,
  "thai": 0.85,
  "chinese": 0.72,
  "mexican": 0.58,
  "indian": 0.45
}
```

### Favorite Categories
- Similar to cuisines, but for food categories
- Examples: mains, starters, desserts, drinks

### Dietary Flags
- **Threshold:** 80% of orders must match
- **Supported Flags:**
  - `vegetarian`
  - `vegan`
  - `halal`
  - `gluten_free`

Example:
```json
{
  "vegetarian": true,
  "vegan": false,
  "halal": false,
  "gluten_free": false
}
```

### Price Sensitivity
- **low:** Average order <₹500
- **medium:** Average order ₹500-2000
- **high:** Average order >₹2000

### Order Frequency
- **daily:** >20 orders/month
- **weekly:** 4-20 orders/month
- **monthly:** 1-4 orders/month
- **occasional:** <1 order/month

### Preferred Order Times
Distribution across four time periods:

Example:
```json
{
  "breakfast": 0.15,  // 6-11
  "lunch": 0.30,      // 11-15
  "dinner": 0.50,     // 17-22
  "late_night": 0.05  // 22-6
}
```

### Brand Affinity
Ranked list of brands with preference scores:

Example:
```json
[
  {
    "brand_id": "uuid-1",
    "brand_name": "Pizza Palace",
    "score": 0.95
  },
  {
    "brand_id": "uuid-2",
    "brand_name": "Thai Garden",
    "score": 0.78
  }
]
```

## Configuration

### Adjusting Price Thresholds

For different markets/currencies:

```python
from app.services.intelligence.price_analyzer import PriceAnalyzer

# Set thresholds in USD
PriceAnalyzer.set_thresholds(low=15.0, high=40.0)
```

### Adjusting Dietary Threshold

Edit `backend/app/services/intelligence/dietary_analyzer.py`:

```python
class DietaryAnalyzer:
    THRESHOLD = 0.8  # Change to 0.7 for 70%, etc.
```

### Adjusting Recency Weights

Edit `backend/app/services/intelligence/cuisine_analyzer.py`:

```python
class CuisineAnalyzer:
    RECENT_WEIGHT = 1.0
    MEDIUM_WEIGHT = 0.7
    OLD_WEIGHT = 0.3
```

## Performance

- **100-order customer:** <500ms
- **1000-order customer:** ~2-3 seconds
- **Concurrent computations:** Safe (per-customer transactions)

## Monitoring

Check preference computation status:

```python
from sqlalchemy import select
from app.models.customer_preference import CustomerPreference

# Check if preferences exist
result = await db.execute(
    select(CustomerPreference).where(
        CustomerPreference.customer_id == customer_id
    )
)
pref = result.scalar_one_or_none()

if pref:
    print(f"Version: {pref.version}")
    print(f"Last computed: {pref.last_computed_at}")
else:
    print("No preferences computed yet")
```

## Troubleshooting

### No Preferences Computed

**Symptom:** Customer has orders but no preferences

**Solution:** Manually trigger computation:
```bash
curl -X POST http://localhost:8000/api/v1/customers/{id}/recompute-preferences
```

### Empty Preference Signals

**Symptom:** All preference fields are null/empty

**Causes:**
- Customer has only 1 order (minimal data)
- Orders have no menu items linked
- Menu items missing cuisine/category data

**Solution:** Ensure menu items have:
- `cuisine_type` populated
- `category` populated
- `dietary_tags` if applicable

### Preferences Not Updating

**Symptom:** Preferences stale after new orders

**Solution:** Preferences auto-compute on CSV ingestion. For manual orders added via API, trigger recomputation explicitly.

## Testing

### Unit Tests
```bash
cd backend
source .venv/bin/activate
pytest tests/test_preference_engine.py -v
```

### Manual Test Script
```bash
python test_preference_manual.py customer@example.com
```

### Integration Test
```bash
# 1. Upload test CSV
curl -X POST http://localhost:8000/api/v1/ingestion/upload \
  -F "file=@test_orders.csv" \
  -F "csv_type=orders"

# 2. Check preference was computed
curl http://localhost:8000/api/v1/customers/{id}/preferences
```

## Best Practices

1. **Recompute After Bulk Changes:** After updating menu items (e.g., adding dietary tags), recompute preferences for affected customers

2. **Monitor Version Numbers:** Track `version` field to detect stale preferences

3. **Handle Edge Cases:** New customers with 1 order will have minimal preferences—wait for more order history

4. **Batch Processing:** For bulk recomputation, use background jobs to avoid API timeouts

5. **Cache Preferences:** Preferences are expensive to compute—cache results and only recompute when order history changes

## API Reference

### Recompute Preferences

**Endpoint:** `POST /api/v1/customers/{customer_id}/recompute-preferences`

**Response:** 200 OK
```json
{
  "id": "uuid",
  "customer_id": "uuid",
  "favorite_cuisines": {...},
  "favorite_categories": {...},
  "dietary_flags": {...},
  "price_sensitivity": "medium",
  "order_frequency": "weekly",
  "brand_affinity": [...],
  "preferred_order_times": {...},
  "last_computed_at": "2024-01-15T12:00:00Z",
  "version": 3,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T12:00:00Z"
}
```

**Errors:**
- 404: Customer not found
- 500: Computation error
