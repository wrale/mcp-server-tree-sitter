"""Tests for the persistent MCP server implementation."""

import tempfile

from mcp_server_tree_sitter.models.project import ProjectRegistry
from mcp_server_tree_sitter.server import (
    mcp,
)  # Was previously importing from persistent_server

# Use the actual project registry for persistence tests
project_registry = ProjectRegistry()


def test_persistent_mcp_instance() -> None:
    """Test that the persistent MCP instance works properly."""
    # Simply check that the instance exists
    assert mcp is not None
    assert mcp.name == "tree_sitter"


def test_persistent_project_registration() -> None:
    """Test that project registration persists across different functions."""
    # We can't directly clear projects in the new design
    # Instead, let's just work with existing ones

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        project_name = "persistent_test"

        # Register a project directly using the registry
        project = project_registry.register_project(project_name, temp_dir)

        # Verify it was registered
        assert project.name == project_name
        all_projects = project_registry.list_projects()
        project_names = [p["name"] for p in all_projects]
        assert project_name in project_names

        # Get the project again to verify persistence
        project2 = project_registry.get_project(project_name)
        assert project2.name == project_name

        # List projects to verify it's included
        projects = project_registry.list_projects()
        assert any(p["name"] == project_name for p in projects)


def test_project_registry_singleton() -> None:
    """Test that project_registry is a singleton that persists."""
    # Check singleton behavior
    registry1 = ProjectRegistry()
    registry2 = ProjectRegistry()

    # Should be the same instance
    assert registry1 is registry2

    # Get projects from both registries
    projects1 = registry1.list_projects()
    projects2 = registry2.list_projects()

    # Should have the same number of projects
    assert len(projects1) == len(projects2)
