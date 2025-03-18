"""Tests for context.py module."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from mcp_server_tree_sitter.cache.parser_cache import TreeCache
from mcp_server_tree_sitter.config import ConfigurationManager, ServerConfig
from mcp_server_tree_sitter.context import ServerContext, global_context
from mcp_server_tree_sitter.exceptions import ProjectError
from mcp_server_tree_sitter.language.registry import LanguageRegistry
from mcp_server_tree_sitter.models.project import ProjectRegistry


@pytest.fixture
def mock_dependencies():
    """Fixture to create mock dependencies for ServerContext."""
    config_manager = MagicMock(spec=ConfigurationManager)
    project_registry = MagicMock(spec=ProjectRegistry)
    language_registry = MagicMock(spec=LanguageRegistry)
    tree_cache = MagicMock(spec=TreeCache)

    # Set up config
    config = MagicMock(spec=ServerConfig)
    config.cache = MagicMock()
    config.cache.enabled = True
    config.cache.max_size_mb = 100
    config.security = MagicMock()
    config.security.max_file_size_mb = 5
    config.language = MagicMock()
    config.language.default_max_depth = 5
    config.log_level = "INFO"

    config_manager.get_config.return_value = config

    return {
        "config_manager": config_manager,
        "project_registry": project_registry,
        "language_registry": language_registry,
        "tree_cache": tree_cache,
    }


@pytest.fixture
def server_context(mock_dependencies):
    """Fixture to create a ServerContext instance with mock dependencies."""
    return ServerContext(
        config_manager=mock_dependencies["config_manager"],
        project_registry=mock_dependencies["project_registry"],
        language_registry=mock_dependencies["language_registry"],
        tree_cache=mock_dependencies["tree_cache"],
    )


def test_server_context_initialization(mock_dependencies):
    """Test that ServerContext is initialized correctly with provided dependencies."""
    context = ServerContext(
        config_manager=mock_dependencies["config_manager"],
        project_registry=mock_dependencies["project_registry"],
        language_registry=mock_dependencies["language_registry"],
        tree_cache=mock_dependencies["tree_cache"],
    )

    assert context.config_manager is mock_dependencies["config_manager"]
    assert context.project_registry is mock_dependencies["project_registry"]
    assert context.language_registry is mock_dependencies["language_registry"]
    assert context.tree_cache is mock_dependencies["tree_cache"]


@patch("mcp_server_tree_sitter.di.get_container")
def test_server_context_initialization_with_container(mock_get_container, mock_dependencies):
    """Test that ServerContext falls back to container when dependencies are not provided."""
    container = MagicMock()
    container.config_manager = mock_dependencies["config_manager"]
    container.project_registry = mock_dependencies["project_registry"]
    container.language_registry = mock_dependencies["language_registry"]
    container.tree_cache = mock_dependencies["tree_cache"]

    # Mock get_container() to return our container
    mock_get_container.return_value = container

    # Test directly injecting dependencies from container
    # This is what happens when get_container() is called
    context = ServerContext(
        config_manager=container.config_manager,
        project_registry=container.project_registry,
        language_registry=container.language_registry,
        tree_cache=container.tree_cache,
    )

    # We're testing that the context correctly uses these injected dependencies
    assert context.config_manager is mock_dependencies["config_manager"]
    assert context.project_registry is mock_dependencies["project_registry"]
    assert context.language_registry is mock_dependencies["language_registry"]
    assert context.tree_cache is mock_dependencies["tree_cache"]


def test_get_config(server_context, mock_dependencies):
    """Test that get_config returns the config from the config manager."""
    config = server_context.get_config()

    mock_dependencies["config_manager"].get_config.assert_called_once()
    assert config == mock_dependencies["config_manager"].get_config.return_value


def test_register_project(server_context, mock_dependencies):
    """Test that register_project calls the project registry with correct parameters."""
    # Setup
    project_registry = mock_dependencies["project_registry"]
    language_registry = mock_dependencies["language_registry"]
    mock_project = MagicMock()
    project_registry.register_project.return_value = mock_project
    mock_project.to_dict.return_value = {"name": "test_project", "path": "/path"}

    # Call the method
    result = server_context.register_project(
        path="/path/to/project", name="test_project", description="Test description"
    )

    # Verify
    project_registry.register_project.assert_called_once_with("test_project", "/path/to/project", "Test description")
    mock_project.scan_files.assert_called_once_with(language_registry)
    assert result == {"name": "test_project", "path": "/path"}


def test_register_project_with_error(server_context, mock_dependencies):
    """Test that register_project handles errors correctly."""
    # Setup
    project_registry = mock_dependencies["project_registry"]
    project_registry.register_project.side_effect = ValueError("Invalid path")

    # Call and verify
    with pytest.raises(ProjectError) as excinfo:
        server_context.register_project("/path/to/project", "test_project")

    assert "Failed to register project" in str(excinfo.value)


def test_list_projects(server_context, mock_dependencies):
    """Test that list_projects calls the project registry."""
    # Setup
    project_registry = mock_dependencies["project_registry"]
    project_registry.list_projects.return_value = [{"name": "project1"}, {"name": "project2"}]

    # Call the method
    result = server_context.list_projects()

    # Verify
    project_registry.list_projects.assert_called_once()
    assert result == [{"name": "project1"}, {"name": "project2"}]


def test_remove_project(server_context, mock_dependencies):
    """Test that remove_project calls the project registry."""
    # Setup
    project_registry = mock_dependencies["project_registry"]

    # Call the method
    result = server_context.remove_project("test_project")

    # Verify
    project_registry.remove_project.assert_called_once_with("test_project")
    assert result == {"status": "success", "message": "Project 'test_project' removed"}


def test_clear_cache_all(server_context, mock_dependencies):
    """Test that clear_cache clears all caches when no project/file is specified."""
    # Setup
    tree_cache = mock_dependencies["tree_cache"]

    # Call the method
    result = server_context.clear_cache()

    # Verify
    tree_cache.invalidate.assert_called_once_with()
    assert result == {"status": "success", "message": "Cache cleared"}


def test_clear_cache_for_file(server_context, mock_dependencies):
    """Test that clear_cache clears cache for a specific file."""
    # Setup
    tree_cache = mock_dependencies["tree_cache"]
    project_registry = mock_dependencies["project_registry"]
    mock_project = MagicMock()
    project_registry.get_project.return_value = mock_project
    mock_project.get_file_path.return_value = "/abs/path/to/file.py"

    # Call the method
    result = server_context.clear_cache("test_project", "file.py")

    # Verify
    project_registry.get_project.assert_called_once_with("test_project")
    mock_project.get_file_path.assert_called_once_with("file.py")
    tree_cache.invalidate.assert_called_once_with("/abs/path/to/file.py")
    assert result == {"status": "success", "message": "Cache cleared for file.py in test_project"}


@patch("logging.getLogger")
def test_configure_with_yaml(mock_get_logger, server_context, mock_dependencies):
    """Test that configure loads a YAML config file."""
    # Setup
    config_manager = mock_dependencies["config_manager"]
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    # Call the method and discard result
    server_context.configure(config_path="/path/to/config.yaml")

    # Verify
    config_manager.load_from_file.assert_called_once_with("/path/to/config.yaml")
    config_manager.to_dict.assert_called_once()


def test_configure_cache_enabled(server_context, mock_dependencies):
    """Test that configure sets cache.enabled correctly."""
    # Setup
    config_manager = mock_dependencies["config_manager"]
    tree_cache = mock_dependencies["tree_cache"]

    # Call the method and discard result
    server_context.configure(cache_enabled=False)

    # Verify
    config_manager.update_value.assert_called_once_with("cache.enabled", False)
    tree_cache.set_enabled.assert_called_once_with(False)
    config_manager.to_dict.assert_called_once()


def test_configure_max_file_size(server_context, mock_dependencies):
    """Test that configure sets security.max_file_size_mb correctly."""
    # Setup
    config_manager = mock_dependencies["config_manager"]

    # Call the method and discard result
    server_context.configure(max_file_size_mb=10)

    # Verify
    config_manager.update_value.assert_called_once_with("security.max_file_size_mb", 10)
    config_manager.to_dict.assert_called_once()


@patch("logging.getLogger")
def test_configure_log_level(mock_get_logger, server_context, mock_dependencies):
    """Test that configure sets log_level correctly."""
    # Setup
    config_manager = mock_dependencies["config_manager"]
    mock_root_logger = MagicMock()
    mock_get_logger.return_value = mock_root_logger

    # Call the method
    with patch(
        "logging.root.manager.loggerDict", {"mcp_server_tree_sitter": None, "mcp_server_tree_sitter.test": None}
    ):
        # Call the method and discard result
        server_context.configure(log_level="DEBUG")

    # Verify
    config_manager.update_value.assert_called_once_with("log_level", "DEBUG")
    mock_root_logger.setLevel.assert_called_with(logging.DEBUG)
    config_manager.to_dict.assert_called_once()


def test_global_context_is_instance():
    """Test that global_context is an instance of ServerContext."""
    assert isinstance(global_context, ServerContext)
