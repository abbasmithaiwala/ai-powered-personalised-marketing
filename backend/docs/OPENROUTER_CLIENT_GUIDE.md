# OpenRouter API Client Guide

## Overview

The OpenRouter API client provides a production-ready interface to OpenRouter's LLM API. It handles authentication, retries, error handling, and supports structured JSON output.

## Features

- ✅ **Automatic Retries**: Retries on rate limits (429) and server errors (5xx)
- ✅ **Exponential Backoff**: 1s → 2s → 4s for failed requests
- ✅ **Request Timeout**: 30 second default timeout
- ✅ **Structured Output**: Supports JSON mode for structured data
- ✅ **Model Flexibility**: Can override model per request
- ✅ **Async Context Manager**: Proper resource cleanup
- ✅ **Type Safety**: Full type hints and Pydantic models

## Configuration

### Environment Variables

Set these in your `.env` file:

```bash
OPENROUTER_API_KEY=sk-or-v1-...       # Required: Your OpenRouter API key
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet  # Optional: Default model
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1  # Optional: API base URL
```

Get your API key from: https://openrouter.ai/keys

### Supported Models

Popular models available via OpenRouter:

- `anthropic/claude-3.5-sonnet` (default, recommended)
- `anthropic/claude-3-opus`
- `anthropic/claude-3-haiku`
- `openai/gpt-4-turbo`
- `openai/gpt-4`
- `openai/gpt-3.5-turbo`
- `meta-llama/llama-3.1-70b-instruct`

See full list: https://openrouter.ai/models

## Basic Usage

### Simple Completion

```python
from app.services.ai.openrouter_client import OpenRouterClient

# Create client (uses config from settings)
client = OpenRouterClient()

# Generate completion
response = await client.complete(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
    ],
    temperature=0.7,
    max_tokens=1024,
)

print(response)  # "The capital of France is Paris."
```

### Using Context Manager (Recommended)

```python
async with OpenRouterClient() as client:
    response = await client.complete(
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response)
# Client automatically closed after context
```

### JSON Mode for Structured Output

```python
# Request JSON response
response = await client.complete(
    messages=[
        {
            "role": "system",
            "content": "Extract sentiment and keywords. Return JSON with format: {sentiment: string, confidence: number, keywords: string[]}"
        },
        {
            "role": "user",
            "content": "This product is amazing! Great quality and fast shipping."
        },
    ],
    response_format={"type": "json_object"},
    temperature=0.3,  # Lower temp for more consistent structure
)

import json
result = json.loads(response)
print(result["sentiment"])  # "positive"
print(result["confidence"])  # 0.95
print(result["keywords"])  # ["amazing", "great", "fast"]
```

## Advanced Usage

### Model Override

```python
# Override default model per request
response = await client.complete(
    messages=[{"role": "user", "content": "Write a poem"}],
    model="anthropic/claude-3-opus",  # Use more capable model
    temperature=1.2,  # Higher temp for creativity
)
```

### Multi-Turn Conversation

```python
conversation = [
    {"role": "system", "content": "You are a helpful customer service agent."},
    {"role": "user", "content": "I want to return my order"},
]

response1 = await client.complete(messages=conversation)
conversation.append({"role": "assistant", "content": response1})

conversation.append({"role": "user", "content": "It's order #12345"})
response2 = await client.complete(messages=conversation)
```

### Custom Configuration

```python
# Override default settings
client = OpenRouterClient(
    api_key="custom-key",
    model="openai/gpt-4",
    base_url="https://custom.url",
    max_retries=5,
    timeout=60.0,
)
```

## Error Handling

The client raises specific exceptions for different error types:

```python
from app.services.ai.openrouter_client import (
    OpenRouterAPIKeyError,
    OpenRouterRateLimitError,
    OpenRouterServerError,
    OpenRouterError,
)

try:
    response = await client.complete(
        messages=[{"role": "user", "content": "Hello"}]
    )
except OpenRouterAPIKeyError:
    # Missing or invalid API key
    print("Please set OPENROUTER_API_KEY in your .env file")
except OpenRouterRateLimitError:
    # Rate limit exceeded after all retries
    print("Rate limit hit. Try again later.")
except OpenRouterServerError:
    # Server error persisted after retries
    print("OpenRouter service unavailable. Try again later.")
except OpenRouterError as e:
    # Other API errors (4xx client errors)
    print(f"API error: {e}")
```

## Retry Behavior

The client automatically retries on:

1. **Rate Limits (429)**: Retries with `Retry-After` header or exponential backoff
2. **Server Errors (5xx)**: Retries with exponential backoff (1s, 2s, 4s)
3. **Timeouts/Connection Errors**: Retries with exponential backoff

No retries on:
- Client errors (400, 401, 403, 404, etc.) - these indicate invalid requests
- Empty/malformed responses - these won't resolve with retries

## Best Practices

### 1. Use Context Manager

Always use the context manager to ensure proper cleanup:

```python
async with OpenRouterClient() as client:
    response = await client.complete(messages=messages)
```

### 2. Set Appropriate Temperature

- **Factual tasks**: `temperature=0.3` (consistent, focused)
- **Balanced**: `temperature=0.7` (default, good mix)
- **Creative tasks**: `temperature=1.2+` (diverse, unpredictable)

### 3. Use JSON Mode for Structured Data

When you need structured output, use `response_format`:

```python
response = await client.complete(
    messages=[...],
    response_format={"type": "json_object"},
    temperature=0.3,  # Lower temp for consistency
)
```

### 4. Handle Errors Gracefully

Always wrap LLM calls in try-except:

```python
try:
    response = await client.complete(messages=messages)
except OpenRouterError as e:
    # Fallback behavior
    logger.error(f"LLM call failed: {e}")
    response = generate_fallback_response()
```

### 5. Reuse Client Instance

Create one client instance and reuse it for multiple requests:

```python
# Good: Reuse client
client = OpenRouterClient()
for user in users:
    response = await client.complete(messages=build_messages(user))
await client.close()

# Bad: Create new client each time
for user in users:
    async with OpenRouterClient() as client:  # Wasteful
        response = await client.complete(messages=build_messages(user))
```

### 6. Set Reasonable max_tokens

Estimate needed tokens to avoid truncation:

- Short responses (tweet-length): `max_tokens=100`
- Email/message: `max_tokens=500`
- Article/blog post: `max_tokens=2000`
- Long-form content: `max_tokens=4000+`

## Testing

The client is fully tested with mocked HTTP calls:

```bash
# Run all tests
pytest tests/test_openrouter*.py -v

# Run specific test class
pytest tests/test_openrouter_client.py::TestOpenRouterClientRetry -v
```

## Performance

- **Typical latency**: 1-5 seconds (depends on model and prompt length)
- **Timeout**: 30 seconds (configurable)
- **Max retries**: 3 (configurable)
- **Total max time**: ~45 seconds (timeout + retries + backoff)

## Security

- ✅ API key stored in environment variables (never hardcoded)
- ✅ Sent via Authorization header (not in URL)
- ✅ HTTPS only (enforced by httpx)
- ✅ No sensitive data logged

## Troubleshooting

### "OPENROUTER_API_KEY is not set"

Set your API key in `.env`:
```bash
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### Rate limit errors

OpenRouter has rate limits based on your plan. The client automatically retries, but if you hit sustained rate limits:

1. Reduce request frequency
2. Upgrade your OpenRouter plan
3. Use a faster model (Haiku vs Sonnet)

### Timeout errors

If requests timeout consistently:

1. Reduce `max_tokens` (less generation time)
2. Increase `timeout` parameter
3. Use a faster model

### Empty responses

If you get "Empty response from API":

1. Check your prompt formatting
2. Verify model is available
3. Try a different model

## Next Steps

Now that you have the OpenRouter client, you can implement:

- **TASK-014**: Personalized message generator
- **TASK-015**: Campaign API with AI-generated messages

See `tasks.md` for full task breakdown.
