"""Tests for server capabilities module."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from mcp_server_tree_sitter.capabilities.server_capabilities import register_capabilities


class MockMCPServer:
    """Mock MCP server for testing capability registration."""

    def __init__(self):
        """Initialize mock server with capability dictionary."""
        self.capabilities = {}

    def capability(self, name):
        """Mock decorator for registering capabilities."""

        def decorator(func):
            self.capabilities[name] = func
            return func

        return decorator


@pytest.fixture
def mock_server():
    """Create a mock MCP server for testing."""
    return MockMCPServer()


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = MagicMock()
    config.cache.enabled = True
    config.security.max_file_size_mb = 10
    config.log_level = "INFO"
    return config


@patch("mcp_server_tree_sitter.di.get_container")
def test_register_capabilities(mock_get_container, mock_server, mock_config):
    """Test that capabilities are registered correctly."""
    # Configure mock container
    mock_container = MagicMock()
    mock_container.config_manager = MagicMock()
    mock_container.config_manager.get_config.return_value = mock_config
    mock_get_container.return_value = mock_container

    # Call the register_capabilities function
    register_capabilities(mock_server)

    # Verify container.config_manager.get_config was called
    mock_container.config_manager.get_config.assert_called_once()


@patch("mcp_server_tree_sitter.capabilities.server_capabilities.logger")
@patch("mcp_server_tree_sitter.di.get_container")
def test_handle_logging(mock_get_container, mock_logger, mock_server, mock_config):
    """Test the logging capability handler."""
    # Configure mock container
    mock_container = MagicMock()
    mock_container.config_manager = MagicMock()
    mock_container.config_manager.get_config.return_value = mock_config
    mock_get_container.return_value = mock_container

    # Register capabilities
    register_capabilities(mock_server)

    # Get the logging handler from capabilities dictionary
    handle_logging = mock_server.capabilities.get("logging")

    # If we couldn't find it, create a test failure
    assert handle_logging is not None, "Could not find handle_logging function"

    # Test with valid log level
    result = handle_logging("info", "Test message")
    assert result == {"status": "success"}
    mock_logger.log.assert_called_with(logging.INFO, "MCP: Test message")

    # Test with invalid log level (should default to INFO)
    mock_logger.log.reset_mock()
    result = handle_logging("invalid", "Test message")
    assert result == {"status": "success"}
    mock_logger.log.assert_called_with(logging.INFO, "MCP: Test message")

    # Test with different log level
    mock_logger.log.reset_mock()
    result = handle_logging("error", "Error message")
    assert result == {"status": "success"}
    mock_logger.log.assert_called_with(logging.ERROR, "MCP: Error message")


@patch("mcp_server_tree_sitter.di.get_container")
def test_handle_completion_project_suggestions(mock_get_container, mock_server, mock_config):
    """Test completion handler for project suggestions."""
    # Configure mock container
    mock_container = MagicMock()
    mock_container.config_manager = MagicMock()
    mock_container.config_manager.get_config.return_value = mock_config

    # Add project_registry to container
    mock_container.project_registry = MagicMock()
    mock_container.project_registry.list_projects.return_value = [
        {"name": "project1"},
        {"name": "project2"},
    ]

    mock_get_container.return_value = mock_container

    # Register capabilities
    register_capabilities(mock_server)

    # Get the completion handler from capabilities dictionary
    handle_completion = mock_server.capabilities.get("completion")

    assert handle_completion is not None, "Could not find handle_completion function"

    # Test with text that should trigger project suggestions
    result = handle_completion("--project p", 11)

    # Verify project registry was used
    mock_container.project_registry.list_projects.assert_called_once()

    # Verify suggestions contain projects
    assert "suggestions" in result
    suggestions = result["suggestions"]
    assert len(suggestions) == 2
    assert suggestions[0]["text"] == "project1"
    assert suggestions[1]["text"] == "project2"


@patch("mcp_server_tree_sitter.di.get_container")
def test_handle_completion_language_suggestions(mock_get_container, mock_server, mock_config):
    """Test completion handler for language suggestions."""
    # Configure mock container
    mock_container = MagicMock()
    mock_container.config_manager = MagicMock()
    mock_container.config_manager.get_config.return_value = mock_config

    # Add language_registry to container
    mock_container.language_registry = MagicMock()
    mock_container.language_registry.list_available_languages.return_value = ["python", "javascript"]

    mock_get_container.return_value = mock_container

    # Register capabilities
    register_capabilities(mock_server)

    # Get the completion handler from capabilities dictionary
    handle_completion = mock_server.capabilities.get("completion")

    assert handle_completion is not None, "Could not find handle_completion function"

    # Test with text that should trigger language suggestions
    result = handle_completion("--language p", 12)

    # Verify language registry was used
    mock_container.language_registry.list_available_languages.assert_called_once()

    # Verify suggestions contain languages
    assert "suggestions" in result
    suggestions = result["suggestions"]
    assert len(suggestions) == 1  # Only 'python' starts with 'p'
    assert suggestions[0]["text"] == "python"


@patch("mcp_server_tree_sitter.di.get_container")
def test_handle_completion_config_suggestions(mock_get_container, mock_server, mock_config):
    """Test completion handler for config suggestions."""
    # Configure mock container
    mock_container = MagicMock()
    mock_container.config_manager = MagicMock()
    mock_container.config_manager.get_config.return_value = mock_config
    mock_get_container.return_value = mock_container

    # Register capabilities
    register_capabilities(mock_server)

    # Get the completion handler from capabilities dictionary
    handle_completion = mock_server.capabilities.get("completion")

    assert handle_completion is not None, "Could not find handle_completion function"

    # Test with text that should trigger config suggestions
    result = handle_completion("--config cache", 14)

    # Verify suggestions contain config options
    assert "suggestions" in result
    suggestions = result["suggestions"]
    assert len(suggestions) == 1  # Only 'cache_enabled' matches
    assert suggestions[0]["text"] == "cache_enabled"
    assert "Cache enabled: True" in suggestions[0]["description"]
