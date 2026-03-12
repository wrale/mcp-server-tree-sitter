"""AST operation tools for MCP server."""

import logging
from pathlib import Path
from typing import Any, Dict

from ..cache.parser_cache import TreeCache
from ..exceptions import FileAccessError, ParsingError
from ..language.registry import LanguageRegistry
from ..models.ast import find_enclosing_scope, node_to_dict
from ..models.project import Project
from ..utils.file_io import read_binary_file
from ..utils.security import validate_file_access
from ..utils.tree_sitter_helpers import (
    parse_source,
)
from ..utils.tree_sitter_types import Node, Tree

logger = logging.getLogger(__name__)


def get_file_ast(
    project: Project,
    path: str,
    language_registry: LanguageRegistry,
    tree_cache: TreeCache,
    max_depth: int | None = None,
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


def parse_file(
    file_path: Path,
    language: str,
    language_registry: LanguageRegistry,
    tree_cache: TreeCache,
) -> tuple[Tree, bytes]:
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


def get_enclosing_scope_for_path(
    project: Project,
    path: str,
    row: int,
    column: int,
    label: str,
    language_registry: LanguageRegistry,
    tree_cache: TreeCache,
    max_lines: int = 0,
) -> Dict[str, Any]:
    """
    Resolve file, parse it (with cache), and return the enclosing scope at (row, column).

    Same return shape as find_enclosing_scope: kind, name, text, start_line, end_line.

    Args:
        project: Project object (with get_file_path, root_path).
        path: File path relative to project root.
        row: Row (0-based).
        column: Column (0-based).
        language_registry: Language registry for detection and parsing.
        tree_cache: Tree cache instance.
        max_lines: Maximum number of lines to return (0 = no limit).

    Returns:
        Dict with kind, text, start_line, end_line, and truncated flag.
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

    return find_enclosing_scope(tree.root_node, source_bytes, row, column, label, language, max_lines)


def find_node_at_position(root_node: Node, row: int, column: int) -> Node | None:
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
