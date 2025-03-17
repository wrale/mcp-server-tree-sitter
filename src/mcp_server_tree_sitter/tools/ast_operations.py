"""AST operation tools for MCP server."""

import logging
from typing import Any, Dict, Optional

from ..exceptions import FileAccessError, ParsingError
from ..models.ast import node_to_dict
from ..utils.file_io import read_binary_file
from ..utils.security import validate_file_access
from ..utils.tree_sitter_helpers import (
    parse_source,
)

logger = logging.getLogger(__name__)


def get_file_ast(
    project: Any,
    path: str,
    language_registry: Any,
    tree_cache: Any,
    max_depth: Optional[int] = None,
    include_text: bool = True,
) -> Dict[str, Any]:
    """
    Get the AST for a file.

    Args:
        project: Project object
        path: File path (relative to project root)
        language_registry: Language registry
        tree_cache: Tree cache instance
        max_depth: Maximum depth to traverse the tree
        include_text: Whether to include node text

    Returns:
        AST as a nested dictionary

    Raises:
        FileAccessError: If file access fails
        ParsingError: If parsing fails
    """
    abs_path = project.get_file_path(path)

    try:
        validate_file_access(abs_path, project.root_path)
    except Exception as e:
        raise FileAccessError(f"Access denied: {e}") from e

    language = language_registry.language_for_file(path)
    if not language:
        raise ParsingError(f"Could not detect language for {path}")

    tree, source_bytes = parse_file(abs_path, language, language_registry, tree_cache)

    return {
        "file": path,
        "language": language,
        "tree": node_to_dict(
            tree.root_node,
            source_bytes,
            include_children=True,
            include_text=include_text,
            max_depth=max_depth if max_depth is not None else 5,
        ),
    }


def parse_file(file_path: Any, language: str, language_registry: Any, tree_cache: Any) -> tuple[Any, bytes]:
    """
    Parse a file using tree-sitter.

    Args:
        file_path: Path to file
        language: Language identifier
        language_registry: Language registry
        tree_cache: Tree cache instance

    Returns:
        (Tree, source_bytes) tuple

    Raises:
        ParsingError: If parsing fails
    """
    # Always check the cache first, even if caching is disabled
    # This ensures cache misses are tracked correctly in tests
    cached = tree_cache.get(file_path, language)
    if cached:
        tree, bytes_data = cached
        return tree, bytes_data

    try:
        # Parse the file using helper
        parser = language_registry.get_parser(language)
        # Use source directly with parser to avoid parser vs. language confusion
        source_bytes = read_binary_file(file_path)
        tree = parse_source(source_bytes, parser)
        result_tuple = (tree, source_bytes)

        # Cache the tree only if caching is enabled
        is_cache_enabled = False
        try:
            # Get cache enabled state from tree_cache
            is_cache_enabled = tree_cache._is_cache_enabled()
        except Exception:
            # Fallback to instance value if method not available
            is_cache_enabled = getattr(tree_cache, "enabled", False)

        # Store in cache only if enabled
        if is_cache_enabled:
            tree_cache.put(file_path, language, tree, source_bytes)

        return result_tuple
    except Exception as e:
        raise ParsingError(f"Error parsing {file_path}: {e}") from e


def find_node_at_position(root_node: Any, row: int, column: int) -> Optional[Any]:
    """
    Find the most specific node at a given position.

    Args:
        root_node: Root node to search from
        row: Row (line) number, 0-based
        column: Column number, 0-based

    Returns:
        Node at position or None if not found
    """
    from ..models.ast import find_node_at_position as find_node

    return find_node(root_node, row, column)
