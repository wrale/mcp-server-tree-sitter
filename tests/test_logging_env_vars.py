"""Tests for environment variable-based logging configuration."""

import io
import logging
import os
from contextlib import contextmanager
from unittest.mock import patch

# Import from bootstrap module rather than logging_config
from mcp_server_tree_sitter.bootstrap import get_log_level_from_env, update_log_levels


@contextmanager
def capture_logs(logger_name="mcp_server_tree_sitter"):
    """
    Context manager to capture logs from a specific logger.

    Args:
        logger_name: Name of the logger to capture

    Returns:
        StringIO object containing captured logs
    """
    # Get the logger
    logger = logging.getLogger(logger_name)

    # Save original level, handlers, and propagate value
    original_level = logger.level
    original_handlers = logger.handlers.copy()
    original_propagate = logger.propagate

    # Create a StringIO object to capture logs
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
    handler.setFormatter(formatter)

    # Clear handlers and add our capture handler
    logger.handlers = [handler]

    # Disable propagation to parent loggers to avoid duplicate messages
    logger.propagate = False

    try:
        yield log_capture
    finally:
        # Restore original handlers, level, and propagate setting
        logger.handlers = original_handlers
        logger.setLevel(original_level)
        logger.propagate = original_propagate


def test_get_log_level_from_env():
    """Test that log level is correctly retrieved from environment variables."""
    # Test with DEBUG level
    with patch.dict(os.environ, {"MCP_TS_LOG_LEVEL": "DEBUG"}):
        level = get_log_level_from_env()
        assert level == logging.DEBUG, "Should return DEBUG level from env var"

    # Test with INFO level
    with patch.dict(os.environ, {"MCP_TS_LOG_LEVEL": "INFO"}):
        level = get_log_level_from_env()
        assert level == logging.INFO, "Should return INFO level from env var"

    # Test with WARNING level
    with patch.dict(os.environ, {"MCP_TS_LOG_LEVEL": "WARNING"}):
        level = get_log_level_from_env()
        assert level == logging.WARNING, "Should return WARNING level from env var"

    # Test with invalid level (should default to INFO)
    with patch.dict(os.environ, {"MCP_TS_LOG_LEVEL": "INVALID_LEVEL"}):
        level = get_log_level_from_env()
        assert level == logging.INFO, "Should return default INFO level for invalid inputs"

    # Test with lowercase level name (should be case-insensitive)
    with patch.dict(os.environ, {"MCP_TS_LOG_LEVEL": "debug"}):
        level = get_log_level_from_env()
        assert level == logging.DEBUG, "Should handle lowercase level names"


def test_update_log_levels():
    """Test that update_log_levels correctly sets levels on root logger and handlers."""
    # Set up test environment
    root_logger = logging.getLogger("mcp_server_tree_sitter")
    original_root_level = root_logger.level
    original_root_handlers = root_logger.handlers.copy()

    # Create a child logger in our package hierarchy
    child_logger = logging.getLogger("mcp_server_tree_sitter.test")
    original_child_level = child_logger.level
    original_child_handlers = child_logger.handlers.copy()

    # Add handlers for testing
    root_handler = logging.StreamHandler()
    root_logger.addHandler(root_handler)

    child_handler = logging.StreamHandler()
    child_handler.setLevel(logging.ERROR)
    child_logger.addHandler(child_handler)

    try:
        # Update log levels to DEBUG
        update_log_levels("DEBUG")

        # Check root logger is updated
        assert root_logger.level == logging.DEBUG, "Root logger level should be updated"
        assert root_handler.level == logging.DEBUG, "Root logger handler level should be updated"

        # Child logger level should NOT be explicitly set (only handlers synchronized)
        # But effective level should be DEBUG through inheritance
        assert child_logger.level != logging.DEBUG, "Child logger level should NOT be explicitly set"
        assert child_logger.getEffectiveLevel() == logging.DEBUG, (
            "Child logger effective level should be DEBUG through inheritance"
        )

        # Child logger handlers should be synchronized to the effective level
        assert child_handler.level == logging.DEBUG, (
            "Child logger handler level should be synchronized to effective level"
        )

        # Test with numeric level value
        update_log_levels(logging.INFO)

        # Check levels again
        assert root_logger.level == logging.INFO, "Root logger level should be updated with numeric value"
        assert root_handler.level == logging.INFO, "Root logger handler level should be updated with numeric value"

        # Check inheritance again
        assert child_logger.level != logging.INFO, "Child logger level should NOT be explicitly set"
        assert child_logger.getEffectiveLevel() == logging.INFO, (
            "Child logger effective level should be INFO through inheritance"
        )
        assert child_handler.level == logging.INFO, (
            "Child logger handler level should be synchronized to effective level"
        )
    finally:
        # Restore original state
        root_logger.handlers = original_root_handlers
        root_logger.setLevel(original_root_level)
        child_logger.handlers = original_child_handlers
        child_logger.setLevel(original_child_level)


