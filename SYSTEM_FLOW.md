# AI-Powered Personalised Marketing System - Complete Flow Documentation

## Overview

This document provides a comprehensive explanation of how the AI-Powered Personalised Marketing system works, with detailed focus on:
- Menu embeddings creation and storage
- User taste profile generation
- Complete data flow from ingestion to campaign execution
- Integration between components

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA INGESTION LAYER                                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   CSV Upload │    │  Order Data  │    │  Menu Items  │                  │
│  │   API        │───▶│  Ingestion   │───▶│   Storage    │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                                │                                            │
└────────────────────────────────┼────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     VECTOR EMBEDDING LAYER                                  │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    EmbeddingBuilder Service                        │    │
│  │  ┌─────────────┐  ┌────────────────┐  ┌────────────────────────┐  │    │
│  │  │ Build Text  │──▶│ Embed via      │──▶│ Store in Qdrant      │  │    │
│  │  │ from Menu   │  │ OpenRouter/    │  │ Vector DB            │  │    │
│  │  │ Fields      │  │ Local Model    │  │ (menu_embeddings)    │  │    │
│  │  └─────────────┘  └────────────────┘  └────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CUSTOMER INTELLIGENCE LAYER                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    PreferenceEngine Service                        │    │
│  │  ┌─────────────────┐  ┌──────────────┐  ┌──────────────────────┐  │    │
│  │  │ Analyze Orders  │──▶│ Compute      │──▶│ Create/Update        │  │    │
│  │  │ & Extract Data  │  │ Preferences  │  │ Preference Record    │  │    │
│  │  └─────────────────┘  └──────────────┘  └──────────────────────┘  │    │
│  │                                                                     │    │
│  │  Components:                                                        │    │
│  │  • CuisineAnalyzer (favorite cuisines)                             │    │
│  │  • CategoryAnalyzer (favorite categories)                          │    │
│  │  • DietaryAnalyzer (dietary restrictions)                          │    │
│  │  • PriceAnalyzer (price sensitivity)                               │    │
│  │  • TimingAnalyzer (order patterns)                                 │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                  │                                          │
│                                  ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                   TasteProfileBuilder Service                      │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │    │
│  │  │ Fetch Item   │──▶│ Apply        │──▶│ Weighted Average +      │  │    │
│  │  │ Embeddings   │  │ Recency      │  │ L2 Normalization        │  │    │
│  │  └──────────────┘  └──────────────┘  └─────────────────────────┘  │    │
│  │                                                     │               │    │
│  │                                                     ▼               │    │
│  │  ┌────────────────────────────────────────────────────────────┐    │    │
│  │  │       Store Taste Profile Vector in Qdrant                 │    │    │
│  │  │       (customer_taste_profiles collection)                 │    │    │
│  │  └────────────────────────────────────────────────────────────┘    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RECOMMENDATION LAYER                                     │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                  RecommendationEngine Service                      │    │
│  │                                                                     │    │
│  │  ┌────────────────────┐          ┌────────────────────┐          │    │
│  │  │ Vector Similarity  │          │ Fallback Strategy  │          │    │
│  │  │ Search (Cosine)    │          │ (Popular Items)    │          │    │
│  │  │                    │          │                    │          │    │
│  │  │ Taste Profile      │◄────────▶│                    │          │    │
│  │  │ vs Menu Embeddings │          │ If no taste        │          │    │
│  │  │                    │          │ profile exists     │          │    │
│  │  └────────┬───────────┘          └────────────────────┘          │    │
│  │           │                                                        │    │
│  │           ▼                                                        │    │
│  │  ┌────────────────────────────────────────────────────────────┐    │    │
│  │  │ Filters Applied:                                           │    │    │
│  │  │ • Exclude recently ordered items (30 days)                 │    │    │
│  │  │ • Respect dietary restrictions                             │    │    │
│  │  │ • Include at least one new brand item                      │    │    │
│  │  │ • Build human-readable reasons                             │    │    │
│  │  └────────────────────────────────────────────────────────────┘    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CAMPAIGN & MESSAGING LAYER                               │
│  ┌────────────────────┐    ┌────────────────────┐    ┌──────────────────┐  │
│  │ Segmentation       │───▶│ MessageGenerator   │───▶│ CampaignService  │  │
│  │ Service            │    │ (LLM Integration)  │    │                  │  │
│  └────────────────────┘    └────────────────────┘    └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Menu Embeddings - How They Work

### What Are Menu Embeddings?

