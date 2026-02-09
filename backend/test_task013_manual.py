#!/usr/bin/env python3
"""
Manual test script for TASK-013: OpenRouter API Client

This script demonstrates how to use the OpenRouter client.
To run with real API calls, set OPENROUTER_API_KEY in .env

Usage:
    python test_task013_manual.py
"""
import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ai.openrouter_client import (
    OpenRouterClient,
    OpenRouterAPIKeyError,
    OpenRouterError,
)
from app.core.config import settings


async def test_basic_completion():
    """Test basic completion with simple prompt."""
    print("\n=== Test 1: Basic Completion ===")

    if not settings.OPENROUTER_API_KEY:
        print("⚠️  OPENROUTER_API_KEY not set. Skipping real API test.")
        print("   To test with real API, set OPENROUTER_API_KEY in .env")
        return

    try:
        async with OpenRouterClient() as client:
            response = await client.complete(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Keep responses brief."},
                    {"role": "user", "content": "What is 2+2?"},
                ],
                temperature=0.3,
                max_tokens=50,
            )

            print(f"✅ Response received:")
            print(f"   {response}")

    except OpenRouterAPIKeyError as e:
        print(f"❌ API Key Error: {e}")
    except OpenRouterError as e:
        print(f"❌ API Error: {e}")


async def test_json_mode():
    """Test JSON mode for structured output."""
    print("\n=== Test 2: JSON Mode (Structured Output) ===")

    if not settings.OPENROUTER_API_KEY:
        print("⚠️  OPENROUTER_API_KEY not set. Skipping real API test.")
        return

    try:
        async with OpenRouterClient() as client:
            response = await client.complete(
                messages=[
                    {
                        "role": "system",
                        "content": "Extract sentiment from text. Return JSON with format: {sentiment: string, confidence: number, keywords: string[]}",
                    },
                    {
                        "role": "user",
                        "content": "This restaurant has amazing food! The pasta is incredible and service is excellent.",
                    },
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=200,
            )

            print(f"✅ Structured JSON received:")
            parsed = json.loads(response)
            print(f"   Sentiment: {parsed.get('sentiment')}")
            print(f"   Confidence: {parsed.get('confidence')}")
            print(f"   Keywords: {parsed.get('keywords')}")

    except json.JSONDecodeError:
        print(f"❌ Failed to parse JSON response: {response}")
    except OpenRouterError as e:
        print(f"❌ API Error: {e}")


async def test_different_models():
    """Test using different models."""
    print("\n=== Test 3: Different Models ===")

    if not settings.OPENROUTER_API_KEY:
        print("⚠️  OPENROUTER_API_KEY not set. Skipping real API test.")
        return

    models = [
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-haiku",
    ]

    for model in models:
        try:
            async with OpenRouterClient(model=model) as client:
                response = await client.complete(
                    messages=[
                        {"role": "user", "content": "Say 'Hello!' in one word."},
                    ],
                    max_tokens=10,
                )

                print(f"✅ {model}: {response}")

        except OpenRouterError as e:
            print(f"❌ {model} failed: {e}")


async def test_conversation():
    """Test multi-turn conversation."""
    print("\n=== Test 4: Multi-Turn Conversation ===")

    if not settings.OPENROUTER_API_KEY:
        print("⚠️  OPENROUTER_API_KEY not set. Skipping real API test.")
        return

    try:
        async with OpenRouterClient() as client:
            conversation = [
                {"role": "system", "content": "You are a food recommendation assistant."},
                {"role": "user", "content": "I love spicy Thai food"},
            ]

            # Turn 1
            response1 = await client.complete(messages=conversation, max_tokens=100)
            print(f"Turn 1 (AI): {response1[:100]}...")

            conversation.append({"role": "assistant", "content": response1})
            conversation.append({"role": "user", "content": "What about vegetarian options?"})

            # Turn 2
            response2 = await client.complete(messages=conversation, max_tokens=100)
            print(f"Turn 2 (AI): {response2[:100]}...")

            print("✅ Multi-turn conversation completed")

    except OpenRouterError as e:
        print(f"❌ Conversation failed: {e}")


async def test_error_handling():
    """Test error handling without API key."""
    print("\n=== Test 5: Error Handling ===")

    # Test without API key
    client = OpenRouterClient(api_key="")

    try:
        await client.complete(
            messages=[{"role": "user", "content": "Test"}]
        )
        print("❌ Should have raised OpenRouterAPIKeyError")
    except OpenRouterAPIKeyError:
        print("✅ Correctly raised OpenRouterAPIKeyError for missing API key")

    # Test with empty messages
    client = OpenRouterClient(api_key="test-key")
    try:
        await client.complete(messages=[])
        print("❌ Should have raised ValueError")
    except ValueError as e:
        print(f"✅ Correctly raised ValueError for empty messages: {e}")


def print_config():
    """Print current configuration."""
    print("\n" + "=" * 60)
    print("OpenRouter Client Configuration")
    print("=" * 60)

    print(f"API Key: {'✅ Set' if settings.OPENROUTER_API_KEY else '❌ Not set'}")
    print(f"Model: {settings.OPENROUTER_MODEL}")
    print(f"Base URL: {settings.OPENROUTER_BASE_URL}")

    if not settings.OPENROUTER_API_KEY:
        print("\n⚠️  To run tests with real API calls:")
        print("   1. Get API key from https://openrouter.ai/keys")
        print("   2. Add to .env: OPENROUTER_API_KEY=sk-or-v1-...")
        print("   3. Run this script again")

    print("=" * 60)


async def main():
    """Run all tests."""
    print("TASK-013: OpenRouter API Client - Manual Test")

    print_config()

    # Run tests
    await test_basic_completion()
    await test_json_mode()
    await test_different_models()
    await test_conversation()
    await test_error_handling()

    print("\n" + "=" * 60)
    print("All manual tests completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("  - TASK-014: Personalized message generator")
    print("  - TASK-015: Campaign API")
    print("\nFor automated tests, run:")
    print("  pytest tests/test_openrouter*.py -v")


if __name__ == "__main__":
    asyncio.run(main())
