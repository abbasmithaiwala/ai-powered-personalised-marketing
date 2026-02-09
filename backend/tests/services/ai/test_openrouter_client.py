"""Unit tests for OpenRouter API client."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from app.services.ai.openrouter_client import (
    OpenRouterClient,
    OpenRouterError,
    OpenRouterAPIKeyError,
    OpenRouterRateLimitError,
    OpenRouterServerError,
)


@pytest.fixture
def mock_client():
    """Create a mock HTTP client."""
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def openrouter_client():
    """Create OpenRouter client with test API key."""
    return OpenRouterClient(
        api_key="test-api-key",
        model="test-model",
        base_url="https://test.openrouter.ai/api/v1",
        max_retries=3,
        timeout=30.0,
    )


class TestOpenRouterClientInit:
    """Test client initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default settings from config."""
        with patch("app.services.ai.openrouter_client.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "default-key"
            mock_settings.OPENROUTER_MODEL = "default-model"
            mock_settings.OPENROUTER_BASE_URL = "https://default.url"

            client = OpenRouterClient()

            assert client.api_key == "default-key"
            assert client.model == "default-model"
            assert client.base_url == "https://default.url"

    def test_init_with_overrides(self):
        """Test initialization with explicit parameters."""
        client = OpenRouterClient(
            api_key="custom-key",
            model="custom-model",
            base_url="https://custom.url/",
            max_retries=5,
            timeout=60.0,
        )

        assert client.api_key == "custom-key"
        assert client.model == "custom-model"
        assert client.base_url == "https://custom.url"  # trailing slash stripped
        assert client.max_retries == 5
        assert client.timeout == 60.0

    def test_init_without_api_key_warns(self, caplog):
        """Test that missing API key logs a warning."""
        with patch("app.services.ai.openrouter_client.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = ""
            mock_settings.OPENROUTER_MODEL = "test-model"
            mock_settings.OPENROUTER_BASE_URL = "https://test.url"

            OpenRouterClient()

            assert "OPENROUTER_API_KEY is not set" in caplog.text


class TestOpenRouterClientComplete:
    """Test completion generation."""

    @pytest.mark.asyncio
    async def test_complete_success(self, openrouter_client):
        """Test successful completion request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Generated response"}}],
            "model": "test-model",
            "usage": {"total_tokens": 100},
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        openrouter_client._client = mock_client

        result = await openrouter_client.complete(
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7,
            max_tokens=1024,
        )

        assert result == "Generated response"
        mock_client.post.assert_called_once()

        # Verify payload structure
        call_args = mock_client.post.call_args
        payload = call_args.kwargs["json"]
        assert payload["model"] == "test-model"
        assert payload["messages"] == [{"role": "user", "content": "Hello"}]
        assert payload["temperature"] == 0.7
        assert payload["max_tokens"] == 1024

    @pytest.mark.asyncio
    async def test_complete_with_json_format(self, openrouter_client):
        """Test completion with JSON response format."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"key": "value"}'}}],
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        openrouter_client._client = mock_client

        result = await openrouter_client.complete(
            messages=[{"role": "user", "content": "Generate JSON"}],
            response_format={"type": "json_object"},
        )

        assert result == '{"key": "value"}'

        # Verify response_format was included
        call_args = mock_client.post.call_args
        payload = call_args.kwargs["json"]
        assert payload["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_complete_with_model_override(self, openrouter_client):
        """Test completion with model override."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        openrouter_client._client = mock_client

        await openrouter_client.complete(
            messages=[{"role": "user", "content": "Test"}],
            model="different-model",
        )

        # Verify model override
        call_args = mock_client.post.call_args
        payload = call_args.kwargs["json"]
        assert payload["model"] == "different-model"

    @pytest.mark.asyncio
    async def test_complete_empty_messages_raises(self, openrouter_client):
        """Test that empty messages list raises ValueError."""
        with pytest.raises(ValueError, match="messages list cannot be empty"):
            await openrouter_client.complete(messages=[])

    @pytest.mark.asyncio
    async def test_complete_without_api_key_raises(self):
        """Test that missing API key raises error at call time."""
        client = OpenRouterClient(api_key="")

        with pytest.raises(OpenRouterAPIKeyError, match="OPENROUTER_API_KEY is not set"):
            await client.complete(messages=[{"role": "user", "content": "Test"}])


