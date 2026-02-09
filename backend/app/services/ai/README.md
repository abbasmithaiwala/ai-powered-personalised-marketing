# AI Services

This module provides interfaces to Large Language Model (LLM) APIs for AI-powered features.

## Components

### OpenRouter Client

Production-ready async client for OpenRouter API (OpenAI-compatible endpoint).

**Features:**
- ✅ Automatic retry with exponential backoff
- ✅ Rate limit handling
- ✅ Request timeout (30s default)
- ✅ JSON mode for structured output
- ✅ Async context manager
- ✅ Custom error types

**Quick Start:**

```python
from app.services.ai import OpenRouterClient

async with OpenRouterClient() as client:
    response = await client.complete(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
        ]
    )
    print(response)
```

**Configuration:**

Set in `.env`:
```bash
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

**Documentation:** See `OPENROUTER_CLIENT_GUIDE.md` for full details.

**Tests:**
```bash
pytest tests/test_openrouter*.py -v
```

## Usage Examples

### Basic Completion

```python
response = await client.complete(
    messages=[{"role": "user", "content": "What's 2+2?"}],
    temperature=0.7,
    max_tokens=100,
)
```

### JSON Mode (Structured Output)

```python
response = await client.complete(
    messages=[
        {
            "role": "system",
            "content": "Return JSON with format: {answer: string, confidence: number}"
        },
        {"role": "user", "content": "Is this product review positive?"},
    ],
    response_format={"type": "json_object"},
)

import json
data = json.loads(response)
```

### Error Handling

```python
from app.services.ai.openrouter_client import (
    OpenRouterAPIKeyError,
    OpenRouterRateLimitError,
    OpenRouterError,
)

try:
    response = await client.complete(messages=messages)
except OpenRouterAPIKeyError:
    # Handle missing/invalid API key
    pass
except OpenRouterRateLimitError:
    # Handle rate limit
    pass
except OpenRouterError as e:
    # Handle other API errors
    pass
```

## Next Steps

This client is used by:
- **TASK-014**: Personalized message generator
- **TASK-015**: Campaign execution (message generation for recipients)

## Resources

- OpenRouter Docs: https://openrouter.ai/docs
- Get API Key: https://openrouter.ai/keys
- Model List: https://openrouter.ai/models
