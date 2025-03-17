"""Tests for how configuration settings affect actual system behavior."""

import tempfile
from pathlib import Path

import pytest

from mcp_server_tree_sitter.api import get_tree_cache
from mcp_server_tree_sitter.exceptions import FileAccessError
from tests.test_helpers import get_ast, register_project_tool, temp_config


@pytest.fixture
def test_project():
    """Create a temporary test project with sample files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create a simple Python file
        test_file = project_path / "test.py"
        with open(test_file, "w") as f:
            f.write("def hello():\n    print('Hello, world!')\n\nhello()\n")

        # Register the project
        project_name = "config_behavior_test"
        try:
            register_project_tool(path=str(project_path), name=project_name)
        except Exception:
            # If registration fails, try with a more unique name
            import time

            project_name = f"config_behavior_test_{int(time.time())}"
            register_project_tool(path=str(project_path), name=project_name)

        yield {"name": project_name, "path": str(project_path), "file": "test.py"}


def test_cache_enabled_setting(test_project):
    """Test that cache.enabled controls caching behavior."""
    # No need to get project registry, project object, or file path here

    # Clear cache to start fresh
    tree_cache = get_tree_cache()
    tree_cache.invalidate()

    # Test with cache enabled
    with temp_config(**{"cache.enabled": True}):
        # First parse should not be from cache
        # No need to get language registry here
        # Language detection is not needed here

        # Track cache access
        cache_miss_count = 0
        cache_hit_count = 0

        # Get tree cache
        tree_cache = get_tree_cache()

        # Override get method to track cache hits/misses
        original_get = tree_cache.get

        def tracked_get(*args, **kwargs):
            nonlocal cache_hit_count, cache_miss_count
            result = original_get(*args, **kwargs)
            if result is None:
                cache_miss_count += 1
            else:
                cache_hit_count += 1
            return result

        tree_cache.get = tracked_get

        try:
            # First parse
            get_ast(project=test_project["name"], path=test_project["file"])
            # Second parse
            get_ast(project=test_project["name"], path=test_project["file"])

            # Verify we got a cache hit on the second parse
            assert cache_miss_count == 1, "First parse should be a cache miss"
            assert cache_hit_count == 1, "Second parse should be a cache hit"
        finally:
            # Restore original method
            tree_cache.get = original_get

    # Clear cache
    tree_cache = get_tree_cache()
    tree_cache.invalidate()

    # Test with cache disabled
    with temp_config(**{"cache.enabled": False}):
        # Track cache access
        cache_miss_count = 0
        put_count = 0

        # Get tree cache
        tree_cache = get_tree_cache()

        # Override methods to track cache activity
        original_get = tree_cache.get
        original_put = tree_cache.put

        def tracked_get(*args, **kwargs):
            nonlocal cache_miss_count
            result = original_get(*args, **kwargs)
            if result is None:
                cache_miss_count += 1
            return result

        def tracked_put(*args, **kwargs):
            nonlocal put_count
            put_count += 1
            return original_put(*args, **kwargs)

        tree_cache.get = tracked_get
        tree_cache.put = tracked_put

        try:
            # First parse
            _ = get_ast(project=test_project["name"], path=test_project["file"])
            # Second parse
            _ = get_ast(project=test_project["name"], path=test_project["file"])

            # Verify both parses were cache misses and no cache puts occurred
            assert cache_miss_count == 2, "Both parses should be cache misses"
            assert put_count == 0, "No cache puts should occur with cache disabled"
        finally:
            # Restore original methods
            tree_cache.get = original_get
            tree_cache.put = original_put


def test_security_file_size_limit(test_project):
    """Test that security.max_file_size_mb prevents processing large files."""
    # Create a larger file
    large_file_path = Path(test_project["path"]) / "large.py"

    # Generate a file just over 1MB
    with open(large_file_path, "w") as f:
        # Create a comment line with approx 1000 chars
        comment_line = "# " + "X" * 998 + "\n"
        # Write ~1100 lines for a ~1.1MB file
        for _ in range(1100):
            f.write(comment_line)

    # Set a 1MB file size limit
    with temp_config(**{"security.max_file_size_mb": 1}):
        with pytest.raises(FileAccessError) as excinfo:
            # This should raise a FileAccessError that wraps the SecurityError
            get_ast(project=test_project["name"], path="large.py")

        # Verify the error message mentions file size
        assert "File too large" in str(excinfo.value)

    # Now set a 2MB limit
    with temp_config(**{"security.max_file_size_mb": 2}):
        # This should succeed
        result = get_ast(project=test_project["name"], path="large.py")
        assert result is not None
        assert "tree" in result


def test_excluded_dirs_setting(test_project):
    """Test that security.excluded_dirs prevents access to excluded directories."""
    # Create a directory structure with an excluded dir
    secret_dir = Path(test_project["path"]) / ".secret"
    secret_dir.mkdir(exist_ok=True)

    # Create a file in the secret directory
    secret_file = secret_dir / "secret.py"
    with open(secret_file, "w") as f:
        f.write("print('This is a secret')\n")

    # Set .secret as an excluded directory
    with temp_config(**{"security.excluded_dirs": [".secret"]}):
        with pytest.raises(FileAccessError) as excinfo:
            # This should raise a FileAccessError that wraps the SecurityError
            get_ast(project=test_project["name"], path=".secret/secret.py")

        # Verify the error message mentions the excluded directory
        assert "excluded directory" in str(excinfo.value) or "Access denied" in str(excinfo.value)

    # Without the exclusion, it should work
    with temp_config(**{"security.excluded_dirs": []}):
        # This should succeed
        result = get_ast(project=test_project["name"], path=".secret/secret.py")
        assert result is not None
        assert "tree" in result


def test_default_max_depth_setting(test_project):
    """Test that language.default_max_depth controls AST traversal depth."""
    # Create a file with nested structure
    nested_file = Path(test_project["path"]) / "nested.py"
    with open(nested_file, "w") as f:
        f.write("""
class OuterClass:
    def outer_method(self):
        if True:
            for i in range(10):
                if i % 2 == 0:
                    def inner_function():
                        return "Deep nesting"
                    return inner_function()
        return None
""")

    # Test with a small depth value
    with temp_config(**{"language.default_max_depth": 2}):
        result = get_ast(project=test_project["name"], path="nested.py")

        # Helper function to find the maximum depth in the AST
        def find_max_depth(node, current_depth=0):
            if not isinstance(node, dict):
                return current_depth

            if "children" not in node:
                return current_depth

            # Check if we hit a depth limit (truncated)
            if "truncated" in node:
                return current_depth

            if not node["children"]:
                return current_depth

            max_child_depth = 0
            for child in node["children"]:
                child_depth = find_max_depth(child, current_depth + 1)
                max_child_depth = max(max_child_depth, child_depth)

            return max_child_depth

        # Maximum depth should be limited
        max_depth = find_max_depth(result["tree"])
        assert max_depth <= 3, f"AST depth should be limited to ~3 levels, got {max_depth}"

    # Test with a larger depth value
    with temp_config(**{"language.default_max_depth": 10}):
        result = get_ast(project=test_project["name"], path="nested.py")

        # Find max depth again
        max_depth = find_max_depth(result["tree"])
        assert max_depth > 3, f"AST depth should be greater with larger max_depth, got {max_depth}"