def test_env_var_affects_logging(monkeypatch):
    """Test that MCP_TS_LOG_LEVEL environment variable affects logging behavior."""
    # Set environment variable to DEBUG
    monkeypatch.setenv("MCP_TS_LOG_LEVEL", "DEBUG")

    # Import the module again to trigger initialization with the new env var
    with patch.dict(os.environ, {"MCP_TS_LOG_LEVEL": "DEBUG"}):
        # Force reloading of the module
        import importlib

        import mcp_server_tree_sitter.bootstrap.logging_bootstrap

        importlib.reload(mcp_server_tree_sitter.bootstrap.logging_bootstrap)

        # Get the root package logger to check its level was set from env var
        root_logger = logging.getLogger("mcp_server_tree_sitter")
        assert root_logger.level == logging.DEBUG, "Root logger level should be DEBUG from env var"

        # Get a child logger from our package
        from mcp_server_tree_sitter.bootstrap import get_logger

        test_logger = get_logger("mcp_server_tree_sitter.env_test")

        # Child logger should NOT have explicit level set
        assert test_logger.level == logging.NOTSET, "Child logger should not have explicit level set"

        # But its effective level should be inherited from root logger
        assert test_logger.getEffectiveLevel() == logging.DEBUG, "Child logger effective level should be DEBUG"

        # Capture logs
        with capture_logs("mcp_server_tree_sitter.env_test") as log_capture:
            # Send debug message
            test_logger.debug("This is a debug message that should appear")

            # Check that debug message appears in logs
            logs = log_capture.getvalue()
            assert "This is a debug message that should appear" in logs, (
                "DEBUG messages should be logged when env var is set"
            )

    # Set environment variable to INFO
    monkeypatch.setenv("MCP_TS_LOG_LEVEL", "INFO")

    # Import the module again with new env var
    with patch.dict(os.environ, {"MCP_TS_LOG_LEVEL": "INFO"}):
        # Force reloading of the module
        import importlib

        import mcp_server_tree_sitter.bootstrap.logging_bootstrap

        importlib.reload(mcp_server_tree_sitter.bootstrap.logging_bootstrap)

        # Get the root package logger to check its level was set from env var
        root_logger = logging.getLogger("mcp_server_tree_sitter")
        assert root_logger.level == logging.INFO, "Root logger level should be INFO from env var"

        # Get a child logger
        from mcp_server_tree_sitter.bootstrap import get_logger

        test_logger = get_logger("mcp_server_tree_sitter.env_test")

        # Child logger should NOT have explicit level set
        assert test_logger.level == logging.NOTSET, "Child logger should not have explicit level set"

        # But its effective level should be inherited from root logger
        assert test_logger.getEffectiveLevel() == logging.INFO, "Child logger effective level should be INFO"

        # Capture logs
        with capture_logs("mcp_server_tree_sitter.env_test") as log_capture:
            # Send debug message that should be filtered
            test_logger.debug("This debug message should be filtered out")

            # Send info message that should appear
            test_logger.info("This info message should appear")

            # Check logs
            logs = log_capture.getvalue()
            assert "This debug message should be filtered out" not in logs, (
                "DEBUG messages should be filtered when env var is INFO"
            )
            assert "This info message should appear" in logs, "INFO messages should be logged when env var is INFO"

        # Verify propagation is enabled
        child_logger = logging.getLogger("mcp_server_tree_sitter.env_test.deep")
        assert child_logger.propagate, "Logger propagation should be enabled"
