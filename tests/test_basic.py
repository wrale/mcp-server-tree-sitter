"""Basic tests for mcp-server-tree-sitter."""

import tempfile

from mcp_server_tree_sitter.config import ServerConfig
from mcp_server_tree_sitter.language.registry import LanguageRegistry
from mcp_server_tree_sitter.models.project import ProjectRegistry


def test_config_default() -> None:
    """Test that default configuration is loaded."""
    # Create a default configuration
    config = ServerConfig()

    # Check defaults
    assert config.cache.enabled is True
    assert config.cache.max_size_mb == 100
    assert config.security.max_file_size_mb == 5
    assert ".git" in config.security.excluded_dirs


def test_project_registry() -> None:
    """Test project registry functionality."""
    registry = ProjectRegistry()

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Register a project
        project = registry.register_project("test", temp_dir)

        # Check project details
        assert project.name == "test"
        # Use os.path.samefile to compare paths instead of string comparison
        # This handles platform-specific path normalization
        # (e.g., /tmp -> /private/tmp on macOS)
        import os

        assert os.path.samefile(str(project.root_path), temp_dir)

        # List projects
        projects = registry.list_projects()
        assert len(projects) == 1
        assert projects[0]["name"] == "test"

        # Get project
        project2 = registry.get_project("test")
        assert project2.name == "test"

        # Remove project
        registry.remove_project("test")
        projects = registry.list_projects()
        assert len(projects) == 0


def test_language_registry() -> None:
    """Test language registry functionality."""
    registry = LanguageRegistry()

    # Test language detection
    assert registry.language_for_file("test.py") == "python"
    assert registry.language_for_file("script.js") == "javascript"
    assert registry.language_for_file("style.css") == "css"

    # Test available languages
    languages = registry.list_available_languages()
    assert isinstance(languages, list)

    # Test installable languages (should be empty now with language-pack)
    installable = registry.list_installable_languages()
    assert isinstance(installable, list)
    assert len(installable) == 0  # No languages need to be separately installed


if __name__ == "__main__":
    # Run tests
    test_config_default()
    test_project_registry()
    test_language_registry()
    print("All tests passed!")
