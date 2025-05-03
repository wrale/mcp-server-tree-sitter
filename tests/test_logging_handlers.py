"""Tests for handler level synchronization in logging configuration."""

import io
import logging
from contextlib import contextmanager

# Import from bootstrap module rather than logging_config
from mcp_server_tree_sitter.bootstrap import get_logger, update_log_levels


@contextmanager
def temp_logger(name="mcp_server_tree_sitter.test_handlers"):
    """Create a temporary logger for testing."""
    logger = logging.getLogger(name)

    # Save original settings
    original_level = logger.level
    original_handlers = logger.handlers.copy()
    original_propagate = logger.propagate

    # Create handlers with different levels for testing
    debug_handler = logging.StreamHandler()
    debug_handler.setLevel(logging.DEBUG)

    info_handler = logging.StreamHandler()
    info_handler.setLevel(logging.INFO)

    warning_handler = logging.StreamHandler()
    warning_handler.setLevel(logging.WARNING)

    # Add handlers and set initial level
    logger.handlers = [debug_handler, info_handler, warning_handler]
    logger.setLevel(logging.INFO)

    try:
        yield logger
    finally:
        # Restore original settings
        logger.handlers = original_handlers
        logger.setLevel(original_level)
        logger.propagate = original_propagate


def test_handler_level_synchronization():
    """Test that handler levels are synchronized with logger's effective level."""
    # Set up test environment
    root_logger = logging.getLogger("mcp_server_tree_sitter")
    original_root_level = root_logger.level
    original_root_handlers = root_logger.handlers.copy()

    # Create a non-root logger to test proper hierarchical behavior
    test_logger = logging.getLogger("mcp_server_tree_sitter.handlers_test")
    original_test_level = test_logger.level
    original_test_handlers = test_logger.handlers.copy()

    # Ensure test logger has no explicit level set (should inherit from root)
    test_logger.setLevel(logging.NOTSET)

    # Add handlers with different levels for testing
    debug_handler = logging.StreamHandler()
    debug_handler.setLevel(logging.DEBUG)

    info_handler = logging.StreamHandler()
    info_handler.setLevel(logging.INFO)

    warning_handler = logging.StreamHandler()
    warning_handler.setLevel(logging.WARNING)

    # Add handlers to the test logger
    test_logger.handlers = [debug_handler, info_handler, warning_handler]

    try:
        # Initial state verification
        assert test_logger.level == logging.NOTSET, "Test logger should not have explicit level"
        assert test_logger.getEffectiveLevel() == root_logger.level, "Effective level should be inherited from root"

        # Initial handler levels
        assert test_logger.handlers[0].level == logging.DEBUG
        assert test_logger.handlers[1].level == logging.INFO
        assert test_logger.handlers[2].level == logging.WARNING

        # Update root logger to DEBUG
        update_log_levels("DEBUG")

        # Child logger level should NOT be explicitly changed
        assert test_logger.level == logging.NOTSET, "Child logger level should NOT be explicitly set"

        # Effective level should now be DEBUG through inheritance
        assert test_logger.getEffectiveLevel() == logging.DEBUG, "Effective level should be DEBUG through inheritance"

        # All handlers should now be at DEBUG level (synchronized to effective level)
        assert test_logger.handlers[0].level == logging.DEBUG
        assert test_logger.handlers[1].level == logging.DEBUG
        assert test_logger.handlers[2].level == logging.DEBUG

        # Update root logger to WARNING
        update_log_levels("WARNING")

        # Child logger level should still not be explicitly changed
        assert test_logger.level == logging.NOTSET, "Child logger level should NOT be explicitly set"

        # Effective level should now be WARNING through inheritance
        assert test_logger.getEffectiveLevel() == logging.WARNING, (
            "Effective level should be WARNING through inheritance"
        )

        # All handlers should now be at WARNING level (synchronized to effective level)
        assert test_logger.handlers[0].level == logging.WARNING
        assert test_logger.handlers[1].level == logging.WARNING
        assert test_logger.handlers[2].level == logging.WARNING
    finally:
        # Restore original state
        root_logger.handlers = original_root_handlers
        root_logger.setLevel(original_root_level)
        test_logger.handlers = original_test_handlers
        test_logger.setLevel(original_test_level)


