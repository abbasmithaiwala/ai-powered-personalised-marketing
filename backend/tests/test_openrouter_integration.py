"""
Integration tests for OpenRouter client.

These tests verify the client behavior with more realistic scenarios,
but still use mocks to avoid making real API calls.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from app.services.ai.openrouter_client import OpenRouterClient


class TestOpenRouterIntegration:
    """Integration tests with realistic scenarios."""

    @pytest.mark.asyncio
    async def test_simple_conversation(self):
        """Test a simple conversation flow."""
        client = OpenRouterClient(
            api_key="test-key",
            model="anthropic/claude-3.5-sonnet",
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Hello! I'm Claude, an AI assistant. How can I help you today?"
                    }
                }
            ],
            "model": "anthropic/claude-3.5-sonnet",
            "usage": {"total_tokens": 25, "prompt_tokens": 10, "completion_tokens": 15},
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        client._client = mock_client

        result = await client.complete(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"},
            ],
            temperature=0.7,
            max_tokens=100,
        )

        assert "Claude" in result
        assert "help" in result

    @pytest.mark.asyncio
    async def test_json_mode_for_structured_output(self):
        """Test JSON mode for structured data extraction."""
        client = OpenRouterClient(api_key="test-key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"sentiment": "positive", "confidence": 0.95, "keywords": ["great", "excellent", "amazing"]}'
                    }
                }
            ],
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        client._client = mock_client

        result = await client.complete(
            messages=[
                {
                    "role": "system",
                    "content": "You analyze sentiment and return JSON with format: {sentiment, confidence, keywords}",
                },
                {"role": "user", "content": "This product is great! Excellent quality and amazing value."},
            ],
            response_format={"type": "json_object"},
        )

        assert "positive" in result
        assert "confidence" in result
        assert "keywords" in result

    @pytest.mark.asyncio
    async def test_context_manager_usage(self):
        """Test using the client as an async context manager."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            async with OpenRouterClient(api_key="test-key") as client:
                result = await client.complete(
                    messages=[{"role": "user", "content": "Test"}]
                )
                assert result == "Response"

            # Verify client was closed
            mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_completions_reuse_client(self):
        """Test that multiple completions reuse the same HTTP client."""
        client = OpenRouterClient(api_key="test-key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        client._client = mock_client

        # Make multiple requests
        await client.complete(messages=[{"role": "user", "content": "First"}])
        await client.complete(messages=[{"role": "user", "content": "Second"}])
        await client.complete(messages=[{"role": "user", "content": "Third"}])

        # Should reuse same client
        assert mock_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_realistic_retry_scenario(self):
        """Test a realistic scenario with transient failures."""
        client = OpenRouterClient(api_key="test-key")

        # Simulate: timeout -> rate limit -> success
        timeout_exception = httpx.TimeoutException("Request timeout")

        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "1"}
        rate_limit_response.text = "Rate limit"

        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Success after retries"}}],
        }

        mock_client = AsyncMock()
        mock_client.post.side_effect = [
            timeout_exception,
            rate_limit_response,
            success_response,
        ]
        client._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await client.complete(
                messages=[{"role": "user", "content": "Test"}]
            )

            assert result == "Success after retries"
            assert mock_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_temperature_and_max_tokens_respected(self):
        """Test that temperature and max_tokens parameters are sent correctly."""
        client = OpenRouterClient(api_key="test-key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Creative response"}}],
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        client._client = mock_client

        await client.complete(
            messages=[{"role": "user", "content": "Write something creative"}],
            temperature=1.5,
            max_tokens=2048,
        )

        # Verify parameters were sent
        call_kwargs = mock_client.post.call_args.kwargs
        payload = call_kwargs["json"]
        assert payload["temperature"] == 1.5
        assert payload["max_tokens"] == 2048

    @pytest.mark.asyncio
    async def test_different_models(self):
        """Test using different models."""
        # Test with different model at client level
        client1 = OpenRouterClient(
            api_key="test-key",
            model="anthropic/claude-3-opus",
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        client1._client = mock_client

        await client1.complete(messages=[{"role": "user", "content": "Test"}])

        payload1 = mock_client.post.call_args.kwargs["json"]
        assert payload1["model"] == "anthropic/claude-3-opus"

        # Test with model override at request level
        client2 = OpenRouterClient(
            api_key="test-key",
            model="anthropic/claude-3.5-sonnet",
        )
        client2._client = mock_client

        await client2.complete(
            messages=[{"role": "user", "content": "Test"}],
            model="openai/gpt-4",
        )

        payload2 = mock_client.post.call_args.kwargs["json"]
        assert payload2["model"] == "openai/gpt-4"
