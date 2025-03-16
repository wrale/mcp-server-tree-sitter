"""Tests for project registry persistence between MCP tool calls."""

import tempfile
import threading

from mcp_server_tree_sitter.models.project import ProjectRegistry
from mcp_server_tree_sitter.tools.project import project_registry, register_project


def test_project_registry_singleton() -> None:
    """Test that project_registry is a singleton that persists."""
    # Clear any existing projects to start fresh
    project_registry.projects.clear()

    # Check we have no projects
    assert len(project_registry.projects) == 0

    # Register a project
    with tempfile.TemporaryDirectory() as temp_dir:
        project_name = "test_project"
        project_registry.register_project(project_name, temp_dir)

        # Verify project was registered
        assert project_name in project_registry.projects

        # Create a new registry instance
        new_registry = ProjectRegistry()

        # Because ProjectRegistry uses a class-level singleton pattern,
        # this should be the same instance
        assert new_registry.projects is project_registry.projects
        assert project_name in new_registry.projects


def test_mcp_tool_persistence() -> None:
    """Test that projects persist using the project functions."""
    # Clear any existing projects to start fresh
    project_registry.projects.clear()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Register a project using the function directly
        project_name = "test_persistence"
        register_project(temp_dir, project_name)

        # Verify it exists in the registry
        assert project_name in project_registry.projects

        # Try to get the project directly
        project = project_registry.get_project(project_name)
        assert project.name == project_name


def test_project_registry_threads() -> None:
    """Test that project registry works correctly across threads."""
    # Clear any existing projects to start fresh
    project_registry.projects.clear()

    with tempfile.TemporaryDirectory() as temp_dir:
        project_name = "thread_test"

        # Function to run in a thread
        def thread_func() -> None:
            # This should use the same registry instance
            registry = ProjectRegistry()
            registry.register_project(f"{project_name}_thread", temp_dir)

        # Register a project in the main thread
        project_registry.register_project(project_name, temp_dir)

        # Start a thread to register another project
        thread = threading.Thread(target=thread_func)
        thread.start()
        thread.join()

        # Both projects should be in the registry
        assert project_name in project_registry.projects
        assert f"{project_name}_thread" in project_registry.projects


def test_server_lifecycle() -> None:
    """Test that project registry survives server "restarts"."""
    # Clear any existing projects to start fresh
    project_registry.projects.clear()

    with tempfile.TemporaryDirectory() as temp_dir:
        project_name = "lifecycle_test"

        # Register a project
        register_project(temp_dir, project_name)

        # Verify it exists
        assert project_name in project_registry.projects

        # Simulate server restart by importing modules again
        # Note: This doesn't actually restart anything, it just tests
        # that the singleton pattern works as expected with imports
        import importlib

        import mcp_server_tree_sitter.tools.project

        importlib.reload(mcp_server_tree_sitter.tools.project)
        from mcp_server_tree_sitter.tools.project import (
            project_registry as new_registry,
        )

        # The registry should still contain our project
        assert project_name in new_registry.projects


def test_project_persistence_in_mcp_server() -> None:
    """Test that project registry survives server \"restarts\"."""
    # Clear any existing projects to start fresh
    project_registry.projects.clear()

    with tempfile.TemporaryDirectory() as temp_dir:
        project_name = "lifecycle_test"

        # Register a project
        register_project(temp_dir, project_name)

        # Verify it exists
        assert project_name in project_registry.projects

        # Simulate server restart by importing modules again
        import importlib

        import mcp_server_tree_sitter.tools.project

        importlib.reload(mcp_server_tree_sitter.tools.project)
        from mcp_server_tree_sitter.tools.project import (
            project_registry as new_registry,
        )

        # The registry should still contain our project
        assert project_name in new_registry.projects


if __name__ == "__main__":
    # Run tests
    test_project_registry_singleton()
    test_mcp_tool_persistence()
    test_project_registry_threads()
    test_server_lifecycle()
    test_project_persistence_in_mcp_server()
    print("All tests passed!")
