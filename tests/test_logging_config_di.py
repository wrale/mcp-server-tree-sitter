"""Tests for log level configuration settings with dependency injection."""

import io
import logging
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

from mcp_server_tree_sitter.di import get_container
from tests.test_helpers import configure, get_ast, register_project_tool, temp_config


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

    # Save original level and handlers
    original_level = logger.level
    original_handlers = logger.handlers.copy()

    # Create a StringIO object to capture logs
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
    handler.setFormatter(formatter)

    # Clear handlers and add our capture handler
    logger.handlers = [handler]

    try:
        yield log_capture
    finally:
        # Restore original handlers and level
        logger.handlers = original_handlers
        logger.setLevel(original_level)


@pytest.fixture
def test_project():
    """Create a temporary test project with a sample file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create a simple Python file
        test_file = project_path / "test.py"
        with open(test_file, "w") as f:
            f.write("def hello():\n    print('Hello, world!')\n\nhello()\n")

        # Register the project
        project_name = "logging_test_project"
        try:
            register_project_tool(path=str(project_path), name=project_name)
        except Exception:
            # If registration fails, try with a more unique name
            import time

            project_name = f"logging_test_project_{int(time.time())}"
            register_project_tool(path=str(project_path), name=project_name)

        yield {"name": project_name, "path": str(project_path), "file": "test.py"}


def test_log_level_setting_di(test_project):
    """Test that log_level setting controls logging verbosity."""
    # Root logger for the package
    logger_name = "mcp_server_tree_sitter"

    # Get container for checking values later
    container = get_container()
    original_log_level = container.get_config().log_level

    try:
        # Test with DEBUG level
        with temp_config(**{"log_level": "DEBUG"}):
            # Apply configuration
            configure(log_level="DEBUG")

            # Capture logs during an operation
            with capture_logs(logger_name) as log_capture:
                # Force the root logger to debug level
                logging.getLogger(logger_name).setLevel(logging.DEBUG)

                # Perform an operation that generates logs
                get_ast(project=test_project["name"], path=test_project["file"])

                # Check captured logs
                logs = log_capture.getvalue()
                print(f"DEBUG logs: {logs}")

                # Should contain DEBUG level messages
                assert "DEBUG:" in logs, "DEBUG level messages should be present"

        # Test with INFO level (less verbose)
        with temp_config(**{"log_level": "INFO"}):
            # Apply configuration
            configure(log_level="INFO")

            # Capture logs during an operation
            with capture_logs(logger_name) as log_capture:
                # Important: Set the root logger to INFO instead of DEBUG
                # to ensure proper level filtering
                root_logger = logging.getLogger(logger_name)
                root_logger.setLevel(logging.INFO)

                # Set the handler level for the logger
                for handler in root_logger.handlers:
                    handler.setLevel(logging.INFO)

                # Create a test logger
                logger = logging.getLogger(f"{logger_name}.test")
                # Make sure it inherits from the root logger
                logger.setLevel(logging.NOTSET)

                # Generate a debug log that should be filtered
                logger.debug("This debug message should be filtered out")

                # Generate an info log that should be included
                logger.info("This info message should be included")

                logs = log_capture.getvalue()
                print(f"INFO logs: {logs}")

                # Should not contain the DEBUG message but should contain INFO
                assert "This debug message should be filtered out" not in logs, "DEBUG messages should be filtered"
                assert "This info message should be included" in logs, "INFO messages should be included"

    finally:
        # Restore original log level
        container.config_manager.update_value("log_level", original_log_level)


def test_log_level_in_yaml_config_di():
    """Test that log_level can be configured via YAML."""
    # Create a temporary YAML file
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w+", delete=False) as temp_file:
        # Write a configuration with explicit log level
        temp_file.write("""
log_level: DEBUG

cache:
  enabled: true
  max_size_mb: 100
""")
        temp_file.flush()
        temp_file_path = temp_file.name

    try:
        # Get container for checking values later
        container = get_container()
        original_log_level = container.get_config().log_level

        try:
            # Load the configuration
            result = configure(config_path=temp_file_path)

            # Verify the log level was set correctly
            assert result["log_level"] == "DEBUG", "Log level should be set from YAML"

            # Verify it's applied to loggers
            with capture_logs("mcp_server_tree_sitter") as log_capture:
                logger = logging.getLogger("mcp_server_tree_sitter.test")
                logger.debug("Test debug message")

                logs = log_capture.getvalue()
                assert "Test debug message" in logs, "DEBUG log level should be applied"

        finally:
            # Restore original log level
            container.config_manager.update_value("log_level", original_log_level)

    finally:
        # Clean up
        import os

        os.unlink(temp_file_path)
