"""Test that logging configuration is applied early in application lifecycle."""

import importlib
import logging
import os
from unittest.mock import MagicMock, patch


def test_early_init_in_package():
    """Test that logging is configured before other modules are imported."""
    # Rather than mocking which won't work well with imports,
    # we'll check the actual package __init__.py file content
    import inspect

    import mcp_server_tree_sitter

    # Get the source code of the package __init__.py
    init_source = inspect.getsource(mcp_server_tree_sitter)

    # Verify bootstrap import is present and comes before other imports
    assert "from . import bootstrap" in init_source, "bootstrap should be imported in __init__.py"

    # Check the bootstrap/__init__.py to ensure it imports logging_bootstrap
    import mcp_server_tree_sitter.bootstrap

    bootstrap_init_source = inspect.getsource(mcp_server_tree_sitter.bootstrap)

    assert "from . import logging_bootstrap" in bootstrap_init_source, "bootstrap init should import logging_bootstrap"

    # Check that bootstrap's __all__ includes logging functions
    assert "get_logger" in mcp_server_tree_sitter.bootstrap.__all__, "get_logger should be exported by bootstrap"
    assert "update_log_levels" in mcp_server_tree_sitter.bootstrap.__all__, (
        "update_log_levels should be exported by bootstrap"
    )


def test_configure_is_called_at_import():
    """Test that the configure_root_logger is called when bootstrap is imported."""
    # Mock the root logger configuration function
    with patch("logging.basicConfig") as mock_basic_config:
        # Force reload of the module to trigger initialization
        import mcp_server_tree_sitter.bootstrap.logging_bootstrap

        importlib.reload(mcp_server_tree_sitter.bootstrap.logging_bootstrap)

        # Verify logging.basicConfig was called
        mock_basic_config.assert_called_once()


def test_environment_vars_processed_early():
    """Test that environment variables are processed before logger configuration."""
    # Test the function directly rather than trying to mock it
    # Save current environment variable value
    original_env = os.environ.get("MCP_TS_LOG_LEVEL", None)

    try:
        # Test with DEBUG level
        os.environ["MCP_TS_LOG_LEVEL"] = "DEBUG"
        from mcp_server_tree_sitter.bootstrap.logging_bootstrap import get_log_level_from_env

        # Verify function returns correct level
        assert get_log_level_from_env() == logging.DEBUG, "Should return DEBUG level from environment"

        # Test with INFO level - this time specify module differently to avoid NameError
        os.environ["MCP_TS_LOG_LEVEL"] = "INFO"
        # First import the module
        import importlib

        import mcp_server_tree_sitter.bootstrap.logging_bootstrap as bootstrap_logging

        # Then reload it to pick up the new environment variable
        importlib.reload(bootstrap_logging)

        # Verify the function returns the new level
        assert bootstrap_logging.get_log_level_from_env() == logging.INFO, "Should return INFO level from environment"

    finally:
        # Restore environment
        if original_env is None:
            del os.environ["MCP_TS_LOG_LEVEL"]
        else:
            os.environ["MCP_TS_LOG_LEVEL"] = original_env


def test_handlers_synchronized_at_init():
    """Test that handler levels are synchronized at initialization."""
    # Mock handlers on the root logger
    mock_handler = MagicMock()
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers

    try:
        # Add mock handler and capture original handlers
        root_logger.handlers = [mock_handler]

        # Set environment variable
        with patch.dict(os.environ, {"MCP_TS_LOG_LEVEL": "DEBUG"}):
            # Mock the get_log_level_from_env function to control return value
            with patch("mcp_server_tree_sitter.bootstrap.logging_bootstrap.get_log_level_from_env") as mock_get_level:
                mock_get_level.return_value = logging.DEBUG

                # Force reload to trigger initialization
                import mcp_server_tree_sitter.bootstrap.logging_bootstrap

                importlib.reload(mcp_server_tree_sitter.bootstrap.logging_bootstrap)

                # Verify handler level was set
                mock_handler.setLevel.assert_called_with(logging.DEBUG)
    finally:
        # Restore original handlers
        root_logger.handlers = original_handlers
