"""Tests for debug flag behavior and environment variable processing."""

import io
import logging
import os

import pytest

from mcp_server_tree_sitter.bootstrap import update_log_levels
from mcp_server_tree_sitter.bootstrap.logging_bootstrap import get_log_level_from_env


def test_debug_flag_with_preexisting_env() -> None:
    """Test that debug flag works correctly with pre-existing environment variables.

    This test simulates the real-world scenario where the logging is configured
    at import time, but the debug flag is processed later. In this case, the
    debug flag should still trigger a reconfiguration of logging levels.
    """
    # Save original environment and logger state
    original_env = os.environ.get("MCP_TS_LOG_LEVEL")

    # Get the root package logger
    pkg_logger = logging.getLogger("mcp_server_tree_sitter")
    original_level = pkg_logger.level

    # Create a clean test environment
    if "MCP_TS_LOG_LEVEL" in os.environ:
        del os.environ["MCP_TS_LOG_LEVEL"]

    # Set logger level to INFO explicitly
    pkg_logger.setLevel(logging.INFO)

    # Create a test handler to verify levels change
    test_handler = logging.StreamHandler()
    test_handler.setLevel(logging.INFO)
    pkg_logger.addHandler(test_handler)

    try:
        # Simulate the debug flag processing
        # First verify we're starting at INFO level
        assert pkg_logger.level == logging.INFO, "Logger should start at INFO level"
        assert test_handler.level == logging.INFO, "Handler should start at INFO level"

        # Now process the debug flag (this is what happens in main())
        os.environ["MCP_TS_LOG_LEVEL"] = "DEBUG"
        update_log_levels("DEBUG")

        # Verify the change was applied
        assert pkg_logger.level == logging.DEBUG, "Logger level should be changed to DEBUG"
        assert test_handler.level == logging.DEBUG, "Handler level should be changed to DEBUG"

        # Verify that new loggers created after updating will inherit the correct level
        new_logger = logging.getLogger("mcp_server_tree_sitter.test.new_module")
        assert new_logger.getEffectiveLevel() == logging.DEBUG, "New loggers should inherit DEBUG level"

    finally:
        # Cleanup
        pkg_logger.removeHandler(test_handler)

        # Restore original environment
        if original_env is not None:
            os.environ["MCP_TS_LOG_LEVEL"] = original_env
        else:
            if "MCP_TS_LOG_LEVEL" in os.environ:
                del os.environ["MCP_TS_LOG_LEVEL"]

        # Restore logger state
        pkg_logger.setLevel(original_level)


def test_update_log_levels_reconfigures_root_logger() -> None:
    """Test that update_log_levels also updates the root logger.

    This tests the enhanced implementation that reconfigures the root
    logger in addition to the package logger, which helps with debug
    flag handling when a module is already imported.
    """
    # Save original logger states
    root_logger = logging.getLogger()
    pkg_logger = logging.getLogger("mcp_server_tree_sitter")
    original_root_level = root_logger.level
    original_pkg_level = pkg_logger.level

    # Create handlers for testing
    root_handler = logging.StreamHandler()
    root_handler.setLevel(logging.INFO)
    root_logger.addHandler(root_handler)

    pkg_handler = logging.StreamHandler()
    pkg_handler.setLevel(logging.INFO)
    pkg_logger.addHandler(pkg_handler)

    try:
        # Set loggers to INFO level
        root_logger.setLevel(logging.INFO)
        pkg_logger.setLevel(logging.INFO)

        # Verify initial levels
        assert root_logger.level == logging.INFO, "Root logger should start at INFO level"
        assert pkg_logger.level == logging.INFO, "Package logger should start at INFO level"
        assert root_handler.level == logging.INFO, "Root handler should start at INFO level"
        assert pkg_handler.level == logging.INFO, "Package handler should start at INFO level"

        # Call update_log_levels with DEBUG
        update_log_levels("DEBUG")

        # Verify all loggers and handlers are updated
        assert root_logger.level == logging.DEBUG, "Root logger should be updated to DEBUG level"
        assert pkg_logger.level == logging.DEBUG, "Package logger should be updated to DEBUG level"
        assert root_handler.level == logging.DEBUG, "Root handler should be updated to DEBUG level"
        assert pkg_handler.level == logging.DEBUG, "Package handler should be updated to DEBUG level"

        # Test with a new child logger
        child_logger = logging.getLogger("mcp_server_tree_sitter.test.child")
        assert child_logger.getEffectiveLevel() == logging.DEBUG, "Child logger should inherit DEBUG level from parent"

    finally:
        # Clean up
        root_logger.removeHandler(root_handler)
        pkg_logger.removeHandler(pkg_handler)

        # Restore original levels
        root_logger.setLevel(original_root_level)
        pkg_logger.setLevel(original_pkg_level)


