"""Tests for the dependency injection container."""

from mcp_server_tree_sitter.di import get_container


def test_container_singleton():
    """Test that get_container returns the same instance each time."""
    container1 = get_container()
    container2 = get_container()
    assert container1 is container2


def test_register_custom_dependency():
    """Test registering and retrieving a custom dependency."""
    container = get_container()

    # Register a custom dependency
    test_value = {"test": "value"}
    container.register_dependency("test_dependency", test_value)

    # Retrieve it
    retrieved = container.get_dependency("test_dependency")
    assert retrieved is test_value


def test_core_dependencies_initialized():
    """Test that core dependencies are automatically initialized."""
    container = get_container()

    assert container.config_manager is not None
    assert container.project_registry is not None
    assert container.language_registry is not None
    assert container.tree_cache is not None
