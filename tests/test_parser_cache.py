"""Unit tests for TreeCache (parser_cache.py).

Covers: LRU eviction, TTL expiration, max-size enforcement, concurrent access,
and cache hit/miss ratio.
"""

import tempfile
import threading
import time
from pathlib import Path

import pytest

from mcp_server_tree_sitter.cache.parser_cache import TreeCache
from mcp_server_tree_sitter.utils.tree_sitter_types import HAS_TREE_SITTER


def _make_real_tree(source: bytes) -> object:
    """Produce a real tree-sitter Tree for cache (ensure_tree requires Tree type)."""
    if not HAS_TREE_SITTER:
        pytest.skip("tree-sitter not installed")
    from mcp_server_tree_sitter.language.registry import LanguageRegistry

    reg = LanguageRegistry()
    if not reg.is_language_available("python"):
        pytest.skip("python language not available")
    parser = reg.get_parser("python")
    return parser.parse(source)


@pytest.fixture
def temp_dir() -> tempfile.TemporaryDirectory[str]:
    """Temporary directory with real files for cache keys (st_mtime)."""
    return tempfile.TemporaryDirectory()


@pytest.fixture
def small_cache() -> TreeCache:
    """Cache with small max size and short TTL for unit tests."""
    return TreeCache(max_size_mb=0.01, ttl_seconds=1, enabled=True)


def test_lru_eviction(small_cache: TreeCache, temp_dir: tempfile.TemporaryDirectory[str]) -> None:
    """Cache evicts oldest entries when full (LRU-style by timestamp)."""
    root = Path(temp_dir.name)
    # Create several small files; total size over 10KB to force eviction
    for i in range(20):
        f = root / f"f{i}.py"
        f.write_text("# " + "x" * 600 + "\n")  # ~600 bytes each

    for i in range(20):
        p = root / f"f{i}.py"
        data = p.read_bytes()
        tree = _make_real_tree(data)
        small_cache.put(p, "python", tree, data)

    # Should have evicted some entries to stay under max_size_mb
    max_bytes = small_cache.max_size_mb * 1024 * 1024
    assert small_cache.current_size_bytes <= max_bytes + 1024  # allow small tolerance
    assert len(small_cache.cache) < 20


def test_ttl_expiration(small_cache: TreeCache, temp_dir: tempfile.TemporaryDirectory[str]) -> None:
    """Entries expire after TTL seconds."""
    root = Path(temp_dir.name)
    f = root / "a.py"
    f.write_text("x = 1\n")
    data = f.read_bytes()
    tree = _make_real_tree(data)
    small_cache.put(f, "python", tree, data)
    assert small_cache.get(f, "python") is not None

    time.sleep(1.5)
    assert small_cache.get(f, "python") is None


def test_max_size_enforcement(small_cache: TreeCache, temp_dir: tempfile.TemporaryDirectory[str]) -> None:
    """Cache does not exceed max_size_mb."""
    root = Path(temp_dir.name)
    # Add entries until we've added more than max size; eviction should keep total under limit
    for i in range(25):
        p = root / f"big{i}.py"
        content = ("# " + "y" * 500 + "\n") * 2  # ~1KB each
        p.write_text(content)
        data = p.read_bytes()
        tree = _make_real_tree(data)
        small_cache.put(p, "python", tree, data)

    max_bytes = small_cache.max_size_mb * 1024 * 1024
    assert small_cache.current_size_bytes <= max_bytes + 2048


def test_concurrent_access(small_cache: TreeCache, temp_dir: tempfile.TemporaryDirectory[str]) -> None:
    """Concurrent get/put from multiple threads do not corrupt cache."""
    root = Path(temp_dir.name)
    errors: list[Exception] = []

    def worker(thread_id: int) -> None:
        try:
            for i in range(10):
                p = root / f"t{thread_id}_f{i}.py"
                p.write_text(f"# thread {thread_id} file {i}\n")
                data = p.read_bytes()
                tree = _make_real_tree(data)
                small_cache.put(p, "python", tree, data)
                small_cache.get(p, "python")
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    # Cache state should be consistent: size matches sum of entry sizes
    total_stored = sum(len(src) for (_, src, _) in small_cache.cache.values())
    assert small_cache.current_size_bytes == total_stored


def test_cache_hit_miss_ratio(small_cache: TreeCache, temp_dir: tempfile.TemporaryDirectory[str]) -> None:
    """Cache hit and miss counts behave as expected."""
    root = Path(temp_dir.name)
    a = root / "a.py"
    b = root / "b.py"
    a.write_text("a = 1\n")
    b.write_text("b = 2\n")
    data_a = a.read_bytes()
    tree = _make_real_tree(data_a)
    small_cache.put(a, "python", tree, data_a)

    miss = small_cache.get(b, "python")
    hit1 = small_cache.get(a, "python")
    hit2 = small_cache.get(a, "python")

    assert miss is None
    assert hit1 is not None
    assert hit2 is not None


def test_cache_disabled_no_put(small_cache: TreeCache, temp_dir: tempfile.TemporaryDirectory[str]) -> None:
    """When disabled, put does not store and get always returns None."""
    small_cache.set_enabled(False)
    root = Path(temp_dir.name)
    f = root / "x.py"
    f.write_text("x\n")
    data = f.read_bytes()
    tree = _make_real_tree(data)
    small_cache.put(f, "python", tree, data)
    assert small_cache.get(f, "python") is None
    assert len(small_cache.cache) == 0


def test_invalidate_clears_entries(small_cache: TreeCache, temp_dir: tempfile.TemporaryDirectory[str]) -> None:
    """invalidate() clears entries for a file or entire cache."""
    root = Path(temp_dir.name)
    f = root / "f.py"
    f.write_text("x\n")
    data = f.read_bytes()
    tree = _make_real_tree(data)
    small_cache.put(f, "python", tree, data)
    assert small_cache.get(f, "python") is not None

    small_cache.invalidate(f)
    assert small_cache.get(f, "python") is None

    small_cache.put(f, "python", tree, data)
    small_cache.invalidate()
    assert len(small_cache.cache) == 0
    assert small_cache.current_size_bytes == 0