class TestOpenRouterClientRetry:
    """Test retry logic."""

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self, openrouter_client):
        """Test retry on 429 rate limit error."""
        # First two attempts fail with 429, third succeeds
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "1"}
        mock_response_429.text = "Rate limit exceeded"

        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {
            "choices": [{"message": {"content": "Success after retry"}}],
        }

        mock_client = AsyncMock()
        mock_client.post.side_effect = [
            mock_response_429,
            mock_response_429,
            mock_response_200,
        ]

        openrouter_client._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await openrouter_client.complete(
                messages=[{"role": "user", "content": "Test"}]
            )

            assert result == "Success after retry"
            assert mock_client.post.call_count == 3
            assert mock_sleep.call_count == 2  # Slept twice before success

    @pytest.mark.asyncio
    async def test_retry_on_server_error(self, openrouter_client):
        """Test retry on 5xx server errors."""
        mock_response_500 = Mock()
        mock_response_500.status_code = 500
        mock_response_500.text = "Internal server error"

        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {
            "choices": [{"message": {"content": "Success"}}],
        }

        mock_client = AsyncMock()
        mock_client.post.side_effect = [mock_response_500, mock_response_200]

        openrouter_client._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await openrouter_client.complete(
                messages=[{"role": "user", "content": "Test"}]
            )

            assert result == "Success"
            assert mock_client.post.call_count == 2
            mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_exhausted_rate_limit(self, openrouter_client):
        """Test that rate limit error is raised after exhausting retries."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "1"}
        mock_response.text = "Rate limit exceeded"

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        openrouter_client._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(OpenRouterRateLimitError, match="Rate limit exceeded"):
                await openrouter_client.complete(
                    messages=[{"role": "user", "content": "Test"}]
                )

            assert mock_client.post.call_count == 3  # max_retries

    @pytest.mark.asyncio
    async def test_retry_exhausted_server_error(self, openrouter_client):
        """Test that server error is raised after exhausting retries."""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.text = "Service unavailable"

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        openrouter_client._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(OpenRouterServerError, match="Server error 503"):
                await openrouter_client.complete(
                    messages=[{"role": "user", "content": "Test"}]
                )

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, openrouter_client):
        """Test retry on timeout errors."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = [
            httpx.TimeoutException("Request timeout"),
            Mock(
                status_code=200,
                json=lambda: {"choices": [{"message": {"content": "Success"}}]},
            ),
        ]

        openrouter_client._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await openrouter_client.complete(
                messages=[{"role": "user", "content": "Test"}]
            )

            assert result == "Success"
            assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_exponential_backoff(self, openrouter_client):
        """Test exponential backoff timing."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Error"

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        openrouter_client._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with pytest.raises(OpenRouterServerError):
                await openrouter_client.complete(
                    messages=[{"role": "user", "content": "Test"}]
                )

            # Verify exponential backoff: 1s, 2s, 4s (2^0, 2^1, 2^2)
            sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
            assert sleep_calls == [1, 2, 4]


class TestOpenRouterClientErrors:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_client_error_4xx_no_retry(self, openrouter_client):
        """Test that 4xx errors (except 429) are not retried."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_response.json.return_value = {
            "error": {"message": "Invalid parameters"}
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        openrouter_client._client = mock_client

        with pytest.raises(OpenRouterError, match="Invalid parameters"):
            await openrouter_client.complete(
                messages=[{"role": "user", "content": "Test"}]
            )

        # Should only try once, no retries
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_response_error(self, openrouter_client):
        """Test error when API returns empty content."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": ""}}],
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        openrouter_client._client = mock_client

        with pytest.raises(OpenRouterError, match="Empty response from API"):
            await openrouter_client.complete(
                messages=[{"role": "user", "content": "Test"}]
            )

    @pytest.mark.asyncio
    async def test_malformed_response_error(self, openrouter_client):
        """Test error when API returns malformed JSON."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Missing expected structure

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        openrouter_client._client = mock_client

        with pytest.raises(OpenRouterError, match="Empty response from API"):
            await openrouter_client.complete(
                messages=[{"role": "user", "content": "Test"}]
            )


class TestOpenRouterClientLifecycle:
    """Test client lifecycle management."""

    @pytest.mark.asyncio
    async def test_client_creation_on_first_use(self, openrouter_client):
        """Test that HTTP client is created lazily."""
        assert openrouter_client._client is None

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
        }

        with patch("httpx.AsyncClient", return_value=AsyncMock()) as mock_client_cls:
            mock_client_instance = mock_client_cls.return_value
            mock_client_instance.post.return_value = mock_response

            await openrouter_client.complete(
                messages=[{"role": "user", "content": "Test"}]
            )

            # Client should be created
            assert openrouter_client._client is not None
            mock_client_cls.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_client(self, openrouter_client):
        """Test that client can be closed."""
        mock_client = AsyncMock()
        openrouter_client._client = mock_client

        await openrouter_client.close()

        mock_client.aclose.assert_called_once()
        assert openrouter_client._client is None

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager usage."""
        client = OpenRouterClient(api_key="test-key")
        mock_client = AsyncMock()

        async with client:
            client._client = mock_client
            assert client._client is not None

        # Client should be closed after context exit
        mock_client.aclose.assert_called_once()
        assert client._client is None