Menu embeddings are **high-dimensional vector representations** (384 dimensions) of menu items that capture semantic meaning. They enable the system to understand relationships between items (e.g., "pizza" is similar to "calzone" even if they have different names).

### Embedding Generation Process

#### Step 1: Build Rich Text Representation

The `EmbeddingBuilder.build_item_text()` method constructs a descriptive text by combining multiple menu item fields:

```python
def build_item_text(self, item: MenuItem) -> str:
    parts = []
    
    # Core identity
    if item.name:
        parts.append(item.name)  # e.g., "Margherita Pizza"
    
    # Cuisine and category context
    if item.cuisine_type and item.category:
        parts.append(f"{item.cuisine_type} {item.category}")  # e.g., "Italian Main"
    
    # Description
    if item.description:
        parts.append(item.description)
    
    # Flavor profile
    if item.flavor_tags:
        parts.append(f"flavors: {', '.join(item.flavor_tags)}")
    
    # Dietary information
    if item.dietary_tags:
        parts.append(f"dietary: {', '.join(item.dietary_tags)}")
    
    return " | ".join(parts)
```

**Example Output:**
```
"Margherita Pizza | Italian Main | Classic Neapolitan style with fresh mozzarella, tomato sauce, and basil | flavors: savory, fresh, classic | dietary: vegetarian"
```

#### Step 2: Generate Vector Embedding

The text is converted to a 384-dimensional vector using:
- **Primary:** OpenRouter API with `text-embedding-3-small` model
- **Fallback:** Local `all-MiniLM-L6-v2` model (sentence-transformers)

```python
async def generate_embedding(self, item: MenuItem) -> List[float]:
    text = self.build_item_text(item)
    embedding = await embedding_service.embed(text)
    # Returns vector like: [0.023, -0.156, 0.089, ...] (384 floats)
    return embedding
```

#### Step 3: Store in Qdrant Vector Database

```python
async def upsert_item_embedding(self, item: MenuItem) -> bool:
    embedding = await self.generate_embedding(item)
    
    payload = {
        "menu_item_id": str(item.id),
        "brand_id": str(item.brand_id),
        "name": item.name,
        "category": item.category,
        "cuisine_type": item.cuisine_type,
        "dietary_tags": item.dietary_tags or [],
        "price": float(item.price) if item.price else None,
    }
    
    point = PointStruct(
        id=str(item.id),  # Use UUID as point ID
        vector=embedding,
        payload=payload,
    )
    
    # Store in Qdrant collection: "menu_item_embeddings"
    success = await vector_store.upsert_points(
        collection_name=MENU_ITEM_EMBEDDINGS_COLLECTION,
        points=[point],
    )
```

### Storage Structure

**Qdrant Collection: `menu_item_embeddings`**
- **Vector Dimension:** 384
- **Distance Metric:** Cosine Similarity
- **Point ID:** Menu item UUID
- **Payload:** Metadata for filtering and display

```
Point Structure:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "vector": [0.023, -0.156, 0.089, ...],  // 384 dimensions
  "payload": {
    "menu_item_id": "550e8400-e29b-41d4-a716-446655440000",
    "brand_id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "Margherita Pizza",
    "category": "Main",
    "cuisine_type": "Italian",
    "dietary_tags": ["vegetarian"],
    "price": 12.99
  }
}
```

### When Are Embeddings Created?

1. **On Menu Item Creation:** New items are automatically embedded
2. **Batch Processing:** `embed_all_items()` can process all menu items
3. **Updates:** When menu item details change, embeddings are regenerated

---

## 2. User Taste Profiles - How They Work

### What Are Taste Profiles?

Taste profiles are **personalized vector representations** of a customer's food preferences, created by aggregating embeddings of items they've ordered, weighted by recency and quantity.

### Taste Profile Generation Process

#### Step 1: Fetch Customer Order History

```python
result = await self.session.execute(
    select(Customer)
    .options(
        selectinload(Customer.orders)
        .selectinload(Order.order_items)
        .selectinload(OrderItem.menu_item)
    )
    .where(Customer.id == customer_id)
)
customer = result.scalar_one_or_none()
```

This loads:
- All customer orders
- All order items per order
- Linked menu items with embedding IDs

#### Step 2: Compute Recency Weights

Orders are weighted by how recently they were placed using **exponential decay**:

```python
@staticmethod
def compute_recency_weight(order_date: datetime) -> float:
    """
    Uses formula: exp(-days_since_order / 90.0)
    
    Recent orders (0-30 days): ~0.7-1.0 weight
    Medium age (30-90 days): ~0.4-0.7 weight
    Older (90-180 days): ~0.1-0.4 weight
    """
    days_since = (now - order_date).total_seconds() / 86400.0
    weight = math.exp(-days_since / 90.0)  # 90-day half-life
    return weight
```

**Why This Matters:** Recent orders reflect current preferences better than old ones.

#### Step 3: Retrieve Item Embeddings

For each ordered item, fetch its embedding from Qdrant:

```python
for order in customer.orders:
    for order_item in order.order_items:
        if order_item.menu_item and order_item.menu_item.embedding_id:
            # Get the 384-dimensional vector from Qdrant
            item_embedding = await self._get_item_embedding(
                order_item.menu_item.embedding_id
            )
```

#### Step 4: Calculate Weighted Average

```python
# Initialize zero vector
profile_vector = [0.0] * VECTOR_DIMENSION  # 384 zeros

# Accumulate weighted embeddings
for embedding, weight in weighted_embeddings:
    for i in range(len(embedding)):
        profile_vector[i] += embedding[i] * weight

# Normalize by total weight (weighted average)
if total_weight > 0:
    profile_vector = [val / total_weight for val in profile_vector]
```

**Example Calculation:**
```
Order 1 (5 days ago, weight=0.95): Margherita Pizza vector
Order 2 (20 days ago, weight=0.80): Pepperoni Pizza vector
Order 3 (60 days ago, weight=0.51): Caesar Salad vector

Profile Vector = (0.95 × Margherita + 0.80 × Pepperoni + 0.51 × Salad) / 2.26
```

#### Step 5: L2 Normalization

```python
@staticmethod
def _l2_normalize(vector: List[float]) -> List[float]:
    """
    Make vector magnitude = 1 for consistent similarity comparisons
    """
    magnitude = math.sqrt(sum(x * x for x in vector))
    if magnitude == 0:
        return vector
    return [x / magnitude for x in vector]
```

**Why Normalize?** Ensures all taste profiles have the same scale, making cosine similarity comparisons fair.

#### Step 6: Store in Qdrant

```python
point = PointStruct(
    id=str(customer_id),  # Use customer UUID as point ID
    vector=profile_vector,
    payload={
        "customer_id": str(customer_id),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    },
)

success = await vector_store.upsert_points(
    collection_name=CUSTOMER_TASTE_PROFILES_COLLECTION,
    points=[point],
)
```

### Storage Structure

**Qdrant Collection: `customer_taste_profiles`**
- **Vector Dimension:** 384 (same as menu items)
- **Distance Metric:** Cosine Similarity
- **Point ID:** Customer UUID

```
Point Structure:
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "vector": [0.045, -0.123, 0.234, ...],  // 384 dimensions (L2 normalized)
  "payload": {
    "customer_id": "770e8400-e29b-41d4-a716-446655440002",
    "last_updated": "2024-01-15T14:30:00Z"
  }
}
```

### When Are Taste Profiles Created?

Taste profiles are automatically built when preferences are computed:

```python
# In PreferenceEngine.compute_preferences()
async def compute_preferences(self, customer_id: UUID):
    # ... compute all preference signals ...
    
    # Trigger taste profile computation
    taste_builder = TasteProfileBuilder(self.db)
    taste_result = await taste_builder.build_taste_profile(customer_id)
    
    return preference
```

**Trigger Points:**
1. After CSV data ingestion (batch processing)
2. When new orders are added
3. Via `rebuild_taste_profiles.py` script for all customers

---

## 3. Complete System Flow

### Data Flow Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          PHASE 1: DATA INGESTION                        │
└─────────────────────────────────────────────────────────────────────────┘

1. CSV Upload via API
   ↓
2. CSV Validation (headers, required fields)
   ↓
3. Data Parsing → Orders, OrderItems, Customers, MenuItems
   ↓
4. Storage in PostgreSQL
   ├─ customers table
   ├─ orders table
   ├─ order_items table
   ├─ menu_items table
   └─ brands table

┌─────────────────────────────────────────────────────────────────────────┐
│                       PHASE 2: VECTOR EMBEDDING                         │
└─────────────────────────────────────────────────────────────────────────┘

5. EmbeddingBuilder processes menu items
   ↓
6. Generate embeddings for each menu item
   ├─ Build rich text from name, cuisine, description, tags
   ├─ Convert text to 384-dim vector via OpenRouter/local model
   └─ Store in Qdrant (menu_item_embeddings collection)
   ↓
