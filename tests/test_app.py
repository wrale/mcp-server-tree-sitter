"""Tests for shared app state (App singleton) and ProjectRegistry singleton."""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from mcp_server_tree_sitter.app import App, get_app
from mcp_server_tree_sitter.models.project import ProjectRegistry


def test_app_singleton() -> None:
    """Test that get_app returns the same instance each time."""
    app1 = get_app()
    app2 = get_app()
    assert app1 is app2


def test_core_state_initialized() -> None:
    """Test that core state is initialized."""
    app = get_app()

    assert app.config_manager is not None
    assert app.project_registry is not None
    assert app.language_registry is not None
    assert app.tree_cache is not None


def test_app_singleton_across_threads() -> None:
    """Confirm only one App instance is created across threads."""
    instances: list[App] = []
    lock = threading.Lock()

    def get_one() -> None:
        a = get_app()
        with lock:
            instances.append(a)

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(get_one) for _ in range(32)]
        for f in as_completed(futures):
            f.result()
    assert len(instances) == 32
    unique = {id(i) for i in instances}
    assert len(unique) == 1, "all threads must see the same app instance"


def test_project_registry_singleton_across_threads() -> None:
    """Confirm only one ProjectRegistry instance is created across threads."""
    instances: list[ProjectRegistry] = []
    lock = threading.Lock()

    def get_one() -> None:
        r = ProjectRegistry()
        with lock:
            instances.append(r)

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(get_one) for _ in range(32)]
        for f in as_completed(futures):
            f.result()
    assert len(instances) == 32
    unique = {id(i) for i in instances}
    assert len(unique) == 1, "all threads must see the same ProjectRegistry instance"
