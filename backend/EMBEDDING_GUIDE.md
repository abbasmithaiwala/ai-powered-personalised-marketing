# Menu Item Embedding System - Quick Reference Guide

## Overview
The embedding system automatically generates semantic vectors for menu items, enabling similarity-based search and recommendations.

## How It Works

### Automatic Embedding Generation

**When you create a menu item:**
```bash
POST /api/v1/menu-items
{
  "name": "Truffle Risotto",
  "brand_id": "...",
  "description": "Creamy arborio rice with black truffle",
  "category": "Mains",
  "cuisine_type": "Italian",
  "dietary_tags": ["vegetarian", "gluten-free"],
  "flavor_tags": ["rich", "umami", "earthy"]
}
```

**What happens:**
1. Menu item saved to PostgreSQL
2. Embedding text constructed: `"Truffle Risotto | Italian Mains | Creamy arborio rice... | flavors: rich, umami, earthy | dietary: vegetarian, gluten-free"`
3. Text converted to 384-dimensional vector
4. Vector stored in Qdrant with metadata
5. `embedding_id` field updated in database
6. Response returned immediately (embedding happens in background)

**When you update a menu item:**
```bash
PUT /api/v1/menu-items/{id}
{
  "description": "Updated description",
  "flavor_tags": ["rich", "umami", "earthy", "luxurious"]
}
```

**What happens:**
- If content changed (name, description, cuisine, category, tags): **Re-embeds automatically**
- If only metadata changed (price, is_available): **No re-embedding**

### Manual Batch Operations

**Embed all items (useful for initial setup):**
```bash
POST /api/v1/admin/embed-all-items
```

**Embed items for specific brand:**
```bash
POST /api/v1/admin/embed-all-items?brand_id=<uuid>
```

**Response:**
```json
{
  "message": "Batch embedding completed",
  "results": {
    "total": 150,
    "successful": 148,
    "failed": 1,
    "skipped": 1
  }
}
```

## Checking Embedding Status

**Get menu item:**
```bash
GET /api/v1/menu-items/{id}
```

**Response:**
```json
{
  "id": "...",
  "name": "Truffle Risotto",
  "embedding_id": "..."  // ← If null, embedding failed or pending
}
```

## Troubleshooting

### Embedding ID is null
**Possible causes:**
1. Embedding generation failed (check logs)
2. Qdrant not connected
3. Embedding service unavailable

**Solutions:**
```bash
# Re-trigger embedding for specific item (update it)
PUT /api/v1/menu-items/{id}
{ "description": "..." }  # Any content field

# Or batch re-embed all items
POST /api/v1/admin/embed-all-items
```

### Slow menu item creation
**Cause:** Embedding generation adds 50-300ms to request
**Solution:** This is expected behavior. For bulk imports, embeddings can be disabled temporarily and batch-generated after.

### Embeddings not updating after item change
**Cause:** Only content fields trigger re-embedding
**Content fields:** name, description, cuisine_type, category, dietary_tags, flavor_tags
**Non-content:** price, is_available

## Performance Tips

### For Bulk Data Import
1. Import menu items via CSV (embeddings auto-generate)
2. Wait for embeddings to complete (check embedding_id fields)
3. Alternatively: Disable auto-embedding during import, then batch-embed after

### For Regular Operations
- Create/update items normally
- Embeddings happen automatically in background
- No special handling needed

## Technical Details

### Embedding Model
- **Local:** all-MiniLM-L6-v2 (384 dimensions)
- **OpenRouter:** text-embedding-3-small (1536 dimensions)
- Configured via `OPENROUTER_API_KEY` environment variable

### Vector Storage
- **Database:** Qdrant
- **Collection:** `menu_item_embeddings`
- **Distance:** Cosine similarity
- **Payload:** Includes brand_id, name, category, cuisine_type, dietary_tags, price

### What Gets Embedded

**Text construction priority:**
1. **Name** (required)
2. **Cuisine + Category** (e.g., "Italian Mains")
3. **Description** (full text)
4. **Flavor tags** (e.g., "flavors: rich, umami, earthy")
5. **Dietary tags** (e.g., "dietary: vegetarian, gluten-free")

**Separator:** ` | ` (pipe with spaces) for clarity

## Common Use Cases

### Initial Catalog Setup
```bash
# 1. Import menu items (creates items without embeddings)
POST /api/v1/ingestion/upload
# Upload CSV with menu items

# 2. Batch generate all embeddings
POST /api/v1/admin/embed-all-items
```

### Adding New Menu Item
```bash
# Just create it - embedding happens automatically
POST /api/v1/menu-items
{...}
```

### Updating Seasonal Menu
```bash
# Update items - embeddings regenerate automatically for content changes
PUT /api/v1/menu-items/{id}
{...}
```

### Removing Items from Search
```bash
# Soft delete (set is_available = false)
DELETE /api/v1/menu-items/{id}

# Embeddings remain in Qdrant but won't be used in recommendations
# (recommendation engine filters by is_available)
```

## Monitoring

**Check logs for embedding events:**
```
embedding_generated - Successfully generated embedding
item_embedding_upserted - Stored in Qdrant
embedding_generation_failed - Error occurred
```

**Key metrics to monitor:**
- Embedding generation latency
- Failed embedding count
- Qdrant connection status

## API Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/menu-items` | Create item (auto-embed) |
| PUT | `/api/v1/menu-items/{id}` | Update item (re-embed if content changed) |
| GET | `/api/v1/menu-items/{id}` | Get item (check embedding_id) |
| POST | `/api/v1/admin/embed-all-items` | Batch embed all items |
| POST | `/api/v1/admin/embed-all-items?brand_id=X` | Batch embed for brand |

## Next Steps

Once embeddings are in place, you can:
1. **TASK-011:** Build customer taste profiles from order history
2. **TASK-012:** Generate personalized recommendations using vector similarity
3. **Search:** Implement semantic menu search
4. **Analytics:** Find similar items, cluster dishes by cuisine style

---

For implementation details, see: [TASK010_SUMMARY.md](TASK010_SUMMARY.md)