7. Update menu_item.embedding_id in PostgreSQL

┌─────────────────────────────────────────────────────────────────────────┐
│                      PHASE 3: CUSTOMER INTELLIGENCE                     │
└─────────────────────────────────────────────────────────────────────────┘

8. PreferenceEngine.compute_preferences(customer_id)
   ├─ Analyze order history
   │   ├─ CuisineAnalyzer: Favorite cuisines (top 5)
   │   ├─ CategoryAnalyzer: Favorite categories
   │   ├─ DietaryAnalyzer: Dietary restrictions detected
   │   ├─ PriceAnalyzer: Price sensitivity (low/medium/high)
   │   ├─ TimingAnalyzer: Order frequency & preferred times
   │   └─ BrandAffinity: Preferred brands with scores
   ↓
   └─ Create/Update customer_preferences record

9. TasteProfileBuilder.build_taste_profile(customer_id)
   ├─ Fetch all orders with menu items
   ├─ Retrieve embeddings for ordered items from Qdrant
   ├─ Apply recency weighting (exponential decay)
   ├─ Calculate weighted average
   ├─ L2 normalize the result
   └─ Store in Qdrant (customer_taste_profiles collection)

┌─────────────────────────────────────────────────────────────────────────┐
│                       PHASE 4: RECOMMENDATIONS                          │
└─────────────────────────────────────────────────────────────────────────┘

10. RecommendationEngine.generate_recommendations(customer_id)
    ├─ Check if taste profile exists in Qdrant
    │   ├─ YES: Use vector similarity search
    │   │   ├─ Query menu_item_embeddings with taste vector
    │   │   ├─ Apply filters (dietary, recent orders, etc.)
    │   │   └─ Return top N similar items
    │   │
    │   └─ NO: Use fallback strategy
    │       ├─ Query popular items from PostgreSQL
    │       └─ Return trending choices
    │
    └─ Build recommendation reasons from preferences
        ("Matches your preference for Italian cuisine")

┌─────────────────────────────────────────────────────────────────────────┐
│                       PHASE 5: CAMPAIGN EXECUTION                       │
└─────────────────────────────────────────────────────────────────────────┘

11. Campaign Creation
    ├─ Define segment filters (cuisine, dietary, location, etc.)
    ├─ Set campaign purpose and offer
    └─ Save as draft

12. Campaign Preview (optional)
    ├─ SegmentationService.find_customers(filters)
    ├─ Sample N customers from segment
    └─ Generate preview messages via MessageGenerator

13. Campaign Execution
    ├─ Get all customers matching filters
    ├─ For each customer:
    │   ├─ MessageGenerator.generate_message()
    │   │   ├─ Get personalized recommendations
    │   │   ├─ Build LLM prompt with customer context
    │   │   ├─ Call OpenRouter/Groq API
    │   │   ├─ Parse JSON response
    │   │   └─ Return structured message (subject, body)
    │   │
    │   └─ Store generated message in campaign_recipients
    │
    └─ Update campaign status to "completed"

14. Result: Personalized marketing messages for each customer
    - Subject line tailored to their preferences
    - Body text referencing their order history
    - Recommended items based on taste profile
```

---

## 4. Key Algorithms Explained

### Recency Weighting

Orders lose relevance over time. The system uses exponential decay:

```
weight = e^(-days/90)

Examples:
- 0 days ago: weight = 1.00 (full weight)
- 30 days ago: weight = 0.72
- 90 days ago: weight = 0.37
- 180 days ago: weight = 0.14
```

**Purpose:** A customer's pizza order from yesterday matters more than one from 6 months ago.

### Vector Similarity Search

```python
# In Qdrant, cosine similarity between taste profile and menu items
cosine_similarity(A, B) = (A · B) / (||A|| × ||B||)

# Since vectors are L2 normalized:
cosine_similarity(A, B) = A · B  (dot product)

Score range: -1 (opposite) to 1 (identical)
```

**Interpretation:**
- Score 0.8+: Very similar taste preferences
- Score 0.5-0.8: Similar preferences
- Score 0.3-0.5: Some overlap
- Score < 0.3: Different preferences

### Dietary Filtering

```python
def _violates_dietary_restrictions(item_tags, restrictions):
    # Vegetarian customer
    if "vegetarian" in restrictions:
        if not ("vegetarian" in item_tags or "vegan" in item_tags):
            return True  # Exclude non-vegetarian items
    
    # Vegan customer
    if "vegan" in restrictions:
        if "vegan" not in item_tags:
            return True  # Exclude non-vegan items
    
    # Other restrictions (halal, gluten_free, etc.)
    for restriction in restrictions:
        if restriction not in item_tags:
            return True
    
    return False
