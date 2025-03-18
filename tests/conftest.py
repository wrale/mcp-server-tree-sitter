"""Pytest configuration for mcp-server-tree-sitter tests."""

import pytest

# Import and register the diagnostic plugin
pytest_plugins = ["mcp_server_tree_sitter.testing.pytest_diagnostic"]


@pytest.fixture(autouse=True, scope="function")
def reset_project_registry():
    """Reset the project registry between tests.

    This prevents tests from interfering with each other when using the
    project registry, which is a singleton that persists across tests.
    """
    # Import here to avoid circular imports
    from mcp_server_tree_sitter.di import get_container

    # Get registry through DI container
    container = get_container()
    registry = container.project_registry

    # Store original projects to restore after test
    original_projects = dict(registry._projects)

    # Clear for this test
    registry._projects.clear()

    yield

    # Restore original projects
    registry._projects.clear()
    registry._projects.update(original_projects)
