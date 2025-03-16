"""Basic tests for mcp-server-tree-sitter."""

import tempfile

from mcp_server_tree_sitter.config import CONFIG, load_config
from mcp_server_tree_sitter.language.registry import LanguageRegistry
from mcp_server_tree_sitter.models.project import ProjectRegistry


def test_config_default():
    """Test that default configuration is loaded."""
    # Reset to default
    load_config()

    # Check defaults
    assert CONFIG.cache.enabled is True
    assert CONFIG.cache.max_size_mb == 100
    assert CONFIG.security.max_file_size_mb == 5
    assert ".git" in CONFIG.security.excluded_dirs


def test_project_registry():
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
        assert len(registry.projects) == 0


def test_language_registry():
    """Test language registry functionality."""
    registry = LanguageRegistry()

    # Test language detection
    assert registry.language_for_file("test.py") == "python"
    assert registry.language_for_file("script.js") == "javascript"
    assert registry.language_for_file("style.css") == "css"

    # Test available languages
    languages = registry.list_available_languages()
    assert isinstance(languages, list)

    # Test installable languages
    installable = registry.list_installable_languages()
    assert isinstance(installable, list)

    # Test getting package name
    assert registry.get_package_name("python") == "tree-sitter-python"


if __name__ == "__main__":
    # Run tests
    test_config_default()
    test_project_registry()
    test_language_registry()
    print("All tests passed!")
