"""
Unit tests for logging middleware.
Tests request/response logging, process time tracking, and error handling.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, Response

from app.middleware.logging import LoggingMiddleware


@pytest.mark.unit
class TestLoggingMiddlewareInit:
    """Test LoggingMiddleware initialization."""

    def test_logging_middleware_init(self):
        """Test LoggingMiddleware initialization."""
        app = MagicMock()

        middleware = LoggingMiddleware(app)

        assert middleware.app == app


@pytest.mark.unit
class TestLoggingMiddlewareDispatch:
    """Test LoggingMiddleware dispatch method."""

    @pytest.mark.asyncio
    async def test_dispatch_logs_request(self):
        """Test that dispatch logs incoming request."""
        app = MagicMock()
        middleware = LoggingMiddleware(app)

        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url = "http://test.com/api/endpoint"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}
        mock_call_next = AsyncMock(return_value=MagicMock(spec=Response))

        with patch("app.middleware.logging.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            result = await middleware.dispatch(mock_request, mock_call_next)

            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args
            assert "method" in call_args[1]
            assert "path" in call_args[1]
            assert "client_host" in call_args[1]
            assert "user_agent" in call_args[1]

    @pytest.mark.asyncio
    async def test_dispatch_logs_response(self):
        """Test that dispatch logs response."""
        app = MagicMock()
        middleware = LoggingMiddleware(app)

        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url = "http://test.com/api/endpoint"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_call_next = AsyncMock(return_value=mock_response)

        with patch("app.middleware.logging.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            result = await middleware.dispatch(mock_request, mock_call_next)

            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args
            assert "status_code" in call_args[1]
            assert "process_time" in call_args[1]

    @pytest.mark.asyncio
    async def test_dispatch_adds_process_time_header(self):
        """Test that dispatch adds X-Process-Time header."""
        app = MagicMock()
        middleware = LoggingMiddleware(app)

        mock_request = MagicMock(spec=Request)
        mock_response = MagicMock(spec=Response)
        mock_response.headers = {}
        mock_call_next = AsyncMock(return_value=mock_response)

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert "X-Process-Time" in mock_response.headers
        assert isinstance(mock_response.headers["X-Process-Time"], str)

    @pytest.mark.asyncio
    async def test_dispatch_without_client(self):
        """Test dispatch when request has no client."""
        app = MagicMock()
        middleware = LoggingMiddleware(app)

        mock_request = MagicMock(spec=Request)
        mock_request.client = None
        mock_request.method = "GET"
        mock_request.url = "http://test.com/api/endpoint"
        mock_request.headers = {}
        mock_call_next = AsyncMock(return_value=MagicMock(spec=Response))

        with patch("app.middleware.logging.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            result = await middleware.dispatch(mock_request, mock_call_next)

            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args
            assert "client_host" in call_args[1]
            assert call_args[1]["client_host"] == "unknown"

    @pytest.mark.asyncio
    async def test_dispatch_without_user_agent(self):
        """Test dispatch when request has no user-agent header."""
        app = MagicMock()
        middleware = LoggingMiddleware(app)

        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url = "http://test.com/api/endpoint"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}
        mock_call_next = AsyncMock(return_value=MagicMock(spec=Response))

        with patch("app.middleware.logging.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            result = await middleware.dispatch(mock_request, mock_call_next)

            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args
            assert "user_agent" in call_args[1]
            assert call_args[1]["user_agent"] == "unknown"

    @pytest.mark.asyncio
    async def test_dispatch_with_exception(self):
        """Test dispatch with exception."""
        app = MagicMock()
        middleware = LoggingMiddleware(app)

        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url = "http://test.com/api/endpoint"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}
        mock_call_next = AsyncMock(side_effect=Exception("Request failed"))

        with patch("app.middleware.logging.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            with pytest.raises(Exception, match="Request failed"):
                await middleware.dispatch(mock_request, mock_call_next)

            mock_logger.error.assert_called()
            call_args = mock_logger.error.call_args
            assert "error" in call_args[1]
            assert "process_time" in call_args[1]

    @pytest.mark.asyncio
    async def test_dispatch_with_long_process_time(self):
        """Test dispatch with long process time."""
        app = MagicMock()
        middleware = LoggingMiddleware(app)

        mock_request = MagicMock(spec=Request)
        mock_response = MagicMock(spec=Response)
        mock_response.headers = {}
        mock_call_next = AsyncMock(return_value=mock_response)

        with patch("app.middleware.logging.time") as mock_time, \
             patch("app.middleware.logging.get_logger") as mock_get_logger:
            mock_time.time.side_effect = [1.0, 2.5]
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            result = await middleware.dispatch(mock_request, mock_call_next)

            assert "X-Process-Time" in mock_response.headers
            process_time = float(mock_response.headers["X-Process-Time"])
            assert process_time == pytest.approx(1.5, rel=0.1)

    @pytest.mark.asyncio
    async def test_dispatch_with_unicode_url(self):
        """Test dispatch with unicode characters in URL."""
        app = MagicMock()
        middleware = LoggingMiddleware(app)

        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url = "http://test.com/api/endpoint?param=测试"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}
        mock_call_next = AsyncMock(return_value=MagicMock(spec=Response))

        with patch("app.middleware.logging.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            result = await middleware.dispatch(mock_request, mock_call_next)

            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args
            assert "path" in call_args[1]
            assert "测试" in call_args[1]["path"]
