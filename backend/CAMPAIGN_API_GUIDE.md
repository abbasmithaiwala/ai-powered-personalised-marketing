# Campaign API Guide

## Overview

The Campaign API provides full lifecycle management for AI-powered marketing campaigns. It allows you to:

1. **Create campaigns** with customer segmentation filters
2. **Preview messages** with sample AI-generated content
3. **Execute campaigns** to generate personalized messages for all recipients
4. **Monitor progress** and view generated messages

## Architecture

### Components

```
Campaign API
├── Models (SQLAlchemy)
│   ├── Campaign - Campaign metadata and status
│   └── CampaignRecipient - Individual recipients with messages
├── Schemas (Pydantic)
│   ├── CampaignCreate/Update/Response
│   ├── SegmentFilters - Customer filtering criteria
│   └── CampaignRecipient schemas
├── Services
│   ├── CampaignService - Campaign lifecycle management
│   ├── SegmentationService - Customer filtering
│   └── MessageGenerator - AI message generation
└── API Endpoints
    ├── POST /campaigns - Create campaign
    ├── GET /campaigns - List campaigns
    ├── GET /campaigns/{id} - Get campaign details
    ├── PUT /campaigns/{id} - Update draft campaign
    ├── POST /campaigns/{id}/preview - Generate sample messages
    ├── POST /campaigns/{id}/execute - Execute campaign
    ├── GET /campaigns/{id}/recipients - List recipients
    └── POST /campaigns/segment-count - Count audience
```

## Campaign Lifecycle

### States

```
draft → previewing → draft → executing → completed
         (temporary)         (or failed)
```

- **draft**: Campaign created, can be edited
- **previewing**: Temporarily set during preview generation
- **ready**: (Optional) Ready for execution
- **executing**: Messages being generated for all recipients
- **completed**: All messages generated successfully
- **failed**: Execution failed

### Typical Flow

1. **Create** campaign with segment filters
2. **Count** audience using segment-count endpoint
3. **Preview** with 3 sample messages to verify quality
4. **Execute** to generate all messages
5. **Monitor** progress via campaign details
6. **View** all generated messages via recipients endpoint

## API Endpoints

### 1. Create Campaign

**POST /api/v1/campaigns**

Create a new campaign in draft status.

**Request Body:**
```json
{
  "name": "Spring Menu Launch",
  "description": "Promote new seasonal dishes",
  "purpose": "Drive sales for spring menu items",
  "segment_filters": {
    "total_orders_min": 5,
    "favorite_cuisine": "italian",
    "city": "London"
  }
}
```