def test_environment_variable_updates_log_level() -> None:
    """Test that setting MCP_TS_LOG_LEVEL changes the logging level correctly."""
    # Save original environment and logger state
    original_env = os.environ.get("MCP_TS_LOG_LEVEL")

    # Get the root package logger
    pkg_logger = logging.getLogger("mcp_server_tree_sitter")
    original_level = pkg_logger.level

    try:
        # First test with DEBUG level
        os.environ["MCP_TS_LOG_LEVEL"] = "DEBUG"

        # Verify the get_log_level_from_env function returns DEBUG
        level = get_log_level_from_env()
        assert level == logging.DEBUG, f"Expected DEBUG level but got {level}"

        # Update log levels and verify the logger is set to DEBUG
        update_log_levels("DEBUG")
        assert pkg_logger.level == logging.DEBUG, f"Logger level should be DEBUG but was {pkg_logger.level}"

        # Check handler levels are synchronized
        for handler in pkg_logger.handlers:
            assert handler.level == logging.DEBUG, f"Handler level should be DEBUG but was {handler.level}"

        # Next test with INFO level
        os.environ["MCP_TS_LOG_LEVEL"] = "INFO"

        # Verify the get_log_level_from_env function returns INFO
        level = get_log_level_from_env()
        assert level == logging.INFO, f"Expected INFO level but got {level}"

        # Update log levels and verify the logger is set to INFO
        update_log_levels("INFO")
        assert pkg_logger.level == logging.INFO, f"Logger level should be INFO but was {pkg_logger.level}"

        # Check handler levels are synchronized
        for handler in pkg_logger.handlers:
            assert handler.level == logging.INFO, f"Handler level should be INFO but was {handler.level}"

    finally:
        # Restore original environment
        if original_env is not None:
            os.environ["MCP_TS_LOG_LEVEL"] = original_env
        else:
            if "MCP_TS_LOG_LEVEL" in os.environ:
                del os.environ["MCP_TS_LOG_LEVEL"]

        # Restore logger state
        pkg_logger.setLevel(original_level)


def test_configure_root_logger_syncs_handlers() -> None:
    """Test that configure_root_logger synchronizes handler levels for existing loggers."""
    from mcp_server_tree_sitter.bootstrap.logging_bootstrap import configure_root_logger

    # Save original environment and logger state
    original_env = os.environ.get("MCP_TS_LOG_LEVEL")

    # Create a test logger in the package hierarchy
    test_logger = logging.getLogger("mcp_server_tree_sitter.test.debug_flag")
    original_test_level = test_logger.level

    # Get the root package logger
    pkg_logger = logging.getLogger("mcp_server_tree_sitter")
    original_pkg_level = pkg_logger.level

    # Create handlers with different levels
    debug_handler = logging.StreamHandler()
    debug_handler.setLevel(logging.DEBUG)

    info_handler = logging.StreamHandler()
    info_handler.setLevel(logging.INFO)

    # Add handlers to the test logger
    test_logger.addHandler(debug_handler)
    test_logger.addHandler(info_handler)

    try:
        # Set environment variable to DEBUG
        os.environ["MCP_TS_LOG_LEVEL"] = "DEBUG"

        # Call configure_root_logger
        configure_root_logger()

        # Verify the root package logger is set to DEBUG
        assert pkg_logger.level == logging.DEBUG, (
            f"Root package logger level should be DEBUG but was {pkg_logger.level}"
        )

        # Verify child logger still has its original level (should not be explicitly set)
        assert test_logger.level == original_test_level, (
            "Child logger level should not be changed by configure_root_logger"
        )

        # Verify child logger's effective level is inherited from root package logger
        assert test_logger.getEffectiveLevel() == logging.DEBUG, (
            f"Child logger effective level should be DEBUG but was {test_logger.getEffectiveLevel()}"
        )

        # Verify all handlers of the test logger are synchronized to DEBUG
        for handler in test_logger.handlers:
            assert handler.level == logging.DEBUG, f"Handler level should be DEBUG but was {handler.level}"

    finally:
        # Clean up
        test_logger.removeHandler(debug_handler)
        test_logger.removeHandler(info_handler)

        # Restore original environment
        if original_env is not None:
            os.environ["MCP_TS_LOG_LEVEL"] = original_env
        else:
            if "MCP_TS_LOG_LEVEL" in os.environ:
                del os.environ["MCP_TS_LOG_LEVEL"]

        # Restore logger state
        test_logger.setLevel(original_test_level)
        pkg_logger.setLevel(original_pkg_level)


def test_log_message_levels() -> None:
    """Test that log messages about environment variables use the DEBUG level."""
    # Save original environment state
    original_env = {}
    for key in list(os.environ.keys()):
        if key.startswith("MCP_TS_"):
            original_env[key] = os.environ[key]
            del os.environ[key]

    try:
        # Test variable for configuration
        os.environ["MCP_TS_CACHE_MAX_SIZE_MB"] = "256"

        # Create a StringIO to capture log output
        log_output = io.StringIO()

        # Create a handler that writes to our StringIO
        handler = logging.StreamHandler(log_output)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
        handler.setFormatter(formatter)

        # Add the handler to the root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)

        # Save the original log level
        original_level = root_logger.level

        # Set the log level to DEBUG to capture all messages
        root_logger.setLevel(logging.DEBUG)

        try:
            # Import config to trigger environment variable processing
            from mcp_server_tree_sitter.config import ServerConfig

            # Create a new config instance to trigger environment variable processing
            # Variable is intentionally used to trigger processing
            _ = ServerConfig()

            # Get the output
            log_content = log_output.getvalue()

            # Check for environment variable application messages
            env_messages = [line for line in log_content.splitlines() if "Applied environment variable" in line]

            # Verify that these messages use DEBUG level, not INFO
            for msg in env_messages:
                assert msg.startswith("DEBUG:"), f"Environment variable message should use DEBUG level but found: {msg}"

            # Check if there are any environment variable messages at INFO level
            info_env_messages = [
                line
                for line in log_content.splitlines()
                if "Applied environment variable" in line and line.startswith("INFO:")
            ]

            assert not info_env_messages, (
                f"No environment variable messages should use INFO level, but found: {info_env_messages}"
            )

        finally:
            # Restore original log level
            root_logger.setLevel(original_level)

            # Remove our handler
            root_logger.removeHandler(handler)

    finally:
        # Restore original environment
        for key in list(os.environ.keys()):
            if key.startswith("MCP_TS_"):
                del os.environ[key]

        for key, value in original_env.items():
            os.environ[key] = value


if __name__ == "__main__":
    pytest.main(["-v", __file__])
