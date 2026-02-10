# Message Generator Service

Production-ready AI-powered personalized message generation for marketing campaigns.

## Overview

The Message Generator orchestrates customer data, menu recommendations, and LLM calls to create personalized marketing messages. It integrates with the OpenRouter API client and recommendation engine to generate contextual, constraint-compliant messages.

## Features

- ✅ **Personalized Context**: Combines customer data, order history, and AI recommendations
- ✅ **LLM Integration**: Uses OpenRouter API for message generation with JSON mode
- ✅ **Strict Validation**: Enforces 60-char subject limit and 150-word body limit
- ✅ **Human-Readable**: Natural language time formatting ("7 days ago", "2 weeks ago")
- ✅ **Error Handling**: Custom exceptions for customer not found, insufficient data, generation failures
- ✅ **Async/Await**: Non-blocking async operations with proper context management

## Architecture

```
MessageGenerator
├── _get_customer()           # Fetch customer from database
├── _get_recommendations()    # Get personalized menu recommendations
├── _get_last_order_summary() # Build human-readable order summary
├── _parse_llm_response()     # Validate and parse LLM JSON output
└── generate_message()        # Main orchestrator
```

## Usage

### Basic Message Generation

```python
from app.services.ai import MessageGenerator
from app.schemas.message import MessageGenerationRequest

async with get_db() as db:
    generator = MessageGenerator(db)

    request = MessageGenerationRequest(
        customer_id=customer.id,
        campaign_purpose="Weekend special - New Italian menu",
        brand_group_name="Pizza Palace",
        offer="20% off your next order",
        recommendation_limit=5,
    )

    response = await generator.generate_message(request)

    print(response.message.subject)  # "John, try our new Italian dishes!"
    print(response.message.body)     # Personalized message text
    print(response.recommendations_used)  # ["Quattro Formaggi Pizza", ...]
```

### Error Handling

```python
from app.services.ai.message_generator import (
    CustomerNotFoundError,
    InsufficientDataError,
    MessageGenerationException,
)
from app.services.ai.openrouter_client import OpenRouterAPIKeyError

try:
    response = await generator.generate_message(request)
except CustomerNotFoundError:
    # Handle customer not found (404)
    pass
except InsufficientDataError:
    # Handle no recommendations available
    pass
except OpenRouterAPIKeyError:
    # Handle missing API key
    pass
except MessageGenerationException as e:
    # Handle other generation errors
    logger.error(f"Message generation failed: {e}")
```

## Schemas

### Request Schema

```python
class MessageGenerationRequest(BaseModel):
    customer_id: UUID
    campaign_purpose: str           # 5-200 chars, e.g., "New menu launch"
    brand_group_name: str           # 2-100 chars
    offer: str | None               # Optional, max 200 chars
    recommendation_limit: int = 5   # 1-10 recommendations
```

### Response Schema

```python
class MessageGenerationResponse(BaseModel):
    customer_id: UUID
    message: GeneratedMessage       # {subject, body}
    recommendations_used: List[str] # Dish names used in generation
    model_used: str                 # LLM model identifier
```

### Generated Message Schema

```python
class GeneratedMessage(BaseModel):
    subject: str        # Max 60 characters
    body: str           # Max 150 words (auto-validated)
```

## Prompt System

### System Prompt

The system prompt defines the AI's role and strict output rules:

```python
MARKETING_MESSAGE_SYSTEM_PROMPT = """You are a marketing copywriter for {brand_group_name}.

**STRICT RULES:**
- Maximum 150 words for body
- Maximum 60 characters for subject line
- Mention specific dishes by their EXACT name
- Use customer's first name (NEVER "Dear Customer")
- Write in friendly, conversational tone

**OUTPUT FORMAT:**
You MUST output ONLY valid JSON:
{
    "subject": "subject line (max 60 chars)",
    "body": "message body (max 150 words)"
}
"""
```

### User Prompt

Contextual information sent to the LLM:

```python
Customer first name: John
Last order summary: Ordered 7 days ago: Margherita Pizza, Caesar Salad, Tiramisu
Recommended dishes:
- Quattro Formaggi Pizza
- Penne Arrabbiata
- Caprese Salad
Campaign purpose: Weekend special - New Italian menu items
Special offer: 20% off your next order
```

## Implementation Details

### Last Order Summary Formatting

Human-readable time formatting for natural language:

```python
# Today
"Ordered today: Margherita Pizza, Caesar Salad"

# Recent (< 7 days)
"Ordered 3 days ago: Margherita Pizza"

# Weeks (7-29 days)
"Ordered 2 weeks ago: Caesar Salad, Tiramisu"

# Months (30+ days)
"Ordered 2 months ago: Quattro Formaggi Pizza"

# No orders
"This customer hasn't ordered yet"
```

### Database Queries

```python
# Fetch customer with error handling
customer = await db.execute(
    select(Customer).where(Customer.id == customer_id)
)

# Get last order with items (eager loading)
last_order = await db.execute(
    select(Order)
    .where(Order.customer_id == customer_id)
    .options(selectinload(Order.order_items))  # Note: order_items, not items!
    .order_by(Order.order_date.desc())
    .limit(1)
)
```

### LLM Call with JSON Mode

```python
async with OpenRouterClient() as client:
    response_text = await client.complete(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=512,
        response_format={"type": "json_object"},  # Ensures JSON output
    )

    # Parse and validate JSON response
    message = GeneratedMessage(**json.loads(response_text))
```

## Testing

### Unit Tests (17 tests)

- Customer fetching (success, not found)
- Recommendation fetching (success, empty, engine error)
- Last order summary (with orders, no orders)
- LLM response parsing (valid JSON, invalid JSON, constraint violations)
- Full message generation (success, customer not found, no recommendations, API errors)

### Integration Tests (6 tests)

- Database integration (real customer fetch, order summary)
- Full flow with mocked LLM (message generation with real DB + mocked OpenRouter)
- Error scenarios (no recommendations)

```bash
# Run all tests
pytest tests/services/ai/test_message_generator*.py -v

# All 23 tests passing (17 unit + 6 integration)
```

## Performance

- **Message Generation**: <5 seconds (including LLM call)
- **Database Queries**: <100ms (with eager loading)
- **LLM Latency**: ~2-4 seconds (depends on OpenRouter API)
- **Validation**: <1ms (Pydantic validation)

## Dependencies

- `OpenRouterClient`: LLM API calls with retry logic
- `RecommendationEngine`: Personalized menu recommendations
- `SQLAlchemy`: Async database queries
- `Pydantic`: Request/response validation

## Common Pitfalls

1. **Order Relationship**: Use `Order.order_items`, not `Order.items`
2. **Mock Recommendations**: Use `RecommendationItem` objects, not dicts
3. **JSON Validation**: LLM must return valid JSON (use `response_format={"type": "json_object"}`)
4. **Word Count**: Validate body word count, not character count (150 words max)
5. **Customer Name**: Handle missing `first_name` (default to "there")

## Next Steps

This service is used by:
- **TASK-015**: Campaign API (bulk message generation for campaigns)
- **TASK-023**: Email sending integration (future)

## Resources

- OpenRouter Docs: https://openrouter.ai/docs
- Task Specification: See `tasks.md` TASK-014
- Memory: See `~/.claude/projects/.../memory/MEMORY.md`
