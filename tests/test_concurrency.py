"""Concurrent access tests for cache, project registry, and search.

Uses ThreadPoolExecutor to simulate concurrent calls; asserts no data
corruption or deadlock.
"""

import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest

from mcp_server_tree_sitter.api import get_project_registry, get_tree_cache
from mcp_server_tree_sitter.models.project import ProjectRegistry
from tests.test_helpers import find_text, get_ast, list_files, register_project_tool, run_query


def _project_registry() -> ProjectRegistry:
    return get_project_registry()


@pytest.fixture
def temp_projects() -> list[tuple[str, Path]]:
    """Create several temp project dirs (caller registers them)."""
    dirs: list[tuple[str, Path]] = []
    for i in range(3):
        tmp = tempfile.mkdtemp(prefix="concurrency_")
        root = Path(tmp)
        (root / "f.py").write_text(f"x = {i}\n")
        dirs.append((f"concurrent_proj_{i}", root))
    yield dirs
    registry = _project_registry()
    for name, _ in dirs:
        try:
            registry.remove_project(name)
        except Exception:
            pass


def test_concurrent_project_register_get(temp_projects: list[tuple[str, Path]]) -> None:
    """Concurrent register_project and get_project do not corrupt registry."""
    registry = _project_registry()
    names_and_paths = temp_projects

    def register(i: int) -> str:
        name, root = names_and_paths[i]
        registry.register_project(name, str(root))
        return name

    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(register, i) for i in range(len(names_and_paths))]
        for f in as_completed(futures):
            f.result()

    listed = registry.list_projects()
    names = {p["name"] for p in listed}
    for name, _ in names_and_paths:
        assert name in names
        proj = registry.get_project(name)
        assert proj.name == name


def test_concurrent_cache_access(temp_projects: list[tuple[str, Path]]) -> None:
    """Concurrent get_ast (cache get/put) does not corrupt cache."""
    for name, root in temp_projects:
        try:
            register_project_tool(path=str(root), name=name)
        except Exception:
            pass

    cache = get_tree_cache()
    cache.invalidate()

    def do_get_ast(project_name: str) -> dict:
        return get_ast(project=project_name, path="f.py")

    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = [
            ex.submit(do_get_ast, name)
            for name, _ in temp_projects
            for _ in range(4)
        ]
        results = [f.result() for f in as_completed(futures)]

    for r in results:
        assert isinstance(r, dict)
        assert "tree" in r
    total_stored = sum(len(src) for (_, src, _) in cache.cache.values())
    assert cache.current_size_bytes == total_stored


def test_concurrent_search_and_query(temp_projects: list[tuple[str, Path]]) -> None:
    """Concurrent search_text and query_code do not deadlock or corrupt."""
    for name, root in temp_projects:
        try:
            register_project_tool(path=str(root), name=name)
        except Exception:
            pass

    def search(project_name: str) -> list:
        return find_text(project=project_name, pattern="x", max_results=10)

    def query(project_name: str) -> list:
        return run_query(
            project=project_name,
            query="(identifier) @id",
            file_path="f.py",
            language="python",
        )

    with ThreadPoolExecutor(max_workers=4) as ex:
        fs = [ex.submit(search, name) for name, _ in temp_projects for _ in range(2)]
        fq = [ex.submit(query, name) for name, _ in temp_projects for _ in range(2)]
        for f in as_completed(fs + fq):
            f.result()


def test_concurrent_list_files(temp_projects: list[tuple[str, Path]]) -> None:
    """Concurrent list_files from multiple projects is safe."""
    for name, root in temp_projects:
        try:
            register_project_tool(path=str(root), name=name)
        except Exception:
            pass

    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = [ex.submit(list_files, name) for name, _ in temp_projects for _ in range(3)]
        results = [f.result() for f in as_completed(futures)]

    for r in results:
        assert isinstance(r, list)
    for name, _ in temp_projects:
        one = list_files(name)
        assert "f.py" in one