**Response (201):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Spring Menu Launch",
  "description": "Promote new seasonal dishes",
  "purpose": "Drive sales for spring menu items",
  "status": "draft",
  "segment_filters": { ... },
  "total_recipients": 0,
  "generated_count": 0,
  "created_at": "2024-02-10T12:00:00Z",
  "updated_at": "2024-02-10T12:00:00Z"
}
```

### 2. List Campaigns

**GET /api/v1/campaigns?page=1&page_size=25**

List all campaigns with pagination.

**Response (200):**
```json
{
  "items": [
    {
      "id": "...",
      "name": "Spring Menu Launch",
      "status": "completed",
      "total_recipients": 150,
      "generated_count": 148,
      ...
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 25,
  "pages": 2
}
```

### 3. Get Campaign Details

**GET /api/v1/campaigns/{id}**

Get full campaign details including progress.

**Response (200):**
```json
{
  "id": "...",
  "name": "Spring Menu Launch",
  "status": "executing",
  "total_recipients": 150,
  "generated_count": 75,
  ...
}
```

Use this endpoint to poll execution progress: `generated_count / total_recipients`.

### 4. Update Campaign

**PUT /api/v1/campaigns/{id}**

Update a draft campaign. Only draft campaigns can be updated.

**Request Body:**
```json
{
  "name": "Updated Campaign Name",
  "description": "New description",
  "segment_filters": {
    "total_orders_min": 10
  }
}
```

**Response (200):** Updated campaign

**Error (400):** If campaign is not in draft status

### 5. Preview Campaign

**POST /api/v1/campaigns/{id}/preview?brand_group_name=My%20Restaurants**

Generate sample AI messages for preview.

**Request Body:**
```json
{
  "sample_size": 3
}
```

**Query Parameters:**
- `brand_group_name` (optional): Brand name for message personalization (default: "Our Restaurant Group")

**Response (200):**
```json
{
  "campaign_id": "...",
  "estimated_audience_size": 150,
  "sample_messages": [
    {
      "id": "...",
      "customer_id": "...",
      "customer_email": "john@example.com",
      "customer_name": "John Doe",
      "generated_message": {
        "subject": "John, try our new spring pasta!",
        "body": "Hi John! We noticed you love Italian cuisine...",
        "recommendations": ["Pasta Primavera", "Tiramisu"],
        "model_used": "anthropic/claude-3.5-sonnet"
      },
      "status": "generated",
      "created_at": "2024-02-10T12:00:00Z"
    },
    ...
  ]
}
```

**Timing:** Typically completes in 10-15 seconds for 3 messages.

### 6. Execute Campaign

**POST /api/v1/campaigns/{id}/execute?brand_group_name=My%20Restaurants**

Execute campaign by generating messages for all recipients.

**Query Parameters:**
- `brand_group_name` (optional): Brand name for message personalization

**Response (200):**
```json
{
  "campaign_id": "...",
  "status": "completed",
  "total_recipients": 150,
  "message": "Campaign execution completed. Generated 148 messages."
}
```

**Performance:**
- MVP: Synchronous execution (blocks until complete)
- ~2-5 seconds per message
- 500 recipients ≈ 10-25 minutes

**Error Handling:**
- Message generation failures are captured per-recipient
- Campaign completes even if some messages fail
- Check recipient status for individual failures

### 7. Get Recipients

**GET /api/v1/campaigns/{id}/recipients?page=1&page_size=25**

List campaign recipients with their generated messages.

**Response (200):**
```json
{
  "items": [
    {
      "id": "...",
      "campaign_id": "...",
      "customer_id": "...",
      "customer_email": "jane@example.com",
      "customer_name": "Jane Smith",
      "generated_message": {
        "subject": "Jane, discover our spring menu!",
        "body": "Hi Jane! Based on your love for fresh salads...",
        "recommendations": ["Spring Salad", "Grilled Salmon"],
        "model_used": "anthropic/claude-3.5-sonnet"
      },
      "status": "generated",
      "error_message": null,
      "created_at": "2024-02-10T12:05:00Z"
    },
    {
      "id": "...",
      "status": "failed",
      "error_message": "Cannot generate message: No recommendations available",
      ...
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 25,
  "pages": 6
}
```

### 8. Count Segment

**POST /api/v1/campaigns/segment-count**

Count customers matching segment filters (for audience size preview).

**Request Body:**
```json
{
  "filters": {
    "total_orders_min": 5,
    "favorite_cuisine": "italian",
    "city": "London"
  }
}
```

**Response (200):**
```json
{
  "count": 150,
  "filters": { ... }
}
```

**Performance:** <200ms for MVP scale

## Segment Filters

### Available Filters

All filters combine with AND logic.

| Filter | Type | Description |
|--------|------|-------------|
| `last_order_after` | datetime | Customers who ordered after this date |
| `last_order_before` | datetime | Customers who ordered before this date |
| `total_spend_min` | float | Minimum total spend (£) |
| `total_spend_max` | float | Maximum total spend (£) |
| `total_orders_min` | int | Minimum number of orders |
| `favorite_cuisine` | string | Favorite cuisine from preferences |
| `dietary_flag` | string | Dietary flag: vegetarian, vegan, halal, gluten_free |
| `city` | string | Customer city (case-insensitive partial match) |
| `order_frequency` | string | Order frequency: daily, weekly, monthly, occasional |
| `brand_id` | UUID | Customers who ordered from this brand |

### Examples

**High-value Italian lovers in London:**
```json
{
  "total_spend_min": 100.0,
  "favorite_cuisine": "italian",
  "city": "London"
}
```

**Vegetarian weekly orderers:**
```json
{
  "dietary_flag": "vegetarian",
  "order_frequency": "weekly"
}
```

**Lapsed customers (no order in 90 days):**
```json
{
  "last_order_before": "2023-11-10T00:00:00Z"
}
```

## Message Generation

### How It Works

1. **Fetch customer data**: Order history, preferences, recommendations
2. **Build context**: Last order summary, favorite cuisines, personalized recommendations
3. **Call LLM**: OpenRouter API with structured JSON output
4. **Validate**: Ensure subject ≤60 chars, body ≤150 words
5. **Store**: Save to `campaign_recipients.generated_message`

### Message Structure

```json
{
  "subject": "John, try our new Italian dishes!",
  "body": "Hi John! We noticed you love Italian cuisine and recently enjoyed our Pasta Carbonara. We've just launched a fresh spring menu with amazing new pasta dishes and desserts. Come try our Pasta Primavera and Tiramisu - we think you'll love them!",
  "recommendations": ["Pasta Primavera", "Tiramisu"],
  "model_used": "anthropic/claude-3.5-sonnet"
}
```

### Quality Guidelines

Messages automatically:
- Use customer's first name (or "there" if missing)
- Mention specific dish names from recommendations
- Reflect customer's taste preferences
- Follow brand voice (set via `brand_group_name`)
- Meet length constraints (60 char subject, 150 word body)

## Error Handling

### Campaign-Level Errors

**404 - Campaign Not Found**
```json
{
  "detail": "Campaign 123... not found"
}
```

**400 - Invalid State**
```json
{
  "detail": "Cannot execute campaign in status 'completed'"
}
```

**400 - No Matching Customers**
```json
{
  "detail": "No customers match campaign filters"
}
```

### Recipient-Level Errors

Message generation failures are captured per-recipient, not campaign-wide:

```json
{
  "status": "failed",
  "error_message": "Cannot generate message: No recommendations available for customer ..."
}
```

Common failure reasons:
- Customer has no order history
- No recommendations available (no taste profile)
- LLM API error (retried 3 times)

## Performance Considerations

### MVP Scale (500 recipients)

- **Preview (3 messages):** 10-15 seconds
- **Execution (500 messages):** 10-25 minutes (synchronous)
- **Segment count:** <200ms

### Optimization Strategies (Post-MVP)

1. **Async Execution**: Use Celery/Redis for background processing
2. **Batch LLM Calls**: Send multiple prompts in parallel
3. **Caching**: Cache recommendations, preferences during execution
4. **Rate Limiting**: Respect OpenRouter rate limits

## Testing

### Unit Tests

```bash
pytest tests/services/test_campaign_service.py -v
pytest tests/services/test_segmentation_service.py -v
```

### Integration Tests

```bash
pytest tests/api/test_campaigns.py -v
```

### Manual Testing

```bash
# 1. Create campaign
curl -X POST http://localhost:8000/api/v1/campaigns \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "segment_filters": {"total_orders_min": 1}}'

# 2. Count audience
curl -X POST http://localhost:8000/api/v1/campaigns/segment-count \
  -H "Content-Type: application/json" \
  -d '{"filters": {"total_orders_min": 1}}'

# 3. Preview
curl -X POST http://localhost:8000/api/v1/campaigns/{id}/preview \
  -H "Content-Type: application/json" \
  -d '{"sample_size": 2}'

# 4. Execute
curl -X POST http://localhost:8000/api/v1/campaigns/{id}/execute

# 5. View recipients
curl http://localhost:8000/api/v1/campaigns/{id}/recipients
```

## Database Schema

### campaigns table

```sql
CREATE TABLE campaigns (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  purpose TEXT,  -- Used in message generation prompt
  status VARCHAR(50) NOT NULL DEFAULT 'draft',
  segment_filters JSONB,  -- SegmentFilters as JSON
  total_recipients INT DEFAULT 0,
  generated_count INT DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
```

### campaign_recipients table

```sql
CREATE TABLE campaign_recipients (
  id UUID PRIMARY KEY,
  campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
  customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
  generated_message JSONB,  -- {subject, body, recommendations, model_used}
  status VARCHAR(50) NOT NULL DEFAULT 'pending',
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
```

## Migration

Apply the migration to create campaign tables:

```bash
cd backend
alembic upgrade head
```

This runs migration `002_add_campaigns_tables.py`.

## Next Steps (Post-MVP)

1. **Email Sending**: Integrate email provider (Resend) - TASK-023
2. **Async Execution**: Use Celery for background processing
3. **Scheduling**: Schedule campaigns for future execution
4. **A/B Testing**: Multiple message variants per campaign
5. **Analytics**: Open rates, click rates, conversion tracking
6. **Templates**: Reusable message templates
7. **Multi-brand**: Support campaigns across multiple brands

## Related Documentation

- [Message Generator Guide](MESSAGE_GENERATOR_GUIDE.md) - AI message generation
- [OpenRouter Client Guide](OPENROUTER_CLIENT_GUIDE.md) - LLM API client
- [Recommendation Engine Guide](RECOMMENDATION_ENGINE_GUIDE.md) - Personalized recommendations
- [Preference Engine Guide](PREFERENCE_ENGINE_GUIDE.md) - Customer preference computation

## Support

For issues or questions:
- Check test files for usage examples
- Review service code for implementation details
- See tasks.md for original requirements (TASK-015)
