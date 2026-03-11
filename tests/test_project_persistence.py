"""Tests for project registry persistence between MCP tool calls."""

import threading
from pathlib import Path

from mcp_server_tree_sitter.api import get_project_registry
from mcp_server_tree_sitter.models.project import ProjectRegistry
from tests.test_helpers import register_project_tool


def test_project_registry_singleton(tmp_path: Path) -> None:
    """Test that project_registry is a singleton that persists."""
    # Get the project registry from API
    project_registry = get_project_registry()

    # We can't directly clear projects in the new design
    # Instead, we'll check the current projects and try to avoid conflicts
    current_projects = project_registry.list_projects()
    # We'll just assert that we know the current state
    assert isinstance(current_projects, list)

    # Register a project
    temp_dir = str(tmp_path)
    project_name = "test_project"
    project_registry.register_project(project_name, temp_dir)

    # Verify project was registered
    all_projects = project_registry.list_projects()
    project_names = [p["name"] for p in all_projects]
    assert project_name in project_names

    # Create a new registry instance
    new_registry = ProjectRegistry()

    # Because ProjectRegistry uses a class-level singleton pattern,
    # this should be the same instance
    all_projects = new_registry.list_projects()
    project_names = [p["name"] for p in all_projects]
    assert project_name in project_names


def test_mcp_tool_persistence(tmp_path: Path) -> None:
    """Test that projects persist using the project functions."""
    # Get the project registry from API
    project_registry = get_project_registry()

    # We can't directly clear projects in the new design
    # Instead, let's work with the existing state

    temp_dir = str(tmp_path)
    # Register a project using the function directly
    project_name = "test_persistence"
    register_project_tool(temp_dir, project_name)

    # Verify it exists in the registry
    all_projects = project_registry.list_projects()
    project_names = [p["name"] for p in all_projects]
    assert project_name in project_names

    # Try to get the project directly
    project = project_registry.get_project(project_name)
    assert project.name == project_name


def test_project_registry_threads(tmp_path: Path) -> None:
    """Test that project registry works correctly across threads."""
    # Get the project registry from API
    project_registry = get_project_registry()

    # We can't directly clear projects in the new design
    # Instead, let's work with the existing state

    temp_dir = str(tmp_path)
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
    all_projects = project_registry.list_projects()
    project_names = [p["name"] for p in all_projects]
    assert project_name in project_names
    assert f"{project_name}_thread" in project_names


def test_server_lifecycle(tmp_path: Path) -> None:
    """Test that project registry survives server "restarts"."""
    # Get the project registry from API
    project_registry = get_project_registry()

    # We can't directly clear projects in the new design
    # Instead, let's work with the existing state

    temp_dir = str(tmp_path)
    project_name = "lifecycle_test"

    # Register a project
    register_project_tool(temp_dir, project_name)

    # Verify it exists
    all_projects = project_registry.list_projects()
    project_names = [p["name"] for p in all_projects]
    assert project_name in project_names

    # Simulate server restart by importing modules again
    # Note: This doesn't actually restart anything, it just tests
    # that the singleton pattern works as expected with imports
    import importlib

    import mcp_server_tree_sitter.api

    importlib.reload(mcp_server_tree_sitter.api)

    # Get the project registry from the reloaded module
    from mcp_server_tree_sitter.api import get_project_registry as new_get_project_registry

    new_project_registry = new_get_project_registry()

    # The registry should still contain our project
    all_projects = new_project_registry.list_projects()
    project_names = [p["name"] for p in all_projects]
    assert project_name in project_names


def test_project_persistence_in_mcp_server(tmp_path: Path) -> None:
    """Test that project registry survives server "restarts"."""
    # Get the project registry from API
    project_registry = get_project_registry()

    # We can't directly clear projects in the new design
    # Instead, let's work with the existing state

    temp_dir = str(tmp_path)
    project_name = "lifecycle_test"

    # Register a project
    register_project_tool(temp_dir, project_name)

    # Verify it exists
    all_projects = project_registry.list_projects()
    project_names = [p["name"] for p in all_projects]
    assert project_name in project_names

    # Simulate server restart by importing modules again
    import importlib

    import mcp_server_tree_sitter.tools.project

    importlib.reload(mcp_server_tree_sitter.tools.project)

    # Get the project registry again
    test_registry = get_project_registry()

    # The registry should still contain our project
    all_projects = test_registry.list_projects()
    project_names = [p["name"] for p in all_projects]
    assert project_name in project_names