```

---

## 5. Data Models

### PostgreSQL Tables

```sql
-- Core entities
brands (id, name, description, ...)
customers (id, email, first_name, last_name, city, total_spend, total_orders, ...)
menu_items (id, brand_id, name, description, category, cuisine_type, price, dietary_tags, flavor_tags, embedding_id, ...)
orders (id, customer_id, brand_id, order_date, total_amount, ...)
order_items (id, order_id, menu_item_id, item_name, quantity, ...)

-- Intelligence
customer_preferences (
  id, customer_id,
  favorite_cuisines JSONB,
  favorite_categories JSONB,
  dietary_flags JSONB,
  price_sensitivity,
  order_frequency,
  brand_affinity JSONB,
  preferred_order_times JSONB,
  last_computed_at
)

-- Campaigns
campaigns (id, name, description, purpose, segment_filters JSONB, status, ...)
campaign_recipients (id, campaign_id, customer_id, generated_message JSONB, status, ...)
```

### Qdrant Collections

```
Collection: menu_item_embeddings
├─ Vector: 384 dimensions, Cosine distance
├─ Point ID: Menu item UUID
└─ Payload: {menu_item_id, brand_id, name, category, cuisine_type, dietary_tags, price}

Collection: customer_taste_profiles
├─ Vector: 384 dimensions, Cosine distance
├─ Point ID: Customer UUID
└─ Payload: {customer_id, last_updated}
```

---

## 6. API Flow Examples

### Example 1: New Customer Onboarding

```
POST /api/v1/ingestion/csv
├─ Upload: orders.csv
├─ Processing:
│   ├─ Parse CSV
│   ├─ Create customers, orders, order_items, menu_items
│   ├─ Trigger embedding generation for new menu items
│   ├─ Compute preferences for each customer
│   └─ Build taste profiles
└─ Result: All data ingested with embeddings and profiles ready
```

### Example 2: Get Recommendations

```
GET /api/v1/customers/{id}/recommendations
├─ Fetch taste profile from Qdrant
├─ Search menu_item_embeddings with taste vector
├─ Filter results (dietary, recent orders)
├─ Build recommendation reasons
└─ Return: [{menu_item_id, name, brand, score, reason}, ...]
```

### Example 3: Create Campaign

```
POST /api/v1/campaigns
├─ Create campaign record (status: draft)
└─ Define segment filters

POST /api/v1/campaigns/{id}/preview
├─ Find customers matching filters
├─ Generate sample messages via LLM
└─ Return preview with estimated audience size

POST /api/v1/campaigns/{id}/execute
├─ Find all matching customers
├─ For each customer:
│   ├─ Get recommendations
│   ├─ Generate personalized message
│   └─ Store in campaign_recipients
└─ Update campaign status: completed
```

---

## 7. Key Files and Their Roles

| File | Purpose |
|------|---------|
| `embedding_builder.py` | Generates and manages menu item embeddings |
| `taste_profile_builder.py` | Builds customer taste profile vectors |
| `recommendation_engine.py` | Generates personalized recommendations |
| `preference_engine.py` | Orchestrates preference computation |
| `cuisine_analyzer.py` | Analyzes cuisine preferences with recency |
| `dietary_analyzer.py` | Detects dietary restrictions |
| `message_generator.py` | Generates personalized messages via LLM |
| `segmentation_service.py` | Filters customers by segment criteria |
| `campaign_service.py` | Manages campaign lifecycle |
| `vector_store.py` | Qdrant client and collection management |
| `embedding_service.py` | Text embedding via OpenRouter/local model |

---

## 8. Summary

The system creates a powerful personalization engine by:

1. **Converting menu items to vectors** that capture semantic meaning
2. **Aggregating customer orders** into taste profile vectors with recency weighting
3. **Using vector similarity search** to find items similar to customer preferences
4. **Generating personalized messages** using LLMs with customer context
5. **Executing targeted campaigns** to specific customer segments

This architecture enables:
- **Semantic understanding** of food items and preferences
- **Continuous learning** from new order data
- **Scalable personalization** via vector database
- **Automated marketing** with AI-generated content