def test_get_logger_handler_sync():
    """Test that get_logger creates loggers with proper level inheritance and synchronized handler levels."""
    # Set up test environment
    root_logger = logging.getLogger("mcp_server_tree_sitter")
    original_root_level = root_logger.level

    # Create a child logger with our utility
    logger_name = "mcp_server_tree_sitter.test_get_logger"

    # First, ensure we start with a clean state
    existing_logger = logging.getLogger(logger_name)
    original_level = existing_logger.level
    original_handlers = existing_logger.handlers.copy()
    existing_logger.handlers = []
    existing_logger.setLevel(logging.NOTSET)  # Clear any explicit level

    try:
        # Get logger with utility function
        test_logger = get_logger(logger_name)

        # Child logger should NOT have an explicit level set
        assert test_logger.level == logging.NOTSET, "Child logger should not have explicit level set"

        # Child logger should inherit level from root package logger
        assert test_logger.getEffectiveLevel() == root_logger.level, "Child logger should inherit level from root"

        # Add a handler and manually set its level to match the logger's effective level
        handler = logging.StreamHandler()
        test_logger.addHandler(handler)
        # Manually set handler level after adding it
        handler.setLevel(test_logger.getEffectiveLevel())

        # Now verify that handler matches logger's effective level
        assert handler.level == test_logger.getEffectiveLevel(), "Handler should match logger's effective level"

        # Update log levels to DEBUG
        update_log_levels("DEBUG")

        # Child logger should still NOT have explicit level
        assert test_logger.level == logging.NOTSET, "Child logger should not have explicit level set after update"

        # Child logger should inherit DEBUG from root
        assert test_logger.getEffectiveLevel() == logging.DEBUG, "Child logger should inherit DEBUG from root"

        # Handler should be updated to match effective level
        assert handler.level == logging.DEBUG, "Handler should match logger's effective level (DEBUG)"

        # Update log levels to WARNING
        update_log_levels("WARNING")

        # Child logger should still NOT have explicit level
        assert test_logger.level == logging.NOTSET, (
            "Child logger should not have explicit level set after second update"
        )

        # Child logger should inherit WARNING from root
        assert test_logger.getEffectiveLevel() == logging.WARNING, "Child logger should inherit WARNING from root"

        # Handler should be updated to match effective level
        assert handler.level == logging.WARNING, "Handler should match logger's effective level (WARNING)"

        # Test root logger behavior
        root_test_logger = get_logger("mcp_server_tree_sitter")
        root_handler = logging.StreamHandler()
        root_test_logger.addHandler(root_handler)

        # Manually set the handler level to match the logger's level
        root_handler.setLevel(root_test_logger.level)

        # Root logger should have explicit level
        assert root_test_logger.level != logging.NOTSET, "Root logger should have explicit level set"

        # Handler should match root logger's level
        assert root_handler.level == root_test_logger.level, "Root logger handler should match logger level"
    finally:
        # Restore original state
        existing_logger.handlers = original_handlers
        existing_logger.setLevel(original_level)
        root_logger.setLevel(original_root_level)


def test_multiple_handlers_with_log_streams():
    """Test that multiple handlers all pass the appropriate log messages."""
    # Create handlers with capture buffers
    debug_capture = io.StringIO()
    debug_handler = logging.StreamHandler(debug_capture)
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(logging.Formatter("DEBUG_HANDLER:%(message)s"))

    info_capture = io.StringIO()
    info_handler = logging.StreamHandler(info_capture)
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(logging.Formatter("INFO_HANDLER:%(message)s"))

    # Create test logger
    logger_name = "mcp_server_tree_sitter.test_multiple"
    test_logger = logging.getLogger(logger_name)

    # Save original settings
    original_level = test_logger.level
    original_handlers = test_logger.handlers.copy()
    original_propagate = test_logger.propagate

    # Configure logger for test
    test_logger.handlers = [debug_handler, info_handler]
    test_logger.propagate = False

    try:
        # Initial state - set to INFO
        test_logger.setLevel(logging.INFO)

        # Log messages at different levels
        test_logger.debug("Debug message that should be filtered")
        test_logger.info("Info message that should appear")
        test_logger.warning("Warning message that should appear")

        # Check debug handler - should only have INFO and WARNING messages
        debug_logs = debug_capture.getvalue()
        assert "Debug message that should be filtered" not in debug_logs
        assert "Info message that should appear" in debug_logs
        assert "Warning message that should appear" in debug_logs

        # Check info handler - should only have INFO and WARNING messages
        info_logs = info_capture.getvalue()
        assert "Debug message that should be filtered" not in info_logs
        assert "Info message that should appear" in info_logs
        assert "Warning message that should appear" in info_logs

        # Now update log levels to DEBUG and explicitly set handler levels
        test_logger.setLevel(logging.DEBUG)
        # Important: Explicitly update the handler levels after changing the logger level
        debug_handler.setLevel(logging.DEBUG)
        info_handler.setLevel(logging.DEBUG)

        # Clear previous captures
        debug_capture.truncate(0)
        debug_capture.seek(0)
        info_capture.truncate(0)
        info_capture.seek(0)

        # Log messages again
        test_logger.debug("Debug message that should now appear")
        test_logger.info("Info message that should appear")

        # Check debug handler - should have both messages
        debug_logs = debug_capture.getvalue()
        assert "Debug message that should now appear" in debug_logs
        assert "Info message that should appear" in debug_logs

        # Check info handler - should now also have both messages
        # because we explicitly set the handler levels to DEBUG
        info_logs = info_capture.getvalue()
        assert "Debug message that should now appear" in info_logs
        assert "Info message that should appear" in info_logs

    finally:
        # Restore original settings
        test_logger.handlers = original_handlers
        test_logger.setLevel(original_level)
        test_logger.propagate = original_propagate
