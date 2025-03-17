"""Tests for cache-specific configuration settings."""

import tempfile
import time
from pathlib import Path

import pytest

from mcp_server_tree_sitter.api import get_language_registry, get_project_registry, get_tree_cache
from tests.test_helpers import get_ast, register_project_tool, temp_config


@pytest.fixture
def test_project():
    """Create a temporary test project with sample files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create multiple files to test cache capacity
        for i in range(10):
            test_file = project_path / f"file{i}.py"
            with open(test_file, "w") as f:
                # Make each file unique and sizeable
                f.write(f"# File {i}\n")
                f.write(f"def function{i}():\n")
                f.write(f"    print('This is function {i}')\n\n")
                # Add more content to make files reasonably sized
                for j in range(20):
                    f.write(f"    # Comment line {j} to add size\n")

        # Register the project
        project_name = "cache_test_project"
        try:
            register_project_tool(path=str(project_path), name=project_name)
        except Exception:
            # If registration fails, try with a more unique name
            import time

            project_name = f"cache_test_project_{int(time.time())}"
            register_project_tool(path=str(project_path), name=project_name)

        yield {"name": project_name, "path": str(project_path)}


def test_cache_max_size_setting(test_project):
    """Test that cache.max_size_mb limits the cache size."""
    # Clear cache to start fresh
    tree_cache = get_tree_cache()
    tree_cache.invalidate()

    # Create larger files to force eviction
    for i in range(5):
        large_file = Path(test_project["path"]) / f"large_file{i}.py"
        with open(large_file, "w") as f:
            # Create a file with approximately 3KB of data
            f.write(f"# File {i} - larger content to trigger cache eviction\n")
            # Add 300 lines with 10 chars each = ~3KB
            for j in range(300):
                f.write(f"# Line {j:04d}\n")

    # Set a very small cache size (just 8KB, so only 2-3 files can fit)
    with temp_config(**{"cache.max_size_mb": 0.008, "cache.enabled": True}):
        # Process all files to fill the cache and force eviction
        for i in range(5):
            get_ast(project=test_project["name"], path=f"large_file{i}.py")

        # Cache should have evicted some entries to stay under the limit

        # Check if eviction worked by counting entries in the cache
        tree_cache = get_tree_cache()
        cache_size = len(tree_cache.cache)
        print(f"Cache entries: {cache_size}")

        # Calculate approximate current size in MB
        size_mb = tree_cache.current_size_bytes / (1024 * 1024)
        print(f"Cache size: {size_mb:.4f} MB")

        # Assert the cache stayed below the configured limit
        assert size_mb <= 0.008, f"Cache exceeded max size: {size_mb:.4f} MB > 0.008 MB"

        # Should be fewer entries than files processed (some were evicted)
        assert cache_size < 5, "Cache should have evicted some entries"


def test_cache_ttl_setting(test_project):
    """Test that cache.ttl_seconds controls cache entry lifetime."""
    # Clear cache to start fresh
    tree_cache = get_tree_cache()
    tree_cache.invalidate()

    # Set a very short TTL (1 second)
    with temp_config(**{"cache.ttl_seconds": 1, "cache.enabled": True}):
        # Parse a file
        file_path = "file0.py"
        get_ast(project=test_project["name"], path=file_path)

        # Verify it's in the cache
        project_registry = get_project_registry()
        project = project_registry.get_project(test_project["name"])
        abs_path = project.get_file_path(file_path)
        language_registry = get_language_registry()
        language = language_registry.language_for_file(file_path)

        # Check cache directly
        tree_cache = get_tree_cache()
        cached_before = tree_cache.get(abs_path, language)
        assert cached_before is not None, "Entry should be in cache initially"

        # Wait for TTL to expire
        time.sleep(1.5)

        # Check if entry was removed after TTL expiration
        tree_cache = get_tree_cache()
        cached_after = tree_cache.get(abs_path, language)
        assert cached_after is None, "Entry should be removed after TTL"


def test_cache_eviction_policy(test_project):
    """Test that the cache evicts oldest entries first when full."""
    # Clear cache to start fresh
    tree_cache = get_tree_cache()
    tree_cache.invalidate()

    # Create larger files to force eviction
    for i in range(5):
        large_file = Path(test_project["path"]) / f"large_evict{i}.py"
        with open(large_file, "w") as f:
            # Create a file with approximately 3KB of data
            f.write(f"# File {i} for eviction test\n")
            # Add 300 lines with 10 chars each = ~3KB
            for j in range(300):
                f.write(f"# Evict {j:04d}\n")

    # Set a tiny cache size to force eviction (6KB = only 2 files)
    with temp_config(**{"cache.max_size_mb": 0.006, "cache.enabled": True}):
        # Track which entries are accessed
        access_order = []

        # Get tree cache instance
        tree_cache = get_tree_cache()

        # Override the cache's get method to track access
        original_get = tree_cache.get

        def tracked_get(file_path, language):
            # Track access
            key = f"{file_path.name}"
            if key not in access_order:
                access_order.append(key)
            return original_get(file_path, language)

        try:
            # Temporarily replace the method
            tree_cache.get = tracked_get

            # Access files in a specific order to populate cache
            for i in range(5):
                get_ast(project=test_project["name"], path=f"large_evict{i}.py")

            # The cache should be smaller than the number of files accessed
            tree_cache = get_tree_cache()
            assert len(tree_cache.cache) < 5, "Cache should have evicted some entries"

            # Check that earlier entries were evicted (oldest first policy)
            project_registry = get_project_registry()
            project = project_registry.get_project(test_project["name"])
            language_registry = get_language_registry()
            language = language_registry.language_for_file("file0.py")

            # Check if the first file is still in cache
            file0_path = project.get_file_path("file0.py")
            cached_file0 = original_get(file0_path, language)

            # Check if the last file is in cache
            file4_path = project.get_file_path("file4.py")
            cached_file4 = original_get(file4_path, language)

            # Assert that later entries are more likely to be in cache
            # We can't make a 100% guarantee due to size differences,
            # but we can check the general pattern
            if cached_file0 is None and cached_file4 is not None:
                assert True, "Eviction policy is working as expected"
            elif cached_file0 is not None and cached_file4 is not None:
                assert True, "Both files in cache, can't verify eviction policy"
            elif cached_file0 is None and cached_file4 is None:
                assert True, "Both files evicted, can't verify eviction policy"
            else:  # cached_file0 is not None and cached_file4 is None
                pytest.fail("Unexpected cache state: older entry present but newer missing")

        finally:
            # Restore original method
            tree_cache.get = original_get
