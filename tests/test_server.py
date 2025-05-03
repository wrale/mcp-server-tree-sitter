"""Tests for the server module."""

import logging
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from mcp_server_tree_sitter.config import ServerConfig
from mcp_server_tree_sitter.di import DependencyContainer
from mcp_server_tree_sitter.server import configure_with_context, main, mcp


@pytest.fixture
def mock_container():
    """Create a mock dependency container."""
    container = MagicMock(spec=DependencyContainer)

    # Set up mocks for required components
    container.config_manager = MagicMock()
    container.tree_cache = MagicMock()

    # Set up initial config with proper nested structure
    initial_config = MagicMock(spec=ServerConfig)

    # Create mock nested objects with proper attributes
    mock_cache = MagicMock()
    mock_cache.max_size_mb = 100
    mock_cache.enabled = True
    mock_cache.ttl_seconds = 300

    mock_security = MagicMock()
    mock_security.max_file_size_mb = 5
    mock_security.excluded_dirs = [".git", "node_modules", "__pycache__"]

    mock_language = MagicMock()
    mock_language.default_max_depth = 5
    mock_language.auto_install = False

    # Attach nested objects to config
    initial_config.cache = mock_cache
    initial_config.security = mock_security
    initial_config.language = mock_language
    initial_config.log_level = "INFO"

    # Ensure get_config returns the mock config
    container.config_manager.get_config.return_value = initial_config
    container.get_config.return_value = initial_config

    # Set up to_dict to return a dictionary with expected structure
    container.config_manager.to_dict.return_value = {
        "cache": {
            "enabled": True,
            "max_size_mb": 100,
            "ttl_seconds": 300,
        },
        "security": {
            "max_file_size_mb": 5,
            "excluded_dirs": [".git", "node_modules", "__pycache__"],
        },
        "language": {
            "auto_install": False,
            "default_max_depth": 5,
        },
        "log_level": "INFO",
    }

    return container


def test_mcp_server_initialized():
    """Test that the MCP server is initialized with the correct name."""
    assert mcp is not None
    assert mcp.name == "tree_sitter"


def test_configure_with_context_basic(mock_container):
    """Test basic configuration with no specific settings."""
    # Call configure_with_context with only the container
    config_dict, config = configure_with_context(mock_container)

    # Verify that get_config was called
    mock_container.config_manager.get_config.assert_called()

    # Verify to_dict was called to return the config
    mock_container.config_manager.to_dict.assert_called_once()

    # Verify config has expected structure
    assert "cache" in config_dict
    assert "security" in config_dict
    assert "language" in config_dict
    assert "log_level" in config_dict


def test_configure_with_context_cache_enabled(mock_container):
    """Test configuration with cache_enabled setting."""
    # Call configure_with_context with cache_enabled=False
    config_dict, config = configure_with_context(mock_container, cache_enabled=False)

    # Verify update_value was called with correct parameters
    mock_container.config_manager.update_value.assert_called_with("cache.enabled", False)

    # Verify tree_cache.set_enabled was called
    mock_container.tree_cache.set_enabled.assert_called_with(False)


def test_configure_with_context_max_file_size(mock_container):
    """Test configuration with max_file_size_mb setting."""
    # Call configure_with_context with max_file_size_mb=20
    config_dict, config = configure_with_context(mock_container, max_file_size_mb=20)

    # Verify update_value was called with correct parameters
    mock_container.config_manager.update_value.assert_called_with("security.max_file_size_mb", 20)


def test_configure_with_context_log_level(mock_container):
    """Test configuration with log_level setting."""
    # Call configure_with_context with log_level="DEBUG"
    with patch("logging.getLogger") as mock_get_logger:
        # Mock root logger
        mock_root_logger = MagicMock()
        mock_get_logger.return_value = mock_root_logger

        # All logger calls should return the same mock root logger
        mock_get_logger.side_effect = lambda name: mock_root_logger

        # Mock logging.root.manager.loggerDict
        with patch(
            "logging.root.manager.loggerDict",
            {
                "mcp_server_tree_sitter": None,
                "mcp_server_tree_sitter.test": None,
            },
        ):
            config_dict, config = configure_with_context(mock_container, log_level="DEBUG")

    # Verify update_value was called with correct parameters
    mock_container.config_manager.update_value.assert_called_with("log_level", "DEBUG")

    # Verify root logger was configured
    # Allow any call to getLogger with any name starting with "mcp_server_tree_sitter"
    mock_get_logger.assert_any_call("mcp_server_tree_sitter")
    mock_root_logger.setLevel.assert_called_with(logging.DEBUG)


def test_configure_with_context_config_path(mock_container):
    """Test configuration with config_path setting."""
    # Create a temporary YAML file
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as temp_file:
        temp_file.write("""
cache:
  enabled: true
  max_size_mb: 200
""")
        temp_file.flush()
        config_path = temp_file.name

    try:
        # Get the absolute path for comparison
        abs_path = os.path.abspath(config_path)

        # Call configure_with_context with the config path
        config_dict, config = configure_with_context(mock_container, config_path=config_path)

        # Verify load_from_file was called with correct path
        mock_container.config_manager.load_from_file.assert_called_with(abs_path)

    finally:
        # Clean up the temporary file
        os.unlink(config_path)


def test_configure_with_context_nonexistent_config_path(mock_container):
    """Test configuration with a nonexistent config path."""
    # Use a path that definitely doesn't exist
    config_path = "/nonexistent/config.yaml"

    # Call configure_with_context with the nonexistent path
    config_dict, config = configure_with_context(mock_container, config_path=config_path)

    # Verify the function handled the nonexistent file gracefully
    mock_container.config_manager.load_from_file.assert_called_with(os.path.abspath(config_path))


def test_main():
    """Test that main function can be called without errors.

    This is a simplified test that just checks that the function can be
    imported and called without raising exceptions. More comprehensive
    testing of the function's behavior is done in test_server_init.

    NOTE: This test doesn't actually call the function to avoid CLI argument
    parsing issues in the test environment.
    """
    # Just verify that the main function exists and is callable
    assert callable(main), "main function should be callable"
