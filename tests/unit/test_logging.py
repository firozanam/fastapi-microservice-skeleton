"""
Unit tests for logging module.
Tests logging processors, configuration, and logger retrieval.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.core.logging import (
    add_app_context,
    configure_logging,
    drop_color_message_key,
    get_logger,
    logger,
)


@pytest.mark.unit
class TestAddAppContext:
    """Test add_app_context processor."""

    def test_add_app_context(self):
        """Test that add_app_context adds app context."""
        with patch("app.core.logging.settings") as mock_settings:
            mock_settings.APP_NAME = "test-app"
            mock_settings.APP_ENV = "test-env"
            mock_settings.APP_VERSION = "1.0.0"

            event_dict = {}
            result = add_app_context(None, "test", event_dict)

            assert result == event_dict
            assert result["app"] == "test-app"
            assert result["environment"] == "test-env"
            assert result["version"] == "1.0.0"


@pytest.mark.unit
class TestDropColorMessageKey:
    """Test drop_color_message_key processor."""

    def test_drop_color_message_key(self):
        """Test that drop_color_message_key removes color_message key."""
        event_dict = {"color_message": "test", "other": "value"}

        result = drop_color_message_key(None, "test", event_dict)

        assert "color_message" not in result
        assert result["other"] == "value"


@pytest.mark.unit
class TestConfigureLogging:
    """Test configure_logging function."""

    @patch("app.core.logging.Path")
    def test_configure_logging_creates_log_directory(self, mock_path):
        """Test that configure_logging creates log directory."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent = MagicMock()
        mock_path_instance.parent.mkdir = MagicMock()

        with patch("app.core.logging.settings") as mock_settings:
            mock_settings.LOG_FILE_PATH = "./logs/app.log"

            configure_logging()

            mock_path_instance.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("app.core.logging.Path")
    def test_configure_logging_sets_up_standard_logging(self, mock_path):
        """Test that configure_logging sets up standard logging."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance

        with patch("app.core.logging.settings") as mock_settings:
            mock_settings.LOG_FILE_PATH = "./logs/app.log"
            mock_settings.LOG_LEVEL = "INFO"

            configure_logging()

            import logging
            logging.basicConfig.assert_called_once()
            assert logging.basicConfig.call_args[0][2] == "format"
            assert logging.basicConfig.call_args[0][4] == "%(message)s"
            assert logging.basicConfig.call_args[1][3] == sys.stdout
            assert logging.basicConfig.call_args[1][2] == getattr(logging, mock_settings.LOG_LEVEL)

    @patch("app.core.logging.Path")
    def test_configure_logging_json_format(self, mock_path):
        """Test configure_logging with JSON format."""
        import structlog
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance

        with patch("app.core.logging.settings") as mock_settings:
            mock_settings.LOG_FORMAT = "json"

            configure_logging()

            import structlog
            structlog.configure.assert_called_once()
            call_kwargs = structlog.configure.call_args[0]
            assert "JSONRenderer" in str(call_kwargs["processors"])

    @patch("app.core.logging.Path")
    def test_configure_logging_text_format(self, mock_path):
        """Test configure_logging with text format."""
        import structlog
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance

        with patch("app.core.logging.settings") as mock_settings:
            mock_settings.LOG_FORMAT = "text"

            configure_logging()

            import structlog
            structlog.configure.assert_called_once()
            call_kwargs = structlog.configure.call_args[0]
            assert "ConsoleRenderer" in str(call_kwargs["processors"])


@pytest.mark.unit
class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_with_name(self):
        """Test get_logger with custom name."""
        result = get_logger("test.module")

        assert result is not None
        assert hasattr(result, "info")
        assert hasattr(result, "error")
        assert hasattr(result, "warning")

    def test_get_logger_without_name(self):
        """Test get_logger without name uses __name__."""
        result = get_logger()

        assert result is not None
        assert hasattr(result, "info")
        assert hasattr(result, "error")


@pytest.mark.unit
class TestLoggerInitialization:
    """Test logger initialization on import."""

    def test_logger_is_initialized(self):
        """Test that logger is initialized on module import."""
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "warning")
